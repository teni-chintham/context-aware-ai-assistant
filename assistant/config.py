"""Central configuration: model pool, scoring weights, provider and paths.

Everything the router uses to make a decision lives here in plain sight,
so a routing decision can be audited and reproduced by anyone.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"
for _d in (MODELS_DIR, RESULTS_DIR):
    _d.mkdir(exist_ok=True)

INTENTS = ["coding", "writing", "search", "reasoning", "multimodal"]

# ---------------------------------------------------------------------------
# Provider
#   ollama  local models via http://localhost:11434 (default, free, offline)
#   openai / anthropic / gemini  cloud APIs, keys read from .env
#   mock    deterministic fake model, used by the test-suite and smoke runs
# ---------------------------------------------------------------------------
PROVIDER = os.getenv("ASSISTANT_PROVIDER", "ollama")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBEDDER = os.getenv("ASSISTANT_EMBEDDER", "ollama")  # ollama | tfidf
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# ---------------------------------------------------------------------------
# Model pool.
# Each entry: which backend model plays this "specialist", and its per-intent
# accuracy estimate (0-1), relative cost (0-1, higher = more expensive) and
# relative latency (0-1, higher = slower).  Accuracy figures are the team's
# published priors; they can be replaced by measured values from results/.
# ---------------------------------------------------------------------------
MODEL_POOL = {
    "GPT": {
        "ollama": "qwen2.5-coder:3b",
        "openai": "gpt-4o",
        "accuracy": {"coding": 0.95, "writing": 0.85, "search": 0.70, "reasoning": 0.90, "multimodal": 0.80},
        "cost": 0.60,
        "latency": 0.50,
    },
    "Claude": {
        "ollama": "llama3.2:3b",
        "anthropic": "claude-sonnet-4-5",
        "accuracy": {"coding": 0.90, "writing": 0.96, "search": 0.72, "reasoning": 0.94, "multimodal": 0.78},
        "cost": 0.65,
        "latency": 0.55,
    },
    "Gemini": {
        "ollama": "moondream",
        "gemini": "gemini-2.0-flash",
        "accuracy": {"coding": 0.80, "writing": 0.80, "search": 0.78, "reasoning": 0.82, "multimodal": 0.96},
        "cost": 0.45,
        "latency": 0.45,
    },
    "Sonar": {
        "ollama": "llama3.2:1b",
        "openai": "gpt-4o-mini",  # stand-in when using cloud APIs
        "accuracy": {"coding": 0.55, "writing": 0.60, "search": 0.95, "reasoning": 0.60, "multimodal": 0.50},
        "cost": 0.20,
        "latency": 0.20,
    },
}

# Scoring weights: score = w_a*acc + w_c*(1-cost) + w_l*(1-latency)
DEFAULT_WEIGHTS = {"accuracy": 0.6, "cost": 0.2, "latency": 0.2}

# ---------------------------------------------------------------------------
# Memory (Model B)
# ---------------------------------------------------------------------------
MEMORY_DB = os.getenv("ASSISTANT_MEMORY_DB", str(ROOT / "memory.db"))
MEMORY_TOP_K = 5
SESSION_SUMMARY_EVERY = 6  # turns

# ---------------------------------------------------------------------------
# RAG (Model C)
# ---------------------------------------------------------------------------
CORPUS_DIR = DATA_DIR / "corpus"
INDEX_PATH = MODELS_DIR / "rag_index.pkl"
CHUNK_WORDS = 120
CHUNK_OVERLAP = 30
RAG_TOP_K = 4
RAG_MIN_SIM = 0.15
