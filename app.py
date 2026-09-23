"""Streamlit demo.

Tabs
  Chat               talk to any variant, inspect every decision
  Compare models     one prompt -> every model in the pool, side by side; the router's pick is highlighted
  Compare A/B/C/D    one question -> baseline, A, B, C, D (shared memory profile + document index)
  Results            the ablation and per-task benchmark numbers from results/
  vs Perplexity      what this project does differently
"""
import json
import sys
import tempfile
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assistant import config, providers  # noqa: E402
from assistant.intent import IntentClassifier  # noqa: E402
from assistant.pipeline import BASE_SYSTEM, VARIANTS, Assistant  # noqa: E402
from assistant.router import route  # noqa: E402

st.set_page_config(page_title="Context-Aware AI Assistant", layout="wide")
st.title("Context-Aware Personal AI Assistant")
st.caption("Dynamic routing + persistent memory + RAG, with every decision visible")

VARIANT_NAMES = {"A": "Model A: routing only", "B": "Model B: memory only", "C": "Model C: RAG only",
                 "D": "Model D: full system", "baseline": "Baseline: fixed model, nothing else"}

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Configuration")
    provider = st.selectbox("Provider", ["ollama", "mock", "openai", "anthropic", "gemini"],
                            index=["ollama", "mock", "openai", "anthropic", "gemini"].index(config.PROVIDER))
    embedder = st.selectbox("Embedder", ["ollama", "tfidf"], index=["ollama", "tfidf"].index(config.EMBEDDER))
    st.subheader("Routing weights")
    wa = st.slider("accuracy", 0.0, 1.0, config.DEFAULT_WEIGHTS["accuracy"], 0.05)
    wc = st.slider("cost", 0.0, 1.0, config.DEFAULT_WEIGHTS["cost"], 0.05)
    wl = st.slider("latency", 0.0, 1.0, config.DEFAULT_WEIGHTS["latency"], 0.05)
    weights = {"accuracy": wa, "cost": wc, "latency": wl}
    image = st.file_uploader("Image (multimodal)", type=["png", "jpg", "jpeg"])
    if provider == "ollama":
        st.write("Ollama:", "running" if providers.ollama_available() else "NOT running")
    st.caption("Model pool: " + ", ".join(f"{k} = {v.get(provider, v['ollama'])}" for k, v in config.MODEL_POOL.items()))


def save_upload():
    if not image:
        return None
    p = config.RESULTS_DIR / f"upload_{image.name}"
    p.write_bytes(image.getvalue())
    return str(p)


@st.cache_resource
def classifier():
    return IntentClassifier()


tab_chat, tab_models, tab_variants, tab_results, tab_pplx = st.tabs(
    ["Chat", "Compare models", "Compare A/B/C/D", "Results", "vs Perplexity"])

# ================================================================ Chat
with tab_chat:
    variant = st.radio("Variant", ["D", "A", "B", "C", "baseline"], format_func=VARIANT_NAMES.get, horizontal=True)
    c1, c2 = st.columns([1, 1])
    if c1.button("New session"):
        st.session_state.pop("assistant", None)
        st.session_state.history = []
    if c2.button("Wipe memory"):
        Assistant.variant("B", embedder=embedder).memory.clear()
        st.success("memory cleared")
    key = (variant, provider, embedder, json.dumps(weights))
    if st.session_state.get("key") != key or "assistant" not in st.session_state:
        st.session_state.assistant = Assistant.variant(variant, provider=provider, embedder=embedder, weights=weights)
        st.session_state.key = key
        st.session_state.history = []
    a: Assistant = st.session_state.assistant

    col_chat, col_inspect = st.columns([3, 2])
    with col_chat:
        for m in st.session_state.history:
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
        with st.form("chat", clear_on_submit=True):
            q = st.text_input("Ask something", key="chat_q")
            sent = st.form_submit_button("Send")
        if sent and q:
            with st.spinner("thinking"):
                try:
                    r = a.chat(q, image=save_upload())
                except Exception as e:
                    st.error(str(e)); st.stop()
            st.session_state.history += [{"role": "user", "content": q},
                                         {"role": "assistant", "content": f"{r.answer}\n\n*{r.model} · {r.latency_s}s*"}]
            st.session_state.last = r
            st.rerun()
    with col_inspect:
        st.subheader("Inspector")
        r = st.session_state.get("last")
        if not r:
            st.info("Ask something to see the routing, memory and retrieval decisions.")
        else:
            if r.intent:
                st.markdown(f"**Intent:** `{r.intent.intent}` ({r.intent.confidence:.2f})")
                st.bar_chart(r.intent.probs)
            if r.decision:
                st.markdown(f"**Routed to:** `{r.decision.chosen}`")
                st.markdown("score = w_a·acc + w_c·(1−cost) + w_l·(1−latency)")
                st.dataframe({m: {**r.decision.breakdown[m], "total": r.decision.scores[m]} for m in r.decision.scores})
            else:
                st.markdown(f"**Fixed model:** `{r.model}` (routing off)")
            if a.use_memory:
                st.markdown(f"**Memory hits:** {len(r.memory_hits)}")
                for h in r.memory_hits:
                    st.write(f"- ({h.kind}, {h.score:.2f}) {h.text}")
                with st.expander("All stored facts"):
                    st.write(a.memory.all_facts())
            if a.use_rag:
                st.markdown(f"**Retrieved passages:** {len(r.passages)}")
                for k, p in enumerate(r.passages, 1):
                    with st.expander(f"[{k}] {p.doc}  sim={p.score:.2f}"):
                        st.write(p.text)
            with st.expander("System prompt sent to the model"):
                st.code(r.system_prompt)

