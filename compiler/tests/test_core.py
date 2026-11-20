import json
from pathlib import Path

import pytest
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from arachne_loom.cli import main

from arachne_loom.generator import compile_document
from arachne_loom.inspector import inspect
from arachne_loom.parser import parse_markdown
from arachne_loom.validator import validate


ROOT = Path(__file__).parents[3]
PACKAGE = ROOT / "arachne-loom"
PROFILE = PACKAGE / "profiles/ctd/config.json"
TASK = PACKAGE / "examples/quickstart/config.json"
BASE = PACKAGE / "compiler/templates/base.docx"


def test_parse_and_validate_minimal():
    model = parse_markdown(PACKAGE / "examples/quickstart/sample.md")
    profile = json.loads(PROFILE.read_text())
    task = json.loads(TASK.read_text())
    task["baseTemplate"] = str(BASE)
    assert validate(model, profile, task) == []


def test_invalid_duplicate_and_missing_reference():
    model = {"schemaVersion": "0.0.1-provisional", "language": "zh-CN", "metadata": {}, "resourceRoot": ".", "blocks": [
        {"type": "heading", "id": "h", "level": 1, "content": "x", "numberPath": ["1"]},
        {"type": "table", "id": "tbl", "title": "x", "headerRows": 1, "rows": [["h"], ["v"]]},
        {"type": "table", "id": "tbl", "title": "x", "headerRows": 1, "rows": [["h"], ["v"]]},
        {"type": "paragraph", "inlines": [{"type": "crossReference", "targetId": "missing"}]},
    ]}
    profile = json.loads(PROFILE.read_text())
    errors = validate(model, profile, {"resourceRoot": "."})
    assert any("duplicate id" in error for error in errors)
    assert any("does not exist" in error for error in errors)


def test_compile_and_independent_inspect(tmp_path):
    model_path = tmp_path / "model.json"
    profile_path = tmp_path / "profile.json"
    task_path = tmp_path / "task.json"
    model = parse_markdown(PACKAGE / "examples/quickstart/sample.md")
    profile = json.loads(PROFILE.read_text())
    task = {"taskId": "test", "resourceRoot": str(PACKAGE / "examples/quickstart"), "baseTemplate": str(BASE)}
    for path, value in ((model_path, model), (profile_path, profile), (task_path, task)):
        path.write_text(json.dumps(value), encoding="utf-8")
    output = compile_document(model, profile, task, tmp_path / "build", model_path, profile_path, task_path)
    actual = inspect(output / "document.docx")
    assert actual["fieldCount"] == 3
    assert len(actual["bookmarks"]) == 1
    assert actual["structuralIssues"] == []
    assert (output / "expected-manifest.json").is_file()


def test_explicit_toc_depth_and_presentation(tmp_path):
    model = parse_markdown(PACKAGE / "examples/quickstart/figure-sample.md")
    profile = json.loads((PACKAGE / "profiles/ctd/zh-CN/config.json").read_text())
    task = json.loads((PACKAGE / "examples/quickstart/figure-config.json").read_text())
    task["baseTemplate"] = str(PACKAGE / "compiler/templates/base.docx")
    task["resourceRoot"] = str(PACKAGE / "examples/quickstart")
    output = compile_document(model, profile, task, tmp_path / "figure")
    actual = inspect(output / "document.docx")
    assert 'TOC \\o "1-4" \\h' in actual["tocFields"]
    document = Document(output / "document.docx")
    heading4 = next(p for p in document.paragraphs if p.text == "研究设计")
    caption = next(p for p in document.paragraphs if p.text.startswith("图 "))
    assert heading4.style.font.italic is False
    assert caption.alignment == 1


def test_csr_captions_use_top_level_chapter_number(tmp_path):
    model = parse_markdown(PACKAGE / "examples/quickstart/sample.md")
    heading = next(block for block in model["blocks"] if block["type"] == "heading")
    heading["level"] = 1
    heading["numberPath"] = ["1"]
    profile = json.loads((PACKAGE / "profiles/csr/zh-CN/config.json").read_text())
    task = json.loads((PACKAGE / "examples/quickstart/config.json").read_text())
    task["baseTemplate"] = str(BASE)
    task["resourceRoot"] = str(PACKAGE / "examples/quickstart")
    output = compile_document(model, profile, task, tmp_path / "csr")
    actual = inspect(output / "document.docx")
    assert 'STYLEREF "标题 1" \\s \\* MERGEFORMAT' in actual["fields"]
    assert "SEQ Table \\s 1 \\* ARABIC" in actual["fields"]
    assert actual["structuralIssues"] == []


