"""Deterministic Canonical Model -> DOCX generator."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from . import __version__
from .fields import append_caption, append_cross_reference, append_toc_field
from .validator import validate_or_raise


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _style_by_id(document: Document, style_id: str):
    """Look up a style by its styleId without triggering python-docx's
    deprecated name-based __getitem__ path."""
    for style in document.styles:
        if style.style_id == style_id:
            return style
    raise KeyError(style_id)


def _stable_bookmark(object_id: str) -> str:
    digest = hashlib.sha256(object_id.encode("utf-8")).hexdigest()[:8]
    return f"rdx_{object_id.replace('-', '_')}_{digest}"[:40]


def _set_field_update_on_open(document: Document) -> None:
    settings = document.settings.element
    element = settings.find(qn("w:updateFields"))
    if element is None:
        element = OxmlElement("w:updateFields")
        settings.append(element)
    element.set(qn("w:val"), "true")


def _set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    element = OxmlElement("w:tblHeader")
    element.set(qn("w:val"), "true")
    tr_pr.append(element)


def _heading_geometry(profile: dict[str, Any], level: int) -> tuple[int, int] | None:
    config = profile.get("headingStyle", {}).get("indentation")
    if config is None:
        return None
    # Resolve to twips once so styles and numbering use identical rounding.
    anchor = config["basePt"] + (level - 1) * config["incrementPt"]
    return round((anchor + config["hangingPt"]) * 20), round(config["hangingPt"] * 20)


def _new_list_numbering(document: Document, kind: str, start: int, marker: int, text: int) -> int:
    """Each list has its own sequence; all lists of one kind share geometry."""
    numbering = document.part.numbering_part.element
    abstract_id = max((int(n.get(qn("w:abstractNumId"))) for n in numbering.findall(qn("w:abstractNum"))), default=0) + 1
    num_id = max((int(n.get(qn("w:numId"))) for n in numbering.findall(qn("w:num"))), default=0) + 1
    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    multi = OxmlElement("w:multiLevelType"); multi.set(qn("w:val"), "singleLevel"); abstract.append(multi)
    level = OxmlElement("w:lvl"); level.set(qn("w:ilvl"), "0")
    for tag, value in [("start", str(start) if kind == "ordered" else "1"),
                       ("numFmt", "decimal" if kind == "ordered" else "bullet"),
                       ("suff", "tab"), ("lvlText", "%1." if kind == "ordered" else "•"), ("lvlJc", "left")]:
        child = OxmlElement(f"w:{tag}"); child.set(qn("w:val"), value); level.append(child)
    ppr = OxmlElement("w:pPr")
    tabs = OxmlElement("w:tabs"); tab = OxmlElement("w:tab")
    tab.set(qn("w:val"), "num"); tab.set(qn("w:pos"), str(text)); tabs.append(tab); ppr.append(tabs)
    ind = OxmlElement("w:ind")
    ind.set(qn("w:left"), str(text)); ind.set(qn("w:hanging"), str(text-marker)); ppr.append(ind)
    level.append(ppr); abstract.append(level); numbering.insert_element_before(abstract, "w:num", "w:numIdMacAtCleanup")
    num = OxmlElement("w:num"); num.set(qn("w:numId"), str(num_id))
    ref = OxmlElement("w:abstractNumId"); ref.set(qn("w:val"), str(abstract_id)); num.append(ref); numbering.append(num)
    return num_id


def _ensure_heading_numbering(document: Document, number_path: list[str], profile: dict[str, Any]) -> int:
    numbering = document.part.numbering_part.element
    abstract_ids = [int(node.get(qn("w:abstractNumId"))) for node in numbering.findall(qn("w:abstractNum"))]
    num_ids = [int(node.get(qn("w:numId"))) for node in numbering.findall(qn("w:num"))]
    abstract_id = max(abstract_ids, default=0) + 1
    num_id = max(num_ids, default=0) + 1
    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    multi = OxmlElement("w:multiLevelType"); multi.set(qn("w:val"), "multilevel"); abstract.append(multi)
    for level in range(9):
        item = OxmlElement("w:lvl"); item.set(qn("w:ilvl"), str(level))
        start = OxmlElement("w:start")
        value = number_path[level] if level < len(number_path) and str(number_path[level]).isdigit() else "1"
        start.set(qn("w:val"), value)
        item.append(start)
        fmt = OxmlElement("w:numFmt"); fmt.set(qn("w:val"), "decimal"); item.append(fmt)
        text = OxmlElement("w:lvlText"); text.set(qn("w:val"), ".".join(["%" + str(i + 1) for i in range(level + 1)])); item.append(text)
        align = OxmlElement("w:lvlJc"); align.set(qn("w:val"), "left"); item.append(align)
        role = profile.get("styles", {}).get("roles", {}).get(f"headingLevel{level + 1}")
        if role:
            pstyle = OxmlElement("w:pStyle"); pstyle.set(qn("w:val"), role["styleId"]); item.append(pstyle)
        geometry = _heading_geometry(profile, level + 1)
        if geometry is not None:
            left, hanging = geometry
            if role:
                item.remove(pstyle)
                item.insert(list(item).index(text), pstyle)
            suffix = OxmlElement("w:suff"); suffix.set(qn("w:val"), "tab")
            item.insert(list(item).index(text), suffix)
            ppr = OxmlElement("w:pPr")
            tabs = OxmlElement("w:tabs")
            tab = OxmlElement("w:tab")
            tab.set(qn("w:val"), "num"); tab.set(qn("w:pos"), str(left))
            tabs.append(tab); ppr.append(tabs)
            ind = OxmlElement("w:ind")
            ind.set(qn("w:left"), str(left)); ind.set(qn("w:hanging"), str(hanging))
            ppr.append(ind); item.append(ppr)
        abstract.append(item)
    numbering.insert_element_before(abstract, "w:num", "w:numIdMacAtCleanup")
    num = OxmlElement("w:num"); num.set(qn("w:numId"), str(num_id))
    abstract_ref = OxmlElement("w:abstractNumId"); abstract_ref.set(qn("w:val"), str(abstract_id)); num.append(abstract_ref)
    numbering.append(num)
    for level in range(1, 10):
        role = profile.get("styles", {}).get("roles", {}).get(f"headingLevel{level}")
        if not role:
            continue
        style = _style_by_id(document, role["styleId"])
        ppr = style._element.get_or_add_pPr()
        old = ppr.find(qn("w:numPr"))
        if old is not None: ppr.remove(old)
        num_pr = OxmlElement("w:numPr")
        ilvl = OxmlElement("w:ilvl"); ilvl.set(qn("w:val"), str(level - 1)); num_pr.append(ilvl)
        ref = OxmlElement("w:numId"); ref.set(qn("w:val"), str(num_id)); num_pr.append(ref)
        ppr.append(num_pr)
    return num_id


def _ensure_profile_heading_styles(document: Document, profile: dict[str, Any]) -> None:
    """Validate that the locale's base exposes the built-in Heading styles."""
    available = {style.style_id for style in document.styles}
    for level in range(1, 10):
        role = profile.get("styles", {}).get("roles", {}).get(f"headingLevel{level}")
        if role and role["styleId"] not in available:
            raise ValueError(f"base template lacks built-in heading style {role['styleId']}")


