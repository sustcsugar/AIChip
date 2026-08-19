# AIChip — 人机协同芯片开发实验

验证"人与 AI 协同，完整开发一款可收敛的芯片"的实验工作区。

## 流程入口

- **总纲 SOP**：`doc/SOP.md` — 流程模型、收敛关口、节点索引
- **设计基线**：`doc/2026-08-19-ai-chip-sop-design.md`
- **收敛判据速查**：`doc/90-收敛判据速查表.md`
- **人机职责矩阵**：`doc/91-人机职责分配矩阵.md`

## 如何使用

1. 在本目录启动 opencode，默认 agent 为 `orchestrator`
2. 对 orchestrator 说"开始 X 阶段"或"执行节点 C3"
3. orchestrator 读取 `state/tracker.md` → 派发对应领域 agent → 领域 agent 加载节点 skill 执行
4. 节点产出后校验收敛判据；到质量门停下等待人工签字
5. 两个强制关口：**D7 功能收敛**、**F5 时序收敛**，必须人工签字

## 目录结构

| 路径 | 内容 |
|------|------|
| `doc/` | SOP 总纲 + 节点详章 + 速查表 + 职责矩阵 + 设计文档 |
| `.opencode/skills/` | 节点级 skill（`node-<ID>-<slug>`）+ 跨切面 skill（review-gate / convergence-judge / ip-discipline） |
| `.opencode/agent/` | 7 个 agent：orchestrator + 6 领域 agent |
| `templates/` | 节点输入/输出模板 |
| `scripts/` | 工具脚本（脚手架 / manifest / tracker 校验 / 合同比对） |
| `state/` | 运行状态：tracker / milestones / decisions |
| `work/` | 芯片工作区：`ip/`（复用 IP）+ `soc/`（SoC 集成） |

## 收敛环模型

```
A 需求与规格 → B 架构 → [C 微架构与 RTL ⇄ D 验证] → 关口1 功能收敛
              → [E 综合 ⇄ F STA] → 关口2 时序收敛 → G 签核交付 → H 物理设计(可选)
```

## 人机协同原则

- AI 负责：执行、度量、判据自检、流程编排
- 人类负责：质量门签字、关键决策、异常裁定、EDA 许可环境
- 签字记录在 `state/decisions.md`，是本实验的对照数据

## 开发调试脚本

```bash
python scripts/scaffold_skills.py            # 重新生成节点 skill
python scripts/check_tracker.py --summary    # 查看节点状态
python scripts/build_manifest.py --ips       # 查看 IP 版本固定
python scripts/contract_check.py --list      # 列出 IP
```