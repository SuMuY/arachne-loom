"""Heading geometry must agree in styles and native numbering, across all levels."""
import json
from pathlib import Path

import pytest
from docx import Document
from docx.oxml.ns import qn

from arachne_loom.generator import compile_document
from arachne_loom.validator import validate

ROOT = Path(__file__).resolve().parents[2]


def inputs(locale="zh-CN"):
    profile = json.loads((ROOT / f"profiles/ctd/{locale}/config.json").read_text())
    model = {"schemaVersion": "0.0.1-provisional", "language": locale, "metadata": {},
             "blocks": [{"type": "heading", "id": f"h{i}", "level": i,
                         "content": f"Heading {i}", "numberPath": ["1"] * i}
                        for i in range(1, 10)] +
                       [{"type": "heading", "id": "sibling", "level": 2,
                         "content": "Sibling", "numberPath": ["1", "2"]}]}
    task = {"taskId": "indent-test", "resourceRoot": str(ROOT),
            "baseTemplate": str(ROOT / "compiler/templates/base.docx")}
    return model, profile, task


@pytest.mark.parametrize("locale", ["zh-CN", "en-US"])
@pytest.mark.parametrize("base,step,gap", [(0, 18, 36), (9, 12, 24), (0, 0, 0)])
def test_heading_indentation(tmp_path, locale, base, step, gap):
    model, profile, task = inputs(locale)
    profile["headingStyle"]["indentation"] = {
        "basePt": base, "incrementPt": step, "hangingPt": gap}
    output = compile_document(model, profile, task, tmp_path / "build")
    doc = Document(output / "document.docx")
    numbering = doc.part.numbering_part.element
    num_id = doc.paragraphs[0]._p.xpath("./w:pPr/w:numPr/w:numId")[0].get(qn("w:val"))
    abstract_id = numbering.xpath(f'./w:num[@w:numId="{num_id}"]/w:abstractNumId')[0].get(qn("w:val"))
    levels = numbering.xpath(f'./w:abstractNum[@w:abstractNumId="{abstract_id}"]/w:lvl')
    for level, item in enumerate(levels):
        left = base + level * step + gap
        style = next(s for s in doc.styles if s.style_id == f"Heading{level + 1}").paragraph_format
        assert style.left_indent is not None, "heading indentation is missing"
        assert style.left_indent.pt == left
        assert style.first_line_indent.pt == -gap
        ind = item.find(qn("w:pPr")).find(qn("w:ind"))
        assert int(ind.get(qn("w:left"))) == round(left * 20)
        assert int(ind.get(qn("w:hanging"))) == round(gap * 20)
        tab = item.find(qn("w:pPr")).find(qn("w:tabs")).find(qn("w:tab"))
        assert int(tab.get(qn("w:pos"))) == round(left * 20)
    assert doc.paragraphs[1].style == doc.paragraphs[-1].style


@pytest.mark.parametrize("bad", [None, [], {}, {"basePt": -1}, {"incrementPt": True},
                                     {"hangingPt": "18"}, {"basePt": float("nan")},
                                     {"basePt": float("inf")}, {"basPt": 12}])
def test_invalid_indentation_rejected(bad):
    model, profile, task = inputs()
    profile["headingStyle"]["indentation"] = bad
    assert any("indentation" in error for error in validate(model, profile, task))


def test_omitted_indentation_keeps_template_geometry(tmp_path):
    model, profile, task = inputs()
    original = Document(task["baseTemplate"])
    output = compile_document(model, profile, task, tmp_path / "build")
    doc = Document(output / "document.docx")
    for level in range(1, 10):
        assert next(s for s in doc.styles if s.style_id == f"Heading{level}").paragraph_format.left_indent == next(s for s in original.styles if s.style_id == f"Heading{level}").paragraph_format.left_indent