def _ensure_hyperlink_style(document: Document, profile: dict[str, Any]) -> None:
    style_id = profile.get("references", {}).get("characterStyleId", "Hyperlink")
    if style_id in {style.style_id for style in document.styles}:
        style = _style_by_id(document, style_id)
    else:
        style = document.styles.add_style(style_id, WD_STYLE_TYPE.CHARACTER)
    style.name = profile.get("references", {}).get("characterStyleName", "Hyperlink")
    style.font.color.rgb = RGBColor.from_string(profile.get("references", {}).get("color", "#0000FF").lstrip("#"))
    style.font.underline = profile.get("references", {}).get("underline", True)


def _bind_heading_numbering(paragraph, level: int, num_id: int) -> None:
    ppr = paragraph._p.get_or_add_pPr()
    num_pr = ppr.find(qn("w:numPr"))
    if num_pr is None:
        num_pr = OxmlElement("w:numPr")
        ppr.append(num_pr)
    ilvl = OxmlElement("w:ilvl")
    ilvl.set(qn("w:val"), str(level - 1))
    num_id_element = OxmlElement("w:numId")
    num_id_element.set(qn("w:val"), str(num_id))
    num_pr.extend((ilvl, num_id_element))


def _clear_heading_numbering(paragraph) -> None:
    """Keep front-matter headings out of the body's chapter sequence."""
    ppr = paragraph._p.get_or_add_pPr()
    num_pr = ppr.find(qn("w:numPr"))
    if num_pr is not None:
        ppr.remove(num_pr)
    outline = ppr.find(qn("w:outlineLvl"))
    if outline is not None:
        ppr.remove(outline)


