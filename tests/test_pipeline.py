"""Offline tests: mock provider + tfidf embedder, no Ollama needed.
Run: ASSISTANT_PROVIDER=mock ASSISTANT_EMBEDDER=tfidf pytest -q
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("ASSISTANT_PROVIDER", "mock")
os.environ.setdefault("ASSISTANT_EMBEDDER", "tfidf")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

from assistant import config, intent, rag  # noqa: E402
from assistant.memory import Memory, extract_facts  # noqa: E402
from assistant.pipeline import Assistant  # noqa: E402
from assistant.router import route, routing_gain  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def artifacts():
    if not intent.MODEL_PATH.exists():
        intent.train()
    if not config.INDEX_PATH.exists():
        rag.build_index(embedder="tfidf")


def test_intent_accuracy():
    m = intent.train()
    assert m["accuracy"] >= 0.80


def test_router_is_transparent_and_deterministic():
    d = route("coding")
    assert d.chosen == "GPT"
    assert abs(sum(d.breakdown["GPT"].values()) - d.scores["GPT"]) < 1e-6
    assert route("search").chosen == "Sonar"
    assert route("multimodal").chosen == "Gemini"
    assert route("writing").chosen == "Claude"


def test_weights_change_decision():
    cheap = route("writing", weights={"accuracy": 0.1, "cost": 0.6, "latency": 0.3})
    assert cheap.chosen == "Sonar"


def test_routing_gain_positive():
    g = routing_gain(["coding", "writing", "search", "reasoning", "multimodal"])
    assert g["mean_gap"] > 0


def test_fact_extraction():
    facts = extract_facts("Hi! My name is Arjun. What is 2+2? I use Neovim.")
    assert any("Arjun" in f for f in facts) and any("Neovim" in f for f in facts)
    assert not any("2+2" in f for f in facts)


def test_memory_recall_across_sessions(tmp_path):
    m = Memory(str(tmp_path / "m.db"), embedder="tfidf")
    m.add_turn("s1", "user", "My dog is called Bruno and he is 4.")
    m.add_turn("s2", "user", "I drive a blue Honda City.")
    hits = m.recall("What is my dog's name?", top_k=1)
    assert hits and "Bruno" in hits[0].text


def test_rag_retrieval():
    r = rag.Retriever()
    ps = r.retrieve("What is the rated payload of the Orbit 2?")
    assert ps and any("600 kg" in p.text for p in ps)


def test_model_d_end_to_end(tmp_path):
    a = Assistant.variant("D", provider="mock", embedder="tfidf", memory_db=str(tmp_path / "d.db"))
    a.chat("My name is Arjun and I live in Bangalore.")
    a.new_session()
    r = a.chat("What is my name?")
    assert "Arjun" in r.answer and r.decision is not None
    r2 = a.chat("Who chairs the Helix board?")
    assert r2.passages and any("Meera Iyer" in p.text for p in r2.passages)


def test_baseline_cannot_answer_corpus(tmp_path):
    a = Assistant.variant("baseline", provider="mock", memory_db=str(tmp_path / "b.db"))
    r = a.chat("Who chairs the Helix board?")
    assert "Meera" not in r.answer


def test_task_bench_graders():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import run_task_bench as b
    code = "```python\ndef is_prime(n):\n    return n > 1 and all(n % d for d in range(2, int(n ** .5) + 1))\n```"
    assert b.grade(code, {"type": "code", "func": "is_prime", "tests": [[[2], True], [[21], False]]})[0]
    assert not b.grade("def is_prime(n): return True", {"type": "code", "func": "is_prime", "tests": [[[21], False]]})[0]
    assert b.grade("so it is 12,100.\nAnswer: 12,100", {"type": "number", "value": 12100})[0]
    assert b.grade("a\nb\nc", {"type": "lines", "n": 3})[0]
    assert b.grade("Bar A is taller.", {"type": "ab_choice", "answer": "A"})[0]
