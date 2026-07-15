"""Fallback smoke runner for environments without pytest."""

from pathlib import Path
import json
import tempfile

from arachne_loom.generator import compile_document
from arachne_loom.inspector import inspect
from arachne_loom.parser import parse_markdown
from arachne_loom.validator import validate


def main() -> None:
    root = Path(__file__).parents[3] / "arachne-loom"
    profile_path = root / "profiles/ctd/zh-CN/config.json"
    task_path = root / "examples/quickstart/config.json"
    model = parse_markdown(root / "examples/quickstart/sample.md")
    profile = json.loads(profile_path.read_text())
    task = {"taskId": "smoke", "resourceRoot": str(root / "examples/quickstart"), "baseTemplate": str(root / "compiler/templates/base.docx")}
    assert not validate(model, profile, task)
    with tempfile.TemporaryDirectory() as directory:
        output = compile_document(model, profile, task, Path(directory) / "build")
        actual = inspect(output / "document.docx")
        assert actual["fieldCount"] == 3
        assert len(actual["bookmarks"]) == 1
    print("smoke passed")


if __name__ == "__main__":
    main()
