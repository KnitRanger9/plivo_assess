# PII Named Entity Recognition for STT Transcripts

A machine learning system for detecting and classifying Personally Identifiable Information (PII) in Speech-to-Text (STT) transcripts using token-level Named Entity Recognition (NER). This project implements a fast, production-ready model that identifies sensitive information such as credit card numbers, phone numbers, emails, names, and dates while maintaining low-latency inference.

## Overview

This repository contains a complete ML pipeline for PII detection in noisy STT transcripts. The system uses transformer-based token classification models (BIO tagging scheme) to detect entities and automatically classify them as PII or non-PII based on predefined rules.

### Key Features

- **Entity Detection**: Identifies 7 entity types (CREDIT_CARD, PHONE, EMAIL, PERSON_NAME, DATE, CITY, LOCATION)
- **PII Classification**: Automatically tags entities as PII (true/false) based on entity type
- **Low Latency**: Optimized for p95 latency < 20ms per utterance (batch size 1, CPU inference)
- **Robust to Noise**: Handles STT transcription artifacts like spelling mistakes, missing punctuation, and spoken forms ("at", "dot", "double nine", "oh" for zero)
- **Span-level Evaluation**: Provides comprehensive metrics including per-entity and PII-specific precision, recall, and F1 scores
- **Production Ready**: Includes training, inference, evaluation, and latency benchmarking scripts

## Entity Types and PII Classification

| Entity Type | PII Classification | Description |
|------------|-------------------|-------------|
| `CREDIT_CARD` | ✅ PII | Credit card numbers |
| `PHONE` | ✅ PII | Phone numbers |
| `EMAIL` | ✅ PII | Email addresses |
| `PERSON_NAME` | ✅ PII | Person names |
| `DATE` | ✅ PII | Dates |
| `CITY` | ❌ Non-PII | City names |
| `LOCATION` | ❌ Non-PII | Location/landmark names |

## Requirements

- Python 3.8+
- PyTorch
- Transformers (HuggingFace)
- NumPy
- Other dependencies listed in `requirements.txt`

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd pii_ner_assignment
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
pii_ner_assignment/
├── data/                          # Data directory
│   ├── train.jsonl               # Training data
│   ├── dev.jsonl                 # Development/validation data
│   └── test.jsonl                # Test data (no ground truth)
├── src/                          # Source code
│   ├── dataset.py                # Dataset loader and BIO tagging
│   ├── labels.py                 # Label definitions and PII mapping
│   ├── model.py                  # Model creation utilities
│   ├── train.py                  # Training script
│   ├── predict.py                # Inference script
│   ├── eval_span_f1.py           # Evaluation metrics
│   ├── measure_latency.py        # Latency benchmarking
│   ├── generate_data.py          # Synthetic data generation (optional)
│   └── validate_jsonl.py         # Data validation utilities
├── out/                          # Model output directory (created after training)
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Usage

### Training

Train a model on the training set:

```bash
python src/train.py \
  --model_name distilbert-base-uncased \
  --train data/train.jsonl \
  --dev data/dev.jsonl \
  --out_dir out \
  --batch_size 8 \
  --epochs 3 \
  --lr 5e-5 \
  --max_length 256
```

**Training Arguments:**
- `--model_name`: HuggingFace model identifier (default: `distilbert-base-uncased`)
- `--train`: Path to training JSONL file
- `--dev`: Path to development JSONL file
- `--out_dir`: Output directory for saved model and tokenizer
- `--batch_size`: Training batch size (default: 8)
- `--epochs`: Number of training epochs (default: 3)
- `--lr`: Learning rate (default: 5e-5)
- `--max_length`: Maximum sequence length (default: 256)
- `--device`: Device to use (`cuda` or `cpu`, auto-detected by default)

### Inference

Generate predictions on a dataset:

```bash
python src/predict.py \
  --model_dir out \
  --input data/dev.jsonl \
  --output out/dev_pred.json \
  --max_length 256
```

**Inference Arguments:**
- `--model_dir`: Directory containing the trained model
- `--input`: Input JSONL file
- `--output`: Output JSON file path
- `--max_length`: Maximum sequence length (default: 256)
- `--device`: Device to use (`cuda` or `cpu`, auto-detected by default)

### Evaluation

Evaluate model predictions against gold labels:

```bash
python src/eval_span_f1.py \
  --gold data/dev.jsonl \
  --pred out/dev_pred.json
```

