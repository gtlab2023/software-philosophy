#!/usr/bin/env bash
set -euo pipefail

MARKETPLACE="software-philosophy"
PLUGIN="software-philosophy@software-philosophy"
SOURCE="${1:-gtlab2023/software-philosophy}"

command -v claude >/dev/null || { echo "error: claude CLI is not installed" >&2; exit 1; }
command -v python3 >/dev/null || { echo "error: python3 is required" >&2; exit 1; }

if claude plugin marketplace list --json | python3 -c 'import json,sys; d=json.load(sys.stdin); raise SystemExit(0 if any(x.get("name")=="software-philosophy" for x in d) else 1)'; then
  claude plugin marketplace update "$MARKETPLACE"
else
  claude plugin marketplace add "$SOURCE" --scope user
fi

if claude plugin list --json | python3 -c 'import json,sys; d=json.load(sys.stdin); raise SystemExit(0 if any(x.get("id")=="software-philosophy@software-philosophy" for x in d) else 1)'; then
  claude plugin update "$PLUGIN" --scope user
else
  claude plugin install "$PLUGIN" --scope user
fi

echo "Installed $PLUGIN. Restart Claude Code to load it."
