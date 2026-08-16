# Software Philosophy

面向 Codex 与 Claude Code 的低上下文开销软件设计插件。项目使用一套源码生成两个宿主发布包，把多本书的思想组织为可组合的 Core、Packs、任务型 Skills、审计器和统一 Hook。

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

Skills 按任务组织，不按书籍或单个重构手法组织。

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
