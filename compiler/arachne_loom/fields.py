"""Low-level OOXML field and bookmark construction; python-docx has no field API."""

from __future__ import annotations

from docx.oxml import OxmlElement
from docx.oxml.ns import qn


def _field_run_style(run, color: str | None = None, underline: bool = False, character_style: str | None = None) -> None:
    if not color and not underline and not character_style:
        return
    rpr = OxmlElement("w:rPr")
    if character_style:
        style = OxmlElement("w:rStyle")
        style.set(qn("w:val"), character_style)
        rpr.append(style)
    if color:
        color_element = OxmlElement("w:color")
        color_element.set(qn("w:val"), color.lstrip("#"))
        rpr.append(color_element)
    if underline:
        underline_element = OxmlElement("w:u")
        underline_element.set(qn("w:val"), "single")
        rpr.append(underline_element)
    run.insert(0, rpr)


def _run_text(parent, value: str):
    run = OxmlElement("w:r")
    text = OxmlElement("w:t")
    if value.startswith(" ") or value.endswith(" "):
        text.set(qn("xml:space"), "preserve")
    text.text = value
    run.append(text)
    parent.append(run)


def append_field(parent, instruction: str, cached: str, color: str | None = None, underline: bool = False,
                 character_style: str | None = None) -> None:
    for field_type, content in (("begin", None), (None, instruction), ("separate", None), (None, cached), ("end", None)):
        run = OxmlElement("w:r")
        if field_type:
            item = OxmlElement("w:fldChar")
            item.set(qn("w:fldCharType"), field_type)
        elif content == instruction:
            item = OxmlElement("w:instrText")
            item.set(qn("xml:space"), "preserve")
            item.text = content
        else:
            item = OxmlElement("w:t")
            item.text = content
        run.append(item)
        _field_run_style(run, color, underline, character_style)
        parent.append(run)


def append_bookmark_start(parent, bookmark_id: int, name: str) -> None:
    item = OxmlElement("w:bookmarkStart")
    item.set(qn("w:id"), str(bookmark_id))
    item.set(qn("w:name"), name)
    parent.append(item)


def append_bookmark_end(parent, bookmark_id: int) -> None:
    item = OxmlElement("w:bookmarkEnd")
    item.set(qn("w:id"), str(bookmark_id))
    parent.append(item)


def append_caption(paragraph, bookmark_id: int, bookmark: str, label: str, chapter_style_name: str,
                   sequence: str, reset_level: int, separator: str, cached_chapter: str, cached_sequence: str,
                   title: str) -> None:
    container = paragraph._p
    append_bookmark_start(container, bookmark_id, bookmark)
    _run_text(container, f"{label} ")
    append_field(container, f'STYLEREF "{chapter_style_name}" \\s \\* MERGEFORMAT', cached_chapter)
    _run_text(container, separator)
    append_field(container, f"SEQ {sequence} \\s {reset_level} \\* ARABIC", cached_sequence)
    append_bookmark_end(container, bookmark_id)
    _run_text(container, f" {title}")


def append_cross_reference(paragraph, bookmark: str, cached: str, color: str = "#0000FF", underline: bool = True) -> None:
    # Keep the reference as one Word-native REF field, matching Word's own
    # cross-reference structure and avoiding nested-field style loss.
    append_field(paragraph._p, f"REF {bookmark} \\h", cached, color, underline, "Hyperlink")


def append_toc_field(paragraph, instruction: str) -> None:
    """Append an updateable TOC/list field with an empty cached result."""
    append_field(paragraph._p, instruction, "")
