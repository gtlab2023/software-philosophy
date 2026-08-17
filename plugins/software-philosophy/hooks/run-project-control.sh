#!/bin/sh

set -u

event=${1:-}
case "$event" in
  project-control-session-start|project-control-stop) ;;
  *)
    printf '%s\n' '{"continue":true,"systemMessage":"Project-control hook skipped: invalid launcher event."}'
    exit 0
    ;;
esac

plugin_root=${CLAUDE_PLUGIN_ROOT:-${PLUGIN_ROOT:-}}
if [ -z "$plugin_root" ]; then
  plugin_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
fi

python_command=
if [ -n "${SOFTWARE_PHILOSOPHY_PYTHON:-}" ] \
  && "$SOFTWARE_PHILOSOPHY_PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
  python_command=$SOFTWARE_PHILOSOPHY_PYTHON
elif python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
  python_command=python3
elif python -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' >/dev/null 2>&1; then
  python_command=python
fi

if [ -n "$python_command" ]; then
  exec "$python_command" "$plugin_root/hooks/coordinator.py" --event "$event"
fi

config_path=$PWD/.project-control.json
if [ ! -f "$config_path" ] && command -v git >/dev/null 2>&1; then
  repo_root=$(git rev-parse --show-toplevel 2>/dev/null || true)
  if [ -n "$repo_root" ]; then
    config_path=$repo_root/.project-control.json
  fi
fi

configured=false
if [ -f "$config_path" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    case "$line" in
      *'"enabled"'*true*) configured=true; break ;;
    esac
  done < "$config_path"
fi

if [ "$configured" = true ]; then
  printf '%s\n' '{"continue":true,"systemMessage":"Project-control hook skipped: Python 3.10+ is unavailable. Install Python, or set SOFTWARE_PHILOSOPHY_PYTHON to a compatible interpreter."}'
else
  printf '%s\n' '{"continue":true}'
fi

exit 0
