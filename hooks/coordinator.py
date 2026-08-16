#!/usr/bin/env python3
"""Platform-neutral Hook coordinator with opt-in reasoning capsules."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKS = ["software-design-philosophy", "refactoring-second-edition"]
REASONING_PACKS = ["first-principles-thinking", "beginning-of-infinity"]
VALID_MODES = {"feature-design", "behavior-preserving-refactor", "mixed-change"}
VALID_REASONING_MODES = {"off", "assumption-audit"}


def run_json(command: list[str]) -> tuple[int, Any, str]:
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    data = None
    if completed.stdout.strip():
        try:
            data = json.loads(completed.stdout)
        except json.JSONDecodeError:
            return completed.returncode or 2, None, completed.stdout.strip()
    return completed.returncode, data, completed.stderr.strip()


def guard_command(payload: dict[str, Any], mode: str) -> list[str]:
    command = [
        sys.executable, str(ROOT / "scripts/refactoring_guard.py"),
        "--mode", mode, "--risk", payload.get("risk", "low"), "--format", "json",
    ]
    for key, flag in (
        ("tests_passed", "--tests-passed"),
        ("characterization_tests", "--characterization-tests"),
        ("tool_proven", "--tool-proven"),
        ("baseline_described", "--baseline-described"),
        ("performance_verified", "--performance-verified"),
    ):
        if payload.get(key):
            command.append(flag)
    for constraint in payload.get("performance_constraints", []):
        command.extend(["--performance-constraint", str(constraint)])
    return command


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", default=None)
    args = parser.parse_args()
    raw = sys.stdin.read().strip()
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"invalid JSON input: {exc}"}, ensure_ascii=False))
        return 2

    event = args.event or payload.get("event", "final-review")
    mode = payload.get("mode", "feature-design")
    reasoning_mode = payload.get("reasoning_mode", "off")
    if mode not in VALID_MODES:
        print(json.dumps({"error": f"unknown mode: {mode}"}, ensure_ascii=False))
        return 2
    if reasoning_mode not in VALID_REASONING_MODES:
        print(json.dumps({"error": f"unknown reasoning_mode: {reasoning_mode}"}, ensure_ascii=False))
        return 2

    paths = [str(item) for item in payload.get("paths", [])]
    packs = list(payload.get("packs", DEFAULT_PACKS))
    if reasoning_mode != "off":
        for pack in REASONING_PACKS:
            if pack not in packs:
                packs.append(pack)

    output: dict[str, Any] = {
        "event": event,
        "mode": mode,
        "reasoning_mode": reasoning_mode,
        "packs": packs,
        "findings": [],
        "audits": {},
        "gate": None,
        "reasoning": None,
        "rule_conflicts": [],
        "relationship_errors": [],
        "errors": [],
    }

    pack_args = [item for pack in packs for item in ("--pack", pack)]
    aggregate_code, rules, aggregate_error = run_json([
        sys.executable, str(ROOT / "scripts/aggregate_rules.py"), *pack_args, "--format", "json",
    ])
    if rules:
        output["rule_conflicts"] = rules.get("duplicate_conflicts", []) + rules.get("unresolved_conflicts", [])
        output["relationship_errors"] = rules.get("relationship_errors", [])
    if aggregate_error:
        output["errors"].append({"source": "aggregate-rules", "message": aggregate_error})
    if aggregate_code and not rules:
        print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
        return 2

    if reasoning_mode == "assumption-audit":
        query = str(payload.get("reasoning_query") or payload.get("task") or "")
        reasoning_code, reasoning, reasoning_error = run_json([
            sys.executable, str(ROOT / "scripts/select_capsule.py"),
            "--capability", "assumption-audit", "--query", query, "--format", "json",
        ])
        output["reasoning"] = reasoning
        if reasoning_code or reasoning_error:
            output["errors"].append({"source": "reasoning-capsule", "message": reasoning_error or f"exit {reasoning_code}"})

    if paths and event in {"post-edit", "final-review"}:
        audit_code, complexity, audit_error = run_json([
            sys.executable, str(ROOT / "scripts/complexity_audit.py"), *paths, "--format", "json",
        ])
        if isinstance(complexity, list):
            output["audits"]["complexity"] = complexity
            output["findings"].extend(complexity)
        if audit_code or audit_error:
            output["errors"].append({"source": "complexity-audit", "message": audit_error or f"exit {audit_code}"})

        if "refactoring-second-edition" in packs:
            smell_code, smells, smell_error = run_json([
                sys.executable, str(ROOT / "scripts/smell_audit.py"), *paths, "--format", "json",
            ])
            if isinstance(smells, list):
                output["audits"]["smells"] = smells
                output["findings"].extend(smells)
            if smell_code or smell_error:
                output["errors"].append({"source": "smell-audit", "message": smell_error or f"exit {smell_code}"})

    if mode in {"behavior-preserving-refactor", "mixed-change"} and event in {"preflight", "post-edit", "final-review"}:
        _, gate, gate_error = run_json(guard_command(payload, mode))
        output["gate"] = gate
        if gate_error:
            output["errors"].append({"source": "refactoring-guard", "message": gate_error})

    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    if output["rule_conflicts"] or output["relationship_errors"]:
        return 1
    if output["errors"]:
        return 2
    if output["gate"] and not output["gate"].get("allowed", False):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
