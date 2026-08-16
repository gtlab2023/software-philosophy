#!/usr/bin/env python3
"""Risk-based safety gate for refactoring and mixed-change workflows."""
from __future__ import annotations

import argparse
import json
from typing import Any

MODES = ("feature-design", "behavior-preserving-refactor", "mixed-change")
RISKS = ("low", "medium", "high")


def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    mode = payload.get("mode", "feature-design")
    risk = payload.get("risk", "low")
    if mode not in MODES:
        raise ValueError(f"unknown mode: {mode}")
    if risk not in RISKS:
        raise ValueError(f"unknown risk: {risk}")

    refactoring_active = mode in {"behavior-preserving-refactor", "mixed-change"}
    evidence = {
        "tests_passed": bool(payload.get("tests_passed")),
        "characterization_tests": bool(payload.get("characterization_tests")),
        "tool_proven": bool(payload.get("tool_proven")),
        "baseline_described": bool(payload.get("baseline_described")),
        "performance_verified": bool(payload.get("performance_verified")),
    }
    constraints = list(payload.get("performance_constraints") or [])
    blockers = []
    warnings = []

    if refactoring_active and not evidence["baseline_described"]:
        blockers.append("Describe observable behavior before structural changes.")

    if refactoring_active and risk in {"medium", "high"}:
        if not (evidence["tests_passed"] or evidence["characterization_tests"]):
            blockers.append("Medium/high-risk refactoring requires relevant tests or characterization tests.")
    elif refactoring_active and risk == "low":
        if not (evidence["tests_passed"] or evidence["characterization_tests"] or evidence["tool_proven"]):
            blockers.append("Low-risk refactoring still requires existing validation or a tool-proven rename/move.")

    if refactoring_active and constraints and not evidence["performance_verified"]:
        blockers.append("Explicit performance constraints must be re-verified after refactoring.")
    if refactoring_active and not constraints:
        warnings.append("No explicit performance constraint was supplied; confirm whether the project defines one.")

    phases = {
        "feature-design": ["feature-change", "feature-validation"],
        "behavior-preserving-refactor": ["behavior-baseline", "small-structural-steps", "refactoring-validation"],
        "mixed-change": ["behavior-baseline", "small-structural-steps", "refactoring-validation", "feature-change", "feature-validation"],
    }[mode]
    return {
        "mode": mode,
        "risk": risk,
        "kind": "gate",
        "allowed": not blockers,
        "status": "pass" if not blockers else "blocked",
        "required_phases": phases,
        "evidence": evidence,
        "performance_constraints": constraints,
        "blockers": blockers,
        "warnings": warnings,
        "decision_policy": ["D4=A", "D5=A", "D8=A"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=MODES, default="feature-design")
    parser.add_argument("--risk", choices=RISKS, default="low")
    parser.add_argument("--tests-passed", action="store_true")
    parser.add_argument("--characterization-tests", action="store_true")
    parser.add_argument("--tool-proven", action="store_true")
    parser.add_argument("--baseline-described", action="store_true")
    parser.add_argument("--performance-constraint", action="append", default=[], dest="performance_constraints")
    parser.add_argument("--performance-verified", action="store_true")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    result = evaluate(vars(args))
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['status'].upper()}: mode={result['mode']} risk={result['risk']}")
        for item in result["blockers"]:
            print(f"BLOCKER: {item}")
        for item in result["warnings"]:
            print(f"WARNING: {item}")
        print("Phases: " + " -> ".join(result["required_phases"]))
    return 0 if result["allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
