"""MEMBER 4 owns this file.
Saves the AI-written code as a real .py file, checks it is safe, and runs it in a SEPARATE process."""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "outputs"

HEADER = '''# Auto-generated proof script. Question: {question}
# Re-run it yourself from the project folder:   python {rel}
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
'''

# The AI may only compute from the cleaned tables. Block anything that touches files, network or the system.
FORBIDDEN = [
    r"\bimport\s+(os|sys|subprocess|socket|requests|shutil|urllib|pathlib)\b",
    r"\bfrom\s+(os|sys|subprocess|socket|requests|shutil|urllib|pathlib)\b",
    r"\bopen\s*\(", r"\beval\s*\(", r"\bexec\s*\(", r"__import__",
    r"read_csv|read_excel|to_csv|read_json",
]


def check_code(code):
    """Return None if OK, otherwise a text describing the problem."""
    if "load_clean_data" not in code:
        return "code must use load_clean_data() so it works on the cleaned tables"
    for pat in FORBIDDEN:
        if re.search(pat, code):
            return f"forbidden pattern in code: {pat}"
    if "print(" not in code:
        return "code never prints the final number"
    return None


def save_script(question, code):
    slug = re.sub(r"[^a-z0-9]+", "_", question.lower()).strip("_")[:40]
    tag = hashlib.sha1(question.encode()).hexdigest()[:4]
    path = OUT_DIR / f"{slug}_{tag}.py"
    OUT_DIR.mkdir(exist_ok=True)
    rel = path.relative_to(ROOT).as_posix()
    header = HEADER.format(question=question.replace("\n", " "), rel=rel)
    path.write_text(header + "\n" + code.strip() + "\n")
    return path


def run_script(path, timeout=30):
    """Run the script in a fresh Python process. Returns (number, error_text)."""
    try:
        p = subprocess.run([sys.executable, str(path)], capture_output=True, text=True,
                           timeout=timeout, cwd=ROOT)
    except subprocess.TimeoutExpired:
        return None, "script timed out"
    if p.returncode != 0:
        return None, "script crashed: " + p.stderr.strip()[-400:]
    lines = [l for l in p.stdout.strip().splitlines() if l.strip()]
    if not lines:
        return None, "script printed nothing"
    try:
        return float(lines[-1]), None
    except ValueError:
        return None, f"last printed line is not a number: {lines[-1]!r}"
