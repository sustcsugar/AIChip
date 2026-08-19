# 节点 H2：Place & Route

> 阶段 H 物理设计（可选扩展） | 归属 agent：signoff-agent | 对应 skill：`.opencode/skills/node-H2-place-route/`

## 1. 节点目的与范围

在 H1 floorplan 基础上完成标准单元**布局（Placement）与布线（Routing）**，产生带真实物理走线的版图，并满足时序、拥塞、DRC 的初版收敛，最终达到 **DRC clean**。

范围：
- 标准单元布局（含时序驱动放置、优化 cell 尺寸）。
- 时钟规划前处理与布线（pre-CTS 布线留出时钟资源）。
- 信号布线 + 修 DRC（short/spacing/antenna）。
- 布线后时序评估（pre-CTS STA 快照，供 H3 时钟树前后对比）。
- 本阶段不建立最终时钟树（归 H3），但需给出可布通的初版。

> 前置说明：H 阶段为可选扩展。仅启用 tapeout 时执行。

## 2. 输入产物（前置条件）

- [ ] H1 floorplan 通过（`.def` + QoR 报告，`state/tracker.md` 中 H1 = passed）
- [ ] 综合 netlist + SDC 约束（F1 评审版）
- [ ] 物理库：std cell LEF/LEF5、macro LEF、route layer 定义（tech lef）、NDM/tech file
- [ ] PG 网络定义（H1 `power_grid.tcl` 输出）
- [ ] 时序库（lib）与寄生参数文件（TLU+ / ITF，用于布线后提取）
- [ ] 拥塞/密度目标与 DRC 规则文件（design rule deck）

## 3. 执行步骤

### Plan
- 读入 H1 floorplan + netlist + SDC，确认工艺/库版本一致。
- 设定布局密度、routing 层数与优先级、DRC 修错迭代预算。

### Execute
- 布局：`place_opt`（时序驱动放置 + 优化），`optimizeDesign`（cell sizing / buffer）。
- 密度与拥塞检查：`checkPlacement -density` / `reportCongestion`，超标则 `refinePlace` 或回到 H1 调整。
- 时钟预布：在 netlist 中标记时钟网络，设置 non-default rules（NDR）预留时钟布线空间。
- 布线：`routeDesign -global -detailed`（全局布线 → 详细布线）。
- DRC 修复：`ecoRoute` / `repairDesign` 循环修 short、spacing、antenna、min area 等违例，直至 clean。
- 布线后时序快照：提取寄生（SPEF）→ 跑 pre-CTS STA，记录 WNS/TNS 基线供 H3 对比。

### Measure
- 指标：密度（%）、congestion 红区数、总 wirelength、via 数、DRC 违例数（按类型：short/spacing/min-area/antenna）、布线完成率（routing completion %）、pre-CTS WNS/TNS。
- 记录：每轮 DRC 修复的违例数量变化。

### Judge
- 对照第 6 节判据：布线完成率 100%、DRC 违例清零（clean）、密度可接受。
- 不满足 → 修复重跑（ecoRoute / 回放置 / 回 H1）；满足 → 进入质量门（检查）。

## 4. 工具与命令

- P&R 工具（Innovus / IC Compiler II）脚本：
  - `place_opt -congestion -effort high`（布局优化）
  - `checkPlacement -density` / `reportCongestion -hotSpot`（密度/拥塞）
  - `routeDesign -globalRoute -detailedRoute`（布线）
  - `ecoRoute -fix_drc true` / `repairDesign`（DRC 修复）
  - `report_design_rules` / `report_drc`（DRC 违例清单）
  - `extractRC`（寄生提取）→ `report_analysis_coverage` / `report_timing`（布线后时序快照）
- 验收脚本：`verify_drc`（工具内 DRC）→ 输出 `drc_violations.rpt`，按类型归类统计。

## 5. 人机职责分配

| 任务 | 执行者 | 协同类型 | 干预点 |
|------|--------|---------|--------|
| 布局、拥塞优化与布线执行 | AI agent | AI 全自动 | — |
| DRC 修复迭代（ecoRoute/repair） | AI agent | AI 全自动 | — |
| 布线后 SPEF 提取与 pre-CTS STA 快照 | AI agent | AI 全自动 | — |
| DRC 违例分类分析与残留违例处理建议 | AI agent | AI 产出人审 | 人工裁定残留违例是否放行/打回 |
| 布局密度/层数等关键参数决策 | 人类 | 人机协同 | 按需 |
| DRC clean 确认签字 | 人类 | 人工 | 必须签字 |

## 6. 收敛判据（DoD）

**DoD：DRC clean。**

可操作判定方法：
- 布线完成率：routing completion = 100%（无未布通的 net）。
- DRC 违例：`report_drc` 全类型违例数为 0（short/spacing/min-area/antenna 等），即 clean。
- 密度：布局密度在目标区间内，无不可解 congestion。
- 时序基线：记录 pre-CTS WNS/TNS（不要求达标，供 H3 对比；若已达标说明留了裕量）。
- 可复现：P&R 全部由脚本驱动，从 H1 `.def` + netlist 可重建，DRC 结果可重复。
- 判定结论：全部满足 → DRC clean 成立；否则继续修复迭代。

## 7. 质量门与签字

- 质量门类型：检查（人工核对 DRC 报告与 completion，确认 DRC clean）。
- 未签字不得进入 H3 CTS。

## 8. 输出产物

- `work/soc/pnr/H2_place_route/`：`place_route.tcl`、`place.def`、`route.def`
- `work/soc/pnr/H2_place_route/route_drc.rpt`（DRC 违例清单，clean）
- `work/soc/pnr/H2_place_route/congestion.rpt`、`utilization.rpt`
- `work/soc/pnr/H2_place_route/prects_sta.rpt`（SPEF + WNS/TNS 基线）
- 更新 `state/tracker.md`：H2 = passed（orchestrator 写入）

## 9. 对应 skill 与 agent

- skill：`node-H2-place-route`
- agent：signoff-agent
- 详章索引：`doc/SOP.md`