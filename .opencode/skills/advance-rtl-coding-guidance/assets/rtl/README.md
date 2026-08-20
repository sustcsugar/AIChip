# advance-rtl-coding-guidance — RTL IP 库

> 本目录是 `advance-rtl-coding-guidance` skill 的可复用 IP 库（assets/rtl）。
> 全部单元提取自 Synopsys DWC_mipi_csi2_host v1.52a（商业 IP），**版权头保留、模块名已简化**（与文件名一致）。
> 使用方式：**复制所需文件到项目 RTL 目录，直接例化**，无额外依赖。

## 依赖关系图

```
┌─────────────────────────────────────────────────────────┐
│ bcm07.v（异步 FIFO 双时钟封装，push/pop 双域）          │
│   ├── 依赖 bcm05.v（FIFO 控制核 ×2）                    │
│   └── 依赖 bcm21.v（指针同步）                          │
├─────────────────────────────────────────────────────────┤
│ bcm05.v（FIFO 控制核：格雷码指针/满空/计数）            │
│   └── 依赖 bcm21.v（对端指针同步）                      │
├─────────────────────────────────────────────────────────┤
│ bcm21.v（多级同步器 2/3/4 级，自包含）                  │
│   └── 无子模块依赖（不定义 DWC_SYNC_N_STAGE_SRC 宏时    │
│       使用内部 fallback RTL，无需 DesignWare 库）       │
├─────────────────────────────────────────────────────────┤
│ bcm00_maj.v（三模表决器，独立）                         │
├─────────────────────────────────────────────────────────┤
│ mpb_elastbuf.v（弹性缓冲/移位型 FIFO，独立）            │
│   └── 无子模块依赖（已移除 include）                    │
└─────────────────────────────────────────────────────────┘
```

**最小复制集**：
- 需要双时钟异步 FIFO → 复制 `bcm07.v` + `bcm05.v` + `bcm21.v`
- 只需要单 bit/多 bit 同步器 → 复制 `bcm21.v`
- 只需要浅 FIFO（≤32 深度，同域或近同步）→ 复制 `mpb_elastbuf.v`
- 需要安全同步（容忍单路亚稳态）→ 复制 `bcm21.v` + `bcm00_maj.v`

## 单元说明

### 1. bcm21.v — 多级同步器

| 参数 | 默认 | 说明 |
|------|------|------|
| `WIDTH` | 1 | 数据宽度（1~1024） |
| `F_SYNC_TYPE` | 2 | 同步方式：2=双寄存器同步器（推荐） |
| `VERIF_EN` | 1 | 验证辅助（0/1） |
| `SVA_TYPE` | 1 | 断言类型 |

端口：`clk_d`（目的域时钟）、`rst_d_n`（目的域异步复位）、`data_s`（源域数据）、`data_d`（同步后数据）。

```verilog
// 例化：单 bit 从 rxbyteclkhs 域同步到 pclk 域
bcm21 #(.WIDTH(1), .F_SYNC_TYPE(2))
  u_sync (
    .clk_d  (pclk),
    .rst_d_n(presetn_psync),
    .data_s (phy_rxulpsesc),
    .data_d (phy_rxulpsesc_s)
  );
```

> **综合提示**：默认（不定义 `DWC_SYNC_1_STAGE_SRC`/`DWC_SYNC_2_STAGE_SRC` 等宏）时使用内部 RTL fallback，独立可综合。仿真时大量 `$display` 位于 `ifndef SYNTHESIS` 分支。

### 2. bcm00_maj.v — 三模表决器

| 参数 | 默认 | 说明 |
|------|------|------|
| `WIDTH` | 1 | 数据宽度（1~8192） |

端口：`a/b/c`（三路输入）、`z`（多数表决输出：`(a&b)|(a&c)|(b&c)`）。

```verilog
// 三路同步后表决
bcm00_maj #(.WIDTH(1)) u_maj (
  .a(sync_a), .b(sync_b), .c(sync_c), .z(safe_sig));
```

### 3. bcm05.v — 异步 FIFO 控制核（单域）

| 参数 | 默认 | 说明 |
|------|------|------|
| `DEPTH` | 8 | 深度（2~16777216，支持非 2 次幂） |
| `ADDR_WIDTH` | 3 | 地址宽度 |
| `COUNT_WIDTH` | 4 | 计数宽度 |
| `AE_LVL` | 2 | almost empty 阈值 |
| `AF_LVL` | 2 | almost full 阈值 |
| `ERR_MODE` | 0 | 错误模式（0=粘滞/1=瞬时） |
| `SYNC_DEPTH` | 2 | 同步器级数 |
| `IO_MODE` | 1 | 0=读侧推进/1=写侧推进 |

端口：`clk/rst_n/init_n/inc_req_n/other_addr_g`（对端格雷指针）、`word_count/empty/almost_empty/half_full/almost_full/full/error`、`this_addr/this_addr_g/next_*`。

**bcm05 是半接口**：输入对端格雷指针 `other_addr_g`，输出本域格雷指针 `this_addr_g`。通常通过 bcm07 使用，或自行按此契约对接：

