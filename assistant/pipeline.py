"""One pipeline, three switches.  The switches ARE the ablation.

    Assistant(routing=True,  memory=False, rag=False)  -> Model A
    Assistant(routing=False, memory=True,  rag=False)  -> Model B
    Assistant(routing=False, memory=False, rag=True)   -> Model C
    Assistant(routing=True,  memory=True,  rag=True)   -> Model D

Flow per query:
    classify intent (if routing) -> score + pick model (if routing, else fixed)
    -> recall memory (if memory) -> retrieve passages (if rag)
    -> build system prompt -> generate -> store turn (if memory)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from . import config, providers
from .intent import IntentClassifier, IntentResult
from .memory import Memory, MemoryHit
from .rag import Passage, Retriever, format_context
from .router import RouteDecision, route

VARIANTS = {
    "A": dict(routing=True, memory=False, rag=False),
    "B": dict(routing=False, memory=True, rag=False),
    "C": dict(routing=False, memory=False, rag=True),
    "D": dict(routing=True, memory=True, rag=True),
    "baseline": dict(routing=False, memory=False, rag=False),
}

FIXED_MODEL = "GPT"  # what a non-routing variant always uses

BASE_SYSTEM = (
    "You are a helpful personal assistant. Answer concisely and directly. "
    "If the answer is not known from the conversation or the provided context, say you do not know "
    "rather than guessing."
)


@dataclass
class Response:
    answer: str
    model: str
    intent: IntentResult | None
    decision: RouteDecision | None
    memory_hits: list[MemoryHit]
    passages: list[Passage]
    latency_s: float
    system_prompt: str = field(repr=False, default="")


class Assistant:
    def __init__(self, routing: bool, memory: bool, rag: bool, *, weights=None, provider=None, embedder=None,
                 memory_db=None, user_id="default", fixed_model=FIXED_MODEL):
        self.routing, self.use_memory, self.use_rag = routing, memory, rag
        self.weights = weights or config.DEFAULT_WEIGHTS
        self.provider = provider
        self.fixed_model = fixed_model
        self.clf = IntentClassifier() if routing else None
        self.memory = Memory(memory_db, user_id=user_id, embedder=embedder) if memory else None
        self.retriever = Retriever() if rag else None
        self.session_id = uuid.uuid4().hex[:8]

    @classmethod
    def variant(cls, name: str, **kw) -> "Assistant":
        return cls(**VARIANTS[name], **kw)

    def new_session(self):
        self.session_id = uuid.uuid4().hex[:8]

    def chat(self, query: str, image: str | None = None) -> Response:
        intent = decision = None
        model = self.fixed_model
        if self.routing:
            intent = self.clf.predict(query)
            if image and intent.intent != "multimodal":
                intent = IntentResult("multimodal", 1.0, {**intent.probs, "multimodal": 1.0})
            decision = route(intent.intent, self.weights)
            model = decision.chosen

        hits = self.memory.recall(query) if self.use_memory else []
        passages = self.retriever.retrieve(query) if self.use_rag else []

        system = self._system_prompt(hits, passages)
        history = self.memory.recent_turns(self.session_id) if self.use_memory else []
        messages = history + [{"role": "user", "content": query}]

        answer, secs = providers.generate(model, system, messages, image=image, backend=self.provider)

        if self.use_memory:
            self.memory.add_turn(self.session_id, "user", query)
            self.memory.add_turn(self.session_id, "assistant", answer)

        return Response(answer, model, intent, decision, hits, passages, secs, system)

    def _system_prompt(self, hits: list[MemoryHit], passages: list[Passage]) -> str:
        parts = [BASE_SYSTEM]
        if hits:
            parts.append("What you remember about this user:\n" + "\n".join(f"- {h.text}" for h in hits))
        if passages:
            parts.append(
                "Retrieved context. Answer ONLY from it and cite passages as [1], [2] etc. "
                "If it does not contain the answer, say so.\n" + format_context(passages)
            )
        return "\n\n".join(parts)
