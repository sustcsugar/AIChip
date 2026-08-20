# AIChip — 人机协同芯片开发实验

验证"人与 AI 协同，完整开发一款可收敛的芯片"的实验工作区。

## 流程入口

- **总纲 SOP**：`AIFlow/doc/SOP.md` — 流程模型、收敛关口、节点索引
- **设计基线**：`AIFlow/doc/设计/2026-08-19-ai-chip-sop-design.md`
- **收敛判据速查**：`AIFlow/doc/辅助文档/90-收敛判据速查表.md`
- **人机职责矩阵**：`AIFlow/doc/辅助文档/91-人机职责分配矩阵.md`

## 如何使用

1. 在本目录启动 opencode，默认 agent 为 `orchestrator`
2. 对 orchestrator 说"开始 X 阶段"或"执行节点 C3"
3. orchestrator 读取 `AIFlow/state/state-tracker.md` → 派发对应领域 agent → 领域 agent 加载节点 skill 执行
4. 节点产出后校验收敛判据；到质量门停下等待人工签字
5. 两个强制关口：**D7 功能收敛**、**F5 时序收敛**，必须人工签字

## 目录结构

> 根目录 = **芯片设计工作目录**；共治管理层与脚手架统一收纳于 `AIFlow/`。

| 路径 | 内容 |
|------|------|
| `docs/` | 芯片设计文档（SoC 项目层）：`spec/`、RTM、vplan 等，编号登记 `docs/00-文档编号登记.md` |
| `rtl/` `verif/` `model/` `build/` | 芯片设计工作目录：RTL 源码、验证环境、参考模型、综合构建 |
| `ip/` | 复用 IP 项目层（axi_uart/ddr/mipi/usb，独立收敛） |
| `ip_manifest.json` | IP 版本固定 manifest（B6 生成初版、C0 固定版本） |
| `AIFlow/` | 共治管理层：`doc/`（SOP + 阶段详章 + 辅助文档 + 设计基线）、`scripts/`（校验/脚手架脚本）、`state/`（tracker / milestones / decisions / roadmap） |
| `.opencode/` | opencode 运行时配置：节点级 + 跨切面 skill（`skills/`，模板资产随 skill 内化）、7 个 agent（`agent/`）。**保留在根目录**（opencode 发现机制要求，见 ADR-012） |

## 收敛环模型

```
A 需求与规格 → B 架构 → [C 微架构与 RTL ⇄ D 验证] → 关口1 功能收敛
              → [E 综合 ⇄ F STA] → 关口2 时序收敛 → G 签核交付 → H 物理设计(可选)
```

## 人机协同原则

- AI 负责：执行、度量、判据自检、流程编排
- 人类负责：质量门签字、关键决策、异常裁定、EDA 许可环境
- 签字记录在 `AIFlow/state/state-decisions.md`，是本实验的对照数据

## 开发调试脚本

```bash
python .opencode/skills/skill-scaffold/scripts/scaffold_skills.py   # 重新生成节点 skill（orchestrator）
python AIFlow/scripts/check_tracker.py --summary    # 查看节点状态
python AIFlow/scripts/build_manifest.py --ips       # 查看 IP 版本固定
python AIFlow/scripts/contract_check.py --list      # 列出 IP
python AIFlow/scripts/roadmap_check.py           # 校验优化方向 roadmap 结构
```