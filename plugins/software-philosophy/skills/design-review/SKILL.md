---
name: design-review
description: Review non-trivial changes for boundaries, complexity, assumptions, contextual smells, and safe evolution. Use for cross-module work, public APIs, persistence, protocols, or architecture.
---

# Design Review

Declare `feature-design`, `behavior-preserving-refactor`, or `mixed-change`.

1. Read repository instructions and nearby code.
2. State intended behavior, affected boundaries, callers, dependencies, risk, and explicit constraints.
3. If a load-bearing premise is unclear, use `assumption-audit`; otherwise do not load reasoning Packs.
4. Compare a minimal coherent design with a stronger-boundary alternative. Apply YAGNI after comparison.
5. Prefer simple common interfaces, hidden decisions, owned complexity, and semantic abstractions.
6. Treat smells as candidates. Do not split by length, objectify DTOs automatically, or remove valuable delegation.
7. For refactoring or mixed mode, establish a behavior baseline and validate structural changes before behavior changes.
8. Recheck the final diff.

Report mode, assumptions, complexity, alternatives, decision, boundaries, candidates, validation by phase, and residual risk. Safety, correctness, compatibility, and project instructions take precedence.
