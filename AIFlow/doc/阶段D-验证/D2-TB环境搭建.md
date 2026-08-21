# 节点 D2：TB环境搭建

> 阶段 D 验证 | 归属 agent：verify-agent | 对应 skill：`.opencode/skills/node-D2-tb-setup/`

## 1. 节点目的与范围

搭建 UVM/cocotb 验证环境与共享组件。本节点将 D1 vplan 的环境规划落实为可编译、可运行的仿真骨架，作为 D3–D6 所有用例的载体。

范围（两级环境 + 共享层 + 参考模型/Scoreboard）：
- **模块级**：`verif/block/<mod>/`，DUT = 单个模块，不得实例化其他设计模块。
- **系统级**：`verif/sys/`，DUT = `soc_top`，挂 AXI VIP + memory model。
- **共享组件**：`verif/common/`，包括 VIP（AXI 等）、行为模型、memory model、公共 sequence/utility 库。
- **参考模型集成（B7 golden）**：把 B7 冻结的系统级/模块级参考模型接入两级环境，构建 **scoreboard 自动比对通路**——同一激励同时驱动 DUT 与参考模型，输出自动比对。
- 覆盖工具链接入：Verilator 代码覆盖率、cocotb 功能覆盖率开关在环境中预置。

## 2. 输入产物（前置条件）

- [ ] D1 vplan passed（含两级环境规划、复用资产清单）
- [ ] B7 参考模型冻结 passed（golden 模型 + 版本，供 scoreboard 集成）
- [ ] C2 模块接口契约 passed（端口、时序、握手，用于 TB 顶层连线）
- [ ] C6 模块级 smoke passed（`AIFlow/state/state-tracker.md` 确认）
- [ ] C7 RTL 冻结 passed（feature complete，RTL 版本锁定）
- [ ] `ip_manifest.json`（mode 配置，决定 sys 级挂 model 还是 rtl）
- [ ] 工具链可用：verilator / cocotb / iverilog（UVM 场景）/ python3 / make

## 3. 执行步骤

### Plan
1. 读取 D1 vplan、接口契约，确认两级 DUT 边界与端口清单。
2. 规划目录结构（`verif/common`、`verif/block/<mod>`、`verif/sys`）与文件清单。
3. 盘点可复用组件：IP 自带 VIP / model 优先复用，缺失的在 `verif/common` 新建。

### Execute
4. 搭建 `verif/common/`：AXI VIP、memory model、行为模型、sequence 库、时钟/复位公共组件。
5. 搭建模块级环境 `verif/block/<mod>/`：TB 顶层、DUT 实例化、时钟复位生成、cocotb 入口 / UVM env、`tests/` 目录、Makefile 与编译文件清单。
6. **寄存器模型（ADR-026）**：以 `docs/regmap/*.rdl` 为源，`peakrdl-uvm` 生成 UVM RAL 模型（预测镜像/后门访问），挂入模块级 env；cocotb 场景用 `peakrdl-python` 生成的 Python 寄存器访问层替代。
7. 搭建系统级环境 `verif/sys/`：`soc_top` 实例化 + AXI VIP + memory model 挂载，按 manifest mode（model / rtl）选择挂载对象。
7. **参考模型 + Scoreboard 集成**：
   - 模块级：实例化 `model/block/<mod>/` 的 golden 模型，与 DUT 同激励同输入，scoreboard 比对模块输出。
   - 系统级：实例化 `model/sys/` 的系统级模型，scoreboard 比对系统输出（含容差策略）。
   - 封装参考模型为仿真可用形态（SV 行为模型或 DPI-C），比对结果统一记录（mismatch 计数 + 日志）。
8. 编写编译/运行脚本（Makefile + runner），打开覆盖率收集开关。
9. 编写 smoke 用例（每个环境至少一个）跑通编译与运行闭环，**含 scoreboard 冒烟比对通过**。

### Measure
10. 记录度量：编译时间、各环境 smoke 用例通过数、覆盖率收集文件是否生成、scoreboard 冒烟比对 mismatch 数（应为 0）。
11. 运行 `python AIFlow/scripts/check_tracker.py --node D2`。

