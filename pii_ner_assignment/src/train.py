import os
import argparse
import json
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from transformers import AutoTokenizer, get_linear_schedule_with_warmup
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
from torchcrf import CRF

from dataset import PIIDataset, collate_batch
from labels import LABELS
from model import create_model


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model_name", default="distilbert-base-uncased")
    ap.add_argument("--train", default="data/train.jsonl")
    ap.add_argument("--dev", default="data/dev.jsonl")
    ap.add_argument("--out_dir", default="out")
    ap.add_argument("--batch_size", type=int, default=8)
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--max_length", type=int, default=256)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    
    # NEW ARGUMENTS
    ap.add_argument("--use_class_weights", action="store_true", 
                    help="Enable class weighting for imbalanced labels")
    ap.add_argument("--use_focal_loss", action="store_true", 
                    help="Enable focal loss (requires use_class_weights)")
    ap.add_argument("--focal_alpha", type=float, default=0.25, 
                    help="Focal loss alpha parameter")
    ap.add_argument("--focal_gamma", type=float, default=2.0, 
                    help="Focal loss gamma parameter")
    ap.add_argument("--use_cosine_scheduler", action="store_true", 
                    help="Use cosine annealing with warmup instead of linear")
    ap.add_argument("--warmup_ratio", type=float, default=0.1, 
                    help="Warmup ratio (0.0-1.0)")
    ap.add_argument("--use_crf", action="store_true", 
                    help="Add CRF layer on top of model for structured decoding")
    
    return ap.parse_args()

def compute_class_weights(train_ds, label_list, device):
    """
    Compute class weights based on label frequency in training data.
    Rare labels (like specific entity types) get higher weights.
    """
    label_counts = {label: 0 for label in label_list}
    
    for item in train_ds.items:
        labels = item["labels"]
        for label_id in labels:
            if label_id >= 0:  # Ignore padding tokens (-100)
                label = label_list[label_id]
                label_counts[label] += 1
    
    total = sum(label_counts.values())
    weights = []
    for label in label_list:
        count = label_counts[label]
        # Inverse frequency weighting
        weight = total / (len(label_list) * max(count, 1))
        weights.append(weight)
    
    weights = torch.tensor(weights, dtype=torch.float32, device=device)
    print(f"Class weights: {dict(zip(label_list, weights.cpu().tolist()))}")
    return weights

class FocalLoss(nn.Module):
    """
    Focal Loss for handling class imbalance.
    Focuses training on hard negatives and rare classes.
    
    Reference: https://arxiv.org/abs/1708.02002
    """
    def __init__(self, alpha=0.25, gamma=2.0, weight=None, reduction="mean"):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.weight = weight
        self.reduction = reduction
    
    def forward(self, logits, targets):
        """
        Args:
            logits: (batch_size, seq_len, num_classes)
            targets: (batch_size, seq_len)
        """
        # Get probabilities
        p = torch.softmax(logits, dim=-1)
        ce_loss = torch.nn.functional.cross_entropy(
            logits.view(-1, logits.size(-1)), 
            targets.view(-1),
            weight=self.weight,
            reduction="none"
        )
        
        # Get probability of true class
        p_t = p.view(-1, p.size(-1))[torch.arange(len(targets.view(-1))), targets.view(-1)]
        
        # Focal loss: -alpha * (1 - p_t)^gamma * ce_loss
        focal_weight = self.alpha * (1 - p_t) ** self.gamma
        focal_loss = focal_weight * ce_loss
        
        if self.reduction == "mean":
            return focal_loss.mean()
        elif self.reduction == "sum":
            return focal_loss.sum()
        else:
            return focal_loss
        
class ModelWithCRF(nn.Module):
    """
    Wraps a token classification model with a CRF layer.
    Ensures valid BIO tag sequences during decoding.
    """
    def __init__(self, base_model, num_labels, label2id):
        super().__init__()
        self.base_model = base_model
        self.crf = CRF(num_labels, batch_first=True)
        self.num_labels = num_labels
        self.label2id = label2id
    
    def forward(self, input_ids, attention_mask, labels=None):
        outputs = self.base_model(
            input_ids=input_ids, 
            attention_mask=attention_mask,
            output_hidden_states=False
        )
        logits = outputs.logits  # (batch_size, seq_len, num_labels)
        
        if labels is not None:
            # Training: use CRF loss
            mask = attention_mask.bool()
            loss = -self.crf(logits, labels, mask=mask, reduction="mean")
            return type('obj', (object,), {'loss': loss})()
        else:
            # Inference: use CRF decoding
            with torch.no_grad():
                predictions = self.crf.decode(logits, mask=attention_mask.bool())
            
            # Convert to tensor for compatibility
            max_len = logits.shape[1]
            pred_tensor = torch.full((logits.shape[0], max_len), 0, dtype=torch.long)
            for i, pred in enumerate(predictions):
                pred_tensor[i, :len(pred)] = torch.tensor(pred)
            
            return type('obj', (object,), {
                'logits': logits,
                'predictions': pred_tensor
            })()
        


