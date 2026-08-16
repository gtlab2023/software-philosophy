# Hook Coordinator

所有 Pack 共用一个平台无关 coordinator；书籍不能注册独立 Hook。

## Lifecycle

- `preflight`：聚合规则，并在需要时运行重构门禁或推理胶囊；
- `post-edit`：运行复杂性、坏味道和安全检查；
- `final-review`：生成统一交付报告。

## Progressive reasoning

普通请求默认：

```json
{"reasoning_mode":"off"}
```

此时只启用两个工程 Pack，不加载假设/解释规则。只有明确需要审查假设、根因或高成本决策时使用：

```json
{
  "event": "preflight",
  "mode": "feature-design",
  "reasoning_mode": "assumption-audit",
  "reasoning_query": "是否应该把当前专用实现改造成通用平台？"
}
```

协调器会按需加入两个推理 Pack，并从共享胶囊最多返回 5 条短规则。完整 Pack、参考资料和书籍内容不会注入 Hook 输出。

重构字段仍包括 `risk`、`baseline_described`、测试证据和性能约束。静态结果保持 `kind: candidate`；只有安全门禁使用 `kind: gate`。
