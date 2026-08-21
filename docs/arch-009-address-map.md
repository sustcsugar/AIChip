# B2 地址映射架构文档（arch-009-address-map.md）

> 节点 B2 产物（地址映射）| 归属：arch-agent | 版本：v1.0（待质量门签字）
> 上位输入（只读，引用原文核验）：
> - spec-005-interface-spec.md §7 + spec-005-memory-map.csv（spec-v1.0 冻结基线，15 区域初版）
> - arch-008-system-arch.md v1.2（B1 已签核：方案 A + 从侧结构 β，ADR-025）
> - ADR-009（AXI4 统一，决策 1 原文："RIB↔AXI 桥 AXI 侧、AXI_SRAM、全部外设从端口统一 AXI4；突发/outstanding/ID 宽度细节由 B3 量化细化"）
> - ADR-025 决策 2 原文（"从侧结构 β 采纳：……AXI_SRAM 走 AXI4 全量（保留突发），8 寄存器外设经 AXI4→AXI4-Lite 转换器（归 AXI_IB glue，归属随 R6 待 B3）降 Lite"）
> - spec-004 §3（PPAC 唯一事实源）：PPAC-013 固件启动时延 ≤100ms（"SPI Flash 模型加载 64 KB 镜像，@50 MHz；单线 SPI 12.5MHz 70% 评估 ≈ 60 ms 留裕量"）；PPAC-014 AXI_SRAM 单次读时延（经桥）≤10 系统时钟周期
>
> 机器可读唯一事实源：`docs/B2-addr-map.yaml`；检查报告：`docs/B2-addr-check.txt`；本文为架构论证与裁定记录。
> **本文不回写 spec-005**（冻结基线只读；基址/大小与冻结初版完全一致，B2 产出为架构级细化属性）。

---

## 1. AXI_SRAM 容量量化论证（MEM-03，64KB 维持）

### 1.1 需求侧分解（@0x2000_0000，64KB = 0x1_0000）

| 需求项 | 依据 | 量化 |
|--------|------|------|
| 固件镜像（代码+rodata+sdata）加载目标 | PPAC-013（64KB 镜像测试激励）/ FS-011 / UC-BOOT-004 | 镜像预算 ≤ 48KB（0xC000） |
| 栈（向下生长，栈顶 0x2000_FFFF） | RV32IM 调用深度（demo 级：LED/UART/SPI/IIC/PWM 联动，UC-DEMO-001），无 RTOS | 4KB |
| data/BSS + 堆 | 全局变量/缓冲（UART/SPI FIFO 镜像、CRC 表可查表在 rodata） | 4KB |
| 合计 | — | **≤ 56KB < 64KB（余量 8KB / 14%）** |

实际固件尺寸预期：SC-12 验收演示级固件（类似 MCU bare-metal hello+协议栈）业界经验 8~24KB，对 48KB 镜像预算裕量 ≥ 2×。

### 1.2 与 PPAC-013 的口径澄清（关键，避免容量误判）

PPAC-013 的"64KB 镜像"是**时延测试激励**（复位释放 → 固件首指令，测加载带宽与通路时延，spec-004 §3 验证方法原文），不要求满 64KB 镜像常驻**并**与运行数据共存——运行态固件受 §1.1 的 56KB 预算约束。加载路径时延与容量无关（60ms 由 SPI 带宽决定，arch-008 §4.1 已核 ≈61ms < 100ms）。

### 1.3 PPAC-014 复核

MEM-03 窗口经桥读时延预算 ≤10 周期分解不变（arch-008 §4.2）；β 结构下 SRAM 分支不经 AXI4→Lite 转换器（ADR-025 决策 2），**零额外转换时延**，预算不受 B2 影响 ✓。

### 1.4 结论

- **维持 64KB（0x10000），MEM-03 窗口基址/大小不变**（与冻结 spec-005 一致，无需基线变更）。
- **软件分段约束**（移交 B7 参考模型 / 软件：链接脚本）：image ≤ 0x2000_BFFF，栈顶 0x2000_FFFF 向下 4KB，data/BSS/堆 4KB。
- 若后续固件实际超 48KB：登记为下一版扩展项（SRAM 扩 128KB，地址窗口按 2 的幂扩至 0x20000，保留区 MEM-04 相应收缩——属基线变更流程，走 OI/ADR，不在本版）。

