# 关键决策记录（ADR）

> orchestrator 维护。记录所有关键决策、评审结论、异常授权。**条目格式见 `.opencode/skills/_shared/templates/adr-template.md`**（Nygard 标准 + 项目溯源字段）。

## 决策日志

### ADR-001 — 实验基线建立
- 日期：2026-08-19
- 状态：已确认
- 背景：需验证"人与 AI 协同完整开发一款可收敛芯片"，无既有流程基线
- 决策：采用收敛环迭代模型 + 领域 agent + 编排者，收敛标准为功能 + 综合后时序收敛
- 后果：
  - 正面：流程可度量、可签核、可追溯
  - 负面：首次运行需验证流程本身的有效性
  - 风险/代价：无
- 依据：AIFlow/doc/设计/2026-08-19-ai-chip-sop-design.md
- 落地：AIFlow/doc/SOP.md、AIFlow/state/state-tracker.md

### ADR-002 — SoC 需求决策（A1 open issue 关闭）
- 日期：2026-08-19
- 状态：已确认
- 背景：A1 需求澄清出现 5 项需求级歧义（OI-A1-001~005），必须人工裁定
- 决策：基于 tinyRISCV 构建 MCU 级 SoC，必选模块 UART/JTAG/SPI/IIC/PWM/中断/GPIO，产品定位 MCU 级
  - OI-A1-001 存储：SPI Flash（固件非易失存储）+ AXI_SRAM（运行数据），启动/固件更新写入 Flash
  - OI-A1-002 tinyRISCV 接入：pin 定版本（待 C0 定 commit），保留 RIB 总线，SoC 层自研 RIB↔AXI 桥接入标准 AXI 外设；无 Debug Module 对 JTAG 的影响待 C0 评估
  - OI-A1-003 外设范围：纳入独立 GPIO（外设引脚复用）
  - OI-A1-004 工艺：暂不定，功能收敛以仿真为主，E/F 阶段前再定工艺/库
  - OI-A1-005 验收演示：LED 点灯 + 串口打印日志 + SPI/IIC/PWM 外设联动
- 后果：
  - 正面：需求基线明确，A1 可收敛
  - 负面：RIB↔AXI 桥为自研 IP，增加 C 阶段工作量；工艺未定影响 E/F 前移约束
  - 风险/代价：桥的正确性需验证兜底
- 依据：用户 2026-08-19 A1 质量门答复（OI-A1-001~005）
- 落地：AIFlow/state/state-decisions.md（本条）；docs/spec/spec-001-PRD.md（REQ 来源列引用 ADR-002）；docs/spec/spec-003-open-issues.md（已关闭问题表含决策摘要）

### ADR-003 — 项目文档命名规范
- 日期：2026-08-19
- 状态：已确认
- 背景：项目生成文档无统一命名，路径/文件名随节点随意产生，影响可追溯与全局编号
- 决策：项目生成文档统一 `<前缀>-<NNN>-<名称>.md` 命名；前缀分类（spec- = 需求/规格，后续阶段 arch-/rtl-/verif-/syn-/sta-/sig- 等），**序号 NNN 项目全局递增**（跨前缀/跨节点不重置）；登记表 `docs/00-文档编号登记.md` 为唯一事实源，生成前取号、生成后登记；**生成顺序 = 节点详章 §3 Execute 步骤顺序，后产物依赖前产物 ID**
- 后果：
  - 正面：全局可追溯、前缀即分类、跨节点编号连续
  - 负面：已有文档需一次性重命名同步；新节点需先查登记表
  - 风险/代价：登记表须保持唯一事实源，orchestrator 维护
- 依据：用户 2026-08-19 评审指示
- 落地：docs/00-文档编号登记.md、A1 详章 §8、.opencode/skills/node-A2-system-spec/assets/templates/spec-system.md

