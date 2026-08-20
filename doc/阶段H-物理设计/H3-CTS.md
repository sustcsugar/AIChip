# 节点 H3：CTS

> 阶段 H 物理设计（可选扩展） | 归属 agent：signoff-agent | 对应 skill：`.opencode/skills/node-H3-cts/`

## 1. 节点目的与范围

时钟树综合（Clock Tree Synthesis）：在 H2 布线结果上建立真实时钟网络（时钟树/网格），把时钟 skew、latency 控制在约束内，确保时序与时钟 DRC 均达标，最终达到 **CTS DRC clean**。

范围：
- 时钟源识别与树形规划（含 useful skew、双沿/多时钟、门控时钟）。
- 时钟树综合 + 时钟网络布线（专用 clock layer 与 NDR）。
- 时钟 DRC 检查（skew/latency/transition/capacitance/duty）。
- CTS 后 hold 修复（`postCTS` 时序优化）与时序评估。
- 本节点目标是**时钟级 clean**，最终 signoff STA 在 H4 完成。

> 前置说明：H 阶段为可选扩展。仅启用 tapeout 时执行。

## 2. 输入产物（前置条件）

- [ ] H2 Place & Route 通过（route.def + DRC clean，`state/state-tracker.md` 中 H2 = passed）
- [ ] SDC 时钟约束（create_clock / create_generated_clock、clock uncertainty、latency）
- [ ] CTS 配置文件：clock 层选择、NDR（双倍宽/间距）、max skew/latency/transition 目标
- [ ] CTS 工具（Innovus cts / ICC2 cts）与库（含 clock cell）
- [ ] H2 pre-CTS STA 基线（WNS/TNS）

## 3. 执行步骤

### Plan
- 从 SDC 提取全部时钟定义，确认与 F1 约束评审一致（数量、频率、generated 关系）。
- 确定 clock tree 策略：skew/latency 目标、useful skew 许可、门控/双沿处理。
- 规划 NDR 与 clock 布线层（避开拥挤信号层）。

### Execute
- 时钟树综合：`clockDesignSpec`（定义时钟/叶结点）→ `clockDesign`（综合时钟树）。
- 时钟网络布线：`routeDesign -clockNets`（按 NDR 布线），时钟网络 DRC 修复。
- 时序修复：`postCTS hold 修复`（插 buffer/延迟单元）、`optDesign -postCTS` 修 setup。
- 时钟 DRC 检查：`report_clock_qor` / `report_clock_timing`（skew/latency/transition/insertion delay）。
- 与 H2 pre-CTS 基线对比，验证 CTS 未破坏 setup（或差异可解释）。

### Measure
- 指标：max skew、max latency、clock transition、useful skew 利用量、时钟 buffer 数、clock net DRC 违例数、postCTS WNS/TNS、hold slack。
- 记录：CTS 前后时序与时钟指标对比表。

### Judge
- 对照第 6 节判据：skew/latency/transition 均在目标内、clock DRC clean、hold 修复后无违规。
- 不满足 → 调 CTS 配置（树结构/NDR/目标）重跑；满足 → 进入质量门（检查）。

## 4. 工具与命令

- CTS 工具脚本：
  - `specifyClockTree` / `createClockTreeSpec`（时钟树规格）
  - `clockDesign` / `ccopt_design`（CTS 综合）
  - `routeDesign -clockNets`（时钟布线）
  - `report_clock_qor` / `report_clock_timing`（时钟 QoR）
  - `report_clock_tree`（树结构/叶节点统计）
  - `optDesign -postCTS -hold`（hold 修复）
  - `report_timing -late -hold`（postCTS 时序）
- 验收脚本：时钟 DRC 按类型（skew/latency/transition/cap/duty）统计违例数。

## 5. 人机职责分配

| 任务 | 执行者 | 协同类型 | 干预点 |
|------|--------|---------|--------|
| 时钟定义解析与树策略拟定 | AI agent | AI 全自动 | — |
| CTS 综合与时钟布线执行 | AI agent | AI 全自动 | — |
| postCTS hold/setup 修复 | AI agent | AI 全自动 | — |
| 时钟 QoR 与 DRC 报告生成 | AI agent | AI 全自动 | — |
| 异常时钟结构（门控/多源/clock gating 失效）分析 | AI agent | AI 产出人审 | 人工判定是否回改约束/RTL |
| 时钟策略与 CTS DRC clean 确认签字 | 人类 | 人工 | 必须签字 |

## 6. 收敛判据（DoD）

**DoD：CTS DRC clean。**

可操作判定方法：
- 时钟 DRC：skew ≤ 目标、latency/insertion delay ≤ 目标、transition ≤ 目标、cap/duty 无违例，违例数为 0。
- 时钟布线 DRC：clock net 无 short/spacing/antenna 违例。
- 时序：postCTS 无 hold 违例；setup 相比 H2 pre-CTS 基线无退化（或退化可解释且 H4 可收敛）。
- 树完整性：所有时钟与叶节点被正确接入（无悬空、无未定义时钟），generated 时钟关系与 SDC 一致。
- 可复现：CTS 由脚本从 H2 结果重建，QoR 可重复。
- 判定结论：全部满足 → CTS DRC clean 成立；否则调策略重跑。

## 7. 质量门与签字

- 质量门类型：检查（人工核对时钟 QoR 与 DRC 报告，确认 CTS DRC clean）。
- 未签字不得进入 H4 Signoff STA。

## 8. 输出产物

- `work/soc/pnr/H3_cts/`：`cts.tcl`、`cts_spec`、`cts.def`
- `work/soc/pnr/H3_cts/clock_qor.rpt`（skew/latency/transition）
- `work/soc/pnr/H3_cts/cts_drc.rpt`（时钟 DRC，clean）
- `work/soc/pnr/H3_cts/postcts_sta.rpt`（WNS/TNS + hold 检查）
- 更新 `state/state-tracker.md`：H3 = passed（orchestrator 写入）

## 9. 对应 skill 与 agent

- skill：`node-H3-cts`
- agent：signoff-agent
- 详章索引：`doc/SOP.md`