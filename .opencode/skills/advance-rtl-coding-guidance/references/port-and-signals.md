# 端口声明与信号生成

> 本文件是 `advance-rtl-coding-guidance` 的深度内容之一，按需加载。
> 适用任务：编写模块端口、参数化设计、内部信号声明、assign 派生信号。

## 1. 端口声明规范

### 1.1 顶层模块：参数化宽度用宏

顶层端口宽度来自全局配置宏（`CSI2_HOST_XXX`），禁止手写魔数。方向显式（`input` / `output wire`），总线 `[W:0]` 形式。

```verilog
module DWC_mipi_csi2_host (
    input               presetn
  , input               pclk
  , input       [ 10:0]  paddr
  , output wire [31:0]  prdata
  , output wire [`CSI2_HOST_IDI_CSIDATA_SIZE-1:0]  csi_data
  , output wire         TESTCLK
  , output wire [`CSI2_HOST_NUMBER_OF_LANES-1:0] phy_enable
  ...
  );
```

要点：
- **comma-first 风格**：逗号放行首，新增/删减端口不产生 diff 噪音
- **宽度统一 `[W-1:0]`**，不用 `[W:1]`
- 输出统一 `output wire`（除非该输出由寄存器驱动，见 3）
- 宏命名 `CSI2_HOST_<NAME>_SIZE` / `CSI2_HOST_<NAME>_RS`，一眼可辨来源

### 1.2 参数化子模块：参数在前，端口在后

```verilog
module DWC_mipi_csi2_host_mpb_elastbuf
    #(parameter [31:0] ADDR_DEPTH  = 32'd2,
      parameter [31:0] DATA_WIDTH  = 32'd32)
    (input  wire                  clk,     //- clock input
     input  wire                  rstz,    //- asynchronous rstz = reset_n
     input  wire                  write,   //- write enable, active high
     input  wire [DATA_WIDTH-1:0] datain,  //- data input
     input  wire                  read,    //- read enable, active high
     output wire [DATA_WIDTH-1:0] dataout, //- data output
     input  wire                  clrbuff, //- synchronous clear FIFO, active high
     output wire                  emptyz,  //- empty, active low
     output wire                  fullz    //- full, active low
     );
```

要点：
- 参数默认值写成 `32'dN` 全宽形式，明确位宽
- 端口按功能分组，每组注释对齐
- 端口宽度**直接由参数表达式**派生（`[DATA_WIDTH-1:0]`），体现参数化意图

### 1.3 参数与 localparam 推导

**所有算法常量用 localparam 推导，禁止裸数字**（DWC 的 FIFO 是范本）：

```verilog
parameter integer DEPTH         =  8;   // RANGE 2 to 16777216
parameter integer ADDR_WIDTH    =  3;   // RANGE 1 to 24
parameter integer COUNT_WIDTH   =  4;   // RANGE 2 to 25
parameter integer AE_LVL        =  2;   // RANGE 1 to DEPTH-1
parameter integer AF_LVL        =  2;

localparam [COUNT_WIDTH-1 : 0] A_EMPTY_VECTOR  = AE_LVL;
localparam [COUNT_WIDTH-1 : 0] A_FULL_VECTOR   = DEPTH - AF_LVL;
localparam [COUNT_WIDTH-1 : 0] HLF_FULL_VECTOR = (DEPTH+1)/2;
```

- 参数带 `RANGE` 注释说明合法范围
- `localparam` 声明时**带位宽**（`[COUNT_WIDTH-1:0]`），防隐式截断
- 支持非 2 次幂深度：用 `RESIDUAL_VALUE_BUS` 余数补偿（见 reusable-modules）

## 2. 内部信号声明

### 2.1 集中声明 + 宽度对齐

内部 wire 在模块头部集中声明，宽度右对齐便于扫描（DWC 顶层 200+ 信号全部如此）：

```verilog
wire       [`CSI2_HOST_PKTANALYZER_DATA_SIZE-1:0]  data           ;
wire                                               err_ecc_double ;
wire                                               header_valid   ;
wire       [`CSI2_HOST_NUMBER_OF_LANES-1:0]        phy_errsoths   ;
```

### 2.2 信号命名规范（重要）

| 模式 | 含义 | 示例 |
|------|------|------|
| `<name>` | 寄存器（时序块输出） | `count_int` |
| `nxt<name>` | 次态（组合块输出，将被寄存） | `nxtcount`、`nxtdetstate` |
| `<name>_s` | 同步后的信号 | `n_lanes_qst_s` |
| `<name>_psync` | 同步到 pclk 域 | `phy_errsoths_psync` |
| `<name>_ro` | 只读寄存器 | `int_st_phy_fatal_ro` |
| `<name>_qst` | 可写寄存器（APB 配置） | `ipi_mode_qst` |
| `<name>_int` | 内部派生信号 | `count_int` |

> **黄金规则：`nxt` 前缀 = 组合次态。** 看到 `nxtx` 就应知道它必然被 `x <= nxtx` 寄存，且组合块内先 `nxtx = x` 保持。

## 3. assign 派生信号生成

### 3.1 静态/拓扑信号用 assign

与时钟无关的派生信号直接 `assign`（DWC 用 assign 生成使能、选择、事件信号）：

```verilog
assign phy_enable[0] = 1'b1;
assign phy_enable[1]    =  n_lanes_qst[0] | n_lanes_qst[1];
assign phy_enable[2]    =  n_lanes_qst[1];
assign phy_enable[3]    =  n_lanes_qst[0] & n_lanes_qst[1];
```

### 3.2 事件/使能信号：组合逻辑生成后打拍

事件信号（如 "帧开始"、"行开始"）用组合逻辑生成，需要跨时钟域或对齐时序时再打一拍：

```verilog
assign vid_event_sel = video_pkt & en_video;
assign ls_event_sel  = line_start & en_line_start;
assign line_event_src_manual = vid_event_sel | ls_event_sel | nul_event_sel | blk_event_sel | emb_event_sel;
assign line_event_src = line_event_selection ? line_event_src_manual : line_event_src_auto;
```

### 3.3 三态/拼接/位宽调整

- 防截断：`{1'b0, signal}` 扩展位宽后再做加法（DWC 频繁使用）
- 位提取用 `[高:低]`，拼接用 `{}`

```verilog
assign hbp_zone = {1'b0, ipi_hsa_time_int} + {1'b0, ipi_hbp_time_int};
```

## 4. 反例对照

| 反例（不推荐） | 问题 | 正确做法 |
|---------------|------|---------|
| `output [7:1] data` | 位宽方向不规范 | `[7:0]` |
| 端口宽 `[DATA_WIDTH:1]` | 与参数化不一致 | `[DATA_WIDTH-1:0]` |
| `reg [3:0] count; ... count = count + 1;`（组合块内自累加） | 形成 latch/环路 | 分离 `nxtcount = count + 1; count <= nxtcount;` |
| 手写 `4'd8` 而非 `DEPTH` 推导 | 魔数，改参数即错 | localparam 推导 |