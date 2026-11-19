import json
from pathlib import Path

import pytest
from docx import Document

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
