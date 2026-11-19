from docx import Document
import zipfile
from hashlib import sha256

from arachne_loom.normalizer import normalize_docx


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
