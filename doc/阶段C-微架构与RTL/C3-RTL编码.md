# 节点 C3：RTL 编码

> 阶段 C | 归属 agent：rtl-agent | 对应 skill：`.opencode/skills/node-C3-rtl-coding/`

## 1. 节点目的与范围

**目的**：依据 C1 微架构规格与 C2 模块接口契约，为每个自研模块编写**可综合**的 RTL，严格遵循编码规范（命名、位宽、同步设计、防 latch/多驱动、时钟域隔离、参数化）。模块级 RTL 写入 `work/soc/rtl/<mod>/`（SoC 自研模块）或 `work/ip/<ip>/rtl/`（IP 项目内模块）。

**范围**：
- 覆盖全部自研模块编码；glue 逻辑（复位生成、时钟管理、中断仲裁、pinmux）在本节点一并编码（在 `work/soc/rtl/` 下按模块目录组织）。
- 复用 IP 的 RTL 不在此编码，只经 manifest 引用（只读）。
- 编码完成后独立编译通过即为本节点最小成功标志；更深的功能正确性由 C6 smoke 与 D 阶段验证覆盖。

## 2. 输入产物（前置条件）

- [ ] C1 微架构规格（passed）：状态机/握手/流水线/Regmap 定义
- [ ] C2 模块接口契约（passed）：端口方向/位宽/时钟域/时序约束
- [ ] B2 地址映射（passed）：Regmap 偏移与访问属性
- [ ] 编码规范（唯一真相源）：`doc/阶段C-微架构与RTL/C3-编码规范.md` — 可综合子集、命名、位宽、同步设计、CDC、注释、违规分级
- [ ] C0 的 `ip_manifest.json`（filelist 生成依据，供编译脚本引用）
- [ ] 目标工作区已存在：`work/soc/rtl/<mod>/`（SoC）、`work/ip/<ip>/rtl/`（IP）

## 3. 执行步骤

### Plan
- 按 C1 的依赖顺序排定编码次序（先叶子模块，后依赖模块，glue 最后）。
- 每个模块规划文件组织：单模块单文件 `<module>.sv`，公共参数/宏独立 `defines.svh`。

### Execute
- **编码前先读 `doc/阶段C-微架构与RTL/C3-编码规范.md`**（规范唯一真相源），按模块执行编码循环：
  1. **端口框架**：从 C2 契约生成完整端口声明（方向/位宽/时钟域一致）。
  2. **寄存器**：按 C1 Regmap 表实现读写逻辑（同步写、复位值、W1C/RO 等访问属性）。
  3. **状态机**：按 C1 状态表编码（`typedef enum` 状态、`always_comb` 次态、`always_ff` 现态、缺省分支显式处理非法状态）。
  4. **数据通路/握手**：按 C1 流水线与握手实现 valid/ready、停顿/背压。
  5. **CDC 隔离**：跨时钟域信号只经同步器/异步 FIFO 交接，禁止跨域组合直连。
- 遵守可综合子集纪律：只用 `always_ff`/`always_comb`（禁 `always_latch` 遗留）、无混合边沿触发、无 `initial` 进综合、禁止块内阻塞赋值混用、位宽显式匹配、避免不可综合构造（`fork/join`、`$display` 仅限 TB）。
- 每模块完成后**用 `templates/c3-selfcheck.md` 复制为 `work/soc/docs/reports/c3-selfcheck-<mod>.md` 逐项自检**（对照 `doc/阶段C-微架构与RTL/C3-编码规范.md` 十节），随后独立编译（lint-only + 编译）确认无语法/声明错误。

### Measure
- 每模块：RTL 行数、模块数、端口数、寄存器实现条数（与 C1 Regmap 比对）、状态机实现条数。
- 编译状态：语法错误数、声明错误数。
- 编码规范自检：latch 数、多驱动数、位宽不匹配数、未命名常量数。

### Judge
- 对照 C1/C2 逐模块核对实现（端口、Regmap、状态机、握手）无缺漏。
- 编译通过 + 编码规范自检清零。
- RTL 可综合：无非综合构造（供 C4 lint 正式确认）。
- 不满足 → 定位模块回退修正，重新编译；满足 → 进入 C4 lint 检查。

## 4. 工具与命令

- 语言：SystemVerilog（可综合子集，SV-2012 常用语法）
- 编译 / lint-only：
  ```bash
  # 单模块语法检查
  verilator --lint-only -Wall --top-module <mod> work/soc/rtl/<mod>/<mod>.sv

  # 系统级编译（引入 manifest IP 与 defines，C3 末期可先行验证可集成性）
  verilator --binary --top-module soc_top -f work/soc/build/filelist.f
  ```
- filelist 生成：`python scripts/build_manifest.py --filelist > work/soc/build/filelist.f`
- RTL 存放：
  - SoC 自研模块：`work/soc/rtl/<mod>/<mod>.sv`
  - IP 项目内模块：`work/ip/<ip>/rtl/<mod>.sv`
  - 公共定义：`work/soc/rtl/common/defines.svh`
- 参考：`doc/阶段C-微架构与RTL/C3-编码规范.md`（规范）、C1 微架构文档、C2 接口契约

## 5. 人机职责分配

| 任务 | 执行者 | 协同类型 | 干预点 |
|------|--------|---------|--------|
| 按依赖序排定模块编码顺序 | AI agent | AI 全自动 | — |
| 端口框架 / Regmap / 状态机 / 数据通路编码 | AI agent | AI 产出人审 | 关键状态机与握手实现需人审 |
| 可综合子集纪律与编码规范自检 | AI agent | AI 全自动 | — |
| 模块独立编译验证 | AI agent | AI 全自动 | — |
| 编码规范异常裁定（waive 或重构） | 人类 | 人机协同 | 出现规范冲突时按需裁定 |
| 与 C1/C2 一致性复核并放行 | 人类 | 人工 | 模块级放行签字（批量可按模块滚动） |

## 6. 收敛判据（DoD）

**DoD：编码规范达标，RTL 可综合。**

可操作判定方法：
1. 每模块独立编译（`verilator --lint-only -Wall`）零错误、零警告。
2. 编码规范自检清零：无 inferred latch、无多驱动、无位宽不匹配、无非综合构造。
3. 与 C1 对齐：模块端口清单 = C2 契约、Regmap 实现条数 = C1 Regmap 表、状态机状态 = C1 状态表，逐项核对一致。
4. RTL 可综合：符合可综合子集（时序逻辑仅 `always_ff`、显式缺省分支、无 `initial`/`fork-join`）。
5. 每模块有人工放行记录（`state/decisions.md` 或代码评审 comment）。

## 7. 质量门与签字

- 质量门类型：**检查**（编译 + 规范自检 + orchestrator 判据核验）
- 检查未通过不得进入 C4；各模块可在检查通过后分批进入 C4/C6（滚动），但 C7 冻结要求全部模块通过。
- 本节点对系统级可集成性不设硬性门（属 C7），但要求模块独立编译即可。

## 8. 输出产物

- `work/soc/rtl/<mod>/<mod>.sv`（每自研模块 RTL 源码）
- `work/soc/rtl/common/defines.svh`（公共参数/宏）
- `work/soc/build/filelist.f`（由 manifest 生成的文件列表，编码末期刷新）
- 编码自检记录：`work/soc/docs/reports/c3-selfcheck-<mod>.md`
- `state/tracker.md` 更新（C3 → passed，按模块粒度可记录子状态）

## 9. 对应 skill 与 agent

- skill：`node-C3-rtl-coding`
- agent：rtl-agent
- 详章索引：`doc/SOP.md`