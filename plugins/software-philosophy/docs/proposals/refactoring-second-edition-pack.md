# Proposal: Refactoring, Second Edition Pack

Status: **Accepted and implemented**

## 1. Objective

将 Martin Fowler《重构：改善既有代码的设计（第 2 版）》中的精华注入 Software Philosophy，但不把每一种重构机械地变成独立 Skill，也不为这本书注册独立 Hook。

该 Pack 应补充现有《软件设计的哲学》Pack 的不足：

- 如何在不改变可观察行为的前提下安全改善结构；
- 如何识别代码坏味道；
- 如何选择和组合重构手法；
- 如何通过测试、小步修改和“两顶帽子”降低风险；
- 如何在真实遗留系统、分支、数据库和性能约束下工作。

本项目只保存重新表述后的原则、目录索引和工作流，不保存书籍原文。

## 2. Architectural placement

新增知识包，而不是新增独立插件：

```text
packs/refactoring-second-edition/
├── principles.json
├── smells.json
├── refactorings.json
├── mappings.json
└── references/
    ├── workflow.md
    ├── testing-safety.md
    └── catalog-guidance.md
```

### 2.1 `principles.json`

计划包含以下原则：

- 重构是在保持可观察行为的前提下改变内部结构；
- 明确区分“添加功能”和“重构”两种模式；
- 以可验证的小步执行结构变化；
- 在添加功能前做预备性重构；
- 在理解代码时做帮助理解的重构；
- 日常捡垃圾式重构优先于长期积累后集中清理；
- 重构需要可靠、快速、相关的测试反馈；
- YAGNI：不为假设中的未来需求提前构建能力；
- 坏味道是调查线索，不是自动定罪；
- 重构与性能优化目的不同，不能混为一种修改模式。

### 2.2 `smells.json`

收入第 2 版的坏味道分类，但每条都标记为：

- `contextual`：是否必须结合上下文判断；
- `static_detectability`：是否适合机械检测；
- `false_positive_risk`：误报风险；
- `related_rules`：与现有 SDP 规则的对应关系；
- `suggested_refactorings`：可能适用的重构手法，而不是强制方案。

示例：

```json
{
  "id": "REF-SMELL-MIDDLE-MAN",
  "title": "Middle Man",
  "contextual": true,
  "static_detectability": "lead-only",
  "false_positive_risk": "high",
  "related_rules": ["SDP-INTERFACE-001", "SDP-RED-005"],
  "decision_question": "该委托是否隐藏了易变依赖关系或访问路径？"
}
```

### 2.3 `refactorings.json`

不复制书中完整做法。每项重构只保存代理执行所需的简化结构：

```json
{
  "id": "REF-EXTRACT-FUNCTION",
  "title": "Extract Function",
  "intent": "把可独立命名的意图从实现细节中分离出来",
  "preconditions": [],
  "risks": [],
  "verification": [],
  "counter_refactoring": "REF-INLINE-FUNCTION",
  "related_smells": []
}
```

每个条目必须包含对应的反向或平衡手法。例如：

- Extract Function / Inline Function；
- Extract Class / Inline Class；
- Hide Delegate / Remove Middle Man；
- Replace Function with Command / Replace Command with Function；
- Change Reference to Value / Change Value to Reference。

这样可以防止代理把目录当作单向教条。

### 2.4 `mappings.json`

维护三类关系：

1. 坏味道 → 候选重构；
2. 现有 SDP 红旗 → Fowler 坏味道；
3. 互为平衡的重构手法。

不允许通过映射自动执行重构，只用于生成候选方案。

## 3. Skill changes

### 3.1 新增 `safe-refactoring`

这是唯一建议新增的 Skill。

触发范围：

- 用户明确要求重构；
- 修改目标是改善结构而非增加行为；
- 为即将加入的新功能做预备性重构；
- 遗留代码需要先建立可测试接缝；
- 重构公共 API、数据结构或持久化边界。

工作流：

1. 声明当前模式：`feature` 或 `refactor`；
2. 定义必须保持不变的可观察行为；
3. 找到或建立最小测试保护网；
4. 识别坏味道，但只选择一个当前阻塞目标；
5. 选择最小可逆重构；
6. 修改一步；
7. 运行最窄相关测试；
8. 重复，保持代码随时可工作；
9. 单独处理行为变化；
10. 最终运行更广验证并审查 diff。

