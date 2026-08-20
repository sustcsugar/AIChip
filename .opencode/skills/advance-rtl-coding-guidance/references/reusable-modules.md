# 可复用模块：FIFO / Buffer / CDC

> 本文件是 `advance-rtl-coding-guidance` 的深度内容之一，按需加载。
> 适用任务：需要 FIFO、弹性缓冲、跨时钟域同步、寄存器组的场景。
>
> **完整可例化代码**：本节展示的是范式片段（聚焦写法）。需要**完整可直接综合/仿真**的模块
> （含端口、参数、内部实现），直接使用 skill 自带的 IP 库：
> - `assets/rtl/bcm21.v` — 多级同步器（完整，自包含）
> - `assets/rtl/bcm05.v` — FIFO 控制核（完整）
> - `assets/rtl/bcm07.v` — 异步 FIFO 双时钟封装（完整）
> - `assets/rtl/bcm00_maj.v` — 三模表决器（完整）
> - `assets/rtl/mpb_elastbuf.v` — 弹性缓冲（完整，已去 include）
> 例化模板与参数表见 `assets/rtl/README.md`。下面片段仅用于理解范式。

## 1. CDC 同步器族（bcm21 / bcm00）

### 1.1 多级同步器（bcm21 范式）

参数化同步器：`WIDTH`（1~1024）、`F_SYNC_TYPE`（0~4，选择 2/3/4 级同步）、`VERIF_EN`。
综合分支直接贯通，仿真分支含采样检查。

```verilog
module bcm21 (   // 完整版见 assets/rtl/bcm21.v（IP 库内模块名与文件名一致）
    clk_d, rst_d_n, data_s, data_d );

parameter integer WIDTH        = 1;  // RANGE 1 to 1024
parameter integer F_SYNC_TYPE  = 2;  // 2 = 双寄存器同步器
parameter integer VERIF_EN     = 1;

input                   clk_d;      // 目的域时钟
input                   rst_d_n;    // 目的域异步复位
input  [WIDTH-1:0]      data_s;     // 源域数据
output [WIDTH-1:0]      data_d;     // 目的域同步后数据

`ifdef SYNTHESIS
  assign data_s_int = data_s;
`else
  // 仿真采样检查逻辑（略）
`endif

// F_SYNC_TYPE=2：两级同步器实例化
DWC_mipi_csi2_host_bcm00_sync2 #(WIDTH) U_SAMPLE_META_2(
    .clk_d(clk_d), .rst_d_n(rst_d_n), .data_s(data_s), .data_d(data_d_int));
```

**同步器核心实现（两级）**：

```verilog
// 两级同步：每级一个 DFF
always @(posedge clk_d or negedge rst_d_n) begin
  if(!rst_d_n) begin d1 <= 0; d2 <= 0; end
  else begin d1 <= data_s; d2 <= d1; end
