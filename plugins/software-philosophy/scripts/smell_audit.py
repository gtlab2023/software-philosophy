#!/usr/bin/env python3
"""Conservative static code-smell detector. Every result is a contextual candidate."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".rs", ".go", ".java", ".kt", ".rb", ".swift"}
DATA_TRANSFER_NAMES = re.compile(r"(?:DTO|Dto|Message|Record|Payload|Request|Response|Event|Value)$")


def files_for(paths: list[Path]):
    for path in paths:
        if path.is_file() and path.suffix in EXTENSIONS:
            yield path
        elif path.is_dir():
            for child in path.rglob("*"):
                if child.is_file() and child.suffix in EXTENSIONS and ".git" not in child.parts:
                    yield child


def candidate(rule: str, name: str, line: int, severity: str, confidence: str, message: str, question: str, suggestions: list[str]):
    return {
        "rule": rule,
        "name": name,
        "kind": "candidate",
        "severity": severity,
        "confidence": confidence,
        "line": line,
        "message": message,
        "decision_question": question,
        "suggested_refactorings": suggestions,
    }


def python_data_classes(text: str):
    findings = []
    lines = text.splitlines()
    class_pattern = re.compile(r"^(class)\s+(\w+)(?:\([^)]*\))?:\s*$")
    for index, line in enumerate(lines):
        match = class_pattern.match(line)
        if not match:
            continue
        name = match.group(2)
        if DATA_TRANSFER_NAMES.search(name):
            continue
        decorators = "\n".join(lines[max(0, index - 3):index])
        if re.search(r"@dataclass\s*\([^)]*frozen\s*=\s*True", decorators):
            continue
        body = []
        for following in lines[index + 1:]:
            if following.strip() and not following.startswith((" ", "\t")):
                break
            body.append(following)
        fields = sum(bool(re.match(r"\s{4,}[A-Za-z_]\w*\s*:\s*[^=]+(?:=.*)?$", item)) for item in body)
        methods = [re.match(r"\s{4,}def\s+(\w+)\s*\(", item) for item in body]
        domain_methods = [item.group(1) for item in methods if item and not item.group(1).startswith("__")]
        if fields >= 3 and not domain_methods:
            findings.append(candidate(
                "REF-SMELL-DATA-CLASS", "data-class-candidate", index + 1, "low", "low",
                f"Class {name} contains several fields and no detected domain methods; confirm its role before moving behavior.",
                "这是贫血领域模型，还是合法的 DTO、消息、序列化结构或不可变值记录？",
                ["REF-MOVE-FUNCTION", "REF-ENCAPSULATE-RECORD"],
            ))
    return findings


def audit(path: Path):
    text = path.read_text(encoding="utf-8", errors="ignore")
    findings = []

    signature = re.compile(r"(?:function\s+\w+|def\s+\w+|fn\s+\w+|(?:public|private|protected)\s+\w+[\w<>\[\]]*\s+\w+)\s*\(([^)]*)\)")
    for match in signature.finditer(text):
        params = [part.strip() for part in match.group(1).split(",") if part.strip() and part.strip() not in {"self", "cls"}]
        if len(params) >= 7:
            line = text[:match.start()].count("\n") + 1
            findings.append(candidate(
                "REF-SMELL-LONG-PARAMETER-LIST", "long-parameter-list-candidate", line, "medium", "medium",
                f"Function-like declaration has {len(params)} parameters.",
                "这些参数是否反复表达同一概念或暴露了调用者不应了解的细节？",
                ["REF-INTRODUCE-PARAMETER-OBJECT", "REF-PRESERVE-WHOLE-OBJECT"],
            ))

    chain_pattern = re.compile(r"\b[A-Za-z_]\w*(?:\([^\n;]*?\))?(?:\.[A-Za-z_]\w*(?:\([^\n;]*?\))?){3,}")
    for match in chain_pattern.finditer(text):
        line = text[:match.start()].count("\n") + 1
        findings.append(candidate(
            "REF-SMELL-MESSAGE-CHAINS", "message-chain-candidate", line, "medium", "low",
            "A long access/call chain may expose an unstable object graph.",
            "调用者是否了解了不稳定的对象图或访问路径？",
            ["REF-HIDE-DELEGATE", "REF-EXTRACT-FUNCTION"],
        ))

    if path.suffix in {".js", ".jsx", ".ts", ".tsx"}:
        global_mutable = re.compile(r"^(?:export\s+)?(?:let|var)\s+([a-z_]\w*)\s*=", re.MULTILINE)
        for match in global_mutable.finditer(text):
            line = text[:match.start()].count("\n") + 1
            findings.append(candidate(
                "REF-SMELL-GLOBAL-DATA", "global-mutable-data-candidate", line, "high", "medium",
                f"Top-level mutable binding {match.group(1)} may have unclear ownership.",
                "共享可变数据的写入者、生命周期和不变量是否有明确所有者？",
                ["REF-ENCAPSULATE-VARIABLE"],
            ))

    if path.suffix == ".py":
        findings.extend(python_data_classes(text))

    return findings


def main() -> int:
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
    elif not results:
        print("No static smell candidates found. Contextual review is still required.")
    else:
        for item in results:
            print(f"{item['file']}:{item['line']} [{item['severity']}/{item['confidence']}] {item['rule']} candidate: {item['message']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
