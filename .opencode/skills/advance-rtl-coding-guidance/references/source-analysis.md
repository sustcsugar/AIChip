# Advance RTL Coding Guidance — 来源分析

> 本文件是 `advance-rtl-coding-guidance` skill 的背景材料，记录范式的提取来源。
> 分析对象：Synopsys DWC MIPI CSI-2 Host Controller v1.52a（商业 IP）。

## 来源 IP 概况

| 项 | 值 |
|----|----|
| IP 名称 | DWC_mipi_csi2_host（Synopsys DesignWare） |
| 版本 | 1.52a GA（2021） |
| 规模 | 61 个文件，约 2.1 万行 Verilog |
| 位置 | `src/mipi_csi2_host/` + `src/async_fifo/` |
| 提取日期 | 2026-08-20 |

## 架构摘要

```
APB(pclk) → reg_bank → synchronizer(CDC 汇聚点)
                         │
RX(rxbyteclkhs): PPI → descrambler → pd → ppi_al → pkt_analyzer
                 → pkt_buffer → pl_proc → prepare_outs → ecc/crc
                         │
IPI(pixclk): mpb_elastbuf → ipi_frame_builder → ipi_pipeline(3级) → wrapper
```

三个时钟域（pclk / rxbyteclkhs / pixclk），跨域信号**单点汇聚**在 synchronizer.v。

## 范式提取来源映射

| 范式 | 主要来源文件 |
|------|-------------|
| 端口声明 / 参数化 | 顶层 `DWC_mipi_csi2_host.v`、`mpb_elastbuf.v`、`bcm05.v` |
| 组合逻辑默认值 | `reg_bank.v`（proc_wr_regs_nxt / proc_rd_regs）、`pkt_buffer.v` |
| case vs if 决策 | `ppi_pg_cu.v`（状态机）、`ipi_pipeline.v`（trash_bytes 译码）、`pkt_buffer.v`（lane 配置） |
| 时序逻辑模板 | `reg_bank.v`（proc_wr_regs）、`ipi_frame_builder.v`（PROC_reg） |
| 两段式状态机 | `ppi_pg_cu.v`（8 态）、`ipi_frame_builder.v`（detstate）、`ipi_pipeline.v`（pixstate 级联） |
| 组合时序分离 | `pkt_buffer.v`（iworden 三件套）、`reg_bank.v`（nxt* 全量） |
| 可复用 FIFO | `bcm05.v`（控制核+格雷码）、`bcm07.v`（双时钟封装）、`mpb_elastbuf.v`（移位型） |
| 可复用 CDC | `bcm21.v`（多级同步器）、`bcm00_maj.v`（三模表决）、`synchronizer.v`（集成范式） |

## 六条核心铁律（skill 内容来源）

1. 组合块先赋默认值 → 杜绝 latch
2. 组合/时序严格分离，`nxt*` 前缀标识次态
3. 两段式 FSM：时序块只 `state <= nxtstate`
4. case 用于互斥多路译码，if 用于优先级/条件组合
5. 参数化 + localparam 推导，禁止魔数
6. 块命名 `PROC_*`，异步复位 `negedge rst_n`

## 代码片段版权说明

参考文件中的代码片段取自 Synopsys 商业 IP 的公开 RTL，仅用于范式说明（做了截断与脱敏）。
实际项目复用时应自行编写等价实现，避免直接复制商业 IP 代码。