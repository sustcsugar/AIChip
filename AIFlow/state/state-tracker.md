# 收敛看板 tracker

> orchestrator 唯一写入者。状态: pending | in_progress | waiting_review | passed | iterating

## 阶段汇总
| 阶段 | 节点 | 状态 |
|------|------|------|
| A | 5 | 5 passed / 0 pending |
| B | 7 | 1 passed / 6 pending |
| C | 8 | 全部 pending |
| D | 7 | 全部 pending |
| E | 6 | 全部 pending |
| F | 5 | 全部 pending |
| G | 3 | 全部 pending |
| H | 5 | 全部 pending |

## 节点明细

## A1 需求与场景定义
- 状态: passed
- 前置: 无
- 收敛指标: A1-D1~D5 全部满足; REQ 20 / SC 12 / UC 32(11 功能域 UC-<feature>-NNN) / OI 0
- 质量门: 已签字（2026-08-19）

## A2 系统规格
- 状态: passed
- 前置: A1
- 收敛指标: A2-D1~D6 全部满足; 功能规格 FS 20 / 指标 PPAC 20（四要素 100%，原 M-NNN，ADR-016 更名）/ REQ 追溯 100% / 五类指标齐备; BLOCK-01~14 编号齐备
- 质量门: 已签字（2026-08-20，编号体系梳理落地后）

## A3 接口规格
- 状态: passed
- 前置: A1, A2
- 收敛指标: A3-D1~D6 全部满足; 引脚 23 / 总线 7 / 中断 10 / 存储 15; 冲突扫描零结果; UC 覆盖 32/32
- 质量门: 已签字（2026-08-20，三项评审决策：AXI4 统一总线 / 引脚复用确认 / M-013≤100ms，详见 ADR-009）

## A4 需求可追溯矩阵
- 状态: passed
- 前置: A1, A2, A3
- 收敛指标: RTM 双向覆盖 100%（REQ 20/20 → SPEC 40/40、TP 34/34，孤儿 0；a4_check_rtm.py PASS）
- 质量门: 已签字（2026-08-21，双向覆盖 100% + 孤儿清单为空 + 缺口裁定确认）

## A5 规格评审冻结
- 状态: passed
- 前置: A1, A2, A3, A4
- 收敛指标: 预审通过 + 人工签字（基线含 ADR-016/017/018 三轮变更后全量校验 PASS）；spec-v1.0 冻结
- 质量门: 已签字（2026-08-21）

## B1 系统架构
- 状态: passed
- 前置: A1, A2, A3, A4, A5
- 收敛指标: 输入=spec-v1.0 冻结基线；DoD 7/7（方案 A+β 已裁定 ADR-025）；ARCH 产物 arch-008（BLOCK 14/14、数据流 32 UC 全覆盖、时延预算全满足）
- 质量门: 已签字（2026-08-21，ADR-025：方案 A + 从侧结构 β；RMP-003/004 采纳落地；治理回顾含 ADR-024 勘误）

## B2 地址映射
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## B3 总线与互联选型
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## B4 性能面积功耗建模
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## B5 架构评审
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## B6 集成规划
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## B7 参考模型开发
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## C0 IP接入与合同验证
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## C1 微架构规格
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## C2 模块接口契约
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## C3 RTL编码
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## C4 Lint检查
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## C5 CDC检查
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## C6 模块级smoke
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## C7 RTL冻结
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## D1 验证计划
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## D2 TB环境搭建
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## D3 定向测试
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## D4 约束随机自动化
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## D5 断言与形式化
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## D6 回归与覆盖率收敛
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## D7 验证签核
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## E1 约束开发
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## E2 库环境设置
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## E3 逻辑综合
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## E4 综合后DRC
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## E5 形式验证LEC
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## E6 门级仿真
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## F1 约束签核评审
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## F2 STA分析
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## F3 违例修复
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## F4 功耗估算
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## F5 时序收敛评审
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## G1 交付物打包
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## G2 收敛双签核
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## G3 基线归档
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## H1 Floorplan
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## H2 Place与Route
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## H3 CTS
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## H4 Signoff-STA
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字

## H5 物理验证
- 状态: pending
- 前置: TBD
- 收敛指标: TBD
- 质量门: 待人工签字
