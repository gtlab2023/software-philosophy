#!/usr/bin/env bash
set -euo pipefail

MARKETPLACE="software-philosophy"
PLUGIN="software-philosophy@software-philosophy"
SOURCE="${1:-gtlab2023/software-philosophy}"

command -v claude >/dev/null || { echo "error: claude CLI is not installed" >&2; exit 1; }

if claude plugin marketplace list --json | grep -Eq '"name"[[:space:]]*:[[:space:]]*"software-philosophy"'; then
  claude plugin marketplace update "$MARKETPLACE"
else
  claude plugin marketplace add "$SOURCE" --scope user
fi

if claude plugin list --json | grep -Eq '"id"[[:space:]]*:[[:space:]]*"software-philosophy@software-philosophy"'; then
  claude plugin update "$PLUGIN" --scope user
else
  claude plugin install "$PLUGIN" --scope user
fi

echo "Installed $PLUGIN. Restart Claude Code to load it."
