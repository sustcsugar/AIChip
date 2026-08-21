# 芯片优化方向 Roadmap（统一待办清单）

> 用途：统一登记开发过程中随时产生的、超出当前收敛范围的优化想法 / 增强方向（下一版芯片、架构备选、流程改进、技术预研）。
> 维护者：orchestrator（唯一写入者，与 state-tracker 纪律一致）。
> 登记时机：① 用户随时提出"记一下 / 待办 / 优化方向 / 下一版可以…"；② **每个节点质量门签核时 orchestrator 必过一遍本清单**（见下）；③ 下一版立项时整体评估。
> **质量门 RMP 联动机制（ADR-019 澄清，2026-08-21）**：每个节点完成、进入质量门时，orchestrator 走查本清单全部条目——**条目"状态"字段是唯一可信源**：`idea` 状态条目若与该节点领域相关，提请评审该条目是否进入评估（planned/rejected/deferred）；`deferred`（如 RMP-001/002，ADR-019）保持跳过直至状态变更；`in_progress/adopted` 检查执行进度。是否评估**只看状态字段**，不看条目内容猜测。
> 条目编号：`RMP-<NNN>` 项目全局递增（**RMP = Roadmap，优化方向条目**，2026-08-20 定义）；登记/校验见 `AIFlow/scripts/roadmap_check.py`。
> 与 OI 的区别：OI 是当前版本规格歧义澄清（必须在当前版本关闭）；Roadmap 是当前版本收敛范围之外的增强 / 未来方向（不阻塞当前版本）。
> **范围裁定（ADR-019，2026-08-21 用户裁定，同日澄清）**：裁定**仅针对当时既有的 RMP-001/002 两条**——不在当前版本芯片实现，作为后续版本优化空间（状态 deferred）；**不是**关闭 roadmap 与当前版本的联动。每个节点质量门仍必须过一遍 RMP 清单，按条目状态决定是否触发评估（见上"质量门 RMP 联动机制"）。

## 条目结构（每条目固定字段）

| 字段 | 说明 |
|------|------|
| 标题 | 一句话命名 |
| 分类 | 下一版增强 / 架构备选 / 流程改进 / 技术预研 |
| 状态 | idea / planned / in_progress / adopted / deferred / rejected |
| 来源 | 提出人 + 日期 + 来源节点/场景 |
| 动机 | 为什么想优化（痛点 / 场景） |
| 方案概述 | 技术方向一句话 |
| 期望收益 | 量化或定性收益 |
| 影响范围 | 涉及的模块 / 文档 / 节点 |
| 关联 | 相关 ADR / OI / M 指标 / 其他 RMP 条目 |
| 处置建议 | 建议在哪评估、下一步动作 |

## Roadmap 条目

### RMP-006 — SystemRDL 作为寄存器全局唯一事实源（技术预研）
- 标题：SystemRDL 作为寄存器全局唯一事实源（PeakRDL 工具链）
- 分类：技术预研（下一版增强候选 / 本版本 C1 前评估）
- 状态：adopted（2026-08-21 用户裁定采用；C1 启动时落地：*.rdl 为寄存器唯一事实源 + peakrdl 工具链；C1/C2/C3/D2 详章与 node-C1 模板已更新，ADR-026）
- 来源：用户，2026-08-21，B2 质量门期间提出
- 动机：寄存器信息当前散落 spec-005 §6（Markdown 冻结初版）/B2-regmap.md，C1/C2/D 阶段将出现 RTL 手写寄存器堆、UVM RAL、固件头文件多处手工对齐，漂移风险高
- 方案概述：Accellera SystemRDL 2.0（业界寄存器描述标准 DSL）+ PeakRDL 开源工具链（pip，纯 Python）：*.rdl 为唯一事实源 → 生成 SV regblock（C3）/ UVM RAL（D2）/ C 头（固件）/ HTML 手册；地址侧维持 B2-addr-map.yaml 或长期演进 RDL addrmap 全覆盖（C0/C1 实践后裁定）
- 期望收益：寄存器单一事实源（ADR-018 同类漂移免疫）；RTL/验证/固件/文档四端自动同步；与 Python 工具链契合
- 影响范围：C1/C2（建立 .rdl）、C3/D2（消费生成物）、spec-005 §6（对照源）、RMP-005（peakrdl 一并装）
- 关联：RMP-005（工具链环境）、ADR-018（单一事实源教训）
- 处置建议：**C0 结束/C1 启动前评估**：若采纳，C1 产物增加 .rdl 定义 + spec-005 §6 对拍校验脚本；B3~B7 不受影响
- 调研报告：本条目即摘要，全文见 2026-08-21 会话（含 IP-XACT/ORDT 对比、迁移路径、风险）

