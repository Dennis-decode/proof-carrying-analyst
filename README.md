# Proof-Carrying Data Analyst (Agentic GenAI)

An AI agent that answers questions about **messy, multi-table business data** and attaches a **re-runnable Python script as proof** for every number. If the data cannot support a reliable answer, it **refuses and explains why**.

Team: _<write your 4 names here>_

## 1. What the project does
1. Loads 4 messy files (`orders.csv`, `customers.csv`, `refunds.csv`, `rates.csv`) plus business rules (`policy.txt`).
2. **Cleans** them with plain Python (no AI) and keeps a log of every issue: duplicates, EUR/USD mix, ambiguous dates, missing values, contradictions between tables.
3. **Plans**: an LLM decides if the question is `answerable`, `unanswerable` (missing column / out-of-range / non-existent entity) or `ambiguous`.
4. **Writes code**: the LLM writes a pandas script; the number comes from running the script, never from the LLM's head.
5. **Verifies**: the script is saved to `outputs/` and re-run in a fresh process by an independent verifier. Mismatch or crash means the answer is rejected.
6. Output: answer + assumptions + cleaning log + proof script + proof JSON (with SHA-256 of the script).

```
Question -> PLAN (LLM) --unanswerable/ambiguous--> REFUSE / ASK
               | answerable
               v
          WRITE CODE (LLM) -> safety check -> RUN (fresh process) -> VERIFY (re-run, compare) -> ANSWER + PROOF
               ^                                      | error / mismatch: feed error back, retry up to 3x, else FAILED
               +--- all code reads data ONLY through src/cleaning.py (cleaned tables + log) ---+
```

## 2. Technologies, libraries and models
Python 3, pandas, python-dotenv, subprocess (for isolated re-runs). LLM: _<fill in: e.g. Gemini (gemini-3.5-flash) / Groq / Claude>_, temperature 0.

## 3. Install dependencies
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows   (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
pip install google-genai        # or: groq / anthropic  (only the one you use)
```

## 4. Configure and run
```bash
copy .env.example .env          # Mac/Linux: cp .env.example .env   -> then put your API key inside .env
python data/generate_data.py    # (re)creates the messy dataset
python main.py "What was net revenue in Q1 2025 after refunds?"
python main.py "What was the profit margin in Q1 2025?"
```
No API key? `LLM_PROVIDER=mock` tests the pipeline with a fake AI (only a few question shapes work).

## 5. Reproduce the demonstrated results
```bash
python tests/run_all.py                              # 12 questions: 8 answerable, 3 refusals, 1 clarification
python -m src.verifier outputs/<any proof>.json      # independent re-check of any answer
python outputs/<any proof>.py                        # prints the same number
```

## Data pipeline (how input data is collected, processed and passed on)
`data/*.csv` -> `src/cleaning.py` (dedupe, date parsing, FX conversion, refund validation, log) -> cleaned tables + log -> `src/agent.py` prompts (schema + rules + log) -> generated script (`outputs/*.py`) -> `src/executor.py` / `src/verifier.py`.

## Traps handled
See `data/TRAPS.md` (duplicates, conflicting duplicate, EUR/USD, missing FX rate, missing amount, ambiguous date, unknown customer, invalid refunds, unanswerable / out-of-range / non-existent / vague questions).

## Evidence and explanation
Every answer ships with: the script (`outputs/*.py`), a proof file (`outputs/*.json` with script hash, assumptions, cleaning log), and the printed cleaning log. Refusals include the reason.

## Sample input and output
_<Paste the real output of `python main.py "What was net revenue in Q1 2025 after refunds?"` and of a refusal here.>_

## Scope note
**Minimum viable (done):** 4-table messy dataset; cleaning with log; planner with refusal and clarification; LLM-written code; isolated execution; independent verifier with tamper detection; 12-question test suite.
**Stretch (attempted/optional):** _<e.g. web UI, more datasets, document-based questions>_
**Known limits:** small dataset; refunds assumed to be in the order's currency; LLM-written code is checked by a simple pattern filter, not a full sandbox.
