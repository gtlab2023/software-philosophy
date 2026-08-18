#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
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


def distilled_workflow_checks(checks):
    required = {
        "root-cause-debugging": [
            "Reproduce the failure", "first observable divergence", "falsifiable hypotheses",
            "regression test", "three failed fixes",
        ],
        "disciplined-delivery": [
            "Git worktree", "Parallelize only", "failing test or reproducer",
            "focused review", "fresh commands", "without authorization",
        ],
    }
    for skill, phrases in required.items():
        path = ROOT / "skills" / skill / "SKILL.md"
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        add(checks, f"distilled workflow skill exists: {skill}", bool(text))
        add(checks, f"distilled workflow is complete: {skill}", "TODO" not in text and all(phrase in text for phrase in phrases))
        add(checks, f"Codex UI metadata exists: {skill}", (path.parent / "agents/openai.yaml").is_file())

    notice = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    add(checks, "Superpowers attribution is recorded", all(token in notice for token in ("Superpowers", "Jesse Vincent", "MIT License")))


def progressive_disclosure_checks(checks):
    current = run("scripts/build_capsules.py", "--check")
    add(checks, "generated capsule is current", current.returncode == 0, current.stdout + current.stderr)
    budget = run("scripts/context_budget_audit.py", "--format", "json")
    budget_data = json.loads(budget.stdout) if budget.stdout else {}
    add(checks, "context budget audit passes", budget.returncode == 0 and budget_data.get("passed"), budget.stderr)
    add(checks, "always-visible metadata does not exceed configured baseline", budget_data.get("metrics", {}).get("skill_metadata_delta_estimated_tokens", 1) <= 0)

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


