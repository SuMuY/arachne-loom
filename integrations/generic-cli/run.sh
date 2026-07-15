#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
COMPILER_DIR=${COMPILER_DIR:-$SCRIPT_DIR/../../compiler}
MODEL=${1:?model JSON required}
PROFILE=${2:?profile JSON required}
TASK=${3:?task JSON required}
OUT_DIR=${4:?output directory required}
PYTHONPATH="$COMPILER_DIR" python3 -m arachne_loom.cli validate "$MODEL" "$PROFILE" "$TASK"
PYTHONPATH="$COMPILER_DIR" python3 -m arachne_loom.cli compile "$MODEL" "$PROFILE" "$TASK" --out-dir "$OUT_DIR"