def _neutralize_front_matter_style(document: Document, style_id: str = "TOCHeading") -> None:
    """Prevent TOC headings from inheriting the body Heading1 numbering chain."""
    try:
        style = _style_by_id(document, style_id)
    except KeyError:
        return
    based_on = style._element.find(qn("w:basedOn"))
    if based_on is None:
        based_on = OxmlElement("w:basedOn")
        style._element.insert(1, based_on)
    based_on.set(qn("w:val"), "Normal")
    ppr = style._element.find(qn("w:pPr"))
    if ppr is not None:
        for tag in ("w:numPr", "w:outlineLvl"):
            element = ppr.find(qn(tag))
            if element is not None:
                ppr.remove(element)


def _actual_style_name(document: Document, style_id: str) -> str:
    for style in document.styles:
        if style.style_id == style_id:
            # Word resolves STYLEREF against the serialized w:name, not python-docx's display-normalized name.
            name = style._element.find(qn("w:name"))
            return name.get(qn("w:val")) if name is not None else style.name
    raise ValueError(f"base template lacks style ID {style_id}")


def _apply_profile(document: Document, profile: dict[str, Any]) -> None:
    body = profile.get("body", {})
    normal = document.styles["Normal"]
    normal.font.name = body.get("fontFamily", "Times New Roman")
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), body.get("fontFamily", "Times New Roman"))
    normal.font.size = Pt(body.get("fontSizePt", 12))
    section = document.sections[0]
    page = profile.get("page", {})
    margins = page.get("marginsCm", {})
    section.top_margin = Cm(margins.get("top", 2))
    section.right_margin = Cm(margins.get("right", 2))
    section.bottom_margin = Cm(margins.get("bottom", 2))
    section.left_margin = Cm(margins.get("left", 2))
    if page.get("size") == "a4":
        section.page_width, section.page_height = Cm(21), Cm(29.7)
    else:
        section.page_width, section.page_height = Cm(21.59), Cm(27.94)
    if "Caption" not in [style.name for style in document.styles]:
        document.styles.add_style("Caption", WD_STYLE_TYPE.PARAGRAPH)
    _neutralize_front_matter_style(document)
    _ensure_profile_heading_styles(document, profile)
    _ensure_hyperlink_style(document, profile)
    for level in range(1, 10):
        role = profile.get("styles", {}).get("roles", {}).get(f"headingLevel{level}")
        if not role:
            continue
        style = _style_by_id(document, role["styleId"])
        name = style._element.find(qn("w:name"))
        if name is not None:
            name.set(qn("w:val"), role["styleName"])
        # The locale base may carry italic on Heading4; CTD headings are upright.
        style.font.italic = profile.get("headingStyle", {}).get("italic", False)
        geometry = _heading_geometry(profile, level)
        if geometry is not None:
            left, hanging = geometry
            style.paragraph_format.left_indent = Pt(left / 20)
            style.paragraph_format.first_line_indent = Pt(-hanging / 20)
            style.paragraph_format.tab_stops.clear_all()
            style.paragraph_format.tab_stops.add_tab_stop(Pt(left / 20), WD_TAB_ALIGNMENT.LIST)
    # Keep role references honest: profile style IDs must exist in the accepted base.
    available = {style.style_id for style in document.styles}
    for role_name, role in profile.get("styles", {}).get("roles", {}).items():
        if role.get("styleId") not in available:
            raise ValueError(f"base template lacks profile style role {role_name}: {role.get('styleId')}")


def _label(profile: dict[str, Any], kind: str, language: str) -> str:
    labels = profile["caption"][kind]["labels"]
    return labels.get(language) or labels.get(profile.get("languageFallback", "")) or ""