def project_control_checks(checks):
    skill = ROOT / "skills" / "project-control"
    text = (skill / "SKILL.md").read_text(encoding="utf-8") if (skill / "SKILL.md").is_file() else ""
    add(checks, "project-control skill exists", bool(text) and "TODO" not in text)
    add(checks, "project-control UI metadata exists", (skill / "agents/openai.yaml").is_file())
    add(checks, "project-control templates exist", all((skill / "assets" / name).is_file() for name in (
        ".project-control.json", "AGENTS.md.fragment", "STATUS.md", "CAPABILITIES.md", "RISKS.md",
    )))
    hook_config = ROOT / "hooks/hooks.json"
    hook_data = json.loads(hook_config.read_text(encoding="utf-8")) if hook_config.is_file() else {}
    add(checks, "project-control Hook config exists", "Stop" in hook_data.get("hooks", {}))
    handlers = [
        handler
        for groups in hook_data.get("hooks", {}).values()
        for group in groups
        for handler in group.get("hooks", [])
    ]
    add(checks, "project-control Hook uses portable launchers", bool(handlers) and all(
        "run-project-control.sh" in handler.get("command", "")
        and "run-project-control.ps1" in handler.get("commandWindows", "")
        for handler in handlers
    ))
    add(checks, "Unix Hook resolves both plugin root variables", bool(handlers) and all(
        "CLAUDE_PLUGIN_ROOT" in handler.get("command", "")
        and "PLUGIN_ROOT" in handler.get("command", "")
        for handler in handlers
    ))
    add(checks, "Windows Hook uses host-expanded plugin root with File mode", bool(handlers) and all(
        "-File" in handler.get("commandWindows", "")
        and "-Command" not in handler.get("commandWindows", "")
        and r'${PLUGIN_ROOT}\hooks\run-project-control.ps1' in handler.get("commandWindows", "")
        for handler in handlers
    ))

    launcher = ROOT / "hooks/run-project-control.sh"
    windows_launcher = ROOT / "hooks/run-project-control.ps1"
    add(checks, "project-control launchers exist", launcher.is_file() and windows_launcher.is_file())

    with tempfile.TemporaryDirectory() as temporary:
        temporary_path = Path(temporary)
        empty_bin = temporary_path / "empty-bin"
        empty_bin.mkdir()
        environment = {
            **os.environ,
            "PATH": str(empty_bin),
            "CLAUDE_PLUGIN_ROOT": str(ROOT),
        }
        skipped = subprocess.run(
            ["/bin/sh", str(launcher), "project-control-session-start"],
            cwd=temporary_path, input="{}", text=True, capture_output=True, env=environment,
        )
        skipped_data = json.loads(skipped.stdout)
        add(checks, "project-control Hook skips cleanly without Python", skipped.returncode == 0 and skipped_data == {"continue": True}, skipped.stderr)

        host_environment = {
            key: value for key, value in os.environ.items()
            if key not in {"CLAUDE_PLUGIN_ROOT", "PLUGIN_ROOT", "SOFTWARE_PHILOSOPHY_PYTHON"}
        }
        host_environment.update({"PATH": str(empty_bin), "PLUGIN_ROOT": str(ROOT)})
        host_neutral = subprocess.run(
            handlers[0]["command"], shell=True, executable="/bin/sh",
            cwd=temporary_path, input="{}", text=True, capture_output=True, env=host_environment,
        )
        host_neutral_data = json.loads(host_neutral.stdout) if host_neutral.stdout else {}
        add(checks, "project-control Hook starts with only PLUGIN_ROOT", host_neutral.returncode == 0 and host_neutral_data == {"continue": True}, host_neutral.stderr)

        (temporary_path / ".project-control.json").write_text('{"version":1,"enabled":true}', encoding="utf-8")
        warned = subprocess.run(
            ["/bin/sh", str(launcher), "project-control-stop"],
            cwd=temporary_path, input="{}", text=True, capture_output=True, env=environment,
        )
        warned_data = json.loads(warned.stdout)
        add(checks, "project-control Hook explains missing Python when configured", warned.returncode == 0 and "systemMessage" in warned_data, warned.stderr)

        fake_bin = temporary_path / "fake-bin"
        fake_bin.mkdir()
        old_python = fake_bin / "python3"
        old_python.write_text('#!/bin/sh\n[ "$1" = "-c" ] && exit 1\nexit 91\n', encoding="utf-8")
        old_python.chmod(0o755)
        fallback_python = fake_bin / "python"
        fallback_python.write_text('#!/bin/sh\n[ "$1" = "-c" ] && exit 0\nexit 17\n', encoding="utf-8")
        fallback_python.chmod(0o755)
        fallback_environment = {**environment, "PATH": str(fake_bin)}
        fallback = subprocess.run(
            ["/bin/sh", str(launcher), "project-control-stop"],
            cwd=temporary_path, input="{}", text=True, capture_output=True, env=fallback_environment,
        )
        add(checks, "project-control Hook rejects old Python and preserves selected exit code", fallback.returncode == 17, fallback.stderr)

        custom_python = temporary_path / "custom python"
        custom_python.write_text('#!/bin/sh\n[ "$1" = "-c" ] && exit 0\nexit 23\n', encoding="utf-8")
        custom_python.chmod(0o755)
        override_environment = {
            **environment,
            "SOFTWARE_PHILOSOPHY_PYTHON": str(custom_python),
        }
        override = subprocess.run(
            ["/bin/sh", str(launcher), "project-control-stop"],
            cwd=temporary_path, input="{}", text=True, capture_output=True, env=override_environment,
        )
        add(checks, "project-control Hook supports an interpreter path with spaces", override.returncode == 23, override.stderr)

    windows_text = windows_launcher.read_text(encoding="utf-8") if windows_launcher.is_file() else ""
    add(checks, "Windows launcher checks standard Python commands", all(token in windows_text for token in (
        "SOFTWARE_PHILOSOPHY_PYTHON", '"py"', '"python3"', '"python"',
    )))

    with tempfile.TemporaryDirectory() as temporary:
        project = Path(temporary)
        (project / ".project-control.json").write_text(json.dumps({
            "version": 1,
            "enabled": True,
            "rules": [{
                "paths": ["proto/**"],
                "require_any": ["docs/contracts/**"],
                "reason": "contracts stay readable",
            }],
        }), encoding="utf-8")
        missing = run(
            "skills/project-control/scripts/project_control_audit.py", "--root", str(project),
            "--path", "proto/example.proto", "--format", "json",
        )
        missing_data = json.loads(missing.stdout)
        add(checks, "project-control blocks undocumented material change", missing.returncode == 1 and len(missing_data["findings"]) == 1)
        covered = run(
            "skills/project-control/scripts/project_control_audit.py", "--root", str(project),
            "--path", "proto/example.proto", "--path", "docs/contracts/sync.md", "--format", "json",
        )
        covered_data = json.loads(covered.stdout)
        add(checks, "project-control accepts matching document update", covered.returncode == 0 and covered_data["passed"])

        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=project, check=True)
        subprocess.run(["git", "config", "user.name", "Plugin Test"], cwd=project, check=True)
        (project / "proto").mkdir()
        (project / "proto/example.proto").write_text("syntax = \"proto3\";\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=project, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline"], cwd=project, check=True)
        payload = json.dumps({"cwd": str(project), "session_id": "project-control-test"})
        environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PLUGIN_DATA": str(project / ".plugin-data")}
        hook = [sys.executable, str(ROOT / "hooks/coordinator.py")]
        started = subprocess.run([*hook, "--event", "project-control-session-start"], input=payload, text=True, capture_output=True, env=environment)
        (project / "proto/example.proto").write_text("syntax = \"proto3\";\nmessage Example {}\n", encoding="utf-8")
        blocked = subprocess.run([*hook, "--event", "project-control-stop"], input=payload, text=True, capture_output=True, env=environment)
        blocked_data = json.loads(blocked.stdout)
        add(checks, "project-control Hook blocks undocumented material change", started.returncode == 0 and blocked_data.get("decision") == "block")
        (project / "docs/contracts").mkdir(parents=True)
        (project / "docs/contracts/proto.md").write_text("# Proto contract\n", encoding="utf-8")
        released = subprocess.run([*hook, "--event", "project-control-stop"], input=payload, text=True, capture_output=True, env=environment)
        released_data = json.loads(released.stdout)
        add(checks, "project-control Hook releases documented change", released.returncode == 0 and released_data.get("continue") is True)


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
    distilled_workflow_checks(checks)
    progressive_disclosure_checks(checks)
    project_control_checks(checks)
    coordinator_regression_checks(checks)
    for name, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'}: {name}")
        if detail:
            print(detail.strip())
    return 0 if all(ok for _, ok, _ in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