# ================================================================ Compare models
with tab_models:
    st.markdown("Send **one prompt to every model in the pool** and see how each answers. "
                "The router's choice is highlighted, with the score that picked it.")
    examples = {"Coding": "Write a Python function is_prime(n) that returns True if n is prime.",
                "Writing": "Write a haiku about monsoon rain. Output only the three lines.",
                "Search": "What is the capital city of Australia?",
                "Reasoning": "A shirt costs 800 rupees after a 20% discount. What was the original price? End with 'Answer: <number>'.",
                "Multimodal": "Describe what is in this image."}
    ex = st.selectbox("Example prompt", ["(type your own)"] + list(examples))
    prompt = st.text_area("Prompt", value=examples.get(ex, ""), height=90, key=f"cmp_prompt_{ex}")
    if st.button("Run on all models", type="primary") and prompt:
        img = save_upload()
        p = classifier().predict(prompt)
        intent = "multimodal" if img else p.intent
        d = route(intent, weights)
        st.markdown(f"**Intent:** `{intent}` ({p.confidence:.2f}) → **router picks `{d.chosen}`**")
        cols = st.columns(len(config.MODEL_POOL))
        for col, m in zip(cols, config.MODEL_POOL):
            with col:
                picked = m == d.chosen
                st.markdown(f"### {'✅ ' if picked else ''}{m}")
                st.caption(f"{config.MODEL_POOL[m].get(provider, config.MODEL_POOL[m]['ollama'])} · score {d.scores[m]:.3f}")
                with st.spinner("generating"):
                    try:
                        ans, secs = providers.generate(m, BASE_SYSTEM, [{"role": "user", "content": prompt}],
                                                       image=img, backend=provider)
                    except Exception as e:
                        ans, secs = f"⚠️ {e}", 0
                if picked:
                    st.success(ans)
                else:
                    st.markdown(ans)
                st.caption(f"{secs}s")
        st.dataframe({m: {**d.breakdown[m], "total": d.scores[m]} for m in d.scores})

# ================================================================ Compare variants
DEFAULT_PROFILE = ("My name is Arjun and I work at PayLoop as a data engineer.\n"
                   "I live in Koramangala, Bangalore.\nI am allergic to peanuts.\nMy favourite language is Rust.")
