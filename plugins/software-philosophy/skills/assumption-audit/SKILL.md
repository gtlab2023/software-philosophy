---
name: assumption-audit
description: Audit hidden assumptions and competing explanations for ambiguous requirements, architecture choices, root-cause analysis, costly decisions, or daily planning. Use when premises or rationale materially affect the outcome; do not use for routine edits or simple factual questions.
---

# Assumption Audit

Use only when assumptions or explanations materially affect the decision.

1. Separate facts, goals, hard constraints, inferences, and assumptions.
2. Identify the assumptions whose failure changes the conclusion; state scope and uncertainty.
3. Run `python3 scripts/select_capsule.py --capability assumption-audit --query "<task>"` and use only the returned rules. Do not load whole Packs by default.
4. Propose at least one real competing explanation or design.
5. Prefer explanations fixed by mechanisms and constraints, not ones adjustable to every result.
6. Define evidence that distinguishes candidates and the smallest useful test.
7. Distinguish solvable in principle from feasible now.
8. Return the decision, evidence, falsifier, next test, and residual uncertainty.

For explicit philosophical or deep comparative analysis only, read the Pack references. Project instructions, safety, observable behavior, and test gates remain authoritative constraints.
