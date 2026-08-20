# 时序逻辑与组合时序分离范式

> 本文件是 `advance-rtl-coding-guidance` 的深度内容之一，按需加载。
> 适用任务：编写时序逻辑（寄存器）、异步/同步复位、`var_reg <= next_var` 组合时序分离。

## 1. 时序逻辑黄金法则

**一个寄存器只属于一个 always 块；时序块只做寄存（`<=`）；组合块只算次态（`=`，命名 `nxt*`）。**

这是 DWC IP 的核心可复用范式——**组合/时序严格分离**。整个 reg_bank（650 行）、pkt_buffer、ipi_pipeline 全部按此组织。

## 2. 标准三件套模板（var_reg <= next_var）

任何"可写寄存器"都按以下三件套编写：

```verilog
// (a) 声明：寄存器 + 次态
reg  iworden;
reg  nxtiworden;

// (b) 时序段：只做寄存（异步复位 + 同步更新）
always @(posedge laneclock or negedge rstz) begin
  if (~rstz)       iworden <= 1'b0;
  else             iworden <= nxtiworden;
end

// (c) 组合段：默认保持 + 条件覆盖
always @ (*) begin
  nxtiworden = iworden;                    // ← 默认保持（防 latch 关键）
  if (shift_enable|data_valid) begin
    case (ppi_iphy_enables)
      9'b000001111 : nxtiworden = 1'b1;
      9'b000000111 : case (clockcnt)
                       4'd1, 4'd2 : nxtiworden = 1'b1;
                       default    : nxtiworden = 1'b0;
                     endcase
      default      : nxtiworden = 1'b0;
    endcase
  end else begin
    nxtiworden = 1'b0;
  end
end
```

**要点**：
- 时序段**不写任何逻辑**，只做 `x <= nxtx` 搬运
- 组合段**不写任何 `<=`**，只写 `=` 且只给 `nxt*` 赋值
- 组合段第一行 `nxtx = x;`（保持）——这是与"寄存器 + 使能"最简洁的表达

## 3. 复位风格

### 3.1 异步复位（推荐，DWC 标准）

```verilog
always @ (posedge clk or negedge rst_n)
begin : PROC_xxx
    if (!rst_n) begin
      sig1 <= 1'd0;
      sig2 <= SYNC_UNSET;
    end else begin
      sig1 <= nxtsig1;
      sig2 <= nxtsig2;
    end
end
```

- 复位低有效（`rst_n` / `rstz` / `presetn` / `pixel_resetn`）
- 敏感列表：`posedge clk or negedge rst_n`（**negedge** 配低有效复位）
- 复位分支给**所有**寄存器赋复位值，不遗漏

### 3.2 异步复位 + 同步释放（复杂设计）

DWC 用 `mpb_syncrstz` 等模块做复位同步（见 reusable-modules）。常规做法：

```verilog
// 复位同步器：两级同步 + 高有效复位生成
reg rst_n_r1, rst_n_r2;
always @(posedge clk or negedge arst_n) begin
  if (!arst_n) begin rst_n_r1 <= 1'b0; rst_n_r2 <= 1'b0; end
  else begin rst_n_r1 <= 1'b1; rst_n_r2 <= rst_n_r1; end
end
assign rst_n = rst_n_r2;   // 同步释放的复位
```

### 3.3 同步复位（软复位）

DWC 支持软复位（`init_n` / `csi2_softpresetn`），与异步复位并列在同一个时序块中：

```verilog
always @ (posedge clk or negedge rst_n) begin : state_regs_PROC
   if (!rst_n) begin          // 异步复位
     count_int <= 0; ...
   end else if (!init_n) begin // 同步软复位
     count_int <= 0; ...
   end else begin              // 正常
     if (advance) count_int <= next_count_int;
     word_count_int <= next_word_count_int;
   end
end
```

> 注意：同步软复位**必须**放在异步复位之后、正常逻辑之前。

## 4. 命名规范（组合时序配套）

| 信号 | 含义 | 出现位置 |
|------|------|---------|
| `x` | 寄存器（现态） | 时序块输出 |
| `nxtx` | 次态（组合结果） | 组合块输出，被 `x <= nxtx` 消费 |
| `x_int` | 内部中间量 | 任意 |

组合块内如果还有"二级"延迟（DWC 中 `nxtnxtpixstate`），命名继续加前缀，见 fsm-pattern。

## 5. 常见错误与反例

| 反例（不推荐） | 问题 | 正确做法 |
|---------------|------|---------|
| 一个 always 块同时写多个不相关寄存器 | 违反单一职责，难维护 | 每个块只写一个功能组的寄存器 |
| 组合块里 `<=` 给寄存器赋值 | 时序/组合混写，仿真与综合语义漂移 | 分离：组合块只算 `nxt*`，时序块 `<=` |
| `always @(*)` 里写 `count = count + 1` | 组合环路（读自身+1）→ latch/振荡 | `nxtcount = count + 1; count <= nxtcount;` |
| 复位分支漏掉某个寄存器 | 上电态不确定 | 复位分支覆盖所有寄存器 |
| 异步复位块写成 `posedge rst_n` | 语法错误（高有效复位误用） | `negedge rst_n`（低有效） |
| 组合块读 `nxtx` 又写 `nxtx` | 组合环路 | 只读现态 `x` 推导次态 |