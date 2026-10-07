"""MEMBER 1 owns this file. Runs every test question and prints PASS/FAIL.   python tests/run_all.py"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.agent import ask  # noqa: E402

questions = json.loads((Path(__file__).parent / "questions.json").read_text())
passed = 0
print(f"{'ID':<3} {'RESULT':<5} {'EXPECTED':<20} {'GOT':<20} QUESTION")
for q in questions:
    r = ask(q["question"])
    ok = r["status"] == q["expect"]
    if ok and q["expect"] == "ANSWERED":
        ok = abs(r["answer"] - q["value"]) < 0.01
    passed += ok
    exp = q["expect"] + (f" {q['value']}" if "value" in q else "")
    got = r["status"] + (f" {r['answer']}" if r["answer"] is not None else "")
    print(f"{q['id']:<3} {'PASS' if ok else 'FAIL':<5} {exp:<20} {got:<20} {q['question']}")
print(f"\n{passed}/{len(questions)} passed")
sys.exit(0 if passed == len(questions) else 1)
