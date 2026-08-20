# 节点 C4：Lint 检查

> 阶段 C | 归属 agent：rtl-agent | 对应 skill：`.opencode/skills/node-C4-lint/`

## 1. 节点目的与范围

**目的**：对 C3 产出的全部 RTL 运行 lint 检查，验证编码规范符合性与**可综合性**，提前暴露并消除潜在 RTL 缺陷（多驱动、位宽不匹配、未连接端口、inferred latch、不可综合构造、代码风格问题）。以 **无 blocker、warning 清零** 为收敛目标，为后续 CDC（C5）、仿真（C6）与综合（E 阶段）提供干净基线。

**范围**：
- 全部 SoC 自研模块 RTL（`work/soc/rtl/`）。
- manifest 引用的 IP RTL（`mode: rtl` 时纳入系统级 lint；`mode: model` 时只 lint 行为模型的可综合检查项——行为模型通常含 `initial`，按模型豁免规则处理）。
- 不覆盖 TB 代码（TB 属 D 阶段，lint 规则不同）；本节点针对设计代码。

## 2. 输入产物（前置条件）

- [ ] C3 RTL 编码（passed）：全部目标模块源码
- [ ] C2 模块接口契约（passed）：端口定义基准（端口连通性/位宽核对）
- [ ] 编码规范与 lint 规则配置：`.opencode/skills/node-C4-lint/` 中的规则集
- [ ] `work/soc/build/filelist.f`（由 `build_manifest.py --filelist` 生成，系统级 lint 输入）
- [ ] `work/soc/rtl/common/defines.svh` 及参数/宏依赖就绪

## 3. 执行步骤

### Plan
- 确定 lint 范围与规则集：模块级（逐模块）与系统级（全量 filelist）两档。
- 建立 warning 基线：首次全量 lint 输出分类统计（blocker / warning / info），作为清零追踪起点。

### Execute
- **模块级 lint**：逐模块 `verilator --lint-only -Wall --top-module <mod>`，对照 C2 契约检查端口连通性。
- **系统级 lint**：`verilator --lint-only -Wall -f work/soc/build/filelist.f`（含 manifest IP），检查模块间连接错误、未定义引用、位宽传递。
- 对每个 warning 归类并处置：
  - blocker（如多驱动、latent latch、位宽截断错误、端口不匹配）→ 必须回 C3 修复。
  - 一般 warning（风格/未使用信号）→ 回 C3 修复清零，或**申请 waive**。
  - waive 规则：必须由人工确认，记录理由（如行为模型豁免、CDC 特判、约定放宽项），统一进 waiver 清单。
- 修复 → 重跑 → 直至无 blocker 且 warning 清零（或全部 waive）。

### Measure
- 全量度量：blocker 数、warning 数、info 数、按类别分布（多驱动/位宽/latch/未连接/风格）。
- 每次重跑轮次的缺陷消减记录（收敛曲线）。
- waiver 清单数及理由。

### Judge
- blocker = 0，warning = 0（waive 项单独统计且全部有人工确认）。
- 系统级 lint 无端口/连接错误，与 C2 契约一致。
- 不满足 → 回 C3 修复后重跑，直至收敛；满足 → 进入 C5 CDC 检查。

## 4. 工具与命令

```bash
# 模块级 lint
verilator --lint-only -Wall --top-module <mod> work/soc/rtl/<mod>/<mod>.sv

# 系统级 lint（含 manifest IP）
python scripts/build_manifest.py --filelist > work/soc/build/filelist.f
verilator --lint-only -Wall -f work/soc/build/filelist.f

# 增强规则（可选，若已配置）
# verible-verilog-lint --rules=-common,style work/soc/rtl/<mod>/<mod>.sv
# svlint work/soc/rtl/<mod>/<mod>.sv
```

- 报告输出：`work/soc/docs/reports/c4-lint-<mod>.md`（模块级）与 `work/soc/docs/reports/c4-lint-sys.md`（系统级）。
- waiver 记录：`work/soc/docs/reports/c4-waiver.md`。
- lint 规则与豁免约定：`.opencode/skills/node-C4-lint/`。

## 5. 人机职责分配

| 任务 | 执行者 | 协同类型 | 干预点 |
|------|--------|---------|--------|
| lint 范围与规则集配置 | AI agent | AI 全自动 | — |
| 模块级与系统级 lint 运行 | AI agent | AI 全自动 | — |
| warning 分类、修复、重跑迭代 | AI agent | AI 全自动 | — |
| waive 判定（是否豁免某项 warning） | 人类 | 人工 | 每项 waive 必须人工确认并记录理由 |
| blocker 处置方案裁定（重写 vs 规则调整） | 人类 | 人机协同 | 出现 blocker 无法修复时按需裁定 |
| 检查结论放行 | 人类 | 人工 | 必须签字 |

## 6. 收敛判据（DoD）

**DoD：无 blocker，warning 清零。**

可操作判定方法：
1. `verilator --lint-only -Wall` 模块级与系统级输出中 **blocker = 0**。
2. warning = 0；若存在 waive 项，则全部在 `c4-waiver.md` 中有唯一编号 + 理由 + 人工签名，且 waive 数不超过既定上限（默认每模块 ≤ 3 项）。
3. 系统级 lint 端口/连接检查与 C2 契约无差异。
4. lint 报告已归档，重跑轮次收敛（最后一轮无新增 warning）。

## 7. 质量门与签字

- 质量门类型：**检查**（lint 工具 + orchestrator 判据核验）
- 检查未通过不得进入 C5；waiver 需人工确认才计入清零。

## 8. 输出产物

- `work/soc/docs/reports/c4-lint-<mod>.md`（模块级 lint 报告：分类统计 + 修复记录）
- `work/soc/docs/reports/c4-lint-sys.md`（系统级 lint 报告）
- `work/soc/docs/reports/c4-waiver.md`（waiver 清单）
- `state/state-tracker.md` 更新（C4 → passed）

## 9. 对应 skill 与 agent

- skill：`node-C4-lint`
- agent：rtl-agent
- 详章索引：`doc/SOP.md`