def _caption(document: Document, profile: dict[str, Any], language: str, kind: str, block: dict[str, Any],
             bookmark_id: int, sequence: int) -> tuple[Any, dict[str, Any]]:
    conf = profile["caption"][kind]
    style_role = conf["chapterStyleRole"]
    chapter_role_config = profile["styles"]["roles"][style_role]
    chapter_style = _actual_style_name(document, chapter_role_config["styleId"])
    paragraph = document.add_paragraph(style=_style_by_id(document, profile["styles"]["roles"][conf["captionStyleRole"]]["styleId"]))
    caption_style_config = profile.get("captionStyle", {})
    paragraph.alignment = 1 if caption_style_config.get("alignment", "center") == "center" else None
    paragraph.paragraph_format.space_before = Pt(caption_style_config.get("spaceBeforePt", 0))
    paragraph.paragraph_format.space_after = Pt(caption_style_config.get("spaceAfterPt", 6))
    paragraph.paragraph_format.line_spacing = caption_style_config.get("lineSpacing", 1)
    caption_style = _style_by_id(document, profile["styles"]["roles"][conf["captionStyleRole"]]["styleId"])
    caption_style.font.size = Pt(caption_style_config.get("fontSizePt", 12))
    caption_style.font.bold = caption_style_config.get("bold", True)
    caption_style.font.italic = caption_style_config.get("italic", False)
    bookmark = _stable_bookmark(block["id"])
    chapter = ".".join(block.get("_currentChapter", [])) or "0"
    append_caption(paragraph, bookmark_id, bookmark, _label(profile, kind, language), chapter_style,
                   conf["sequenceIdentifier"], conf["sequenceResetLevel"], conf["separator"], chapter,
                   str(sequence), block["title"])
    return paragraph, {"objectId": block["id"], "bookmark": bookmark, "kind": kind,
                       "cachedDisplay": f"{_label(profile, kind, language)} {chapter}{conf['separator']}{sequence}"}


def expected_manifest(model: dict[str, Any], profile: dict[str, Any], task: dict[str, Any], hashes: dict[str, str]) -> dict[str, Any]:
    objects, captions, references, tables, images = [], [], [], [], []
    chapter: list[str] = []
    seq = {"table": 0, "figure": 0}
    for position, block in enumerate(model["blocks"]):
        kind = block["type"]
        if kind == "heading":
            chapter = block.get("numberPath", chapter)
        if kind in {"heading", "table", "figure"}:
            objects.append({"id": block["id"], "type": kind, "order": position})
        if kind in seq:
            seq[kind] += 1
            conf = profile["caption"][kind]
            label = _label(profile, kind, model["language"])
            number = ".".join(chapter) or "0"
            captions.append({"objectId": block["id"], "bookmark": _stable_bookmark(block["id"]), "kind": kind,
                             "cachedDisplay": f"{label} {number}{conf['separator']}{seq[kind]}"})
            if kind == "table": tables.append({"id": block["id"], "rows": len(block["rows"]), "columns": len(block["rows"][0])})
            else: images.append({"id": block["id"], "src": block["src"]})
        if kind in {"paragraph", "list"}:
            inlines = block["inlines"] if kind == "paragraph" else [inline for item in block["items"] for inline in item["inlines"]]
            for inline_index, inline in enumerate(inlines):
                if inline["type"] == "crossReference":
                    references.append({"block": position, "inline": inline_index, "targetId": inline["targetId"]})
    toc = profile.get("toc", {}) if task.get("emitLists", False) else {}
    toc_fields = []
    toc_level = task.get("tocMaxLevel", toc.get("bodyMaxLevel", 3))
    if toc.get("bodyEnabled"):
        toc_fields.append({"kind": "toc", "instruction": f'TOC \\o "1-{toc_level}" \\h'})
    if toc.get("tableListEnabled"):
        toc_fields.append({"kind": "tables", "instruction": 'TOC \\c "Table" \\h'})
    if toc.get("figureListEnabled"):
        toc_fields.append({"kind": "figures", "instruction": 'TOC \\c "Figure" \\h'})
    return {"manifestVersion": "0.0.1", "createdAt": datetime.now(timezone.utc).isoformat(), "compilerVersion": __version__,
            "hashes": hashes, "objects": objects, "captions": captions, "crossReferences": references,
            "tables": tables, "images": images, "tocFields": toc_fields,
            "expectedFieldCount": len(captions) * 2 + len(references) + len(toc_fields)}


