"""A FAKE 'AI' used only to test the pipeline without an API key (LLM_PROVIDER=mock).
It understands just a handful of question shapes. Real runs must use a real model."""
import json
import re

HEAD = "from src.cleaning import load_clean_data\ntables, notes = load_clean_data()\norders = tables['orders']\n"
MONTHS = {"january": 1, "february": 2, "march": 3, "april": 4}


def _question(prompt):
    return re.findall(r"QUESTION: (.+)", prompt)[-1].strip().lower()


def _plan(q):
    if any(w in q for w in ["profit", "margin", "cost"]):
        return {"verdict": "unanswerable", "reason": "There is no cost data, so profit cannot be computed.", "assumptions": []}
    if "2026" in q:
        return {"verdict": "unanswerable", "reason": "Orders only cover January-April 2025; nothing exists for 2026.", "assumptions": []}
    if "c99" in q:
        return {"verdict": "unanswerable", "reason": "Customer C99 does not exist in the data.", "assumptions": []}
    if "best customer" in q:
        return {"verdict": "ambiguous", "reason": "'Best' could mean most revenue, most orders or most recent. Please say which.", "assumptions": []}
    return {"verdict": "answerable", "reason": "The needed columns exist.",
            "assumptions": ["Revenue = completed orders in USD", "Q1 = January to March 2025"]}


def _code(q):
    gross = ("d = orders[(orders['status']=='completed') & (orders['order_date'].dt.year==2025) & "
             "(orders['order_date'].dt.month<={hi}) & (orders['order_date'].dt.month>={lo})]\n"
             "gross = d['amount_usd'].sum()\n")
    if "net" in q:
        return (HEAD + gross.format(lo=1, hi=3) +
                "r = tables['refunds']\nr = r[r['valid'] & (r['refund_date'].dt.year==2025) & (r['refund_date'].dt.month<=3)]\n"
                "result = gross - r['refund_usd'].sum()\nprint(round(result, 2))\n")
    if "q1" in q or "quarter" in q:
        return HEAD + gross.format(lo=1, hi=3) + "print(round(gross, 2))\n"
    for name, n in MONTHS.items():
        if name in q:
            return HEAD + gross.format(lo=n, hi=n) + "print(round(gross, 2))\n"
    if "india" in q:
        return HEAD + "c = tables['customers']\nprint(c[c['country']=='India']['customer_id'].nunique())\n"
    if "unique customers" in q or "distinct customers" in q:
        return HEAD + "print(orders[orders['status']=='completed']['customer_id'].nunique())\n"
    if "how many orders" in q:
        return HEAD + "print(orders['order_id'].nunique())\n"
    return HEAD + "print(0)\n"


def mock_llm(prompt):
    q = _question(prompt)
    if "TASK: PLAN" in prompt:
        return json.dumps(_plan(q))
    return _code(q)
