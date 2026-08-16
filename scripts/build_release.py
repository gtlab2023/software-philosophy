#!/usr/bin/env python3
"""Build host packages, one universal marketplace payload, and both marketplace catalogs."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED_DIRECTORIES = ("skills", "packs", "core", "scripts", "hooks", "evals", "docs", "config", "capsules")


def copy_tree(src: Path, dst: Path):
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def copy_shared(target: Path):
    target.mkdir(parents=True, exist_ok=True)
    for directory in SHARED_DIRECTORIES:
        copy_tree(ROOT / directory, target / directory)
    for filename in ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
        (target / filename).write_text((ROOT / filename).read_text(encoding="utf-8"), encoding="utf-8")


def write_marketplaces(distribution: dict, version: str):
    name = distribution["plugin_name"]
    marketplace = distribution["marketplace_name"]
    repo = distribution["repository"]
    path = f"./plugins/{name}"

    write_json(ROOT / ".agents/plugins/marketplace.json", {
        "name": marketplace,
        "interface": {"displayName": distribution["display_name"]},
        "plugins": [{
            "name": name,
            "source": {"source": "local", "path": path},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": distribution["category"],
        }],
    })

    write_json(ROOT / ".claude-plugin/marketplace.json", {
        "name": marketplace,
        "owner": {"name": distribution["owner"], "url": repo},
        "metadata": {
            "description": "Task-oriented software design, refactoring, and bounded-context reasoning skills.",
            "version": version,
            "pluginRoot": "./plugins",
        },
        "plugins": [{
            "name": name,
            "source": path,
            "description": "Complexity-conscious design, safe refactoring, and opt-in assumption audits.",
            "version": version,
            "author": {"name": "Software Philosophy contributors"},
            "homepage": repo,
            "repository": repo,
            "category": "development",
            "tags": ["software-design", "refactoring", "architecture", "critical-thinking"],
        }],
    })


def build(clean: bool):
    subprocess.run([sys.executable, str(ROOT / "scripts/build_capsules.py")], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts/context_budget_audit.py")], cwd=ROOT, check=True)

    codex_manifest = load_json(ROOT / ".codex-plugin/plugin.json")
    claude_manifest = load_json(ROOT / "adapters/claude/.claude-plugin/plugin.json")
    distribution = load_json(ROOT / "config/distribution.json")
    if codex_manifest["name"] != claude_manifest["name"] or codex_manifest["version"] != claude_manifest["version"]:
        raise ValueError("Codex and Claude manifests must have matching name and version")
    if codex_manifest["name"] != distribution["plugin_name"]:
        raise ValueError("distribution plugin_name must match manifests")

    dist = ROOT / "dist"
    universal = ROOT / "plugins" / distribution["plugin_name"]
    if clean:
        if dist.exists():
            shutil.rmtree(dist)
        if universal.exists():
            shutil.rmtree(universal)

    for host in ("codex", "claude"):
        target = dist / host
        copy_shared(target)
        if host == "codex":
            write_json(target / ".codex-plugin/plugin.json", codex_manifest)
        else:
            write_json(target / ".claude-plugin/plugin.json", claude_manifest)

    copy_shared(universal)
    write_json(universal / ".codex-plugin/plugin.json", codex_manifest)
    write_json(universal / ".claude-plugin/plugin.json", claude_manifest)
    write_marketplaces(distribution, codex_manifest["version"])

    print(f"Built {dist / 'codex'}")
    print(f"Built {dist / 'claude'}")
    print(f"Built {universal}")
    print(f"Built {ROOT / '.agents/plugins/marketplace.json'}")
    print(f"Built {ROOT / '.claude-plugin/marketplace.json'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()
    build(args.clean)
