#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALL_PACKS = [
    "software-design-philosophy",
    "refactoring-second-edition",
    "first-principles-thinking",
    "beginning-of-infinity",
]
ENGINEERING_PACKS = ALL_PACKS[:2]


def run(*args: str, input_text: str | None = None):
    return subprocess.run([sys.executable, *args], cwd=ROOT, input=input_text, text=True, capture_output=True)


def add(checks, name, ok, detail=""):
    checks.append((name, bool(ok), detail))


def aggregate_checks(checks):
    pack_args = [item for pack in ALL_PACKS for item in ("--pack", pack)]
    result = run("scripts/aggregate_rules.py", *pack_args, "--format", "json")
    add(checks, "aggregate all packs", result.returncode == 0, result.stderr)
    data = json.loads(result.stdout) if result.stdout else {}
    if not data:
        return {}
    items = data["principles"] + data["red_flags"] + data["smells"] + data["refactorings"]
    ids = [item["id"] for item in items]
    add(checks, "all knowledge IDs are unique", len(ids) == len(set(ids)))
    add(checks, "no relationship errors", not data["relationship_errors"])
    add(checks, "no unresolved conflicts", not data["unresolved_conflicts"])
    add(checks, "all smells stay candidates", all(item.get("kind") == "candidate" for item in data["smells"]))
    reasoning_rules = [item for item in data["principles"] if item["pack"] in ALL_PACKS[2:]]
    add(checks, "reasoning principles have compact runtime cards", reasoning_rules and all(item.get("runtime", {}).get("prompt") for item in reasoning_rules))
    return data


def policy_checks(checks, data):
    policy = json.loads((ROOT / "evals/cases/policy-cases.json").read_text(encoding="utf-8"))
    add(checks, "refactoring decision set is recorded", policy["decision_set"] == {
        "D1": "A", "D2": "C", "D3": "A", "D4": "A",
        "D5": "A", "D6": "A", "D7": "A", "D8": "A",
    })
    by_id = {item["id"]: item for item in data.get("principles", []) + data.get("smells", [])}
    for case in policy["cases"]:
        item_id = case.get("rule") or case.get("smell")
        searchable = " ".join(str(value) for value in by_id.get(item_id, {}).values())
        add(checks, f"refactoring policy {case['id']}", bool(searchable) and all(token in searchable for token in case["must_include"]))

    reasoning = json.loads((ROOT / "evals/cases/reasoning-policy-cases.json").read_text(encoding="utf-8"))
    add(checks, "reasoning decisions D9-D14 are recorded", set(reasoning["decision_set"]) == {f"D{number}" for number in range(9, 15)})
    for case in reasoning["selection_cases"]:
        selected = run("scripts/select_capsule.py", "--capability", "assumption-audit", "--query", case["query"])
        payload = json.loads(selected.stdout)
        selected_ids = {item["id"] for item in payload["rules"]}
        add(checks, f"reasoning selection {case['id']}", selected.returncode == 0 and set(case["must_select"]) <= selected_ids, selected.stderr)
        add(checks, f"reasoning selection bounded {case['id']}", payload["selected_count"] <= 5 and payload["estimated_tokens"] <= 320)


