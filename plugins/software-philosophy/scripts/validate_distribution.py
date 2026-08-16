#!/usr/bin/env python3
"""Validate dual-host marketplace packaging and release identity."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    checks = []
    distribution = load(ROOT / "config/distribution.json")
    name = distribution["plugin_name"]
    codex = load(ROOT / ".codex-plugin/plugin.json")
    claude = load(ROOT / "adapters/claude/.claude-plugin/plugin.json")
    codex_market = load(ROOT / ".agents/plugins/marketplace.json")
    claude_market = load(ROOT / ".claude-plugin/marketplace.json")
    universal = ROOT / "plugins" / name
    universal_codex = load(universal / ".codex-plugin/plugin.json")
    universal_claude = load(universal / ".claude-plugin/plugin.json")

    def add(label, condition):
        checks.append((label, bool(condition)))

    add("manifest names match distribution", codex["name"] == claude["name"] == distribution["plugin_name"])
    add("manifest versions match", codex["version"] == claude["version"])
    add("repository metadata matches", codex.get("repository") == claude.get("repository") == distribution["repository"])
    add("Codex marketplace identity matches", codex_market["name"] == distribution["marketplace_name"])
    add("Claude marketplace identity matches", claude_market["name"] == distribution["marketplace_name"])
    add("Codex marketplace path is universal payload", codex_market["plugins"][0]["source"]["path"] == f"./plugins/{name}")
    add("Claude marketplace path is universal payload", claude_market["plugins"][0]["source"] == f"./plugins/{name}")
    add("Claude marketplace version matches", claude_market["plugins"][0]["version"] == claude["version"])
    add("universal Codex manifest matches", universal_codex == codex)
    add("universal Claude manifest matches", universal_claude == claude)
    add("universal payload includes documentation and licenses", all(
        (universal / filename).is_file() for filename in ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md")
    ))
    for skill in ("root-cause-debugging", "disciplined-delivery"):
        add(f"universal payload includes {skill}", all((universal / "skills" / skill / path).is_file() for path in (
            Path("SKILL.md"), Path("agents/openai.yaml"),
        )))

    stale = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in {".git", "dist", "build"} for part in path.parts):
            continue
        if path.suffix in {".pyc"} or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        old_slug = "w" + "oftware-philosophy"
        old_title = "W" + "oftware Philosophy"
        if old_slug in text or old_title in text:
            stale.append(str(path.relative_to(ROOT)))
    add("old project identity is absent", not stale)

    for label, passed in checks:
        print(f"{'PASS' if passed else 'FAIL'}: {label}")
    if stale:
        print("stale identity files: " + ", ".join(stale))
    return 0 if all(passed for _, passed in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