### RMP-005 — 开源 EDA 工具链环境准备（verilator/iverilog 等）
- 标题：开源 EDA 工具链环境准备（verilator/iverilog 等）
- 分类：流程改进
- 状态：planned（2026-08-21 用户裁定：采用 verilator 为仿真工具；C0 前必须 resolved）
- 来源：arch-agent friction log（B2：详章 DoD 要求 verilator --lint-only 冒烟，环境无 verilator/iverilog，退化校验），2026-08-21
- 动机：B2 已出现首次退化校验（生成 SV 包仅做 ASCII/常量断言）；后续 C4/C6/D 阶段全面依赖 verilator+cocotb，E 阶段依赖 yosys，环境不就绪将连环退化
- 方案概述：安装/验证开源工具链（**verilator 为仿真工具**、iverilog、cocotb、yosys，Windows/WSL 方案裁定），输出环境自检脚本（--version 全绿）
- 期望收益：消除仿真/lint 类 DoD 的退化校验；C 阶段前就绪
- 影响范围：开发环境、E2/D2 节点前置
- 关联：ADR-004（开源降级口径）、RMP-003（同属环境类）、RMP-006（peakrdl 一并装）
- 处置建议：**C0 前必须 resolved**，用户提供环境或授权 WSL 安装

### RMP-004 — 勘误/变更影响面管理：主文档↔配套产物配对清单 + 自验范围声明
- 标题：勘误/变更影响面管理：主文档↔配套产物配对清单 + 自验范围声明
- 分类：流程改进
- 状态：adopted（2026-08-21 B1 质量门裁定采纳并落地：governance-retro 机器三查加第 4 查"产物配对一致性"+ 审核附加纪律两条（自验范围声明/变更影响面=配对组）；骨架 Judge 步骤强化自验声明 → 46 skill 再生成）
- 来源：arch-agent friction log（B1 ADR-024 勘误遗漏 CSV），2026-08-21
- 动机：arch-008 勘误只改了 .md，配套 module-list.csv 遗漏同步；agent 自验"通过"掩盖了检查范围不含 CSV 的盲区（检查对 ≠ 变更影响面）
- 方案概述：①节点产物登记"主文档↔配套文件"配对关系（如 md↔csv），勘误 SOP 增加"关键词 grep 于产物配对全组"；②agent 自验报告必须显式声明检查了哪些文件，使范围遗漏可审计
- 期望收益：消除多文件产物的部分勘误风险；自验可审计
- 影响范围：节点 skill Measure/Judge 步骤措辞、governance-retro 审核表、文档登记表结构（可选加配对列）
- 关联：ADR-023（friction log 机制）、ADR-024（本次勘误根因）
- 处置建议：任一质量门评估后改 planned；最小实现为 governance-retro 审核表加"产物配对一致性"检查行

