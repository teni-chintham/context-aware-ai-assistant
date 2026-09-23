"""Train the intent classifier (Model A part 1) and print held-out metrics."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from assistant import intent

m = intent.train()
print(f"examples: {m['n_total']}  train: {m['n_train']}  test: {m['n_test']}")
print(f"held-out accuracy (grouped, no leakage): {m['accuracy']:.3f}   macro F1: {m['macro_f1']:.3f}")
print(f"random-split accuracy (leaky, for comparison): {m['random_split_accuracy_leaky']:.3f}")
for k, v in m["per_class"].items():
    print(f"  {k:<11} P={v['precision']:.2f} R={v['recall']:.2f} F1={v['f1-score']:.2f}")
print(f"saved model -> {intent.MODEL_PATH}\nmetrics -> {intent.METRICS_PATH}")
