---
name: disciplined-delivery
description: Execute risky or multi-step changes with checkpoints, optional isolation and parallelism, test-first feedback, review, and fresh verification. Use for cross-module, multi-agent, or branch-delivery work; skip routine edits.
---

# Disciplined Delivery

Use the lightest workflow matching the actual risk.

1. **Preflight**: read repository instructions and approved requirements. Record acceptance criteria, dependencies, risk, baseline checks, and stop conditions.
2. **Isolate when useful**: for risky, concurrent, or interruptible work, use an isolated workspace or Git worktree/branch when supported. Verify a clean baseline and ignored project-local worktree directories. Skip isolation without a concrete benefit.
3. **Decompose by dependency**: make a short ordered plan. Parallelize only tasks without shared mutable files, state, or unresolved design. Give each worker bounded scope, constraints, paths, and acceptance checks; otherwise work serially.
4. **Use feedback**: for observable behavior changes, prefer a failing test or reproducer before the minimal passing change, then refactor. Record justified exceptions. For structural work, use `safe-refactoring` and separate behavior from structure.
5. **Checkpoint**: work in small batches, run narrow validation, inspect the diff, and stop on baseline failure, conflicting requirements, or unexpected scope growth.
6. **Review**: request focused review of requirements, correctness, boundaries, tests, and risk. Check feedback against code and evidence. Resolve severe findings first; ask the user about speculative scope.
7. **Verify completion**: run fresh commands, inspect status and output, run broader relevant checks, and inspect final diff/status. Never claim success from stale or partial evidence.
8. **Finish safely**: present merge, PR/push, keep, or discard options when relevant. Do not push, merge, delete, or discard without authorization.

Report plan progress, verification evidence, review decisions, branch state, remaining risks, and any action requiring user choice.
