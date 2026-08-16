# Policy Evals

这些夹具验证冲突决策不会退化为机械规则：

- 长函数不会仅因行数被标记为必须提炼；
- `OrderDTO` 不会被静态规则自动定罪为 Data Class；
- 无行为的领域对象只产生低置信度 `candidate`；
- 长参数列表会产生可调查线索；
- 委托检测保持 `candidate`，由边界价值问题决定是否保留；
- 风险测试门禁和 mixed-change 阶段顺序可被脚本验证。

运行：

```bash
python3 scripts/test_plugin.py
```