### RMP-003 — 校验脚本 Windows 控制台中文乱码（输出编码统一 UTF-8）
- 标题：校验脚本 Windows 控制台中文乱码（输出编码统一 UTF-8）
- 分类：流程改进
- 状态：adopted（2026-08-21 B1 质量门裁定全量解决，已落地：7 个脚本统一 stdout/stderr reconfigure UTF-8，GBK 控制台冒烟 10/10 通过；落地节点 B1）
- 来源：arch-agent friction log（B1 执行），2026-08-21
- 动机：check_tracker.py 等校验脚本在 Windows GBK 控制台输出中文乱码（如 scaffold 脚本曾因 ⚠ 字符 UnicodeEncodeError 崩溃），影响人机协同可读性与脚本健壮性
- 方案概述：AIFlow/scripts/ 全部脚本统一 stdout/stderr 强制 UTF-8（`sys.stdout.reconfigure(encoding="utf-8")` 或 PYTHONIOENCODING 约定），消除平台差异
- 期望收益：脚本输出跨平台可读；杜绝编码崩溃
- 影响范围：AIFlow/scripts/*.py（约 10 个）、skill-scaffold/scripts
- 关联：ADR-023（friction log 机制首次产出）
- 处置建议：任一质量门评估后改 planned，一次性批量修复（30 分钟级）

### RMP-001 — 内存映射 SPI Flash 访问（MMIO 只读窗口 / XIP）
- 标题：内存映射 SPI Flash 访问（MMIO 只读窗口 / XIP）
- 分类：下一版增强（架构备选）
- 状态：deferred（下一版；ADR-019 裁定不进入当前版本）
- 来源：用户，2026-08-20，A3 签核后提出
- 动机：当前 Flash 仅 PIO 访问，CPU 需软件驱动 SPI 寄存器逐字节搬数据；希望 CPU 像读内存一样直接访问外部 Flash 内容
- 方案概述：增加内存映射 Flash 控制器，把 SPI Flash 内容映射为 MMIO 只读窗口（AXI 从端口）；CPU load 命中窗口时控制器自动执行 SPI 读命令并返回数据；读走 MMIO、写/擦除仍走寄存器（PIO）；可选 XIP（代码直接在 Flash 执行）与缓存/预取
- 期望收益：免软件搬运；大数据读取（配置表/字库/只读常量）编程简化；XIP 可省启动拷贝
- 影响范围：BLOCK-05 扩展或新增 BLOCK-15；spec-005 新增 MMIO 只读窗口（可挂 0x5000_0000 未映射区）；spec-004 PPAC 表（新增 XIP/读带宽指标）；B1/B3（缓存/预取/线宽）；C1/C2（控制器微架构/契约）；A3 已冻结需走变更流程
- 关联：ADR-009（高速 SPI 待 B1）；RMP-002（高速 SPI）；PPAC-006/PPAC-013；OI-A3-006（已关闭）
- 处置建议：**下一版立项时**与 RMP-002 合并评估（架构评审 + 建模量化"无缓存 MMIO vs 带缓存"的带宽/面积/启动时延收益）；若采纳进入下一版 PRD（增补 REQ 走 OI 流程）

### RMP-002 — 高速 SPI（QSPI / 160MHz 级）
- 标题：高速 SPI（QSPI / 160MHz 级）
- 分类：架构备选（下一版增强）
- 状态：deferred（下一版；ADR-019 裁定不进入当前版本）
- 来源：用户，2026-08-20，A3 签核讨论中提出
- 动机：当前单线 SPI SCLK ≤ 12.5 MHz（Fsys/4），启动与大数据读带宽受限；QSPI NOR Flash 器件可达 104–166 MHz
- 方案概述：SPI 升级为 QSPI（x4）并提高 SCLK（需独立 SPI 时钟/PLL 或提高 Fsys）；与 RMP-001 XIP 配套可构成完整高速 Flash 通路
- 期望收益：读带宽 ×4~×16；启动时延可从 ~60ms 降至 ms 级；支撑 XIP
- 影响范围：BLOCK-05（SPI master）、BLOCK-11（时钟架构：单域 → 独立 SPI 时钟域）、PPAC-006、A3 引脚（新增 IO2/IO3）、B1/B3/B4
- 关联：ADR-009（160MHz 待 B1 评估，随本裁定转为下一版评估）；RMP-001；PPAC-006/PPAC-013
- 处置建议：**下一版立项时**与时钟架构一并评估；若上 160MHz 需同步修订 PPAC-006/BLOCK-05 并触发 A3 变更流程

## 状态流转规则

```
idea →（评估后）→ planned / adopted / deferred / rejected
```

- adopted：折入当前或下一版 PRD（增补 REQ 走 OI 流程），条目标注 adopted 并登记落地节点
- deferred：延后，保留条目
- rejected：标注原因，保留留档（登记即留档，不删除）
- 评估入口（ADR-019 澄清）：**每个节点质量门**走查清单，`idea` 且领域相关 → 提请评估；`deferred` → 跳过（除非用户/评审主动改状态）；状态字段为唯一可信源。下一版立项时对全部条目整体复评
