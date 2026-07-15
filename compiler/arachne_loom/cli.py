from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .generator import compile_document
from .inspector import inspect_to_file
from .parser import ParseError, parse_to_file
from .validator import ValidationError, load_json, validate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="loom")
    commands = parser.add_subparsers(dest="command", required=True)
    parse = commands.add_parser("parse"); parse.add_argument("input"); parse.add_argument("-o", "--output", required=True)
    validate_p = commands.add_parser("validate"); validate_p.add_argument("model"); validate_p.add_argument("profile"); validate_p.add_argument("task")
    compile_p = commands.add_parser("compile"); compile_p.add_argument("model"); compile_p.add_argument("profile"); compile_p.add_argument("task"); compile_p.add_argument("--out-dir", required=True)
    inspect_p = commands.add_parser("inspect"); inspect_p.add_argument("document"); inspect_p.add_argument("-o", "--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "parse": parse_to_file(args.input, args.output)
        elif args.command == "validate":
            task = load_json(args.task)
            task_dir = Path(args.task).resolve().parent
            resource_value = Path(task.get("resourceRoot", "."))
            task["resourceRoot"] = str((task_dir / resource_value).resolve()) if not resource_value.is_absolute() else str(resource_value.resolve())
            errors = validate(load_json(args.model), load_json(args.profile), task)
            if errors:
                print("\n".join(errors), file=sys.stderr); return 2
            print("validation passed")
        elif args.command == "compile":
            output = compile_document(load_json(args.model), load_json(args.profile), load_json(args.task), args.out_dir, args.model, args.profile, args.task)
            print(output)
        else: inspect_to_file(args.document, args.output)
    except (ParseError, ValidationError, ValueError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr); return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
