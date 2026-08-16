#!/usr/bin/env python3
"""Compile source Pack runtime fields into small on-demand capability capsules."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build() -> list[Path]:
    config = load(ROOT / "config/capsules.json")
    output_dir = ROOT / "capsules"
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for capability, spec in config.items():
        cards = []
        for pack in spec["source_packs"]:
            source = load(ROOT / "packs" / pack / "principles.json")
            for rule in source.get("rules", []):
                runtime = rule.get("runtime")
                if not runtime:
                    continue
                cards.append({
                    "id": rule["id"],
                    "prompt": runtime["prompt"],
                    "triggers": runtime.get("triggers", []),
                    "priority": runtime.get("priority", 0),
                    "default": bool(runtime.get("default", False)),
                })
        cards.sort(key=lambda item: (-item["priority"], item["id"]))
        capsule = {
            "capability": capability,
            "generated_from": spec["source_packs"],
            "max_selected_rules": spec["max_selected_rules"],
            "rules": cards,
        }
        target = output_dir / f"{capability}.json"
        target.write_text(json.dumps(capsule, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        written.append(target)
    return written


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        before = {path.name: path.read_text(encoding="utf-8") for path in (ROOT / "capsules").glob("*.json")}
        paths = build()
        after = {path.name: path.read_text(encoding="utf-8") for path in paths}
        if before != after:
            print("error: generated capsules were stale")
            return 1
        print("Capsules are current")
        return 0
    for path in build():
        print(f"Built {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