end
assign data_d = d2;
```

**何时用 2/3/4 级**：
- 2 级：常规单 bit 同步（最常用）
- 3 级：高 MTBF 要求 / 源域变化率高的信号
- 4 级：汽车/安全等级

### 1.2 三模表决（bcm00_maj）

对关键信号做三路冗余同步 + 多数表决，容忍单路亚稳态异常：

```verilog
module bcm00_maj (a, b, c, z);   // 完整版见 assets/rtl/bcm00_maj.v
parameter integer WIDTH = 1;
input  [WIDTH-1:0] a, b, c;
output [WIDTH-1:0] z;
assign z = (a & b) | (a & c) | (b & c);   // 多数表决
endmodule
```

### 1.3 CDC 集成范式（synchronizer.v）

**架构纪律：跨域信号单点汇聚**——所有跨时钟域信号只经过一个 synchronizer 模块进出，不散落内嵌。

```verilog
// 批量同步向量信号：generate/for
generate
genvar gv5;
for(gv5=0; gv5<`CSI2_HOST_NUMBER_OF_LANES; gv5=gv5+1) begin : gen_phy_async
  bcm21 #(.WIDTH(1), .F_SYNC_TYPE(...))
    u1_bcm21_u2pt (.clk_d(fpclk), .rst_d_n(presetn_psync),
                   .data_s(phy_rxulpsesc[gv5]), .data_d(phy_rxulpsesc_s[gv5]));
end
endgenerate
```

同步后如果还需要寄存一拍（对齐时序），再加独立时序块：

```verilog
always @ (posedge fpclk or negedge presetn_psync) begin : phy_stopstatedata_s_PROC
  if(!presetn_psync) phy_stopstatedata_s <= {`CSI2_HOST_NUMBER_OF_LANES{1'b0}};
  else               phy_stopstatedata_s <= phy_stopstatedata_s_aux;
end
```

## 2. 异步 FIFO 体系（bcm05 / bcm07）

### 2.1 架构分层（DWC 标准）

```
bcm07（双时钟域 FIFO 封装）
 ├── push 侧：clk_push/rst_push_n/push_req_n/push_*状态
 ├── pop  侧：clk_pop/rst_pop_n/pop_req_n/pop_*状态
 └── 内部：bcm05（单域控制核）+ 外部 SRAM（we_n/wr_addr/rd_addr）
```

### 2.2 格雷码编码/解码（FIFO 指针跨域的核心）

```verilog
// 二进制 → 格雷
function automatic [COUNT_WIDTH-1:0] func_bin2gray;
  input [COUNT_WIDTH-1:0] f_b;
  begin func_bin2gray = f_b ^ (f_b >> 1); end
endfunction

// 格雷 → 二进制（迭代异或）
function automatic [COUNT_WIDTH-1:0] func_gray2bin;
  input [COUNT_WIDTH-1:0] f_g;
  reg   [COUNT_WIDTH-1:0] f_b;
  integer f_i;
  begin
    f_b = {COUNT_WIDTH{1'b0}};
    for (f_i=COUNT_WIDTH-1 ; f_i >= 0 ; f_i=f_i-1) begin
      if (f_i < COUNT_WIDTH-1) f_b[f_i] = f_g[f_i] ^ f_b[f_i+1];
      else                     f_b[f_i] = f_g[f_i];
    end
    func_gray2bin = f_b;
  end
endfunction
```

### 2.3 指针同步与满/空判断

```verilog
// 对端指针格雷码同步到本域
bcm21 #(COUNT_WIDTH, SYNC_DEPTH, ...)
  U_sync(.clk_d(clk), .rst_d_n(rst_n), .data_s(other_addr_g), .data_d(raw_sync));

assign other_addr_g_sync = raw_sync ^ START_VALUE_GRAY_BUS;  // 格雷去偏移
assign other_addr_decoded = func_gray2bin(other_addr_g_sync); // 解码

// 满/空：本域计数与阈值比较
assign next_almost_empty = (next_word_count_int <= A_EMPTY_VECTOR);
assign next_almost_full  = (next_word_count_int >= A_FULL_VECTOR);
assign next_empty        = (next_word_count_int == BUS_LOW);
assign next_full_int     = (next_word_count_int == FULL_COUNT_BUS);
```

**要点**：格雷码保证跨域同步时**最多 1 bit 翻转**，消除指针竞争；满/空用计数比较而非直接比较同步后的指针（避免同步延迟导致的误判）。

### 2.4 非 2 次幂深度支持

```verilog
// 余数补偿：非 2 次幂深度时调整计数
localparam RESIDUAL_VALUE_BUS = ((1 << COUNT_WIDTH) - ((DEPTH == (1 << (COUNT_WIDTH-1)))?
                                  (DEPTH * 2) : ((DEPTH + 2) - (DEPTH & 1))));
```

## 3. 弹性缓冲（mpb_elastbuf：移位寄存器型 FIFO）

无需 RAM、参数化深宽、带同步清零。适合浅 FIFO（2~32 深度）：

```verilog
module mpb_elastbuf   // 完整版见 assets/rtl/mpb_elastbuf.v
    #(parameter [31:0] ADDR_DEPTH = 32'd2,
      parameter [31:0] DATA_WIDTH = 32'd32)
    (input wire clk, input wire rstz,
     input wire write, input wire [DATA_WIDTH-1:0] datain,
     input wire read,  output wire [DATA_WIDTH-1:0] dataout,
     input wire clrbuff, output wire emptyz, output wire fullz);

localparam ADDR_DEPTH_BITS = $clog2(ADDR_DEPTH+1);
reg  [ADDR_DEPTH-1:0] writeptr;                 // 移位指针：0=空位，1=有数据
reg  [DATA_WIDTH-1:0] memshift [ADDR_DEPTH-1:0];

assign full   = writeptr[ADDR_DEPTH-1];         // 最高位=满
assign emptyz = writeptr[0];                    // 最低位=空
assign dataout = memshift[0];                   // 最新字永远在 [0]

// 读写指针：读右移、写左移、同拍读优先
always @ (posedge clk or negedge rstz) begin : PROC_writeptr
  if (!rstz)           writeptr <= {ADDR_DEPTH{1'b0}};
  else begin
    if (clrbuff)       writeptr <= {ADDR_DEPTH{1'b0}};
    else begin
      if (read & ~write)      writeptr <= {1'b0, writeptr[ADDR_DEPTH-1:1]};  // shift right
      else if (~read & write) writeptr <= {writeptr[ADDR_DEPTH-2:0], 1'b1}; // shift left
      else if (read & write) begin
        if (full)  writeptr <= {1'b0, writeptr[ADDR_DEPTH-1:1]};   // 读优先
        else if (empty) writeptr <= {writeptr[ADDR_DEPTH-2:0], 1'b1};
      end
    end
  end
end
```

**存储阵列用 generate 展开**（每级一个时序块）：

```verilog
generate
genvar i;
for (i=0; i<(ADDR_DEPTH-1); i=i+1) begin : shift_register
  always @ (posedge clk or negedge rstz) begin: PROC_memshift_older_words
    if (!rstz) memshift[i] <= {DATA_WIDTH{1'b0}};
    else begin
      if (clrbuff) memshift[i] <= {DATA_WIDTH{1'b0}};
      else begin
        if (read & ~write) begin
          if (writeptr[(i+1)]) memshift[i] <= memshift[(i+1)];  // 前级下移
          else                 memshift[i] <= {DATA_WIDTH{1'b0}};
        end else if (~read & write) begin
          if (~writeptr[i]) memshift[i] <= datain;              // 空位写入
        end
        ...
      end
    end
  end
end
endgenerate
```

## 4. 寄存器组（reg_bank 范式）

APB 寄存器组的读写完整范式（约 650 行，DWC 结构）：

```verilog
// 写：时序段（复位 + en_wr + case(paddr)）
always @ (posedge pclk or negedge presetn) begin : proc_wr_regs
  if(~presetn) begin
    n_lanes_qst <= `CSI2_HOST_N_LANES_QST_RST_VAL;   // 复位默认值（可为宏）
    // ... 全部寄存器复位值
  end
  else if(en_wr) begin
    case(paddr)
      `CSI2_HOST_N_LANES_OS : n_lanes_qst <= nxtn_lanes_qst;
      // ...
    endcase
  end
  else begin
    // autoclear 寄存器（写 1 清 0 类）
    ipi_mem_flush[0] <= 1'b0;
  end
end

// 写次态：组合段（默认保持 + 位提取/拼接）
always @ (*) begin : proc_wr_regs_nxt
  nxtn_lanes_qst = n_lanes_qst;      // 默认保持
  if(en_wr) begin
    case(paddr)
      `CSI2_HOST_N_LANES_OS : nxtn_lanes_qst = pwdata[3:0];
      // 位域拼接：nxtipi_mode_qst = {pwdata[24], 7'd0, pwdata[16], ...};
    endcase
  end
end

// 读：组合段（默认 0 + case）
always @(*) begin : proc_rd_regs
  rdata = 32'b0;
  if(en_rd) begin
    case(paddr)
      `CSI2_HOST_N_LANES_OS : rdata[3:0] = n_lanes_qst;
      // ...
    endcase
  end
end
```

**寄存器组要点**：
- 复位默认值用宏定义（`CSI2_HOST_N_LANES_QST_RST_VAL`），可配置
- 位域提取/拼接集中在**次态组合块**（`proc_wr_regs_nxt`），时序块只搬移
- autoclear / write-1-clear 寄存器在时序块的 `else`（无写）分支自动清零
- 中断 status 寄存器（`_ro`）由中断源逻辑驱动，force/msk 由软件写

## 5. 模块选择决策表

| 需求 | 选择 | 原因 |
|------|------|------|
| 单 bit / 多 bit 跨时钟域 | bcm21 同步器（2/3/4 级） | 参数化、可配 |
| 跨时钟域关键信号（安全） | 三路同步 + bcm00_maj 表决 | 容忍单路亚稳态 |
| 异步 FIFO（双时钟） | bcm07 + bcm05 + 外部 SRAM | 深度可做大、工业标准 |
| 浅 FIFO / 弹性缓冲（同域或近同步） | mpb_elastbuf 移位型 | 无需 RAM、实现简单 |
| APB/寄存器配置接口 | reg_bank 范式 | 读写分离、autoclear、中断管理 |
| 复位同步释放 | mpb_syncrstz / 两级同步器 | 消除异步复位释放竞争 |