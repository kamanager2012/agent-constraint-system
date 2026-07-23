#!/bin/bash
# deploy.sh — ACS v1.5 deployment tool
# Usage:
#   ./deploy.sh                    Deploy versions/v5.3/ → ~/.claude/hooks/
#   ./deploy.sh --dry-run          Preview changes without applying
#   ./deploy.sh --rollback TIMESTAMP  Restore from backup
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
SOURCE_DIR="$REPO_ROOT/versions/v5.3"
TARGET_DIR="$HOME/.claude/hooks"
BACKUP_DIR="$REPO_ROOT/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DRY_RUN=false
ROLLBACK_TS=""

# --- Parse arguments ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        --rollback) ROLLBACK_TS="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# --- Rollback mode ---
if [[ -n "$ROLLBACK_TS" ]]; then
    BACKUP_PATH="$BACKUP_DIR/$ROLLBACK_TS"
    if [[ ! -d "$BACKUP_PATH" ]]; then
        echo "Error: backup '$ROLLBACK_TS' not found in $BACKUP_DIR/"
        exit 1
    fi
    echo "Rolling back to $ROLLBACK_TS ..."
    cp -v "$BACKUP_PATH"/*.py "$TARGET_DIR/" 2>/dev/null || true
    cp -v "$BACKUP_PATH"/*.json "$TARGET_DIR/" 2>/dev/null || true
    cp -v "$BACKUP_PATH"/*.sh "$TARGET_DIR/" 2>/dev/null || true
    echo "Rollback complete. Verifying integrity ..."
    python3 "$TARGET_DIR/acs_lite.py" integrity-store
    python3 "$TARGET_DIR/acs_lite.py" status
    exit 0
fi

# --- Validate ---
if [[ ! -d "$SOURCE_DIR" ]]; then
    echo "Error: source directory not found: $SOURCE_DIR"
    echo "Run from agent-constraint-system/ repo root."
    exit 1
fi

if [[ ! -d "$TARGET_DIR" ]]; then
    echo "Error: target directory not found: $TARGET_DIR"
    exit 1
fi

# --- Snapshot current state ---
BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"
echo "=== Backing up current deployment → $BACKUP_PATH ==="
if $DRY_RUN; then
    echo "[DRY RUN] mkdir -p $BACKUP_PATH"
else
    mkdir -p "$BACKUP_PATH"
    cp "$TARGET_DIR"/*.py "$BACKUP_PATH/" 2>/dev/null || true
    cp "$TARGET_DIR"/*.json "$BACKUP_PATH/" 2>/dev/null || true
    cp "$TARGET_DIR"/*.sh "$BACKUP_PATH/" 2>/dev/null || true
    echo "Backup: $BACKUP_PATH ($(ls "$BACKUP_PATH" | wc -l) files)"
fi

# --- Deploy ---
echo ""
echo "=== Deploying v1.5 → $TARGET_DIR ==="
deployed=0
skipped=0

for src in "$SOURCE_DIR"/*.py "$SOURCE_DIR"/*.json "$SOURCE_DIR"/*.sh; do
    base=$(basename "$src")
    # Skip runtime data files (not source)
    case "$base" in
        acs_violations.json|hooks.json|package.json|MANIFEST.md) skipped=$((skipped + 1)); continue ;;
    esac
    dst="$TARGET_DIR/$base"

    if [[ -f "$dst" ]]; then
        if diff -q "$src" "$dst" > /dev/null 2>&1; then
            skipped=$((skipped + 1))
            continue  # unchanged
        fi
    fi

    if $DRY_RUN; then
        echo "[DRY RUN] cp $base → $dst"
    else
        cp "$src" "$dst"
        echo "  deployed: $base"
    fi
    deployed=$((deployed + 1))
done

echo ""
echo "=== Summary ==="
echo "  deployed: $deployed"
echo "  skipped (unchanged): $skipped"
echo "  backup: $BACKUP_PATH"

if $DRY_RUN; then
    echo ""
    echo "[DRY RUN complete — no files modified]"
    exit 0
fi

# --- Integrity check ---
echo ""
echo "=== Rebaselining integrity chain ==="
python3 "$TARGET_DIR/acs_lite.py" integrity-store
python3 "$TARGET_DIR/acs_lite.py" status

echo ""
echo "Deploy complete. To rollback: ./deploy.sh --rollback $TIMESTAMP"
