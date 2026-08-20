# 共享模板（跨节点 / 跨切面）

> 本目录是**跨节点共享模板**的唯一事实源（见 `state/state-decisions.md` ADR-011）。
> 单节点专属模板内化于对应 node skill 的 `assets/templates/`，**不**放在这里。
> 维护者：orchestrator（唯一写入，与 state-tracker / state-roadmap 纪律一致）。

## 当前清单

| 模板 | 用途 | 用法持有者 |
|------|------|-----------|
| `review-checklist.md` | 质量门评审检查清单 | review-gate skill；所有 `gate: 评审/人工签字` 节点详章 |
| `adr-template.md` | 关键决策 ADR 条目格式 | `state/state-decisions.md`（orchestrator 登记） |
| `convergence-report.md` | 收敛双签核报告结构 | D7 验证签核、G2 收敛双签核；convergence-judge skill |
| `ip_manifest.json` | IP 版本固定 manifest 初始结构（示例） | B6 集成规划、C0 合同验证；ip-discipline skill |

## 使用方式

- skill / 详章以仓库根相对路径引用：`.opencode/skills/_shared/templates/<文件名>`
- 使用前先复制为工作文件，不在本目录内直接填写产物
- 运行时产物（如 `work/soc/ip_manifest.json`）保持在工作区，本目录只放模板示例

## 维护纪律

1. 新增/修改共享模板：orchestrator 登记（必要时记 ADR），并同步更新本清单表
2. 单节点模板优先内化到对应 skill 的 `assets/templates/`；只有被 ≥2 个节点/切面共用时才提升到本目录
3. 删除模板需在 ADR 留痕（登记即留档，不静默删除）
