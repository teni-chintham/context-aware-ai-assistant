"""Chunk + embed data/corpus into the RAG index (Model C)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from assistant import rag, config, providers

if config.EMBEDDER == "ollama" and not providers.ollama_available():
    sys.exit("Ollama is not running. Start it (ollama serve) or set ASSISTANT_EMBEDDER=tfidf")
print(rag.build_index(), "->", config.INDEX_PATH)
