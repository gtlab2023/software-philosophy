#!/usr/bin/env bash
set -euo pipefail

MARKETPLACE="software-philosophy"
PLUGIN="software-philosophy@software-philosophy"
SOURCE="${1:-gtlab2023/software-philosophy}"

command -v codex >/dev/null || { echo "error: codex CLI is not installed" >&2; exit 1; }

if codex plugin marketplace list --json | grep -Eq '"name"[[:space:]]*:[[:space:]]*"software-philosophy"'; then
  codex plugin marketplace upgrade "$MARKETPLACE" >/dev/null 2>&1 || true
else
  codex plugin marketplace add "$SOURCE"
fi

codex plugin add "$PLUGIN"
echo "Installed $PLUGIN. Start a new Codex task to load it."
