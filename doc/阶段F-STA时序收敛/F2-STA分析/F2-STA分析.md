# 节点 F2：STA 分析

> 阶段 F STA 时序收敛 | 归属 agent：signoff-agent | 对应 skill：`.opencode/skills/node-f2-sta/`

## 1. 节点目的与范围

对门级网表执行多模式、多角（MMMC）静态时序分析，覆盖全部功能模式与 PVT/RC 角，列出**全部**时序违例（setup/hold/min pulse width 等），作为违例修复（F3）的输入。STA 是时序收敛环（Loop 2）的核心分析节点。

范围：构建 scenario/analysis view（模式 × 角），运行 `update_timing`，按角/模式输出 WNS/TNS/违例路径。不包含违例修复（F3）与签核结论（F5）。

## 2. 输入产物（前置条件）

- [ ] 前序节点产物（由 `state/tracker.md` 确认 passed）：F1 约束签核评审（人工签字）、E5 LEC、E4 DRC
- [ ] E3 门级网表 `top_netlist.v`；E2 全部 PVT/RC 角库
- [ ] F1 签核版 SDC `work/soc/sta/constraints/soc_top.sdc`
- [ ] 模式定义：功能模式（function）、扫描/测试模式（scan/shift/capture）、复位模式（若独立）
- [ ] 角定义表：PVT 角（SS/TT/FF）与 RC 角（rc_worst/rc_best 等）组合

## 3. 执行步骤

### Plan
- 明确模式与角的完整笛卡尔集：如 function×{ss_rc_worst, ff_rc_best, tt}、scan×{ss_rc_worst, ff_rc_best}
- 明确产物清单：各 scenario 的 WNS/TNS 汇总、全量违例路径清单、最差路径报告
- 确认 STA 库、SDC、netlist 版本快照（可追溯）

### Execute
- 读入网表：`read_verilog top_netlist.v`；`link_design`
- 建立模式与角：`create_mode`/`set_mode`（Primetime）、`create_process_corner`/`set_process_corner`、`create_rc_corner`；`create_scenario`/`create_analysis_view` 组合
- 施加约束：`read_sdc soc_top.sdc`（按模式应用对应约束；扫描模式用 `set_case_analysis` 关闭功能时钟/声明 shift/capture）
- 寄生/延迟模型：门级采用库内 `wire_load_model` 或 `set_wire_load_mode`（无布局线网）；如 E3 已出 SDF 可用 `read_parasitics`
- 更新时序：`update_timing`（或 `update_timing -full`）
- 按 scenario 输出：
  - `report_checks -path_delay max`（setup）与 `-path_delay min`（hold），`-slack_lesser_than 0 -path_type full -format {instance cell net timing_point slack}`
  - `report_checks -path_delay max -slack_lesser_than 0` 汇总每 scenario 的 WNS（最差 slack）与违例路径数
  - `report_clock_timing -type skew|transition` 检查时钟质量
  - `report_constraints`/`report_timing -delay_type max -max_paths 1` 复核
- TNS 计算：对全部负 slack 路径求和（按 endpooint 或路径口径，脚本统一口径后记录口径定义）

### Measure
- 收集：每个 scenario 的 WNS、TNS、违例路径数、violation 类型分布（setup/hold/min_pulse）；全角最小 WNS（全局最差）

### Judge
- 违例已全量列出：覆盖全部 scenario、全部路径类型（max/min）
- 全局 WNS/TNS 已计算并记录口径（此节点不要求 ≥ 0，仅要求「列全、量准」）
- 违例清单为空则直接满足收敛；非空 → 移交 F3
- 不满足（漏角/漏模式/报告缺失）→ 修正重跑；满足 → 进入质量门（检查）

## 4. 工具与命令

