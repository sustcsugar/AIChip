---
name: advance-rtl-coding-guidance
description: >-
  高级 RTL 编码规范指引：以 Synopsys DWC MIPI CSI-2 Host 商业 IP 代码为黄金基准，
  提取可综合 Verilog/SystemVerilog 的标准范式——端口声明、信号生成、组合逻辑、
  时序逻辑、case vs if 决策、两段式状态机、组合时序分离（var_reg <= next_var）、
  FIFO/buffer/CDC 可复用模块。当需要编写、评审、重构 RTL 代码，判断代码规范是否
  达标，或提取标准代码片段/可复用模块时使用。本 skill 是通用编码规范，适用于任何
  RTL 编写任务，不限于 MIPI 场景。也适用于评审他人 RTL 代码、代码 review 中给出
  规范整改意见、回答"这段代码写得对不对/好不好"的问题。
---

# Advance RTL Coding Guidance

以 Synopsys 商业 IP（DWC_mipi_csi2_host v1.52a，约 2.1 万行）为黄金基准的**可综合 RTL 编码规范**。
本 skill 把该 IP 中反复出现、被商用验证的编码范式固化为可直接套用的模板与决策规则。

> 来源分析报告：`references/source-analysis.md`（首次使用前可读一次建立背景）。

## 何时使用

**应该使用**：
- 编写新的可综合 RTL 模块（任何规模）
- 评审 / review 他人 RTL 代码，给规范整改意见
- 重构既有 RTL，消除 latch、拆分巨型 always、统一状态机写法
- 提取标准代码片段 / 可复用模块（FIFO、同步器、弹性缓冲、寄存器组）
- 回答"这段 RTL 写法是否符合商用规范"类问题

**不应该使用**：
- 编写 testbench / 验证环境（这是 verify 侧，用 UVM/cocotb 规范）
- 编写不可综合的行为模型（纯算法参考模型）
- 时序约束 SDC / 综合脚本

## IP 库（assets/rtl/）— 直接例化的可复用模块

本 skill 附带一个**完整可用的 RTL IP 库**，提取自 DWC IP 源码，版权头保留、模块名已简化为与文件名一致。
使用方式：**把所需文件复制到项目 RTL 目录，直接例化**，无需手工移植。

| 文件 | 模块名 | 用途 | 依赖 |
|------|--------|------|------|
| `assets/rtl/bcm07.v` | `bcm07` | 异步 FIFO 双时钟封装（push/pop 双域） | bcm05, bcm21 |
| `assets/rtl/bcm05.v` | `bcm05` | FIFO 控制核（格雷码指针/满空/计数） | bcm21 |
| `assets/rtl/bcm21.v` | `bcm21` | 多级同步器（2/3/4 级，自包含） | 无 |
| `assets/rtl/bcm00_maj.v` | `bcm00_maj` | 三模表决器 | 无 |
| `assets/rtl/mpb_elastbuf.v` | `mpb_elastbuf` | 弹性缓冲/移位型 FIFO（已去 include） | 无 |

**例化模板、参数表、依赖说明**见 `assets/rtl/README.md`。

最小复制集：
- 需要**异步 FIFO** → 复制 `bcm07.v` + `bcm05.v` + `bcm21.v`
- 只要**同步器** → 复制 `bcm21.v`
- 只要**浅 FIFO** → 复制 `mpb_elastbuf.v`

```verilog
// 示例：异步 FIFO 64×8 直接例化
bcm07 #(
  .DEPTH(64), .ADDR_WIDTH(6), .COUNT_WIDTH(7),
  .PUSH_AE_LVL(4), .PUSH_AF_LVL(4), .POP_AE_LVL(4), .POP_AF_LVL(4))
  u_async_fifo (
    .clk_push(wclk), .rst_push_n(wrst_n), .init_push_n(winit_n),
    .push_req_n(wreq_n), .push_full(push_full), .push_word_count(),
    .clk_pop(rclk), .rst_pop_n(rrst_n), .init_pop_n(rinit_n),
    .pop_req_n(rreq_n), .pop_empty(pop_empty), .pop_word_count(),
    .we_n(we_n), .wr_addr(wr_addr), .rd_addr(rd_addr));
```

> 纪律：保留版权头；模块名与文件名一致（内部 bcm05↔bcm21、bcm07↔bcm05 已同步）；`SYNTHESIS` 宏定义时仿真/断言分支自动剔除。详见 `assets/rtl/README.md`。

## 工作流

