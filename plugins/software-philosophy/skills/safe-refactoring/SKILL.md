---
name: safe-refactoring
description: Execute behavior-preserving structural changes with explicit modes, risk-based test gates, small reversible steps, and contextual smells. Use for legacy cleanup, preparatory refactoring, API-preserving restructuring, or mixed feature/refactoring work.
---

# Safe Refactoring

Choose `behavior-preserving-refactor`, `feature-design`, or `mixed-change`; never interleave structural and behavior changes within one step.

1. Record observable outputs, errors, state, persistence, protocols, compatibility, and performance constraints.
2. Set risk. Medium/high refactors need relevant tests or characterization tests. Low-risk tool-proven renames/moves still need existing validation.
3. Investigate a concrete friction or smell. Compare a refactoring with its inverse when available.
4. Prefer semantic boundaries; exempt legitimate DTOs and delegation that hides volatile knowledge.
5. Make one reversible structural change, run the narrowest validation, and revert immediately on baseline failure.
6. In mixed mode, finish and validate the structural phase before changing behavior.

Report mode, risk, baseline, constraints, investigated candidate, steps, rollback points, phase-specific validation, and residual risk.
