#!/bin/sh
# Install arachne-loom's local git hooks.
#
# Git hooks are NOT cloned, so every contributor (and every fresh checkout)
# must run this once:
#
#   sh scripts/install-hooks.sh
#
# The pre-push hook runs the leak-guard scanner and refuses the push if any
# sensitive pattern is found. CI runs the same scanner as a backstop.

set -e
REPO_ROOT=$(git rev-parse --show-toplevel)
HOOK_DIR="$REPO_ROOT/.git/hooks"

mkdir -p "$HOOK_DIR"
cat > "$HOOK_DIR/pre-push" <<'HOOK'
#!/bin/sh
# arachne-loom leak guard (pre-push). Blocks pushing sensitive data.
REPO_ROOT=$(git rev-parse --show-toplevel)
python3 "$REPO_ROOT/scripts/scan-sensitive.py" || {
    echo "" >&2
    echo "pre-push blocked by leak guard. Nothing was pushed." >&2
    exit 1
}
HOOK
chmod +x "$HOOK_DIR/pre-push"
echo "Installed pre-push hook -> $HOOK_DIR/pre-push"
