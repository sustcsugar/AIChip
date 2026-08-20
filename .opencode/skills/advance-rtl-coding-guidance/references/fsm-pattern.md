# 两段式状态机范式

> 本文件是 `advance-rtl-coding-guidance` 的深度内容之一，按需加载。
> 适用任务：编写状态机（FSM），评审他人状态机代码。

## 1. 状态机黄金法则

DWC IP 全部使用**两段式状态机**：时序段只做状态寄存，组合段只算次态。

- 时序段：`always @(posedge clk or negedge rst_n) state <= nxtstate;`
- 组合段：`always @(*) case(state) ... endcase` 算 `nxtstate`
- 组合段同时算**输出（Moore 型）**或**输出随状态+输入（Mealy 型）**

## 2. 标准两段式模板

### 2.1 状态定义（常量，非裸数字）

```verilog
// 用 localparam 或宏定义状态；状态名全大写
localparam SYNC_UNSET      = 2'd0;
localparam SYNC_LINE_START = 2'd1;
localparam SYNC_BLANKING   = 2'd2;
localparam SYNC_VIDEO      = 2'd3;
```

### 2.2 组合段（次态 + 输出）

```verilog
always @ (*)
begin : nxtstate_PROC
    case (state)
      IDLE : begin
        if(ppi_pg_enable_level) nxtstate = BLANKING;
        else                    nxtstate = IDLE;
      end
      FRAME_START : begin
        if(cccounter >= {6'd0, header_period}) nxtstate = BLANKING;
        else                                   nxtstate = FRAME_START;
      end
      PAYLOAD : begin
        if ((pix_counter >= h_limit) && payload_sent) nxtstate = PACKET_FOOTER;
        else                                          nxtstate = PAYLOAD;
      end
      BLANKING : begin
        if(cccounter >= {6'd0, blanking_period}) begin
          if(prev_state == IDLE)        nxtstate = FRAME_START;
          else if (prev_state == LINE_END) ...
          else                          nxtstate = BLANKING;
        end else nxtstate = BLANKING;
      end
      default:
        nxtstate = IDLE;    // 防护：未覆盖状态回安全态
    endcase
end
```

### 2.3 时序段（状态寄存）

```verilog
always @ (posedge rxbyteclkhs or negedge rstz)
begin : state_PROC
    if (!rstz)         state <= 7'd0;        // 复位到初始态（IDLE）
    else begin
      if (ppi_pg_enable_level) state <= nxtstate;   // 使能门控（可选）
    end
end
```

### 2.4 输出生成

- **Moore 输出**：由现态 `state` 译码（组合），或打拍成寄存器输出
- **Mealy 输出**：在次态组合块中随输入一起算

DWC 对"每状态输出"的典型做法是独立组合块：

```verilog
always @ (*)
begin : PROC_n_line_event_src
   case (detstate)
     SYNC_UNSET : line_event_src_auto = line_start|nul_pkt|blk_pkt|video_pkt|emb_pkt;
     SYNC_LINE_START : line_event_src_auto = line_start;
     SYNC_BLANKING : line_event_src_auto = nul_pkt|blk_pkt|emb_pkt_ipiz;
     SYNC_VIDEO : line_event_src_auto = video_pkt | emb_pkt_ipi;
   endcase
end
```

## 3. 状态机保护机制（DWC 特色，强烈建议采用）

### 3.1 非法跳转注释（供 lint/形式化工具消费）

DWC 用 `//ccx_fsm:` 注释声明非法转移，工具会据此检查：

```verilog
//ccx_fsm: ; detstate ; SYNC_VIDEO->SYNC_BLANKING ; "Illegal FSM transition, added for state machine protection."
//ccx_fsm: ; detstate ; SYNC_VIDEO->SYNC_LINE_START ; "Illegal transition, added for state machine protection."
```

### 3.2 未覆盖状态回安全态

所有 case 的 `default` 回到 `IDLE`/`SYNC_UNSET`，防止非法状态卡死：

```verilog
default:
  nxtstate = IDLE;    // "Default statement for linting purposes."
```

### 3.3 状态编码

- 小 FSM（<16 态）：顺序编码即可，复位简单
- 大 FSM：可用 `localparam` 常量（DWC 用 7 位宽容纳 8 态，留余量）

## 4. 扩展范式

### 4.1 FSM 级联（主 FSM 控制子 FSM）

DWC 的 ipi_pipeline 中，像素 FSM 的次态依赖主 FSM 的**次态**（提前一拍对齐）：

```verilog
// 子 FSM 组合段读取主 FSM 的 nxtstate（跨状态机同步）
always @ (*) begin : PROC_pix_state_reg
  case (pixstate)
    PIX_IDLE : begin
      if(elastbuf_emptyz && (~stage1on1d)) nxtpixstate = DATA_AVAILABLE;
      else if((nxtstate == VIDEO) && (stage1on1d)) nxtpixstate = TRANSMITING;
      else nxtpixstate = PIX_IDLE;
    end
    ...
  endcase
end
```

### 4.2 二级延迟次态（防毛刺）

需要时可在次态后**再打一拍**（`nxtnxtpixstate`），把"立即生效"变成"下一拍生效"：

```verilog
always @ ( * ) begin : PROC_pixstate_nxt
  if(~stoppipeline)          nxtnxtpixstate = nxtpixstate;
  else if ((nxtstate != HOLD_STATE_VIDEO) & (pixstate== FINISH)) nxtnxtpixstate = nxtpixstate;
  else                       nxtnxtpixstate = pixstate;
end
```

### 4.3 计数器在状态机中的应用

状态内计数（DWC 的 `cccounter`、`pix_counter`）用独立组合/时序对：

```verilog
// 计数使能：组合
assign cnt_en = (state == PAYLOAD) && payload_valid;
// 计数寄存：时序
always @(posedge clk or negedge rst_n)
  if(!rst_n) cccounter <= 0;
  else if(cnt_en) cccounter <= nxtcccounter;
```

## 5. 反例对照

| 反例（不推荐） | 问题 | 正确做法 |
|---------------|------|---------|
| 三段式（状态寄存 + 次态 + 输出三段） | 可读但冗余，输出多一拍 | 两段式即可覆盖 |
| 单 always 块内 `case` 直接 `state <=` | 组合时序混写 | 分离为两段 |
| 状态用裸数字 `2'd0` 直接比较 | 不可读、易错 | localparam 常量 |
| case 无 default | 非法状态无出路 | default 回 IDLE |
| 组合块内不赋默认值 | 未覆盖路径 → latch | 先 `nxtstate = state;` 或每分支全覆盖 |
| 复位到非初始态 | 上电行为不确定 | 复位到 IDLE/初始态 |