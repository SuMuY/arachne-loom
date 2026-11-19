from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_workflow_routes_existing_docx_and_requires_native_numbering():
    workflow = (ROOT / "SKILL.md").read_text()

    assert "existing DOCX" in workflow
    assert "Always write to a different output path" in workflow
    assert "does not convert typed numbering" in workflow
    assert "up to nine nested list levels" in workflow
    assert "Word-native numbering" in workflow
    assert "do not use an ad hoc file-specific patch" in workflow


def test_heading_guidance_requires_compact_measured_number_width():
    workflow = (ROOT / "SKILL.md").read_text()
    reference = (ROOT / "docs/heading-indentation.md").read_text()

    assert "compact hanging width" in workflow
    assert "72 pt" in reference
    assert "smallest hanging area" in reference
    assert "number-to-text gap" in reference


def test_word_acceptance_checks_marker_text_spacing_and_line_breaks():
    workflow = (ROOT / "SKILL.md").read_text()

    assert "number-to-text spacing is compact" in workflow
    assert "no marker-only line or unintended break" in workflow
    assert "Save, close, reopen" in workflow


def test_root_skill_is_canonical_and_claude_integration_has_no_duplicate_workflow():
    skill = (ROOT / "SKILL.md").read_text()
    claude_readme = (ROOT / "integrations/claude-code/README.md").read_text()
    integrations = (ROOT / "integrations/README.md").read_text()

    assert skill.startswith("---\nname: arachne-loom\n")
    assert "workbench-neutral" in integrations
    assert "canonical" in integrations
    assert "workflow.md" not in integrations
    assert not (ROOT / "integrations/claude-code/workflow.md").exists()
    assert "Claude SDK dependency" in claude_readme
    assert "up to nine nested list levels" in skill
    assert "Save, close, reopen" in skill
    assert "does not convert typed numbering" in skill
