---
name: governance-retro
description: 节点治理回顾：每个节点收敛达标后、质量门前，对治理层/agent/skill 三层做审核，形成节点级回顾-评审-更新反馈回路。由 orchestrator 在每个节点 convergence-judge 判定 converged 后、置 waiting_review 前执行。
---

# Governance Retro — 节点治理回顾

> 唯一执行者：orchestrator。目标：保证治理层正确性/纯洁性/专业性，加速临时资产沉淀为固定资产。

## 触发时机

- 每个节点 convergence-judge 判定 `converged` 之后、置 `waiting_review` 之前（质量门硬前置）
- 任何时点 agent/用户报告治理层异常时（临时触发，流程相同）

## 输入

- 本节点领域 agent 的报告，**必须附 friction log**（执行中的卡点/口径冲突/缺失资产/临时变通；无则显式声明"无"）
- 机器三查结果（见下）

## 流程

### 1. 机器三查（先跑，客观基线）

1. **资产边界扫描**（ADR 边界口径）：`.opencode/skills/` 与 `.opencode/agent/` 中不得引用项目态编号（ADR-NNN 内容、OI/RMP 具体条目）与项目本体文档内容；路径机制引用（如"写入 state-decisions.md"）合规
2. **骨架漂移检查**：`python AIFlow/scripts/workflow_audit.py`（重点 W10；已登记 KNOWN_CUSTOM 的定制除外）
3. **结构校验**：tracker/roadmap/文档登记校验脚本全绿

### 2. 三层审核（对照 friction log 逐项定性）

| 层 | 审核问题 | 常见缺陷模式 |
|----|---------|-------------|
| 治理层 | SOP/节点详章/辅助文档是否暴露缺陷？ | DoD 口径不清、编号未登记、步骤断点/重复、术语漂移 |
| agent | agent 定义是否漂移/缺失纪律？ | 术语过时、路径失效、职责与实跑不符 |
| skill | skill 是否有缺口/违规/漂移？ | 边界违规、手工定制未登记、模板缺失、执行卡点无指引 |

### 3. 逐项处置（三出口）

- **当场修**（单点、低影响）：orchestrator 直接修复并在本回顾记录留痕；连续 ADR 留痕成本高时按主题合并登记
- **登记 ADR**（决策/授权/异常类）：写入项目 `state-decisions.md`
- **登记 RMP**（流程改进/优化方向类，超出本节点修复范围）：`idea` 状态，进入质量门 RMP 走查流程

### 4. 资产沉淀评估（临时→固定）

对本节点产生的临时资产逐项判定：

| 判定 | 动作 |
|------|------|
| 通用可复用（校验脚本/模板/规范片段） | 内化进对应 skill 的 `assets/` 或 `_shared/templates/`，原位置改引用 |
| 项目专属 | 留在项目工作区（docs/ 等），仅在治理文档登记 |
| 一次性 | 丢弃，friction log 留痕 |

### 5. 回顾记录

- 回顾结论写入本节点评审纪要的"治理回顾"节（三层结论 + 处置清单 + friction log 摘要）
- 无发现时显式记录"三层审核无发现"（留痕即审计证据）

## 升级规则（需人类裁定）

涉及以下变更时，orchestrator 不得自行执行，报告人类确认：

- 骨架模板修改（触发 46 节点 skill 再生成）
- SOP 流程模型/节点增删
- agent 权限/职责边界变更

## 输出格式

```
节点 <ID> 治理回顾: clean | fixed | escalated
  机器三查: 边界=<PASS/FAIL+位置> 漂移=<...> 结构=<...>
  治理层: <发现/无> → <处置>
  agent: <发现/无> → <处置>
  skill: <发现/无> → <处置>
  资产沉淀: <内化清单/无>
  friction log: <N 条，摘要>
```
