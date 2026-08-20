# 节点 C5：CDC 检查

> 阶段 C | 归属 agent：rtl-agent | 对应 skill：`.opencode/skills/node-C5-cdc/`

## 1. 节点目的与范围

**目的**：对全部 RTL 进行跨时钟域（CDC）检查，识别所有跨时钟域信号路径，验证同步结构（2-flop 同步器 / 握手协议 / 异步 FIFO / 格雷码计数器）的正确性与完整性，消除亚稳态传播风险与 CDC 违例（缺失同步器、跨域组合逻辑、多 bit 直连、复位域问题、跨域 reconvergence）。收敛目标：**无 CDC 违例**。

**范围**：
- 全部自研模块内部及跨模块的时钟域交接（C1/C2 已标注的 CDC 接口）。
- manifest 引用的 IP（`mode: rtl`）边界：检查 SoC 与 IP 之间接口的同步结构；IP 内部 CDC 属 IP 项目自身责任，本节点只核验其同步方案已声明且边界合规。
- 复位域（异步复位释放、复位去断言同步）一并纳入检查。

## 2. 输入产物（前置条件）

- [ ] C3 RTL 编码（passed）+ C4 lint（passed）：RTL 已 lint 清零
- [ ] C1 微架构规格的"跨时钟域"章节（passed）：时钟域划分与同步策略声明
- [ ] C2 模块接口契约（passed）：跨时钟域接口清单与同步约束
- [ ] 时钟/复位定义文件：`docs/cdc/clk-def.json`（时钟域名称、频率、相位、复位域映射）
- [ ] IP 侧同步方案声明（来自 `ip/<ip>/AIFlow/doc/interface-contract.md`，C0 已验证）

## 3. 执行步骤

### Plan
- 从 C1/C2 收集时钟域划分与全部跨时钟域接口清单，生成待查路径表。
- 配置时钟域定义（`clk-def.json`）：列出每个时钟域、频率/周期、与复位域的关系。

### Execute
- **路径识别**：静态遍历 RTL，标记每条信号的起点时钟域与终点时钟域，生成跨域路径清单。
- **分类核对**，对每类跨域路径执行对应规则：
  - **单 bit 控制信号跨域** → 必须经过 2-flop（或 3-flop）同步器；核查同步器实例与 fan-out 仅限同步后域。
  - **多 bit 数据跨域** → 必须经过异步 FIFO / 握手（req-ack）/ 格雷码编码；禁止直接 2-flop 多 bit。
  - **跨域组合逻辑** → 禁止在同步器输入前做跨域组合计算；发现即违例。
  - **复位域** → 异步复位释放需同步去断言；检查复位信号跨域同步结构。
  - **reconvergence** → 同一逻辑经不同同步路径收敛到同一终点时，评估一致性风险并记录。
- 违例处置：修复（回 C3 加同步器/换握手方案）→ 重跑；或 waive（须人工确认：如"慢速使能 + 静止数据"受控场景）。
- 更新时钟域属性文件与同步器清单，保证 C5 结果与 C7/D 阶段一致。

### Measure
- 跨域路径总数、同步器实例数、异步 FIFO 数。
- 违例数按类别分布（缺同步器 / 多 bit 直连 / 跨域组合 / 复位域 / reconvergence）。
- 修复轮次、waive 数及理由。

### Judge
- 违例 = 0；waive 全部有人工确认并留痕。
- 单 bit 跨域均有同步器、多 bit 跨域均非直连 2-flop、无跨域组合逻辑。
- 与 C1 CDC 声明一致：RTL 实现未超出微架构声明的同步方案。
- 不满足 → 回 C3/C1 修复重跑；满足 → 进入 C6 模块级 smoke。

## 4. 工具与命令

- 开源主流程（本实验无商用 CDC 工具时的策略）：
  - 结构识别：基于 `clk-def.json` + 自研脚本 `AIFlow/scripts/cdc_check.py`——遍历 RTL 标注信号时钟域，输出跨域路径表。
  - 同步器模式匹配：脚本匹配 2-flop 同步器 / 异步 FIFO 实例 / 握手 req-ack 结构，标注通过/未覆盖路径。
  - 断言补充：在 C6 smoke TB 中挂 CDC 相关断言（如"同步器输入变化在快域禁止重迭"）。
- 可选商用增强：SpyGlass CDC / Questa CDC（若实验室环境允许，作为交叉验证）。
- 配置与报告：
  - `docs/cdc/clk-def.json`（时钟域定义）
  - `docs/reports/c5-cdc.md`（跨域路径表 + 违例清单）
  - `docs/reports/c5-waiver.md`（CDC waive 清单）

## 5. 人机职责分配

| 任务 | 执行者 | 协同类型 | 干预点 |
|------|--------|---------|--------|
| 时钟域定义文件生成与跨域路径清单提取 | AI agent | AI 全自动 | — |
| 同步器 / FIFO / 握手结构匹配与违例分类 | AI agent | AI 全自动 | — |
| 违例修复（补同步器 / 换同步方案）回 C3 | AI agent | AI 全自动 | — |
| CDC 方案裁定（2-flop vs 握手 vs FIFO / 受控场景 waive） | 人类 | 人机协同 | 每项 waive 与方案变更需人工裁定 |
| reconvergence / 复位域风险人工评估 | 人类 | 人机协同 | 高风险项人工评估 |
| 检查结论放行 | 人类 | 人工 | 必须签字 |

## 6. 收敛判据（DoD）

**DoD：无 CDC 违例。**

可操作判定方法：
1. `cdc_check.py` 输出中违例数为 0，跨域路径表全部标注同步方案且与 RTL 实例匹配。
2. 规则核验：单 bit 跨域路径均有 2-flop 同步器；多 bit 跨域路径均为异步 FIFO / 握手 / 格雷码，无多 bit 直连 2-flop。
3. 无跨域组合逻辑路径；复位跨域均有同步去断言结构。
4. waive 项 ≤ 既定上限，且全部在 `c5-waiver.md` 记录理由与人工签名。
5. RTL 实现与 C1 CDC 章节声明一致，无"未声明的新增跨域路径"。

## 7. 质量门与签字

- 质量门类型：**检查**（CDC 静态检查 + orchestrator 判据核验）
- 检查未通过不得进入 C6；waiver 需人工确认。

## 8. 输出产物

- `docs/cdc/clk-def.json`（时钟域与复位域定义，D 阶段与 E 阶段 SDC 复用）
- `docs/reports/c5-cdc.md`（跨域路径表、同步器清单、违例与修复记录）
- `docs/reports/c5-waiver.md`（waive 清单）
- `AIFlow/state/state-tracker.md` 更新（C5 → passed）

## 9. 对应 skill 与 agent

- skill：`node-C5-cdc`
- agent：rtl-agent
- 详章索引：`AIFlow/doc/SOP.md`