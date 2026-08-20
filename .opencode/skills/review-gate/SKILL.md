---
name: review-gate
description: 质量门评审通用流程：评审清单、签字机制、评审纪要。当任何 SOP 节点进入 waiting_review 状态、需要组织评审或处理评审签字时使用。
---

# Review Gate — 质量门评审通用流程

> 应用于所有 `gate: 评审` / `gate: 人工签字` 的节点。评审结果必须记录到 `state/state-decisions.md`。

## 触发时机

- 节点执行完成、收敛判据自检通过，orchestrator 将节点置为 `waiting_review`
- 人工要求对某节点/产物评审

## 流程

1. **准备评审材料**
   - 节点产出物清单（路径 + 摘要）
   - 收敛判据自检结果（对照 `doc/辅助文档/90-收敛判据速查表.md`）
   - 已知风险与遗留问题清单

2. **执行评审清单**
   - 对照模板 `templates/review-checklist.md` 逐项检查
   - 至少覆盖：完整性 / 一致性 / 可追溯性 / 异常处理 / 遗留问题

3. **产出评审结论**
   - 通过（pass）→ 人工签字，节点置 `passed`
   - 有条件通过（conditionally pass）→ 列出必须修复项，节点置 `iterating`，修复后复审
   - 不通过（fail）→ 节点置 `iterating`，返回执行步骤修复

4. **记录**
   - 评审结论写入 `state/state-decisions.md`
   - 更新 `state/state-tracker.md` 对应节点状态
   - **规范回写**：评审意见若涉及规范/格式/命名（非仅本节点产物），必须同步回写节点详章、`templates/`、`node-template`（如需）并重新生成 skill，确保 SOP 定义层与实际执行一致

## 签字规则

- 人工签字是唯一放行方式，AI 不得自行将节点置为 `passed`
- 签字记录格式：`[节点ID] 通过/有条件通过/不通过 — 签字人/日期/意见`