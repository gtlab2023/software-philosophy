---
name: design-twice
description: Compare two plausible designs for a non-trivial feature, API, state flow, persistence change, or cross-module refactor, then choose the smallest complete option justified by current evidence.
---

# Design Twice

Compare:

- **A — Minimal coherent change**: smallest boundary-preserving design;
- **B — Structural improvement**: centralizes more durable complexity.

For each, state interface, complexity location, hidden/exposed knowledge, assumptions, migration cost, validation, rollback, performance constraints, and likely red flags. When candidates depend on different premises, use `assumption-audit` to identify distinguishing evidence.

Choose explicitly. Apply YAGNI after comparison; record unjustified long-term capability instead of building it.
