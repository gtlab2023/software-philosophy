# Decision 0001: Refactoring Pack Conflict Policy

- Status: Accepted
- Date: 2026-08-16
- Applies to: `software-design-philosophy` + `refactoring-second-edition`

## Decision set

```text
D1=A
D2=C
D3=A
D4=A
D5=A
D6=A
D7=A
D8=A
```

## Resolutions

1. **Semantic extraction**：仅当提炼能够命名意图、隐藏细节或形成稳定边界时提炼函数；长度只是调查线索。
2. **Semantic split for special cases**：边界输入、协议差异和基础设施异常优先归一化；稳定且有独立业务语义的状态可建模为 Special Case；不得用 Special Case 隐藏错误。
3. **Design Twice + YAGNI**：非平凡修改比较两个设计，只实现当前需求证明有价值的最小完整方案。
4. **Risk-based testing gate**：中高风险重构需要相关测试或 characterization tests；低风险且工具可证明的重命名或移动可不新增测试。
5. **Measure-first performance policy**：默认先保证可读性并通过测量定位热点，同时保留项目明确声明的性能约束。
6. **Context-sensitive Data Class**：领域贫血对象是线索；DTO、消息、序列化结构和不可变值记录不自动构成坏味道。
7. **Boundary-value Middle Man test**：隐藏易变依赖图、权限、缓存、协议或所有权的委托层应保留；纯转发层才作为候选坏味道。
8. **Separate validation phases**：同一任务可包含重构与功能修改，但必须分阶段修改、验证和报告。

## Consequences

- Pack 规则通过 `extends`、`counterbalances` 和已决策映射组合，不把同一思想重复注册为多个 Hook。
- 静态检查只输出 `candidate`，不能把坏味道当成确定违规。
- 安全重构工作流必须显式记录模式、风险等级、行为基线、验证证据和性能约束。
