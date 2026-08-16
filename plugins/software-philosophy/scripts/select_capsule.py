#!/usr/bin/env python3
"""Select a bounded set of runtime rule cards without loading source Packs into context."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from token_utils import estimate_tokens

ROOT = Path(__file__).resolve().parents[1]


def select(capability: str, query: str, limit: int | None = None):
    path = ROOT / "capsules" / f"{capability}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    maximum = min(limit or data["max_selected_rules"], data["max_selected_rules"])
    normalized = query.casefold()
    scored = []
    for rule in data["rules"]:
        score = sum(3 for trigger in rule["triggers"] if trigger.casefold() in normalized)
        if rule["default"]:
            score += 1
        scored.append((score, rule["priority"], rule["id"], rule))
    matched = [item for item in scored if item[0] > 1]
    if not matched:
        matched = [item for item in scored if item[3]["default"]]
    matched.sort(key=lambda item: (-item[0], -item[1], item[2]))
    rules = [{"id": item[3]["id"], "prompt": item[3]["prompt"]} for item in matched[:maximum]]
    compact_text = "\n".join(f"{item['id']}: {item['prompt']}" for item in rules)
    return {
        "capability": capability,
        "selected_count": len(rules),
        "estimated_tokens": estimate_tokens(compact_text),
        "rules": rules,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capability", required=True)
    parser.add_argument("--query", default="")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--format", choices=["json", "text"], default="json")
    args = parser.parse_args()
    result = select(args.capability, args.query, args.limit)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    else:
        for rule in result["rules"]:
            print(f"{rule['id']}: {rule['prompt']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
