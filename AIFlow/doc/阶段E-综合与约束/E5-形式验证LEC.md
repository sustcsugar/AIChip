# 节点 E5：形式验证 LEC

> 阶段 E 综合与约束 | 归属 agent：syn-agent | 对应 skill：`.opencode/skills/node-e5-lec/`

## 1. 节点目的与范围

以形式等价性检查（LEC）验证门级网表与冻结 RTL 逻辑等价，确认综合没有改变功能。LEC 通过是「综合结果可信任」的形式化证据，是进入门级仿真（E6）与 STA（F）的先决条件。

范围：以冻结 RTL 为 golden，E3 网表为 revised，运行 LEC 匹配与验证，分析所有 not-equivalent / unmapped 点。不包含网表功能仿真（E6）。

## 2. 输入产物（前置条件）

- [ ] 前序节点产物（由 `AIFlow/state/state-tracker.md` 确认 passed）：E3 逻辑综合、E4 综合后 DRC（均检查通过）
- [ ] C7 冻结 RTL（golden，与综合用同版本，ip-discipline 只读消费）
- [ ] E3 门级网表 `top_netlist.v`（revised）
- [ ] E3 生成的 SVF（`top_svf.svf`，描述综合变换，帮助 LEC 匹配）
- [ ] E2 库环境（LEC 需读库做门级功能映射）

## 3. 执行步骤

### Plan
- 确认 golden/revised 版本一致（RTL 冻结 tag、网表为同次综合产物）
- 明确忽略规则清单：仅允许合理的恒定信号/未用输出（有书面依据），不允许功能级豁免
- 明确产物清单：LEC 报告、未匹配/未等价点清单

### Execute
- 建立 LEC 环境：读入 RTL 为 golden 设计，读入网表为 implemented 设计，读入所需库
- 施加名称匹配与自动 setup：读入 SVF（Formality `read_svf`/Conformal 等价 setup），必要时配置重命名规则（`add renaming`、`add suffix`）
- 设置 top：`set_top` / `set design top <golden> <impl>`
- 匹配：`match`（Formality）/ `add mapped points`（Conformal）确认逻辑点映射关系
- 验证：`verify`（Formality）/ `compare`（Conformal）
- 对 not-equivalent / unmapped 点逐一分析：报出路径/信号/原因（综合 bug、约束影响、SVF 缺失、setup 问题）
- 收敛检查：未匹配点可加 `setup`/`add don't verify` 前必须记录依据并人工复核

### Measure
- 收集：等价点总数、匹配点数量、not-equivalent 数量、unmapped（unmatched）数量、验证耗时

### Judge
- RTL↔netlist 完全等价：not-equivalent = 0
- unmapped 点 = 0 或全部为「已复核、可豁免」且有书面依据（如无扇出的常量定义）
- 若 not-equivalent > 0：不得放行，回 E3 重新综合或回 C 阶段修正 RTL，然后重跑 LEC
- 不满足 → 迭代修复；满足 → 进入质量门（检查）

## 4. 工具与命令

- 工具：Synopsys Formality 或 Cadence Conformal（LEC）；商用工具由人机协同脚本驱动
- Formality（`soc/syn/AIFlow/scripts/fm.tcl`）：
  - `set_app_var search_path <rtl_dir> <lib_dir>`；`set_app_var link_library <lib>`
  - `read_verilog -container r -lib work -golden <rtl_file_list>`（golden）
  - `read_verilog -container i -lib work -implement <netlist>`（implemented）
  - `set_top <top>`；`set_verification_top`
  - `read_svf top_svf.svf`（若生成）
  - `match`；`verify`
  - `report_verification_results`、`report_unmatched_points -summary`、`report_failing_points -all`
  - `save_session`（留档复现）
- Conformal（LEC，等价步骤）：
  - `set design top <rtl_top>`；`read design -verilog -golden <rtl>`；`read design -verilog -golden <netlist>`（实现库经 `read library`）
  - `add renaming`（名称不匹配时）；`add mapped points`；`add don't verify`（仅豁免项）
  - `compare`；`report compare data -class nonequivalent -summary`；`analyze datapath`（数据通路不等价时）
- 复验辅助：`AIFlow/scripts/check_lec.py` 解析报告 → 提取 not-equivalent/unmapped 计数与点位

## 5. 人机职责分配

| 任务 | 执行者 | 协同类型 | 干预点 |
|------|--------|---------|--------|
| 编写 LEC 流程脚本（fm.tcl / lec dofile） | AI agent | AI 全自动 | — |
| 运行 LEC 并解析验证结果 | AI agent | 人机协同 | 商用 EDA 依赖人类许可环境：需人类确认 Formality/Conformal license、启动工具 run |
| not-equivalent 点根因分析 | AI agent + 人类 | 人机协同 | 人类裁定根因：综合设置、SVF 缺失、约束影响或 RTL 结构 |
| 豁免/忽略规则批准（don't verify、unmapped） | 人类 | 人工 | 必须确认：任何豁免都可能掩盖功能差异 |
| 度量与判据自检 | AI agent | AI 全自动 | — |
| 质量门检查签字 | 人类 | 人工 | 必须签字 |

## 6. 收敛判据（DoD）

**RTL↔netlist 等价**，判定方法：
- `verify`/`compare` 结论为「verification succeeded / equivalent」，not-equivalent 点 = 0
- unmapped/unmatched 点 = 0，或全部为已复核豁免项（清单 + 依据文档化）
- LEC 报告留存（可复现：save_session / 报告文件归档）

## 7. 质量门与签字

- 质量门类型：检查（check）
- 检查重点：not-equivalent = 0、unmapped 清零或全部豁免有据、报告归档
- 未签字不得进入 E6 门级仿真

## 8. 输出产物

- `soc/syn/reports/lec_report.log` — 验证结果原始报告
- `soc/syn/reports/lec_summary.md` — LEC 结论（等价状态、匹配统计、豁免清单）
- `soc/syn/reports/lec_unmatched.txt` / `lec_failing.txt` — 未匹配/未等价点位（如有，应为空或已豁免）
- `soc/syn/reports/lec_session` — Formality session（可复现性留档）

## 9. 对应 skill 与 agent

- skill：`node-e5-lec`
- agent：syn-agent
- 详章索引：`AIFlow/doc/SOP.md`