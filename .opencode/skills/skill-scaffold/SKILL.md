---
name: skill-scaffold
description: >-
  节点 skill 生成/再生成能力（orchestrator 专用）：以 nodes.json（节点注册）为数据源、
  assets/node-template/ 为骨架模板，批量生成/再生成 46 个 node-<ID>-<slug> skill。
  当需要新增节点、修改节点骨架、批量生成/再生成节点 skill、或因规范变更回写到节点 skill 时使用。
  配套工作流：改 nodes.json → 改骨架模板 → 运行 scripts/scaffold_skills.py → workflow-audit(W10) 验证。
---

# Skill Scaffold — 节点 skill 生成能力

> 适用者：orchestrator（唯一执行者）。能力随 skill 打包：模板 + 脚本 + 数据规范一站式。
> 生成机制：`nodes.json`（数据）× `assets/node-template/SKILL.md`（骨架）→ `scripts/scaffold_skills.py`（渲染）→ 46 个 `node-<ID>-<slug>/SKILL.md`。

## 何时使用

- 新增节点（改 `AIFlow/scripts/nodes.json` 注册表）
- 修改节点骨架（改 `assets/node-template/SKILL.md`，影响全部节点 skill）
- 规范/格式变更需要批量回写节点 skill（配合 review-gate"规范回写"纪律）
- 校验节点 skill 是否与骨架漂移（配合 workflow-audit W10）

## 输入

| 输入 | 路径 | 说明 |
|------|------|------|
| 节点注册表 | `AIFlow/scripts/nodes.json` | 46 节点数据（字段规范见 `references/nodes-schema.md`） |
| 骨架模板 | `assets/node-template/SKILL.md` | 含 `{{ID}}`/`{{NAME}}` 等占位符 |
| 节点详章模板 | `assets/node-template/node-doc-template.md` | 新建节点详章时使用 |
| 生成脚本 | `scripts/scaffold_skills.py` | 渲染 + 覆盖保护 |

## 工作流

1. 读取 `AIFlow/scripts/nodes.json`，确认节点注册数据（新增节点时按 `references/nodes-schema.md` 补全 9 字段）
2. 若修改骨架：编辑 `assets/node-template/SKILL.md`（占位符约定见 §模板约定）
3. 运行生成脚本：
   - 全部再生成：`python .opencode/skills/skill-scaffold/scripts/scaffold_skills.py --force`
   - 单节点：`python .opencode/skills/skill-scaffold/scripts/scaffold_skills.py --node C3`
   - 非交互（CI）：`python .opencode/skills/skill-scaffold/scripts/scaffold_skills.py --force --yes`
4. 运行 `python AIFlow/scripts/workflow_audit.py`，确认 W10（脚手架一致性）通过
5. 向 orchestrator 报告生成结果；若涉及节点注册变化，同步更新 SOP 节点索引与速查表 90/职责矩阵 91（workflow-audit W7/W15/W16 会校验）

## 模板约定（assets/node-template/SKILL.md）

- 占位符：`{{ID}}` `{{NAME}}` `{{SLUG}}` `{{DESCRIPTION}}` `{{DOC}}` `{{AGENT}}` `{{DOD}}` `{{GATE_TYPE}}`
- 公共步骤写进骨架（所有节点共享）；节点专属内容不写骨架（避免污染全部节点），按需在生成后手工定制
- 定制保护：`--force` 覆盖前比对，发现手工定制差异会告警，`--yes` 跳过确认但会在报告中列出

## 纪律

- **orchestrator 为唯一执行者**；其他 agent 不得直接运行生成脚本或批量修改 node skill
- 新增/删除节点：必须同步改 `nodes.json` + SOP 节点索引 + 速查表 90 + 职责矩阵 91，再生成并跑 workflow-audit 全量校验
- 非节点 skill（跨切面/专用）不走本生成流程，由 orchestrator 手工创建并登记 ADR
- 生成后若出现"未登记定制"告警（W10），先确认是否预期：预期则把节点加入 workflow_audit.py 的 KNOWN_CUSTOM 并在 ADR 留痕；非预期则回写骨架

## 参考

- 数据规范：`references/nodes-schema.md`
- 审计：`AIFlow/scripts/workflow_audit.py`（W10 脚手架一致性、W7/W15/W16 索引与覆盖）
- 决策依据：见项目 `AIFlow/state/state-decisions.md` 中的 skill 生命周期相关 ADR（资产内化 / 唯一执行者等，按项目实际记录查阅）
