# Task for Claude Code: get the ablation running on this Mac

You are in `~/coding/ai-assistant`, the BCSE497J Project-I codebase (Context-Aware Personal AI Assistant: routing + memory + RAG, ablation Models A/B/C/D). Read README.md first. Another Claude session is watching this Terminal through screenshots and will write the report from your outputs, so keep terminal output readable and keep RUN_LOG.md current.

## Steps

1. **Check the environment.** Run `python3 --version` (need 3.10+), `ollama --version`, `sysctl -n hw.memsize`, and `df -h ~`. If Ollama isn't running, start it in the background with `ollama serve`.
2. **Setup.** Run `bash setup.sh`. The model pulls total about 15 GB.
   - If RAM is 8 GB, or disk has less than 20 GB free, edit `assistant/config.py` and setup.sh. Use smaller models: `qwen2.5-coder:3b`, `llama3.2:3b`, `moondream` for vision, `llama3.2:1b` for Sonar. Record the change in RUN_LOG.md.
3. **Offline tests.** Run `ASSISTANT_PROVIDER=mock ASSISTANT_EMBEDDER=tfidf python -m pytest -q tests`. All must pass.
4. **Smoke run on Ollama.** Run `python scripts/run_ablation.py --variants baseline D --limit 5`. Fix anything that breaks, such as timeouts, model names or Ollama errors.
5. **Full ablation.** Run `python scripts/run_ablation.py`. Expect 20 to 60 minutes. Do not interrupt it.
6. **Demo check.** Run `streamlit run app.py --server.headless true` for about 20 seconds, confirm it starts without errors, then stop it.
7. **Write RUN_LOG.md.** Include:
   - machine specs and the models actually used
   - the final intent metrics from results/intent_metrics.json
   - the full ablation table from results/ablation.csv
   - routing gain
   - every error you hit and how you fixed it
   - total run time

## Rules

- Never edit files in `data/eval/`, `data/corpus/` or `data/intents.csv`, and never edit the gold answers or scoring logic to improve numbers. The results must be honest. If a number looks bad, report it; don't tune it away.
- Code fixes for crashes, timeouts or compatibility are fine. Log each one in RUN_LOG.md.
- After each step, print a one-line status: `=== STEP n DONE: <result>` or `=== STEP n FAILED: <reason>`.
- If blocked for more than 3 attempts on the same error, stop and print `=== BLOCKED: <reason>`.
