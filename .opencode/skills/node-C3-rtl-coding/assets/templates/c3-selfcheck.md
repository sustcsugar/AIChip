# C3 模块自检记录 — <module>

> 模板：每模块复制一份为 `work/soc/docs/reports/c3-selfcheck-<mod>.md`，编码后逐项勾选。
> 依据：`doc/阶段C-微架构与RTL/C3-编码规范.md`。违规分级：Blocker 必修复 / Warning 必修复或 waiver / Info 可选。

## 模块信息
- 模块名 / 文件路径 / 时钟域 / 复位策略
- 对应 C1 微架构文档 ID / C2 契约 ID

## 1. 可综合子集
- [ ] 仅 `always_ff` / `always_comb`，无 `always_latch`
- [ ] 无混合边沿触发
- [ ] 无 `initial`、无不可综合构造（fork/join/wait/动态数组）
- [ ] 阻塞/非阻塞赋值用法正确

## 2. 命名规范
- [ ] 模块名/信号名/寄存器名符合规范
- [ ] 低有效 `_n`、时钟 `_clk`、寄存器 `_r`、参数大写
- [ ] 无魔法数（参数来自 defines.svh）

## 3. 位宽与类型
- [ ] 位宽显式声明，无不匹配/隐式截断
- [ ] 符号性明确

## 4. 同步设计
- [ ] 状态机 `enum` + `always_comb`/`always_ff` 分离，显式 default 处理非法状态
- [ ] `always_comb` 全路径覆盖，无 latch 风险

## 5. 单驱动
- [ ] 每信号单一驱动器，无多驱动
- [ ] 内部无三态/z 比较

## 6. CDC 隔离
- [ ] 跨域信号经同步器/异步 FIFO，标注 `<CDC: 源→目的, 机制>`
- [ ] 异步复位同步释放

## 7. 复位
- [ ] 复位值与 C1 Regmap 一致
- [ ] 复位策略统一

## 8. 文件组织与注释
- [ ] 单模块单文件；公共参数在 defines.svh
- [ ] 模块头/状态机/握手/CDC/Regmap 注释完整

## 9. 编译检查
- [ ] `verilator --lint-only -Wall --top-module <mod> <mod>.sv` 零错误零警告
- [ ] 与 C2 契约端口一致；与 C1 Regmap 条数一致

## 10. 自检结论
- [ ] 无 Blocker，无未 waiver Warning
- 待 waiver 项：____
- 自检人（AI agent）：____  日期：____
- 人工复核：通过 / 不通过  签字人：____  日期：____