### Judge
12. 对照收敛判据逐项检查（见第 6 节）。
13. 不满足 → 修正编译错误 / 环境缺陷后重测；满足 → 进入质量门。

## 4. 工具与命令

- **Verilator 编译**（cocotb 场景）：
  - `make -C verif/block/<mod>`（内部 `SIM=verilator`）
  - 手动：`verilator --binary -j 0 --timing --trace --assert --cc --top-module <dut> tb_top.sv`
- **cocotb 运行**：`SIM=verilator make` ；单用例：`make TESTCASE=test_xxx`；波形：`WAVES=1 make`（生成 fst/vcd，gtkwave 查看）。
- **UVM 场景（iverilog/verilator）**：
  - 编译：`iverilog -g2012 -o sim.out tb_top.sv <uvm-1.2 源码> <dut>/*.sv`
  - 运行：`vvp sim.out +UVM_TESTNAME=xxx_test`
- **覆盖率开关（D6 预置）**：
  - `verilator --coverage --coverage-line --coverage-toggle --coverage-branch --coverage-cond ...`
  - 运行后生成 `coverage.dat`；`verilator_coverage --help` 确认工具可用。
- **目录约定**：
  - `verif/common/`：AXI VIP、memory model、行为模型
  - `verif/block/<mod>/`：模块级 TB + `tests/`
  - `verif/sys/`：系统级 TB（`soc_top` + VIP + memory model）
  - 参考模型（B7 golden，只读引用）：`model/sys/`、`model/block/<mod>/`、`ip/<ip>/model/`
- 状态校验：`python AIFlow/scripts/check_tracker.py --node D2`。

## 5. 人机职责分配

| 任务 | 执行者 | 协同类型 | 干预点 |
|------|--------|---------|--------|
| 目录脚手架、编译/运行脚本编写 | AI agent | AI 全自动 | — |
| common 共享组件（VIP/行为模型/memory model）开发 | AI agent | AI 全自动 | — |
| 两级 TB 顶层连线与 DUT 实例化 | AI agent | AI 全自动 | 连线错误会导致 D3+ 连锁失败 |
| 工具链安装 / 环境变量配置 | 人类 | 人工 | 工具缺失时必须人工介入 |
| smoke 用例与编译结果判定 | AI agent | AI 全自动 | — |
| 环境结构合理性检查 | 人类 | 人机协同 | 按需，检查 common/block/sys 边界 |
| 质量门检查签字 | 人类 | 人工 | 必须签字 |

## 6. 收敛判据（DoD）

**环境编译运行通过。**

可操作判定方法：
- 两级环境（block + sys）编译均无 error（warning 记录不阻断）。
- 每个环境的 smoke 用例运行通过：cocotb 输出 `Passed` 或 `0 errors`，进程 exit code 0。
- **scoreboard 冒烟比对通过：参考模型 vs RTL 比对 mismatch = 0（block 与 sys 各一例）。**
- 覆盖率收集开关生效：运行后 `coverage.dat` / 功能覆盖 report 文件非空。
- `verif/common/` 共享组件被 block 与 sys 至少各一处引用。
- `python AIFlow/scripts/check_tracker.py --node D2` 通过。

## 7. 质量门与签字

- 质量门类型：检查。
- 未签字不得进入 D3。

## 8. 输出产物

- `verif/common/`：VIP、memory model、行为模型、公共 sequence/utility。
- `verif/block/<mod>/`：模块级 TB（tb_top、Makefile、文件清单、`tests/`）。
- `verif/sys/`：系统级 TB（`soc_top` 挂载 AXI VIP + memory model）。
- 编译日志、smoke 运行日志、smoke 通过报告。
- `ip/<mod>/tb/` 下的 IP 自带 TB（如存在，纳入 block 级体系）。

## 9. 对应 skill 与 agent

- skill：`node-D2-tb-setup`
- agent：verify-agent
- 详章索引：`AIFlow/doc/SOP.md`
