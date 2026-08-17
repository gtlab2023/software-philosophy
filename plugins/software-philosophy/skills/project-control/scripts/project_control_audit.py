#!/usr/bin/env python3
"""Check configured material changes have a matching human-readable document change."""
from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from pathlib import Path
from typing import Any


def load_config(root: Path) -> dict[str, Any] | None:
    path = root / ".project-control.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != 1:
        raise ValueError(".project-control.json must be an object with version 1")
    return data


def matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def audit(root: Path, paths: list[str]) -> dict[str, Any]:
    config = load_config(root)
    normalized = sorted({Path(path).as_posix().lstrip("./") for path in paths if path})
    if not config or not config.get("enabled", False):
        return {"enabled": False, "passed": True, "changed_paths": normalized, "findings": []}

    findings = []
    for index, rule in enumerate(config.get("rules", []), start=1):
        if not isinstance(rule, dict):
            raise ValueError(f"rule {index} must be an object")
        source_patterns = rule.get("paths", [])
        document_patterns = rule.get("require_any", [])
        if not source_patterns or not document_patterns:
            raise ValueError(f"rule {index} requires non-empty paths and require_any")
        affected = [path for path in normalized if matches(path, source_patterns)]
        documented = [path for path in normalized if matches(path, document_patterns)]
        if affected and not documented:
            findings.append({
                "rule": index,
                "affected_paths": affected,
                "required_documents": document_patterns,
                "reason": rule.get("reason", "Material changes need a matching human-readable document update."),
            })

    return {
        "enabled": True,
        "passed": not findings,
        "changed_paths": normalized,
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--paths-json")
    parser.add_argument("--format", choices=("json", "text"), default="text")
    args = parser.parse_args()
    paths = list(args.path)
    if args.paths_json:
        decoded = json.loads(args.paths_json)
        if not isinstance(decoded, list) or not all(isinstance(path, str) for path in decoded):
            raise ValueError("--paths-json must be a JSON array of strings")
        paths.extend(decoded)
    try:
        result = audit(Path(args.root).resolve(), paths)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif not result["enabled"]:
        print("Project control is not enabled for this repository.")
    elif result["passed"]:
        print("PASS: project-control documentation impact check")
    else:
        for finding in result["findings"]:
            print(f"FAIL: rule {finding['rule']}: {finding['reason']}")
            print("  affected: " + ", ".join(finding["affected_paths"]))
            print("  update one of: " + ", ".join(finding["required_documents"]))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
