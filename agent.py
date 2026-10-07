"""MEMBER 3 owns this file.
The brain: PLAN (can we answer?) -> WRITE CODE -> RUN -> VERIFY. Refuses when it cannot answer reliably."""
import json
import re

from src.cleaning import describe_tables, load_clean_data, load_policy
from src.executor import check_code, run_script, save_script, ROOT
from src.llm import call_llm
from src.verifier import verify_script, write_proof

SYSTEM = "You are a careful data analyst. Never guess. Follow the output format exactly."

PLAN_PROMPT = """TASK: PLAN
Decide whether the question below can be answered RELIABLY from the data.

BUSINESS RULES:
<<POLICY>>
DATA (already cleaned):
<<SCHEMA>>
CLEANING LOG:
<<NOTES>>

Verdicts:
- "answerable": every column and period needed exists, and the question has one clear meaning
  (or the business rules define it).
- "unanswerable": a needed column is missing (e.g. cost/profit), the period is outside the data range,
  or the person/item asked about does not exist.
- "ambiguous": the question has several reasonable meanings and the business rules do not decide (e.g. "best customer").
A confident wrong answer is worse than refusing. Never invent data.
Reply with ONLY this JSON (no markdown):
{"verdict": "answerable|unanswerable|ambiguous", "reason": "<1-2 sentences>", "assumptions": ["<definitions you will use>"]}

QUESTION: <<QUESTION>>"""

CODE_PROMPT = """TASK: WRITE_CODE
Write a short Python script (pandas) that computes the answer.
RULES:
- The first two lines must be exactly:
from src.cleaning import load_clean_data
tables, notes = load_clean_data()
- Tables: tables["orders"], tables["customers"], tables["refunds"] (already cleaned, described below).
- Use only pandas / numpy / datetime / math. No reading files, no network, no input().
- Money is in orders.amount_usd. Revenue = orders with status == "completed" (see business rules).
- Date filters on order_date automatically leave out rows with empty (ambiguous) dates. That is intended.
- The LAST line must print exactly ONE number: print(round(result, 2)). No other print statements.
- Reply with ONLY code. No explanations, no markdown fences.
BUSINESS RULES:
<<POLICY>>
AGREED DEFINITIONS: <<ASSUMPTIONS>>
DATA:
<<SCHEMA>>
<<ERROR>>
QUESTION: <<QUESTION>>"""


def _fill(template, **kw):
    for k, v in kw.items():
        template = template.replace(f"<<{k.upper()}>>", str(v))
    return template


def _parse_json(text):
    text = re.sub(r"```(?:json)?", "", text)
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1])


def _clean_code(text):
    text = re.sub(r"^```(?:python)?\s*", "", text.strip())
    return re.sub(r"\s*```$", "", text).strip()


def plan_question(question, tables, notes):
    prompt = _fill(PLAN_PROMPT, policy=load_policy(), schema=describe_tables(tables),
                   notes="\n".join(notes), question=question)
    for _ in range(2):
        try:
            plan = _parse_json(call_llm(prompt, SYSTEM))
            if plan.get("verdict") in ("answerable", "unanswerable", "ambiguous"):
                return plan
        except (ValueError, KeyError):
            continue
    return {"verdict": "unanswerable", "reason": "Could not understand the planner's reply, so refusing to guess.",
            "assumptions": []}


def ask(question):
    """Main entry point. Returns a dict with status ANSWERED / REFUSED / NEEDS_CLARIFICATION / FAILED."""
    tables, notes = load_clean_data()
    plan = plan_question(question, tables, notes)
    result = {"question": question, "status": None, "answer": None, "reason": plan.get("reason", ""),
              "assumptions": plan.get("assumptions", []), "cleaning_notes": notes,
              "code_path": None, "proof_path": None, "verified": False}

    if plan["verdict"] == "unanswerable":
        result["status"] = "REFUSED"
        return result
    if plan["verdict"] == "ambiguous":
        result["status"] = "NEEDS_CLARIFICATION"
        return result

    error = ""
    for _ in range(3):  # up to 3 attempts; on failure we feed the error back to the AI
        prompt = _fill(CODE_PROMPT, policy=load_policy(), assumptions="; ".join(plan.get("assumptions", [])),
                       schema=describe_tables(tables),
                       error=f"YOUR PREVIOUS ATTEMPT FAILED: {error}\nFix it." if error else "",
                       question=question)
        code = _clean_code(call_llm(prompt, SYSTEM))
        problem = check_code(code)
        if problem:
            error = problem
            continue
        path = save_script(question, code)
        value, err = run_script(path)
        if err:
            error = err
            continue
        ok, detail = verify_script(path, value)  # independent re-run in a fresh process
        if not ok:
            error = "verification failed: " + detail
            continue
        proof = write_proof(question, value, path, plan.get("assumptions", []), notes)
        result.update(status="ANSWERED", answer=value, verified=True,
                      code_path=path.relative_to(ROOT).as_posix(), proof_path=proof.relative_to(ROOT).as_posix())
        return result

    result["status"] = "FAILED"
    result["reason"] = f"Could not produce code that runs and verifies ({error}). Refusing to give an unverified number."
    return result
