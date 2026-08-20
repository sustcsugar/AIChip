# 节点 C0：IP 接入与合同验证

> 阶段 C | 归属 agent：rtl-agent | 对应 skill：`.opencode/skills/node-C0-ip-adoption/`

## 1. 节点目的与范围

**目的**：将 B6 集成规划中选定的复用 IP 正式接入 SoC。验证每个 IP 的接口合同（总线 AXI、寄存器映射 Regmap、复位、时钟、中断）与 SoC 集成规格逐项一致，并将 IP 版本与引用模式（`model` / `rtl`）固定（pin）到 `work/soc/ip_manifest.json`，建立 SoC 只读消费基线。

**范围**：
- 覆盖 manifest 中全部复用 IP（如 mipi/usb/ddr/axi_uart）。
- 验证对象是**接口合同**（`work/ip/<ip>/doc/interface-contract.md`）与 SoC 集成规格的**一致性**，不验证 IP 内部功能正确性（属 IP 项目自身 D 阶段收敛）。
- 本节点不修改任何 `work/ip/<ip>/` 下的源码，遵守 ip-discipline 纪律。

## 2. 输入产物（前置条件）

- [ ] B6 集成规划（passed）：IP 选型表、版本基线、复用策略（`state/state-tracker.md` 确认）
- [ ] A3 接口规格（passed）：引脚 / 总线 / 中断 / 存储映射规格冻结
- [ ] B2 地址映射（passed）：SoC 地址映射表（Regmap 一致性比对依据）
- [ ] B3 总线与互联选型（passed）：AXI/APB 协议版本、主从方向、位宽、ID 宽度
- [ ] 每颗 IP 的接口合同文档：`work/ip/<ip>/doc/interface-contract.md`（按 `.opencode/skills/node-C0-ip-adoption/assets/templates/ip-contract.md` 生成，由 IP 项目维护）
- [ ] SoC 侧接口规格文档：`work/soc/docs/spec/spec-NNN-接口规格.md`
- [ ] `work/ip/<ip>/` 项目目录已存在（含 `doc/`、`rtl/`、`model/`，当前为占位或最小实现）
- [ ] `work/soc/ip_manifest.json` 初版已生成（可由 `scripts/build_manifest.py` 引导创建）

## 3. 执行步骤

### Plan
- 读取 B6 选型表与 SoC 接口规格，列出全部待接入 IP 清单（名称、版本、路径）。
- 核对每颗 IP 的 `interface-contract.md` 是否存在；缺失则回退通知 IP 项目补充（不阻塞其他 IP）。
- 明确本节点要 pin 的 manifest 初始 `mode`（见第 4 节 mode 切换规则）。

### Execute
- 对每颗 IP 逐类比对合同，覆盖 5 大检查项：
  1. **总线接口**：协议（AXI4/AXI4-Lite/APB）、主/从方向、数据位宽、ID 宽度、突发支持、对齐要求。
  2. **Regmap**：寄存器偏移、访问属性、位宽、复位值，与 B2 地址映射表一致。
  3. **复位与时钟**：复位极性、同步/异步复位、时钟域数量与频率、门控与异步复位处理方式。
  4. **中断**：中断源数量、极性、使能控制、与 SoC 中断仲裁接口约定。
  5. **引脚与电源**：引脚复用、引脚电平、电源域要求、已知 erratum。
- 运行 `python scripts/contract_check.py --ip <ip> --soc-spec work/soc/docs/spec/spec-NNN-接口规格.md` 做自动比对。
- 对自动比对无法覆盖（`[?] 跳过`）的项，逐条人工核对并记录结论。
- 不一致项分两类处置：SoC 规格错误 → 修正 SoC 规格；IP 合同错误 → 反馈 IP 项目修订后重新发布。任何情况下**不得直接改 IP 源码**。
- 比对全部通过后更新 `work/soc/ip_manifest.json`：写死每颗 IP 的 `version` 与 `mode`，递增 `soc_version`，提交 git。
- 输出合同检查报告（每 IP 一份），含 `.opencode/skills/node-C0-ip-adoption/assets/templates/ip-contract.md` 第 8 节"合同验证记录"表。

### Measure
- 每颗 IP：检查项数 `n_checked`、失败项 `n_fail`、跳过项 `n_skip`。
- 5 大类（总线/Regmap/复位时钟/中断/引脚）各自的通过状态。
- manifest 中每个 IP 的 `version` / `mode` / `path` 与 B6 选型表的一致性核验结果。

