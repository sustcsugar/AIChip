# 人机协同芯片开发实验 — SOP 与 Agent/Skill 体系设计

- 日期：2026-08-19
- 状态：已确认（设计基线）
- 目标：验证"人与 AI 协同，完整开发一款可收敛的芯片"

## 1. 实验定义

- **收敛标准**：功能正确（功能覆盖率达标 + 回归全绿）+ 综合后时序收敛（STA WNS/TNS ≥ 0）
- **工具链**：混合 — RTL 验证用开源（Verilator/cocotb/UVM 等），后端用商用工具（DC/GENUS/Primetime，人机协同脚本）
- **流程模型**：收敛环迭代模型 + 两个强制收敛关口（功能收敛关口 D7、时序收敛关口 F5）
- **Agent 组织**：6 个领域 agent + 1 个编排者（orchestrator）
- **芯片形态**：SoC + IP 复用架构（子系统/子模块作为独立可复用项目开发）

## 2. 收敛环流程模型

```
治理层 G0：状态跟踪 / 收敛看板 / 里程碑 / 评审门控（贯穿全程）
  │
  ▼
A 需求与规格 → B 架构与集成规划      （规划期，文档密集）
  │
  ▼
C 微架构与 RTL ←→ D 验证             （功能收敛环 Loop 1）
  │                    │   bug 反馈
  ▼  关口1：功能收敛（D7 验证签核）
E 综合与约束 ←→ F STA 时序           （时序收敛环 Loop 2）
  │                    │   违例修复/约束校正（可回退改 RTL）
  ▼  关口2：时序收敛（F5 签核）
G 签核与交付 → H 物理设计（可选扩展）
```

每个阶段内部：Plan → Execute → Measure → Judge（收敛判据）→ Iterate/Release。

## 3. 节点树

### 阶段 A 需求与规格

| ID | 节点 | 关键输出产物 | 收敛判据（DoD） |
|----|------|-------------|----------------|
| A1 | 需求与场景定义 | PRD、用例清单 | 场景无未决 open issue |
| A2 | 系统规格 | 系统规格书（功能/性能指标） | 指标可量化、可测试 |
| A3 | 接口规格 | 引脚/总线/中断/存储映射规格 | 接口清单冻结 |
| A4 | 需求可追溯矩阵 | RTM | RTM 双向覆盖 100% |
| A5 | 规格评审冻结 | 评审纪要、Spec v1.0 | 规格冻结，评审签字 |

### 阶段 B 架构与集成规划

| ID | 节点 | 关键输出产物 | 收敛判据（DoD） |
|----|------|-------------|----------------|
| B1 | 系统架构 | 顶层框图、模块划分 | 架构冻结 |
| B2 | 地址映射 | Memory map | 无地址冲突 |
| B3 | 总线与互联选型 | 互联架构说明 | 选型有量化依据 |
| B4 | 性能/面积/功耗建模 | 估算报告 | 估算满足 A2 指标 |
| B5 | 架构评审 | 评审纪要 | 架构冻结，签字 |
| B6 | 集成规划 | IP 选型表（自研/复用）、版本基线、复用策略 | 每个功能块明确来源 |
| B7 | 参考模型开发 | 系统级/模块级 golden 模型、模型规格、冻结版本 | 模型行为与规格一致，冻结为 golden |

### 阶段 C 微架构与 RTL

| ID | 节点 | 关键输出产物 | 收敛判据（DoD） |
|----|------|-------------|----------------|
| C0 | IP 接入与合同验证 | 合同检查报告、manifest 固定、SoC 集成规格 | 接口/regmap/复位/时钟/中断与 SoC 一致，版本已 pin |
| C1 | 微架构规格 | 每模块微架构说明 | 状态机/握手/流水线完整 |
| C2 | 模块接口契约 | 接口定义文档 | 接口契约无歧义 |
| C3 | RTL 编码 | RTL 源码 | 编码规范达标 |
| C4 | Lint 检查 | lint 报告 | 无 blocker/warning 清零 |
| C5 | CDC 检查 | CDC 报告 | 无 CDC 违例 |
| C6 | 模块级 smoke | 自测结果 | 模块级仿真通过 |
| C7 | RTL 冻结 | RTL freeze tag | feature complete |

