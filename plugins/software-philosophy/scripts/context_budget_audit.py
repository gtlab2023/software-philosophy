#!/usr/bin/env python3
"""Audit progressive-disclosure and estimated context budgets."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from select_capsule import select
from token_utils import estimate_tokens

ROOT = Path(__file__).resolve().parents[1]


def frontmatter_and_body(path: Path):
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3:
        raise ValueError(f"invalid skill frontmatter: {path}")
    frontmatter, body = parts[1], parts[2]
    name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
    description_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
    if not name_match or not description_match:
        raise ValueError(f"missing skill metadata: {path}")
    return name_match.group(1), description_match.group(1), body


def audit():
    config = json.loads((ROOT / "config/context-budget.json").read_text(encoding="utf-8"))
    budgets = config["budgets"]
    skills = []
    metadata_total = 0
    checks = []

    for path in sorted((ROOT / "skills").glob("*/SKILL.md")):
        name, description, body = frontmatter_and_body(path)
        metadata_tokens = estimate_tokens(name + "\n" + description)
        body_tokens = estimate_tokens(body)
        metadata_total += metadata_tokens
        skills.append({"name": name, "metadata_estimated_tokens": metadata_tokens, "body_estimated_tokens": body_tokens})
        checks.append({
            "name": f"skill-body:{name}",
            "passed": body_tokens <= budgets["single_skill_body_estimated_tokens"],
            "actual": body_tokens,
            "limit": budgets["single_skill_body_estimated_tokens"],
        })
        if name == "assumption-audit":
            checks.append({
                "name": "assumption-audit-body",
                "passed": body_tokens <= budgets["assumption_audit_body_estimated_tokens"],
                "actual": body_tokens,
                "limit": budgets["assumption_audit_body_estimated_tokens"],
            })

    delta = metadata_total - config["baseline_skill_metadata_estimated_tokens"]
    checks.extend([
        {
            "name": "skill-metadata-total", "passed": metadata_total <= budgets["skill_metadata_total_estimated_tokens"],
            "actual": metadata_total, "limit": budgets["skill_metadata_total_estimated_tokens"],
        },
        {
            "name": "skill-metadata-delta", "passed": delta <= budgets["skill_metadata_delta_estimated_tokens"],
            "actual": delta, "limit": budgets["skill_metadata_delta_estimated_tokens"],
        },
    ])

    capsule_path = ROOT / "capsules/assumption-audit.json"
    capsule_tokens = estimate_tokens(capsule_path.read_text(encoding="utf-8"))
    checks.append({
        "name": "capsule-full-storage", "passed": capsule_tokens <= budgets["capsule_full_estimated_tokens"],
        "actual": capsule_tokens, "limit": budgets["capsule_full_estimated_tokens"],
    })

    queries = [
        "这个需求依赖哪些假设和约束？",
        "为什么这个错误会发生，哪个根因解释更好？",
        "是否应该建设通用平台，还是保持专用实现？",
        "大家都使用这个最佳实践，是否有可审查的替代方案？",
    ]
    selections = []
    for query in queries:
        result = select("assumption-audit", query)
        selections.append({"query": query, **result})
        checks.extend([
            {
                "name": f"selected-count:{query}",
                "passed": result["selected_count"] <= budgets["selected_rule_count"],
                "actual": result["selected_count"], "limit": budgets["selected_rule_count"],
            },
            {
                "name": f"selected-tokens:{query}",
                "passed": result["estimated_tokens"] <= budgets["selected_rules_estimated_tokens"],
                "actual": result["estimated_tokens"], "limit": budgets["selected_rules_estimated_tokens"],
            },
        ])

    return {
        "baseline_version": config["baseline_version"],
        "passed": all(item["passed"] for item in checks),
        "metrics": {
            "skill_metadata_estimated_tokens": metadata_total,
            "skill_metadata_delta_estimated_tokens": delta,
            "capsule_full_storage_estimated_tokens": capsule_tokens,
        },
        "skills": skills,
        "selections": selections,
        "checks": checks,
        "note": "Estimates are conservative regression budgets, not provider billing counts.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", choices=["json", "text"], default="text")
    args = parser.parse_args()
    try:
        result = audit()
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"error: {exc}")
        return 2
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        for check in result["checks"]:
            print(f"{'PASS' if check['passed'] else 'FAIL'}: {check['name']} ({check['actual']} <= {check['limit']})")
        print(json.dumps(result["metrics"], ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
