#!/usr/bin/env bash
set -euo pipefail

MARKETPLACE="software-philosophy"
PLUGIN="software-philosophy@software-philosophy"
SOURCE="${1:-gtlab2023/software-philosophy}"

command -v codex >/dev/null || { echo "error: codex CLI is not installed" >&2; exit 1; }
command -v python3 >/dev/null || { echo "error: python3 is required" >&2; exit 1; }

if codex plugin marketplace list --json | python3 -c 'import json,sys; d=json.load(sys.stdin); raise SystemExit(0 if any(x.get("name")=="software-philosophy" for x in d.get("marketplaces",[])) else 1)'; then
  codex plugin marketplace upgrade "$MARKETPLACE" >/dev/null 2>&1 || true
else
  codex plugin marketplace add "$SOURCE"
fi

codex plugin add "$PLUGIN"
echo "Installed $PLUGIN. Start a new Codex task to load it."