### Step 1 · 识别任务类型

先确定本次任务属于哪一类，决定加载哪个 reference：

| 任务类型 | 路由 |
|---------|------|
| 端口声明 / 参数化 / 信号命名 / assign 生成 | → `references/port-and-signals.md` |
| 组合逻辑 / case vs if 决策 / 防 latch | → `references/combinational-logic.md` |
| 时序逻辑 / 异步复位 / 组合时序分离范式 | → `references/sequential-logic.md` |
| 状态机（两段式 / 三段式 / FSM 级联） | → `references/fsm-pattern.md` |
| FIFO / 弹性缓冲 / CDC 同步器 / 寄存器组 | → `references/reusable-modules.md` |
| 写完后自检 / 评审他人代码 | → `references/checklist.md` |

一次任务通常需要 **2~3 个 reference**（例如：写一个带 FIFO 的状态机模块 = fsm + reusable + port）。

### Step 2 · 按需加载 reference

只读与当前任务相关的 reference 文件，不要全量加载。
每个 reference 内含：规范说明 + 黄金代码片段（取自 DWC IP）+ 反例。

### Step 3 · 编写代码

遵循 reference 中的范式模板编写。**核心铁律**（所有任务都适用，不必每次重读）：

1. **组合块先赋默认值**：`always @(*)` 内第一件事给所有输出赋默认（`nxtx = x;` 或 `rdata = 32'b0;`），再条件覆盖 → 杜绝 latch。
2. **组合/时序严格分离**：`var`（寄存器）只被一个时序块赋值；次态信号命名 `nxt<var>`，组合块只写 `nxt*`。
3. **两段式 FSM**：时序块只做 `state <= nxtstate`；组合块只算 `nxtstate`；所有状态覆盖 + `default` 防护。
4. **case 用于互斥多路译码，if 用于优先级/条件组合**（详见 combinational reference）。
5. **参数化 + localparam 推导**：宽度、阈值全部由参数/宏派生，禁止魔数。
6. **同步复位用 `if(!rst_n)`、异步复位用 `always @(posedge clk or negedge rst_n)`，块命名 `PROC_<name>`**。

### Step 4 · 自检

写完或评审完，用 `references/checklist.md` 逐项核对。
可用 `scripts/check_rtl_style.py` 做机械性检查（命名、always 块结构、宽度一致性）。

**脚本与清单的对应关系**（脚本自动覆盖的清单项）：

| 清单项 | 脚本检查 | 级别 |
|--------|---------|------|
| A1 块命名 | 每个 always 块是否 `begin : PROC_*` | warning |
| B1 组合块默认值 | 组合块 nxt* 有无保持/常量/case-default 默认赋值 | warning |
| B3 组合时序分离 | 组合块内对非 nxt 用 `<=`；nxt* 用 `<=` | blocker |
| B4 case 带 default | 每个 case 是否有 default 分支 | blocker |
| B6 敏感列表 `@(*)` | 组合块敏感列表是否含 `*` | warning |
| C4 时序块只用 `<=` | 时序块内是否出现阻塞赋值 `=` | warning |
| C5 同步复位顺序 | 是否出现 `else if(...reset...)` 分支（提示人工确认） | suggestion |
| F5 localparam 位宽 | localparam 是否带 `[W-1:0]` 位宽 | warning |

> 脚本是机械性辅助，无法覆盖语义检查（A2 nxt 配对为启发式、D 类状态机检查需人工/形式化工具确认）。脚本输出 `blocker` 时**必须**人工复核后修复。

### Step 5 · 输出

给出代码时，附一段简短说明：用到了哪些范式、为什么这样写（例如"组合块先默认值防 latch；case 因为是多路互斥译码"）。
评审他人代码时，按严重程度分级：`blocker`（latch/竞争/不可综合）→ `warning`（风格/可读性）→ `suggestion`（优化空间）。

## 黄金基准

本 skill 的全部范式模板来自 Synopsys DWC_mipi_csi2_host 商业 IP（v1.52a），该 IP：

- 约 2.1 万行、61 个文件，GA 发布
- 每个 always 块命名 `PROC_*`，便于 lint 定位
- 每个组合块有默认值赋值，无 latch
- 状态机全部两段式，带 `default` 防护和非法跳转注释（`//ccx_fsm:`）
- FIFO/CDC 全参数化，含 spyglass 豁免注释（`// spyglass disable_block XXX`）

参考文件中的代码片段均为该 IP 真实代码（做了少量截断以聚焦范式）。