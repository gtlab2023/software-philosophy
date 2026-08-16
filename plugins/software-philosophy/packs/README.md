# Knowledge Packs

Pack 保存来源原则和关系，不直接注册 Hook，也不要求代理在所有任务中加载。

## Contract

每个 Pack 至少包含 `principles.json`。可选：

- `red_flags.json`：设计红旗；
- `smells.json`：只产生 `candidate` 的上下文坏味道；
- `refactorings.json`：意图、风险、验证和反向手法；
- `mappings.json`：跨 Pack 的 `extends`、`counterbalance`、`conflicts` 和决策；
- `references/`：仅按需读取的深度资料；
- principle `runtime`：用于生成短规则胶囊的提示、触发词和优先级。

新增 Pack 时：

1. 分配全局稳定 ID；
2. 复用 Core 并声明跨 Pack 关系；
3. 不复制 Skill、Hook 或检查器；
4. 不保存书籍原文；
5. 为误报例外、冲突决策和触发行为增加 eval；
6. 如果进入运行胶囊，必须通过 `context_budget_audit.py`。
