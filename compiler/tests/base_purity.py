"""Static base-package audit; Word open/save evidence remains a separate gate."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

from lxml import etree


def audit(path: str | Path) -> dict:
    path = Path(path)
    findings: list[str] = []
    with zipfile.ZipFile(path) as package:
        names = set(package.namelist())
        required = {"[Content_Types].xml", "word/document.xml", "word/styles.xml", "word/numbering.xml", "word/_rels/document.xml.rels"}
        findings.extend(f"missing:{name}" for name in sorted(required - names))
        for name in required & names:
            try:
                etree.fromstring(package.read(name))
            except etree.XMLSyntaxError as exc:
                findings.append(f"invalid-xml:{name}:{exc}")
        document = package.read("word/document.xml").decode("utf-8", "ignore")
        for token in ("SEQ", "REF", "STYLEREF", "TOC", "bookmarkStart", "commentRangeStart", "w:ins", "w:del"):
            if token in document:
                findings.append(f"residual:{token}")
        media = [name for name in names if name.startswith("word/media/")]
        if media:
            findings.append(f"unrelated-media:{len(media)}")
        content_types = package.read("[Content_Types].xml").decode("utf-8", "ignore")
        if "wordprocessingml.template.main+xml" in content_types:
            findings.append("template-content-type")
    return {"file": str(path), "staticStatus": "PASS" if not findings else "FAIL", "findings": findings,
            "wordOpenSaveStatus": "PENDING", "wordOpenSaveReason": "Requires desktop Word open-save-reopen evidence."}


if __name__ == "__main__":
    result = audit(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["staticStatus"] == "PASS" else 1)
