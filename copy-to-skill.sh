#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <target-skill-dir>" >&2
    exit 2
fi

TARGET="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$SCRIPT_DIR/bring"
CLI_REF="$SCRIPT_DIR/cliref.md"

mkdir -p "$TARGET/scripts/bin" "$TARGET/references"
rsync -a \
    --exclude='.venv/' \
    --exclude='bin/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    "$SRC/" "$TARGET/scripts/"

cp "$CLI_REF" "$TARGET/references/cliref.md"

cat > "$TARGET/scripts/bin/bring-cli" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

CLI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

unset VIRTUAL_ENV CONDA_PREFIX CONDA_DEFAULT_ENV
exec uv run --project "$CLI_DIR" --directory "$(dirname "$CLI_DIR")" python -m scripts "$@"
EOF

chmod +x "$TARGET/scripts/bin/bring-cli"