### ADR-004 — 无工艺库阶段的收敛降级标准
- 日期：2026-08-19
- 状态：已确认
- 背景：ADR-002 定"工艺/库暂不定，仿真为主"，但 ADR-001/SOP 关口2 要求"所有角下 WNS/TNS ≥ 0"，无工艺库无法做真实 STA，二者矛盾
- 决策：在目标工艺库确定前，E/F 阶段收敛降级为——① 功能收敛（D7）不受影响；② E 阶段以开源综合（yosys）验证可综合性与 lint/DRC clean 替代商用 DC 流程；③ F 阶段以综合后结构检查 + 延迟估算代替 Signoff STA；④ 一旦工艺库就绪（或用户指定），补跑完整 E/F 并作为正式时序收敛证据
- 后果：
  - 正面：流程不被 EDA 许可/工艺库阻塞，可先收敛功能
  - 负面：时序收敛是"待补"状态而非真收敛，G2 双签核需标注受限
  - 风险/代价：可能需在功能收敛后回退补时序，迭代成本可控
- 依据：ADR-002 OI-A1-004（工艺暂定）+ ADR-001 收敛标准冲突分析
- 落地：E/F 阶段详章判据按此降级口径执行；G2 签核时标注时序受限

### ADR-005 — 节点校验脚本命名规范
- 日期：2026-08-19
- 状态：已确认
- 背景：A1 专属校验脚本初建为 check_req.py，后经评审临时改名 a1_check_req.py，说明脚本命名无既定规则
- 决策：节点专属校验脚本统一 `AIFlow/scripts/<节点ID小写>_<用途>.py` 命名（如 `a1_check_req.py`、`a2_check_metric.py`）；通用脚本（check_tracker/build_manifest 等）保持现状
- 后果：
  - 正面：脚本归属节点一目了然，命名可预测
  - 负面：无
  - 风险/代价：无
- 依据：用户 2026-08-19 评审指示（脚本改名）+ 本次流程复盘
- 落地：AIFlow/scripts/ 现有脚本符合即不迁移；新增节点脚本按此规则

### ADR-006 — skill 资产"全外置"试运行裁决与再评估触发点
- 日期：2026-08-20
- 状态：已确认
- 背景：skill-creator 方法论审查发现本体系 46 个节点 skill 为"薄壳"——执行知识全部委托 AIFlow/doc/ 详章，无捆绑 AIFlow/scripts/references/assets，与 skill-creator 推荐（专属内容随 skill 打包）冲突；此前已口头决定"保持全外置试运行"但未登记
- 决策：延续"全外置"策略试运行——skill 只承载流程壳 + 指针，执行规范/模板/判据驻留 AIFlow/doc/ 与 AIFlow/scripts/；同时补两个防护：① scaffold_skills.py 增加覆盖保护（--force 覆盖前比对，有手工定制差异时告警），允许节点 skill 渐进内化专属资产而不被批量重生成抹掉；② 设**再评估触发点**：a) 任一节点 skill 被实跑暴露缺陷≥2 次；b) 阶段 C 开始（RTL 编码期，执行知识密度显著上升）；c) 用户主动要求。届时重新评估"专属资产内化到 skill 目录"
- 后果：
  - 正面：skill 保持轻量，单一事实源仍在 AIFlow/doc/；本轮无需大规模迁移
  - 负面：skill 不自包含，换项目/环境时依赖本项目 doc 布局
  - 风险/代价：触发性再评估依赖纪律执行，暂挂 orchestrator 里程碑跟踪
- 依据：skill-creator 方法论审查报告（2026-08-20）+ 用户"保持全外置试运行"决策
- 落地：AIFlow/scripts/scaffold_skills.py（覆盖保护补丁）；再评估触发点记入 AIFlow/state/state-milestones.md