## 2. Boot ROM 容量确认（MEM-01，4KB 维持，B1 交接 R5）

bootloader 功能集（arch-008 §3 BLOCK-12）：SPI 初始化/PIO 读循环/CRC 校验/跳转 + UART 固件更新协议入口。紧凑 RISC-V 汇编估算：主循环 PIO 读（≈100 指令）+ CRC（≈80，查表则 rodata +256B）+ 更新协议（≈300，含 XMODEM 级收包）+ 初始化/跳转/向量表（≈200）≈ **700 指令 × 4B ≈ 2.8KB + 表 0.25KB ≈ 3.0KB < 4KB**（裕量 25%，紧凑但充分；C 编译 -Os 可能超——**建议 bootloader 汇编或 -Os + section 收紧，约束移交 B7/软件**）。**结论：维持 4KB。**

## 3. 完整地址映射表（B2 版，架构级细化）

> 机器可读版含全部字段：`docs/B2-addr-map.yaml`（唯一事实源）。检查：`build_addr_map.py` 输出 PASS（0 ERROR，见 §6 度量）。

### 3.1 主表（15 区域）

| MEM | 名称 | 基址 | 大小 | 对齐 | 总线域 | 从设备 | 访问 | 译码归属 | 错误响应（建议，B3 定） |
|-----|------|------|------|------|--------|--------|------|----------|--------------------------|
| 01 | Boot ROM | 0x0000_0000 | 4KB | 4KB | RIB | BLOCK-12 | RO | RIB 侧译码 | 窗口内偏移全实现；RIB_ERR 保留口径 |
| 02 | RIB 保留区 | 0x0000_1000 | 0x1FFF_F000 | 4KB | RIB | —（译码外） | — | RIB 侧译码 | RIB_ERR（桥转换返回核） |
| 03 | AXI_SRAM | 0x2000_0000 | 64KB | 64KB（2^16） | AXI | BLOCK-14 | R/W | AXI_IB | SLVERR（全窗口实现，保留口径） |
| 04 | AXI 保留区 | 0x2001_0000 | 0x1FFF_0000 | 4KB | AXI | — | — | AXI_IB | DECERR |
| 05 | UART | 0x4000_0000 | 4KB | 4KB | AXI | BLOCK-03 | R/W | AXI_IB（经 Lite 转换器） | SLVERR（未实现偏移） |
| 06 | SPI | 0x4000_1000 | 4KB | 4KB | AXI | BLOCK-05 | R/W | AXI_IB（经 Lite 转换器） | SLVERR |
| 07 | IIC | 0x4000_2000 | 4KB | 4KB | AXI | BLOCK-06 | R/W | AXI_IB（经 Lite 转换器） | SLVERR |
| 08 | PWM | 0x4000_3000 | 4KB | 4KB | AXI | BLOCK-07 | R/W | AXI_IB（经 Lite 转换器） | SLVERR |
| 09 | GPIO | 0x4000_4000 | 4KB | 4KB | AXI | BLOCK-08 | R/W | AXI_IB（经 Lite 转换器） | SLVERR |
| 10 | INT | 0x4000_5000 | 4KB | 4KB | AXI | BLOCK-09 | R/W | AXI_IB（经 Lite 转换器） | SLVERR |
| 11 | TIMER | 0x4000_6000 | 4KB | 4KB | AXI | BLOCK-10 | R/W | AXI_IB（经 Lite 转换器） | SLVERR |
| 12 | CLK_RST | 0x4000_7000 | 4KB | 4KB | AXI | BLOCK-11 | R/W | AXI_IB（经 Lite 转换器） | SLVERR |
| 13 | 外设保留区 | 0x4000_8000 | 0x0FFF_8000 | 4KB | AXI | — | — | AXI_IB | DECERR |
| 14 | SPI Flash（外部） | —（无映射） | — | — | — | BLOCK-13 | PIO | 不参与译码 | N/A（经 BLOCK-05 PIO） |
| 15 | 未映射区 | 0x5000_0000 | 0xB000_0000 | 4KB | AXI | — | — | AXI_IB | DECERR |

### 3.2 译码归属与错误响应策略

**两级译码**（arch-008 方案 A）：