def _render(model: dict[str, Any], profile: dict[str, Any], task: dict[str, Any], base: Path, output: Path) -> dict[str, Any]:
    document = Document(base)
    _apply_profile(document, profile)
    first_path = next((block.get("numberPath", []) for block in model["blocks"] if block.get("type") == "heading"), [])
    heading_num_id = _ensure_heading_numbering(document, first_path, profile)
    language = model["language"]
    current_chapter: list[str] = []
    # Precompute stable caption targets so a reference may legally precede its object.
    caption_map: dict[str, dict[str, Any]] = {
        item["objectId"]: item for item in expected_manifest(model, profile, task, {}).get("captions", [])
    }
    table_seq = figure_seq = 0
    bookmark_id = 1
    toc = profile.get("toc", {}) if task.get("emitLists", False) else {}
    toc_titles = {"toc": "目录" if language == "zh-CN" else "Contents",
                  "tables": "表目录" if language == "zh-CN" else "List of Tables",
                  "figures": "图目录" if language == "zh-CN" else "List of Figures"}
    toc_level = task.get("tocMaxLevel", toc.get("bodyMaxLevel", 3))
    toc_instructions = {
        "toc": f'TOC \\o "1-{toc_level}" \\h',
        "tables": 'TOC \\c "Table" \\h',
        "figures": 'TOC \\c "Figure" \\h',
    }
    enabled = {"toc": toc.get("bodyEnabled"), "tables": toc.get("tableListEnabled"), "figures": toc.get("figureListEnabled")}
    for part in toc.get("order", ["toc", "tables", "figures"]):
        if not enabled.get(part):
            continue
        toc_heading = document.add_paragraph(toc_titles[part], style="TOC Heading")
        _clear_heading_numbering(toc_heading)
        toc_paragraph = document.add_paragraph()
        append_toc_field(toc_paragraph, toc_instructions[part])
    for block in model["blocks"]:
        kind = block["type"]
        if kind == "heading":
            current_chapter = block.get("numberPath", current_chapter)
            role = profile["styles"]["roles"][f"headingLevel{block['level']}"]
            paragraph = document.add_paragraph(block["content"], style=_style_by_id(document, role["styleId"]))
            _bind_heading_numbering(paragraph, block["level"], heading_num_id)
            paragraph.paragraph_format.keep_with_next = True
        elif kind in {"paragraph", "list"}:
            if kind == "list":
                geometry = profile.get("listStyle", {}).get(block["kind"], {"markerPt": 18, "textPt": 42})
                marker, text = round(geometry["markerPt"] * 20), round(geometry["textPt"] * 20)
                list_num = _new_list_numbering(document, block["kind"], block.get("start", 1), marker, text)
                items = block["items"]
            else:
                items = [block]
            for item in items:
                paragraph = document.add_paragraph()
                if kind == "list":
                    _bind_heading_numbering(paragraph, 1, list_num)
                    paragraph.paragraph_format.left_indent = Pt(text / 20)
                    paragraph.paragraph_format.first_line_indent = Pt((marker - text) / 20)
                    paragraph.paragraph_format.tab_stops.add_tab_stop(Pt(text / 20), WD_TAB_ALIGNMENT.LIST)
                for inline in item["inlines"]:
                    if inline["type"] == "text":
                        paragraph.add_run(inline["text"])
                    elif inline["type"] == "crossReference":
                        target = caption_map[inline["targetId"]]
                        references = profile.get("references", {})
                        append_cross_reference(paragraph, target["bookmark"], target["cachedDisplay"],
                                               references.get("color", "#0000FF"), references.get("underline", True))
                    else:
                        raise ValueError("literature citations are not implemented")
        elif kind == "table":
            table_seq += 1
            copy = dict(block, _currentChapter=current_chapter)
            _, entry = _caption(document, profile, language, "table", copy, bookmark_id, table_seq)
            bookmark_id += 1
            caption_map[block["id"]] = entry
            rows = block["rows"]
            table = document.add_table(rows=len(rows), cols=len(rows[0]))
            table.style = "Table Grid"
            for row_index, row in enumerate(rows):
                for col_index, value in enumerate(row):
                    table.cell(row_index, col_index).text = value
            _set_repeat_table_header(table.rows[0])
        elif kind == "figure":
            figure_seq += 1
            image_path = (Path(task.get("resourceRoot", model["resourceRoot"])) / block["src"]).resolve()
            document.add_picture(str(image_path))
            image_paragraph = document.paragraphs[-1]
            image_paragraph.alignment = 1
            image_paragraph.paragraph_format.space_before = Pt(0)
            image_paragraph.paragraph_format.space_after = Pt(6)
            image_paragraph.paragraph_format.line_spacing = 1
            copy = dict(block, _currentChapter=current_chapter)
            _, entry = _caption(document, profile, language, "figure", copy, bookmark_id, figure_seq)
            bookmark_id += 1
            caption_map[block["id"]] = entry
        elif kind == "references":
            document.add_paragraph("References", style="Heading 1")
            for item in block["items"]:
                document.add_paragraph(item["content"])
        else:
            raise ValueError(f"unsupported block type {kind}")
    _set_field_update_on_open(document)
    document.core_properties.title = str(model.get("metadata", {}).get("title", ""))
    document.core_properties.comments = "Generated by arachne-loom; update fields in desktop Word before release."
    document.save(output)
    return caption_map