### ADR-007 — state 目录文件命名规范
- 日期：2026-08-20
- 状态：已确认
- 背景：AIFlow/state/ 下 tracker.md / milestones.md / decisions.md 未带目录前缀，与 ADR-003 全局编号命名精神不一致，且文件散落难以一眼识别归属
- 决策：AIFlow/state/ 目录内文件统一以 `state-` 前缀命名：`state-tracker.md`、`state-milestones.md`、`state-decisions.md`；所有文档/脚本/agent/skill 引用同步更新
- 后果：
  - 正面：文件名自含归属，与目录语义一致，引用无歧义
  - 负面：一次性全局替换（96+ 文件），需确认无残留
  - 风险/代价：外部脚本若硬编码旧路径需同步；登记在 ADR-003 编号精神之内
- 依据：用户 2026-08-20 指示
- 落地：AIFlow/state/ 三个文件已重命名；AIFlow/scripts/check_tracker.py、README.md、orchestrator agent、node-template 及全部 node skill、各节点详章引用已全局替换

### ADR-008 — A 阶段编号体系语义定义（FS/REQ/M/OI）
- 日期：2026-08-20
- 状态：已确认
- 背景：A1/A2 产物出现 REQ/SC/UC/OI/FS/M 六类编号，用户质疑语义重叠；审查确认 REQ↔FS 1:1 与 REQ 内嵌指标 vs M 表存在双源风险，OI 编号语义未覆盖 A1 之后
- 决策：
  1. **FS 与 REQ 分工**：FS 是 REQ 的规格化细化（需求陈述 → 可测试系统行为），**不新增需求**；新增功能必须先改 PRD 增补 REQ，再补 FS
  2. **M 表为指标唯一事实源**：spec-004 §3 指标表是全部量化指标唯一入口；REQ/详章/后续文档数字均为引用，指标调整只改 M 表并同步引用处
  3. **OI 编号全流程化**：OI 为"全流程需求/规格歧义澄清"编号，不限定 A1；格式 `OI-<节点ID>-<全局序号>`，序号项目全局递增不随节点重置；现有 5 项（均出自 A1）重命名为 OI-A1-001~005，下一位从 006 接续
  4. **BLOCK 物理模块编号（扩展）**：物理模块统一 `BLOCK-NN` 编号（BLOCK-01~14），全文档以 BLOCK-NN 引用；FS 描述行为（逻辑维度）、BLOCK 描述物理构成（结构维度），二者映射显式化于 FS 表"对应模块"列（多对多）；spec-004 头部增设"编号体系总览"（缩写全称 + 主脉络：REQ 为根，分设计侧 REQ→FS→M 与验证侧 REQ→SC→UC→FP 两主线，BLOCK 为结构层，OI 贯穿全程）
- 后果：
  - 正面：六类编号语义边界清晰，消除"两套 20 条"困惑；指标单一事实源防漂移；OI 全流程可追溯；BLOCK 编号使物理模块可引用、FS↔模块映射显式化
  - 负面：OI 现有条目一次性重命名（spec-001/002/003/004 + decisions 已同步）；a1_check_req.py 正则需适配新格式；模块表行号改为 BLOCK 编号
  - 风险/代价：后续新增 FS/M 须先经 REQ/OI 流程，纪律要求由 spec-agent 执行 + orchestrator 判据把关
- 依据：用户 2026-08-20 裁定（编号体系审查结论 + 三条明确指令 + BLOCK 编号指令）
- 落地：spec-004 新增"编号体系总览"与"编号体系声明"节、模块表 BLOCK-01~14 编号、FS 表"对应模块"列、FP 组织维度说明、§7 追溯表 BLOCK 引用；spec-003 新增 OI 编号规范说明；AIFlow/scripts/a1_check_req.py OI 正则更新；spec-001/002/003/004 与 state-decisions.md 的 OI 引用全局替换为 OI-A1- 格式