This outputs:
- Per-entity precision, recall, and F1 scores
- Macro-averaged F1 score
- PII-only metrics (precision, recall, F1)
- Non-PII metrics (precision, recall, F1)

### Latency Measurement

Measure inference latency:

```bash
python src/measure_latency.py \
  --model_dir out \
  --input data/dev.jsonl \
  --runs 50 \
  --max_length 256
```

This outputs p50 and p95 latency metrics in milliseconds.

**Latency Arguments:**
- `--model_dir`: Directory containing the trained model
- `--input`: Input JSONL file for benchmarking
- `--runs`: Number of inference runs (default: 50)
- `--max_length`: Maximum sequence length (default: 256)
- `--device`: Device to use (`cuda` or `cpu`, auto-detected by default)

## Data Format

### Input Format (JSONL)

Each line in `train.jsonl` and `dev.jsonl` is a JSON object:

```json
{
  "id": "utt_0012",
  "text": "my credit card number is four two four two 4242 4242 4242 and email is ramesh sharma at gmail dot com",
  "entities": [
    { "start": 3, "end": 19, "label": "CREDIT_CARD" },
    { "start": 63, "end": 77, "label": "PERSON_NAME" },
    { "start": 81, "end": 105, "label": "EMAIL" }
  ]
}
```

- `id`: Unique utterance identifier
- `text`: STT-style transcript (may contain spelling mistakes, missing punctuation, spoken forms)
- `entities`: List of gold entity spans
  - `start`: Start character index (Python slice semantics)
  - `end`: End character index (exclusive)
  - `label`: Entity type

### Output Format (JSON)

Predictions are written as a single JSON object:

```json
{
  "utt_0012": [
    { "start": 3, "end": 19, "label": "CREDIT_CARD", "pii": true },
    { "start": 63, "end": 77, "label": "PERSON_NAME", "pii": true },
    { "start": 81, "end": 105, "label": "EMAIL", "pii": true }
  ],
  "utt_0013": [
    { "start": 10, "end": 22, "label": "PHONE", "pii": true }
  ]
}
```

Each entity includes:
- `start`: Start character index
- `end`: End character index (exclusive)
- `label`: Predicted entity type
- `pii`: Boolean indicating if the entity is PII

## Model Architecture

The system uses a token classification model based on HuggingFace transformers:

- **Base Model**: Configurable (default: `distilbert-base-uncased`)
- **Tagging Scheme**: BIO (Begin-Inside-Outside)
- **Task**: Token-level classification with 15 labels (7 entity types × 2 tags + O)
- **Training**: Fine-tuning with AdamW optimizer and linear learning rate scheduling

The model is optimized for:
- **Speed**: Lightweight base models and efficient inference
- **Accuracy**: Fine-tuning on STT-style transcripts with noisy patterns
- **Precision**: Emphasis on PII precision to minimize false positives

## Performance Targets

- **Latency**: p95 ≤ 20 ms per utterance (batch size 1, CPU)
- **PII Precision**: ≥ 0.80 on development set
- **Entity F1**: Competitive per-entity and macro-averaged F1 scores

Note: PII precision is prioritized over recall for safety considerations.

## Evaluation Metrics

The evaluation script provides:

1. **Per-Entity Metrics**: Precision, Recall, F1 for each entity type
2. **Macro-F1**: Average F1 score across all entity types
3. **PII Metrics**: Precision, Recall, F1 for PII entities only
4. **Non-PII Metrics**: Precision, Recall, F1 for non-PII entities

## Example Workflow

Complete training and evaluation workflow:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Train the model
python src/train.py \
  --model_name distilbert-base-uncased \
  --train data/train.jsonl \
  --dev data/dev.jsonl \
  --out_dir out \
  --epochs 3

# 3. Generate predictions
python src/predict.py \
  --model_dir out \
  --input data/dev.jsonl \
  --output out/dev_pred.json

# 4. Evaluate performance
python src/eval_span_f1.py \
  --gold data/dev.jsonl \
  --pred out/dev_pred.json

# 5. Measure latency
python src/measure_latency.py \
  --model_dir out \
  --input data/dev.jsonl \
  --runs 50
```

## Notes

- The model uses learned sequence labeling (not regex-based) as the primary detection method
- STT transcripts may contain various forms of spoken numbers (e.g., "four two four two" instead of "4242")
- Email addresses may appear as "name at domain dot com" format
- The system handles character-level span alignment between tokenized and original text

