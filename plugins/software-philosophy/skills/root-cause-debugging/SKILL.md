---
name: root-cause-debugging
description: Diagnose failures from evidence before changing code. Use for regressions, flaky tests, unexpected behavior, unclear causes, boundary-spanning faults, or failed prior fixes.
---

# Root-Cause Debugging

Do not patch before obtaining causal evidence. If urgent containment is required, label it temporary and continue the investigation.

1. Reproduce the failure and capture the exact command, inputs, environment, output, frequency, and expected behavior.
2. Locate the first observable divergence. Trace values and control flow backward across boundaries; add focused instrumentation when evidence is missing.
3. Compare a nearby working path, recent changes, and violated invariants. Separate correlation from mechanism.
4. State one to three falsifiable hypotheses, rank them, and run the smallest test that distinguishes them. Change one variable at a time.
5. Correct the narrowest root cause, not the downstream symptom. Avoid unrelated cleanup.
6. Add or strengthen a regression test when the behavior is testable. Re-run the reproducer, narrow tests, then broader relevant checks.

After three failed fixes, or when no hypothesis explains the evidence, stop changing code and revisit assumptions, architecture, or ownership boundaries with `assumption-audit` or `design-review`.

Report the symptom, evidence chain, root cause, rejected hypotheses, correction, regression evidence, and residual uncertainty.
