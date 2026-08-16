---
name: complexity-audit
description: Audit a diff or code area for accidental complexity, information leakage, shallow boundaries, duplicated decisions, and contextual code smells. Use during review, before delivery, or after refactoring.
---

# Complexity Audit

1. Run `python3 scripts/complexity_audit.py <paths>`.
2. With the refactoring Pack enabled, also run `python3 scripts/smell_audit.py <paths>`.
3. Treat every static result as a candidate, never proof.
4. Review interface depth, decision ownership, repeated knowledge, special-case semantics, state, and dependency direction.
5. Exempt cohesive long functions, legitimate DTO/message/value records, and delegation that hides volatile graphs, permissions, caches, protocols, or ownership.
6. Report severity, confidence, location, decision question, impact, and a scoped alternative. Avoid unrelated refactoring.
