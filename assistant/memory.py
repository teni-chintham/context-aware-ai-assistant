"""Model B: persistent, benchmarked memory.

Three tiers, all in one SQLite file so it survives restarts:
  1. conversation turns   (short-term, per session)
  2. session summaries    (medium-term, one per session)
  3. user facts           (long-term, extracted from what the user states)

Recall = embed the new query, cosine-rank stored facts + summaries, inject
the top-k above a similarity floor into the system prompt.
"""
from __future__ import annotations

import re
import sqlite3
import time
from dataclasses import dataclass

import numpy as np

from . import config, providers

_FIRST_PERSON = re.compile(
    r"\b(my|i am|i'm|i use|i like|i love|i prefer|i have|i've|i work|i live|i study|i want|i need|"
    r"i hate|i don't|i dont|call me|remember that|note that|i was born|i usually|i always|i never)\b",
    re.I,
)


@dataclass
class MemoryHit:
    kind: str  # fact | summary
    text: str
    score: float


class Memory:
    def __init__(self, db_path: str | None = None, user_id: str = "default", embedder: str | None = None):
        # check_same_thread=False: Streamlit runs every rerun on a fresh thread while the
        # Assistant (and this connection) lives in st.session_state, so the connection
        # legitimately outlives the thread that created it.  CPython's sqlite3 is built in
        # serialized threading mode, so sharing one connection this way is safe.
        self.db = sqlite3.connect(db_path or config.MEMORY_DB, check_same_thread=False)
        self.user_id = user_id
        self.embedder = embedder
        self._init()

    # ------------------------------------------------------------------ schema
    def _init(self):
        c = self.db.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS turns(
            id INTEGER PRIMARY KEY, user_id TEXT, session_id TEXT, role TEXT, content TEXT, ts REAL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS facts(
            id INTEGER PRIMARY KEY, user_id TEXT, session_id TEXT, text TEXT UNIQUE, emb BLOB, ts REAL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS summaries(
            id INTEGER PRIMARY KEY, user_id TEXT, session_id TEXT, text TEXT, emb BLOB, ts REAL)""")
        self.db.commit()

    # ------------------------------------------------------------------ write
    def add_turn(self, session_id: str, role: str, content: str):
        self.db.execute("INSERT INTO turns(user_id,session_id,role,content,ts) VALUES(?,?,?,?,?)",
                        (self.user_id, session_id, role, content, time.time()))
        self.db.commit()
        if role == "user":
            for fact in extract_facts(content):
                self.add_fact(fact, session_id)
        n = self.db.execute("SELECT COUNT(*) FROM turns WHERE session_id=?", (session_id,)).fetchone()[0]
        if n % config.SESSION_SUMMARY_EVERY == 0:
            self.summarize_session(session_id)

    def add_fact(self, text: str, session_id: str = "manual"):
        text = text.strip()
        if not text:
            return
        emb = providers.embed([text], self.embedder)[0]
        try:
            self.db.execute("INSERT INTO facts(user_id,session_id,text,emb,ts) VALUES(?,?,?,?,?)",
                            (self.user_id, session_id, text, emb.tobytes(), time.time()))
            self.db.commit()
        except sqlite3.IntegrityError:
            pass  # already known

    def summarize_session(self, session_id: str):
        rows = self.db.execute("SELECT role, content FROM turns WHERE session_id=? ORDER BY id",
                               (session_id,)).fetchall()
        # summarise what the user TOLD us (statements), not what they asked
        user_lines = [c.split(".")[0][:120] for r, c in rows if r == "user" and not c.strip().endswith("?")]
        if not user_lines:
            return
        text = f"Earlier session: user said " + "; ".join(user_lines[-8:])
        emb = providers.embed([text], self.embedder)[0]
        self.db.execute("DELETE FROM summaries WHERE session_id=?", (session_id,))
        self.db.execute("INSERT INTO summaries(user_id,session_id,text,emb,ts) VALUES(?,?,?,?,?)",
                        (self.user_id, session_id, text, emb.tobytes(), time.time()))
        self.db.commit()

    # ------------------------------------------------------------------ read
    def recent_turns(self, session_id: str, n: int = 8) -> list[dict]:
        rows = self.db.execute("SELECT role, content FROM turns WHERE session_id=? ORDER BY id DESC LIMIT ?",
                               (session_id, n)).fetchall()
        return [{"role": r, "content": c} for r, c in reversed(rows)]

    def recall(self, query: str, top_k: int = config.MEMORY_TOP_K, min_sim: float = 0.05) -> list[MemoryHit]:
        rows = [("fact", t, e) for t, e in self.db.execute(
            "SELECT text, emb FROM facts WHERE user_id=?", (self.user_id,))]
        rows += [("summary", t, e) for t, e in self.db.execute(
            "SELECT text, emb FROM summaries WHERE user_id=?", (self.user_id,))]
        if not rows:
            return []
        q = providers.embed([query], self.embedder)[0]
        M = np.stack([np.frombuffer(e, dtype=np.float32) for _, _, e in rows])
        sims = M @ q
        order = np.argsort(-sims)[:top_k]
        return [MemoryHit(rows[i][0], rows[i][1], float(sims[i])) for i in order if sims[i] >= min_sim]

    def all_facts(self) -> list[str]:
        return [t for (t,) in self.db.execute("SELECT text FROM facts WHERE user_id=? ORDER BY id", (self.user_id,))]

    def clear(self):
        for t in ("turns", "facts", "summaries"):
            self.db.execute(f"DELETE FROM {t} WHERE user_id=?", (self.user_id,))
        self.db.commit()


def extract_facts(message: str) -> list[str]:
    """Rule-based extraction of durable first-person statements.

    Deterministic on purpose: the memory benchmark must be reproducible, and
    an LLM extractor would make the ablation depend on the generator's whims.
    """
    facts = []
    for sent in re.split(r"(?<=[.!?])\s+|\n", message):
        s = sent.strip()
        if len(s) < 8 or s.endswith("?"):
            continue
        if _FIRST_PERSON.search(s):
            s = re.sub(r"^(remember that|note that|by the way,?|btw,?)\s*", "", s, flags=re.I).strip()
            facts.append(s[0].upper() + s[1:])
    return facts
