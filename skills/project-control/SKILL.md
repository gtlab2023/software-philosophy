---
name: project-control
description: Keep AI-developed projects legible and verifiable. Use to establish, update, or audit current project status, capability maps, module boundaries, risks, decisions, and evidence after changes to behavior, public interfaces, schemas, protocols, deployment, operations, or material risks; also use to detect documentation drift. Skip formatting-only changes and internal refactors with no durable impact.
---

# Project Control

Maintain a small control plane so people can find current truth without reading every implementation detail.

## Workflow

1. Read applicable instructions, project layout, current documents, and validation commands. Treat code, manifests, tests, and deployed configuration as evidence; treat plans and logs as history unless marked current.
2. Choose `bootstrap`, `update`, `audit`, or `verify`.
3. Update current documents when behavior, capability, boundary, interface, protocol, operation, or material risk changes. Otherwise state `docs impact: none` with a reason.
4. Keep current truth, durable decisions, and history separate. Never repair a historical log to describe present reality.
5. Run deterministic checks where code can prove facts. Never invent verification evidence.
6. Before handoff, report updated documents, fresh verification, and remaining uncertainty.

## Minimum Control Plane

- `README.md`: five-minute entry and reading paths.
- `docs/current/`: status, capability matrix, risks, and dated evidence.
- `docs/architecture/`: module responsibility, interfaces, invariants, failure modes, and tests.
- `docs/decisions/`: durable tradeoffs; `docs/history/`: plans and logs.

Use the `assets/` templates, but adapt paths rather than creating duplicate truth.

## Automation

Copy `assets/.project-control.json` to opt in and narrow its rules to durable boundaries. Add `assets/AGENTS.md.fragment` to project instructions. Run `scripts/project_control_audit.py --root <project> --path <changed-path>` in CI. The bundled Hook blocks task completion when configured material paths change without a matching document; it never writes documents automatically.

Use `Designed`, `Implemented`, `Unit Verified`, `Integrated`, `Deployed`, and `Production Verified`. Attach fresh commands, dates, commits, and environment limits to verification claims.
