# Decision 0002: Assumptions, Explanations, and Context Budget

- Status: Accepted
- Date: 2026-08-16
- Applies to: `first-principles-thinking`, `beginning-of-infinity`, and all existing Packs

## Decisions

### D9 — Provisional foundations

第一性原理在代理工作流中表示“当前任务明确采用的基础假设或不变量”，不是不可修正的永恒真理。任何基础假设都必须声明适用边界、证据和可推翻条件。

### D10 — Explanation and verification

好解释不能代替测试；测试通过也不能代替根因解释。结构性决策需要解释，行为正确性需要可执行验证。

### D11 — Constrained optimism

“特定问题原则上可解决”用于反对宿命论，不构成对当前时间、成本、权限、数据和技术条件的可行性承诺。

### D12 — Demand-justified universality

只有当当前任务出现稳定机制、真实复用或纠错收益时才追求通用性。通用性不能覆盖 YAGNI、清晰领域边界和最小完整设计。

### D13 — Criticism, not contrarianism

不依赖权威意味着允许质疑并要求理由，不意味着默认反对共识。替代解释必须承担同等证据、风险和验证责任。

### D14 — Progressive disclosure

两个新 Pack 默认不进入普通编程任务上下文。运行时只允许通过一个共享 Skill 或显式 Hook `reasoning_mode` 选择最多 5 条短规则；完整 Pack 和参考资料仅在明确深度分析时读取。

## Consequences

- 两本书各自保留来源 Pack，但运行时编译为同一个 `assumption-audit` 胶囊。
- 不增加书籍专属 Hook，不为每本书创建 Skill。
- 普通任务继续只启用原有两个工程 Pack。
- 构建与测试必须执行上下文预算审计，超预算失败。
