---
name: roadmap-capture
description: >-
  优化方向统一登记 skill：当用户/团队在开发过程中提出任何芯片优化想法、增强方向、
  "下一版可以…"、流程改进或技术预研议题时，按 AIFlow/state/state-roadmap.md 的 RMP 结构登记。
  维护统一 roadmap 清单（RMP-NNN 全局递增），登记后跑 AIFlow/scripts/roadmap_check.py 校验格式。
---

# Roadmap Capture — 优化方向统一登记

## 何时使用

- 用户随时冒出想法："记一下 / 记个待办 / 优化方向 / 下一版可以… / 能不能加个…"
- 节点签核 / 质量门时，orchestrator 主动询问后登记
- 架构节点（B1/B3/B5）启动前，读取 roadmap 并把"待评估"条目并入输入

## 工作流

1. 读取 `AIFlow/state/state-roadmap.md`，确认下一个 RMP 序号（**RMP = Roadmap，优化方向条目**；全局递增，不随节点重置）
2. 按"条目结构"逐字段登记：标题 / 分类 / 状态 / 来源 / 动机 / 方案概述 / 期望收益 / 影响范围 / 关联 / 处置建议
3. 状态默认 `idea`；分类在 下一版增强 / 架构备选 / 流程改进 / 技术预研 中选择
4. 登记后运行 `python AIFlow/scripts/roadmap_check.py` 校验（编号唯一、字段齐全、状态/分类合法）
5. 若与既有 ADR / OI / M 指标 / 其他 RMP 条目相关，填写"关联"字段并在对应文档加一行指向

## 纪律

- **orchestrator 为唯一写入者**；其他 agent 捕获到想法后，起草后交 orchestrator 落账
- 当前版本收敛范围内的问题**不登记为 RMP**（走 OI 流程）；RMP 是超出版本范围的增强 / 方向
- 登记即留档：被否决 / 延后的条目保留并标注状态，不删除
- 登记 ≠ 承诺实现：是否纳入版本由 B1/B3/B5 等评审节点评估