```verilog
// 读侧控制核例化（bcm07 内部模式）
bcm05 #(
  .DEPTH(64), .ADDR_WIDTH(6), .COUNT_WIDTH(7),
  .AE_LVL(4), .AF_LVL(4), .SYNC_DEPTH(2), .IO_MODE(0))
  u_rd_ctrl (
    .clk(clk_pop), .rst_n(rst_pop_n), .init_n(init_pop_n),
    .inc_req_n(pop_req_n), .other_addr_g(push_addr_g),
    .word_count(pop_word_count),
    .empty(pop_empty), .almost_empty(pop_ae), .half_full(pop_hf),
    .almost_full(pop_af), .full(pop_full), .error(pop_error),
    .this_addr(rd_addr), .this_addr_g(pop_addr_g),
    .next_word_count(), .next_empty_n(), .next_full(), .next_error());
```

### 4. bcm07.v — 异步 FIFO 双时钟封装（推荐直接使用）

| 参数 | 默认 | 说明 |
|------|------|------|
| `DEPTH` | 8 | 深度（2~16777216） |
| `ADDR_WIDTH` | 3 | 地址宽度 |
| `COUNT_WIDTH` | 4 | 计数宽度 |
| `PUSH_AE_LVL`/`POP_AE_LVL` | 2 | 各域 almost empty 阈值 |
| `PUSH_AF_LVL`/`POP_AF_LVL` | 2 | 各域 almost full 阈值 |
| `PUSH_SYNC`/`POP_SYNC` | 2 | 各域同步器级数 |
| `MEM_MODE` | 0 | 灰度指针流水线：0=无、1/2/3=读/写/双侧打一拍（用于外部存储器时序收紧） |
| `ERR_MODE` | 0 | 错误模式 |

端口：push 侧 `clk_push/rst_push_n/init_push_n/push_req_n/push_*状态/push_word_count`；pop 侧对称；RAM 接口 `we_n/wr_addr/rd_addr`。

```verilog
// 完整异步 FIFO 例化（64×8bit，写域→读域）
bcm07 #(
  .DEPTH(64), .ADDR_WIDTH(6), .COUNT_WIDTH(7),
  .PUSH_AE_LVL(4), .PUSH_AF_LVL(4),
  .POP_AE_LVL(4), .POP_AF_LVL(4))
  u_async_fifo (
    // push 域
    .clk_push(wclk), .rst_push_n(wrst_n), .init_push_n(winit_n),
    .push_req_n(wreq_n),
    .push_empty(), .push_ae(), .push_hf(), .push_af(), .push_full(push_full),
    .push_error(), .push_word_count(),
    // pop 域
    .clk_pop(rclk), .rst_pop_n(rrst_n), .init_pop_n(rinit_n),
    .pop_req_n(rreq_n),
    .pop_empty(pop_empty), .pop_ae(), .pop_hf(), .pop_af(), .pop_full(),
    .pop_error(), .pop_word_count(),
    // RAM 接口（外部 SRAM 或内部寄存器堆）
    .we_n(we_n), .wr_addr(wr_addr), .rd_addr(rd_addr));
```

> **数据通路说明**：bcm07 是纯控制模块（`we_n = push_full | push_req_n`，`wr_addr/rd_addr` 来自两侧 bcm05 的 `this_addr`）。**数据存储（wdata/rdata 与 RAM 实例）需由外部 RAM 或自建寄存器堆提供**，bcm07 只输出地址与读写使能。SVA 断言在 `DWC_BCM_SNPS_ASSERT_ON` 且非 `SYNTHESIS` 时编译。

### 5. mpb_elastbuf.v — 弹性缓冲（移位型 FIFO）

| 参数 | 默认 | 说明 |
|------|------|------|
| `ADDR_DEPTH` | 2 | 深度（≥2） |
| `DATA_WIDTH` | 32 | 数据宽度 |

端口：`clk/rstz/write/datain/read/dataout/clrbuff/emptyz/fullz`（empty/full 低有效）。

```verilog
// 4×6bit 事件缓冲例化
mpb_elastbuf #(.ADDR_DEPTH(4), .DATA_WIDTH(6))
  u_elastbuf (
    .clk(pixclk), .rstz(pixel_resetn), .clrbuff(init_pop),
    .datain(datatype_dly), .write(elastbuf_wr_en), .fullz(elastbuf_fullz),
    .dataout(elastbuf_data_rd), .read(elastbuf_rd_en), .emptyz(elastbuf_emptyz));
```

## 使用纪律

1. **保留版权头**：文件含 Synopsys 版权声明，商用前确认许可协议（本 skill 仅作内部复用模板）。
2. **模块名即文件名**：`bcm21`/`bcm05`/`bcm07`/`bcm00_maj`/`mpb_elastbuf`。内部引用（bcm05↔bcm21、bcm07↔bcm05）已全局同步，复制后**无需改名**；若项目内需重命名，注意全局替换所有实例。
3. **综合宏**：`SYNTHESIS` 定义时仿真辅助/断言分支被剔除；`DWC_BCM_SNPS_ASSERT_ON` 控制断言编译。**仿真若需启用断言**，bcm21/bcm07 会引用 `DWC_mipi_csi2_host_sva0x` 与 `DWC_mipi_csi2_host_bvm02` 等断言模块——这些不在本库内，需从原 IP 源码补充（或保持该宏未定义，仅功能仿真）。
4. **复位风格**：全部为异步复位低有效（`rst_n`/`rstz`），与 SoC 复位策略对齐后再接入。
5. **IP 只读**：本库文件按只读资产管理，如需定制派生新模块，复制后改名使用。