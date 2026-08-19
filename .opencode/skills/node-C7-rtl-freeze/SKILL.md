---
name: node-C7-rtl-freeze
description: 系统级集成完成，RTL feature complete 并打 freeze tag。当需要执行或判断节点 C7（RTL冻结）的状态、产出或收敛时使用。
---

# Node C7: RTL冻结

> 本 skill 承载节点 C7 的执行工作流。节点完整定义（含人机职责）见 `doc/阶段C-微架构与RTL/C7-RTL冻结/C7-RTL冻结.md`。
> 归属 agent：rtl-agent。执行前必须先读 `state/tracker.md` 确认节点处于 in_progress 且前置输入完整。

## 1. 目的

系统级集成完成，RTL feature complete 并打 freeze tag

## 2. 输入产物（前置条件）

- [ ] 前序节点产物已存在且 passed（见 tracker）
- [ ] 本节点输入清单齐备

## 3. 执行步骤

### Plan
1. 读取输入产物，确认理解目标
2. 若存在模板（`templates/`），先复制模板为工作文件
3. **读取本节点的规范/标准文档**（如 `doc/阶段C-微架构与RTL/C3-RTL编码/C3-编码规范.md`，若详章指明存在），作为执行约束

### Execute
3. 按输入产物执行本节点工作
4. 产物写入 `work/`（或 `doc/`）对应路径

### Measure
5. 收集度量数据（数量/报告/指标）

### Judge
6. 对照收敛判据逐项检查
7. 不满足 → 定位差距，修正后重测；满足 → 进入质量门

## 4. 工具与命令

- 由节点详章定义（开源工具 / 商用工具脚本 / 校验脚本）
- 校验脚本：`python scripts/check_tracker.py --node C7`

## 5. 收敛判据（DoD）

feature complete，freeze 基线建立

## 6. 质量门与签字

- 质量门类型：人工签字
- 达标后置 `waiting_review`，等待人工签字后方可 `passed`

## 7. 输出产物

- 本节点的产物路径（由节点详章定义）

## 8. 人机职责

| 角色 | 职责 | 干预点 |
|------|------|--------|
| AI agent | 执行主体工作 + 度量 + 判据自检 | 自动执行 |
| 人类 | 质量门签字 / 关键决策 / 异常裁定 | 必须人工确认 |

## 9. 参考

- 节点详章：`doc/阶段C-微架构与RTL/C7-RTL冻结/C7-RTL冻结.md`
- 速查表：`doc/辅助文档/90-收敛判据速查表.md`
- 职责矩阵：`doc/辅助文档/91-人机职责分配矩阵.md`