- 工具：Synopsys PrimeTime（签核 STA）；由人机协同脚本驱动
- 常用定义（多模式多角）：
  - `create_mode function -sdc_files soc_top.func.sdc`；`create_mode scan -sdc_files soc_top.scan.sdc`
  - `create_process_corner ss_corner`、`ff_corner`；`create_rc_corner rc_worst/rc_best`
  - `create_scenario func_ss` → `set_analysis_view -setup func_ss` / `-hold func_ss`（setup/hold 可各用一角，hold 用 FF/rc_best，setup 用 SS/rc_worst）
  - 或 MMMC 文件方式：`set_mcmm_options` + `create_analysis_view`
- 分析命令：
  - `update_timing`；`report_analysis_view`
  - `report_checks -path_delay max -slack_lesser_than 0 -path_type full -max_paths <n> -format {instance cell net timing_point slack}`
  - `report_checks -path_delay min -slack_lesser_than 0 -path_type full`
  - `report_clock_timing -type skew -significant_digits 3`、`report_clock_transition`
  - `report_checks -path_delay max -slack_lesser_than 0 -group <clock>`（按时钟组分组违例）
- 脚本与汇总：`scripts/run_sta.tcl`（遍历 scenario）、`scripts/parse_sta.py`（解析 → 汇总 WNS/TNS/违例表）

> WNS/TNS 定义（口径统一）：
> **WNS**（Worst Negative Slack）= 全部检查路径（max/min）中 slack 的最小值，即最差违例的 slack 值；
> **TNS**（Total Negative Slack）= 所有负 slack 路径 slack 的总和（Σ slack，slack<0）。本流程按**逐 endpoint 口径**统计 TNS（同一 endpoint 只计入最差一条），并写入汇总表注明口径，保证 F3/F5 跨节点可比。

## 5. 人机职责分配

| 任务 | 执行者 | 协同类型 | 干预点 |
|------|--------|---------|--------|
| 构建 scenario/角/模式矩阵与 STA 脚本 | AI agent | AI 全自动 | — |
| 运行 Primetime 全角 STA | AI agent | 人机协同 | 商用 EDA 依赖人类许可环境：多角 run 资源大，license/队列需人类协调 |
| scenario 矩阵完整性核对（角×模式无遗漏） | AI agent + 人类 | 人机协同 | 人类按签核规范确认角集合符合工艺要求 |
| WNS/TNS 口径确认与违例分类 | 人类 | 人工 | 必须确认：口径不统一则 F3/F5 无法判定 |
| 违例根因初判（约束假象 vs 真实路径） | AI agent + 人类 | 人机协同 | 人类裁定是否需回 F1 修约束 |
| 度量与判据自检 | AI agent | AI 全自动 | — |
| 质量门检查签字 | 人类 | 人工 | 必须签字 |

## 6. 收敛判据（DoD）

**违例已全量列出**，判定方法：
- 全部 scenario（模式 × 角）均已执行 `update_timing` 并输出报告，矩阵无遗漏
- 每个 scenario 的 WNS/TNS/违例路径数已汇总，setup/hold/min_pulse 全覆盖
- 全局最差 WNS/TNS 已确认并记录口径
- 违例清单可直接作为 F3 修复输入（含路径、slack、路径类型、所在时钟组）

## 7. 质量门与签字

- 质量门类型：检查（check）
- 检查重点：scenario 矩阵完整、违例全量列出、WNS/TNS 口径记录
- 未签字不得进入 F3

## 8. 输出产物

- `work/soc/sta/reports/sta_summary.csv` — 全 scenario WNS/TNS/违例数汇总
- `work/soc/sta/reports/sta_violations_max.rpt` / `sta_violations_min.rpt` — 全量违例路径
- `work/soc/sta/reports/sta_worst_path.rpt` — 各角最差路径
- `work/soc/sta/reports/sta_clock_quality.rpt` — 时钟 skew/transition 报告
- `work/soc/sta/reports/sta_log.txt` — 各 scenario 运行日志
- `work/soc/sta/reports/sta_scope.md` — scenario 矩阵与 WNS/TNS 口径定义记录

## 9. 对应 skill 与 agent

- skill：`node-f2-sta`
- agent：signoff-agent
- 详章索引：`doc/SOP.md`