# 节点 H4：Signoff-STA

> 阶段 H 物理设计（可选扩展） | 归属 agent：signoff-agent | 对应 skill：`.opencode/skills/node-H4-signoff-sta/`

## 1. 节点目的与范围

物理实现后的**签核级时序分析**：在 CTS 之后的完整版图上，用签核级寄生提取与多模式多角（MMMC）分析，完成 setup/hold 签核时序，目标是 **WNS/TNS ≥ 0**。与 F 阶段综合后 STA 对应，H4 是基于真实物理版图（含时钟树与走线寄生）的最终时序确认。

范围：
- 从版图抽取签核级寄生（SPEF/RC，含 signal + clock net）。
- 建立 MMMC 签核环境（多 PVT 角、多模式、片上变异 OCV/AOCV）。
- 全角 setup/hold 分析 + 违例报告。
- 违例修复（可回 H2/H3 或增量 ECO）直至全角达标。
- 输出签核时序报告，作为 H5 物理验证的时序旁证。

> 前置说明：H 阶段为可选扩展。仅启用 tapeout 时执行。

## 2. 输入产物（前置条件）

- [ ] H3 CTS 通过（cts.def + CTS DRC clean，`state/state-tracker.md` 中 H3 = passed）
- [ ] 签核 SDC 约束（F1 评审版，含 OCV/setup/hold 建模设置）
- [ ] 签核 STA 工具（Primetime / Tempus）与 signoff 库（lib + 角文件，含 cell/nets 的 OCV derating）
- [ ] 寄生提取配置（TLU+ / ITF / NDM，签核级 extraction mode）
- [ ] H2/H3 的 WNS/TNS 基线（对比用）
- [ ] G2 收敛报告中 F5 的签核结论（对照口径）

## 3. 执行步骤

### Plan
- 确定签核角集合：setup 用 worst-case（slow/slow、low temp 等），hold 用 best-case（fast/fast、high temp 等），含功能 vs 测试（scan）模式。
- 配置 MMMC 场景：`create_delays` / scenario 定义（PLL off/on、模式组合）。
- 设定 OCV 方法（AOCV tables / derate）与 clock uncertainty 口径。

### Execute
- 寄生提取：`extractRC -coupling -clock`（含耦合电容与时钟网寄生）→ 导出 SPEF。
- 读入版图 + netlist + SDC + SPEF 到签核工具，运行全场景分析。
- 报告：`report_timing -late`（setup，全角全场景）、`report_timing -hold`、`report_analysis_coverage`、WNS/TNS。
- 违例分析：按场景/角归类 setup/hold 违例路径，定位根因（时钟 skew、负载、路径级数）。
- 修复：违例 → 走 ECO（尺寸调整/buffer/延迟单元/回 H2-H3 局部改动）后重新提取重跑；无违例则直接确认。

### Measure
- 指标：全角全场景 WNS / TNS（setup 与 hold）、违例路径数（按角/场景/时序类型）、analysis coverage（%）。
- 记录：修复迭代前后 WNS/TNS 变化、每轮 ECO 改动量。

### Judge
- 对照第 6 节判据：所有场景 WNS/TNS ≥ 0，无隐藏违例。
- 不满足 → 修复重提取重跑（可回 H2/H3）；满足 → 进入质量门（检查）。

## 4. 工具与命令

- 寄生提取（P&R 工具内）：`extractRC -quality <signoff> -coupling -clock` → `write_parasitics -format spef`
- 签核 STA（Primetime/Tempus）：
  - `read_db <mmmc_scenario>` / `set_analysis_view`（场景）
  - `report_timing -late -max_paths <N>`（setup）
  - `report_timing -hold -max_paths <N>`（hold）
  - `report_analysis_coverage`（覆盖率）
  - `report_worst_4_paths` / `get_timing_paths` 导出 WNS/TNS（脚本化统计）
- 汇总脚本：跨角解析 `report_timing` 输出，生成 `signoff_sta_summary.rpt`（每角 WNS/TNS/违例数）。

## 5. 人机职责分配

| 任务 | 执行者 | 协同类型 | 干预点 |
|------|--------|---------|--------|
| 签核角/场景配置（MMMC） | AI agent | AI 全自动 | — |
| 寄生提取与全场景 STA 运行 | AI agent | AI 全自动 | — |
| 违例路径根因分析与修复建议 | AI agent | AI 产出人审 | 人工确认根因与修复方案后执行 |
| ECO 修复与重跑（含回 H2/H3 触发） | AI agent | 人机协同 | 需人工批准跨节点回退 |
| WNS/TNS 汇总报告生成 | AI agent | AI 全自动 | — |
| 时序收敛（WNS/TNS ≥ 0）确认签字 | 人类 | 人工 | 必须签字 |

## 6. 收敛判据（DoD）

**DoD：WNS/TNS ≥ 0。**

可操作判定方法：
- 全场景覆盖：所有签核场景（setup 角 + hold 角 + 各功能/测试模式）均被分析，analysis coverage = 100%。
- setup：所有场景 WNS ≥ 0、TNS ≥ 0（严格签核口径）；如有例外须经人工签核豁免并记录。
- hold：所有场景无 hold 违例（WNS/TNS ≥ 0）。
- 寄生真实：SPEF 来自签核级提取（含 coupling + clock），非估算模型。
- 一致性：本节点 WNS/TNS 口径与 F5 一致（同 SDC、同 OCV 设置），无"签核口径漂移"。
- 可复现：给定版图 + 脚本可重复生成同一结果。
- 判定结论：全部满足 → WNS/TNS ≥ 0 成立；否则继续修复或走豁免流程。

## 7. 质量门与签字

- 质量门类型：检查（人工核对全角时序汇总，确认 WNS/TNS ≥ 0）。
- 未签字不得进入 H5 物理验证（物理验证需在时序签核后做最终版图）。

## 8. 输出产物

- `work/soc/pnr/H4_signoff_sta/`：`sta_signoff.tcl`、MMMC 场景文件
- `work/soc/pnr/H4_signoff_sta/signoff_spf.spef`（签核级寄生）
- `work/soc/pnr/H4_signoff_sta/signoff_sta_summary.rpt`（全角 WNS/TNS/违例路径）
- `work/soc/pnr/H4_signoff_sta/violation_detail.rpt`（违例根因，如有）
- 更新 `state/state-tracker.md`：H4 = passed（orchestrator 写入）

## 9. 对应 skill 与 agent

- skill：`node-H4-signoff-sta`
- agent：signoff-agent
- 详章索引：`doc/SOP.md`