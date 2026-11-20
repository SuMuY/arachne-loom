"""Conservative style normalization for existing DOCX paragraphs."""

from __future__ import annotations

import json
import math
import re
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def _apply_heading_geometry(paragraph, profile: dict[str, Any], level: int) -> bool:
    config = profile.get("headingStyle", {}).get("indentation", {
        "basePt": 0, "incrementPt": 18, "hangingPt": 24,
    })
    anchor = config["basePt"] + (level - 1) * config["incrementPt"]
    left = round((anchor + config["hangingPt"]) * 20)
    hanging = round(config["hangingPt"] * 20)
    ppr = paragraph._p.get_or_add_pPr()
    ind = ppr.find(qn("w:ind"))
    if ind is None:
        ind = OxmlElement("w:ind")
        ppr.append(ind)
    ind.set(qn("w:left"), str(left))
    ind.set(qn("w:hanging"), str(hanging))
    tabs = ppr.find(qn("w:tabs"))
    if tabs is None:
        tabs = OxmlElement("w:tabs")
        ppr.append(tabs)
    for tab in list(tabs.findall(qn("w:tab"))):
        if tab.get(qn("w:val")) == "num":
            tabs.remove(tab)
    tab = OxmlElement("w:tab")
    tab.set(qn("w:val"), "num")
    tab.set(qn("w:pos"), str(left))
    tabs.append(tab)
    return True


def _list_level(paragraph, numbering) -> tuple[str, int, int] | None:
    ppr = paragraph._p.pPr
    num_pr = ppr.numPr if ppr is not None else None
    style = paragraph.style
    inherited_style = style
    while num_pr is None and style is not None:
        style_ppr = style._element.pPr
        num_pr = style_ppr.numPr if style_ppr is not None else None
        style = style.base_style
    if num_pr is None or num_pr.numId is None:
        name = inherited_style.name.lower()
        if "list bullet" in name:
            return "unordered", -1, 0
        if "list number" in name:
            return "ordered", -1, 0
        return None
    num_id = int(num_pr.numId.val)
    level = int(num_pr.ilvl.val) if num_pr.ilvl is not None else 0
    num = numbering.find(f"{qn('w:num')}[@{qn('w:numId')}='{num_id}']")
    if num is None:
        return None
    abstract_id = num.find(qn("w:abstractNumId"))
    if abstract_id is None:
        return None
    abstract = numbering.find(f"{qn('w:abstractNum')}[@{qn('w:abstractNumId')}='{abstract_id.get(qn('w:val'))}']")
    lvl = abstract.find(f"{qn('w:lvl')}[@{qn('w:ilvl')}='{level}']") if abstract is not None else None
    fmt = lvl.find(qn("w:numFmt")) if lvl is not None else None
    if fmt is None:
        return None
    kind = "unordered" if fmt.get(qn("w:val")) == "bullet" else "ordered"
    return kind, num_id, level


def _set_list_geometry(ppr, marker: int, text: int) -> None:
    ind = ppr.find(qn('w:ind'))
    if ind is None:
        ind = OxmlElement('w:ind')
        ppr.append(ind)
    for name in ('firstLine', 'firstLineChars', 'hangingChars', 'leftChars', 'start', 'startChars'):
        ind.attrib.pop(qn('w:' + name), None)
    ind.set(qn('w:left'), str(text))
    ind.set(qn('w:hanging'), str(text - marker))
    tabs = ppr.find(qn('w:tabs'))
    if tabs is None:
        tabs = OxmlElement('w:tabs')
        ppr.append(tabs)
    for tab in list(tabs):
        if tab.get(qn('w:val')) == 'num':
            tabs.remove(tab)
    tab = OxmlElement('w:tab')
    tab.set(qn('w:val'), 'num')
    tab.set(qn('w:pos'), str(text))
    tabs.append(tab)