### 3.2 扩展 `complexity-audit`

增加 Fowler 坏味道词汇和映射，但保持以下边界：

- 静态检查只产生 leads；
- 不把函数长度、类大小或参数数量直接判为失败；
- 先说明为什么某个坏味道增加了当前修改成本；
- 每个建议必须同时考虑其反向重构。

### 3.3 小幅扩展 `design-review`

在现有流程开头加入模式判断：

```text
feature-design | behavior-preserving-refactor | mixed-change
```

`mixed-change` 默认要求把结构调整和行为修改拆成可独立验证的阶段，但是否作为硬规则由所有者决定。

### 3.4 不新增以下 Skills

不按每项重构建立 `extract-function`、`move-field` 等 Skill。它们应是 `safe-refactoring` 可检索的目录数据，否则会产生几十个触发重叠的 Skills。

## 4. Hook coordinator changes

统一 Hook coordinator 增加 `mode`：

```json
{
  "event": "preflight | post-edit | final-review",
  "mode": "feature | refactor | mixed",
  "packs": [
    "software-design-philosophy",
    "refactoring-second-edition"
  ]
}
```

### `preflight`

- 识别是否为行为保持型重构；
- 记录行为不变量；
- 检查是否存在相关测试命令；
- 判断是否需要先建立 characterization tests；
- 标记高风险边界：公共 API、数据库、协议、并发、持久化。

### `post-edit`

- 运行最窄相关测试；
- 检查语法、类型和静态分析；
- 记录本次修改是否混入新功能；
- 提示重构步幅是否过大，但不依赖行数作唯一判断。

### `final-review`

- 验证可观察行为声明；
- 汇总坏味道是否减少；
- 检查是否产生新的浅模块、中间人或过度抽象；
- 运行更广测试；
- 输出仍未解决的设计债务。

原则：仍然只有一个 coordinator，不为新 Pack 创建第二套 Hooks。

## 5. Validators

### 5.1 新增 `smell_audit.py`

第一期只实现低误报或容易解释的候选检测：

- 重复代码候选；
- 过长参数列表；
- 重复 switch / 条件分派；
- 可疑传递方法 / Middle Man；
- 霰弹式修改线索（基于 git diff 的同类改动分散度）；
- 数据泥团候选；
- 基本类型偏执候选；
- 全局可变数据候选。

输出必须写 `candidate`，不直接写 `violation`。

### 5.2 新增 `refactoring_guard.py`

负责过程性检查：

- 当前重构是否声明行为不变量；
- 是否记录了验证命令；
- 修改是否触及高风险边界；
- 是否需要人工确认；
- 是否把功能变化和重构混在同一阶段。

不尝试证明行为完全等价。

## 6. Evaluation design

新增至少以下 eval：

1. Extract Function 能提升意图表达的安全例；
2. 过度 Extract Function 产生浅函数和传递层的反例；
3. Introduce Special Case 消除重复 null 条件的安全例；
4. Special Case 对象只是隐藏错误状态的反例；
5. YAGNI 避免提前抽象的安全例；
6. 缺乏最小抽象导致霰弹式修改的反例；
7. 有可靠测试时的小步重构；
8. 无测试遗留代码中先建立 characterization tests；
9. 性能热点需要保留针对性优化；
10. 非热点代码不应为了猜测性能牺牲可读性。

每个 eval 包含：

- 原代码；
- 请求；
- 必须保留的行为；
- 允许的安全方案；
- 应拒绝的过度方案；
- 预期触发的规则 ID。

## 7. Conflict decisions

以下冲突会改变代理行为，需要项目所有者决策。

### D1. Extract Function vs Deep Modules

**A — Semantic extraction（推荐）**

只有当新函数能够命名意图、隐藏细节或形成稳定边界时才提炼。函数长度只是线索。允许较长但内聚、顺序清晰的函数。

**B — Aggressive small functions**

倾向把长函数持续拆小，即使部分函数只用于提升局部可读性。优点是局部意图明显，风险是浅函数、跳转和传递层增多。

### D2. Introduce Special Case vs Define Special Cases Away

