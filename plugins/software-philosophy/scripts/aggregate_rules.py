#!/usr/bin/env python3
"""Merge enabled Pack knowledge, validate relationships, and report unresolved conflicts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path, *, required: bool = False) -> dict[str, Any]:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return {}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load_pack(name: str) -> dict[str, Any]:
    directory = ROOT / "packs" / name
    if not directory.is_dir():
        raise FileNotFoundError(f"Unknown pack: {name}")
    principles = load_json(directory / "principles.json", required=True)
    return {
        "name": name,
        "principles": principles.get("rules", []),
        "red_flags": load_json(directory / "red_flags.json").get("red_flags", []),
        "smells": load_json(directory / "smells.json").get("smells", []),
        "refactorings": load_json(directory / "refactorings.json").get("refactorings", []),
        "mappings": load_json(directory / "mappings.json").get("mappings", []),
        "unresolved_conflicts": load_json(directory / "mappings.json").get("unresolved_conflicts", []),
    }


def relationship_targets(item: dict[str, Any], key: str) -> list[str]:
    singular = "counterbalance" if key == "counterbalances" else key.rstrip("s")
    values = item.get(key, item.get(singular, []))
    if isinstance(values, str):
        return [values]
    return list(values or [])


def merge(pack_names: list[str]) -> dict[str, Any]:
    collections: dict[str, dict[str, dict[str, Any]]] = {
        "principles": {},
        "red_flags": {},
        "smells": {},
        "refactorings": {},
    }
    duplicate_ids: list[str] = []
    all_seen: dict[str, tuple[str, dict[str, Any]]] = {}
    mappings: list[dict[str, Any]] = []
    unresolved_conflicts: list[Any] = []

    for name in pack_names:
        pack = load_pack(name)
        for collection_name in collections:
            for raw_item in pack[collection_name]:
                item = {**raw_item, "pack": name}
                item_id = item["id"]
                previous = all_seen.get(item_id)
                if previous and previous != (collection_name, item):
                    duplicate_ids.append(item_id)
                    continue
                all_seen[item_id] = (collection_name, item)
                collections[collection_name][item_id] = item
        mappings.extend({**mapping, "pack": name} for mapping in pack["mappings"])
        unresolved_conflicts.extend(pack["unresolved_conflicts"])

    active_ids = set(all_seen)
    relationship_errors: list[dict[str, str]] = []
    declared_conflicts: list[dict[str, str]] = []
    relations: list[dict[str, str]] = []

    for collection_name, items in collections.items():
        for item in items.values():
            for field, relation in (
                ("extends", "extends"),
                ("conflicts", "conflicts"),
                ("counterbalances", "counterbalance"),
            ):
                for target in relationship_targets(item, field):
                    record = {"from": item["id"], "to": target, "relation": relation, "pack": item["pack"]}
                    relations.append(record)
                    if target not in active_ids:
                        relationship_errors.append({**record, "error": "target-not-enabled"})
                    if relation == "conflicts" and target in active_ids:
                        declared_conflicts.append(record)

    mapping_keys = set()
    for mapping in mappings:
        source = mapping.get("from")
        target = mapping.get("to")
        relation = mapping.get("relation")
        if source not in active_ids or target not in active_ids:
            relationship_errors.append({
                "from": str(source), "to": str(target), "relation": str(relation),
                "pack": mapping["pack"], "error": "mapping-endpoint-not-enabled",
            })
        mapping_keys.add((source, target, relation))

    for conflict in declared_conflicts:
        direct = (conflict["from"], conflict["to"], "conflicts")
        reverse = (conflict["to"], conflict["from"], "conflicts")
        if direct not in mapping_keys and reverse not in mapping_keys:
            unresolved_conflicts.append(conflict)

    return {
        "packs": list(pack_names),
        **{name: list(items.values()) for name, items in collections.items()},
        "mappings": mappings,
        "relationships": relations,
        "declared_conflicts": declared_conflicts,
        "unresolved_conflicts": unresolved_conflicts,
        "relationship_errors": relationship_errors,
        "duplicate_conflicts": sorted(set(duplicate_ids)),
    }


def markdown(data: dict[str, Any]) -> str:
    lines = ["# Active Design Rules", "", f"Enabled Packs: {', '.join(data['packs'])}", ""]
    if data["duplicate_conflicts"] or data["relationship_errors"] or data["unresolved_conflicts"]:
        lines += ["## Aggregation problems", ""]
        for item in data["duplicate_conflicts"]:
            lines.append(f"- Duplicate ID: `{item}`")
        for item in data["relationship_errors"]:
            lines.append(f"- Invalid relation: `{item['from']}` {item['relation']} `{item['to']}` ({item['error']})")
        for item in data["unresolved_conflicts"]:
            lines.append(f"- Unresolved conflict: `{item}`")
        lines.append("")

    lines += ["## Principles", ""]
    for rule in data["principles"]:
        lines += [
            f"### `{rule['id']}` — {rule['title']}", "",
            f"- Pack: `{rule['pack']}`",
            f"- Category: `{rule['category']}`",
            f"- Severity: `{rule['severity']}`",
            f"- Enforcement: `{rule['enforcement']}`",
            f"- Rule: {rule['statement']}", "",
        ]

    if data["red_flags"]:
        lines += ["## Red flags", ""]
        for flag in data["red_flags"]:
            lines.append(f"- `{flag['id']}` **{flag['title']}** ({flag['severity']}): {flag['question']}")
        lines.append("")

    if data["smells"]:
        lines += ["## Contextual code smells", ""]
        for smell in data["smells"]:
            lines.append(f"- `{smell['id']}` **{smell['title']}** ({smell['severity']}, candidate): {smell['decision_question']}")
        lines.append("")

    if data["mappings"]:
        lines += ["## Cross-pack mappings", ""]
        for mapping in data["mappings"]:
            lines.append(
                f"- `{mapping['from']}` —{mapping['relation']}→ `{mapping['to']}` "
                f"[{mapping.get('decision', 'no-decision')}]: {mapping.get('resolution', '')}"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", action="append", required=True, dest="packs")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        data = merge(args.packs)
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    rendered = json.dumps(data, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else markdown(data)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    problems = data["duplicate_conflicts"] or data["relationship_errors"] or data["unresolved_conflicts"]
    if problems:
        print("warning: rule aggregation problems detected", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
