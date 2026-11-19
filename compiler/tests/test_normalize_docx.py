from docx import Document
from docx.oxml.ns import qn
import zipfile
from hashlib import sha256
import json
from pathlib import Path

from arachne_loom.generator import compile_document
from arachne_loom.normalizer import normalize_docx

ROOT = Path(__file__).resolve().parents[2]


def test_normalizes_native_heading_and_list_geometry_without_changing_text(tmp_path):
    source = tmp_path / "source.docx"
    output = tmp_path / "normalized.docx"
    doc = Document()
    doc.add_paragraph("1. Heading one", style="Heading 1")
    doc.add_paragraph("1.1 Heading two", style="Heading 2")
    doc.add_paragraph("manual 1. keep literal")
    doc.add_paragraph("Native item", style="List Bullet")
    doc.add_table(rows=1, cols=1).cell(0, 0).paragraphs[0].text = "Table heading"
    doc.tables[0].cell(0, 0).paragraphs[0].style = "Heading 1"
    doc.save(source)

    report = normalize_docx(source, output, {
        "headingStyle": {"indentation": {"basePt": 0, "incrementPt": 18, "hangingPt": 24}},
        "listStyle": {"unordered": {"markerPt": 18, "textPt": 42}},
    })

    result = Document(output)
    assert [p.text for p in result.paragraphs] == [p.text for p in Document(source).paragraphs]
    assert result.tables[0].cell(0, 0).text == Document(source).tables[0].cell(0, 0).text
    assert report["headingsUpdated"] == 3
    assert report["listsUpdated"] == 1
    assert report["manualNumberingChanged"] == 0
    assert result.paragraphs[0].style.name == "Heading 1"
    assert result.paragraphs[1].style.name == "Heading 2"
    assert report["manualNumberingChanged"] == 0
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(output) as normalized:
        assert original.namelist() == normalized.namelist()
        for name in original.namelist():
            if name not in {"word/document.xml", "word/numbering.xml"}:
                assert sha256(original.read(name)).digest() == sha256(normalized.read(name)).digest()


def test_rejects_input_output_alias_and_leaves_source_unchanged(tmp_path):
    source = tmp_path / "source.docx"
    doc = Document()
    doc.add_paragraph("Heading", style="Heading 1")
    doc.save(source)
    before = source.read_bytes()

    try:
        normalize_docx(source, source, {})
    except ValueError as exc:
        assert "different" in str(exc)
    else:
        raise AssertionError("normalizer must not overwrite its source")
    assert source.read_bytes() == before


def test_nested_list_marker_and_text_geometry_steps_together_before_and_after_normalize(tmp_path):
    profile = json.loads((ROOT / "profiles/ctd/zh-CN/config.json").read_text())
    profile["listStyle"] = {
        "ordered": {"markerPt": 18, "textPt": 42},
        "unordered": {"markerPt": 18, "textPt": 42},
    }
    task = {
        "taskId": "nested-list-geometry",
        "profileLanguage": "zh-CN",
        "resourceRoot": str(ROOT),
        "baseTemplate": str(ROOT / "compiler/templates/zh-CN/base.docx"),
    }
    model = {
        "schemaVersion": "0.0.1-provisional",
        "language": "zh-CN",
        "metadata": {},
        "resourceRoot": str(ROOT),
        "blocks": [{
            "type": "list",
            "kind": "ordered",
            "items": [
                {"level": level, "kind": "ordered", "inlines": [{"type": "text", "text": f"Level {level + 1}"}]}
                for level in range(9)
            ],
        }],
    }
    generated = compile_document(model, profile, task, tmp_path / "generated") / "document.docx"
    normalized = tmp_path / "normalized.docx"

    def assert_progressive_geometry(path):
        doc = Document(path)
        numbering = doc.part.numbering_part.element
        for level, paragraph in enumerate(doc.paragraphs):
            num_pr = paragraph._p.xpath("./w:pPr/w:numPr")[0]
            assert int(num_pr.find(qn("w:ilvl")).get(qn("w:val"))) == level
            num_id = num_pr.find(qn("w:numId")).get(qn("w:val"))
            abstract_id = numbering.xpath(f'./w:num[@w:numId="{num_id}"]/w:abstractNumId')[0].get(qn("w:val"))
            abstract = numbering.xpath(f'./w:abstractNum[@w:abstractNumId="{abstract_id}"]')[0]
            numbering_level = next(item for item in abstract.findall(qn("w:lvl"))
                                   if item.get(qn("w:ilvl")) == str(level))
            indent = numbering_level.find(qn("w:pPr")).find(qn("w:ind"))
            paragraph_indent = paragraph._p.xpath("./w:pPr/w:ind")[0]
            expected_text = 42 * 20 + level * 360
            expected_marker = 18 * 20 + level * 360
            assert int(indent.get(qn("w:left"))) == expected_text
            assert int(indent.get(qn("w:hanging"))) == expected_text - expected_marker
            assert int(paragraph_indent.get(qn("w:left"))) == expected_text
            assert int(paragraph_indent.get(qn("w:hanging"))) == expected_text - expected_marker

    assert_progressive_geometry(generated)
    normalize_docx(generated, normalized, profile)
    assert_progressive_geometry(normalized)