**A — Normalize first**

优先通过边界归一化、默认值或更好的模型消除特殊情况；仅在无法消除时使用 Special Case 对象。

**B — Special Case first**

只要多个位置重复判断同一特殊状态，就优先引入显式 Special Case / Null Object。

**C — Semantic split（推荐）**

- 无效输入、协议差异和基础设施异常：在边界归一化或消除；
- 稳定且有独立业务语义的状态：允许建模为 Special Case；
- 仅为隐藏错误而创建的 Special Case：拒绝。

### D3. Design Twice vs Evolutionary Refactoring / YAGNI

**A — Hybrid（推荐）**

非平凡修改先比较两个设计，但只实现满足当前需求的最小完整方案；长期方案只记录，不为假设未来提前建设。

**B — Strategic upfront design**

更倾向在编码前建立长期抽象，即使当前需求尚未全部验证。

**C — Evolutionary only**

只做满足当前需求的最小变化，通过后续坏味道和重构逐步形成架构。

### D4. Testing as a refactoring gate

**A — Risk-based gate（推荐）**

- 中高风险重构必须先有相关测试或 characterization tests；
- 低风险、工具可证明的重命名/移动允许没有新增测试；
- 无法建立测试时必须声明风险并缩小步幅。

**B — Strict gate**

没有可运行的自动测试就不允许执行任何重构。

**C — Advisory only**

测试只是建议，代理可基于静态分析和人工检查继续重构。

### D5. Refactoring vs performance

**A — Measure-first with explicit constraints（推荐）**

默认优先可读性并通过 profiling 定位热点；如果项目已有明确延迟、内存、吞吐或实时约束，则设计阶段必须保留这些约束。

**B — Readability first**

先重构到最清晰，再单独做性能优化，即使可能短暂退化。

**C — Performance-aware by default**

任何重构都必须同时评估潜在性能影响，代价是流程更重。

### D6. Data Class as a smell

**A — Context-sensitive（推荐）**

领域模型中的贫血对象是线索；DTO、序列化结构、消息和不可变值记录不自动视为坏味道。

**B — Strong object-oriented rule**

只含数据和访问器的类默认应把相关行为移入对象。

### D7. Middle Man vs Hide Delegate / Information Hiding

**A — Boundary-value test（推荐）**

如果委托层隐藏易变依赖图、权限、缓存、协议或所有权，则保留；如果只是逐个转发相同接口，则标记为浅层或 Middle Man。

**B — Prefer direct access**

优先移除中间人，减少调用跳转。

**C — Prefer encapsulation**

即使当前只做转发，也优先保留委托边界，以减少调用者对对象图的了解。

### D8. Mixed feature and refactoring changes

**A — Separate validation phases（推荐）**

允许在一个任务中完成，但必须先完成并验证结构调整，再添加行为，最终报告两个阶段。

**B — Strict separation**

重构和功能修改必须拆成两个独立任务或提交。

**C — Flexible**

只要最终测试通过，可以在同一修改阶段交错进行。

## 8. Recommended decision set

建议默认选择：

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

这套组合把两本书的优势结合起来：

- 用 Ousterhout 约束抽象质量和复杂性落点；
- 用 Fowler 提供小步、安全、可测试的演进方式；
- 不把“函数越小越好”或“看到坏味道就重构”变成机械规则；
- 不允许 YAGNI 成为放任糟糕边界的借口；
- 不允许长期设计成为提前建设假设能力的借口。

## 9. Implementation phases

### Phase 1 — Knowledge model

- 新增 Pack JSON；
- 更新聚合器支持 `extends`、`conflicts` 和 `counterbalance`；
- 建立与 SDP 规则的去重映射。

### Phase 2 — Workflow

- 新增 `safe-refactoring` Skill；
- 更新 `design-review` 与 `complexity-audit`；
- 更新 Hook coordinator 的 `mode` 协议。

### Phase 3 — Validators

- 新增 smell audit；
- 新增 refactoring guard；
- 所有静态发现保持 candidate 语义。

### Phase 4 — Evals and release

- 增加冲突案例；
- 验证不会过度提炼函数或强制对象化 DTO；
- 构建并校验 Codex/Claude 两个发布目录；
- 版本升级到 `0.2.0`。
