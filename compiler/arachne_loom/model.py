"""Canonical Model helpers. JSON Schema remains the normative input contract."""

from __future__ import annotations

from typing import Any


def canonical_document(language: str, metadata: dict[str, Any], blocks: list[dict[str, Any]], resource_root: str = ".") -> dict[str, Any]:
    return {
        "schemaVersion": "0.0.1-provisional",
        "language": language,
        "metadata": metadata,
        "resourceRoot": resource_root,
        "blocks": blocks,
    }


def text_inline(value: str) -> dict[str, str]:
    return {"type": "text", "text": value}