### 阶段 D 验证（功能收敛环）

| ID | 节点 | 关键输出产物 | 收敛判据（DoD） |
|----|------|-------------|----------------|
| D1 | 验证计划 | vplan（测试点/场景/覆盖率目标） | 测试点→需求覆盖 |
| D2 | TB/环境搭建 | UVM/cocotb 环境 | 编译运行通过 |
| D3 | 定向测试 | 定向用例集 | 用例全过 |
| D4 | 约束随机/自动化 | 随机用例 | 无未预期崩溃 |
| D5 | 断言与形式化 | 断言/formal 结果 | 断言无失败 |
| D6 | 回归与覆盖率收敛 | 覆盖率报告 | 功能+代码覆盖率达标 |
| D7 | 验证签核 | RCR 清单 | 关口1：无未决 RCR |

### 阶段 E 综合与约束

| ID | 节点 | 关键输出产物 | 收敛判据（DoD） |
|----|------|-------------|----------------|
| E1 | 约束开发 | SDC | 约束与规格一致 |
| E2 | 库/环境设置 | 综合环境配置 | 库读入无误 |
| E3 | 逻辑综合 | netlist | 综合 DRC clean |
| E4 | 综合后 DRC | 时序 DRC 报告 | max_trans/cap/fanout clean |
| E5 | 形式验证（LEC） | 等价性报告 | RTL↔netlist 等价 |
| E6 | 门级仿真（可选） | 门级 smoke 结果 | 无 mismatch |

### 阶段 F STA 时序收敛

| ID | 节点 | 关键输出产物 | 收敛判据（DoD） |
|----|------|-------------|----------------|
| F1 | 约束签核评审 | SDC 签核评审 | 约束质量确认 |
| F2 | STA 分析 | 多模式多角 STA 报告 | 违例已全量列出 |
| F3 | 违例修复 | 修复后的时序报告 | WNS/TNS ≥ 0（或达标） |
| F4 | 功耗估算（可选） | 功耗报告 | 满足预算 |
| F5 | 时序收敛评审 | 签核报告 | 关口2：时序收敛签字 |

### 阶段 G 签核与交付

| ID | 节点 | 关键输出产物 | 收敛判据（DoD） |
|----|------|-------------|----------------|
| G1 | 交付物打包 | 交付包（RTL/netlist/SDC/文档/报告） | 交付物清单齐全 |
| G2 | 收敛双签核 | 收敛报告 | 功能+时序双收敛确认 |
| G3 | 基线归档 | Git release tag | 基线冻结 |

### 阶段 H 物理设计（可选扩展）

| ID | 节点 | 关键输出产物 | 收敛判据（DoD） |
|----|------|-------------|----------------|
| H1 | Floorplan | floorplan | 面积/利用率达标 |
| H2 | Place & Route | 布局布线结果 | DRC clean |
| H3 | CTS | 时钟树 | CTS DRC clean |
| H4 | Signoff STA | 签核时序报告 | WNS/TNS ≥ 0 |
| H5 | 物理验证 | DRC/LVS 报告 | clean |

## 4. 两层项目模型（IP 复用嵌入）

- **IP 项目层**：mipi/usb/ddr/axi_uart 等独立收敛单元，自带 rtl/AIFlow/doc/tb/vip/model/constraint/RELEASE.md，收敛到 D7 签核即发布 tag。
- **SoC 项目层**：集成收敛单元，通过 `soc/ip_manifest.json` 固定 IP 版本（只读消费），自研 glue 逻辑（复位/时钟/中断仲裁/pinmux）。
- **验证策略**：早期集成用 `mode: model`（行为模型），签核前切 `mode: rtl`（真实 RTL 全量回归）。
- **硬性纪律（ip-discipline）**：任何 agent 不得修改 manifest 锁定的 IP 源码，改动走 IP 项目新版本。

```json
// soc/ip_manifest.json
{
  "soc_version": "soc_v0.3",
  "ips": {
    "mipi_dsi": { "path": "ip/mipi", "version": "mipi_v1.2", "mode": "rtl" },
    "usb":      { "path": "ip/usb",  "version": "usb_v2.0",  "mode": "rtl" },
    "ddr":      { "path": "ip/ddr",  "version": "ddr_v1.5",  "mode": "rtl" },
    "axi_uart": { "path": "ip/axi_uart", "version": "au_v0.9",  "mode": "rtl" }
  }
}
```

