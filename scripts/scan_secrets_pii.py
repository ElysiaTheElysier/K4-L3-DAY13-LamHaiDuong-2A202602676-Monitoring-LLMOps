from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Secret patterns
SECRET_PATTERNS = [
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI/Langfuse Secret Key"),
    (r"pk-lf-[a-zA-Z0-9-]{20,}", "Langfuse Public Key in code"),
    (r"ghp_[a-zA-Z0-9]{30,}", "GitHub Personal Access Token"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
]

# Raw PII patterns
RAW_PII_PATTERNS = [
    (r"(?<![A-Z_])[\w\.-]+@[\w\.-]+\.\w+", "Unredacted Email"),
    (r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){9}(?!\d)", "Unredacted VN Phone"),
    (r"\b\d{12}\b", "Unredacted CCCD (12 digits)"),
    (r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "Unredacted Credit Card"),
]

IGNORE_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".antigravity"}
IGNORE_FILES = {".env", "sample_queries.jsonl"}  # sample queries intentionally have test PII


def scan_file(file_path: Path) -> list[str]:
    issues: list[str] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return issues

    # Scan for secrets in all text files
    for pattern, desc in SECRET_PATTERNS:
        if re.search(pattern, content):
            issues.append(f"Potential secret found: {desc}")

    # Scan for raw PII only in logs or markdown
    if file_path.suffix in {".jsonl", ".txt", ".md"} and file_path.name not in IGNORE_FILES:
        for pattern, desc in RAW_PII_PATTERNS:
            matches = re.findall(pattern, content)
            # Filter out redaction tokens like [REDACTED_EMAIL]
            real_leaks = [m for m in matches if not any(tag in m for tag in ["REDACTED", "000000000000", "0123456789"])]
            if real_leaks and "sample" not in file_path.name:
                issues.append(f"Potential raw PII found: {desc} ({len(real_leaks)} occurrences)")

    return issues


def main() -> int:
    print("=== [BONUS AUTOMATION] Secret & PII Scanner ===")
    total_files = 0
    total_issues = 0

    for path in REPO_ROOT.rglob("*"):
        if any(ignored in path.parts for ignored in IGNORE_DIRS):
            continue
        if path.is_file() and path.suffix in {".py", ".yaml", ".json", ".jsonl", ".md", ".txt"}:
            total_files += 1
            issues = scan_file(path)
            if issues:
                total_issues += len(issues)
                print(f"[FAIL] {path.relative_to(REPO_ROOT)}:")
                for issue in issues:
                    print(f"       - {issue}")

    print(f"\nScanned {total_files} files.")
    if total_issues == 0:
        print("[SUCCESS] No secrets or unredacted PII leaks found! Repository is clean.")
        return 0
    else:
        print(f"[WARNING] Found {total_issues} potential security issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
