#!/bin/bash
# One-line installer for Agent Constraint System
# curl -fsSL https://raw.githubusercontent.com/kamanager2012/agent-constraint-system/main/install-remote.sh | bash

set -e
INSTALL_DIR="$HOME/.acs"

echo "ACS v1.5.0 — Agent Constraint System"
echo ""

# Download from GitHub
TMP=$(mktemp -d)
git clone --depth 1 https://github.com/kamanager2012/agent-constraint-system.git "$TMP" 2>/dev/null

cd "$TMP"
bash install.sh --all

rm -rf "$TMP"
echo ""
echo "Done. Run: acs status"
