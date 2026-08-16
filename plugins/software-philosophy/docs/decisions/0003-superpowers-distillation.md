# Decision 0003: Distill Superpowers without stacking workflow plugins

## Status

Accepted for 0.4.0.

## Problem

Running Superpowers beside Software Philosophy duplicated brainstorming, planning, debugging, testing, review, and completion guidance. The local Superpowers 6.3.0 installation exposed fourteen Skills and approximately 584 estimated always-visible tokens, while several invoked Skills were substantially larger. Keeping both enabled risked repeated process, conflicting triggers, extra latency, and context cost.

## Decision

Integrate only the capabilities not already represented clearly:

- `root-cause-debugging`: reproduction, first divergence, evidence tracing, falsifiable hypotheses, minimal causal correction, and regression verification;
- `disciplined-delivery`: optional worktree isolation, dependency-aware parallelism, test-first feedback, focused review, fresh completion evidence, and authorization-aware branch finishing.

Retain existing Skills for design comparison, planning-level review, assumptions, architecture decisions, complexity, and refactoring. Do not add equivalents of Superpowers' global invocation policy or Skill-authoring workflow.

## Conflict policy

- Apply the lightest process matching risk; routine edits must not trigger delivery ceremony.
- Test-first is preferred for observable behavior, not universal dogma.
- Parallel execution requires independent state and resolved design.
- Review feedback is evidence to verify, not an instruction to accept blindly.
- Fresh verification is mandatory before completion claims.
- Destructive or remote Git actions still require user authorization.

## Context budget

The source Skill metadata estimate is capped at 600 tokens. Version 0.4.0 establishes a 565-token baseline and allows no silent increase from that baseline. Skill bodies remain on demand and each stays below 650 estimated tokens.

## Attribution

Superpowers 6.3.0 by Jesse Vincent is MIT-licensed. The source was used as conceptual input; all runtime instructions here were rewritten and compressed. See `THIRD_PARTY_NOTICES.md`.