### Judge
- `contract_check.py` 退出码 0（`n_fail == 0`）。
- 跳过项全部有人工核对记录，无遗留 `[?]`。
- `build_manifest.py --ips` 输出与 B6 选型表逐项一致。
- 不满足 → 节点置回 `iterating`，修正规格或合同后重跑比对，直至收敛。

## 4. 工具与命令

```bash
# 列出可用 IP
python scripts/contract_check.py --list

# 单 IP 合同比对（必须同时给 --ip 与 --soc-spec）
python scripts/contract_check.py --ip mipi --soc-spec work/soc/docs/spec/spec-NNN-接口规格.md

# 查看 manifest 中 IP 版本与 mode
python scripts/build_manifest.py --ips

# 按 manifest 生成 RTL 文件列表（C3/C4/C7 复用）
python scripts/build_manifest.py --filelist

# 检查 tracker 前置条件
python scripts/check_tracker.py --summary
```

**manifest `mode` 切换规则**（`work/soc/ip_manifest.json`）：
- `mode: "model"`：早期集成阶段，SoC 引用 `work/ip/<ip>/model/` 行为模型，仿真快、可用于 C6 模块级与早期系统 smoke。
- `mode: "rtl"`：IP 已 D7 签核发布 tag 后，切换为引用 `work/ip/<ip>/rtl/` 真实 RTL，供 C7 集成与 D 阶段全量回归。
- C0 首次 pin 时按当前可发布状态选择：IP 已签核 → `rtl`；未签核 → `model`，并在 manifest 注释中标注计划切换点（一般位于 D6 回归前，由 verify-agent 执行切换）。

**ip-discipline 纪律**：
- manifest 锁定的 IP 源码为只读，任何 agent 不得修改。
- 发现 IP bug → 记录 RCR，反馈 IP 项目出新版本 → 更新 manifest 版本号。
- 违反纪律的修改在 C4/C7 检查中会被标记为违规项。

## 5. 人机职责分配

| 任务 | 执行者 | 协同类型 | 干预点 |
|------|--------|---------|--------|
| 读取 B6 选型表与 SoC 接口规格，生成待接入 IP 清单 | AI agent | AI 全自动 | — |
| 运行 `contract_check.py` 逐 IP 自动比对 5 大检查项 | AI agent | AI 全自动 | — |
| 自动比对跳过的项（`[?]`）逐条人工核对 | 人类（配合 AI 汇总） | 人机协同 | 每个跳过项必须人工确认并留痕 |
| 不一致项裁定（改 SoC 规格 vs 反馈 IP 修订） | 人类 | 人机协同 | 出现不一致时按需裁定 |
| 更新 `ip_manifest.json` pin 版本与 mode | AI agent | AI 产出人审 | 版本选择与 mode 决策需人确认 |
| 输出合同检查报告并自检判据 | AI agent | AI 全自动 | — |
| 质量门检查与放行 | 人类 | 人工 | 必须签字 |

## 6. 收敛判据（DoD）

**DoD：接口一致，版本已 pin 到 `ip_manifest.json`。**

可操作判定方法：
1. `contract_check.py` 对每颗 IP 输出"检查 N 项，失败 0 项"，退出码 0。
2. 跳过项清零：所有 `[?]` 项有人工核对结论，无遗留未确认项。
3. `build_manifest.py --ips` 输出的每颗 IP `version` 与 B6 选型表完全一致，`mode` 与当前验证阶段匹配。
4. `work/soc/ip_manifest.json` 已更新且 `soc_version` 递增，git 已有提交记录（`git log` 可查）。
5. 无 ip-discipline 违规：比对过程中未发生任何对 `work/ip/<ip>/` 源码的写操作（git status 干净）。

## 7. 质量门与签字

- 质量门类型：**检查**（自动化比对 + orchestrator 收敛判据核验）
- 检查未通过不得进入 C1；`state/state-tracker.md` 中 C0 状态置 `passed` 后方可派发下一节点。
- 比对报告与 manifest 变更作为检查依据归档。

## 8. 输出产物

- `work/soc/ip_manifest.json`（更新：IP version/mode/path 固定，`soc_version` 递增）— 交付给 C3/C7/D 阶段消费
- `work/soc/docs/reports/c0-contract-check-<ip>.md`（每 IP 一份合同比对报告，含 5 大检查项验证记录表）
- `work/soc/docs/reports/c0-waiver.md`（如有不一致项的裁定记录与修正说明；无则注明"无"）
- `state/state-tracker.md` 更新（C0 → passed），由 orchestrator 写入
- git 提交：manifest 变更 + 报告（commit message 标注 `C0`）

## 9. 对应 skill 与 agent

- skill：`node-C0-ip-adoption`
- agent：rtl-agent
- 详章索引：`doc/SOP.md`