#!/usr/bin/env python3
"""Leak guard: scan tracked files (and .docx internals) for sensitive data.

Exit code 0 = clean, 1 = matches found, 2 = usage/config error.

Scanned:
  - all git-tracked text files
  - the extracted text of every .docx (real trial IDs hide inside word/*.xml)

Patterns come from scripts/sensitive-patterns.txt (append-only). This script
is invoked by the pre-push hook and by CI, so both gates share one source.
"""
from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PATTERN_FILE = REPO / "scripts" / "sensitive-patterns.txt"

# Files this scanner must never flag itself on (the pattern list; and this
# script, which necessarily contains example shapes in comments).
SELF_EXEMPT = {
    "scripts/sensitive-patterns.txt",
    "scripts/scan-sensitive.py",
}

# Directories that legitimately contain pattern examples (the reusable template
# ships its own patterns.txt with illustrative shapes). Exempt by prefix.
EXEMPT_PREFIXES = (
    "scripts/leak-guard/",
)

TEXT_SUFFIXES = {
    ".md", ".py", ".txt", ".json", ".toml", ".yml", ".yaml",
    ".sh", ".cfg", ".ini", ".rst", "",
}


def load_patterns() -> list[re.Pattern]:
    if not PATTERN_FILE.exists():
        print(f"error: pattern file missing: {PATTERN_FILE}", file=sys.stderr)
        sys.exit(2)
    patterns = []
    for raw in PATTERN_FILE.read_text(encoding="utf-8").splitlines():
        # strip inline comments after the regex, then whitespace
        line = raw.split("#", 1)[0].strip() if not raw.lstrip().startswith("#") else ""
        if not line:
            continue
        patterns.append(re.compile(line, re.IGNORECASE))
    if not patterns:
        print("error: no patterns loaded", file=sys.stderr)
        sys.exit(2)
    return patterns


def tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(REPO), "ls-files"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def docx_text(path: Path) -> str:
    """Concatenate text of all XML parts inside a .docx (or any OOXML zip)."""
    chunks = []
    try:
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if name.endswith(".xml"):
                    chunks.append(z.read(name).decode("utf-8", "ignore"))
    except (zipfile.BadZipFile, OSError):
        return ""
    return "\n".join(chunks)


def scan() -> int:
    patterns = load_patterns()
    hits: list[tuple[str, str, str]] = []  # (file, pattern, sample)

    for rel in tracked_files():
        if rel in SELF_EXEMPT or rel.startswith(EXEMPT_PREFIXES):
            continue
        path = REPO / rel
        if not path.is_file():
            continue
        suffix = path.suffix.lower()

        if suffix == ".docx":
            text = docx_text(path)
        elif suffix in TEXT_SUFFIXES:
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
        else:
            continue  # skip other binaries (images, etc.)

        for pat in patterns:
            m = pat.search(text)
            if m:
                hits.append((rel, pat.pattern, m.group(0)))

    if hits:
        print("SENSITIVE DATA DETECTED — push/commit blocked:\n", file=sys.stderr)
        for rel, pattern, sample in hits:
            print(f"  {rel}: matched /{pattern}/  ->  {sample!r}", file=sys.stderr)
        print(
            "\nReplace real identifiers with synthetic values, or add a documented\n"
            "exemption. Never publish real trial IDs, names, or project codes.",
            file=sys.stderr,
        )
        return 1

    print("leak guard: clean (no sensitive patterns found)")
    return 0


if __name__ == "__main__":
    sys.exit(scan())
