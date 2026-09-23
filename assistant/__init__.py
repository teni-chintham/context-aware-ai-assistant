"""Context-Aware Personal AI Assistant.

Four ablation variants share one pipeline (see pipeline.Assistant):
  Model A  routing only
  Model B  memory only
  Model C  RAG only
  Model D  routing + memory + RAG
"""
from .pipeline import Assistant, VARIANTS  # noqa: F401
