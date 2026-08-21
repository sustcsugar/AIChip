# 规格评审纪要（A5 节点）— 阶段 A 收口

> 节点 A5：规格评审冻结 | 日期：2026-08-21 | 归属 agent：spec-agent
> 评审清单：`.opencode/skills/_shared/templates/review-checklist.md`
> 前置：A1/A2/A3/A4 = passed（tracker 确认）

## 1. 评审范围与材料包

| 产物 | 路径 | 状态 |
|------|------|------|
| PRD（REQ 20） | `docs/spec/spec-001-PRD.md` | A1 passed |
| 使用场景/用例（SC 12 / UC 32） | `docs/spec/spec-002-use-cases.md` | A1 passed |
| Open Issue（OI 全关闭） | `docs/spec/spec-003-open-issues.md` | A1 passed |
| 系统规格（FS 20 / M 20） | `docs/spec/spec-004-system-spec.md` (+csv) | A2 passed |
| 接口规格（总线/引脚/中断/存储） | `docs/spec/spec-005-interface-spec.md` (+csv×3) | A3 passed |
| RTM 双向矩阵（20×40×34） | `docs/spec/spec-006-rtm.md` (+report) | A4 passed |

## 2. 预审结果（review-checklist 逐项）

### 通用项
- [x] 产出物齐全，路径与命名符合 SOP（spec-NNN-*，ADR-003 编号登记齐全）
- [x] 内容与输入规格/需求一致（可追溯）— RTM 双向覆盖 100%（REQ→SPEC 20/20、REQ→TP 20/20、反向 40/40、34/34）
- [x] 无占位符/空章节/未决 TODO（全库扫描通过；"待定"均为有意标注：工艺/B6 C0 归属）
- [x] 异常与边界情况已覆盖（UC 含正常/边界/异常三路径；A1-D5 校验 PASS）
- [x] 收敛判据（DoD）全部达标并有证据（a1/a2/a3/a4 校验脚本全部 PASS）
- [x] 遗留问题已列出（见 §3 Non-blocking 清单）

### 阶段特定项（规格类）
- [x] 指标可量化、可测试（spec-004 PPAC 表四要素：目标值/单位/测试方法/来源需求，a2_check_ppac PASS）
- [x] RTM 双向覆盖（a4_check_rtm.py：双向 100%，孤儿 0）

### 客观证据汇总

| 校验脚本 | 结果 |
|----------|------|
| `a1_check_req.py` | PASS（REQ 20 / SC 12 / UC 32 / OI 0） |
| `a2_check_ppac.py` | PASS（FS 20 / PPAC 20 四要素 100%） |
| `a3_check_interface.py` | PASS（冲突零、遗漏空、UC 覆盖 32/32） |
| `a4_check_rtm.py` | PASS（双向覆盖 100%，孤儿 0） |

## 3. 问题清单与分级

### Blocking（必须关闭才能冻结）：**0 项**

### Non-blocking 遗留项（不阻塞冻结，记录影响/责任人/目标节点）

| # | 遗留项 | 影响 | 责任人 | 目标节点 | 关联 |
|---|--------|------|--------|---------|------|
| N1 | 工艺/库未定（OI-A1-004） | E/F 阶段降级口径，正式 STA 待补 | 用户 | E2 库环境 | ADR-004 |
| N2 | tinyRISCV 版本 pin + Debug Module 对 JTAG 影响 | 核接入细节未定 | C0 合同验证 | C0 / B6 | REQ-001/004 |
| N3 | BLOCK-03 UART 复用/自研待定 | 模块来源未定 | B6 集成规划 | B6 | REQ-002 |
| N4 | 高速 SPI（QSPI / 160MHz 级） | 当前 SCLK 上限 Fsys/4 | B1 架构评审 | B1 | RMP-002 / ADR-009 |
| N5 | MMIO Flash / XIP | 当前 PIO 访问 | B1 架构评审 | B1 | RMP-001 |
| N6 | 寄存器接口初版待细化 | Regmap 细节未定 | rtl-agent | C1 / C2 | spec-005 §6 |

## 4. 规格 v1.0 定稿清单（冻结基线）

以下产物冻结为 **规格 v1.0 基线**（git tag `spec-v1.0`，冻结动作待人工批准后执行）：

```
docs/spec/spec-001-PRD.md
docs/spec/spec-002-use-cases.md
docs/spec/spec-003-open-issues.md
docs/spec/spec-004-system-spec.md + spec-004-system-spec.csv
docs/spec/spec-005-interface-spec.md + pins/memory-map/irq csv
docs/spec/spec-006-rtm.md + spec-006-rtm-report.md
```

## 5. 评审结论与签字

- 预审结论：**通过**（Blocking=0；Non-blocking 6 项均已记录责任人/目标节点）
- 评审结论（待人工主持确认）：□ 通过  □ 有条件通过（列出修复项）  □ 不通过
- 评审签字（阶段 A 收口）：

| 角色 | 签字 | 日期 |
|------|------|------|
| 评审人（用户/规格负责人） | ____ | ____ |

- 签字后动作：① tracker A5 → passed（阶段 A 完成）；② `git tag spec-v1.0` 冻结基线；③ 进入阶段 B（B1 系统架构）

---

## 变更记录

- 2026-08-21：A5 waiting_review 期间执行术语规范变更（ADR-016）：性能指标编号前缀 `M-NNN` → `PPAC-NNN`（数字不变，共 20 项），涉及 spec-003/004/005/006 及校验脚本；本纪要引用已同步，RTM 双向覆盖经 `a4_check_rtm.py` 复验仍 100% PASS。
