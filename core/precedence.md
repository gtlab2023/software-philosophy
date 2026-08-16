# Rule Precedence

当多个来源提供规则时，按以下顺序处理：

1. **Safety and correctness**：安全、数据边界、兼容性、正确性和不可破坏的系统约束；
2. **Explicit project instructions**：当前仓库的 `AGENTS.md`、`CLAUDE.md`、架构决策和用户明确要求；
3. **Core invariants**：本项目 `core/` 中的设计不变量；
4. **Task context**：当前任务的风险、期限、规模和修改范围；
5. **Enabled Packs**：当前任务明确启用的书籍/方法论规则包；
6. **Style preferences**：个人风格和非必要偏好。

低优先级规则不能静默覆盖高优先级规则。

如果两个同级规则无法同时满足，输出冲突报告：

- 冲突规则 ID；
- 各自要求；
- 当前任务相关上下文；
- 选择的规则；
- 被放弃的规则；
- 选择理由。
