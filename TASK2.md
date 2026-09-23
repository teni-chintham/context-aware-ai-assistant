# Task 2 for Claude Code: per-task benchmark, demo screenshots, GitHub push

You are in `~/coding/ai-assistant`. TASK.md is done (see RUN_LOG.md). Ollama and the small-model pool are already set up. Use `.venv`.

Another Claude session reads your output files to build the final report and slides. It checks the files, not this terminal, so **write every result to the paths below**.

## Steps

1. **Tests.**
   - Run `source .venv/bin/activate && ASSISTANT_PROVIDER=mock ASSISTANT_EMBEDDER=tfidf python -m pytest -v tests 2>&1 | tee .runlogs/pytest.txt`.
   - All 10 must pass. Grader tests are new.
2. **Per-task benchmark.**
   - Make sure `ollama serve` is running.
   - Run `python scripts/make_task_images.py`.
   - Smoke run: `python scripts/run_task_bench.py --limit 1 --fresh 2>&1 | tee .runlogs/task_bench_smoke.txt`.
   - Fix crashes only.
   - Full run: `python scripts/run_task_bench.py --fresh 2>&1 | tee .runlogs/task_bench.txt`. This is about 200 model calls. Don't interrupt it. It resumes from `results/task_bench_raw.jsonl` if restarted without `--fresh`.
   - Look at 10 random rows of `results/task_bench_raw.jsonl`. If a correct answer was graded wrong (or the reverse) because of a **grader bug**, fix the grader, re-grade from the cached answers (no `--fresh`), and log it.
   - Never change task prompts or expected answers to lift scores.
3. **Demo screenshots.**
   - Start `streamlit run app.py --server.headless true --server.port 8501` in the background.
   - Use Playwright in Python (`pip install playwright && python -m playwright install chromium`; fall back to macOS `screencapture` on a Safari window if that fails).
   - Capture 1440x900 PNGs into `docs/screenshots/`, with the Inspector panel visible:
     - `01_coding_routing.png`: variant "Model D", ask *Write a Python function that reverses a linked list*. Show the intent probabilities and the score table.
     - `02_search_routing.png`: ask *What is the capital of Australia?* It should route to Sonar.
     - `03_memory.png`: say *My name is Arjun and I work at PayLoop as a data engineer.*, click **New session**, then ask *Where do I work?* Show the memory hits.
     - `04_rag.png`: ask *Who chairs the Helix board?* Expand the retrieved passages.
     - `05_writing_routing.png`: ask *Write a haiku about monsoon rain*.
     - `06_weights.png`: set the cost weight to 1.0 and accuracy to 0.1, then ask the haiku again. Show that the routed model changes. Skip this one if the sliders can't be automated, and note it.
   - Look at each image. Retake any that are blank, cut off or show an error. Then stop Streamlit.
4. **GitHub.**
   - Check `gh auth status`. If it isn't logged in, stop and print `=== BLOCKED: run gh auth login`.
   - Otherwise run `git init` (if needed) and commit everything not ignored by `.gitignore`. That includes `results/` and `docs/`, but no `.venv`, model weights or `memory.db`.
   - Create a **private** repo named `context-aware-ai-assistant` with `gh repo create context-aware-ai-assistant --private --source . --push`.
   - Never make it public.
   - Commit message: `Context-aware AI assistant: routing, memory, RAG, ablation and per-task benchmark`.
5. **Status file.** Write `.runlogs/task2_status.md` with:
   - pass/fail for each step
   - the repo URL
   - the list of screenshots
   - every grader fix
   - the benchmark summary printed at the end of step 2

   Also append a "Task 2" section to RUN_LOG.md.

After each step, print `=== STEP n DONE: ...` or `=== STEP n FAILED: ...`.
