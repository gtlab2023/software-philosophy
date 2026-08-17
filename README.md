# Software Philosophy

面向 Codex 与 Claude Code 的低上下文开销软件工程插件。项目使用一套源码生成两个宿主发布包，把软件设计思想与经过压缩的调试、执行和交付纪律组织为可组合的 Core、Packs、任务型 Skills、审计器和统一 Hook。

本项目只保存重新表述的原则、决策问题和工作流，不保存书籍原文。

## 内置 Packs

### 默认工程 Packs

- `software-design-philosophy`：复杂性、深模块、信息隐藏、清晰边界和战略设计；
- `refactoring-second-edition`：行为保持、小步重构、上下文坏味道和风险测试门禁。

普通编程任务默认只启用这两个 Pack。

### 按需推理 Packs

- `first-principles-thinking`：显式化承重假设、系统边界、推理层级和机制迁移；
- `beginning-of-infinity`：易谬主义、好解释、竞争解释、批评与纠错、受约束的乐观主义。

两个推理 Pack 不常驻普通任务上下文，只通过 `assumption-audit` Skill 或显式 Hook `reasoning_mode` 按需启用。

## Progressive disclosure

```text
Skill 元数据               始终可见，但受预算约束
SKILL.md                   仅 Skill 命中后加载
capsules/                  脚本最多选择 5 条短规则
Pack principles/references 仅明确深度分析时读取
```

两个来源 Pack 会编译成共享胶囊：

`capsules/assumption-audit.json`

普通请求不会加载胶囊正文；显式审查时运行：

```bash
python3 scripts/select_capsule.py \
  --capability assumption-audit \
  --query "是否应该把当前专用实现改造成通用平台？"
```

## Skills

- `design-review`
- `complexity-audit`
- `safe-refactoring`
- `design-twice`
- `architecture-decision`
- `assumption-audit`
- `root-cause-debugging`
- `disciplined-delivery`
- `project-control`

Skills 按任务组织，不按书籍或单个重构手法组织。

`root-cause-debugging` 与 `disciplined-delivery` 吸收了 Superpowers 中不与现有设计能力重复的部分：故障证据链、可证伪假设、测试优先反馈、可选 worktree、依赖感知并行、代码审查和完成前验证。它们按需触发，不提供全局强制流程；普通修改不会自动承担完整交付仪式。

`project-control` 将同一套复杂度控制应用于项目认知：它把当前事实、架构边界、决策和历史分开；为项目提供能力矩阵、风险清单和验证证据模板；并可通过项目根 `.project-control.json` 与 Hook 在重大代码变更缺少对应人类文档时阻止任务结束。它默认不启用，也不会自动改写项目文档。

## Project control adoption

在目标项目中显式调用 `$project-control` 建立最小控制面。需要自动门禁时，复制 Skill 的 `.project-control.json` 模板到项目根并缩小路径规则，再将 `AGENTS.md.fragment` 合入项目指令。之后 Hook 只对已启用项目生效：它会在任务结束前检查本轮重大代码变更是否带有匹配的人类文档；CI 可直接运行 `project_control_audit.py` 做相同的确定性检查。

## Installation

Codex:

```bash
codex plugin marketplace add gtlab2023/software-philosophy
codex plugin add software-philosophy@software-philosophy
```

Claude Code:

```bash
claude plugin marketplace add gtlab2023/software-philosophy
claude plugin install software-philosophy@software-philosophy --scope user
```

See `docs/installation.md` for local development, updates, removal, and validation.

## Commands

聚合全部来源规则：

```bash
python3 scripts/aggregate_rules.py \
  --pack software-design-philosophy \
  --pack refactoring-second-edition \
  --pack first-principles-thinking \
  --pack beginning-of-infinity \
  --format markdown
```

验证上下文预算：

```bash
python3 scripts/context_budget_audit.py
```

测试和构建：

```bash
python3 scripts/test_plugin.py
python3 scripts/build_release.py --clean
```

发布目录：

- `dist/codex`
- `dist/claude`

## Invariants

- 一本书不是一个 Skill，也不拥有 Hook；
- 静态检测只能产生 `candidate`，安全门禁必须有证据；
- 第一性原理是可修正的任务基础，不是不可质疑的真理；
- 好解释不能代替测试，测试通过也不能代替根因解释；
- 通用性服从当前需求、YAGNI 和清晰边界；
- 新能力不能静默增加普通任务上下文；构建超出预算时失败。
- 并行、worktree、TDD 和多代理按风险选择，不是每个任务的必经步骤；
- 没有新鲜命令输出时不能宣称验证或交付完成；远程及破坏性 Git 操作仍需授权。

## Attribution

紧凑调试与交付工作流参考了 MIT 许可的 Superpowers 6.3.0，并经过独立重写、去重和上下文预算约束。详情见 `THIRD_PARTY_NOTICES.md` 与 `docs/decisions/0003-superpowers-distillation.md`。
