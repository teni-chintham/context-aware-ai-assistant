# Presenting the Context-Aware AI Assistant (Review 2)

About 15 minutes: 10 minutes of slides and 4 of demo, plus questions. The speaker notes on each slide say what to cover.

## Who presents what

| Part | Slides | Presenter | Time |
|---|---|---|---|
| Problem, what changed since Review 1, vs Perplexity | 1–4 | Nischay | 3 min |
| Architecture, routing formula, ablation design, evaluation | 5–8 | Tejas | 3 min |
| Results: intent, ablation, hallucination finding, per-task benchmark | 9–15 | Teni | 4 min |
| Demo slides, live demo | 16–18 | Teni drives, Tejas narrates | 4 min |
| Limitations, next steps, questions | 19–20 | Nischay | 1 min |

Swap the names around as you like.

## Before the review (10 minutes, on Teni's Mac)

```bash
cd ~/coding/ai-assistant
source .venv/bin/activate
ollama serve &                 # skip if it's already running
streamlit run app.py
```

- **Warm up every model.** Open the **Compare models** tab and click **Run on all models** once. The first call to each model loads it into memory and takes 5 to 10 seconds; after that, answers take 1 to 5 seconds.
- **Wipe old memory.** In the **Chat** tab, click **Wipe memory** so the demo doesn't pick up earlier test data.
- **Leave the weights alone.** Keep the default sliders (0.60 / 0.20 / 0.20) until the step that changes them.
- **Close other apps.** The Mac has 8 GB of RAM, and Chrome plus Ollama is a tight fit.

## Live demo script (4 minutes)

1. **Chat tab, Model D.** Type *Write a Python function that reverses a linked list*.
   - Point to the intent (coding, 0.99) and the score table. The GPT role wins with 0.75.
2. **Same tab.** Type *Write a haiku about monsoon rain*. It routes to the Claude role.
   - Drag the **cost** slider to 1.0 and **accuracy** to 0.1, then ask again. It now routes to the Sonar role, because the formula is live.
   - Reset the sliders afterwards.
3. **Compare models tab.** Pick the **Coding** example and click **Run on all models**.
   - All four models answer side by side, with the router's pick highlighted.
   - Then pick **Search**.
4. **Compare A/B/C/D tab.** Choose *Where do I work?* and click **Run through…**.
   - Only B and D know the answer (PayLoop).
   - Then choose *Who chairs the Helix board?*. Only C and D know that one (Meera Iyer).
5. **vs Perplexity tab.** Show the comparison table as the closing point of the demo.

**If something breaks:** stay on the demo slides (16 and 17). They're real screenshots of the same steps.

## Numbers to know by heart

- **Intent accuracy:** 84.4% on unseen questions from the original dataset, and 93.3% on 150 new prompts.
  - By phrasing: 100% direct, 98% verbose, 82% casual.
- **Per-task benchmark:** the routed system got 84% of 50 tasks right.
  - The best single model got 78%.
  - The best possible choice per task type, known only in hindsight, gets 88%.
- **Ablation:** memory recall goes from 0% to 96.7% with memory.
  - Retrieval accuracy goes from 0% to 88.9% with RAG.
  - Hallucination is 52.8% for the baseline and 5.6% for Model D.
- **Surprise finding:** memory without retrieval (Model B) hallucinates 91.7% of the time.

## Likely questions

- **"Your Review 2 said 97%. Why is it 84% now?"**
  - The old split let paraphrases of test questions leak into training.
  - Splitting by the original question gives 84.4%. Put the same way, the leaky method now gives 100%, which proves the point.
- **"How is this different from Perplexity?"**
  - Perplexity has live web search and far bigger models, and we don't claim to beat it at search.
  - We publish the routing rule, show why every model was chosen, and measure what each component adds. Perplexity does none of these.
- **"Why small local models and not GPT or Claude?"**
  - The study is free and reproducible on a laptop.
  - Switching to the real APIs is a config change (`.env`), and we'll run them before the final review.
- **"Why does Model B hallucinate more than the baseline?"**
  - Earlier made-up answers stay in the chat history, and the model continues confidently instead of saying it doesn't know.
  - That's why memory needs retrieval beside it, which is what Model D does.
- **"In the demo, why did it say 'I do not know' for the capital of Australia?"**
  - Retrieval returned the closest company passages, and the strict "answer only from these" rule made the model refuse.
  - The fix, applying that rule only when the passages are actually relevant, is in our next steps.
- **"Is the grading fair?"**
  - Coding is graded by running unit tests, maths by the exact number, and writing by checkable rules such as line count or JSON keys.
  - Every answer is logged in `results/task_bench_raw.jsonl`, so anyone can check.
- **"Why does routing only help a bit (84% vs 78%)?"**
  - With small models, one of them (the coder) is strong at most text tasks.
  - The gain comes from sending images to the only vision model and keeping the vision model away from maths.
  - The spread between models is larger with big commercial models.

## Files

- Slides: the "Context-Aware AI Assistant: Review Deck" artifact. It can be downloaded as PPTX or PDF.
- Report: `docs/BCSE497J_Project_Report_Final.docx` (and `.pdf`).
- Code, data, every model answer and the run logs: the GitHub repo.
