# nodes.json 字段规范（节点注册表）

> `AIFlow/scripts/nodes.json` 是节点注册的唯一事实源，供 scaffold_skills.py（生成）、check_tracker.py（依赖校验）、workflow_audit.py（骨架审查）共用。
> 新增/修改节点必须符合本规范；workflow_audit W1 会校验字段齐全与取值合法。

## 节点字段（9 项，全部必填）

| 字段 | 类型 | 约束 | 示例 |
|------|------|------|------|
| `id` | string | 格式 `[A-H]\d+`，全局唯一，不随阶段重置 | `"A1"` |
| `slug` | string | 小写连字符，唯一 | `"req-scope"` |
| `name` | string | 节点中文名 | `"需求与场景定义"` |
| `phase` | string | 阶段字母 `A-H` | `"A"` |
| `agent` | string | 必须对应 `.opencode/agent/<name>.md` | `"spec-agent"` |
| `doc` | string | 详章相对 `AIFlow/doc/` 的路径 | `"阶段A-需求与规格/A1-需求与场景定义.md"` |
| `description` | string | 一句话职责描述（生成 skill 的目的节） | `"分析产品需求，定义使用场景与用例清单"` |
| `dod` | string | 收敛判据（DoD） | `"场景清单无未决 open issue"` |
| `gate` | string | 取值：`评审` / `检查` / `人工签字` | `"评审"` |

## 派生规则

- skill 目录名：`node-<id>-<slug>`（如 `node-A1-req-scope`）
- skill 文件：`.opencode/skills/node-<id>-<slug>/SKILL.md`
- 索引一致性：SOP.md（W7）、速查表 90（W15）、职责矩阵 91（W16）必须与 nodes.json 一一对应

## 校验

```bash
python AIFlow/scripts/workflow_audit.py   # W1 注册表完整性 + W2/W3/W5 详章/skill/agent 存在性
python AIFlow/scripts/check_tracker.py    # 节点前后置依赖
```