def compile_document(model: dict[str, Any], profile: dict[str, Any], task: dict[str, Any], out_dir: str | Path,
                     model_path: str | Path | None = None, profile_path: str | Path | None = None,
                     task_path: str | Path | None = None) -> Path:
    destination = Path(out_dir).resolve()
    task_dir = Path(task_path).resolve().parent if task_path else Path.cwd()
    validation_task = dict(task)
    resource_value = Path(task.get("resourceRoot", model.get("resourceRoot", ".")))
    validation_task["resourceRoot"] = str((task_dir / resource_value).resolve()) if not resource_value.is_absolute() else str(resource_value.resolve())
    validate_or_raise(model, profile, validation_task)
    base_value = Path(task.get("baseTemplate", Path(__file__).parents[1] / "templates" / "base.docx"))
    base = (task_dir / base_value).resolve() if not base_value.is_absolute() else base_value.resolve()
    if not base.is_file():
        raise FileNotFoundError(f"base template not found: {base}")
    hashes = {"base": _hash(base)}
    for key, path in (("model", model_path), ("profile", profile_path), ("task", task_path)):
        if path:
            hashes[key] = _hash(Path(path))
    parent = destination.parent
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}.tmp-", dir=parent))
    try:
        manifest = expected_manifest(model, profile, task, hashes)
        render_task = dict(task)
        resource_value = Path(task.get("resourceRoot", model.get("resourceRoot", ".")))
        render_task["resourceRoot"] = str((task_dir / resource_value).resolve()) if not resource_value.is_absolute() else str(resource_value.resolve())
        _render(model, profile, render_task, base, temporary / "document.docx")
        (temporary / "expected-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        report = {"status": "STATIC_PASS_PENDING_WORD_ACCEPTANCE", "staticChecks": ["input validation", "DOCX generation", "manifest emitted"],
                  "wordAcceptance": {"status": "PENDING", "reason": "Requires supported desktop Microsoft Word evidence; not inferred from OOXML."}}
        (temporary / "acceptance-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (temporary / "unresolved-issues.json").write_text(json.dumps([{"severity": "manual", "issue": "Seven desktop Word behavior tests remain required before release."}], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        from .inspector import inspect_to_file
        actual = inspect_to_file(temporary / "document.docx", temporary / "actual-manifest.json", hashes)
        if actual.get("structuralIssues"):
            raise ValueError(f"generated DOCX has structural field/bookmark issues: {actual['structuralIssues']}")
        if destination.exists():
            backup = destination.with_name(destination.name + ".previous")
            if backup.exists(): shutil.rmtree(backup)
            os.replace(destination, backup)
            try: os.replace(temporary, destination)
            except Exception:
                os.replace(backup, destination)
                raise
            shutil.rmtree(backup)
        else:
            os.replace(temporary, destination)
        return destination
    finally:
        if temporary.exists(): shutil.rmtree(temporary)
