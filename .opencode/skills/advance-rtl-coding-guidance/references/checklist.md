# RTL 编码规范自检清单

> 本文件是 `advance-rtl-coding-guidance` 的深度内容之一，按需加载。
> 适用任务：写完代码后自检、评审他人代码时逐项核对。
> 机械性检查可用 `scripts/check_rtl_style.py` 辅助。

## 使用方法

- 对照清单逐项检查，标记 `PASS` / `FAIL` / `N/A`
- 评审他人代码时，按严重度输出：`blocker`（必须改）→ `warning`（应改）→ `suggestion`（可选）

## A. 结构与命名（结构性）

| # | 检查项 | 严重度 |
|---|--------|--------|
| A1 | 每个 always 块有命名标签 `begin : PROC_<name>` | warning |
| A2 | 寄存器信号名与次态信号名成对（`x` ↔ `nxtx`） | warning |
| A3 | 状态常量用 localparam，非裸数字 | blocker |
| A4 | 参数/localparam 带位宽声明（`[W-1:0]`） | warning |
| A5 | 无未使用信号（lint W528 类） | warning |
| A6 | 信号宽度一致，无隐式截断（lint W164a/W164b） | warning |

## B. 组合逻辑（防 latch）

| # | 检查项 | 严重度 |
|---|--------|--------|
| B1 | 每个 `always @(*)` 输出**先赋默认值**再覆盖 | **blocker** |
| B2 | 组合块内**只用 `=`，不用 `<=`** | **blocker** |
| B3 | 组合块内**只写 `nxt*` 次态，不直接改寄存器** | **blocker** |
| B4 | 每个 case 都有 `default` | blocker |
| B5 | case 用于互斥多路译码，if 用于优先级逻辑 | suggestion |
| B6 | 组合块敏感列表完整（`@(*)`，不用罗列信号） | blocker |

## C. 时序逻辑（可综合性）

| # | 检查项 | 严重度 |
|---|--------|--------|
| C1 | 时序块敏感列表正确（异步复位 `posedge clk or negedge rst_n`） | blocker |
| C2 | 复位分支覆盖**所有**寄存器 | blocker |
| C3 | 一个寄存器只被一个 always 块赋值 | blocker |
| C4 | 时序块只用 `<=` | blocker |
| C5 | 同步软复位在异步复位之后、正常逻辑之前 | warning |
| C6 | 无组合环路（组合块读自身输出） | blocker |

## D. 状态机

| # | 检查项 | 严重度 |
|---|--------|--------|
| D1 | 两段式：时序段只 `state <= nxtstate`，组合段只算 `nxtstate` | warning |
| D2 | 次态组合块 case 覆盖所有状态 + `default` 回安全态 | blocker |
| D3 | 复位到初始态（IDLE） | warning |
| D4 | 状态转移有注释说明（含非法跳转声明） | suggestion |
| D5 | 状态编码不冲突（无重复编码） | blocker |

## E. 可复用模块（FIFO/CDC）

| # | 检查项 | 严重度 |
|---|--------|--------|
| E1 | FIFO 指针跨域用格雷码，同步后解码 | blocker |
| E2 | FIFO 满/空判断用计数比较，非直接比较同步后指针 | warning |
| E3 | 跨域信号只经同步器进出（单点汇聚） | warning |
| E4 | 同步器带目的域复位，复位值定义明确 | warning |
| E5 | 多 bit 跨域不用普通两级同步（需格雷/握手/异步FIFO） | blocker |
| E6 | 弹性缓冲读/写同拍冲突有明确优先级 | warning |

## F. 可读性与维护性

| # | 检查项 | 严重度 |
|---|--------|--------|
| F1 | 端口/内部信号分组声明，宽度对齐 | suggestion |
| F2 | 复杂位域操作有注释说明（为什么这样拼） | suggestion |
| F3 | 工具豁免有注释（`// spyglass disable_block XXX` + 原因） | warning |
| F4 | 模块参数带 RANGE 注释，默认值明确 | suggestion |
| F5 | 无魔数（宽度/阈值均由参数推导） | warning |

## 输出格式模板（评审他人代码时）

```
## Review: <module_name>.v

### blocker
- [B1] 组合块 proc_xxx 未赋默认值 → 潜在 latch（行 42-47）

### warning
- [C5] 同步复位位置错误（行 88）

### suggestion
- [D4] 状态转移建议补充非法跳转注释
```

## 与脚本配合

```bash
# 机械性检查（命名/结构/常见反模式）
python scripts/check_rtl_style.py <file.v> [<file2.v> ...]
```

**脚本自动覆盖的清单项**：A1、B1、B3、B4、B6、C4、C5（提示级）、F5。
**脚本无法覆盖、需人工/工具检查的项**：A2（命名配对为启发式）、A3-A6、C1-C3、C6、D1-D5、E1-E6、F1-F4。
脚本发现 `blocker` 时必须人工复核——启发式可能误报（如 B1 对"case 全覆盖无默认值但无 latch"的写法会提示）。