def main():
    args = parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    
    # Save config for reproducibility
    config = {
        "model_name": args.model_name,
        "batch_size": args.batch_size,
        "epochs": args.epochs,
        "lr": args.lr,
        "max_length": args.max_length,
        "use_class_weights": args.use_class_weights,
        "use_focal_loss": args.use_focal_loss,
        "use_cosine_scheduler": args.use_cosine_scheduler,
        "use_crf": args.use_crf,
    }
    with open(os.path.join(args.out_dir, "config.json"), "w") as f:
        json.dump(config, f, indent=2)



    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    train_ds = PIIDataset(args.train, tokenizer, LABELS, max_length=args.max_length, is_train=True)
    dev_ds = PIIDataset(args.dev, tokenizer, LABELS, max_length=args.max_length, is_train=False)

    train_dl = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=lambda b: collate_batch(b, pad_token_id=tokenizer.pad_token_id),
    )
    
    dev_dl = DataLoader(
        dev_ds,
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=lambda b: collate_batch(b, pad_token_id=tokenizer.pad_token_id),
    )

    base_model = create_model(args.model_name)
    
    if args.use_crf:
        model = ModelWithCRF(base_model, num_labels=len(LABELS), label2id=label2id)
        print("✓ CRF layer enabled")
    else:
        model = base_model
    
    model.to(args.device)
    model.train()

    class_weights = None
    if args.use_class_weights:
        class_weights = compute_class_weights(train_ds, LABELS, args.device)
        print("✓ Class weighting enabled")
    
    # Choose loss function
    if args.use_focal_loss:
        if not args.use_class_weights:
            print("Warning: Focal loss works best with class weights. Enabling class weighting.")
            class_weights = compute_class_weights(train_ds, LABELS, args.device)
        loss_fn = FocalLoss(
            alpha=args.focal_alpha,
            gamma=args.focal_gamma,
            weight=class_weights,
            reduction="mean"
        )
        print(f"✓ Focal Loss enabled (alpha={args.focal_alpha}, gamma={args.focal_gamma})")
    else:
        loss_fn = None  # Use model's built-in loss
    
    # Optimizer
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    total_steps = len(train_dl) * args.epochs
    
    # Learning rate scheduler
    if args.use_cosine_scheduler:
        scheduler = CosineAnnealingWarmRestarts(
            optimizer,
            T_0=len(train_dl),  # Restart every epoch
            T_mult=1,
            eta_min=0,
            last_epoch=-1
        )
        # Add warmup
        num_warmup_steps = int(args.warmup_ratio * total_steps)
        print(f"✓ Cosine annealing scheduler with warmup (warmup_steps={num_warmup_steps})")
    else:
        scheduler = get_linear_schedule_with_warmup(
            optimizer, 
            num_warmup_steps=int(args.warmup_ratio * total_steps), 
            num_training_steps=total_steps
        )
        print(f"✓ Linear scheduler with warmup")

    best_dev_loss = float("inf")
    patience_counter = 0
    patience = 2
    
    for epoch in range(args.epochs):
        running_loss = 0.0
        model.train()
        
        for batch in tqdm(train_dl, desc=f"Epoch {epoch+1}/{args.epochs}"):
            input_ids = torch.tensor(batch["input_ids"], device=args.device)
            attention_mask = torch.tensor(batch["attention_mask"], device=args.device)
            labels = torch.tensor(batch["labels"], device=args.device)

            if args.use_crf:
                # CRF model handles its own loss
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                loss = outputs.loss
            elif args.use_focal_loss:
                # Focal loss
                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                logits = outputs.logits
                loss = loss_fn(logits, labels)
            else:
                # Default cross-entropy (with optional class weights)
                outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                loss = outputs.loss
                
                if class_weights is not None:
                    # Re-weight loss
                    ce_loss = torch.nn.functional.cross_entropy(
                        logits.view(-1, logits.size(-1)), 
                        labels.view(-1),
                        weight=class_weights,
                        reduction="mean"
                    )
                    loss = ce_loss

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)  # Gradient clipping
            optimizer.step()
            
            if args.use_cosine_scheduler:
                scheduler.step()
            
            running_loss += loss.item()

        avg_loss = running_loss / max(1, len(train_dl))
        print(f"Epoch {epoch+1} average loss: {avg_loss:.4f}")

        # Validation
        model.eval()
        dev_loss = 0.0
        with torch.no_grad():
            for batch in dev_dl:
                input_ids = torch.tensor(batch["input_ids"], device=args.device)
                attention_mask = torch.tensor(batch["attention_mask"], device=args.device)
                labels = torch.tensor(batch["labels"], device=args.device)
                
                if args.use_crf:
                    outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                    loss = outputs.loss
                elif args.use_focal_loss:
                    outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                    loss = loss_fn(outputs.logits, labels)
                else:
                    outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
                    loss = outputs.loss
                
                dev_loss += loss.item()

        avg_dev_loss = dev_loss / max(1, len(dev_dl))
        print(f"Epoch {epoch+1} dev loss: {avg_dev_loss:.4f}")

        # Early stopping + best model saving
        if epoch == 0 or avg_dev_loss < best_dev_loss:
            best_dev_loss = avg_dev_loss
            model.save_pretrained(args.out_dir)
            tokenizer.save_pretrained(args.out_dir)
            patience_counter = 0
            print(f"→ Best model saved (dev_loss: {avg_dev_loss:.4f})")
        else:
            patience_counter += 1
            print(f"→ No improvement. Patience: {patience_counter}/{patience}")
            if patience_counter >= patience:
                print("→ Early stopping triggered")
                break

        model.train()
        if not args.use_cosine_scheduler:
            scheduler.step()

    model.save_pretrained(args.out_dir)
    tokenizer.save_pretrained(args.out_dir)
    
    # Save training metadata
    metadata = {
        "best_dev_loss": best_dev_loss,
        "epochs_trained": epoch + 1,
        "early_stopping": patience_counter >= patience,
    }
    with open(os.path.join(args.out_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"Saved model + tokenizer to {args.out_dir}")


if __name__ == "__main__":
    main()
