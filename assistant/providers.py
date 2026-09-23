"""LLM + embedding providers.

generate(model_key, system, messages) -> text
embed(texts) -> list[list[float]]

Backends: ollama (default), openai, anthropic, gemini, mock.
All cloud calls use plain HTTPS via requests so no vendor SDK is required.
"""
from __future__ import annotations

import base64
import os
import re
import time
from pathlib import Path

import numpy as np
import requests

from . import config

try:  # optional .env support
    from dotenv import load_dotenv
    load_dotenv(config.ROOT / ".env")
except Exception:  # pragma: no cover
    pass


class ProviderError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def _backend_model(model_key: str, backend: str) -> str:
    entry = config.MODEL_POOL[model_key]
    if backend in entry:
        return entry[backend]
    # cloud backends: fall back to whatever cloud model this key defines
    for b in ("openai", "anthropic", "gemini"):
        if b in entry:
            return entry[b]
    return entry["ollama"]


def _ollama_generate(model: str, system: str, messages: list[dict], image: str | None) -> str:
    msgs = [{"role": "system", "content": system}] + messages
    if image and msgs:
        msgs[-1] = dict(msgs[-1], images=[_b64(image)])
    r = requests.post(
        f"{config.OLLAMA_HOST}/api/chat",
        json={"model": model, "messages": msgs, "stream": False, "options": {"temperature": 0.1}},
        timeout=600,
    )
    if r.status_code != 200:
        raise ProviderError(f"Ollama {r.status_code}: {r.text[:300]}")
    return r.json()["message"]["content"].strip()


def _openai_generate(model: str, system: str, messages: list[dict], image=None) -> str:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ProviderError("OPENAI_API_KEY not set")
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": model, "messages": [{"role": "system", "content": system}] + messages, "temperature": 0.1},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def _anthropic_generate(model: str, system: str, messages: list[dict], image=None) -> str:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise ProviderError("ANTHROPIC_API_KEY not set")
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
        json={"model": model, "system": system, "messages": messages, "max_tokens": 1024, "temperature": 0.1},
        timeout=120,
    )
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json()["content"]).strip()


def _gemini_generate(model: str, system: str, messages: list[dict], image=None) -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise ProviderError("GEMINI_API_KEY not set")
    contents = [
        {"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]} for m in messages
    ]
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        json={"systemInstruction": {"parts": [{"text": system}]}, "contents": contents},
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


def _mock_generate(model: str, system: str, messages: list[dict], image=None) -> str:
    """Deterministic stand-in used by tests and offline smoke runs.

    It answers only from context the pipeline injected (memory facts or
    retrieved passages).  With no usable context it says it does not know.
    This mimics a well-behaved grounded model, so the ablation harness can be
    exercised end-to-end without any LLM running.
    """
    question = messages[-1]["content"].lower()
    q_words = set(re.findall(r"[a-z0-9]+", question)) - _STOP
    best, best_overlap, best_cite = None, 0, ""
    for line in system.splitlines():
        line = line.strip(" -•")
        if not line or line.endswith(":") or line.lower().startswith(("you are", "rules", "if the", "cite", "answer")):
            continue
        cite = ""
        m = re.match(r"(\[\d+\]) \([^)]*\) ", line)
        if m:
            cite, line = m.group(1) + " ", line[m.end():]
        for sent in re.split(r"(?<=[.!?])\s+", line):
            words = set(re.findall(r"[a-z0-9]+", sent.lower())) - _STOP
            overlap = len(q_words & words)
            if overlap > best_overlap:
                best, best_overlap, best_cite = sent, overlap, cite
    if best and best_overlap >= 1:
        return best_cite + best
    return "I don't have that information in my context."


_STOP = set("the a an is are was were of to in on for and or what which who how do does did my me i you your it this that with at by from as be can please tell about".split())

_GENERATORS = {
    "ollama": _ollama_generate,
    "openai": _openai_generate,
    "anthropic": _anthropic_generate,
    "gemini": _gemini_generate,
    "mock": _mock_generate,
}


def generate(model_key: str, system: str, messages: list[dict], image: str | None = None,
             backend: str | None = None) -> tuple[str, float]:
    """Returns (text, seconds)."""
    backend = backend or config.PROVIDER
    fn = _GENERATORS[backend]
    model = _backend_model(model_key, backend) if backend != "mock" else "mock"
    t0 = time.time()
    text = fn(model, system, messages, image)
    return text, round(time.time() - t0, 3)


def _b64(path: str) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode()


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------
_hash_vec = None


def _tfidf_embed(texts: list[str]) -> np.ndarray:
    """Fit-free lexical embedding (hashed char n-grams, L2 normed)."""
    global _hash_vec
    from sklearn.feature_extraction.text import HashingVectorizer
    if _hash_vec is None:
        _hash_vec = HashingVectorizer(analyzer="char_wb", ngram_range=(3, 5), n_features=2 ** 18, norm="l2",
                                      alternate_sign=False)
    return _hash_vec.transform(texts).toarray().astype(np.float32)


def _ollama_embed(texts: list[str]) -> np.ndarray:
    r = requests.post(f"{config.OLLAMA_HOST}/api/embed",
                      json={"model": config.OLLAMA_EMBED_MODEL, "input": texts}, timeout=300)
    if r.status_code != 200:
        raise ProviderError(f"Ollama embed {r.status_code}: {r.text[:300]}")
    v = np.array(r.json()["embeddings"], dtype=np.float32)
    v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-9
    return v


def embed(texts: list[str], embedder: str | None = None) -> np.ndarray:
    embedder = embedder or config.EMBEDDER
    if embedder == "ollama":
        return _ollama_embed(texts)
    return _tfidf_embed(texts)


def ollama_available() -> bool:
    try:
        return requests.get(f"{config.OLLAMA_HOST}/api/tags", timeout=2).status_code == 200
    except Exception:
        return False
