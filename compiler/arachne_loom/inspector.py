"""Independent OOXML reader. It does not import generator or field construction code."""

from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}


def _text(element) -> str:
    return "".join(element.xpath(".//w:t/text()", namespaces=NS))


def inspect(docx_path: str | Path, hashes: dict[str, str] | None = None) -> dict[str, Any]:
    path = Path(docx_path)
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        required = {"[Content_Types].xml", "word/document.xml", "word/_rels/document.xml.rels"}
        missing = sorted(required - names)
        if missing:
            raise ValueError(f"DOCX missing required parts: {missing}")
        document = etree.fromstring(archive.read("word/document.xml"))
        relationships = etree.fromstring(archive.read("word/_rels/document.xml.rels"))
    bookmarks = [item.get(f"{{{W}}}name") for item in document.xpath(".//w:bookmarkStart", namespaces=NS)]
    structural_issues: list[dict[str, Any]] = []
    # A bookmark range must be properly nested. Ignore Word's _Toc anchors,
    # which are commonly crossed with caption bookmarks after a TOC update.
    bookmark_stack: list[tuple[str, str, int]] = []
    bookmark_start_paragraph: dict[str, int] = {}
    bookmark_end_paragraph: dict[str, int] = {}
    for current_paragraph, paragraph in enumerate(document.xpath(".//w:body/w:p", namespaces=NS)):
      for element in paragraph.xpath(".//w:bookmarkStart | .//w:bookmarkEnd", namespaces=NS):
        if element.tag.endswith("bookmarkStart"):
            bookmark_id = element.get(f"{{{W}}}id")
            bookmark_name = element.get(f"{{{W}}}name")
            bookmark_stack.append((bookmark_id, bookmark_name, current_paragraph))
            bookmark_start_paragraph[bookmark_id] = current_paragraph
            if bookmark_name and bookmark_name.startswith("rdx_") and not paragraph.xpath(".//w:t | .//w:instrText | .//w:drawing", namespaces=NS):
                structural_issues.append({"type": "object-bookmark-in-empty-paragraph", "bookmarkId": bookmark_id,
                                          "name": bookmark_name, "paragraph": current_paragraph,
                                          "style": (paragraph.xpath("./w:pPr/w:pStyle/@w:val", namespaces=NS) or [None])[0]})
            continue
        bookmark_id = element.get(f"{{{W}}}id")
        bookmark_end_paragraph[bookmark_id] = current_paragraph
        if not bookmark_stack or bookmark_stack[-1][0] != bookmark_id:
            open_names = [name for _, name, _ in bookmark_stack]
            if any(name and name.startswith("rdx_") for name in open_names) and any(name and name.startswith("rdx_") for name in open_names[1:]):
                structural_issues.append({"type": "crossing-bookmark", "bookmarkId": bookmark_id,
                                          "open": open_names})
            for index in range(len(bookmark_stack) - 1, -1, -1):
                if bookmark_stack[index][0] == bookmark_id:
                    bookmark_stack.pop(index)
                    break
        else:
            bookmark_stack.pop()
    for bookmark_id, name, _ in bookmark_stack:
        structural_issues.append({"type": "unclosed-bookmark", "bookmarkId": bookmark_id, "name": name})
    for bookmark_id, start_paragraph in bookmark_start_paragraph.items():
        name = next((item.get(f"{{{W}}}name") for item in document.xpath(".//w:bookmarkStart", namespaces=NS)
                     if item.get(f"{{{W}}}id") == bookmark_id), "")
        end_paragraph = bookmark_end_paragraph.get(bookmark_id)
        if name.startswith("rdx_") and end_paragraph is not None and end_paragraph != start_paragraph:
            structural_issues.append({"type": "bookmark-spans-paragraphs", "bookmarkId": bookmark_id,
                                      "name": name, "startParagraph": start_paragraph,
                                      "endParagraph": end_paragraph})
    instructions = ["".join(item.xpath(".//w:instrText/text()", namespaces=NS)) for item in document.xpath(".//w:r", namespaces=NS)]
    field_stack: list[dict[str, Any]] = []
    for paragraph_index, paragraph in enumerate(document.xpath(".//w:body/w:p", namespaces=NS)):
        for field_char in paragraph.xpath(".//w:fldChar", namespaces=NS):
            field_type = field_char.get(f"{{{W}}}fldCharType")
            if field_type == "begin":
                field_stack.append({"paragraph": paragraph_index, "instruction": ""})
            elif field_type == "end":
                if not field_stack:
                    structural_issues.append({"type": "orphan-field-end", "paragraph": paragraph_index})
                else:
                    field = field_stack.pop()
                    begin_paragraph = field["paragraph"]
                    instruction = field["instruction"].strip()
                    # TOC fields own generated result paragraphs and are
                    # expected to span paragraphs. Object/reference fields
                    # must remain atomic so insertion cannot duplicate a REF.
                    if begin_paragraph != paragraph_index and instruction.startswith(("REF ", "SEQ ", "STYLEREF")):
                        structural_issues.append({"type": "cross-paragraph-field", "instruction": instruction,
                                                  "beginParagraph": begin_paragraph, "endParagraph": paragraph_index})
        for instr in paragraph.xpath(".//w:instrText", namespaces=NS):
            if field_stack:
                field_stack[-1]["instruction"] += "".join(instr.xpath(".//text()"))
    for field in field_stack:
        instruction = field["instruction"].strip()
        if instruction.startswith(("REF ", "SEQ ", "STYLEREF")):
            structural_issues.append({"type": "unclosed-field", "instruction": instruction,
                                      "beginParagraph": field["paragraph"]})
    fields = [instruction for instruction in instructions if instruction.strip()]
    toc_fields = [instruction for instruction in fields if instruction.strip().startswith("TOC")]
    hyperlink_runs = len(document.xpath('.//w:instrText[contains(., "REF ")][contains(., "\\h")]', namespaces=NS))
    tables = []
    for index, table in enumerate(document.xpath(".//w:tbl", namespaces=NS)):
        rows = table.xpath("./w:tr", namespaces=NS)
        columns = max((len(row.xpath("./w:tc", namespaces=NS)) for row in rows), default=0)
        tables.append({"order": index, "rows": len(rows), "columns": columns})
    images = [rel.get("Target") for rel in relationships if rel.get("Type", "").endswith("/image")]
    return {"manifestVersion": "0.0.1", "createdAt": datetime.now(timezone.utc).isoformat(), "hashes": hashes or {},
            "bookmarks": bookmarks, "fields": fields, "fieldCount": len(fields), "tocFields": toc_fields,
            "hyperlinkRefRuns": hyperlink_runs, "tables": tables,
            "images": images, "wordErrorCachePresent": "错误!" in _text(document),
            "structuralIssues": structural_issues}


def inspect_to_file(docx_path: str | Path, output_path: str | Path, hashes: dict[str, str] | None = None) -> dict[str, Any]:
    result = inspect(docx_path, hashes)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result
