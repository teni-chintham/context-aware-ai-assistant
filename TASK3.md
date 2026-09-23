# Task 3: screenshots of the new comparison tabs

`app.py` now has five tabs: Chat, Compare models, Compare A/B/C/D, Results, vs Perplexity. Chat uses a text box with a **Send** button, and the variant picker is a radio at the top of the Chat tab.

1. Start `streamlit run app.py --server.headless true --server.port 8501` with Ollama running.
2. If any screenshot from TASK2 step 3 is missing or was taken on the old layout, retake it on the new one.
3. Using the same Playwright approach at 1440x900 (full page where a tab is tall), save these to `docs/screenshots/`:
   - `07_compare_models_coding.png`: Compare models tab, example "Coding", click **Run on all models**. Wait for all 4 answers.
   - `08_compare_models_search.png`: same, with example "Search".
   - `09_compare_variants_memory.png`: Compare A/B/C/D tab, question "Where do I work?", then **Run through baseline, A, B, C, D**. Wait for all 5.
   - `10_compare_variants_rag.png`: same, with "Who chairs the Helix board?".
   - `11_results_tab.png`: Results tab, full page.
   - `12_vs_perplexity.png`: vs Perplexity tab.
4. Look at every image and retake any that are blank or still show a spinner. Stop Streamlit.
5. Commit and push to the existing GitHub repo: `git add -A && git commit -m "Comparison tabs and screenshots" && git push`.
6. Append the list of screenshots and the push result to `.runlogs/task2_status.md`, then print `=== TASK3 DONE`.