### ADR-009 — A3 接口规格评审决策（AXI4 统一 / 引脚复用确认 / M-013 放宽 / 高速 SPI 待 B1）
- 日期：2026-08-20
- 状态：已确认
- 背景：A3 接口规格评审，三项决策点需人工裁定：① 总线统一协议（AXI4-Lite vs AXI4 全量）；② 引脚复用方案；③ OI-A3-006（SPI Flash 启动带宽 vs M-013 ≤5ms 冲突）
- 决策：
  1. **总线统一采用 AMBA AXI4**：RIB↔AXI 桥 AXI 侧、AXI_SRAM、全部外设从端口统一 AXI4；突发/outstanding/ID 宽度细节由 B3 量化细化
  2. **引脚复用按现方案**：GPIO pad AF1 复用 UART/SPI/IIC/PWM，AF0 为 GPIO，16 路 GPIO 保持
  3. **M-013 放宽至 ≤ 100 ms**：单线 SPI @ Fsys/4=12.5 MHz，协议满速 12.5 Mbps、70% 评估 ≈ 8.75 Mbps → 64KB 固件加载 ≈ 60 ms，留 ~1.6× 裕量；测试口径不变（SPI Flash 模型加载 64KB @50MHz）
  4. **高速 SPI 能力登记待 B1 评估**：QSPI NOR Flash 器件可达 104–166 MHz（160 MHz 经验），但当前单时钟域架构（FS-010，外设时钟由 Fsys 分频）下 SCLK 硬上限 = Fsys = 50 MHz；要上 160 MHz 需引入独立 SPI 时钟（PLL），属 B1/B3 架构决策，不阻塞 A3 冻结
- 后果：
  - 正面：A3 三项评审点全部关闭，接口清单可冻结；M-013 目标可测可实现
  - 负面：AXI4 全量较 AXI4-Lite 增加桥与从端口实现复杂度（突发/outstanding 处理），C1/C2 细化
  - 风险/代价：160 MHz 能力未定，若 B1 决定上高速 SPI，M-006/BLOCK-05 需同步修订
- 依据：用户 2026-08-20 A3 评审裁定（AXI4 统一 / 引脚复用确认 / M-013 ≤100ms / 160MHz 待 B1）
- 落地：spec-005-interface-spec.md（AXI4 统一、§2.3、§9.1）；spec-004（M-013 ≤100ms，md+csv）；spec-003（OI-A3-006 关闭）；state-tracker.md（A3 passed）

### ADR-010 — 优化方向 Roadmap 统一登记机制（state-roadmap + roadmap-capture skill）
- 日期：2026-08-20
- 状态：已确认
- 背景：开发过程中用户会随时产生芯片优化想法（如 MMIO Flash/XIP、高速 SPI），此前无统一存放处，稍纵即逝；需要一条"随时登记、定期评估"的轻量通道
- 决策：
  1. 新建 `AIFlow/state/state-roadmap.md` 作为统一待办/优化方向清单，条目编号 `RMP-NNN` 全局递增，固定字段：标题/分类/状态/来源/动机/方案概述/期望收益/影响范围/关联/处置建议
  2. **以 skill（roadmap-capture）而非独立 agent 承载登记流程**：skill 可被任意 agent 随取随用，登记是一次性轻量动作，不需要常驻角色；维护者收敛为 orchestrator（与 state-tracker 唯一写入者纪律一致）
  3. 触发点：用户随时提出 → 当前 agent 登记；每个质量门签核时 orchestrator 主动询问；B1/B3/B5 启动前读取并把待评估条目并入输入
  4. 与 OI 分工：OI 是当前版本规格歧义（必须关闭）；RMP（原 RT，2026-08-20 改名）是超出版本范围的增强/方向（不阻塞当前版本）；登记即留档，不删除
- 后果：
  - 正面：优化想法即时留档、可追溯、定期评估；roadmap 成为下一版方向的事实源
  - 负面：需纪律维护（orchestrator 唯一写入）；条目若不定期评估会堆积
  - 风险/代价：登记 ≠ 承诺实现；评估入口在 B1/B3/B5 等节点，需在节点详章中引用
- 依据：用户 2026-08-20 指示（统一待办/roadmap + skill 承载）
- 落地：AIFlow/state/state-roadmap.md（RMP-001 MMIO Flash/XIP、RMP-002 高速 SPI）；.opencode/skills/roadmap-capture/SKILL.md；AIFlow/scripts/roadmap_check.py；orchestrator agent 职责更新；README/SOP 同步