## 5. 两级验证环境区分

| | 模块级验证 `ip/<ip>/tb` 或 `verif/block/` | 系统级验证 `verif/sys/` |
|---|---|---|
| DUT | 单个模块 | 顶层 soc_top |
| 依赖 | 行为模型/VIP（来自 `verif/common/`） | 真实总线 VIP + memory model |
| 目的 | 模块独立收敛 | 集成收敛（互联/仲裁/复位/中断） |
| 归属 | C 阶段（C3–C6） | D 阶段（D1–D7） |

关键约束：block TB 不实例化其他设计模块；sys TB 只实例化 soc_top。

## 5.1 参考模型与 Scoreboard（B7 → D 阶段）

- **B7 参考模型开发**（B 阶段）：系统级模型 `model/sys/` + 模块级模型 `model/block/<mod>/`（模块级统一用 `block` 命名），IP 自带模型随 IP 交付（`ip/<ip>/model/`，对应 manifest `mode: model`）。
- **双重用途**：前期算法/性能评估（B 阶段）；后期作为 golden 比对数据（D 阶段）。
- **Scoreboard 集成**（D2）：两级环境各实例化 `DUT + 参考模型 + scoreboard`，同激励驱动、输出自动比对。
- **收敛判据**（D6/D7）：全量回归中 scoreboard 比对 **mismatch = 0** 纳入功能收敛判据，实现仿真自检闭环。

## 6. Agent 架构

