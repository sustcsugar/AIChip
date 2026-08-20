# AIFlow — 共治管理层

> 本目录收纳本实验的**共治管理层与脚手架**：流程文档、校验脚本、运行状态。
> 芯片设计工作目录 = 仓库根（`docs/`、`rtl/`、`verif/`、`model/`、`build/`、`ip/`、`ip_manifest.json`）。
> `.opencode/`（opencode 的 agent/skill 运行时）保留在仓库根目录——这是 opencode 发现机制的要求（只从当前目录向上到 git 根查找固定目录名 `.opencode/`），详见 `state/state-decisions.md` ADR-012。

## 内容

| 路径 | 内容 |
|------|------|
| `doc/` | 流程定义：`SOP.md` 总纲 + `阶段A–H/` 节点详章 + `辅助文档/`（90/91）+ `设计/`（设计基线） |
| `scripts/` | 工具脚本：scaffold_skills / check_tracker / build_manifest / contract_check / roadmap_check / a1–a3 节点校验 |
| `state/` | 运行状态：state-tracker / state-milestones / state-decisions（ADR）/ state-roadmap（RMP 优化方向） |

## 使用

- 从仓库根启动 opencode（默认 agent = orchestrator），流程入口 `AIFlow/doc/SOP.md`
- 脚本从根目录调用：`python AIFlow/scripts/<script>.py ...`
- 状态文件（tracker / milestones / decisions / roadmap）由 orchestrator 唯一写入
