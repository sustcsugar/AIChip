# 节点 C7：RTL 冻结

> 阶段 C | 归属 agent：rtl-agent | 对应 skill：`.opencode/skills/node-C7-rtl-freeze/`

## 1. 节点目的与范围

**目的**：完成**系统级集成**——组装 `soc_top`（实例化全部自研模块 + manifest 锁定的复用 IP + glue 逻辑），确认 RTL **feature complete**，并通过 git **freeze tag** 建立 RTL 基线，作为 C 阶段与 D 阶段（系统级验证）的交接点。此后功能修改需走变更流程（ECR）并重开 freeze。

**范围**：
- 系统级集成点：`soc_top` 只实例化自研模块与 manifest 引用的 IP，禁止内联未纳管逻辑。
- 系统级最小 smoke：复位释放 + 顶层通路基本联通检查（**只实例化 soc_top**）；完整系统级验证归 D 阶段。
- 本节点结束时 C 阶段全部节点均 passed。

## 2. 输入产物（前置条件）

- [ ] C0–C6 全部 passed（`state/tracker.md` 确认）：合同已验证、微架构/契约/编码/lint/CDC/模块 smoke 齐备
- [ ] B6 集成规划（passed）：soc_top 实例化清单（自研模块 + 复用 IP + 来源）
- [ ] C0 的 `work/soc/ip_manifest.json`（passed）：IP 版本与 mode 已 pin
- [ ] 系统级编译环境：`work/soc/build/` + `work/soc/verif/sys/`（系统级最小 TB 骨架）
- [ ] 全部模块级 TB 与 smoke 报告（C6）

## 3. 执行步骤

### Plan
- 从 B6 集成规划列出 soc_top 实例化清单：每个自研模块、每颗复用 IP、glue 逻辑（复位生成/时钟管理/中断仲裁/pinmux）。
- 确认 manifest mode：feature complete 检查期建议 `mode: rtl`（若 IP 已签核）；未签核 IP 用 `model` 并在集成报告中标注依赖风险。

### Execute
- **组装 soc_top**：`work/soc/rtl/soc_top.sv`——
  - 实例化全部自研模块（端口按 C2 契约连接）。
  - 实例化复用 IP（只读引用，经 `build_manifest.py --filelist` 引入文件）。
  - 实现 glue 逻辑（复位/时钟/中断仲裁/pinmux，端口与 C2/C7 计划一致）。
  - 顶层时钟/复位/引脚映射到 SoC 外部接口（对齐 A3 接口规格）。
- **全量编译**：`verilator --binary --top-module soc_top -f work/soc/build/filelist.f`，零错误。
- **系统级最小 smoke**：`work/soc/verif/sys/` 中只实例化 soc_top，验证：复位释放无 X、各时钟域启动、每颗 IP 与自研模块的顶层通路可联通（寄存器可达性抽查）。
- **feature complete 核对**：自研模块清单、IP 清单、端口连接与 B6 清单 / C2 契约逐项比对，无缺失模块、无未连接端口、无 TODO 占位。
- **打 freeze tag**：`git tag soc_rtl_freeze_<date>_<soc_version>`，记录 tag hash 与基线 commit 说明。

### Measure
- soc_top 实例化模块数 vs B6 清单（自研数 + IP 数 + glue 数）。
- 编译错误数、系统 smoke 用例通过数、未连接端口数、TODO 残留数。
- freeze tag：名称、hash、创建时间。

### Judge
- 对照 DoD 逐项检查（见第 6 节）。
- feature complete 未达标 → 补齐缺失模块/连接后重编译、重 smoke、重打 tag。
- 达标 → 提交人工签字（本节点质量门为**人工签字**）。

## 4. 工具与命令

```bash
# 生成全量 filelist（含 manifest IP）
python scripts/build_manifest.py --filelist > work/soc/build/filelist.f

# 系统级编译
verilator --binary --top-module soc_top -f work/soc/build/filelist.f

# 系统级最小 smoke（work/soc/verif/sys/ 下，只实例化 soc_top）
cd work/soc/verif/sys && make

# 冻结基线
git add work/soc/rtl work/soc/build work/soc/ip_manifest.json
git commit -m "C7: soc_top integrated, feature complete"
git tag soc_rtl_freeze_<date>_<soc_version>
git log --oneline -1
```

- 关键路径：`work/soc/rtl/soc_top.sv`、`work/soc/rtl/glue/`（glue 逻辑模块）。
- 系统级验证目录：`work/soc/verif/sys/`（只实例化 soc_top，D 阶段在此扩展）。

## 5. 人机职责分配

| 任务 | 执行者 | 协同类型 | 干预点 |
|------|--------|---------|--------|
| 实例化清单核对（B6 vs soc_top） | AI agent | AI 全自动 | — |
| soc_top 组装与 glue 集成编码 | AI agent | AI 产出人审 | 顶层连接与 glue 设计需人审 |
| 全量编译 + 系统级最小 smoke | AI agent | AI 全自动 | — |
| feature complete 核对报告生成 | AI agent | AI 全自动 | — |
| feature complete 最终裁定（是否缺失/能否豁免） | 人类 | 人机协同 | 豁免或补项决策需人裁定 |
| **freeze tag 打标与签字** | 人类 | 人工 | **必须签字**（本节点唯一硬性人工点） |

## 6. 收敛判据（DoD）

**DoD：feature complete，freeze 基线建立。**

可操作判定方法：
1. **feature complete**：
   - soc_top 实例化数 = B6 清单数（自研模块 + 复用 IP + glue），无缺失。
   - 全量编译（`verilator --binary --top-module soc_top`）零错误。
   - 端口连接与 C2 契约一致，无未连接端口；RTL 内无 TODO/FIXME 占位。
   - 系统级最小 smoke 全过（复位释放、各时钟域启动、顶层通路连通抽查）。
2. **freeze 基线建立**：
   - git tag `soc_rtl_freeze_<date>_<soc_version>` 已创建，hash 记录在集成报告中。
   - manifest（C0）与 RTL 处于同一 commit，可完整复现构建。
   - 基线说明写入集成报告，明确"后续修改需 ECR 流程"。
3. 人工签字：`state/decisions.md` 记录 C7 放行签名。

## 7. 质量门与签字

- 质量门类型：**人工签字**（系统级集成的硬性人工门）
- 未签字不得进入 D 阶段；freeze 之后功能变更一律走 ECR，变更后需重打 freeze tag。

## 8. 输出产物

- `work/soc/rtl/soc_top.sv`（系统级集成顶层）
- `work/soc/rtl/glue/`（glue 逻辑：复位/时钟/中断仲裁/pinmux）
- `work/soc/verif/sys/`（系统级最小 smoke TB 骨架，D 阶段扩展）
- `work/soc/docs/reports/c7-integration.md`（集成报告：清单核对、编译结果、smoke 结果、feature complete 结论）
- `work/soc/docs/reports/c7-freeze.md`（freeze 基线记录：tag/hash/commit 说明/ECR 流程说明）
- git：commit + freeze tag
- `state/tracker.md` 更新（C 阶段全部 → passed，D 阶段解锁）

## 9. 对应 skill 与 agent

- skill：`node-C7-rtl-freeze`
- agent：rtl-agent
- 详章索引：`doc/SOP.md`