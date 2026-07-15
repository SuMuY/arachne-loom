#!/usr/bin/env python3
"""Leak guard (portable): scan tracked files + .docx internals for sensitive data.

Project-agnostic. Drop scripts/leak-guard/ into any git repo and it works:
it finds the repo root via git and its pattern file next to itself.

Exit code 0 = clean, 1 = matches found, 2 = usage/config error.

Scanned:
  - all git-tracked text files
  - the extracted text of every .docx / .docm / .xlsx / .pptx (secrets hide in
    the OOXML parts, not just visible text)

Patterns come from patterns.txt beside this script (append-only).
"""
from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PATTERN_FILE = HERE / "patterns.txt"

TEXT_SUFFIXES = {
    ".md", ".py", ".txt", ".json", ".toml", ".yml", ".yaml",
    ".sh", ".cfg", ".ini", ".rst", ".csv", ".tsv", ".xml", ".html", "",
}
OOXML_SUFFIXES = {".docx", ".docm", ".xlsx", ".pptx"}


def repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return Path(out)


def load_patterns() -> list[re.Pattern]:
    if not PATTERN_FILE.exists():
        print(f"error: pattern file missing: {PATTERN_FILE}", file=sys.stderr)
        sys.exit(2)
    patterns = []
    for raw in PATTERN_FILE.read_text(encoding="utf-8").splitlines():
        if raw.lstrip().startswith("#"):
            continue
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        patterns.append(re.compile(line, re.IGNORECASE))
    if not patterns:
        print("error: no patterns loaded", file=sys.stderr)
        sys.exit(2)
    return patterns


def tracked_files(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(root), "ls-files"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def ooxml_text(path: Path) -> str:
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
    root = repo_root()
    patterns = load_patterns()
    # This script and its pattern file necessarily contain example shapes.
    self_exempt = {
        str(PATTERN_FILE.relative_to(root)),
        str(Path(__file__).resolve().relative_to(root)),
    }
    hits: list[tuple[str, str, str]] = []

    for rel in tracked_files(root):
        if rel in self_exempt:
            continue
        path = root / rel
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix in OOXML_SUFFIXES:
            text = ooxml_text(path)
        elif suffix in TEXT_SUFFIXES:
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
        else:
            continue
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
            "exemption. Never publish real IDs, names, or project codes.",
            file=sys.stderr,
        )
        return 1

    print("leak guard: clean (no sensitive patterns found)")
    return 0


if __name__ == "__main__":
    sys.exit(scan())
