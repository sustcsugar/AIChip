# 组合逻辑与 case vs if 决策

> 本文件是 `advance-rtl-coding-guidance` 的深度内容之一，按需加载。
> 适用任务：编写 `always @(*)` 组合逻辑、多路选择、译码、防 latch。

## 1. 组合逻辑黄金法则

**先赋默认值，再按条件覆盖。** 这是 DWC IP 组合逻辑的唯一标准写法，也是消除 latch 的根本手段。

### 1.1 标准模板：默认保持 + 条件覆盖

```verilog
always @ (*) begin  :  proc_wr_regs_nxt
    // 1) 默认值：所有输出 = 当前态（保持）
    nxtn_lanes_qst    = n_lanes_qst;
    nxtphy_shutdownz  = phy_shutdownz;
    nxtdphy_rstz      = dphy_rstz;
    // ... 全部输出先赋默认

    // 2) 条件覆盖
    if(en_wr) begin
      case(paddr)
        `CSI2_HOST_N_LANES_OS : nxtn_lanes_qst = pwdata[...];
        // ...
      endcase
    end
end
```

**为什么**：组合块若有任何路径未对输出赋值，综合器会推断 latch。默认值先行保证**每条路径都有赋值**，同时"保持原值"的语义自然表达，比在 case 每个分支写 `default: nxtx = x` 更不易遗漏。

### 1.2 读多路选择器模板

读回读寄存器也用同样模式（先全 0 默认，再按地址选）：

```verilog
always @(*) begin : proc_rd_regs
    rdata = 32'b0;                 // 默认全 0，未使能时输出 0（无 latch）
    if(en_rd) begin
      case(paddr)
        `CSI2_HOST_N_LANES_OS : rdata[3:0] = n_lanes_qst;
        // ...
      endcase
    end
end
```

## 2. case vs if 决策规则（核心）

DWC IP 中的实际判据，可直接套用：

### 2.1 用 case 的场景

| 场景 | 特征 | DWC 实例 |
|------|------|---------|
| **互斥多路状态/编码译码** | 各分支互斥，无优先级 | 状态机次态：`case(state)` |
| **查表型译码** | 输入编码 → 输出值（字节数、数据格式） | `case(wordcount_valid[2:0])` 得到 trash_bytes |
| **寄存器地址译码** | 地址 → 目标寄存器 | `case(paddr)` 读写各一处 |
| **多配置分支** | 按 lane 数/配置选择 | `case(ppi_iphy_enables)` |

```verilog
// 查表型译码（ipi_pipeline.v）
always @ (*) begin : PROC_trash_bytes
    case (wordcount_valid[2:0])
      0 : trash_bytes = 3'd0;
      1 : trash_bytes = 3'd7;
      ...
      default : trash_bytes = 3'd1;
    endcase
end

// 多配置分支（pkt_buffer.v）—— case 内嵌 case
always @(*) begin
  case (ppi_iphy_enables)
    9'b000000111: nxtheader_en = (startreg == 4'h1);
    9'b000000011,
    9'b100000001: nxtheader_en = (startreg == 4'h1);
    9'b000000001: nxtheader_en = (startreg == 4'h7);
    default:      nxtheader_en = ((start == 1'h1) & (startreg == 4'h0));
  endcase
end
```

### 2.2 用 if-else 的场景

| 场景 | 特征 | DWC 实例 |
|------|------|---------|
| **优先级逻辑** | 条件有先后，先命中先执行 | `if(cameramode) ... else ...` 最高优先级开关 |
| **级联条件组合** | 多条件叠加判断 | `if(init_pop & elastbuf_wr_pkt)` |
| **双值决策** | 二选一、保持/更新 | `if(read & ~write) ... else if(~read & write) ...` |

```verilog
// 优先级：先判 enable，再判内部状态（ipi_frame_builder.v）
always @ (*) begin : PROC_nxtdetstate
    nxtevent_pkt_wr_en = sr2vt_ipi_en_dt_dly;   // 默认值
    if(controllermode) begin
      nxtdetstate = SYNC_UNSET;                  // 最高优先级覆盖
    end else begin
      case (detstate) ... endcase
    end
end
```

### 2.3 决策速查

```
需要选路的条件是否互斥且无优先级？
├── 是，且分支 ≥ 3 或按编码/地址译码 → case
├── 是，但只有 2 分支            → if-else 或三元 ?: 均可
└── 否，有优先级/逻辑组合        → if-else 链
```

## 3. case 书写规范

### 3.1 必须带 default

- 状态机：`default: nxtstate = IDLE;`（防护未覆盖状态）
- 译码：`default: x = 默认值;`（防护未知编码）

```verilog
case (state)
  IDLE : begin ... end
  ...
  default:
    nxtstate = IDLE;    // 所有状态覆盖 + default 防护
endcase
```

### 3.2 合并分支

多个 case 项产生相同结果时用逗号合并：

```verilog
case (clockcnt)
  4'd1, 4'd2,
  4'd3, 4'd5: nxtiworden = 1'b1;
  default:    nxtiworden = 1'b0;
endcase
```

### 3.3 case 内嵌 case

外层按配置选路、内层按细分条件选路时允许嵌套（DWC 在 lane 配置 × clock 计数上大量使用）。嵌套时保持**内层也有 default**。

## 4. 反例对照

| 反例（不推荐） | 问题 | 正确做法 |
|---------------|------|---------|
| `always @(*) begin if(a) y = 1; end` | y 在 a=0 时未赋值 → latch | 先 `y = 0;` 或 `y = y;` 再覆盖 |
| 3+ 分支全用 if-else | 可读性差、易漏优先级语义 | case |
| case 无 default | 未覆盖编码 → latch/未知态 | 补 default |
| 状态机组合块里直接 `state = ...`（同名） | 与寄存器同名易混淆 | 次态统一 `nxtstate` |
| 组合块内对寄存器赋值 `count = count + 1` | 环路/锁存 | `nxtcount = count + 1;` + 时序块寄存 |