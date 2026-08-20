# 工作流审查报告 — 2026-08-21

- 触发原因：架构/目录/治理层变更后全量回归审查（ADR-012 目录重构 + ADR-011 模板内化后首次全量审查）
- 审查范围：全量 — 46 节点 + 7 agent + 全部 skill（node-* / 跨切面 / workflow-audit）+ AIFlow/doc 深度资产（SOP/详章/90/91/92/设计基线）
- 审查机制：workflow-audit skill（ADR-013）规则化产出，`python AIFlow/scripts/workflow_audit.py` W1-W17 可复现

## 1. 机械层结果

| # | 检查 | 命令 | 退出码 | 结论 |
|---|------|------|--------|------|
| M1 | 流程骨架审计（W1-W17） | `python AIFlow/scripts/workflow_audit.py` | 0 | 通过（Blocker=0 Warning=0 Info=1） |
| M2 | 节点依赖与判据 | `python AIFlow/scripts/check_tracker.py` | 0 | 通过（46 节点前后置满足） |
| M3 | Roadmap 结构 | `python AIFlow/scripts/roadmap_check.py` | 0 | 通过（2 个 RMP 条目，编号唯一连续） |
| M4 | 脚手架一致性 | 含于 M1（W10） | 0 | 通过（排除 7 个已知定制 skill） |
| M5 | 节点产物校验 | a1/a2/a3_check_*.py | 0 | 全部 PASS（结构检查通过，待人工评审签字） |

> M1 的 W14 Info（`C3-编码规范.md` 为非节点支撑文档）属预期，仅留档，不构成问题。

## 2. 结构不变量

- [x] N1 节点四层对应 — 46 节点均有 详章 + skill + 归属 agent + DoD + gate + tracker 条目（证据：M1 W2-W8 全过）
- [x] N2 强制关口 — D7 与 F5 的 gate 均为 `人工签字`（证据：nodes.json + SOP §3 关口表）
- [x] N3 收敛环 — Loop1（C⇄D 功能环）与 Loop2（E⇄F 时序环）定义于 SOP §2（证据：SOP §2 收敛环模型）
- [x] N4 两层项目模型 — `ip/`（IP 项目层）与根目录（SoC 项目层）经 `ip_manifest.json` 关联，path 指向 `ip/`（证据：build_manifest.py 解析正常）
- [x] N5 引用完整性 — 无悬空路径（证据：M1 W9/W11 全过）
- [x] N6 辅助文档覆盖 — 90/91 覆盖 46 节点、92 覆盖核心缩写（证据：M1 W15/W16/W17 全过）

## 3. 控制流

- [x] C1 前置依赖 — 节点前置必须全部 passed 才能 in_progress（证据：M2 check_tracker 通过，tracker 前置无悬空引用）
- [x] C2 质量门 — 人工签字为唯一放行；A1/A2/A3 签字记录已在 state-decisions.md 评审记录表（证据：M1 W8 + decisions 评审表）
- [x] C3 状态机合法 — 状态值均在 {pending, in_progress, waiting_review, passed, iterating}；A 阶段阶段汇总已修正为 3 passed / 2 pending（证据：M1 W8）
- [x] C4 签核留痕 — D7/F5/G2 尚未执行（A 阶段进行中，属正常）；A1-A3 评审记录在档（证据：decisions.md）
- [x] C5 归档纪律 — state-* 文件由 orchestrator 唯一写入，命名遵循 ADR-007（证据：目录审计）

## 4. 语义层（AI 判断 · 需人工复核）

| 项 | 判断 | 依据 | 建议 |
|----|------|------|------|
| S1 流程模型 vs 实际执行 | 目录迁移后 SOP/README/AIFlow/opencode.json 口径一致，未发现模型与执行偏离 | 全量引用扫描 + 人工比对 | 在真实 opencode 会话中实测 agent/skill 加载后确认 |
| S2 节点划分合理性 | 46 节点归属结构一致；B7 已归 arch-agent 并修复职责声明 | M1 W6 + 人工复核 | 无需调整 |
| S3 控制流遗漏分支 | 回退路径（iterating→修复→复审）与可选阶段 H（signoff-agent 承接）已定义 | SOP §2/§3 + signoff-agent 职责 | 无需调整 |
| S4 术语规范 | RT→RMP 残留已清理；92-术语表已建立并纳入 W17 校验 | 全库扫描 + M1 W17 | 后续新增缩写先登记（orchestrator 纪律） |
| S5 语义一致性 | 编号体系 ADR-008 在 spec-004 落地；本次迁移未改产物语义 | spec-004 + ADR-008 比对 | 无需调整 |

## 5. 问题清单

| 严重级 | 类型 | 项 | 问题 | 处置 |
|--------|------|-----|------|------|
| Warning | 资产 | W6 | arch-agent 职责声明遗漏 B7（描述/职责/加载清单三处只到 B6） | 已修复 |
| Warning | 资产 | W6 | signoff-agent 描述遗漏 H1-H5 范围 | 已修复 |
| Warning | 资产 | W8 | tracker 阶段汇总 A 行失实（"全部 pending" vs 实际 3 passed） | 已修复 |
| Warning | 资产 | — | roadmap-capture / state-roadmap / ADR-010 残留旧缩写 RT（未随改名同步） | 已修复（统一 RMP + ADR 留痕） |
| Warning | 资产 | — | orchestrator 职责编号重复（两个 6） | 已修复（6/7） |
| Warning | 工具 | W8/W16/W17 | 审计脚本正则缺陷（`\s*` 回溯致负向前瞻误判；91 矩阵/复合缩写解析不全） | 已修复（审计脚本自身） |
| Info | 资产 | W14 | C3-编码规范.md 为非节点支撑文档 | 留档（预期，不构成问题） |

## 6. 结论

- **Blocker: 0 / Warning: 0 / Info: 1**（修复后终态；W14 属预期留档）
- **放行建议：通过** — 机械层 / 结构不变量 / 控制流全绿；语义层 S1-S5 为 AI 判断，需人工复核后作为最终确认
- 审查机制自检：workflow-audit skill 已按模板产出本报告，流程可复现（`python AIFlow/scripts/workflow_audit.py` 退出码 0）
- 签字：____  日期：____

---

## 后续修正记录

| 日期 | 事项 | 处置 |
|------|------|------|
| 2026-08-21 | 用户指出 W/M/N/C/S 规则编号未登记 92-术语表（违反"新增缩写先登记后使用"纪律，本报告第 4 节 S4 语义项未覆盖审计规则自身编号） | 92-术语表新增"四、审查规则编号"章节（W1-W18 明细 + M/N/C/S 前缀表）；workflow_audit.py 新增 W18 自一致性规则（脚本 W 编号与术语表一一对应，防止此类遗漏复发） |
