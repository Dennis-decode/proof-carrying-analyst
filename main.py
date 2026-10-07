"""MEMBER 4 owns this file.  Usage:  python main.py "What was total revenue in January 2025?" """
import sys

from src.agent import ask


def show(r):
    print("=" * 70)
    print("Question :", r["question"])
    print("Status   :", r["status"])
    if r["status"] == "ANSWERED":
        print(f"Answer   : {r['answer']:,.2f}")
        print("Verified :", "YES (re-ran the code in a fresh process, same number)")
        print("Proof    :", r["code_path"], "|", r["proof_path"])
    else:
        print("Why      :", r["reason"])
    if r["assumptions"]:
        print("Assumptions:")
        for a in r["assumptions"]:
            print("  -", a)
    if r["status"] == "ANSWERED":
        print("Data issues handled (cleaning log):")
        for n in r["cleaning_notes"]:
            print("  -", n)
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit('usage: python main.py "your question"')
    show(ask(" ".join(sys.argv[1:])))