### ADR-011 — 流程资产内化：模板归位到 skill 资产（ADR-006 再评估落地）
- 日期：2026-08-20
- 状态：已确认
- 背景：ADR-006 确立"skill 资产全外置"试运行并设三个再评估触发点；本次**用户主动要求**（触发点 c 满足）实施首次大规模流程架构优化与资产内化——顶层 `templates/` 与 skill 目录分离，模板散落工作区、skill 不自包含、跨节点共享模板无统一归属
- 决策：
  1. **单节点模板内化到对应 node skill 的 `assets/templates/`**（7 个）：spec-system→node-A2、spec-microarch→node-C1、vplan→node-D1、c3-selfcheck→node-C3、model-spec→node-B7、ip-contract→node-C0（C2/A1/A3 按需引用）、node-doc-template→node-template
  2. **跨节点共享模板统一归入 `.opencode/skills/_shared/templates/`**（4 个初始示例）：review-checklist、adr-template、convergence-report、ip_manifest.json；跨切面 skill（review-gate/convergence-judge/ip-discipline）作为"用法持有者"在 SKILL.md 指向该目录
  3. **删除顶层 `templates/`**；doc 详章 / agent / state / skill 全部引用迁移到新路径；node skill 通用模板行改为"本 skill `assets/templates/` 存在模板则复制"
  4. **共享模板维护纪律**：orchestrator 唯一写入；新增/修改在 `_shared/templates/README.md` 登记；单节点模板优先内化 skill，仅 ≥2 节点共用才提升到 `_shared/`；运行时产物（`ip_manifest.json`）保持在工作区，仅模板示例内化
- 后果：
  - 正面：skill 自包含（模板随 skill 走）、共享模板单一归属、工作区根目录收敛为 AIFlow/doc/AIFlow/scripts/AIFlow/state/work；换项目/环境时节点 skill 可直接携带模板
  - 负面：引用路径变长（`.opencode/skills/_shared/…`）；一次性迁移需全量校验无残留
  - 风险/代价：已生成产物（spec-004/005 等）不受影响（路径仅流程/文档引用）；scaffold_skills.py 再生成不会写回专属模板指针（A1/A2 定制保护机制已存在，见 ADR-006）
- 依据：用户 2026-08-20 指示（"按照这个方案先实施…第一次大规模流程架构优化与资产内化…仔细排查治理层整个流程"）+ ADR-006 再评估触发点 c（用户主动要求）
- 落地：本 commit（templates/ → `.opencode/skills/{node-*, _shared}/templates/` 迁移 + 全量引用替换 + 删除顶层 templates/）

