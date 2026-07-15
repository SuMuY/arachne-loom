#!/bin/sh
# Install the leak-guard pre-push hook in the current git repo.
#
# Git hooks are NOT cloned, so run this once per fresh checkout / machine:
#   sh scripts/leak-guard/install-hooks.sh
#
# The hook runs scan.py before every push and refuses the push on any match.
# CI should run the same scan.py as the backstop (see SETUP.md).

set -e
# Resolve both paths to physical form (pwd -P) so symlinks like macOS
# /tmp -> /private/tmp don't break the prefix strip below.
REPO_ROOT=$(cd "$(git rev-parse --show-toplevel)" && pwd -P)
GUARD_DIR=$(cd "$(dirname "$0")" && pwd -P)
# Path of this leak-guard dir relative to the repo root (so the hook can find
# scan.py wherever the folder was dropped).
REL_GUARD=${GUARD_DIR#"$REPO_ROOT"/}
HOOK_DIR="$REPO_ROOT/.git/hooks"

mkdir -p "$HOOK_DIR"
cat > "$HOOK_DIR/pre-push" <<HOOK
#!/bin/sh
# leak guard (pre-push) — blocks pushing sensitive data.
REPO_ROOT=\$(git rev-parse --show-toplevel)
python3 "\$REPO_ROOT/$REL_GUARD/scan.py" || {
    echo "" >&2
    echo "pre-push blocked by leak guard. Nothing was pushed." >&2
    exit 1
}
HOOK
chmod +x "$HOOK_DIR/pre-push"
echo "Installed pre-push hook -> $HOOK_DIR/pre-push (runs $REL_GUARD/scan.py)"
