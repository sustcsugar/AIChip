# 节点 H1：Floorplan

> 阶段 H 物理设计（可选扩展） | 归属 agent：signoff-agent | 对应 skill：`.opencode/skills/node-H1-floorplan/`

## 1. 节点目的与范围

物理设计布局规划：把综合后 netlist 映射到芯片版图几何。目标是在给定的 die/package 尺寸内确定 die 尺寸、IO/PG 布局、宏单元（macro）摆放、模块分区与布线资源分配，使**面积 / 利用率达标**，并为后续 Place & Route 提供可行的物理框架。

范围：
- 确定 die 尺寸、aspect ratio（长宽比）、core/IO/pad 边界与利用率目标。
- 放置 IO 与 power/ground ring、电源规划（PG mesh / strap 宽度）。
- 摆放硬宏（memory、模拟 IP、hard macro），设定软宏/标准单元区域（blockage 与 region）。
- 初步布线资源估算（congestion estimate）与模块布局优化。
- 建立本节点专用 QoR 报告（面积、利用率、congestion 热图）。

> 前置说明：H 阶段为可选扩展。本实验收敛标准止于 F5 时序收敛，仅在需要 tapeout 时才启用 H1。

## 2. 输入产物（前置条件）

- [ ] G3 基线冻结（release tag + 交付包，`state/state-tracker.md` 中 G3 = passed）
- [ ] 综合 netlist（DC/GENUS 输出，含 `.ddc` / `.vg`）+ 库设置（E2/E3）
- [ ] 签核 SDC 约束（F1 评审通过版）
- [ ] 物理库（LEF、PDK tech file、macro LEF/GDS）、std cell LEF + timing/delay 库
- [ ] IO/pad 库与封装/引脚图（die 尺寸约束、IO 总数、PG pin 分配）
- [ ] 功耗目标与 IR-drop 预算（F4 功耗报告，如做）
- [ ] 模块面积/数量级信息（B4 建模、E3 综合面积报告）

## 3. 执行步骤

### Plan
- 读取 die/package 约束（IO 数、封装引脚、die 尺寸上限）与 netlist 门数/宏数量。
- 设定初版目标：利用率目标（一般 50%~75%）、aspect ratio、PG 方案。
- 列出全部 hard macro 清单（尺寸、端口方向、PG 需求）。

### Execute
- 创建 floorplan：`floorplan -coreDensity <目标利用率> -dieSize <x><y>`（或按 macro 面积自动估算）。
- 摆 IO/pad：`placeIO`（根据封装引脚图定 IO 扇区）；生成 power ring 与 PG mesh。
- 摆 hard macro：手工/脚本摆放 memory 与模拟 IP（对齐 power grid、避免阻塞关键 IO），设置模块 region 与 blockage（`createBlockage` / `createGuide`）。
- 布电源网络：`addRing` + `addStripe`，设定 strap 宽度/间距满足 IR-drop 预算。
- 走线资源估算：`checkPlacement -density` / `reportCongestion`，生成 congestion 热图。
- 迭代：利用率超标或 congestion 红区 → 调 die 尺寸/宏摆放/区域分配后重跑。

### Measure
- 指标：core 利用率（%）、die 面积、macro 数/总面积、congestion 超阈值区域数、IR-drop 预估、预估 wirelength。
- 记录：每轮迭代的利用率与 congestion 变化曲线。

### Judge
- 对照第 6 节判据：利用率在目标区间、无不可解 congestion 红区、宏摆放合法（无重叠、无 DRC 冲突）。
- 不满足 → 调整 floorplan 重跑；满足 → 进入质量门（检查）。

## 4. 工具与命令

- 综合工具 GUI/脚本（DC/Genus）中执行：
  - `floorplan -coreDensity <util> -dieSize <w> <h>`（创建 core/io 区域）
  - `placeIO -ioFile <pad_file>`（IO 摆放）
  - `addRing -nets {VDD VSS} -width <w> -spacing <s>`（电源环）
  - `addStripe -nets {VDD VSS} -layer <M> -width <w> -spacing <s>`（PG 条带）
  - `createMacroPlacement` / 脚本放置 macro；`createBlockage` / `createGuide`（区域与阻塞）
  - `checkPlacement -density`（利用率检查）
  - `reportCongestion` / `report_area`（congestion 与面积报告）
- 面积估算复核：`report_area`（综合后）对照 `report_qor`（物理后）。
- 关键文件：`floorplan.tcl`、`macro_placement.tcl`、`power_grid.tcl`（可复现脚本），输出 `.def`/`.fp`。

## 5. 人机职责分配

| 任务 | 执行者 | 协同类型 | 干预点 |
|------|--------|---------|--------|
| 生成初版 floorplan（die/IO/PG/macro） | AI agent | AI 全自动 | — |
| 摆放 hard macro、设置 region/blockage | AI agent | AI 产出人审 | 人工确认宏摆放与关键 IO 布局 |
| congestion 与利用率迭代优化 | AI agent | AI 全自动 | — |
| 生成 QoR 报告与迭代记录 | AI agent | AI 全自动 | — |
| die 尺寸/封装约束的澄清与批准 | 人类 | 人机协同 | 按需（涉及封装/成本决策） |
| 面积与利用率达标确认签字 | 人类 | 人工 | 必须签字 |

## 6. 收敛判据（DoD）

**DoD：面积 / 利用率达标。**

可操作判定方法：
- 利用率：core 利用率处于目标区间（如 50%~75%），且 `checkPlacement -density` 无越界违规。
- 面积：die 面积 ≤ 封装/die 尺寸上限；估算面积（宏+std cell+布道资源）与 die 面积匹配。
- 宏合法性：所有 hard macro 无重叠、无越界、对齐 PG grid，端口方向满足布线可达性。
- congestion：`reportCongestion` 无红色拥塞区（或可接受且后续 P&R 可解）。
- PG/IR：电源 ring/stripe 宽度与间距满足预估电流与 IR-drop 预算（≤ 5% VDD 目标）。
- 可复现：floorplan 由 `.tcl` 脚本从零可重建，QoR 数字可重复。
- 判定结论：全部满足 → 面积/利用率达标；否则迭代重做。

## 7. 质量门与签字

- 质量门类型：检查（人工核对 QoR 报告，确认面积/利用率达标）。
- 未签字不得进入 H2 Place & Route。

## 8. 输出产物

- `work/soc/pnr/H1_floorplan/`：`floorplan.tcl`、`macro_placement.tcl`、`power_grid.tcl`
- `work/soc/pnr/H1_floorplan/floorplan.def`（或 `.fp`）
- `work/soc/pnr/H1_floorplan/QoR_floorplan.rpt`（面积/利用率/congestion/IR-drop 预估）
- 宏摆放示意图与 congestion 热图（png/pdf）
- 更新 `state/state-tracker.md`：H1 = passed（orchestrator 写入）

## 9. 对应 skill 与 agent

- skill：`node-H1-floorplan`
- agent：signoff-agent
- 详章索引：`doc/SOP.md`