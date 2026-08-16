#!/usr/bin/env python3
"""Small dependency-free audit that produces review leads, not definitive judgments."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java", ".kt", ".rb", ".swift"}


def files_for(paths):
    for raw in paths:
        path = Path(raw)
        if path.is_file() and path.suffix in EXTENSIONS:
            yield path
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and child.suffix in EXTENSIONS and ".git" not in child.parts:
                    yield child


def audit(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings = []
    lines = text.splitlines()

    # Conservative forwarding-method heuristic for common languages.
    forwarding = re.compile(r"(?:return\s+)?(?:self\.|this\.)?[A-Za-z_][\w.]*\([^\n]*\)\s*;?\s*$")
    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if forwarding.fullmatch(stripped) and ("return" in stripped or stripped.endswith(";")):
            findings.append({
                "rule": "SDP-RED-005",
                "name": "pass-through-method-candidate",
                "kind": "candidate",
                "confidence": "low",
                "severity": "low",
                "line": idx,
                "message": "Possible pass-through method; review whether this boundary hides meaningful policy."
            })

    # Repeated non-trivial adjacent lines within a file.
    normalized = {}
    for idx, line in enumerate(lines, 1):
        value = re.sub(r"\s+", " ", line.strip())
        if len(value) >= 32 and not value.startswith(("//", "#", "*")):
            normalized.setdefault(value, []).append(idx)
    for value, positions in normalized.items():
        if len(positions) > 1:
            findings.append({
                "rule": "SDP-RED-006",
                "name": "repeated-line-candidate",
                "kind": "candidate",
                "confidence": "low",
                "severity": "low",
                "line": positions[0],
                "message": f"A substantial line repeats at lines {positions}; review for duplicated design logic."
            })

    # Public-ish API smell: many parameters in one function signature.
    signature = re.compile(r"(?:function\s+\w+|def\s+\w+|fn\s+\w+|(?:public|private|protected)\s+\w+[\w<>\[\]]*\s+\w+)\s*\(([^)]*)\)")
    for match in signature.finditer(text):
        params = [p.strip() for p in match.group(1).split(",") if p.strip()]
        if len(params) >= 7:
            line = text[:match.start()].count("\n") + 1
            findings.append({
                "rule": "SDP-RED-004",
                "name": "overexposed-interface-candidate",
                "kind": "candidate",
                "confidence": "medium",
                "severity": "medium",
                "line": line,
                "message": f"Function-like interface has {len(params)} parameters; review common vs rare options."
            })

    return findings


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()
    results = []
    seen = set()
    for path in files_for(args.paths):
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        for finding in audit(path):
            results.append({"file": str(path), **finding})
    if args.format == "json":
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        if not results:
            print("No static design leads found. Contextual review is still required.")
        for item in results:
            print(f"{item['file']}:{item['line']} [{item['severity']}] {item['rule']}: {item['message']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