@pytest.mark.parametrize("document_type, language, custom", [
    ("ctd", "zh-CN", False), ("ctd", "en-US", False),
    ("csr", "zh-CN", False), ("csr", "en-US", False),
    ("csr", "zh-CN", True),
])
def test_compile_applies_body_and_table_format_from_profile(tmp_path, document_type, language, custom):
    model = parse_markdown(PACKAGE / "examples/quickstart/sample.md")
    model["language"] = language
    heading = next(block for block in model["blocks"] if block["type"] == "heading")
    if document_type == "csr":
        heading.update(level=1, numberPath=["1"])
    profile_path = PACKAGE / f"profiles/{document_type}/{language}/config.json"
    spacing, alignment, after, table_size = 1.5, WD_ALIGN_PARAGRAPH.JUSTIFY, 6, 10.5
    if custom:
        profile = json.loads(profile_path.read_text())
        profile["body"].update(lineSpacing=2, alignment="left", paragraphAfterPt=0)
        profile["table"]["fontSizePt"] = 9
        profile_path = tmp_path / "profile.json"
        profile_path.write_text(json.dumps(profile))
        spacing, alignment, after, table_size = 2, WD_ALIGN_PARAGRAPH.LEFT, 0, 9
    model_path = tmp_path / "model.json"
    model_path.write_text(json.dumps(model))
    task_path = tmp_path / "task.json"
    task_path.write_text(json.dumps({"baseTemplate": str(PACKAGE / f"compiler/templates/{language}/base.docx")}))
    output = tmp_path / "build"
    assert main(["compile", str(model_path), str(profile_path), str(task_path), "--out-dir", str(output)]) == 0

    document = Document(output / "document.docx")
    for paragraph in document.paragraphs:
        if paragraph.style.name == "Normal":
            assert paragraph.paragraph_format.line_spacing == spacing
            assert paragraph.alignment == alignment
            assert paragraph.paragraph_format.space_after == Pt(after)
    assert sum(p.style.name == "Normal" for p in document.paragraphs) == 2
    assert document.paragraphs[0].paragraph_format.line_spacing is None
    caption = next(p for p in document.paragraphs if p.style.name == "Caption")
    assert caption.paragraph_format.line_spacing == 1
    assert caption.alignment == WD_ALIGN_PARAGRAPH.CENTER
    for row in document.tables[0].rows:
        for cell in row.cells:
            assert cell.text
            assert all(run.font.size == Pt(table_size) for p in cell.paragraphs for run in p.runs)


def test_inspector_detects_crossing_bookmark(tmp_path):
    source = PACKAGE / "examples/quickstart/negative-fixtures/document-word-broken.docx"
    actual = inspect(source)
    assert any(issue["type"] == "bookmark-spans-paragraphs" for issue in actual["structuralIssues"])
    assert any(issue["type"] == "cross-paragraph-field" for issue in actual["structuralIssues"])


def test_no_sensitive_data_in_repo():
    """Layer 3: the leak-guard scanner must find nothing. Same scanner the
    pre-push hook and CI run, so pytest is also a leak gate."""
    import subprocess
    result = subprocess.run(
        ["python3", str(PACKAGE / "scripts" / "scan-sensitive.py")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"leak guard failed:\n{result.stderr}"


def test_csr_native_caption_results_restart_at_chapters(tmp_path):
    resources = PACKAGE / 'examples/quickstart'
    profile = json.loads((PACKAGE / 'profiles/csr/zh-CN/config.json').read_text())
    model = parse_markdown(resources / 'sample.md')
    blocks = []
    for chapter in (1, 2):
        blocks.extend([
            {'type': 'heading', 'id': f'h{chapter}', 'level': 1, 'numberPath': [str(chapter)], 'content': '章'},
            {'type': 'heading', 'id': f's{chapter}', 'level': 2, 'numberPath': [str(chapter), '1'], 'content': '节'},
            {'type': 'paragraph', 'inlines': [{'type': 'crossReference', 'targetId': f't{chapter}'}]},
            {'type': 'table', 'id': f't{chapter}', 'title': '表格', 'headerRows': 1, 'rows': [['标题'], ['值']]},
            {'type': 'figure', 'id': f'f{chapter}', 'title': '图片', 'src': 'images/figure.png'},
        ])
    blocks.append({'type': 'table', 'id': 't3', 'title': '续表', 'headerRows': 1, 'rows': [['标题']]})
    model['blocks'] = blocks
    output = compile_document(model, profile, {'baseTemplate': str(BASE), 'resourceRoot': str(resources)}, tmp_path / 'build')
    document = Document(output / 'document.docx')
    texts = [p.text for p in document.paragraphs]
    for chapter in (1, 2):
        assert f'表 {chapter}-1' in texts
        assert f'表 {chapter}-1 表格' in texts
        assert f'图 {chapter}-1 图片' in texts
    assert '表 2-2 续表' in texts
    manifest = json.loads((output / 'expected-manifest.json').read_text())
    assert [item['cachedDisplay'] for item in manifest['captions']] == ['表 1-1', '图 1-1', '表 2-1', '图 2-1', '表 2-2']
    fields = inspect(output / 'document.docx')['fields']
    assert fields.count(r'SEQ Table \s 1 \* ARABIC') == 3
    assert fields.count(r'SEQ Figure \s 1 \* ARABIC') == 2
    assert sum(field.startswith('REF ') for field in fields) == 2


def test_native_profile_overrides(tmp_path):
    from docx.oxml.ns import qn
    model = parse_markdown(PACKAGE / 'examples/quickstart/sample.md')
    profile = json.loads(PROFILE.read_text())
    profile['page']['orientation'] = 'landscape'
    profile['table']['repeatHeaderRow'] = False
    profile['caption']['table'].update(position='below', sequenceIdentifier='StudyTable')
    profile['captionStyle']['alignment'] = 'right'
    profile['references']['characterStyleId'] = 'StudyRef'
    output = compile_document(model, profile, {'baseTemplate': str(BASE), 'emitLists': True}, tmp_path / 'out')
    path = output / 'document.docx'
    doc = Document(path)
    assert doc.sections[0].page_width > doc.sections[0].page_height
    table = doc.tables[0]
    assert table._tbl.tblPr.find(qn('w:tblW')).get(qn('w:w')) == '5000'
    borders = table._tbl.tblPr.find(qn('w:tblBorders'))
    assert borders.find(qn('w:insideV')).get(qn('w:val')) == 'nil'
    assert not table.rows[0]._tr.xpath('./w:trPr/w:tblHeader')
    assert table._tbl.getnext().xpath('./w:pPr/w:jc/@w:val') == ['right']
    assert doc.element.xpath('.//w:rStyle[@w:val="StudyRef"]')
    assert 'TOC \\c "StudyTable" \\h' in inspect(path)['tocFields']