1. **RIB 侧译码**（核 RIB 互联，归属边界 BLOCK-01/02，时序契约 C0/C1 细化）：
   `addr < 0x2000_0000`：命中 MEM-01（0x0~0xFFF）→ ROM；其余（MEM-02）→ RIB_ERR（不挂死，FS-016 口径：非法地址报错）。
   `addr ≥ 0x2000_0000`：转发桥（BLOCK-02）→ AXI4 事务。
2. **AXI_IB 译码**（归属随 R6 待 B3，推荐并入 BLOCK-02，arch-008 §3）：
   - `0x2000_0000/64KB` → SRAM 分支（**AXI4 全量**，ADR-025 β）；
   - `0x4000_0000/32KB`（高 18 位比对，8 个 4KB 窗口线性与/或树）→ 外设分支（经 **AXI4→AXI4-Lite 转换器**，AXI_IB glue，归属随 R6 待 B3）；
   - 其余 → default slave 返回 DECERR（含 MEM-04/13/15）。

**错误响应分级（建议，最终口径 B3）**：
- **DECERR**：译码无匹配窗口（MEM-04/13/15 及一切未定义地址）；
- **SLVERR**：窗口内偏移未实现 / 访问属性违规（如写 MEM-01，若 RIB 侧实现该检查）；
- **RIB_ERR**：RIB 域译码失败（MEM-02），由桥转换错误响应返回核（arch-008 §4.2 已含）。

### 3.3 保留区/未映射区策略

- 保留区（MEM-02/04/13）与未映射区（MEM-15）统一"访问报错不挂死"（FS-016，UC-BUS-001/BOOT-002 验证路径）。
- 外设保留区 MEM-13（≈255.5MB @0x4000_8000 起）为后续复用 IP 窗口扩展区（4KB 粒度线性扩展，B6/C0 引入 IP 后重跑冲突检查，见 B2-regmap.md §3）。
- 全空间封闭：mapped 区域并集 = 4GB（0x0 封闭至 0xFFFF_FFFF，脚本校验），无孤儿间隙。

## 4. β 结构映射视角（ADR-025）

### 4.1 外设 8 窗口可达性（0x4000_0000 ~ 0x4000_7FFF）

```
核(BLOCK-01) --RIB-DATA--> 桥(BLOCK-02, RIB从+AXI4主)
  --AXI4--> AXI_IB 译码（0x4000_0000/32KB 命中 → 外设分支）
  --> AXI4→AXI4-Lite 转换器（AXI_IB glue，归属随 R6 待 B3）
       · 单拍化：强制 LEN=0（突发进入寄存器区的处理策略待 B3/C2，ADR-025 留白项）
       · ID 单一化（桥后单 ID，spec-005 §2.2 #5）
       · 插入时延 ≤1 周期（arch-008 §10.2，§4.2 预算裕量 2 周期可吸收 → 外设访问仍 ≤10 ✓）
  --> AXI4-Lite 从机 ×8（BLOCK-03/05/06/07/08/09/10/11，各 4KB 窗口）
```

8 个 4KB 窗口在转换器**之后**由 Lite 侧 4KB 译码区分（窗口连续、等粒度、无空洞，0x4000_0000~0x4000_7FFF），可达性完整；转换器对地址本身透明（地址透传，仅协议降宽）。

### 4.2 SRAM 突发访问窗口属性（MEM-03）

- β 结构下 SRAM 分支**不经转换器**，保留 AXI4 全量突发（ADR-025 决策 2；PPAC-013 加载路径依赖：64KB 顺序写以突发摊薄地址通道开销）。
- 窗口 64KB、2^16 对齐（基址 0x2000_0000）→ 译码可简化为高 16 位比对。
- **AXI4 协议规则**：突发不得跨 4KB 边界——固件加载 64KB 由多个 ≤4KB 对齐突发组成（软件/桥拆分，B3 定突发深度上限后细化）。
- 突发长度（ARLEN/AWLEN）、outstanding 深度、ID 宽度：**B3 量化**（R7，不在 B2 范围）。

## 5. 冲突检查（Measure）

脚本 `AIFlow/scripts/build_addr_map.py`（本节点产出，详章 §4 指定的工具，此前不存在——见 friction log F-B2-01）对 `docs/B2-addr-map.yaml` 执行 7 项检查：两两重叠 / 越界 / 4KB 对齐（基址与大小）/ 功能窗口 2 的幂 / 空间封闭无孤儿间隙 / 每从设备恰一功能窗口 / 非映射器件隔离。**结果：ERROR 0、PASS**（完整报告 `docs/B2-addr-check.txt`）。

