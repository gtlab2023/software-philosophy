#!/usr/bin/env python3
"""Codex lifecycle adapter for the opt-in project-control documentation guard."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "project-control" / "scripts"))
from project_control_audit import audit  # noqa: E402


def run_git(root: Path, *args: str) -> str:
    completed = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True)
    if completed.returncode:
        raise ValueError(completed.stderr.strip() or "not a Git repository")
    return completed.stdout


def repo_root(cwd: str | None) -> Path:
    candidate = Path(cwd or os.getcwd()).resolve()
    return Path(run_git(candidate, "rev-parse", "--show-toplevel").strip())


def fingerprint(path: Path) -> str:
    if not path.is_file():
        return "<missing>"
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def dirty_paths(root: Path) -> list[str]:
    paths = set()
    for args in (("diff", "--name-only"), ("diff", "--cached", "--name-only"), ("ls-files", "--others", "--exclude-standard")):
        paths.update(path for path in run_git(root, *args).splitlines() if path)
    return sorted(paths)


def state_path(payload: dict[str, Any], root: Path) -> Path:
    storage = Path(os.environ.get("PLUGIN_DATA", Path(tempfile.gettempdir()) / "software-philosophy"))
    identity = str(payload.get("session_id") or payload.get("conversation_id") or root)
    key = hashlib.sha256(identity.encode()).hexdigest()[:24]
    path = storage / "project-control" / f"{key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def begin(payload: dict[str, Any]) -> dict[str, Any]:
    root = repo_root(payload.get("cwd"))
    if not audit(root, [])["enabled"]:
        return {"continue": True}
    state = {
        "root": str(root),
        "head": run_git(root, "rev-parse", "HEAD").strip(),
        "dirty": {path: fingerprint(root / path) for path in dirty_paths(root)},
    }
    state_path(payload, root).write_text(json.dumps(state), encoding="utf-8")
    return {"continue": True}


def changed_since_start(root: Path, state: dict[str, Any]) -> list[str]:
    paths = set(dirty_paths(root))
    head = state.get("head")
    if head:
        paths.update(path for path in run_git(root, "diff", "--name-only", f"{head}...HEAD").splitlines() if path)
    baseline = state.get("dirty", {})
    changed = []
    for path in sorted(paths):
        if path not in baseline or fingerprint(root / path) != baseline[path]:
            changed.append(path)
    return changed


def finish(payload: dict[str, Any]) -> dict[str, Any]:
    root = repo_root(payload.get("cwd"))
    path = state_path(payload, root)
    if not path.is_file():
        return {"continue": True}
    state = json.loads(path.read_text(encoding="utf-8"))
    result = audit(root, changed_since_start(root, state))
    if not result["enabled"] or result["passed"]:
        path.unlink(missing_ok=True)
        return {"continue": True}
    messages = []
    for finding in result["findings"]:
        messages.append(
            f"{finding['reason']} Affected: {', '.join(finding['affected_paths'])}. "
            f"Update one of: {', '.join(finding['required_documents'])}."
        )
    return {
        "decision": "block",
        "reason": "Project-control documentation check failed. " + " ".join(messages) + " Use $project-control to update current human-readable documentation, then finish again.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", choices=("session-start", "post-tool-use", "stop"), required=True)
    args = parser.parse_args()
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if args.event == "session-start":
            response = begin(payload)
        elif args.event == "stop":
            response = finish(payload)
        else:
            response = {"continue": True}
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        response = {"continue": True, "systemMessage": f"Project-control hook skipped: {exc}"}
    print(json.dumps(response, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