### ADR-012 — 目录架构重构：根目录即芯片设计工作目录，共治管理层下沉 AIFlow/
- 日期：2026-08-21
- 状态：已确认
- 背景：原架构根目录为共治管理层（doc/ scripts/ state/ .opencode/），芯片设计内容埋在 work/soc/、work/ip/ 两层之下，骨架与脚手架淹没了实际芯片产物；用户提出根目录应为芯片设计工作目录、脚手架单独成目录 AIFlow/
- 决策：
  1. **根目录 = 芯片设计工作目录（SoC 项目层）**：work/soc/* 上浮为 docs/ rtl/ verif/ model/ build/ + ip_manifest.json；work/ip 上浮为 ip/（IP 项目层与 SoC 平级，两层模型保留；manifest 路径 ../ip/xx → ip/xx）
  2. **共治管理层下沉 AIFlow/**：doc/ scripts/ state/ 迁至 AIFlow/（AIFlow/README.md 说明职责与使用）
  3. **.opencode/ 保留在根目录**：opencode 只从当前目录向上到 git 根逐层查找固定目录名 `.opencode/`（无自定义路径配置），移入 AIFlow/.opencode 将导致 agent/skill 静默失效；作为隐藏目录保留在根，是本架构唯一功能性例外
  4. 全部引用迁移：~1200 处路径引用（doc 详章/skill/agent/state/scripts/README/opencode.json/.gitignore/设计文档目录树）统一替换；脚本 ROOT 语义调整（AIFlow/scripts 的 ROOT=AIFlow，芯片根经 ROOT.parent 访问）
- 后果：
  - 正面：芯片产物（docs/ rtl/ verif/ ip/）在根目录直接可见，目录语义清晰；治理层单一归属 AIFlow/
  - 负面：引用路径变长（AIFlow/doc/...、AIFlow/scripts/...）；opencode.json instructions 与脚本调用命令需带 AIFlow/ 前缀
  - 风险/代价：历史 commit 中的 work/ 路径与现结构不对应（git 可追溯重命名）；.opencode/ 保留根目录是功能性例外，需在文档中持续明示
- 依据：用户 2026-08-21 指示（"根目录即为芯片设计的工作目录，脚手架作为单独的一个文件夹，命名为AIFlow"）+ 用户确认方案 A（.opencode 保留根目录）
- 落地：本 commit（目录迁移 + 1195 处路径替换 + 脚本/配置/文档更新）

### ADR-013 — 流程骨架规则化审查机制（workflow-audit skill + 确定性审计脚本）
- 日期：2026-08-21
- 状态：已确认
- 背景：AI 对"整体流程/工作流"的审查是概率性的——不同轮次结论可能漂移、易遗漏、无法复现；用户要求为 orchestrator 创建流程骨架审查 skill，并尽可能规则化，消除 AI 审查的不确定问题
- 决策：
  1. **新增 `workflow-audit` skill（orchestrator 专用）**：审查整体工作流、控制流与流程骨架；触发时机 = 治理层变更后全量回归 / 质量门前 / 阶段切换前 / 用户要求
  2. **规则化分层**：机械层（确定性脚本 M1-M5，退出码驱动，Blocker 即停）→ 结构不变量 N1-N6 → 控制流 C1-C5 → 语义层 S1-S5（AI 判断，必须人工复核）；机械结论与 AI 判断严格分离，报告模板固定
  3. **新增 `AIFlow/scripts/workflow_audit.py`**：W1-W17 确定性规则（注册表/详章/skill/agent 归属/SOP 索引/tracker/引用完整性/脚手架一致性/模板资产/速查表/职责矩阵/术语表）
  4. **新增 `AIFlow/doc/辅助文档/92-术语与缩写表.md`**：落地"缩写先登记后使用"纪律；W17 校验核心缩写覆盖
  5. **本次全量审查修复**：arch-agent 缺 B7、signoff-agent 缺 H1-H5、tracker 阶段汇总 A 行失实、roadmap-capture 残留旧缩写 RT、orchestrator 职责编号重复
- 后果：
  - 正面：流程审查可复现、可自动化（退出码可接入 CI）；AI 判断与机械结论分离，人工只需复核语义项；缩写纪律落地
  - 负面：新增脚本与 skill 需随治理演进维护；语义层仍需人工复核
  - 风险/代价：规则清单（W1-W17）需随流程演进同步扩展；术语表需持续登记（orchestrator 纪律）
- 依据：用户 2026-08-21 指示（"为 orchestrator 创建一个 skill 专门审查整体工作流以及控制流…尽可能的进行规则化处理，防止 AI 分析审查所带来的概率问题以及不确定问题"）
- 落地：本 commit（workflow-audit skill + workflow_audit.py + 92-术语表 + 审查问题修复）

### ADR-014 — skill 生命周期归属：orchestrator 为唯一生成/维护者
- 日期：2026-08-21
- 状态：已确认
- 背景：节点 skill 由 `scaffold_skills.py`（nodes.json + node-template → 渲染）生成，但"由谁执行生成/再生成"此前无任何文档/agent 定义显式归属，review-gate"规范回写"也只写"重新生成 skill"未指明执行者；职责缺口易导致批量再生成无人负责或误执行
- 决策：
  1. **orchestrator 为节点 skill 生命周期唯一执行者**：维护 nodes.json 与 node-template；运行 `scaffold_skills.py` 生成/再生成 46 个节点 skill；新增节点或改 node-template 后必须再生成并跑 workflow-audit（W10）验证一致性
  2. **非节点 skill（跨切面/专用）**的新建与变更由 orchestrator 发起并登记 ADR
  3. review-gate"规范回写"流程明确执行者：由 orchestrator 运行 scaffold_skills.py 重新生成
- 后果：
  - 正面：职责单一化，防止多 agent 并发改 skill 导致漂移；与 state-* 唯一写入纪律（orchestrator）一致
  - 负面：orchestrator 承担额外维护职责
  - 风险/代价：scaffold --force 覆盖保护（ADR-006）仍是防误抹定制的兜底；W10 校验防止漂移
- 依据：用户 2026-08-21 询问"skill 是由谁来生成的"暴露职责未显式化
- 落地：orchestrator.md 职责第 9 条 + review-gate 规范回写指向执行者

### ADR-015 — skill 生成能力内化：skill-scaffold（orchestrator 自带能力）
- 日期：2026-08-21
- 状态：已确认
- 背景：ADR-014 确定 orchestrator 为 skill 生命周期唯一执行者，但生成能力仍散落为 AIFlow/scripts/scaffold_skills.py + .opencode/skills/node-template/ 两个位置，与"能力随 skill 打包"的内化方向（ADR-011）不一致；用户提出将生成能力内化到 orchestrator
- 决策：
  1. **新增 orchestrator 专用 skill `skill-scaffold`**：SKILL.md（生成工作流 + 纪律）+ `assets/node-template/`（骨架模板 + 节点详章模板）+ `scripts/scaffold_skills.py`（生成脚本）+ `references/nodes-schema.md`（nodes.json 字段规范）
  2. **迁移**：原 `.opencode/skills/node-template/`（含 node-doc-template.md）与 `AIFlow/scripts/scaffold_skills.py` 迁入 skill-scaffold；`nodes.json` 保持 `AIFlow/scripts/`（check_tracker/workflow_audit 共享的注册数据，单一事实源）
  3. **引用同步**：workflow_audit W10 模板路径、orchestrator 职责 #9、review-gate 规范回写、README/AIFlow-README/设计文档/A1 详章/92-术语表全部迁移到新路径
- 后果：
  - 正面：生成能力自包含（模板 + 脚本 + 规范一站式随 skill 走）；orchestrator 加载 skill-scaffold 即可完成生成，不依赖散落脚本；与 ADR-011 资产内化方向一致
  - 负面：脚本调用路径变长；nodes.json 仍驻留 AIFlow/scripts/（能力与数据分离，属有意保留——数据为多脚本共享）
  - 风险/代价：路径引用面较广，需全量校验无残留；scaffold 脚本根路径回溯改为 parents[4]，随目录结构调整需同步
- 依据：用户 2026-08-21 指示（"将生成skill的能力，内化到orchestrator中"）
- 落地：本 commit（skill-scaffold 创建 + node-template/scaffold 脚本迁入 + 全量引用迁移）

## 评审记录

| 日期 | 节点 | 结论 | 签字人 | 意见 |
|------|------|------|--------|------|
| 2026-08-19 | A1 需求与场景定义 | 通过 | 用户 | 评审意见（UC 二级编号、脚本改名、doc 平铺）已逐条落实后签字 |
| 2026-08-20 | A2 系统规格 | 通过 | 用户 | 编号体系梳理（BLOCK 编号、编号体系总览、主脉络）落地后签字；指标目标值按 spec-004 定稿 |
| 2026-08-20 | A3 接口规格 | 通过 | 用户 | 三项评审决策确认后签字：AXI4 统一总线、引脚复用按现方案、M-013 ≤100ms、高速 SPI(160MHz)待 B1（详见 ADR-009） |

## 异常与授权记录

| 日期 | 事项 | 授权人 | 说明 |
|------|------|--------|------|
| | | | |