def _apply_list_geometry(doc: Document, paragraph, profile: dict[str, Any], level: int) -> bool:
    item = _list_level(paragraph, doc.part.numbering_part.element)
    if item is None:
        return False
    kind, num_id, _ = item
    geometry = profile.get("listStyle", {}).get(kind)
    if not geometry:
        geometry = {"markerPt": 18, "textPt": 42}
    marker = round(geometry["markerPt"] * 20) + level * 360
    text = round(geometry["textPt"] * 20) + level * 360
    _set_list_geometry(paragraph._p.get_or_add_pPr(), marker, text)
    if num_id == -1:
        return True
    numbering = doc.part.numbering_part.element
    num = numbering.find(f"{qn('w:num')}[@{qn('w:numId')}='{num_id}']")
    abstract_id = num.find(qn("w:abstractNumId")).get(qn("w:val"))
    abstract = numbering.find(f"{qn('w:abstractNum')}[@{qn('w:abstractNumId')}='{abstract_id}']")
    lvl = abstract.find(f"{qn('w:lvl')}[@{qn('w:ilvl')}='{level}']")
    if lvl is None:
        return False
    ppr = lvl.find(qn("w:pPr"))
    if ppr is None:
        ppr = OxmlElement("w:pPr")
        lvl.append(ppr)
    _set_list_geometry(ppr, marker, text)
    return True


def normalize_docx(source: str | Path, output: str | Path, profile: dict[str, Any]) -> dict[str, int]:
    """Normalize recognized native headings/lists, preserving all text and other package parts."""
    source_path, output_path = Path(source).resolve(), Path(output).resolve()
    if source_path == output_path:
        raise ValueError("source and output must be different files")
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    indentation = profile.get("headingStyle", {}).get("indentation")
    if indentation is not None:
        if set(indentation) != {"basePt", "incrementPt", "hangingPt"} or any(
            not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0
            for value in indentation.values()
        ):
            raise ValueError("headingStyle.indentation must contain finite non-negative basePt, incrementPt, hangingPt")
    for kind, geometry in profile.get("listStyle", {}).items():
        if kind not in {"ordered", "unordered"} or set(geometry) != {"markerPt", "textPt"} or any(
            not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0
            for value in geometry.values()
        ) or geometry["textPt"] <= geometry["markerPt"]:
            raise ValueError(f"invalid listStyle geometry for {kind}")
    doc = Document(source_path)
    headings = lists = 0
    paragraphs = list(doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                paragraphs.extend(cell.paragraphs)
    seen = set()
    for paragraph in paragraphs:
        if id(paragraph._p) in seen:
            continue
        seen.add(id(paragraph._p))
        style_id = paragraph.style.style_id
        match = re.fullmatch(r"Heading([1-9])", style_id)
        if match is None:
            candidate = re.fullmatch(r"Heading ([1-9])", paragraph.style.name or "")
            outline = paragraph.style._element.xpath("./w:pPr/w:outlineLvl/@w:val")
            if candidate and not paragraph.style._element.get(qn("w:customStyle")) in ("1", "true", "on") and outline == [str(int(candidate[1]) - 1)]:
                match = candidate
        if match:
            headings += _apply_heading_geometry(paragraph, profile, int(match[1]))
        elif _list_level(paragraph, doc.part.numbering_part.element) is not None:
            item = _list_level(paragraph, doc.part.numbering_part.element)
            lists += _apply_list_geometry(doc, paragraph, profile, item[2])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_path.parent) as temporary:
        stage = Path(temporary) / "normalized.docx"
        doc.save(stage)
        with zipfile.ZipFile(source_path) as original, zipfile.ZipFile(stage) as edited:
            replacements = {"word/document.xml", "word/numbering.xml"}
            changed = {name: edited.read(name) for name in replacements if name in original.namelist() and name in edited.namelist()}
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as result:
                for item in original.infolist():
                    result.writestr(item, changed.get(item.filename, original.read(item.filename)))
    return {"headingsUpdated": headings, "listsUpdated": lists, "manualNumberingChanged": 0}


def normalize_to_file(source: str | Path, output: str | Path, profile_path: str | Path) -> dict[str, int]:
    return normalize_docx(source, output, json.loads(Path(profile_path).read_text(encoding="utf-8")))