生成产物：`rtl/inc/axi_addr_pkg.sv`（地址常量 SV 包）+ `soc/sw/include/soc_addr.h`（C 基址头）。Verilator lint 冒烟因环境无 verilator 不可执行（friction F-B2-02）；退化校验：生成内容为纯 `localparam`/`#define` 常量（无逻辑），语法风险极低，待 E2/工具链就绪后补 lint。

## 6. Measure 度量汇总

| 度量 | 值 |
|------|-----|
| 区域总数 | 15（mapped 14 + 非映射 1），与 spec-005 冻结基线 15 一致 |
| 功能窗口 | 10（ROM 1 + SRAM 1 + 外设 8）；功能窗口覆盖 102400B（0x19000） |
| 冲突（重叠/越界/错译码） | **0**（脚本 PASS） |
| 对齐 | 全区域 4KB 对齐 ✓；SRAM 2^16 对齐（译码简化）✓ |
| 空间封闭 | mapped 并集 = 4GB，无孤儿间隙 ✓ |
| 每从设备窗口 | 恰 1（BLOCK-02 仅承载保留区，非功能窗口）✓ |
| 容量结论 | SRAM 64KB 维持（预算 56KB/64KB，余量 14%）；Boot ROM 4KB 维持（估 3.0KB，裕量 25%） |
| 基线偏差 | **0**（全部基址/大小与 spec-005 冻结值一致，无回写） |
| 译码复杂度 | RIB 侧 1 级（高 1 位 + 4KB 窗口）；AXI 侧 1 级（高 16 位 SRAM + 高 18 位外设 + default） |

## 7. B3 交接项（地址相关）

| # | 事项 | 来源 |
|---|------|------|
| 1 | 错误响应类型统一口径确认：DECERR（译码失败）/ SLVERR（窗口内违规）分级是否采纳（本文 §3.2 建议） | arch-008 §7、本文 §3.2 |
| 2 | 译码归属：AXI_IB 并入 BLOCK-02 vs 独立 glue（R6）及转换器随之归属 | ADR-025 决策 2 留白 |
| 3 | 突发进入寄存器区（0x4000_0000/32KB）的处理策略：转换器直接 SLVERR vs 拆拍 | ADR-025 留白（B3/C2） |
| 4 | SRAM 突发深度上限（ARLEN/AWLEN）/桥 outstanding/ID 宽度量化（R7），及其与 4KB 边界拆分的配合 | ADR-009 决策 1 留白 |
| 5 | RIB 侧译码失败（MEM-02）错误响应的 RIB 协议编码（依赖 C0 核契约） | arch-008 R3 |
| 6 | 转换器插入的 ≤1 周期时延在 PPAC-014 ≤10 预算中的入账确认（裕量 2 周期覆盖） | arch-008 §10.2 |

## 8. DoD 自检（Judge，对照详章 §6）

| DoD 判据 | 证据 | 结论 |
|----------|------|------|
| `build_addr_map.py` 无 ERROR | `docs/B2-addr-check.txt`：ERROR 0，PASS | ✅ |
| 每从设备恰一窗口，无歧义映射 | 脚本检查 6：功能窗口 BLOCK 唯一（10 窗口/10 BLOCK） | ✅ |
| 复用 IP 寄存器空间并入且无冲突 | ip/ 四目录为空，无可并入内容（B2-regmap.md §3 说明，B6/C0 引入后复核） | ✅（附条件说明） |
| 生成产物可编译（verilator lint） | 环境无 verilator：退化校验（纯常量包，无逻辑），待工具链补验 | ⚠️ 附摩擦记录 F-B2-02 |
| 容量有量化依据 | SRAM §1（56/64KB）/ ROM §2（3.0/4KB） | ✅ |
| 不触碰冻结基线 | 全部基址/大小 = spec-005 冻结值；无 spec-005/state-* 修改 | ✅ |

## 9. 变更记录

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| v1.0 | 2026-08-21 | 初版：SRAM/ROM 容量量化（均维持）、15 区域架构级映射表（译码归属/错误响应/β 视角）、冲突检查 PASS、B3 交接 6 项 | arch-agent |
