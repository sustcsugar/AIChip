# 节点 C6：模块级 smoke

> 阶段 C | 归属 agent：rtl-agent | 对应 skill：`.opencode/skills/node-C6-block-smoke/`

## 1. 节点目的与范围

**目的**：对每个自研模块运行**基础冒烟仿真**（smoke test），验证基本功能通路可用：复位可正确释放、时钟正常、寄存器可读写、握手可完成、状态机可推进、无 X 传播阻塞仿真、无超时死锁。smoke 只验证"通路通了"，不做覆盖率收敛（属 D 阶段）。

**范围**：
- 每个自研模块一个模块级 TB，位于 `verif/block/<mod>/`。
- **DUT = 单模块**；TB 内**不实例化任何其他设计模块**，对外部依赖（总线、存储器、上下游模块）用行为模型 / VIP / 驱动 stub 替代。
- 行为模型来源：`work/soc/verif/common/`（共享行为模型/VIP）；复用 IP 可挂其 `work/ip/<ip>/model/` 行为模型。
- 系统级集成验证（只实例化 soc_top）不在本节点，属 C7 系统 smoke 与 D 阶段。

## 2. 输入产物（前置条件）

- [ ] C3 RTL 编码（passed）+ C4 lint（passed）+ C5 CDC（passed）
- [ ] C1 微架构规格（passed）：期望行为（状态机转移、握手、Regmap 语义）
- [ ] C2 模块接口契约（passed）：端口与时序（TB 驱动/采样依据）
- [ ] 行为模型/VIP 可用：`work/soc/verif/common/`（或 IP `model/`）
- [ ] 仿真工具链就绪：Verilator + cocotb（或 Verilator + C++ TB）

## 3. 执行步骤

### Plan
- 每模块在 `verif/block/<mod>/` 建立 TB 骨架：DUT（单模块）+ 行为模型 stub + 时钟/复位生成 + 测试用例列表。
- 定义 smoke 用例集（每模块 5–10 条）：
  1. 复位序列：断言/释放后模块进入期望复位态，无 X 泄漏。
  2. 寄存器通路：按 C1 Regmap 逐寄存器写-读回读（含复位值、W1C/RO 属性抽查）。
  3. 基本握手：一次完整 AXI/APB 或流式握手事务完成，数据正确。
  4. 状态机关键路径：驱动一次完整生命周期转移（如 idle→busy→done）。
  5. 中断路径（如适用）：置位条件触发中断信号，确认机制有效。
  6. 超时保护：每条用例设 timeout，捕获死锁。

### Execute
- 编写/生成 smoke TB（cocotb：Python 驱动 + 时钟/复位协程；或 Verilator C++ TB）。
- 驱动序列：复位释放 → 等待稳定 → 逐条执行 smoke 用例 → 断言检查（值比对 + 握手完成 + 状态断言）。
- 监控：X 传播（在采样点检查 X/Z）、timeout、断言失败。
- 记录每模块 smoke 结果与日志。

### Measure
- 每模块：用例数、通过数、失败数、仿真时间、timeout 数。
- 覆盖的功能条目（以 C1 为基准）：Regmap 覆盖寄存器数、握手类型数、状态机路径数。
- X 传播 / 断言失败计数。

### Judge
- 全部模块 smoke 用例通过，无 timeout、无 X 阻塞、无断言失败。
- 失败 → 定位（RTL bug 回 C3；期望行为错误回 C1/C2 澄清）→ 重跑直至收敛。
- 满足 → C 阶段模块级验证完成，进入 C7 系统级集成与冻结。

## 4. 工具与命令

- 仿真栈：**Verilator + cocotb**（首选）或 Verilator + C++ testbench。
- TB 目录：`work/soc/verif/block/<mod>/`
  - `tb_<mod>.py`（cocotb 用例）/ `tb_<mod>.cpp`
  - `Makefile`（封装编译+运行）
  - `run_tb.sh`（生成 filelist、调 verilator、跑 cocotb）
- 运行示例：
  ```bash
  # 单模块 smoke（cocotb）
  cd work/soc/verif/block/<mod> && make
  # 或显式
  python -m cocotb --hdl-verilator ... # 依 Makefile 封装
  ```
- 依赖：行为模型/VIP 从 `work/soc/verif/common/` 引用（路径在 TB 内 `--include`）。
- 约束：block TB 的 DUT 只含 `<mod>` 顶层，**不得实例化其他设计模块**（违者 C6 判拒）。
- 报告：`work/soc/verif/block/<mod>/results/smoke_report.md`。

## 5. 人机职责分配

| 任务 | 执行者 | 协同类型 | 干预点 |
|------|--------|---------|--------|
| 每模块 TB 骨架与 smoke 用例集生成 | AI agent | AI 全自动 | — |
| 时钟/复位/激励/断言与 X/timeout 监控编写 | AI agent | AI 全自动 | — |
| 运行仿真、收集结果、失败定位与修复迭代 | AI agent | AI 全自动 | — |
| 期望行为歧义裁定（RTL 对 vs 规格错） | 人类 | 人机协同 | 仿真与规格冲突时按需裁定 |
| 行为模型/VIP 缺失时的补建方案 | 人类 + AI | 人机协同 | 模型复用决策需人确认 |
| 检查结论放行 | 人类 | 人工 | 必须签字 |

## 6. 收敛判据（DoD）

**DoD：模块级仿真通过。**

可操作判定方法：
1. 每个模块 smoke 用例 **100% 通过**（通过数 / 总数 = 1），无 timeout、无 X 阻塞、无断言失败。
2. 每模块至少覆盖：复位释放、Regmap 写读回读（含复位值抽查）、一次完整握手、状态机一条关键转移路径。
3. TB 合规：DUT 为单模块，`verif/block/<mod>/` 下未实例化其他设计模块（代码审查确认）。
4. smoke 报告归档，失败项修复闭环（每条失败有定位与解决记录）。

## 7. 质量门与签字

- 质量门类型：**检查**（仿真通过 + orchestrator 判据核验 + TB 合规审查）
- 检查未通过不得进入 C7；各模块可滚动通过，C7 要求全部模块通过。

## 8. 输出产物

- `work/soc/verif/block/<mod>/`（每模块 smoke TB：源码 + Makefile）
- `work/soc/verif/block/<mod>/results/smoke_report.md`（用例结果、日志摘要、失败闭环）
- `work/soc/docs/reports/c6-block-summary.md`（全模块 smoke 汇总表）
- `state/tracker.md` 更新（C6 → passed）

## 9. 对应 skill 与 agent

- skill：`node-C6-block-smoke`
- agent：rtl-agent
- 详章索引：`doc/SOP.md`