"""Ablation study: run Models baseline / A / B / C / D on three benchmarks.

  routing   intent accuracy on the held-out split + routing gain vs fixed models
  memory    facts stated over 4 sessions, 30 recall questions in a fresh session
  rag       36 questions answerable only from data/corpus (fictional company,
            so no model can know the answers without retrieval)

Usage
  python scripts/run_ablation.py                 # all variants, current provider
  python scripts/run_ablation.py --provider mock # offline smoke run
  python scripts/run_ablation.py --variants A D --limit 10
Outputs results/ablation.json, results/ablation.csv, results/*.png
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from assistant import config, providers  # noqa: E402
from assistant.intent import METRICS_PATH  # noqa: E402
from assistant.pipeline import VARIANTS, Assistant  # noqa: E402
from assistant.router import routing_gain  # noqa: E402

EVAL = config.DATA_DIR / "eval"
ABSTAIN = re.compile(
    r"(don'?t know|do not know|don'?t have|do not have|not (?:in|from|part of|mentioned|contain|available|have)|no information|"
    r"cannot (?:find|determine|answer)|can'?t (?:find|determine|answer)|unable to|not provided|unknown to me)", re.I)


def contains_gold(answer: str, gold: list[str], any_: bool = True) -> bool:
    a = answer.lower()
    hits = [g.lower() in a for g in gold]
    return any(hits) if any_ else all(hits)


# --------------------------------------------------------------------------- benchmarks
def bench_memory(variant: str, provider: str, embedder: str, limit: int | None) -> dict:
    data = json.loads((EVAL / "memory_bench.json").read_text())
    with tempfile.TemporaryDirectory() as td:
        db = str(Path(td) / "mem.db")
        a = Assistant.variant(variant, provider=provider, embedder=embedder, memory_db=db)
        # phase 1: the user talks across several sessions
        t0 = time.time()
        for sess in data["sessions"]:
            a.new_session()
            for msg in sess:
                a.chat(msg)
        # phase 2: brand-new session, ask what it remembers
        a.new_session()
        qs = data["questions"][:limit] if limit else data["questions"]
        rows, correct = [], 0
        for q in qs:
            r = a.chat(q["q"])
            ok = contains_gold(r.answer, q["gold"])
            correct += ok
            rows.append({"q": q["q"], "answer": r.answer[:200], "correct": ok, "n_hits": len(r.memory_hits)})
        n = len(qs)
        stored = len(a.memory.all_facts()) if a.memory else 0
        return {"recall_accuracy": round(correct / n, 3), "n": n, "facts_stored": stored,
                "seconds": round(time.time() - t0, 1), "rows": rows}


def bench_rag(variant: str, provider: str, embedder: str, limit: int | None) -> dict:
    data = json.loads((EVAL / "rag_qa.json").read_text())
    qs = data[:limit] if limit else data
    a = Assistant.variant(variant, provider=provider, embedder=embedder,
                          memory_db=str(Path(tempfile.mkdtemp()) / "m.db"))
    t0 = time.time()
    rows, correct, abstain, cited = [], 0, 0, 0
    for q in qs:
        r = a.chat(q["q"])
        ok = contains_gold(r.answer, q["gold"], q.get("any", True))
        ab = (not ok) and bool(ABSTAIN.search(r.answer))
        ci = bool(re.search(r"\[\d+\]", r.answer))
        correct += ok; abstain += ab; cited += ci
        rows.append({"q": q["q"], "answer": r.answer[:200], "correct": ok, "abstained": ab,
                     "cited": ci, "n_passages": len(r.passages)})
    n = len(qs)
    halluc = n - correct - abstain
    return {"accuracy": round(correct / n, 3), "abstention_rate": round(abstain / n, 3),
            "hallucination_rate": round(halluc / n, 3), "citation_rate": round(cited / n, 3),
            "n": n, "seconds": round(time.time() - t0, 1), "rows": rows}


def bench_routing() -> dict:
    if not METRICS_PATH.exists():
        raise SystemExit("run scripts/train_intent.py first")
    m = json.loads(METRICS_PATH.read_text())
    import pandas as pd
    df = pd.read_csv(config.DATA_DIR / "intents.csv")
    test_intents = df[df["split"] == "test"]["intent"].tolist() if "split" in df else df["intent"].tolist()
    gain = routing_gain(test_intents)
    return {"intent_accuracy": round(m["accuracy"], 3), "macro_f1": round(m["macro_f1"], 3),
            "n_test": m["n_test"], "n_total": m["n_total"], "routing_gain": gain,
            "per_class": {k: round(v["f1-score"], 3) for k, v in m["per_class"].items()}}


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="+", default=["baseline", "A", "B", "C", "D"])
    ap.add_argument("--provider", default=config.PROVIDER)
    ap.add_argument("--embedder", default=config.EMBEDDER)
    ap.add_argument("--limit", type=int, default=None, help="questions per benchmark (quick runs)")
    ap.add_argument("--skip", nargs="*", default=[], choices=["memory", "rag"])
    args = ap.parse_args()

    if args.provider == "ollama" and not providers.ollama_available():
        sys.exit("Ollama not reachable. Run `ollama serve`, or use --provider mock --embedder tfidf")

    results = {"provider": args.provider, "embedder": args.embedder, "fixed_model": "GPT",
               "routing": bench_routing(), "variants": {}}
    print(f"routing: intent acc {results['routing']['intent_accuracy']}, "
          f"mean gain vs fixed {results['routing']['routing_gain']['mean_gap']}")

    for v in args.variants:
        flags = VARIANTS[v]
        print(f"\n== Model {v}  {flags}")
        entry = {"flags": flags}
        if "memory" not in args.skip:
            entry["memory"] = bench_memory(v, args.provider, args.embedder, args.limit)
            print(f"   memory recall  {entry['memory']['recall_accuracy']:.3f}  ({entry['memory']['seconds']}s)")
        if "rag" not in args.skip:
            entry["rag"] = bench_rag(v, args.provider, args.embedder, args.limit)
            r = entry["rag"]
            print(f"   rag accuracy   {r['accuracy']:.3f}  hallucination {r['hallucination_rate']:.3f}  "
                  f"abstain {r['abstention_rate']:.3f}  cited {r['citation_rate']:.3f}  ({r['seconds']}s)")
        results["variants"][v] = entry

    out = config.RESULTS_DIR / "ablation.json"
    out.write_text(json.dumps(results, indent=2))
    write_csv(results)
    try:
        make_figures(results)
    except Exception as e:  # matplotlib optional
        print("figures skipped:", e)
    print(f"\nsaved -> {out}")


def write_csv(results: dict):
    with (config.RESULTS_DIR / "ablation.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "routing", "memory", "rag", "memory_recall", "rag_accuracy",
                    "hallucination_rate", "citation_rate"])
        for v, e in results["variants"].items():
            fl = e["flags"]
            m, r = e.get("memory", {}), e.get("rag", {})
            w.writerow([v, fl["routing"], fl["memory"], fl["rag"], m.get("recall_accuracy", ""),
                        r.get("accuracy", ""), r.get("hallucination_rate", ""), r.get("citation_rate", "")])


def make_figures(results: dict):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = list(results["variants"])
    labels = [f"Model {n}" if n != "baseline" else "Baseline" for n in names]
    mem = [results["variants"][n].get("memory", {}).get("recall_accuracy", 0) for n in names]
    acc = [results["variants"][n].get("rag", {}).get("accuracy", 0) for n in names]
    hal = [results["variants"][n].get("rag", {}).get("hallucination_rate", 0) for n in names]

    fig, ax = plt.subplots(figsize=(8, 4.2))
    x = range(len(names)); w = 0.27
    ax.bar([i - w for i in x], mem, w, label="Memory recall accuracy")
    ax.bar(list(x), acc, w, label="RAG answer accuracy")
    ax.bar([i + w for i in x], hal, w, label="Hallucination rate (lower is better)")
    ax.set_xticks(list(x)); ax.set_xticklabels(labels); ax.set_ylim(0, 1.05)
    ax.set_title(f"Ablation study ({results['provider']})"); ax.legend(fontsize=8); ax.grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig(config.RESULTS_DIR / "ablation.png", dpi=160); plt.close(fig)

    g = results["routing"]["routing_gain"]["per_fixed_model"]
    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(list(g), list(g.values()))
    ax.axhline(results["routing"]["routing_gain"]["mean_gap"], ls="--", c="k", lw=1,
               label=f"mean gap {results['routing']['routing_gain']['mean_gap']}")
    ax.set_ylabel("routed score minus fixed-model score"); ax.set_title("Routing gain vs always using one model")
    ax.legend(); ax.grid(axis="y", alpha=.3)
    fig.tight_layout(); fig.savefig(config.RESULTS_DIR / "routing_gain.png", dpi=160); plt.close(fig)


if __name__ == "__main__":
    main()
