from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_workflow_routes_existing_docx_and_requires_native_numbering():
    workflow = (ROOT / "integrations/claude-code/workflow.md").read_text()

    assert "existing DOCX" in workflow
    assert "Always write to a different output path" in workflow
    assert "does not convert manual typed numbering" in workflow
    assert "up to nine nested list levels" in workflow
    assert "native Word numbering" in workflow
    assert "do not substitute an ad hoc file-specific patch" in workflow


def test_heading_guidance_requires_compact_measured_number_width():
    workflow = (ROOT / "integrations/claude-code/workflow.md").read_text()
    reference = (ROOT / "docs/heading-indentation.md").read_text()

    assert "compact hanging width" in workflow
    assert "72 pt" in reference
    assert "smallest hanging area" in reference
    assert "number-to-text gap" in reference


def test_word_acceptance_checks_marker_text_spacing_and_line_breaks():
    workflow = (ROOT / "integrations/claude-code/workflow.md").read_text()

    assert "number-to-text spacing is compact" in workflow
    assert "no marker-only line or unintended break" in workflow
    assert "Save, close, reopen" in workflow