with tab_variants:
    st.markdown("Ask **one question through all five builds**. Every build shares the same user profile "
                "(stored in memory for the builds that have memory) and the same document index (used by the builds with RAG).")
    profile = st.text_area("What the user told the assistant in earlier sessions", DEFAULT_PROFILE, height=110)
    vq_examples = ["Where do I work?", "Who chairs the Helix board?", "What is the rated payload of the Orbit 2?",
                   "Write a Python function that reverses a string."]
    vq = st.selectbox("Question", vq_examples + ["(type your own)"])
    if vq == "(type your own)":
        vq = st.text_input("Your question", key="vq_own")
    if st.button("Run through baseline, A, B, C, D", type="primary") and vq:
        db = str(Path(tempfile.mkdtemp()) / "cmp.db")
        cols = st.columns(5)
        for col, v in zip(cols, ["baseline", "A", "B", "C", "D"]):
            with col:
                fl = VARIANTS[v]
                st.markdown(f"#### {VARIANT_NAMES[v].split(':')[0]}")
                st.caption(" · ".join(f"{k} {'on' if fl[k] else 'off'}" for k in ("routing", "memory", "rag")))
                with st.spinner("running"):
                    try:
                        av = Assistant.variant(v, provider=provider, embedder=embedder, weights=weights,
                                               memory_db=db, user_id=f"cmp-{v}")
                        if av.memory:
                            av.memory.clear()
                            for line in profile.splitlines():
                                if line.strip():
                                    av.memory.add_turn("profile", "user", line.strip())
                            av.new_session()
                        t0 = time.time()
                        r = av.chat(vq)
                        st.markdown(r.answer)
                        st.caption(f"model {r.model} · {len(r.memory_hits)} memory hits · {len(r.passages)} passages · {time.time() - t0:.1f}s")
                    except Exception as e:
                        st.error(str(e))

# ================================================================ Results
with tab_results:
    R = config.RESULTS_DIR
    if (R / "ablation.json").exists():
        ab = json.loads((R / "ablation.json").read_text())
        st.subheader(f"Ablation study ({ab['provider']})")
        st.dataframe({VARIANT_NAMES[k]: {"memory recall": e.get("memory", {}).get("recall_accuracy"),
                                         "RAG accuracy": e.get("rag", {}).get("accuracy"),
                                         "hallucination": e.get("rag", {}).get("hallucination_rate"),
                                         "abstain": e.get("rag", {}).get("abstention_rate")}
                      for k, e in ab["variants"].items()})
        for f in ["ablation.png", "routing_gain.png"]:
            if (R / f).exists():
                st.image(str(R / f))
    if (R / "task_bench.json").exists():
        tb = json.loads((R / "task_bench.json").read_text())
        st.subheader(f"Per-task benchmark: {tb['n_tasks']} tasks, {tb['n_prompts']} prompts")
        st.markdown(f"Intent routing accuracy: **{tb['routing']['text_only_accuracy']:.1%}** "
                    f"(by phrasing: {', '.join(f'{k} {v:.0%}' for k, v in tb['routing']['by_style'].items())})")
        st.dataframe(tb["accuracy_by_model_intent"])
        st.dataframe({k: {"tasks correct": v} for k, v in tb["systems"].items()})
        for f in ["tb_accuracy_heatmap.png", "tb_systems.png", "tb_confusion.png", "tb_phrasing.png"]:
            if (R / f).exists():
                st.image(str(R / f))
    if not (R / "ablation.json").exists():
        st.info("Run scripts/run_ablation.py and scripts/run_task_bench.py to fill this tab.")

# ================================================================ vs Perplexity
with tab_pplx:
    st.subheader("How this project differs from Perplexity")
    st.markdown("""
Perplexity is a production answer engine that already combines model routing, memory and retrieval with citations.
This project does **not** claim to be bigger or better at search. It claims to be **transparent and measured**.

| | Perplexity | This project |
|---|---|---|
| Routing rule | Undisclosed | Published formula: `w_a·accuracy + w_c·(1−cost) + w_l·(1−latency)` |
| Why a model was chosen | Not shown | Every decision shows intent probabilities and each model's score |
| Control | Pick a model by hand, or let the product choose | Adjust the weights live; the decision changes |
| Scope | Search-style question answering | Coding, writing, reasoning, search and images, each routed separately |
| Memory | Personalisation, not benchmarked publicly | Three-tier memory with a recall benchmark (30 questions, 4 sessions) |
| Evidence | No published ablation | Ablation (baseline/A/B/C/D) + 50-task benchmark, every answer logged |
| Retrieval source | Live web | Your own documents (local index); web search is future work |
| Models | Large commercial models | Any provider: local Ollama models here, cloud APIs by config |
| Runs offline / free | No | Yes |

**Where Perplexity is stronger:** live web search, far larger models, production scale and reliable citations.
**Where this project adds something:** it shows *why* each model was chosen and *how much* each component contributes.
""")
