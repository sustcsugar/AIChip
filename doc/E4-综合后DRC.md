# 节点 E4：综合后 DRC

> 阶段 E 综合与约束 | 归属 agent：syn-agent | 对应 skill：`.opencode/skills/node-e4-synth-drc/`

## 1. 节点目的与范围

对综合后门级网表执行时序 DRC 检查：max_transition、max_capacitance、max_fanout、min_pulse_width 等设计规则违例，确认综合产物满足工艺 DRC 要求。DRC clean 是网表质量基线，避免违例被带进 F 阶段 STA 与物理设计。

范围：对 E3 网表施加 E1 约束，运行 DC/GENUS 的 DRC 报告与 timing DRC 报告，逐类逐条清点违例。不包含 LEC 等价性（E5）、门级功能仿真（E6）。

## 2. 输入产物（前置条件）

- [ ] 前序节点产物（由 `state/tracker.md` 确认 passed）：E3 逻辑综合（检查通过）、E1 约束开发、E2 库环境
- [ ] E3 门级网表 `work/soc/syn/output/top_netlist.v` 与综合数据库
- [ ] E1 `top.sdc`（DRC 目标值来源）
- [ ] E2 库环境的 DRC 缺省值信息

## 3. 执行步骤

### Plan
- 明确 DRC 检查维度：transition、capacitance、fanout、min pulse width，以及 max area（如启用）
- 明确违例分类口径：全局 DRC vs 时钟网络 DRC（时钟树综合前时钟上可容差策略需记录）
- 明确产物清单：DRC 报告、违例逐条清单

### Execute
- 在综合工具或独立 DRC 流程中对网表重新 link，施加 `top.sdc`
- 运行设计规则报告：`report_design_rules`（DC）/ `report_design_rules`（GENUS），或 `report_constraint -all_violators` 的 DRC 部分
- 运行时序路径 DRC 抽查：`report_timing -delay_type max -max_paths <n>` 确认长路径末端 transition/cap 不超限
- 对每条违例提取：路径/网络名、数值、超限类型、涉及单元
- 对时钟网络违例单独归类（时钟树尚未综合，需标注为已知且物理阶段处理项）
- 比对库缺省 DRC 值与 SDC `set_max_*` 目标，区分「约束过紧」与「真实工艺违例」

### Measure
- 收集：各类违例计数（transition/cap/fanout/min_pulse_width）、最差超限量、涉及网络与单元数量、时钟网络违例占比

### Judge
- 全部门级网络 DRC clean（违例数 = 0）
- 时钟网络违例若存在：必须记录为「已知项，由物理设计 CTS 处理」，且不影响门级功能与 LEC
- 不满足 → 分类处理：约束过紧则回 E1 校正；库目标矛盾回 E2 核查；结构问题回 E3 重综合或回退 C 阶段；满足 → 进入质量门（检查）

## 4. 工具与命令

- 工具：DC（Design Compiler）、GENUS，或独立 DRC 复核；商用工具由人机协同脚本驱动
- 核心命令：
  - DC：`current_design <top>`；`link`；`read_sdc top.sdc`；`report_design_rules -verbose`；`report_constraint -all_violators`
  - GENUS：`read_db top.genus.db`；`read_sdc top.sdc`；`report_design_rules`（过渡/电容/扇出类）；`report_constraints -all_violators -max_transition -max_capacitance -max_fanout`
- 逐条提取：`get_nets -filter "max_transition*"` 类属性过滤，或解析报告生成违例表
- 交叉核对库缺省：`get_lib_defaults`（DC）获取库内默认 max_transition/max_capacitance/max_fanout
- 自定义脚本：`scripts/parse_drc.py` 解析报告 → 生成结构化违例清单 `drc_violations.csv`

## 5. 人机职责分配

| 任务 | 执行者 | 协同类型 | 干预点 |
|------|--------|---------|--------|
| 准备 DRC 检查流程脚本 | AI agent | AI 全自动 | — |
| 运行 DRC 报告并解析违例清单 | AI agent | 人机协同 | 商用 EDA 依赖人类许可环境：工具 run 需人类确认 license/环境 |
| 违例分类（约束过紧/库目标矛盾/真实违例/时钟网络已知项） | AI agent + 人类 | 人机协同 | 人类裁定类别归属与处理去向 |
| 时钟网络违例的容差裁定（CTS 前已知项登记） | 人类 | 人工 | 必须确认：确认该项不会影响门级功能/LEC 基线 |
| 度量与判据自检 | AI agent | AI 全自动 | — |
| 质量门检查签字 | 人类 | 人工 | 必须签字 |

## 6. 收敛判据（DoD）

**综合 DRC clean**，判定方法：
- max_transition / max_capacitance / max_fanout / min_pulse_width 违例计数 = 0（数据网络）
- 若存在违例，则每条均已完成分类：约束过紧 → 回 E1；库目标矛盾 → 回 E2；结构问题 → 回 E3/C；时钟网络项 → 登记为 CTS 前已知项且有书面依据
- `drc_violations.csv` 违例清单为空或全部归类完结

## 7. 质量门与签字

- 质量门类型：检查（check）
- 检查重点：违例全量列清、分类正确、时钟网络已知项有依据
- 未签字不得进入 E5

## 8. 输出产物

- `work/soc/syn/reports/drc_report.rpt` — `report_design_rules`/`report_constraint` DRC 原始报告
- `work/soc/syn/reports/drc_violations.csv` — 逐条违例清单（类型/网络/单元/数值/处理去向）
- `work/soc/syn/reports/drc_checklist.md` — DRC 检查结论（clean 状态或已知项登记）

## 9. 对应 skill 与 agent

- skill：`node-e4-synth-drc`
- agent：syn-agent
- 详章索引：`doc/SOP.md`