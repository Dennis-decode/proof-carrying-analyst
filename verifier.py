"""MEMBER 4 owns this file.
The VERIFIER: it does NOT trust the agent. It re-runs the saved script in a fresh process and compares.
Anyone can run it:   python -m src.verifier outputs/<proof>.json
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from src.executor import ROOT, run_script


def verify_script(script_path, claimed, tol=0.01):
    value, err = run_script(script_path)
    if err:
        return False, err
    if abs(value - claimed) > tol:
        return False, f"re-run gave {value}, agent claimed {claimed}"
    return True, f"re-run gave {value} (matches)"


def write_proof(question, answer, script_path, assumptions, notes):
    script_path = Path(script_path)
    proof = {
        "question": question,
        "answer": answer,
        "script": script_path.relative_to(ROOT).as_posix(),
        "script_sha256": hashlib.sha256(script_path.read_bytes()).hexdigest(),
        "assumptions": assumptions,
        "cleaning_notes": notes,
        "verified_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    out = script_path.with_suffix(".json")
    out.write_text(json.dumps(proof, indent=2))
    return out


def verify_proof(proof_path):
    proof = json.loads(Path(proof_path).read_text())
    script = ROOT / proof["script"]
    if hashlib.sha256(script.read_bytes()).hexdigest() != proof["script_sha256"]:
        return False, "script was changed after the proof was written"
    return verify_script(script, proof["answer"])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python -m src.verifier outputs/<proof>.json")
    ok, detail = verify_proof(sys.argv[1])
    print(("VERIFIED: " if ok else "REJECTED: ") + detail)
    sys.exit(0 if ok else 1)
