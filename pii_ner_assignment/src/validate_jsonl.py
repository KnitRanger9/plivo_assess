# scripts/validate_jsonl.py
import json
def validate(path):
    for n,line in enumerate(open(path)):
        obj=json.loads(line)
        for e in obj.get("entities",[]):
            s,e_idx,label=e["start"],e["end"],e["label"]
            assert 0<=s<e_idx<=len(obj["text"]), f"Bad offsets {s},{e_idx} on line {n}"
            # optional check for expected token patterns
    print("OK")