def static_and_guard_checks(checks):
    smell = run("scripts/smell_audit.py", "evals/fixtures", "--format", "json")
    add(checks, "smell audit runs", smell.returncode == 0, smell.stderr)
    smell_data = json.loads(smell.stdout) if smell.stdout else []
    add(checks, "static smell findings stay candidates", all(item.get("kind") == "candidate" for item in smell_data))
    dto = [item for item in smell_data if item["file"].endswith("order_dto.py") and item["rule"] == "REF-SMELL-DATA-CLASS"]
    entity = [item for item in smell_data if item["file"].endswith("anemic_order.py") and item["rule"] == "REF-SMELL-DATA-CLASS"]
    long_params = [item for item in smell_data if item["file"].endswith("long_parameters.py") and item["rule"] == "REF-SMELL-LONG-PARAMETER-LIST"]
    long_function = [item for item in smell_data if item["file"].endswith("cohesive_long_function.py") and item["rule"] == "REF-SMELL-LONG-FUNCTION"]
    add(checks, "DTO is not automatically flagged", not dto)
    add(checks, "anemic object is a low-confidence candidate", len(entity) == 1 and entity[0]["confidence"] == "low")
    add(checks, "long parameter list produces a lead", bool(long_params))
    add(checks, "cohesive long function is not line-count flagged", not long_function)

    blocked = run("scripts/refactoring_guard.py", "--mode", "behavior-preserving-refactor", "--risk", "medium", "--format", "json")
    add(checks, "unsafe medium refactor is blocked", blocked.returncode == 1 and not json.loads(blocked.stdout)["allowed"])
    guarded = run(
        "scripts/refactoring_guard.py", "--mode", "behavior-preserving-refactor", "--risk", "medium",
        "--baseline-described", "--tests-passed", "--format", "json",
    )
    add(checks, "tested medium refactor passes", guarded.returncode == 0, guarded.stderr)
    mixed = run(
        "scripts/refactoring_guard.py", "--mode", "mixed-change", "--risk", "medium",
        "--baseline-described", "--characterization-tests", "--format", "json",
    )
    phases = ["behavior-baseline", "small-structural-steps", "refactoring-validation", "feature-change", "feature-validation"]
    add(checks, "mixed change phases stay separated", mixed.returncode == 0 and json.loads(mixed.stdout)["required_phases"] == phases)


def progressive_disclosure_checks(checks):
    current = run("scripts/build_capsules.py", "--check")
    add(checks, "generated capsule is current", current.returncode == 0, current.stdout + current.stderr)
    budget = run("scripts/context_budget_audit.py", "--format", "json")
    budget_data = json.loads(budget.stdout) if budget.stdout else {}
    add(checks, "context budget audit passes", budget.returncode == 0 and budget_data.get("passed"), budget.stderr)
    add(checks, "always-visible metadata does not exceed v0.2 baseline", budget_data.get("metrics", {}).get("skill_metadata_delta_estimated_tokens", 1) <= 0)

    default_hook = run("hooks/coordinator.py", input_text=json.dumps({"event": "preflight", "mode": "feature-design"}))
    default_data = json.loads(default_hook.stdout)
    add(checks, "default hook keeps reasoning off", default_hook.returncode == 0 and default_data["reasoning"] is None)
    add(checks, "default hook loads only engineering packs", default_data["packs"] == ENGINEERING_PACKS)

    reasoning_hook = run("hooks/coordinator.py", input_text=json.dumps({
        "event": "preflight", "mode": "feature-design", "reasoning_mode": "assumption-audit",
        "reasoning_query": "是否应该基于当前假设建设通用平台？",
    }))
    reasoning_data = json.loads(reasoning_hook.stdout)
    add(checks, "opt-in reasoning hook runs", reasoning_hook.returncode == 0, reasoning_hook.stderr)
    add(checks, "opt-in hook adds both reasoning packs", all(pack in reasoning_data["packs"] for pack in ALL_PACKS[2:]))
    add(checks, "opt-in hook returns bounded capsule", reasoning_data["reasoning"]["selected_count"] <= 5 and reasoning_data["reasoning"]["estimated_tokens"] <= 320)


def coordinator_regression_checks(checks):
    payload = {
        "event": "final-review", "mode": "mixed-change", "risk": "medium",
        "paths": ["evals/fixtures"], "packs": ENGINEERING_PACKS,
        "baseline_described": True, "tests_passed": True,
    }
    result = run("hooks/coordinator.py", input_text=json.dumps(payload))
    add(checks, "engineering coordinator regression passes", result.returncode == 0, result.stderr)
    if result.stdout:
        data = json.loads(result.stdout)
        add(checks, "coordinator reports no conflicts", not data["rule_conflicts"] and not data["relationship_errors"])
        add(checks, "coordinator merges engineering audits", set(data["audits"]) == {"complexity", "smells"})
        add(checks, "coordinator refactoring gate passes", data["gate"] and data["gate"]["allowed"])


def main() -> int:
    checks = []
    data = aggregate_checks(checks)
    if data:
        policy_checks(checks, data)
    static_and_guard_checks(checks)
    progressive_disclosure_checks(checks)
    coordinator_regression_checks(checks)
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
        if detail:
            print(detail.strip())
    return 0 if all(ok for _, ok, _ in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
