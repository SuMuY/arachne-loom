"""Strict deterministic input checks. Unsupported semantic structures are rejected."""

from __future__ import annotations

import json
import mimetypes
import math
import re
from pathlib import Path
from typing import Any


class ValidationError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _role(profile: dict[str, Any], role: str) -> dict[str, Any] | None:
    return profile.get("styles", {}).get("roles", {}).get(role)


def validate(model: dict[str, Any], profile: dict[str, Any], task: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    heading = profile.get("headingStyle", {})
    if "indentation" in heading:
        config = heading["indentation"]
        keys = {"basePt", "incrementPt", "hangingPt"}
        if not isinstance(config, dict) or set(config) != keys:
            errors.append("headingStyle.indentation requires exactly basePt, incrementPt, hangingPt")
        else:
            for key, value in config.items():
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                    errors.append(f"headingStyle.indentation.{key} must be a finite non-negative number")
    if "listStyle" in profile:
        config = profile["listStyle"]
        if not isinstance(config, dict) or set(config) - {"ordered", "unordered"}:
            errors.append("listStyle must contain only ordered/unordered objects")
        else:
            for kind, geometry in config.items():
                if not isinstance(geometry, dict) or set(geometry) != {"markerPt", "textPt"}:
                    errors.append(f"listStyle.{kind} requires markerPt and textPt")
                elif any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in geometry.values()):
                    errors.append(f"listStyle.{kind} positions must be finite non-negative numbers")
                elif geometry["textPt"] <= geometry["markerPt"]:
                    errors.append(f"listStyle.{kind}.textPt must exceed markerPt")
    if model.get("schemaVersion") != "0.0.1-provisional":
        errors.append("unsupported or missing schemaVersion")
    if model.get("language") not in {"zh-CN", "en-US"}:
        errors.append("language must be zh-CN or en-US")
    if profile.get("language") and profile["language"] != model.get("language"):
        errors.append(f"profile language {profile['language']} does not match model language {model.get('language')}")
    if task.get("profileLanguage") and task["profileLanguage"] != profile.get("language"):
        errors.append(f"task profileLanguage {task['profileLanguage']} does not match profile language {profile.get('language')}")
    resource_root = Path(task.get("resourceRoot", model.get("resourceRoot", "."))).resolve()
    if not resource_root.is_dir():
        errors.append(f"resourceRoot does not exist: {resource_root}")
    ids: set[str] = set()
    targets: set[str] = set()
    refs: list[str] = []
    previous_level = 0
    seen_heading_levels: set[int] = set()
    for position, block in enumerate(model.get("blocks", []), start=1):
        kind = block.get("type")
        if kind == "heading":
            level = block.get("level")
            if not isinstance(level, int) or not 1 <= level <= 9:
                errors.append(f"block {position}: heading level must be 1..9")
            elif previous_level and level > previous_level + 1:
                errors.append(f"block {position}: heading level jumps from {previous_level} to {level}")
            previous_level = level if isinstance(level, int) else previous_level
            if isinstance(level, int):
                seen_heading_levels.add(level)
            role = _role(profile, f"headingLevel{level}") if isinstance(level, int) else None
            if not role:
                errors.append(f"block {position}: profile lacks headingLevel{level}")
        if kind in {"heading", "table", "figure"}:
            value = block.get("id")
            if not isinstance(value, str) or not ID.match(value):
                errors.append(f"block {position}: invalid stable id")
            elif value in ids:
                errors.append(f"block {position}: duplicate id {value}")
            else:
                ids.add(value)
                if kind in {"table", "figure"}:
                    targets.add(value)
        if kind == "list":
            if block.get("kind") not in {"ordered", "unordered"}:
                errors.append(f"block {position}: list kind must be ordered or unordered")
            start = block.get("start", 1)
            if isinstance(start, bool) or not isinstance(start, int) or not 1 <= start <= 2147483647:
                errors.append(f"block {position}: list start must be a positive 32-bit integer")
            items = block.get("items")
            if not isinstance(items, list) or not items:
                errors.append(f"block {position}: list requires non-empty items")
            elif any(not isinstance(item, dict) or not isinstance(item.get("inlines"), list) or not item["inlines"] for item in items):
                errors.append(f"block {position}: list items require non-empty inlines")
            else:
                previous_list_level = 0
                for item_index, item in enumerate(items, start=1):
                    level = item.get("level", 0)
                    item_kind = item.get("kind", block.get("kind"))
                    item_start = item.get("start", 1)
                    if isinstance(level, bool) or not isinstance(level, int) or not 0 <= level <= 8:
                        errors.append(f"block {position} item {item_index}: list level must be 0..8")
                    elif item_index == 1 and level != 0:
                        errors.append(f"block {position} item {item_index}: list level must begin at level 0")
                    elif level > previous_list_level + 1:
                        errors.append(f"block {position} item {item_index}: list level jumps from {previous_list_level} to {level}")
                    else:
                        previous_list_level = level
                    if item_kind not in {"ordered", "unordered"}:
                        errors.append(f"block {position} item {item_index}: list kind must be ordered or unordered")
                    elif isinstance(level, int) and not isinstance(level, bool):
                        previous_kind = next((prior.get("kind", block.get("kind")) for prior in items[:item_index - 1]
                                              if prior.get("level", 0) == level), None)
                        if previous_kind is not None and previous_kind != item_kind:
                            errors.append(f"block {position} item {item_index}: list kind cannot change within level {level}")
                    if isinstance(item_start, bool) or not isinstance(item_start, int) or not 1 <= item_start <= 2147483647:
                        errors.append(f"block {position} item {item_index}: list start must be a positive 32-bit integer")
        if kind == "list" and (not isinstance(block.get("items"), list) or any(not isinstance(item, dict) or not isinstance(item.get("inlines"), list) for item in block["items"])):
            continue
        if kind in {"paragraph", "list"}:
            inlines = block.get("inlines", []) if kind == "paragraph" else [inline for item in block.get("items", []) if isinstance(item, dict) for inline in item.get("inlines", [])]
            for inline in inlines:
                if inline.get("type") == "crossReference":
                    refs.append(inline.get("targetId", ""))
                if inline.get("type") == "literatureCitation" and not profile.get("capabilities", {}).get("literatureCitations", False):
                    errors.append(f"block {position}: literature citations are not supported by this profile")
        if kind == "table":
            rows = block.get("rows")
            if not isinstance(rows, list) or not rows or not all(isinstance(row, list) and row for row in rows):
                errors.append(f"block {position}: table needs non-empty rows")
            elif len({len(row) for row in rows}) != 1:
                errors.append(f"block {position}: merged or ragged tables are not supported in v0")
            chapter_role = profile.get("caption", {}).get("table", {}).get("chapterStyleRole", "")
            try:
                chapter_level = int(chapter_role.removeprefix("headingLevel"))
            except ValueError:
                chapter_level = 0
            if chapter_level and chapter_level not in seen_heading_levels:
                errors.append(f"block {position}: table caption requires {chapter_role} before the table")
        if kind == "figure":
            value = block.get("src")
            if not isinstance(value, str):
                errors.append(f"block {position}: figure src is required")
            else:
                candidate = (resource_root / value).resolve()
                try:
                    candidate.relative_to(resource_root)
                except ValueError:
                    errors.append(f"block {position}: figure path escapes resourceRoot")
                else:
                    if candidate.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
                        errors.append(f"block {position}: unsupported image format {candidate.suffix}")
                    elif not candidate.is_file():
                        errors.append(f"block {position}: missing image {value}")
                    elif not mimetypes.guess_type(candidate.name)[0]:
                        errors.append(f"block {position}: unrecognised image MIME type")
            chapter_role = profile.get("caption", {}).get("figure", {}).get("chapterStyleRole", "")
            try:
                chapter_level = int(chapter_role.removeprefix("headingLevel"))
            except ValueError:
                chapter_level = 0
            if chapter_level and chapter_level not in seen_heading_levels:
                errors.append(f"block {position}: figure caption requires {chapter_role} before the figure")
    for target in refs:
        if target not in targets:
            errors.append(f"cross-reference target does not exist or is not referencable: {target}")
    for kind in ("table", "figure"):
        caption = profile.get("caption", {}).get(kind, {})
        required = ("sequenceIdentifier", "captionStyleRole", "chapterStyleRole", "sequenceResetLevel", "separator", "labels")
        missing = [key for key in required if key not in caption]
        if missing:
            errors.append(f"profile caption.{kind} missing: {', '.join(missing)}")
        role = caption.get("chapterStyleRole")
        if role and not _role(profile, role):
            errors.append(f"profile caption.{kind} references undefined role {role}")
    return errors


def validate_or_raise(model: dict[str, Any], profile: dict[str, Any], task: dict[str, Any]) -> None:
    errors = validate(model, profile, task)
    if errors:
        raise ValidationError(errors)
