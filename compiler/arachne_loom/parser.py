"""A deliberately narrow CTD-Markdown adapter; it never guesses references."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .model import canonical_document, text_inline

HEADING = re.compile(r"^(#{1,9})\s+(?:(\d+(?:\.\d+)*)\s+)?(.+?)\s*$")
LIST_ITEM = re.compile(r"^([-+*•]|[0-9]+[.)])\s+(.+)$")
DIRECTIVE = re.compile(r"^:::(table|figure)\s+(.+?)\s*$")
ATTR = re.compile(r'([a-zA-Z][\w-]*)=("[^"]*"|[^\s]+)')
REFERENCE = re.compile(r"\[@([A-Za-z][A-Za-z0-9_-]*)\]")


class ParseError(ValueError):
    pass


def _attrs(raw: str) -> dict[str, str]:
    values = {key: value.strip('"') for key, value in ATTR.findall(raw)}
    if not values:
        raise ParseError(f"invalid directive attributes: {raw}")
    return values


def _inlines(text: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    cursor = 0
    for match in REFERENCE.finditer(text):
        if match.start() > cursor:
            items.append(text_inline(text[cursor:match.start()]))
        target = match.group(1)
        items.append({"type": "literatureCitation" if target.startswith("ref-") else "crossReference", "targetId": target})
        cursor = match.end()
    if cursor < len(text):
        items.append(text_inline(text[cursor:]))
    return items or [text_inline("")]


def parse_markdown(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    lines = source.read_text(encoding="utf-8").splitlines()
    language, title = "zh-CN", source.stem
    start = 0
    if lines[:1] == ["---"]:
        try:
            end = lines.index("---", 1)
        except ValueError as exc:
            raise ParseError("unclosed YAML front matter") from exc
        for line in lines[1:end]:
            key, _, value = line.partition(":")
            if key.strip() == "language":
                language = value.strip().strip('"')
            if key.strip() == "title":
                title = value.strip().strip('"')
        start = end + 1

    blocks: list[dict[str, Any]] = []
    i = start
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        heading = HEADING.match(line)
        if heading:
            hashes, number, body = heading.groups()
            blocks.append({"type": "heading", "id": f"h-{len(blocks)+1}", "level": len(hashes), "content": body,
                           "numberPath": number.split(".") if number else []})
            i += 1
            continue
        list_match = LIST_ITEM.match(line)
        if list_match:
            marker, content = list_match.groups()
            ordered = marker[0].isdigit()
            block = {"type": "list", "kind": "ordered" if ordered else "unordered",
                     "start": int(marker[:-1]) if ordered else 1, "items": []}
            while i < len(lines):
                match = LIST_ITEM.match(lines[i].strip())
                if not match or match.group(1)[0].isdigit() != ordered:
                    break
                if lines[i][:1].isspace():
                    raise ParseError(f"nested lists are not supported at line {i+1}")
                block["items"].append({"inlines": _inlines(match.group(2))})
                i += 1
            blocks.append(block)
            continue
        directive = DIRECTIVE.match(line)
        if directive:
            kind, attr_text = directive.groups()
            attrs = _attrs(attr_text)
            if kind == "figure":
                for required in ("id", "src", "title"):
                    if required not in attrs:
                        raise ParseError(f"figure missing {required} at line {i+1}")
                blocks.append({"type": "figure", "id": attrs["id"], "src": attrs["src"], "title": attrs["title"],
                               "alt": attrs.get("alt", ""), "sourceSpan": {"line": i + 1}})
                i += 1
                if i < len(lines) and lines[i].strip() == ":::":
                    i += 1
                continue
            for required in ("id", "title"):
                if required not in attrs:
                    raise ParseError(f"table missing {required} at line {i+1}")
            table_lines: list[str] = []
            i += 1
            while i < len(lines) and lines[i].strip() != ":::":
                if lines[i].strip():
                    table_lines.append(lines[i].strip())
                i += 1
            if i == len(lines):
                raise ParseError(f"unclosed table at line {i+1}")
            rows = [[cell.strip() for cell in row.strip("|").split("|")] for row in table_lines]
            if len(rows) < 2 or not all(rows):
                raise ParseError(f"table needs header and rows at line {i+1}")
            rows.pop(1) if set("".join(rows[1])) <= {"-", ":"} else None
            blocks.append({"type": "table", "id": attrs["id"], "title": attrs["title"], "headerRows": 1,
                           "rows": rows, "sourceSpan": {"line": i + 1}})
            i += 1
            continue
        if line == ":::references":
            items: list[dict[str, str]] = []
            i += 1
            while i < len(lines) and lines[i].strip() != ":::":
                match = re.match(r"^@([A-Za-z][\w-]*):\s*(.+)$", lines[i].strip())
                if not match:
                    raise ParseError(f"invalid reference entry at line {i+1}")
                items.append({"id": match.group(1), "content": match.group(2)})
                i += 1
            if i == len(lines):
                raise ParseError("unclosed references block")
            blocks.append({"type": "references", "items": items, "order": "citationOrder"})
            i += 1
            continue
        blocks.append({"type": "paragraph", "inlines": _inlines(line), "sourceSpan": {"line": i + 1}})
        i += 1
    return canonical_document(language, {"title": title}, blocks, str(source.parent.resolve()))


def parse_to_file(input_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    model = parse_markdown(input_path)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return model