| Agent | 负责阶段 | 挂载 skills | 关键职责 | 输出落点 |
|-------|---------|------------|---------|---------|
| orchestrator | 全局 | review-gate, convergence-judge | 维护收敛看板、按 SOP 调度、收敛判据检查、评审门控、决策记录 | AIFlow/state/* |
| spec-agent | A (A1–A5) | node-a1…a5 | PRD/系统规格/接口规格/RTM | AIFlow/doc/*, 根目录产物（docs/ rtl/ verif/ ip/ 等） |
| arch-agent | B (B1–B7) | node-b1…b7 | 架构、memory map、总线选型、B6 集成规划、B7 参考模型 | AIFlow/doc/*, 根目录产物（docs/ rtl/ verif/ ip/ 等） |
| rtl-agent | C (C0–C7) | node-c0…c7, ip-discipline | 微架构规格、C0 IP 合同验证、RTL 编码、lint/CDC、模块 smoke、freeze | work/*/rtl |
| verify-agent | D (D1–D7) | node-d1…d7 | vplan、TB、用例、覆盖率收敛、model↔rtl 切换、子系统集成验证 | ip/*/verif 与根 verif/ |
| syn-agent | E (E1–E6) | node-e1…e6 | SDC、综合脚本、综合、LEC、门级仿真 | soc/syn |
| signoff-agent | F+G (F1–F5, G1–G3) | node-f1…f5, node-g1…g3 | STA 分析、违例修复协调、交付打包、双签核 | soc/sta, 交付包 |

- orchestrator 不写设计/验证代码，只做调度 + 判据检查。
- 领域 agent 只在 orchestrator 批准后进入节点。

## 7. Skill 组织

- **节点级**：每个 SOP 节点一个 skill，命名 `node-<id>-<name>`。SKILL.md 模板：目的/输入产物/执行步骤/工具调用/收敛判据检查/输出产物/人机职责分配。
- **跨切面**：`review-gate`（质量门评审）、`convergence-judge`（收敛判据检查）、`ip-discipline`（IP 只读纪律）。
- **生成机制**：`skill-scaffold`（orchestrator 自带能力）——`nodes.json` × 骨架模板 → `scaffold_skills.py` 批量生成，避免格式漂移。

## 8. 状态跟踪

```
AIFlow/state/state-tracker.md   ← orchestrator 唯一写入者
[ C3 RTL编码 ] 状态=in_progress | waiting_review | passed | iterating
  收敛指标: lint=0 违例, 覆盖率=85%, 版本次数=2
  质量门: 待人工签字
```

配套 `AIFlow/scripts/check_tracker.py` 校验节点前后置条件。

## 9. 项目目录骨架

```
D:\work\AIChip\
├── opencode.json                     # default_agent=orchestrator + instructions(AIFlow/doc/SOP.md)
├── README.md                         # 实验说明（芯片工作目录入口）
├── .gitignore
├── .opencode/                        # ★ opencode 运行时配置（保留根目录：发现机制要求，ADR-012）
│   ├── skills/                       # 节点级 + 跨切面 skill（自动加载）
│   │   ├── skill-scaffold/SKILL.md       # orchestrator 专用：节点 skill 生成能力（ADR-014/015）
│   │   │   ├── assets/node-template/     # 骨架模板 + 节点详章模板
│   │   │   ├── scripts/scaffold_skills.py
│   │   │   └── references/nodes-schema.md
│   │   ├── node-<id>-<slug>/SKILL.md     …（每节点一个；专属模板内化于各 skill assets/templates/）
│   │   ├── _shared/templates/            # 跨节点共享模板（单一归属）
│   │   │   ├── review-checklist.md  adr-template.md
│   │   │   ├── convergence-report.md  ip_manifest.json
│   │   ├── review-gate/SKILL.md
│   │   ├── convergence-judge/SKILL.md
│   │   └── ip-discipline/SKILL.md
│   └── agent/                        # ★ 7 个 agent（自动加载）
│       ├── orchestrator.md
│       └── spec-agent.md  arch-agent.md  rtl-agent.md
│           verify-agent.md  syn-agent.md  signoff-agent.md
├── AIFlow/                           # ★ 共治管理层（文档/脚本/状态）
│   ├── doc/
│   │   ├── SOP.md                    # 主 SOP：流程模型 + 收敛关口 + 节点索引
│   │   ├── 阶段A–H/                  # 节点详章平铺（每节点一文件）
│   │   ├── 辅助文档/（90-收敛判据速查表、91-人机职责分配矩阵）
│   │   └── 设计/2026-08-19-ai-chip-sop-design.md   # 本设计文档
│   ├── scripts/                      # 工具脚本（scaffold 已内化至 skill-scaffold）
│   │   ├── workflow_audit.py         # 流程骨架审计（W1-W18）
│   │   ├── build_manifest.py         # 解析 manifest → 文件列表
│   │   ├── check_tracker.py          # 节点前后置/收敛判据校验
│   │   └── contract_check.py         # IP 接口合同比对
│   └── state/                        # 运行状态（orchestrator 写入）
│       ├── state-tracker.md  state-milestones.md  state-decisions.md  state-roadmap.md
├── docs/                             # ★ 芯片设计文档（SoC 项目层）
│   ├── 00-文档编号登记.md
│   └── spec/  …（spec-001~005 等）
├── ip/                               # ★ 复用 IP 项目层（独立收敛）
│   └── {mipi, usb, ddr, axi_uart}/
├── rtl/  verif/  model/  build/      # 芯片设计工作目录
└── ip_manifest.json                  # IP 版本固定 manifest（path 指向 ip/）
```

## 10. 使用流程

1. 项目根启动 opencode，默认 agent = orchestrator。
2. orchestrator 读 AIFlow/state/state-tracker.md → 决定当前节点 → 派发领域 agent（subagent）→ 加载节点 skill → 执行 → 产物写根目录对应路径（docs/ rtl/ verif/ ip/ 等）。
3. check_tracker.py 校验收敛判据 → 更新 tracker → 质量门处停下等人工签字。
4. 判据不满足则节点置回 iterating，重新派发修复。

## 11. 待实现清单

1. AIFlow/doc/SOP.md（总纲）+ AIFlow/doc/ 节点详章（每节点一文件）
2. .opencode/skills/skill-scaffold（骨架模板 + scaffold 脚本 + nodes 规范）+ 全部节点 skill
3. .opencode/agent/ 7 个 agent 定义
4. AIFlow/scripts/ AIFlow/state/ 初始文件（节点/共享模板内化至 .opencode/skills/ 资产，无顶层 templates/）
5. README.md（含对照实验记录方法）
6. opencode.json（default_agent 等）