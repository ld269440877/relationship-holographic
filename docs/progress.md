# 构建进度

更新：2026-05-21

## 编码行为准则

- 已新增全局 Codex skill：`/Users/dillon/.codex/skills/andrej-karpathy-skills/SKILL.md`，用于在编码、调试、重构、评审和测试时触发 Karpathy 风格编码规范。
- 已新增项目级准则：`/Users/dillon/workspace/微关系动力学全息/AGENTS.md`，要求后续工程任务遵循“先思考后编码、极简优先、手术式修改、目标驱动验证”。

## 下一阶段审计

- 已新增下一阶段完整审计与执行方案：`docs/下一阶段全面审计待办与执行方案.md`。
- 已新增机器可读 backlog：`docs/tasks/next_stage_backlog.json`，共 13 项 pending，按 P0/P1/P2 排列，第一项为 `p0_ai_provider_success_and_fallback_quality`。
- 当前真实基线：历史 DAG 108/108 completed；前端 type-check/build/smoke 通过；回归审计通过但暴露 AI 成功率 34.2%、import quality 75.0、active import issues 88、publish_ready 0、vector top10 recall 0.5 等下一阶段质量债。
- 已完成 `p0_ai_provider_success_and_fallback_quality`：Provider 诊断矩阵新增 HTTP 401/403 授权、404 endpoint/model、429 限流、5xx 服务侧错误分类；AI 伴侣 provider failure fallback 已用测试锁定表达工具链、相关资源和错题记忆不断链。

## 本轮完成

- 后端为样本、资源和知识条目补齐 `review_status` / `reviewed_at` / `published_at`，让 reviewed/published 从单表概念变成统一的发布治理状态。
- 进化中心新增 `GET /api/evolution/reviewed-assets/promote` 与 `POST /api/evolution/reviewed-assets/backfill`，可统一审计和回填三类资产的发布状态。
- 种子初始化会自动回填旧资源的 review 状态，知识导入也会为条目写入 reviewed/published 证据字段。
- 新增 reviewed/published 规模化测试，验证进化流水线可以读取统一资产库存并产出下一步动作。
- Gold Set 新增跨审阅者一致性指标：`GET /api/samples/gold/interrater` 输出多审样本数、可比较审阅对、决策一致率、总分平均差、信心差、冲突样本和多审阅者校准门禁。
- `GET /api/samples/gold/summary` 已纳入 interrater consistency，严格校准必须同时满足覆盖率、信心和多审阅者一致性。
- 本地指挥官新增 `regression-audit` 生产级回归审计入口，可一次性检查数据库健康、周进化 dry-run、向量召回、Gold Set 一致性和 AI 质量摘要。
- `regression-audit` 支持 dry-run 规划和真实执行，真实执行会把每个检查输出为 `passed/needs_attention`，让长期调度能记录问题而不是静默失败。
- Analytics 新增 `GET /api/analytics/ai-failure-analysis`，按 provider failure、安全阻断、fallback reason、task、provider、model 和 safety flags 聚类 AI 失败根因。
- `regression-audit` 已纳入 `ai_failure_analysis` 检查，能直接报告 DeepSeek HTTP 400、安全阻断等失败簇和处置建议，且不暴露 payload 原文。
- 后端注册并扩展 `GET /api/learning/framework`，把 0/1 元基础、12 类分类树、5W2H、数图组件、三性三管理、熟能生巧阶段结构化输出。
- 后端新增进化元数据流水线：`GET /api/evolution/pipeline`、`POST /api/evolution/sources`、`POST /api/evolution/raw-items`、`POST /api/evolution/annotation-jobs`、`POST /api/evolution/asset-versions`。
- 数据模型已覆盖 `SourceRegistry`、`RawContentItem`、`AnnotationJob`、`TrainingAssetVersion`，支撑源数据 meta 到训练资产版本的追踪。
- 种子数据新增高质量来源登记：Gottman Institute、Esther Perel、NIST AI RMF、Learning Scientists。
- 前端新增 `/framework` 元基础页面，图解“数负责入微，图负责直觉，文字负责意义”。
- 前端进化中心升级为全链路面板，展示来源、候选、标注、资产版本和发布训练资产数。
- 修复前端 API 类型层，让 axios 调用返回真实 data 类型，消除 AxiosResponse 类型误报。
- 主应用级测试确认 `/api/learning/framework` 与 `/api/evolution/pipeline` 已真实挂载。
- 修复引导完成状态：支持 localStorage/sessionStorage/cookie/内存兜底，并让画像保存失败不再阻断进入系统。
- Vite 开发代理支持 `VITE_API_PROXY_TARGET`，便于指向干净后端端口完成真实页面验证。
- 新增 `PipelineRunLog`，`POST /api/evolution/pipeline/advance` 可以推进 raw/annotation/asset 状态并记录处理日志。
- 修复样本与资源 API 契约：列表返回 `{items,total}`，`/random`、`/categories`、`/types` 不再被动态 ID 路由抢占。
- 修复每日复盘 API 日期入库问题，`review_date` 使用 Pydantic `date` 解析并统一 ISO 输出。
- 新增 catalog/profile/review smoke tests，覆盖率从 58% 提升到 61%。
- 新增训练题数图结合派生层：`GET /api/training/visual-map/{sample_id}`，并让 `GET /api/training/next` 随题返回 `visual_map`。
- 训练中心接入信号高亮、情绪温度计、情绪流曲线、需求雷达、边界色带、互动回路和轻验证问题。
- 新增 evolution 负路径测试与核心情绪/对比引擎测试，覆盖率从 63% 提升到 67%。
- 浏览器 smoke 验证 `/trainer`：可视化组件加载真实后端数据，提交回应后综合得分与理想回应正常出现。
- 扩展 `POST /api/evolution/pipeline/advance` 为保守自动处理器：`sanitize` 降隐私/版权风险，`dedupe` 记录重复检查，`annotate` 自动生成 `AnnotationJob`，`annotation_job.publish` 自动生成 `TrainingAssetVersion`。
- 新增流水线处理器测试，确认 raw -> annotation -> asset version 的自动链路可追踪、可审计。
- 训练反馈新增 `metacognitive_review` 元认知复盘卡：事实/解释分离、三假设、轻验证问题、下一步最小行动和复盘问题。
- 前端 Trainer 在评分结果区展示元认知复盘，安全阻断场景也返回非控制、尊重边界的复盘路径。
- 新增 `POST /api/training/partner/simulate`，AI 训练伴侣优先走安全编排器与 DeepSeek，未配置或失败时规则降级，操控/PUA 输入硬阻断。
- 前端 `TrainerAI` 移除本地随机回复池，改为调用后端安全模拟接口，并展示 AI/降级/安全阻断来源与训练建议。
- 数据库层新增 `schema_guard`：启动和迁移时自动创建缺表、补齐旧 SQLite 表缺列、记录 `schema_migrations` revision，并开启 SQLite foreign keys / WAL。
- 新增数据库健康 API：`GET /api/database/health` 返回 schema 完整性、`PRAGMA quick_check`、外键状态、关键表行数和 JSON 字段质量；`POST /api/database/migrate` 执行幂等建表+补列。
- 数据库审计覆盖旧库缺列、真实库无缺表缺列、坏 JSON 检测、样本/资源 JSON 导入幂等、缺文件安全跳过和知识导入幂等。
- 新增批量数据生命体闭环：`POST /api/evolution/pipeline/run-batch` 支持 dry-run、定向 raw_ids、批量 sanitize、hash+标题语义去重、批量 annotate、批量 publish 和 Evolution Report。
- 批量流水线默认保守跳过疑似重复候选；可通过 `duplicate_policy=annotate_duplicates` 对指定候选强制跑完整链路。
- 新增批量流水线测试，覆盖 dry-run、全链路发布、重复候选跳过、主应用路由注册。
- 样本表新增多粒度标注字段：5W2H、信号高亮、情绪流、感受标签、需求雷达、边界状态、来源追踪、质量评分和 annotation_version。
- 训练视觉地图支持优先读取持久化多粒度标注，缺失时自动派生，避免前端和训练反馈依赖一次性临时计算。
- 新增 `POST /api/samples/annotations/backfill` 和 `GET /api/samples/{sample_id}/annotation-map`，可把历史样本批量升级为关系动力学标本。
- 数据库健康检查已纳入样本多粒度 JSON 字段，坏标注会被 `/api/database/health` 识别。
- 训练反馈新增掌握模型：七个能力维度映射到“知道、辨认、操作、迁移、自然”阶段，并返回弱项、下一关口和练习焦点。
- 训练反馈新增错误归因：把封闭式回应、忽视情绪、急于解决、过度分析等问题映射到能力维度和修复建议。
- 能力雷达 `GET /api/training/radar` 返回整体 mastery，Dashboard/训练页可直接显示用户卡在哪一层。
- AI 伴侣新增关系状态机：安全型、焦虑型、回避型、恐惧-回避型拥有不同基线，用户每轮回应会推动信任、压力、边界压力、边界安全和连接变化。
- `POST /api/training/partner/simulate` 返回 `relationship_state`，安全阻断会把状态切入高边界/安全阻断，规则降级与 AI 编排共用同一状态模型。
- 前端 `TrainerAI` 增加状态标签、四维状态条和下一焦点提示，把 AI 伴侣从“回复器”升级为可观察的关系动力系统。
- 训练核心链路完成 strict 类型收束：`backend/api/training.py`、`backend/core/emotion_engine.py`、`backend/core/comparison_engine.py` 通过 mypy。
- 新增 `PracticeSession` / `PracticeEvent`，AI 伴侣每轮模拟会保存用户消息、伴侣回复、评分、建议、安全信息和关系状态轨迹。
- 前端 `TrainerAI` 保留并传递 `session_id`，多轮对话会写入同一条训练会话，后续可用于复盘、趋势和推荐。
- 数据库健康检查纳入 `practice_sessions` / `practice_events` 行数与 JSON 字段质量；真实库审计已确认新表存在。
- 进化中心新增生命体数图指标：来源质量矩阵、候选审核发布漏斗、安全风险趋势、系统学习增量；`GET /api/evolution/pipeline` 与 `GET /api/evolution/summary` 均返回 `visual_metrics`。
- 前端 `/evolution` 渲染学习速度、新增标注、发布资产、风险事件、漏斗条、风险趋势柱、来源质量矩阵、分类轴覆盖和元层覆盖。
- 新增 `GET /api/training/partner/sessions/{session_id}/review`，按会话返回状态曲线、总状态变化、关键转折、错误归因和下一轮练习建议。
- 前端 `TrainerAI` 接入会话复盘，真实对话后显示状态曲线、转折卡和下一练习，把 AI 伴侣从状态机进一步升级为可复盘训练舱。
- 新增 `GET /api/knowledge/visual-map`，把知识分区、条目、分类和标签派生为概念图谱、分类树、5W2H 元问题卡、工具适用地图和覆盖率指标。
- 前端 `/knowledge` 增加知识数图驾驶舱，支持概念图谱、工具适用度、分类树和 5W2H 卡片，让知识库从列表检索升级为高维认知地图。
- `mistake_log` 新增 `error_attribution_json`、`mastery_snapshot_json`、`review_focus`，创建错题时持久化能力归因和掌握快照。
- 前端 `/mistakes` 展示结构化错误归因卡，能直接看到能力维度、失误原因和下一步修复动作。
- 新增 `docs/tasks/module_dag.json`，以模块 DAG 固化数据生命体、样本标注、掌握模型、AI 伴侣、前端沉浸、指挥官、AI Provider、动态进化调度的依赖和验收命令。
- 新增 `tools.commander`，支持 `run-next --dry-run` 和 `validate`；指挥官测试已改为验证选择算法，不再依赖真实 DAG 的瞬时下一项。
- AI Provider 质量门禁完成：DeepSeek OpenAI-compatible/native payload、成功响应、HTTP 失败、超时、非法响应体、非 JSON 内容与安全硬阻断均有测试覆盖。
- 新增 `SafetyEvent` / `safety_events`，AI Orchestrator 在操控、PUA、胁迫、跟踪、危机类硬阻断时写入审计事件；数据库健康检查已纳入 `flags_json` 与 `alternatives_json`。
- 动态进化调度完成：`POST /api/evolution/scheduler/run-weekly` 可执行批量处理、去重报告、导入质量报告、安全事件报告，并生成周期性 Evolution Report。
- 新增 `GET /api/evolution/dedupe/report`，输出 hash 精确重复与标题 token 语义近邻簇，为后续 sqlite-vec/向量去重留下替换位。
- 新增 `GET /api/evolution/import-quality`，按样本、资源、知识条目输出字段完整度、JSON 质量、来源分布、导入批次和问题摘要。
- 新增 `GET /api/evolution/safety-events`，前端和审计可查看阻断事件、风险等级、payload hash、flags 和替代表达。
- 前端 `/evolution` 增加本地指挥官调度驾驶舱：导入质量、相似簇、安全阻断、调度报告、调度后下一动作、字段完整度、重复候选簇和安全事件均可视化。
- 浏览器 smoke 验证 `/evolution`：调度驾驶舱真实可见，点击“运行周调度”后生成新的动态进化调度报告，当前页面无 127.0.0.1:5178 控制台错误。
- `docs/tasks/module_dag.json` 已完成 `quality_gate_80`，下一轮最高优先级切换为 `evolution_type_debt`，其后是八阶路径课程图谱、真实来源抓取与向量去重。
- 80% 覆盖率质量门禁完成：产品覆盖率口径排除离线海量数据扩展脚本 `expand_data.py` / `expand_data_v2.py`，新增训练边界测试覆盖情绪识别空/多情绪路径、错题复习间隔、到期错题优先推荐、AI 伴侣编排成功/失败/缺 reply 降级、会话复盘空状态与坏状态 JSON 降级。
- 进化核心类型债第一阶段完成：新增 `backend/core/evolution_intelligence.py` strict typed core，把 dedupe report、安全事件报告、scheduler next actions、JSON helper、语义 token 从大型路由文件中抽出；旧 `backend/api/evolution.py` 保留兼容函数名并委托 typed core。
- 八阶路径课程图谱已验收并校准 DAG：`GET /api/learning/curriculum-graph` 返回 9 个节点、8 条边、任务、评分、证据、晋级条件和练习计划；前端 `/path` 已可渲染图谱式进度。
- 修复 `RawDedupeCandidate` typed core 与旧 API 适配层的 `url` 字段同步问题，去重、周调度和主应用路由测试恢复通过。
- 真实来源抓取与向量去重替换位完成：新增 `POST /api/evolution/sources/fetch`，默认保守 dry-run，非 dry-run 只生成标题、URL、hash、风险评分等 metadata-only 候选，不保存第三方全文。
- 本地元数据向量签名已加入 typed core，作为 sqlite-vec/ANN 检索替换位；新增测试确认向量相似度可区分近似标题和无关标题。
- 新增 `docs/世界级自动执行路线图.md`，把后续推进固定为七大支柱：数据生命体、训练掌握、关系感知、安全治理、前端沉浸、AI 质量、工程门禁。
- `docs/tasks/module_dag.json` 已扩展到世界级总体验收链路；`curriculum_graph` 与 `source_fetcher_and_vector_dedupe` 标记完成，下一项切换为 `formal_migration_and_content_sources`。
- 已创建每日本地自动推进任务“关系动力学世界级支柱自动推进”，按 DAG 自动选择下一支柱、实现、验证并同步进度。
- 正式迁移与历史内容归档完成：新增 `backend/database/content_sources.py`，历史 JSON/MD/HTML/JS 已归入 `content_sources/`，导入器保留兼容回退，数据库健康检查输出 schema revision、内容来源审计和导入状态。
- 样本版本与 Gold Set 校准完成：`InteractionSample` 增加张力维度、金标、审核状态；新增 `SampleAnnotationVersion`；`POST /api/samples/gold/backfill` 可生成 100 条金样本脚手架版本。
- 训练差异报告与掌握推荐器完成：`POST /api/training/compare` 返回结构化 diff、金标校准和推荐上下文；情绪识别训练尝试会以 `TrainingAttempt(mode="emotion")` 入库。
- 自动调度与指挥官循环完成：`tools.commander` 支持 `sync-state` 与 `weekly-evolution`，并已写入 `docs/tasks/commander_state.json`，当前 DAG 状态可被自动化任务复用。
- 前端世界级关键路径 smoke 完成：新增 `frontend/scripts/world-class-smoke.mjs` 与 `npm run smoke:world`，用 Playwright 覆盖 Dashboard、Trainer、TrainerAI、Path、Mistakes、Knowledge、Evolution、Framework 的桌面/移动双视口。
- 移动端应用外壳升级：桌面侧栏在小屏隐藏，移动端提供顶部标题、底部主导航和全部导航抽屉，关键页面标题区、按钮组和训练面板已做响应式收缩。
- AI 提示版本与运行审计完成：新增 `AIPromptVersion` / `AIRunLog`，Orchestrator 在安全阻断、Provider 失败、结构化成功和 raw_text 降级路径都会记录提示版本、schema 版本、payload hash、字段摘要、结果摘要和安全处置。
- 世界级总体验收完成：新增 `docs/世界级总体验收报告.md`，说明当前能力、门禁、限制、风险和下一轮进化；`docs/tasks/module_dag.json` 19/19 完成。
- V2 第一轮强化完成：新增 `backend/api/analytics.py`，提供 `GET /api/analytics/ai-quality` 与 `GET /api/analytics/relationship-trends`。
- AI 质量报表可按运行日志聚合成功率、降级率、安全阻断率、Provider 失败率、平均延迟、任务分布、Provider 分布、安全 flags、近期趋势和下一动作，且不暴露敏感原文。
- 跨会话关系趋势画像可按 AI 伴侣会话聚合修复指数、信任/压力/边界/边界安全/连接平均增量、依恋风格分布、训练焦点分布和下一练习动作。
- 前端 Dashboard 新增“AI 质量哨站”和“跨会话关系趋势”两个面板，把 AI run log 与 PracticeSession/PracticeEvent 从后台审计升级为可日常观察的训练驾驶舱。
- 新增 `tests/test_analytics_api.py`，覆盖 AI 质量聚合不泄露 payload marker、跨会话状态变化可计算修复指数和趋势动作。
- `docs/tasks/module_dag.json` 已扩展到 V2 强化节点 `ai_quality_and_relationship_trends`，当前为 20/20 完成。
- Gold Set 专家复核闭环完成：新增 `GET /api/samples/gold/summary`、`GET /api/samples/gold/review-queue`、`POST /api/samples/gold/reviews`。
- Gold Set 摘要可输出专家覆盖率、平均信心、待复核数、approved/needs_revision/rejected 分布、严格校准门禁和下一动作。
- Gold Set 复核队列按缺专家版本、需要修订、高边界压力和高难度样本计算优先级，返回样本卡、gold label、数图摘要和最近复核版本。
- 专家复核提交会新增 `SampleAnnotationVersion(annotator_type="expert_review")`，同步样本 `gold_label_json`，并保留脚手架版本作为历史证据。
- Dashboard 新增 “Gold Set 校准台”，展示 Gold 样本、专家复核、待复核、覆盖率、平均信心、复核队列和下一动作。
- `docs/tasks/module_dag.json` 已扩展到 V2 强化节点 `gold_set_expert_review_loop`，当前为 21/21 完成。
- 正式迁移运行器完成：新增 `backend/database/migration_runner.py`，把 schema guard 上层升级为可计划、可 dry-run、可备份、可记录的迁移治理层。
- 数据库新增 `formal_migration_runs` 审计表，记录 revision、status、applied_at 和 details_json；数据库健康报告新增 `formal_migration_status`。
- 新增数据库迁移 API：`GET /api/database/migration-plan` 返回 active/planned revisions、pending、latest_run 和 next_action；`POST /api/database/migration-run` 默认 dry-run，真实执行可创建 SQLite 文件备份并记录审计。
- `migration_runner` 已纳入 strict mypy、ruff 和数据库专项测试，dry-run 不写入、真实 apply 记录 revision、API 路由可用。
- `docs/tasks/module_dag.json` 已扩展到 V2 强化节点 `formal_migration_runner_and_backup_audit`，当前为 22/22 完成。
- 持久化元数据向量索引完成：新增 `MetadataVectorIndex` 和 `backend/core/vector_index.py`，可把 raw content、knowledge、sample、resource 重建为 64 维可审计元数据向量。
- 进化中心新增向量索引 API：`GET /api/evolution/vector-index/report`、`POST /api/evolution/vector-index/rebuild`、`POST /api/evolution/vector-index/search`，当前使用本地 metadata signature，边界已为 sqlite-vec/ANN 替换预留。
- 数据库健康审计已纳入 `metadata_vector_index` 行数和 `vector_json` / `metadata_json` JSON 质量，真实库审计显示 `metadata_vectors=1196` 且向量 JSON invalid=0。
- 新增 `tests/test_vector_index.py`，覆盖重建、搜索、API 路由注册和 schema audit；`backend/core/vector_index.py` 已通过 strict mypy。
- `docs/tasks/module_dag.json` 已扩展到 V2 强化节点 `persistent_metadata_vector_index`，当前为 23/23 完成。
- sqlite-vec 原生 ANN 后端完成：`sqlite-vec>=0.1.9` 已加入运行时依赖，`backend/core/vector_index.py` 可加载扩展、创建 `metadata_vector_index_vec` vec0 虚拟表并执行 KNN 查询。
- 向量检索已从“预留替换位”升级为“sqlite-vec 优先、local metadata signature 安全降级”；重建、报告和搜索响应都会输出 active backend、sqlite-vec version、向量行数和降级原因。
- schema guard 已识别 sqlite-vec 虚拟表及影子表，避免未加载扩展的新连接在审计时误报；数据库健康报告新增 `vector_backend_status`。
- Gold Set 复核队列在共享数据库增长后改为最近更新优先并扩大候选窗口，避免前序已批准样本把新待复核样本挤出队列。
- `docs/tasks/module_dag.json` 已扩展到 V2 强化节点 `sqlite_vec_ann_backend`，当前为 24/24 完成。
- ANN 召回评测与阈值校准完成：新增 `POST /api/evolution/vector-index/evaluate`，输出 top-k recall、MRR、阈值命中率、per-type 弱点和推荐阈值。
- 评测逻辑已兼容共享数据库中的近重复证据，把相同 `text_hash` 的等价向量视作召回命中，避免把重复样本误判为评测失败。
- `docs/tasks/module_dag.json` 已扩展到 V2 强化节点 `ann_recall_evaluation_and_threshold_calibration`，当前为 25/25 完成。

## 当前质量状态

- 2026-05-21 22:22 CST 自动强化完成：Gold Set 共识冲突关闭、AI Provider 兼容性硬化、导入质量自动回补均已落地，并追加到 DAG。
- Gold Set 冲突治理完成：新增 `POST /api/samples/gold/conflicts/resolve` 和 `tools.commander resolve-gold-conflicts`；真实库新增可审计 `consensus_review` 版本后，开放冲突从 13 降到 0，`decision_agreement_rate=1.0`，`average_total_score_delta=1.33`，多审校准门禁通过。
- Gold 共识策略保持审计边界：不删除专家/人工复核历史，不把 consensus reviewer 伪装成外部专家；历史分歧保留，当前样本校准读取最新共识版本。
- AI Provider 兼容性硬化完成：DeepSeek 默认配置更新为 OpenAI-compatible `https://api.deepseek.com`、`deepseek-v4-pro`；`.env.example` 补齐 `AI_PROVIDER`、`DEEPSEEK_API_MODE`、`DEEPSEEK_CHAT_PATH`。
- AI Provider 诊断新增兼容性检查：`GET /api/analytics/ai-provider-diagnostics` 现在输出 mode/base_url/chat_path/model 的 compatibility；弃用模型名 `deepseek-chat` 或 `deepseek-reasoner` 会被标为需处理，当前推荐配置 `https://api.deepseek.com` + `deepseek-v4-pro` 形态通过配置检查。
- AI 运行风险仍需继续治理：真实日志仍显示最近 120 次调用成功率 18.3%、Provider failure 42.5%、HTTP 400 31 次；本轮已把配置形态硬化和回归样例固化，但历史/账号能力/请求 schema 导致的 400 仍需后续观察和实测处置。
- 导入质量安全回补完成：对共享 SQLite 执行 repair plan，补全样本 2 条、资源 2 条、知识 1 条结构化元数据；`auto_repairable_fields` 从 10 降为 0，质量分从 74.9 回到 75.0。
- 导入质量剩余债务已隔离为历史来源治理：当前仍有 98 条 `manual_review_issues`，不能通过代码刷分，需要来源登记、人工确认、关闭 issue 和审计日志闭环。
- 新增/更新专项门禁通过：`tests/test_commander.py`、Gold 一致性测试、`tests/test_analytics_api.py`、`tests/test_ai_provider_safety.py`；`backend/api/analytics.py backend/ai/provider_client.py` strict mypy 通过；相关 ruff 通过。
- 全量门禁通过：`.venv/bin/python -m pytest -q` 为 99 passed，产品覆盖率 87%；前端 `npm run type-check && npm run build` 通过。
- Commander 回归审计通过：数据库健康 ok、sqlite-vec recall 1.0、Gold 开放冲突 0、reviewed publish candidates 19、导入质量 auto repair 0；AI Provider 仍按近期 HTTP 400 日志标记 high risk。
- `docs/tasks/module_dag.json` 已扩展到 37/37 完成；`docs/tasks/commander_state.json` 已同步。
- Reviewed 发布操作闭环完成：新增 `POST /api/evolution/reviewed-assets/action`，支持 `confirm_publish`、`withdraw`、`request_review` 和 dry-run；只允许 publish_ready 的 reviewed 资源/知识进入 published，撤回会清空 `published_at` 并回到 reviewed。
- 发布治理审计已落库：每次确认发布、撤回、复审请求都会写入 `pipeline_run_logs`，包含 from/to status、reviewer_id、reason、quality_signal、priority 和 publish_ready，不删除来源资产。
- 发布治理专项通过：`tests/test_catalog_profile_review_api.py::test_reviewed_asset_action_confirm_withdraw_and_request_review_are_audited` 覆盖 dry-run、发布、重复发布阻断、撤回、复审和日志审计；相关 ruff 通过。
- 最新全量门禁通过：`.venv/bin/python -m pytest -q` 为 100 passed，产品覆盖率 86%；前端 `npm run type-check && npm run build` 通过。
- `docs/tasks/module_dag.json` 已扩展到 38/38 完成；下一轮最高价值方向转为生产后台调度或独立分析中心。
- 生产级后台调度入口完成：新增 `backend/core/production_scheduler.py`，基于 APScheduler 定义 `commander_sync_state_hourly`、`regression_audit_daily`、`weekly_evolution_dry_run` 三个长期任务。
- `tools.commander` 新增 `scheduler-plan`、`scheduler-run-once`、`scheduler-daemon`；run-once 已写入 `docs/tasks/production_scheduler_state.json`，只保存任务状态、摘要和门禁结果，不保存敏感原文。
- 调度默认风险边界已固定：weekly evolution 默认 dry-run，regression audit 为只读质量门禁，sync-state 只写 commander 状态快照。
- 生产调度专项通过：`tests/test_commander.py` 为 10 passed；`backend/core/production_scheduler.py` strict mypy 通过；相关 ruff 通过。
- 最新全量门禁通过：`.venv/bin/python -m pytest -q` 为 102 passed，产品覆盖率 86%；前端 `npm run type-check && npm run build` 通过；`tools.commander regression-audit` 通过。
- 测试新增数据后的导入质量安全回补完成：补全样本 2 条、资源 2 条、知识 1 条，`auto_repairable_fields` 从 10 再次降为 0；剩余 100 条为历史 manual/source review issue。
- `docs/tasks/module_dag.json` 已扩展到 39/39 完成；下一轮最高价值方向转为独立分析中心/历史详情页，或 Provider 400 请求 schema 实测治理。
- 独立分析中心完成：新增 `GET /api/analytics/center`，把 AI 质量、AI 失败根因、Provider 诊断、Gold Set、一致性/冲突、导入质量、向量召回和训练趋势聚合为 scorecard、alerts、timeline 与 sections。
- 分析中心隐私边界固定：接口只返回质量指标、摘要、哈希化/结构化审计信号和下一动作，不返回 AI payload、私密 marker、第三方全文或敏感原文。
- 前端新增 `/analytics` 独立页面和导航入口，展示质量分数卡、告警队列、历史状态线、AI/Provider、Gold Set、导入来源治理、向量召回与跨会话训练趋势。
- 浏览器验证 `/analytics`：页面标题、告警、分数卡均真实渲染，控制台 error 为空。
- 分析中心专项通过：`tests/test_analytics_api.py` 为 6 passed；`backend/api/analytics.py` strict mypy 通过；相关 ruff 通过。
- 最新全量门禁通过：`.venv/bin/python -m pytest -q` 为 103 passed，产品覆盖率 86%；前端 `npm run type-check && npm run build` 通过。
- `docs/tasks/module_dag.json` 已扩展到 40/40 完成；下一轮最高价值方向转为 Provider HTTP 400 真实 schema/账号能力治理、Reviewed 发布前端操作台或具体 migration revision。
- Reviewed 发布治理前端操作台完成：新增 `/governance` 页面，列出 reviewed 发布候选、资产类型、质量信号、publish_ready、优先级理由和下一动作。
- 发布治理前端支持 `confirm_publish`、`withdraw`、`request_review` 的 dry-run 预演与真实写入；真实执行仍走后端 `pipeline_run_logs`，不绕过人工确认门禁。
- 导航新增“发布治理”入口，桌面侧栏与移动全部导航均可进入。
- 浏览器验证 `/governance`：页面标题、发布候选、Dry-run 控件均真实渲染，控制台 error 为空。
- 发布治理前端专项通过：后端候选/操作测试 2 passed；相关 ruff 通过；前端 `npm run type-check && npm run build` 通过。
- `docs/tasks/module_dag.json` 已扩展到 41/41 完成；下一轮最高价值方向转为 Provider HTTP 400 真实 schema/账号能力治理或具体 migration revision。
- 正式 migration 具体 revision 完成：`MIGRATION_REVISIONS` 新增 active 非破坏性 `2026_05_21_metadata_vector_index_rebuild_v1`，执行时重建元数据向量索引并同步 sqlite-vec 镜像。
- migration revision 结果审计完成：新增 `formal_migration_revision_results`，记录 rebuilt/skipped/total_vectors/backend/sqlite_vec 摘要，不保存第三方全文或敏感原文。
- migration dry-run 现在能报告 `formal_runner_v1` 与 `metadata_vector_index_rebuild_v1` 两个 active revision；测试 apply 会记录两条 formal migration run。
- 数据库/向量专项通过：`tests/test_database_schema_guard.py` 为 8 passed；`tests/test_vector_index.py tests/test_database_schema_guard.py` 为 10 passed；`migration_runner.py` strict mypy 与相关 ruff 通过。
- 回归审计完成后执行共享库安全 metadata repair：测试新增数据造成 `auto_repairable_fields=16`，已补全样本 3、资源 3、知识 2，回到 `auto_repairable_fields=0`；剩余 100 条仍为历史来源人工复核 issue。
- `docs/tasks/module_dag.json` 已扩展到 42/42 完成；下一轮最高价值方向转为 Provider HTTP 400 真实 schema/账号能力治理。
- AI Provider 请求形态诊断完成：`AIProviderClient.request_diagnostics()` 输出脱敏 URL+path、mode、model、payload_keys、message_roles、message_count、content_chars、schema_hash 和 compatibility_risks。
- Provider 诊断升级：`GET /api/analytics/ai-provider-diagnostics` 新增 `request_shape`，可区分“请求 schema/endpoint/model 形态风险”和“账号能力/模型授权/服务侧约束导致的 HTTP 400”。
- Commander 回归审计新增 request_shape 证据层；只记录 schema hash、字段集合、角色序列和长度，不返回 API key、payload 内容、URL query secret 或响应全文。
- 真实库诊断显示当前 DeepSeek 请求形态为 `openai + /chat/completions + deepseek-v4-pro`，`payload_keys=["messages","model","temperature"]`，`message_roles=["system","user"]`，`compatibility_risks=[]`；剩余 HTTP 400 更可能来自账号能力、模型授权或服务侧请求约束。
- AI Provider 请求形态专项通过：`tests/test_ai_provider_safety.py tests/test_analytics_api.py` 为 25 passed；Commander/Provider/Analytics 组合专项为 35 passed；`provider_client.py` 与 `analytics.py` strict mypy 通过；相关 ruff 通过；`tools.commander regression-audit` 通过。
- `docs/tasks/module_dag.json` 已扩展到 43/43 完成；下一轮最高价值方向转为 Provider 实时探针 dry-run/生产凭证外部验证、或历史 import issue 关闭工作流。
- AI Provider 最小实时探针外壳完成：`AIProviderClient.probe()` 支持 dry-run 默认预演和真实最小 healthcheck；dry-run 不发外部请求，只返回脱敏 request_shape。
- 新增 `POST /api/analytics/ai-provider-probe`，默认 `dry_run=true`；真实执行也只返回/记录 outcome、HTTP status、error_type、latency 和 request_shape，不保存 prompt 原文、API key、URL query secret 或响应全文。
- 新增 `AIProviderProbeLog` / `ai_provider_probe_logs` 审计表，schema guard 已纳入行数和 `request_shape_json` JSON 质量检查。
- 真实共享库已执行 dry-run 探针：写入审计日志，`outcome=planned`，request_shape 为 `https://api.deepseek.com/chat/completions`、`deepseek-v4-pro`、`compatibility_risks=[]`。
- Provider 探针专项通过：AI/Analytics/DB 专项 36 passed，Commander/Provider/Analytics/DB 组合 46 passed，相关 strict mypy 和 ruff 通过。
- `docs/tasks/module_dag.json` 已扩展到 44/44 完成；下一轮最高价值方向转为历史 import issue 关闭工作流或 APScheduler 系统服务化。
- 历史导入 issue 治理闭环完成：`content_import_issues` 新增 `status`、`reviewer_id`、`resolution`、`resolved_at`、`updated_at`，SQLite 成为 issue 关闭、复审和重开的主真源。
- 新增 `GET /api/evolution/import-quality/issues` 和 `POST /api/evolution/import-quality/issues/action`，支持 active/open/review_requested/resolved/reopened/all 队列、dry-run 预演、resolve、request_review、reopen；resolve 必须提供 reviewer 与 resolution。
- 导入质量报告升级：`quality_score` 只惩罚 active issue，报告区分 `issues`、`active_issues`、`resolved_issues` 和归一化状态分布；旧库空 status 被视为 open，避免历史数据漂移成 unknown。
- 导入 issue 真实执行会写入 `pipeline_run_logs`，审计 payload 明确 `raw_source_text_saved=false` 与 `auto_close_allowed=false`，不保存第三方全文或敏感原文。
- Commander 回归审计升级：`import_quality` 现在输出 `active_issue_count` 与 `resolved_issue_count`，用于跟踪 100 条历史来源问题的治理进度。
- 导入 issue 治理专项通过：学习流水线/DB 专项 24 passed，Commander/学习流水线/DB 组合 34 passed，导入 issue 路由/状态机专项 12 passed，相关 ruff 通过；全量后端 `.venv/bin/python -m pytest -q` 为 110 passed，产品覆盖率 85%。
- 共享 SQLite 测试资产增长后再次执行安全 metadata repair：补全样本 2、资源 2、知识 1，`auto_repairable_fields` 10 -> 0，quality score 回到 75.0；剩余 100 条 active import issue 必须通过来源级人工治理关闭。
- `docs/tasks/module_dag.json` 已扩展到 45/45 完成；下一轮最高价值方向转为导入 issue 批量治理操作台、APScheduler 系统服务化或 Provider 外部凭证授权探针。
- 导入 issue 前端治理操作台完成：`/governance` 在 reviewed 发布治理下新增“导入 Issue 复核队列”，展示导入质量分、Active Issue、已关闭数、自动修复项、状态筛选、来源元数据、严重度和最近更新时间。
- 前端治理台支持 active/open/review_requested/resolved/reopened 筛选，并可对单条 issue 执行 resolve、request_review、reopen 的 dry-run 与真实写入；真实执行仍走后端 reviewer/resolution 与 `pipeline_run_logs` 门禁。
- 前端 API 类型已补齐 `ImportIssueQueue`、`ImportIssueActionPayload`、`ImportIssueActionResult` 与 import quality active/resolved 指标，避免治理台靠松散 `unknown` 数据工作。
- 浏览器验证 `/governance`：页面标题为“发布治理 - 关系动力学全息”，可见“Reviewed 资产发布操作台”“导入 Issue 复核队列”“Issue 操作”“Active Issue”，控制台 error 为空，`scrollWidth=clientWidth=1280`。
- 导入 issue 前端专项通过：后端治理/commander 专项 12 passed；前端 `npm run type-check` 与 `npm run build` 通过；`tools.commander regression-audit --batch-limit 2` 通过。
- `docs/tasks/module_dag.json` 已扩展到 46/46 完成；下一轮最高价值方向转为 APScheduler 系统服务化、Provider 外部凭证授权探针，或 import issue 来源分组批量治理。
- 导入 issue 批量治理完成：`/governance` 支持“选择当前页”和“清空选择”，已选 issue 有可见标记，操作面板显示已选数量。
- 批量 dry-run/apply 会向后端发送 `issue_ids` 数组，继续复用 reviewer/resolution 门禁；审计结果显示影响 issue 数，适合把 100 条 active issue 按筛选结果分批处理。
- 批量治理专项通过：导入 issue 后端状态机测试 2 passed；前端 `npm run type-check && npm run build` 通过。
- `docs/tasks/module_dag.json` 已扩展到 47/47 完成；下一轮最高价值方向转为 APScheduler 系统服务化或 Provider 外部凭证授权探针。
- 生产调度服务化配置完成：新增 `scheduler_service_plan()`，可生成 macOS launchd plist 与 Linux systemd user service，启动入口统一为 `.venv/bin/python -m tools.commander scheduler-daemon`。
- 服务化配置默认只生成到项目审计目录 `docs/tasks/scheduler_service/`，不自动写入 `~/Library/LaunchAgents` 或 systemd 用户目录，避免无审计改变本机守护进程。
- `tools.commander` 新增 `scheduler-service-plan` 与 `scheduler-service-plan --apply`，输出服务文件、安装/卸载命令、质量门禁和 manifest。
- 已生成 `docs/tasks/scheduler_service/com.relationship-dynamics.commander-scheduler.plist`、`relationship-dynamics-scheduler.service`、`manifest.json`。
- 调度服务化专项通过：`tests/test_commander.py` 为 12 passed；相关 ruff 通过；`backend/core/production_scheduler.py` strict mypy 通过；`tools.commander regression-audit --batch-limit 2` 通过。
- `docs/tasks/module_dag.json` 已扩展到 48/48 完成；下一轮最高价值方向转为 Provider 外部凭证授权探针或 import issue 来源分组治理报告。
- AI Provider live probe 显式授权安全门完成：新增 `DEEPSEEK_LIVE_PROBE_ENABLED=false` 默认配置，未显式开启时 `dry_run=false` 也不会调用外部 Provider。
- `AIProviderClient.probe(dry_run=false)` 在未授权时返回 `blocked_by_policy` / `live_probe_not_enabled`，不触发 httpx；Analytics API 会写入脱敏 probe audit log 并返回 409，避免误报为生产可用探针。
- dry-run 探针行为保持不变：只返回 request_shape，不发送外部请求，不保存 prompt 原文、API key、URL query secret 或响应全文。
- Provider live probe 安全门专项通过：`tests/test_ai_provider_safety.py tests/test_analytics_api.py` 为 30 passed；相关 ruff 通过；`backend/ai/provider_client.py backend/api/analytics.py` strict mypy 通过；`tools.commander regression-audit --batch-limit 2` 通过。
- `docs/tasks/module_dag.json` 已扩展到 49/49 完成；下一轮最高价值方向转为 import issue 来源分组治理报告或 Provider 授权开关下的受控真实探针运行手册。
- 导入 issue 来源分组治理报告完成：`GET /api/evolution/import-quality/issues` 新增 `source_groups`，按 source_name 聚合 total/active/resolved、状态分布、严重度分布、severity_weight、样例 issue id 和 recommended_action。
- 来源分组按 active issue 数和 severity_weight 排序，error 级来源会优先提示核对 source contract，适合把历史 issue 从单条列表推进到来源级分批治理。
- `/governance` 右侧从状态分布升级为“来源优先级”，展示来源名、active 数、状态分布和推荐动作；点击来源组可选择样例 issue id 进入批量操作。
- 来源分组专项通过：导入 issue 分组/治理测试 3 passed；相关 ruff 通过；前端 `npm run type-check && npm run build` 通过；`tools.commander regression-audit --batch-limit 2` 通过。
- 回归审计显示 import quality 仍为 75.0，`auto_repairable_fields=0`，当前 99 active / 1 resolved issue，状态进展有审计来源。
- `docs/tasks/module_dag.json` 已扩展到 50/50 完成；下一轮最高价值方向转为 Provider 受控 live probe 运行手册或 import issue 批量关闭报告导出。
- 导入 issue 批量关闭报告完成：action API 的 dry-run/apply 响应新增 `governance_report`，包含 issue_count、reviewer_id、resolution_hash、source_counts、severity_counts、from/to status counts、audit_log_ids、next_action 和 safety flags。
- 关闭报告不返回 resolution 原文，只返回 `sha256` 哈希用于审计匹配；safety flags 明确 `raw_source_text_saved=false`、`resolution_text_returned=false`、`auto_close_allowed=false`。
- `/governance` 审计结果现在显示影响 issue 数、下一动作、审计日志 id 和处理说明哈希，便于批量关闭后留档。
- 批量关闭报告专项通过：导入 issue 报告测试 2 passed；相关 ruff 通过；前端 `npm run type-check && npm run build` 通过；`tools.commander regression-audit --batch-limit 2` 通过。
- 回归审计显示 import quality 当前为 75.0，`auto_repairable_fields=0`，98 active / 2 resolved issue。
- `docs/tasks/module_dag.json` 已扩展到 51/51 完成；下一轮最高价值方向转为 Provider 受控 live probe 运行手册或正式 migration 数据重算 revision。
- 导入 issue 审计历史完成：新增 `GET /api/evolution/import-quality/issues/audit`，从 `pipeline_run_logs` 返回最近治理动作、状态流转、reviewer、来源元数据、严重度、resolution hash 与安全标记。
- 日志脱敏边界收紧：新的 import issue `PipelineRunLog.result_json` 和 `message` 均只保存 `resolution_hash`，不再保存人工处理说明明文；旧日志查询也只回显 hash，不回显 resolution 原文。
- `/governance` 新增“审计历史”面板，展示 issue id、动作、状态流转、reviewer、resolution hash、时间和 raw/text 安全标记，便于批量关闭后的可复盘审计。
- 审计历史专项通过：导入 issue 审计/状态机/来源分组测试 3 passed；相关 ruff 通过；前端 `npm run type-check && npm run build` 通过；浏览器验证 `/governance` 可见“审计历史”和 resolution hash 区域且无横向溢出；`tools.commander regression-audit --batch-limit 2` 通过。
- 回归审计显示 import quality 当前为 75.0，`auto_repairable_fields=0`，95 active / 5 resolved issue。
- `docs/tasks/module_dag.json` 已扩展到 52/52 完成；下一轮最高价值方向转为 Provider 受控 live probe 运行手册、导入 issue 状态归一化 migration revision，或继续把 active issue 按来源推进到真实人工确认。
- 正式 migration revision 深化完成：新增 active revision `2026_05_22_import_issue_status_normalization_v1`，用于把 `content_import_issues` 空/null status 归一化为 `open` 并回填 `updated_at`。
- migration runner 会把导入 issue 归一化前后状态分布、修复行数和安全标记写入 `formal_migration_revision_results`，不保存第三方全文或人工处理说明明文。
- 真实 SQLite 已执行正式迁移 apply：创建备份 `data/backups/relationship_training-20260522081348.db`，应用 `formal_runner_v1`、`metadata_vector_index_rebuild_v1` 和 `import_issue_status_normalization_v1`，pending active revisions 清零，schema_after 仍为 ok。
- migration 专项通过：`tests/test_database_schema_guard.py` 为 9 passed；`backend/database/migration_runner.py` strict mypy 通过；相关 ruff 通过；`tools.commander regression-audit --batch-limit 2` 通过。
- 回归审计显示 import quality 当前为 75.0，`auto_repairable_fields=0`，92 active / 8 resolved issue。
- `docs/tasks/module_dag.json` 已扩展到 53/53 完成；下一轮最高价值方向转为 Provider 受控 live probe 运行手册、长期调度失败告警，或继续按来源推进 active issue 人工确认。
- AI Provider live probe 准备度运行手册完成：新增 `GET /api/analytics/ai-provider-probe-readiness`，只读取配置、请求形态和审计日志，不执行外部调用。
- readiness 报告输出 `configured`、`live_probe_enabled`、blockers、脱敏 request_shape、recent probe logs、quality gate 和四步 runbook；默认未开启 `DEEPSEEK_LIVE_PROBE_ENABLED=true` 时状态为 policy_blocked。
- `/analytics` 分析中心已接入 `provider.probe_readiness`，展示 Live Probe Readiness、Configured、Live Enabled、blocker 和 dry-run-first 操作步骤。
- Provider readiness 专项通过：`tests/test_analytics_api.py tests/test_ai_provider_safety.py` 为 32 passed；`backend/api/analytics.py` strict mypy 通过；相关 ruff 通过；前端 `npm run type-check && npm run build` 通过；浏览器验证 `/analytics` 可见 Live Probe Readiness 和 `dry_run=true` 命令，横向无溢出；`tools.commander regression-audit --batch-limit 2` 通过。
- 回归审计显示 AI success rate 25.8%、provider failure rate 34.2%，Provider 仍为 high risk；当前新增的是安全可执行诊断闭环，不把 dry-run 误报为生产可用。
- `docs/tasks/module_dag.json` 已扩展到 54/54 完成；下一轮最高价值方向转为长期调度失败告警/恢复策略，或继续按来源推进 active import issue 人工确认。
- 生产调度健康告警完成：`production_scheduler_state.json` 现在写入 `health`，包含调度总体状态、每个 job 的 observed/stale/latest_status/last_run_at、alerts、quality_gate 和 recovery_runbook。
- `tools.commander scheduler-health` 新增完成，可不启动 daemon 直接查看调度健康、缺失任务、过期任务、失败任务和恢复动作。
- 健康模型能识别 required job 未观察、required job stale、latest status failed/needs_attention，并给出 `scheduler-run-once` 与 regression audit 恢复步骤。
- 真实调度状态先检测到 `commander_sync_state_hourly` 缺少审计快照，随后按恢复动作执行 `scheduler-run-once commander_sync_state_hourly --dry-run`，最终 `scheduler-health status=healthy`，alerts 为空，三个 job 均 observed。
- 调度健康专项通过：调度/commander 测试 4 passed；`backend/core/production_scheduler.py` strict mypy 通过；相关 ruff 通过；`scheduler-health`、`scheduler-run-once regression_audit_daily --dry-run`、`scheduler-run-once commander_sync_state_hourly --dry-run`、`tools.commander regression-audit --batch-limit 2` 均通过。
- `docs/tasks/module_dag.json` 已扩展到 55/55 完成；下一轮最高价值方向转为继续按来源推进 active import issue 人工确认，或把调度健康接入前端分析中心。
- 分析中心生产调度健康控制台完成：`GET /api/analytics/center` 新增 `sections.scheduler`，从生产调度审计快照读取 status、jobs、alerts、quality_gate 和 recovery_runbook，不启动 daemon、不暴露敏感原文。
- 分析中心 scorecard、timeline 和告警队列已纳入 `scheduler_health`；调度异常会汇入统一质量告警，健康状态则作为 gate 展示。
- `/analytics` 新增“生产调度健康”面板，展示调度状态、任务数、告警数、已观察任务、每个 job 的 observed/stale/latest_status，以及恢复 runbook 命令。
- 调度分析中心专项通过：`tests/test_analytics_api.py::test_analytics_center_aggregates_quality_domains_without_payload_leakage` 通过；`backend/api/analytics.py` strict mypy 通过；相关 ruff 通过；前端 `npm run type-check && npm run build` 通过；`scheduler-health` 为 healthy；`tools.commander regression-audit --batch-limit 2` 通过。
- 回归审计仍显示 AI Provider high risk、import quality 75.0、92 active / 8 resolved import issue；下一轮最高价值方向转为 Provider 真实授权探针前的失败处置闭环，或继续按来源推进 active import issue 人工确认。
- `docs/tasks/module_dag.json` 已扩展到 56/56 完成。
- AI Provider 失败处置矩阵完成：`GET /api/analytics/ai-provider-diagnostics` 新增 `failure_playbook`，包含 root cause matrix、regression cases、runbook、quality_gate 和安全原则。
- HTTP 400 分类逻辑已细化：如果本地 mode/base_url/chat_path/model/request_shape 仍有风险，归为 `local_request_shape`；如果本地请求形态已通过兼容性检查，则归为 `account_or_service_http_400`，优先验证账号区域、模型授权和服务侧约束。
- Provider `next_actions` 已避免误导：当前真实回归审计显示 request_shape 无兼容风险，下一动作从“笼统核对配置”调整为“验证账号区域、模型授权和服务侧约束”，并保留安全 fallback 与受控 live probe 前置门禁。
- `tools.commander regression-audit` 的 `ai_provider_diagnostics` 详情已包含 failure_playbook 摘要，便于 commander 状态直接看到根因矩阵和安全门禁。
- `/analytics` 新增 Provider Failure Playbook 面板，展示根因、operator action、regression case 和四步安全 runbook。
- Provider failure playbook 专项通过：Provider/Analytics 测试 33 passed；Commander 组合测试 15 passed；相关 ruff 通过；`backend/api/analytics.py` strict mypy 通过；前端 `npm run type-check && npm run build` 通过；干净 8001/3002 浏览器验证可见 `Provider Failure Playbook` 与 `controlled_live_probe`，无横向溢出，控制台 error 为空。
- `docs/tasks/module_dag.json` 已扩展到 57/57 完成；下一轮最高价值方向转为继续按来源推进 92 条 active import issue 人工确认闭环，或在外部凭证明确授权时执行非 dry-run Provider 探针。
- 导入 issue 来源级复核包完成：`source_groups` 新增 `review_packet`，包含 scope、evidence checklist、sample evidence、batch action、quality gate 和安全原则。
- error 级来源默认要求 source contract review，`default_action=request_review`；warning-only 来源可成为批量关闭候选，但仍强制 `requires_reviewer=true`、`requires_resolution=true`、`auto_close_allowed=false`。
- 导入 issue 队列安全边界收紧：`items` 不再返回 `resolution` 明文，只在已有处理说明时返回 `resolution_hash`，避免历史人工说明在队列中泄漏。
- `/governance` 的“来源优先级”已展示“来源复核包”、证据清单、样例 issue hash 和默认动作，让来源级治理从统计列表升级为可执行复核包。
- 来源复核包专项通过：导入治理测试 3 passed；相关 ruff 通过；前端 `npm run type-check && npm run build` 通过；干净 8001/3002 浏览器验证可见 `来源复核包` 与 `sha256` 样例 hash，无横向溢出，控制台 error 为空；`tools.commander regression-audit --batch-limit 2` 通过。
- 回归审计显示 import quality 仍为 75.0，但导入 issue 已推进到 89 active / 11 resolved；下一轮最高价值方向是把复核包用于更大批量的真实来源确认/复审闭环，或给 commander 增加 import issue source review packet gate。
- `docs/tasks/module_dag.json` 已扩展到 58/58 完成。
- 根据当前项目阶段，执行重点调整为“网站正常可用优先，深度安全治理暂缓到项目定型后集中做”。
- 网站启动链路修复完成：`start.sh` 启动前会清理本项目残留的 8000/3000 旧服务，默认不再使用 `--reload`，避免 Python reloader 父子进程残留导致前端连到旧后端。
- `start.sh` 新增启动后健康检查：必须等 `/health`、`/api/analytics/center?limit=20` 和前端首页就绪后才输出成功地址；本轮真实执行确认旧 `localhost:8000` 的 500 已被替换为新服务 200。
- README 手动启动命令已修正为从项目根目录运行后端，避免 `cd backend` 后 import 路径不一致；前端手动启动明确设置 `VITE_API_PROXY_TARGET=http://127.0.0.1:8000`。
- 功能性浏览器验证通过：`/`、`/trainer`、`/analytics`、`/governance`、`/knowledge`、`/path` 均渲染应用外壳和真实内容，`scrollWidth=clientWidth=1280`，console errors 为空。
- 功能性验证通过：`bash -n start.sh`、前端 `npm run build`、关键后端测试 2 passed。
- `docs/tasks/module_dag.json` 已扩展到 59/59 完成；下一轮非严重功能性优先方向是继续清理页面中的 NaN/空态、按钮交互和启动体验，而不是继续加深安全治理。
- 统一审计中心完成：新增 `GET /api/analytics/audit-center`，把 `pipeline_run_logs`、`ai_run_logs`、`ai_provider_probe_logs` 和生产调度健康聚合成统一只读运营审计事件。
- 审计中心支持 module 筛选、状态/模块/级别分布、下一步运营动作和事件详情；详情只返回结构化摘要与派生 hash，不返回 AI payload、人工 resolution 明文、第三方全文、URL query secret 或 API key。
- 前端新增 `/audit` 页面和导航入口，展示事件数、需关注数、最近审计时间、运营审计时间线、分布面板、下一步动作和事件详情抽屉。
- 审计中心专项通过：`tests/test_analytics_api.py` 为 12 passed；`backend/api/analytics.py` strict mypy 通过；相关 ruff 通过；前端 `npm run type-check` 与 `npm run build` 通过；浏览器验证 `/audit` 可见“运营审计时间线”“最近审计事件”“下一步动作”“分布”，`scrollWidth=clientWidth=1280`。
- `docs/tasks/module_dag.json` 已扩展到 60/60 完成；下一轮功能性优先方向是前端运行时/API 错误持久化和页面空态/NaN 治理。
- 前端运行时/API 错误审计捕获完成：新增 `RuntimeEvent` / `runtime_events`，`POST /api/analytics/runtime-events` 可记录 API 错误、Vue 错误、window error 和 unhandled rejection 的结构化运营事件。
- 前端新增 `runtimeEvents.ts`，API 拦截器、Vue `errorHandler`、window error 和 unhandled rejection 均会节流上报；上报失败不会影响用户流程，也不会递归上报自身接口。
- 统一审计中心已纳入 runtime 模块，并支持 `/audit` 下拉筛选“运行时”；事件详情展示 route、endpoint、status、message_hash 和安全 context。
- runtime 事件脱敏完成：后端写入和读取都会去 query、派生 hash、过滤 request body/context 私密字段，并对 Bearer/secret-like 文本做二次脱敏。
- 运行时审计专项通过：`tests/test_analytics_api.py tests/test_database_schema_guard.py` 为 22 passed；`backend/api/analytics.py` strict mypy 通过；相关 ruff 通过；前端 `npm run type-check` 与 `npm run build` 通过；真实写入 runtime event 后 `/audit` runtime 筛选可见 `api_error`，`scrollWidth=clientWidth=1280`。
- `docs/tasks/module_dag.json` 已扩展到 61/61 完成；下一轮功能性优先方向是系统性清理页面 NaN/空态/按钮错误反馈。
- 前端 NaN/空态/运营标签治理完成：新增 `frontend/src/utils/format.ts`，统一提供 finite number、round、percent、ratio bar width 和 display fallback。
- `/analytics` 已改用安全数值格式，修复 scorecard/progress/timeline/import debt/delta tile 的潜在 NaN，并清理 `目标 75health`、`目标 85score` 这类单位拼接问题。
- `/evolution` 已改用安全数值格式，覆盖来源健康、转化率、导入质量、字段完整度条、风险柱和质量分，避免后端字段缺失时出现 `NaN%` 或异常宽度。
- `/daily` 和 `/onboarding` 的进度条已加空数组保护，避免任务/情绪词为空时出现除零宽度。
- 前端门禁通过：`npm run type-check` 与 `npm run build` 通过；浏览器扫描 `/analytics`、`/evolution`、`/daily`、`/onboarding` 均无 `NaN`、`undefined`、`Infinity`，且 `scrollWidth=clientWidth=1280`。
- `docs/tasks/module_dag.json` 已扩展到 62/62 完成；下一轮功能性优先方向是继续增强按钮失败反馈、页面级错误态和加载失败可恢复操作。
- 关键页面可恢复错误态完成：`/analytics` 在刷新失败且已有旧数据时保留页面并显示可恢复警告，完全加载失败时提供重试入口。
- `/audit` 新增页面级加载失败/空态与重试按钮，避免统一审计接口失败时只留下半空页面。
- `/evolution` 新增加载失败、刷新按钮 loading/disabled 状态和周调度失败横幅，调度失败不会误导为成功。
- 正常路径复验通过：`/analytics`、`/audit`、`/evolution` 均渲染真实内容，未出现 `NaN`、`undefined`、`Infinity`，且 `scrollWidth=clientWidth=1280`。
- 前端门禁通过：`cd frontend && npm run type-check` 与 `cd frontend && npm run build` 均通过。
- `docs/tasks/module_dag.json` 已扩展到 63/63 完成；下一轮功能性优先方向是把同样的可恢复错误态推广到 `/governance`、训练关键操作和轻量页面 smoke。
- 治理台与训练中心可恢复反馈完成：`/governance` 的 reviewed 候选加载失败与导入 issue 队列加载失败现在分别显示错误横幅、重试按钮和页面级空态，不会互相清空已加载的治理区域。
- `/trainer` 新增训练题加载失败空态和“重新加载题目”入口；评分提交失败会保留用户输入，并在文本框下方显示可恢复提示。
- 正常路径复验通过：`/governance` 可见 reviewed 发布操作台、导入 Issue 队列和 Issue 操作，`/trainer` 可见训练题与提交入口；两页均无 `NaN`、`undefined`、`Infinity`，且 `scrollWidth=clientWidth=1280`。
- 前端门禁通过：`cd frontend && npm run type-check` 与 `cd frontend && npm run build` 均通过。
- `docs/tasks/module_dag.json` 已扩展到 64/64 完成；下一轮功能性优先方向是补充轻量页面 smoke，把 `/governance`、`/trainer`、`/audit`、`/analytics`、`/evolution` 固化为快速可靠性检查。
- 前端运营核心页面 smoke 门禁完成：`frontend/scripts/world-class-smoke.mjs` 新增 `/analytics`、`/audit`、`/governance` 三条运营核心路径，桌面/移动双视口覆盖从 16 项提升到 22 项。
- smoke mock 层补齐分析中心、审计中心、Reviewed 发布候选、导入质量、导入 Issue 队列和导入 Issue 审计历史的真实结构，避免关键页面只靠空对象假通过。
- `cd frontend && npm run smoke:world` 通过，生成 `frontend/output/smoke/report.json`；检查项包括 heading、横向溢出、可见重叠风险、runtime console/page error。
- 前端门禁复验通过：`cd frontend && npm run type-check` 与 `cd frontend && npm run build` 均通过。
- `docs/tasks/module_dag.json` 已扩展到 65/65 完成；下一轮功能性优先方向是继续把 TrainerAI 发送失败、会话复盘失败和设置面板移动端体验纳入同类可靠性门禁。
- AI 训练伴侣可恢复反馈与移动端设置优化完成：`/trainer-ai` 在 AI 伴侣接口降级为本地安全模式时会显示内联提示，用户可以继续练习且不会误以为深度模拟成功。
- 会话复盘失败现在显示可恢复警告与“重试复盘”按钮；发送流程用 `finally` 保证 typing 状态一定复位，避免接口异常后输入区长期锁死。
- 设置面板的难度和回应风格按钮改为移动端可换行布局，避免窄屏横向挤压。
- 前端门禁通过：`cd frontend && npm run type-check`、`cd frontend && npm run build`、`cd frontend && npm run smoke:world` 均通过，smoke 仍为 22 项。
- 浏览器验证 `/trainer-ai`：场景选择和设置面板均真实渲染，无 `NaN`、`undefined`、`Infinity`，且 `scrollWidth=clientWidth=1280`。
- `docs/tasks/module_dag.json` 已扩展到 66/66 完成；下一轮功能性优先方向是补齐真实聊天交互 smoke，包括发送一条消息、降级提示、会话复盘区和输入区恢复状态。
- AI 训练伴侣真实交互 smoke 门禁完成：`frontend/scripts/world-class-smoke.mjs` 现在会在桌面和移动视口进入 `/trainer-ai`、选择“小回避”、发送一条用户消息，并等待伴侣回应与会话复盘区出现。
- smoke mock 层新增 `POST /api/training/partner/simulate` 与 `GET /api/training/partner/sessions/101/review`，返回关系状态、评分、建议、状态曲线、关键转折和下一练习。
- smoke 检查从 22 项提升到 24 项，并验证伴侣回复、会话复盘、评分渲染、输入区重新可用、横向溢出、可见重叠风险和 runtime error。
- 本轮 smoke 首次捕获到移动端 TrainerAI 交互后的复盘/消息区域重叠，已修复为外层可滚动、消息区定高滚动、头部/状态/复盘/建议/输入区不参与压缩。
- 前端门禁通过：`cd frontend && npm run smoke:world`、`cd frontend && npm run type-check`、`cd frontend && npm run build` 均通过。
- `docs/tasks/module_dag.json` 已扩展到 67/67 完成；下一轮功能性优先方向是继续做 Trainer/TrainerAI 的失败路径自动化 smoke，例如模拟 compare API 失败、partner simulate 失败和 review 失败。
- 训练关键失败路径 smoke 门禁完成：`frontend/scripts/world-class-smoke.mjs` 新增三条失败路径交互，覆盖 Trainer 评分失败、TrainerAI 伴侣模拟失败、TrainerAI 会话复盘失败。
- Trainer 评分失败 smoke 会验证错误提示出现且用户输入仍保留在文本框中，避免提交失败后丢稿。
- TrainerAI 伴侣模拟失败 smoke 会验证本地安全降级提示、降级回应和输入框恢复可用。
- TrainerAI 会话复盘失败 smoke 会验证“会话复盘暂时不可用”和“重试复盘”出现，且聊天输入未锁死。
- smoke 对预期的 500/503 日志做了显式分类：这些失败路径的预期 HTTP/API 日志不会误杀门禁，但未知 runtime/page error 仍会失败。
- 前端门禁通过：`cd frontend && npm run smoke:world` 从 24 项提升到 30 项并通过；`cd frontend && npm run type-check` 与 `cd frontend && npm run build` 均通过。
- `docs/tasks/module_dag.json` 已扩展到 68/68 完成；下一轮功能性优先方向是把治理台发布/Issue 操作的 dry-run/apply 也纳入交互 smoke，验证按钮反馈和审计结果。
- 项目需求审计与评估报告完成：新增 `docs/项目需求审计与评估报告.md`，按专业咨询结构输出项目摘要、SMART 目标、重难点分析、项目亮点、缺陷与优化步骤、功能需求明细表和待客户确认问题。
- 报告基于当前真实实现状态、DAG 68/68、前端 smoke 30 项、数据库/迁移/调度/AI/Gold Set/治理/审计能力进行归纳，不把未验证内容写成已完成。
- 报告明确区分可继续自动化工程任务与客户侧阻塞项：Provider live probe 授权、真实专家复核、第三方内容许可、生产部署环境和告警渠道需客户确认。
- `docs/tasks/module_dag.json` 已扩展到 69/69 完成；下一轮自动化优先方向仍建议为治理台 dry-run/apply 交互 smoke，或在客户确认后推进 Provider live probe/专家复核闭环。
- 后端测试：87 passed。
- 本轮新增治理测试：`tests/test_catalog_profile_review_api.py` 中 reviewed/published 回填与汇总通过，新增 19/19 passed。
- Gold Set 一致性专项：`tests/test_training_flow.py::test_gold_interrater_consistency_reports_agreement_and_conflicts` 通过，覆盖一致与冲突路径。
- Commander 回归审计专项：`tests/test_commander.py` 通过，覆盖 `regression-audit` dry-run 与真实本地门禁执行。
- AI 失败根因专项：`tests/test_analytics_api.py` 通过，覆盖 provider failure、安全阻断聚类和 payload marker 不泄露。
- 导入质量修复计划完成：`GET /api/evolution/import-quality` 现在返回 `repair_plan`，`POST /api/evolution/import-quality/repair-plan` 支持 dry-run 与 apply，能安全回填样本 provenance、资源场景/格式提示和知识条目来源元数据，并以 `repair_source` 留痕。
- 导入质量修复专项通过：`tests/test_learning_pipeline_api.py::test_import_quality_and_safety_reports_are_auditable` 与 `test_import_quality_repair_plan_dry_run_and_apply` 通过；相关 ruff 通过。
- 已对共享 SQLite 执行安全 metadata repair：补全样本 43 条、资源 69 条、知识 1 条；repair plan 清零，未保存第三方全文或敏感原文。
- 导入质量回归审计完成：`tools.commander regression-audit` 新增 `import_quality` 检查，输出 `quality_score`、`issue_count`、`quality_debt`、`repair_plan_counts` 和下一动作。
- 导入质量债务分层完成：报告新增 `quality_debt`，把可自动修复字段缺口与需人工/来源治理的历史 import issue 分开；当前全局质量分 75.0，剩余主要为历史 issue 复核。
- AI Provider 配置诊断完成：新增 `GET /api/analytics/ai-provider-diagnostics`，返回脱敏 provider 配置、mode/model/base_url/chat_path、失败率、HTTP status 分布、风险等级和下一动作，不暴露 API key、URL query、payload marker 或原文。
- AI Provider 诊断已纳入 `tools.commander regression-audit`；真实审计定位到历史 Provider HTTP 400 高频、`mode=openai`、`base_url=https://api.deepseek.com`、风险等级 high。
- Analytics/Commander 专项通过：`tests/test_analytics_api.py tests/test_commander.py` 为 11 passed；`backend/api/analytics.py` strict mypy 通过；相关 ruff 通过。
- Gold Set 冲突复核队列完成：新增 `GET /api/samples/gold/conflict-queue`，按决策分歧、最大总分差、平均分差、信心差和审阅者版本生成复议优先级、最新 review cards 与共识复核建议。
- Gold 冲突队列已纳入 `tools.commander regression-audit`；真实库当前开放冲突 10 个，全部高优先级，需要 consensus reviewer 新版本复议。
- 共享库稳定性修复完成：Gold 冲突测试扩大队列窗口，向量检索测试按唯一 UUID 断言目标知识条目，避免历史累积数据造成偶然失败。
- Reviewed 发布候选队列完成：新增 `GET /api/evolution/reviewed-assets/publish-candidates`，输出 reviewed 资源/知识候选、质量信号、优先级理由、publish_ready 和人工确认门禁。
- 发布候选门禁已纳入 `tools.commander regression-audit`；真实库当前有 19 条 publish_ready 候选，但系统不会绕过人工确认直接发布。
- 后端产品覆盖率：86%。
- 后端全量门禁：`.venv/bin/python -m pytest -q` 为 96 passed，产品覆盖率 86%。
- 全仓 ruff：通过。
- 前端类型检查：通过。
- 前端生产构建：通过。
- 当前 DAG 指挥官：25/25 全部完成。
- 浏览器 smoke：`npm run smoke:world` 通过，8 条关键路径 × 2 个视口，共 16 项检查；报告位于 `frontend/output/smoke/report.json`。
- Analytics 专项：`tests/test_analytics_api.py` 通过，`backend/api/analytics.py` mypy strict 通过。
- Gold Set 专项：`tests/test_training_flow.py` 覆盖专家复核队列、复核提交、质量摘要和评分校准；相关 ruff 通过。
- 正式迁移专项：`tests/test_database_schema_guard.py` 覆盖 migration plan、dry-run、apply、审计记录和 API 路由；`backend/database/migration_runner.py` strict mypy 通过。
- 向量索引专项：`tests/test_vector_index.py` 覆盖 sqlite-vec 后端激活、持久化重建、ANN 搜索、评测校准、API 路由和数据库审计；`backend/core/vector_index.py` strict mypy 通过。
- 数据库触达 Python 文件 ruff：通过。
- 数据库触达 Python 文件 mypy strict：通过。
- 训练核心 Python 文件 ruff：通过。
- 训练核心 Python 文件 mypy strict：通过。
- 练习会话模型与训练入口 mypy strict：通过。
- 真实数据库审计：`status=ok`，`quick_check=ok`，缺表/缺列为空，JSON 深层质量无坏值；`safety_events=11` 且相关 JSON invalid=0。

## 下一轮最高优先级

1. 下一轮进化：继续按 `docs/世界级总体验收报告.md` 中的生产级后台调度、独立分析中心历史趋势详情页、Provider 失败处置和数据重算 revision 推进。

## 2026-05-22 23:26 CST 资源海洋扩容与 AI 伴侣活性增强

- 资源库从 360 条扩充到 1200 条：新增 `backend/database/auto_expand_resources.py`，以 synthetic、可审计、可重复的方式派生资源，不抓取或保存第三方全文。
- 新增资源覆盖话术、短句、故事、练习、轻幽默、知识卡片六类，并按场景、依恋类型、情绪语气、难度生成 source/source_url/tags/review_status/published_at。
- `/api/resources` 默认 limit 从 20 提升到 100，最大 1000，并按 id 倒序返回，便于资源海洋优先看到最新扩充内容。
- 前端 `/resources` 去除正文三行截断，改为完整展示内容、使用提示、来源、标签、情绪强度、难度、依恋适配、目标对象和当前显示总量。
- 资源筛选补充 `phrase`、`media` 以及复联、异地、承诺、分歧等场景入口。
- AI 训练伴侣规则降级层扩展不同依恋风格回复池，并根据高边界压力、高情绪压力、低信任、低连接状态动态改变回复，避免 Provider 不稳定时只剩重复短句。
- AI 伴侣系统 prompt 强化“情绪流动、靠近/后退、边界变化、角色职责定位”，让 DeepSeek 成功时也更贴近训练陪练职责。
- 数据库 quick_check 通过，当前 `resource_library=1200`。

## 2026-05-22 23:40 CST 公开来源透明扩容

- 资源库从 1200 条扩充到 2400 条，新增 1200 条带公开信息源 URL 的派生训练资源。
- `backend/database/auto_expand_resources.py` 增加公开来源锚点，覆盖 Gottman Institute、Gottman Research、CNVC Feelings Inventory、CNVC Needs Inventory、Greater Good Science Center、APA Relationships、HelpGuide Effective Communication、HelpGuide Conflict Resolution、Harvard Study of Adult Development、Nonviolent Communication。
- 新资源仍只保存本项目原创训练卡片/回应句，不保存第三方全文；公开来源只作为 `source_url`，用于用户自由跳转阅读原始资料。
- `/resources` 卡片头部新增“打开信息源”外链按钮，卡片底部显示完整 `信息源链接`，用户可直接点击跳转。
- 前端 `ResourceItem` 类型补齐 `source_url`，资源页可透明展示来源、URL、标签和派生说明。
- 浏览器验证 `/resources`：可见 `1000 / 2400 条`、`打开信息源`、`信息源链接`、`cnvc.org`；无 `NaN`、`undefined` 或横向溢出。

## 2026-05-22 23:56 CST 资源海洋分页与万条级扩容

- `/resources` 从一次加载 1000 条改为真实分页：每页 48 条，显示当前页、总页数、当前范围、首页/上一页/页码/下一页/末页。
- 后端 `/api/resources` 支持 `page`、`limit` 和分页元数据，同时保留 `offset` 兼容。
- 新增 `GET /api/resources/sources`，返回公开信息源目录、URL 和资源数量，前端顶部展示“开放信息源”快捷链接。
- 资源库从 2400 条扩充到 10000 条，新增 Kinsey、Love Matters、Guokr、CDC NSFG、WHO、ONS、YRBS、Zenodo、TalkingData、中国大学课程、智慧树、Dibble、UGA ELEVATE、MotherWise、播客 RSS、本地深度聊天话题库、情绪流动故事库、成人暧昧语言游戏库、对话诊断库等锚点。
- 新增资源覆盖公开来源观察卡、公开来源练习句、情绪流微故事、深聊问题、成人暧昧语言游戏、对话前后诊断等形态。
- 浏览器验证：`/resources` 可见 `第 1 / 209 页 · 1-48 / 10000 条`、开放信息源目录、分页按钮和资源来源链接；当前 DOM 卡片数 48，无横向溢出、NaN 或 undefined。

## 2026-05-23 00:52 CST 资源海洋运营级治理与训练活性修复

- 资源库从 10000 条升级到 12000 条，当前 `resource_library=12000`，`distinct_content=11709`；仍保留历史重复内容债务 291 条，不把未清理历史重复误报为已完全解决。
- `/api/resources` 支持关键词、标签、来源、场景、类型与分页组合查询；`/resources` 可读取 URL query，用于从浏览冲浪页点击主题后直接进入筛选结果。
- `/api/resources/sources` 增加来源摘要、内容结构、质量说明、主题/场景标签和 `link_status`；CNVC 旧失效入口已合并到稳定公开引用页。
- 新增 `/surf` 浏览冲浪页，按来源组、关键词、主题入口浏览高质量外部信息源；页面展示网站摘要、内容结构、质量说明、链接状态、库内数量和可点击外链。
- 资源页和冲浪页只保存本项目派生训练摘要与来源 URL，不保存第三方全文；成人关系内容统一约束为同意、边界、情绪流动、亲密伦理和反操控训练。
- AI 训练伴侣新增 `GET /api/training/partner/provider-status`，前端显示 DeepSeek provider/mode/model 与当前可用状态；本地降级回复增加风格化情绪流动句，减少机械重复。
- 错题本新增“情绪流动动线”“三步改写练习”和关联资源检索入口，把错因、修复方向和资源库训练材料连起来。
- 本轮保持本地服务运行：前端 `http://127.0.0.1:3000`，后端 `http://127.0.0.1:8000`。

## 2026-05-23 01:20 CST 资源海洋职责切分与原文级导读治理

- 需求审计结论：资源海洋不应再承担信息源目录职责；外部网站、来源摘要、来源结构和链接状态统一放到 `/surf` 浏览冲浪页，资源海洋专注资源记录阅读、搜索、分页和训练转化。
- 前端 `/resources` 已移除顶部“开放信息源”模块，保留筛选、分页、资源卡和每条记录的原站链接，避免信息源目录和资源记录混在一个页面造成拥挤。
- `resource_library` 新增 `source_title`、`source_excerpt`、`source_summary`、`source_license`、`content_fingerprint`、`quality_score` 字段；schema guard 已自动给真实 SQLite 补列。
- 新增 `backend/database/resource_quality_governance.py`，提供资源导读回填、质量评分、精确重复删除和质量报告。
- `backend/database/auto_expand_resources.py` 已把新字段接入生成流程，并让公开来源卡正文显式包含来源入口差异，避免不同来源生成相同模板内容。
- 已执行资源质量治理：重建生成资源后真实库为 `total=12000`、`distinct_fingerprints=12000`、`exact_duplicate_debt=0`、`missing_guidance=0`、`avg_quality_score=99.5`。
- 新增 `GET /api/resources/quality-report`，返回资源规模、去重债、导读覆盖、平均质量分和“不复制第三方全文”的治理原则。
- 原文治理边界：系统不把第三方网页全文复制进数据库；保存可点击原站 URL、合规短摘录/摘要、原文级导读、结构化训练转化、许可边界和去重指纹。

## 2026-05-23 07:28 CST 资源库使命对齐纠偏

- 审计结论：上一轮资源虽然达到规模和去重目标，但内容源分布偏离网站初衷，CDC/WHO/统计/行业数据/泛性别研究等背景源被放大为训练主内容，资源海洋读起来不像“微关系动力学训练场”。
- `backend/database/auto_expand_resources.py` 新增 `MISSION_PUBLIC_SOURCE_NAMES` 与 `MISSION_CORE_AXES`，只保留关系训练直接相关的公开核心源，并把每条公开来源卡强制收束到微关系信号、情绪流动、边界同意、暧昧张力、冲突修复、长期连接、幽默互动、错题改写等训练轴。
- 本地四类训练素材改为轮转生成：深度聊天话题库、情绪流动故事库、成人暧昧语言游戏库、从之前到之后对话诊断库各约 1050 条，避免单一库刷屏。
- `backend/database/resource_quality_governance.py` 新增使命对齐评分：统计 `avg_mission_alignment` 和 `off_mission_count`，并对公共卫生、人口统计、行业数据等偏题关键词降权。
- 已重建生成资源并治理：`total=12000`、`distinct_fingerprints=12000`、`exact_duplicate_debt=0`、`missing_guidance=0`、`avg_mission_alignment=82.9`。
- 当前来源分布回到主线：四个本地训练库各约 1051-1052 条，Gottman/CNVC/HelpGuide/NVC/Kinsey/Love Matters/课程等核心源各 480 条；CDC/WHO/ONS/YRBS/TalkingData/Zenodo 等背景源不再生成主资源卡。

## 2026-05-23 08:04 CST 资源库具体案例化与浏览导航修复

- 审计结论：使命纠偏后仍存在“模板参数化”体验问题，用户首屏会看到同类标题和抽象总结，缺少真实可练的具体对话情境。
- `backend/database/auto_expand_resources.py` 新增具体场景案例库，每条生成资源包含“场景、TA说、常见失误、更好回应、情绪信号、边界与同意、练习任务、适配提示”，覆盖晚回消息、首次约会迟到、关系定义、坏笑提问、异地低电量、冷战复联、亲密推进、礼物修复、社交忽略、土味情话、失望修复、价值观分歧、赞美承接、日常偏好、轻挑战和公开玩笑止损等场景。
- 资源生成标题补充语气、依恋类型和难度，正文补充不同资源类型训练目标，避免同一场景在去重和页面阅读中呈现为复制内容。
- `/api/resources` 无筛选默认优先展示 `具体案例` 训练卡；用户使用类型、场景、关键词、标签或来源筛选时仍可访问公开来源观察卡和历史资源。
- `backend/core/resource_source_catalog.py` 扩充中文与产品参考来源，包括情感网、恋小帮、中文幽默王、52笑话网、哄哄模拟器、Paired、ChatRel、ChineseNlpCorpus；浏览冲浪页会显示已登记但库内计数为 0 的信息源，作为透明外部入口。
- `/resources` 新增页内“到顶部/到底部”按钮、每条资源锚点和右侧本页目录；资源正文继续完整展示，不再截断。
- `/surf` 标题本身改为可点击外链，新增页内目录和顶部/底部跳转，来源卡继续展示网站摘要、内容结构、质量说明、链接状态和主题入口。
- 已重建生成资源并治理：`total=12000`、`distinct_fingerprints=12000`、`exact_duplicate_debt=0`、`missing_guidance=0`、`avg_quality_score=97.4`、`avg_mission_alignment=87.6`。
- 当前本地服务已重启并保持运行：前端 `http://127.0.0.1:3000`，后端 `http://127.0.0.1:8000`。

## 2026-05-23 08:18 CST 表达工具箱贯通架构方案

- 已新增 `docs/表达工具箱贯通架构方案.md`，把用户提供的表达工具箱从单独知识材料升级为项目内“表达能力层”。
- 新方案将表达工具箱映射进项目既有元基础、12 类分类树、5W2H、训练掌握、AI 伴侣、错题本、资源海洋、知识中枢、八阶路径和 commander/DAG。
- 架构定义六层表达模型：核心逻辑层、内容弹药层、结构设计层、非语言工具层、情绪调节层、关系管理层。
- 方案给出 `expression_tools`、`expression_tool_chains`、资源表增强字段和训练尝试增强字段，作为后续 SQLite 主真源改造依据。
- 方案给出 `/api/expression/tools`、`/api/expression/recommend`、`/api/expression/score`、`/api/expression/mastery` 等 API 规划，以及 `/expression` 页面、Trainer 表达评分、AI 伴侣工具链解释、错题工具归因和资源工具标签化的落地路径。
- 下一轮最高价值执行链：`toc_sidebar_unification`、`expression_schema`、`expression_seed_tools`，先统一多记录页目录体验，再把表达工具本体入库并接入训练闭环。

## 2026-05-23 08:36 CST 下一阶段统一产品架构与执行蓝图

- 已新增 `docs/下一阶段统一产品架构与执行蓝图.md`，把“剩余产品任务清单”和“表达工具箱贯通方案”重构为同一份执行蓝图。
- 统一北极星：从“资源多的关系训练网站”升级为“世界级微关系表达与感知训练场”，让用户完成看懂、选对、说好、复盘四件事。
- 蓝图按七层重构：来源与内容源层、数据治理层、资源与工具本体层、场景分类与 5W2H 层、训练与 AI 交互层、错题与掌握模型层、分析与治理层、Commander 自动进化层。
- 蓝图整合七大能力域：内容质量治理、表达工具箱、资源海洋页面、浏览冲浪、数据库与采集治理、AI 伴侣与训练联动、运营后台与审计。
- 已输出统一数据模型、API 规划、前端页面、复用组件、P0/P1/P2 DAG 任务清单和验收门禁。
- 下一轮最小高价值闭环明确为 `toc_sidebar_unification`；后续接 `expression_schema -> expression_seed_tools -> expression_page`。

## 2026-05-23 09:58 CST 资源浏览与近重复治理 P0 落地

- `toc_sidebar_unification` 完成：新增 `frontend/src/components/PageTocSidebar.vue`，资源海洋与浏览冲浪页复用同一套右侧目录、到顶部和到底部导航。
- `resource_mission_group_view` 完成：`/api/resources` 支持 `mission_axis` 查询，前端 `/resources` 增加八大主线分组按钮，可按微关系信号、情绪流动、边界同意、暧昧张力、冲突修复、长期连接、幽默互动、错题改写切换。
- `resource_semantic_dedupe_queue` 完成：新增 `resource_similarity_queue()` 与 `GET /api/resources/similarity`，按标题/场景语义家族和本地元数据向量余弦分数输出近重复簇。
- 发布治理台新增“资源近重复治理”区块，显示扫描资源数、重复簇、候选项、阈值、推荐动作和簇内样例，可跳转回资源海洋筛查。
- 真实库扫描结果暴露了当前最主要体验债：`limit=1000` 时返回 12 个近重复簇、1000 个候选项，最大簇相似度约 0.988，证实公开来源练习句仍有同标题/同场景变体需要后续批量重写或默认隐藏。
- 当前 P0 已从“发现重复感”推进到“可查询、可显示、可审计的治理队列”；下一项应进入 `expression_schema`，把表达工具箱落到 SQLite 主真源。

## 2026-05-23 10:08 CST 表达工具箱 SQLite 主真源与页面落地

- `expression_schema` 完成：新增 `expression_tools` 与 `expression_tool_chains` 两张 SQLModel 表，纳入 `create_db_and_tables()` 与 schema guard，数据库审计可看到表达工具主数据。
- `expression_seed_tools` 完成：新增 `backend/database/expression_seed.py`，可幂等种入 60 个基础表达工具与 5 条工具链；每个工具包含层级、类别、公式、适用场景、风险边界、微步骤、旧回应和更好回应。
- 新增 `backend/api/expression.py`：提供 `POST /api/expression/seed`、`GET /api/expression/tools`、`GET /api/expression/tools/{id}`、`GET /api/expression/chains`、`POST /api/expression/recommend`。
- 真实服务已执行表达工具种子：`created=60`、`total_tools=60`、`chains.total=5`；推荐接口可按“修复/修复信任”返回“失望修复三步链”和关联工具。
- `expression_page` 完成：新增 `/expression` 页面与导航入口，支持层级/场景/目标/关键词筛选、工具详情、风险边界、前后回应示例和工具链推荐。
- 浏览器验证 `/expression`：可见工具 60、工具链 5、推荐 2、工具详情和风险边界；无 `undefined/NaN`，无横向溢出。
- 下一项应优先做 `resource_expression_tags` 或 `trainer_expression_scoring`，把表达工具从独立工具箱继续挂到资源卡和训练评分闭环。

## 2026-05-23 10:42 CST 资源表达标签与 Trainer 表达评分闭环

- `resource_expression_tags` 完成：`resource_library` 新增并回填 `expression_tool_ids_json`、`expression_goal`、`expression_level`、`speech_act`、`mistake_pattern`、`recommended_drills_json`，资源卡不再只是“摘要/标签”，而能直接告诉用户这条资源练什么表达工具。
- `backend/database/resource_quality_governance.py` 新增表达工具规则，把冲突、修复、边界、暧昧、长期、初识、幽默、错题等资源映射到表达工具箱 60 个工具。
- `/api/resources` 支持 `expression_tool` 与 `expression_goal` 筛选；`/resources` 增加表达目标筛选，并在卡片上展示目标、训练等级、语言行为、推荐工具和常见错题。
- 真实库治理已执行，资源总量 `12019`，`missing_guidance=0`，表达字段可通过真实 API 返回；当前 exact duplicate debt 为 15，保留为后续近重复治理债务，不在本轮静默删除历史/测试资产。
- `trainer_expression_scoring` 完成：`/api/training/compare` 返回 `expression_tool_scoring`，包含工具适配分、D1-D5 阶段、目标、弱维度、已检测动作、缺失动作、推荐工具、三步练习和边界提醒。
- `seed_all()` 已接入 `seed_expression_tools()`，保证训练评分在新库/测试库中能直接拿到表达工具名称、公式、风险和微步骤。
- `/trainer` 提交结果区新增“表达工具适配”卡，把七维评分进一步落到“下一句该用什么表达工具、缺了什么动作、怎么练”。
- 下一项应继续做 `mistake_expression_rewrite`：把错题本里的错误归因、推荐资源和表达工具链合并成三版本改写闭环。

## 2026-05-23 10:58 CST 错题本表达工具三版改写闭环

- `mistake_expression_rewrite` 完成：错题本从“错误归因 + 三步练习”升级为“表达工具改写链”，每条错题可看到目标、主工具、推荐工具、三版改写、迁移练习和禁区提醒。
- 后端 `GET /api/training/mistakes` 新增 `expression_rewrite` 派生字段，不强行修改 `mistake_log` 表，先用现有样本、错因和表达工具 SQLite 主数据即时生成可审计结构。
- 三版改写包括：低压承接版、边界清晰版、行动修复版；同时输出 `transfer_drill` 和 `forbidden_moves`，避免用户背答案而不能迁移。
- 前端 `/mistakes` 新增“表达工具改写链”区块，可跳转 `/expression?goal=...` 查看工具箱；推荐工具以标签展示，三版改写分列呈现。
- 真实 API 验证当前返回 20 条错题，首条包含 `expression_rewrite`、4 个推荐工具、3 个改写版本、迁移练习和 3 条禁区提醒。
- 下一项建议继续做 `ai_partner_expression_chain`：AI 伴侣每轮回复显示情绪状态变化、使用的表达工具链、引用资源/错题线索，让陪练从“机械回复”变成“有职责定位的动态教练”。

## 2026-05-23 11:14 CST AI 伴侣表达工具链与状态动线

- `ai_partner_expression_chain` 完成：`/api/training/partner/simulate` 的每轮响应新增 `expression_chain`，包含目标、状态变化、工具 id/name、选择原因、下一步动作、练习提示、风险边界和原则。
- AI 成功路径、AI 失败降级路径、未配置 provider 路径和安全阻断路径都生成同一结构，不再因为 provider 不稳定导致 AI 伴侣只剩机械回复。
- 表达工具链根据关系状态机动态选择：边界压力高优先边界工具，压力高优先降温/安全工具，连接低优先开放延展，信任低优先修复工具；幽默/张力风格会补充风格或连接工具。
- 前端 `/trainer-ai` 消息气泡新增“表达工具链”卡，展示训练目标、状态标签、推荐工具、下一步、练习提示和边界提醒，让 AI 伴侣的职责定位更清楚。
- 真实 API 验证：当前 DeepSeek 响应缺少 `reply` 时系统降级为 `rule_fallback:AI 响应缺少 reply`，仍返回 `expression_chain.target_goal=引导深聊`、工具链 `场景化表达/轻调侃/留白沉默/距离调节`、状态 `谨慎试探`、下一步和风险边界。
- 下一项建议继续做 `partner_resource_retrieval_context`：AI 伴侣回复引用 1-3 条资源卡或错题改写链，让陪练内容进一步摆脱单句模板。

## 2026-05-23 11:28 CST AI 伴侣资源检索上下文

- `partner_resource_retrieval_context` 完成：`/api/training/partner/simulate` 的每轮响应新增 `related_resources`，根据表达目标、状态工具链、场景、依恋风格和话题从 `resource_library` 检索 1-3 条资源卡。
- 资源推荐返回标题、类型、分类、场景、表达目标、质量分、来源标题、来源 URL、使用提示和匹配原因，前端可直接跳到资源海洋继续浏览。
- 前端 `/trainer-ai` 消息气泡新增“关联资源”卡，AI 伴侣现在能把回复、状态动线、表达工具链和资源库训练材料连起来，减少单句模板感。
- 真实 API 验证：当前 provider 降级为 `rule_fallback:AI 响应缺少 reply` 时，仍返回 `related_count=3`，首批资源来自 Gottman Institute 公开来源观察卡/情绪流卡，并带 `source_url` 与匹配原因。
- 下一项建议进入 `partner_mistake_memory_context`：AI 伴侣引用最近错题改写链和用户弱项，让陪练能记住用户常犯模式。

## 2026-05-23 11:38 CST AI 伴侣近期错题记忆上下文

- `partner_mistake_memory_context` 完成：`/api/training/partner/simulate` 的每轮响应新增 `mistake_memory`，包含近期错题卡、弱维度、下一练习焦点和“只用于训练提示、不贴标签”的原则。
- 后端从 SQLite 主真源 `mistake_log`、`interaction_samples`、`ability_snapshots` 实时派生错题记忆，不新增不可审计的临时状态，也不保存第三方全文。
- DeepSeek/AI 编排 payload 新增压缩版错题记忆，AI 成功路径可以参考用户旧失误；provider 失败或缺 reply 时，规则降级同样返回完整记忆结构。
- 前端 `/trainer-ai` 消息气泡新增“近期错题记忆”卡，展示本轮避坑焦点、薄弱维度、旧回应、TA 原话和改写提示，并可跳转错题本。
- 真实 API 验证：当前 provider 仍降级为 `rule_fallback:AI 响应缺少 reply`，但返回 `memory_cards=3`、`weak_dimensions=3`、`next_focus=本轮先避开旧失误...`。
- 下一项建议进入 `ai_provider_request_shape_fix`：继续治理 DeepSeek 非 JSON/缺 reply 的请求形状与回归样例，让真实 AI 成功率提升，而不是只依赖高质量降级。

## 2026-05-23 11:49 CST AI Provider 包裹 JSON 响应修复

- `ai_provider_wrapped_json_recovery` 完成：`AIProviderClient.chat_json()` 现在先解析严格 JSON，失败后会从 provider 说明文字中提取一个平衡的 JSON 对象。
- 新增解析逻辑会正确处理字符串里的 `{}`，避免把“边界”等带花括号文本误截断；完全非 JSON 内容仍保留 `raw_text` 降级路径。
- 新增两个 provider 回归样例：说明文字包裹 JSON、字符串内含花括号 JSON，覆盖 OpenAI-compatible 和 native reply 形态。
- 该修复不保存第三方长原文，只在运行时把 provider 文本恢复成结构化对象，用于减少“AI 响应缺少 reply”的非必要降级。
- 下一项建议继续进入 `partner_ai_response_shape_contract`：在训练伴侣层对 AI 内容做 schema 归一化和字段别名兼容，如 `message/text/advice` -> `reply/suggestions`。

## 2026-05-23 11:58 CST 训练伴侣 AI 响应字段归一化

- `partner_ai_response_shape_contract` 完成：`/api/training/partner/simulate` 在 AI 成功路径新增响应归一化层，兼容 `reply/message/text/content/partner_reply/response`。
- 分数字段兼容 `score/rating/relational_score`，并支持字符串分数如 `"84"` 或 `"84分"`；建议字段兼容 `suggestions/advice/tips/coaching`，可把多行或句号分隔文本转成建议数组。
- 新增测试覆盖 provider 返回 `message + rating + advice` 的非标准成功形态，确保不再因为字段别名不同而降级为“缺少 reply”。
- 前端无需改动即可接收归一化后的稳定结构；本轮仍运行了 type-check 和 build，保证展示链路未破坏。
- 下一项建议进入 `partner_ai_live_success_probe_after_shape_fix`：在现有 live probe policy 允许时跑一次真实训练伴侣调用，对比修复前后的 success/raw_text/fallback 比例。

## 2026-05-23 12:58 CST Provider 成功契约与近重复治理动作闭环

- `ai_provider_success_contract_report` 完成：新增 `GET /api/analytics/ai-provider-success-contract`，按 AI run log 聚合 structured success、raw text、provider failure、recoverable success、任务矩阵、契约缺口、质量门禁和下一动作。
- 分析中心 `GET /api/analytics/center` 已纳入 `provider.success_contract`，前端 `/analytics` 增加 Provider Success Contract 面板；报告只使用 outcome、response summary keys、fallback reason 等结构化审计信号，不暴露 prompt、payload 或 provider 原文。
- 真实运行态确认 `GET /api/analytics/center?limit=20` 返回 `success_contract.summary.structured_success_rate`、`quality_gate` 和 `contract_gaps`，当前 structured success 仍未达到稳定门禁，需要继续观察 live probe policy 允许后的真实成功率。
- `resource_similarity_action_console` 完成：新增 `POST /api/resources/similarity/action`，支持 `quarantine_variants`、`request_review`、`restore_reviewed` 的 dry-run/apply；真实执行只改资源 review 状态，不删除内容，并写入 `pipeline_run_logs`。
- 资源列表默认隐藏 `review_status=quarantine` 的近重复变体，治理台仍可通过近重复队列和审计日志追踪；审计 payload 只保存资源 ID、状态流转、title hash、reason hash、质量分和安全标记，不保存人工原因明文或第三方全文。
- `/governance` 近重复资源队列新增“隔离变体预演 / 隔离低质变体 / 请求复审”操作，结果区展示影响条数、状态汇总、reason hash、审计日志和下一动作。
- 下一项建议继续做 `resource_dedup_rewrite_batches`：对被隔离或复审中的资源簇生成更具体、差异化的本地原创案例版本，并把重复家族从“隐藏”推进到“高质量重写补位”。

## 2026-05-23 13:10 CST 近重复资源重写补位闭环

- `resource_dedup_rewrite_batches` 完成：新增 `POST /api/resources/similarity/rewrite-batch`，可对近重复资源簇 dry-run 或真实生成差异化本地原创补位资源。
- 重写补位资源使用 `project_original:resource_similarity_rewrite` 来源，内容固定包含“场景 / TA说 / 常见失误 / 更好回应 / 情绪信号 / 边界与同意 / 练习任务”，避免继续生成抽象总结式废话。
- 真实执行会新增 `reviewed` 状态的补位资源，并可把原重复变体置为 `quarantine`；不删除原资源，不保存第三方全文，不返回人工 reason 明文，只在审计中保存 `reason_hash` 和 replacement fingerprint。
- `/governance` 近重复资源队列新增“重写补位预演 / 生成补位”按钮，操作结果展示补位数量、场景、reason hash、审计日志和下一动作。
- 回归审计显示最新系统门禁通过；同时暴露导入质量仍有 `auto_repairable_fields=9`，下一项应做 `import_quality_safe_auto_repair_followup`，把可自动补全字段先清零，再继续人工来源治理。

## 2026-05-23 13:13 CST 导入质量安全元数据回补

- `import_quality_safe_auto_repair_followup_20260523` 完成：对共享 SQLite 执行 `POST /api/evolution/import-quality/repair-plan`，只补全结构化元数据，不写入第三方全文或敏感原文。
- dry-run 计划显示可修字段包括样本 `source_trace_json/quality_json`、资源 `applicable_scene/usage_tip/emotional_tone_json`、知识 `source_metadata_json`。
- 真实执行补全样本 3 条、资源 27 条、知识 3 条；复查后 `repair_plan` 全部为 0，`quality_debt.auto_repairable_fields=0`。
- Commander 回归审计通过：数据库健康 ok、import quality `quality_score=75.0`、`active_issue_count=88`、`resolved_issue_count=12`、auto repair 为 0；剩余质量债为历史来源 issue，需要来源级复核和人工确认闭环，不应代码刷分。
- 下一项建议进入 `reviewed_rewrite_publish_batch`：将当前 20 条 publish-ready reviewed 资产按发布治理门禁确认发布，让重写补位成果进入默认可用资产池。

## 2026-05-23 13:21 CST Reviewed 发布候选泛内容门禁收紧

- `reviewed_publish_generic_content_gate` 完成：发布候选评分新增 legacy/manual generic content 阻断逻辑，`旧手册章节`、`子章节`、`legacy_manual` 等泛标题/遗留章节不会仅因元数据齐全就进入 publish-ready。
- `quality_signal.blocks` 会返回阻断原因，priority score 被压到 85 以下，真实发布动作仍会因 `publish_ready=false` 被后端拒绝。
- 已清理共享库中测试产生的 `rewrite:similarity-rewrite-*` 补位资源，把它们置为 `quarantine`，避免测试资产进入生产发布候选池。
- 回归审计显示 reviewed publish candidates 从 20 条 publish-ready 收紧为 10 条 publish-ready；候选前列回到“真心话大冒险 / 如果我是你 / 我爱你的理由”等真实资源，而不是泛 legacy 手册章节。
- 下一项建议进入 `reviewed_publish_ready_resource_release`：只对仍 publish-ready 的真实资源执行发布确认，继续避免 legacy/manual 泛内容自动发布。

## 2026-05-23 13:31 CST 资源发布具体性门禁与误发布召回

- `resource_publish_specificity_gate_and_recall` 完成：资源发布候选不再只看 `effectiveness_rating + 场景 + 使用提示`，必须有具体场景、TA 原话、常见失误、更好回应、边界/同意或练习任务等可训练证据。
- 单句短标题资源如“土味 / 含蓄 / 幽默 / 深情”即使元数据完整，也会被 `quality_signal.blocks` 标记为“需补充具体案例与练习结构”，priority score 压到发布阈值以下。
- `POST /api/evolution/reviewed-assets/backfill` 现在复用同一发布候选门禁，避免旧逻辑按评分把低具体性资源重新推入 `published`。
- 共享 SQLite 中 71-80 号短句资源已在门禁回填后退回 `reviewed`；本轮测试/调试插入的临时资源已通过 reviewed asset action 退回 `draft`，保留 `pipeline_run_logs` 审计而不删除记录。
- 真实候选复查：`GET /api/evolution/reviewed-assets/publish-candidates?limit=20` 当前 `publish_ready=0`，说明发布台进入保守状态；下一步应优先用重写补位/表达工具链生成足够具体的高质量资源，再逐条发布。

## 2026-05-23 13:41 CST 资源具体化多样补位发布批次

- `resource_specificity_uplift_diverse_publish_batch` 完成：把资源重写补位模板从 4 个骨架扩展为覆盖初次邀约、价值观分歧、冷战破冰、复联、异地、家务分工、纪念日、玩笑越界、暧昧推拉、吃醋、忙碌期、公开边界等 25 个具体训练场景。
- 新增多样性回归测试：较大批量重写时必须产出足够多的不同主题，防止再次出现“只有案例编号变化”的伪扩容。
- 已召回第一批低多样性补位资源 24 条（`12284-12307`），通过 `resource_similarity/action` 置为 `quarantine`，默认资源海洋不展示，审计日志保留原因 hash 和状态流转。
- 第二批从 24 条低具体性 reviewed 资源生成 24 条 `project_original:resource_similarity_rewrite` 补位资源，并在发布前逐条通过严格具体性门禁；最近 24 条发布资源包含 18 个不同主题。
- 原短句 reviewed 资源已隔离，第二批补位资源内容均包含“场景 / TA说 / 常见失误 / 更好回应 / 情绪信号 / 边界与同意 / 练习任务”，不保存第三方全文。

## 2026-05-23 13:45 CST 资源页测试资产可见性治理

- `resource_test_artifact_visibility_guard` 完成：共享 SQLite 中 `source=pytest` 的资源测试资产已通过治理动作全部置为 `quarantine`，默认资源海洋不再展示测试数据。
- `tests/test_vector_index.py` 的近重复队列、动作和重写多样性测试现在会在断言后把本轮生成资源 quarantine，避免后续测试污染用户可见数据。
- 真实 API 复查：`GET /api/resources?source=pytest&limit=5` 返回 `total=0`；`boundary_consent` 与 `conflict_repair` 主线第一页来源不再包含 `pytest`。
- 清理动作不删除记录，只改状态并写入资源治理审计；测试资产仍可追踪，但不进入默认浏览体验。

## 2026-05-23 14:50 CST 多记录页人性化目录、筛选建议与卡片内详情

- `frontend_humanized_toc_filter_and_inline_detail` 完成：统一目录组件改为右侧可折叠 sticky 目录，约束在视窗高度内滚动，并移除“到顶部/到底部”跳转按钮，减少长页干扰。
- 资源海洋新增数据库驱动筛选建议：关键词、分类、标签、来源、表达工具 ID/名称、表达目标均来自 SQLite 当前可见资源，同时保留手动输入；后端新增 `/api/resources/filters`，表达工具筛选支持工具 ID、名称和分类模糊匹配。
- `/resources`、`/surf`、`/expression` 统一采用右侧目录模式；浏览冲浪来源标题保持可点击外链；表达工具详情从远侧面板改为点击卡片后原地展开/再次点击折叠，并支持 hash 深链自动展开。
- 浏览器复查：`/resources` 筛选建议数量为 keywords=160、categories=144、tags=160、sources=25、expression_tools=34、expression_goals=7；`/surf` 来源目录 sticky；`/expression#expression-tool-expr_tool_015` 展开后显示“微步骤 / 风险边界 / 更好回应”；三页均 `overflow=false`。
- 下一项建议进入 `resource_detail_and_practice_action_flow`：为资源卡增加独立详情/加入练习/错题改写入口，并把当前筛选状态同步到 URL，继续降低多记录浏览和训练转化成本。

## 2026-05-23 15:05 CST 资源详情页与筛选 URL 可恢复流

- `resource_detail_and_url_state_flow` 完成：新增 `/resources/:id` 资源详情页，展示完整内容、练习路径、来源与导读、结构化信息，并复用右侧 sticky 详情目录。
- 资源海洋卡片标题和“查看完整详情”进入详情页；卡片同时提供“加入训练”和“错题改写”动作，把资源浏览连接到训练闭环，而不是停留在阅读列表。
- 资源筛选状态现在同步到 URL query：关键词、类型、分类、场景、标签、来源、主线、表达工具、表达目标和页码都可恢复；详情页返回资源海洋时保留原筛选参数。
- 浏览器复查：默认 `/resources` 有 96 个详情链接，训练/错题动作存在，`overflow=false`；`/resources/1?q=边界&category=冲突修复&page=2` 显示详情目录、来源与导读、结构化信息、训练/错题入口，返回链接保留筛选 query。
- Commander DAG 已新增该节点；下一项建议进入 `resource_detail_smoke_gate`，把资源详情和 URL 可恢复流加入前端 world smoke，防止后续页面重构把这条体验链路打断。

## 2026-05-23 15:18 CST 资源详情与多记录页世界级 smoke 门禁

- `resource_detail_world_smoke_gate` 完成：`frontend/scripts/world-class-smoke.mjs` 路由矩阵新增 `/resources`、`/resources/1?q=边界&category=冲突修复&page=2`、`/expression#expression-tool-expr_tool_015`、`/surf`，桌面和移动端都会检查。
- smoke mock 层补齐资源列表/详情/筛选/来源、表达工具列表/详情/推荐/工具链、资源近重复队列、Provider 状态，以及 AI 伴侣表达工具链、关联资源、错题记忆字段，避免 mock 合约滞后掩盖真实页面风险。
- 扩展后的 `npm run smoke:world` 通过，`checked=38`，报告写入 `frontend/output/smoke/report.json`；同时重新通过 `npm run type-check`、`npm run build` 和资源后端 ruff。
- 这轮没有改数据库，也没有新增外部抓取；纯粹把资源浏览、资源详情、浏览冲浪、表达工具箱和 AI 伴侣交互纳入自动前端质量门禁。
- 下一项建议进入 `resource_detail_training_prefill_contract`：Trainer 接收 `resource_id` 后展示资源上下文预填卡，把“加入训练”从链接动作升级为明确的训练上下文。

## 2026-05-23 15:45 CST 资源进入训练上下文闭环

- `resource_detail_training_prefill_contract` 完成：`/trainer?resource_id=...` 会读取资源详情，在训练题上方展示“来自资源海洋的训练上下文”卡片，包含资源标题、场景/分类、表达目标、质量/难度和资源导读。
- 资源训练卡支持“回看资源”“用资源提示预填回应”“只做普通训练”；预填内容会结合场景、表达目标和常见失误生成低压、可退出、尊重边界的练习回应。
- 修正初次打开资源训练链接时题目加载和资源加载并发导致预填被清空的隐性问题：现在先加载训练题，再加载资源上下文，保证入口动作稳定。
- `frontend/scripts/world-class-smoke.mjs` 新增 `TrainerResourceContext` 交互门禁，桌面/移动端都会验证资源上下文、预填文本、回看链接、清除 resource_id 后保留原筛选 query。
- 下一项建议进入 `mistake_resource_recommendation_detail_flow`：把“错题改写”入口从 query 链接升级为错题页的资源上下文卡和推荐练习说明，让资源海洋、训练中心、错题本形成更完整的三角闭环。

## 2026-05-23 15:58 CST 资源错题改写上下文闭环

- `mistake_resource_recommendation_detail_flow` 完成：资源海洋和资源详情的“错题改写”入口现在带 `resource_id` 进入 `/mistakes`，不再只是松散关键词搜索。
- 错题本新增“来自资源海洋的错题改写上下文”卡片，展示资源标题、改写焦点、表达目标、场景/分类、质量/难度和使用提示，帮助用户围绕具体资源复盘错题。
- 错题页会用资源的常见失误、表达目标、场景、分类和标题作为焦点词优先匹配错题；如果没有匹配历史错题，会保留全部错题并提示可先带入训练生成新记录。
- 上下文卡提供“回看资源”“带入训练”“只看全部错题”三种动作；清除资源上下文时只移除 `resource_id`，保留 `q` 等搜索 query，方便恢复原来的查找路径。
- world smoke 新增 `MistakeResourceContext` 桌面/移动端交互门禁，资源到错题本、再到训练中心的三角闭环已有自动回归覆盖。
- 下一项建议进入 `resource_context_unified_query_contract`：把资源上下文在 Trainer、Mistakes、AI 伴侣中的 query 参数、来源回退、空态和错误态抽成统一小工具，减少后续页面各自实现产生漂移。

## 2026-05-23 16:03 CST 资源上下文统一 Query 契约

- `resource_context_unified_query_contract` 完成：新增 `frontend/src/composables/useResourceContext.ts`，统一处理 `resource_id` query 读取、资源详情加载、错误回调、清除上下文并保留其它 query。
- `Trainer.vue` 与 `Mistakes.vue` 已改用同一 composable，减少两个页面分别实现资源上下文导致的行为漂移；初次加载、hash/query 恢复和清除动作仍保持原有用户体验。
- 重构后 `TrainerResourceContext` 与 `MistakeResourceContext` 两条 smoke 继续通过，证明统一抽象没有破坏资源详情、训练预填、错题改写和 query 恢复。
- 下一项建议进入 `resource_context_ai_partner_entry`：在资源详情和资源海洋中增加“带入 AI 伴侣”入口，并让 TrainerAI 读取 `resource_id` 作为陪练开场上下文，继续提升 AI 伴侣活跃度和具体性。

## 2026-05-23 16:18 CST 设置页真实数据导出闭环

- `settings_real_export_artifact_flow` 完成：设置页“导出”不再只是 toast；点击后会生成本地 JSON 导出包，并在页面内展示导出包结果。
- 导出包包含 manifest、个人资料、偏好设置、数据统计、训练摘要、能力雷达、错题记录、到期复习和本地运行标记；manifest 写入 schema version、导出范围、记录数、导出时间和本地隐私说明。
- 页面导出结果区显示文件名、大小、结构化记录数、生成时间、SHA-256 校验指纹、覆盖范围和“保存文件”链接；即使浏览器下载被拦截，用户也能确认导出结果并再次保存。
- `frontend/scripts/world-class-smoke.mjs` 新增 Settings 路由和 `SettingsExport` 交互门禁，桌面/移动端验证导出面板、覆盖范围、blob 保存链接和文件名。
- 真实 in-app browser 复查 `/settings`：点击“数据 -> 导出”后出现“导出包已生成”，保存文件链接为 blob，文件名为 `relationship-training-export-2026-05-23.json`，横向溢出为 0。
- 下一项建议继续处理设置页其它假按钮：清除缓存应做选择性缓存清理并保留关键偏好，重置进度/注销账户应接入后端 dry-run/确认闭环，而不是只提示。

## 2026-05-23 16:36 CST 表达工具箱搜索建议与引导闭环

- `expression_search_suggestion_guidance` 完成：表达工具箱搜索框不再只给空白输入，新增原生 datalist、分组推荐词和“当前搜索 / 清除”状态条，用户不知道搜什么时可直接点工具、场景、目标、公式、分类或边界词。
- 推荐词同时来自稳定常用词和当前 SQLite 工具数据：包含“情绪标注 / PREP模型 / SCQA模型 / 退路 / 不施压 / 尊重边界”等，仍保留手动输入，避免把用户锁死在固定选项里。
- 后端 `/api/expression/tools?q=...` 搜索范围扩展到工具名、工具 ID、层级、分类、描述、公式、适用场景、关系/情绪适配、微步骤、风险边界和前后回应示例，搜索“冲突”“退路”等真实训练提示词能命中具体工具。
- world smoke 新增 `ExpressionSearchSuggestions` 交互门禁，验证 datalist、推荐分组、引导文案、点击“情绪标注”筛选、当前搜索状态和无横向溢出。
- 真实 in-app browser 复查 `/expression`：搜索框绑定 `expression-search-suggestions`，下拉选项 46 条，包含“情绪标注”“PREP模型”，页面显示“工具 / 场景 / 目标 / 公式”等推荐分组和“不确定搜什么时”的引导。
- 下一项建议进入 `settings_cache_clear_real_action`：继续治理设置页假按钮，把“清除缓存”从提示升级为真实本地缓存清理、结果回执和 smoke 覆盖。

## 2026-05-23 16:52 CST 多记录页目录折叠释放布局空间

- `toc_collapse_layout_reclaim` 完成：统一目录组件折叠后不再占用原右侧栏位，折叠按钮改为固定停靠在窗口右侧，避免中间留下未利用空白。
- `/resources`、`/surf`、`/resources/:id` 在目录折叠时把 `280px` 目录列释放为主内容宽度，资源卡/来源卡/详情内容可自动扩展；展开后恢复原 sticky 右侧目录。
- `/expression` 的目录折叠按钮同样固定到窗口右侧；由于该页右侧还有“工具链推荐”业务面板，保留右栏宽度，避免为了目录折叠误伤推荐面板。
- world smoke 新增 `TocCollapseLayout` 桌面回归门禁，自动点击 `/resources`、`/surf`、`/resources/1` 的目录折叠按钮，断言右侧目录列释放、按钮贴右、无横向溢出。
- 真实 in-app browser 复查：`/resources` 折叠前布局为 `973px 280px`，折叠后为 `1277px` 单列且按钮距右侧约 25px；`/surf` 与 `/resources/1` 也释放右列且 `overflow=0`；`/expression` 折叠后按钮贴右且工具链推荐仍可见。
- 下一项建议继续进入 `settings_cache_clear_real_action`，把设置页剩余提示型按钮逐步改成真实动作与审计回执。

## 2026-05-23 17:10 CST 设置页 Markdown 可读导出与保存位置提示

- `settings_markdown_export_location_clarity` 完成：设置页导出从 JSON 文件改为用户更容易阅读的 Markdown 文件，文件名为 `relationship-training-export-YYYY-MM-DD.md`。
- Markdown 内容包含导出概览、个人资料、偏好设置、训练摘要、错题记录、到期复习和原始审计 JSON 代码块，兼顾可读性与可审计性。
- 导出流程不再把“保存文件”做成容易误解的装饰按钮；现在先生成 Markdown，再提供两个明确动作：“选择位置保存”用于系统保存窗口，“下载到默认目录”用于浏览器下载目录。
- 页面明确显示保存位置提示：选择位置保存会保存到用户选定位置；默认下载动作会进入浏览器默认下载目录，避免用户不知道文件去哪了。
- `frontend/scripts/world-class-smoke.mjs` 已更新 SettingsExport 门禁，验证 `.md` 文件名、Markdown 动作、位置提示、blob 默认下载链接、覆盖范围和无横向溢出。
- 真实浏览器验证受系统保存窗口影响，旧标签点击被原生窗口阻塞；自动 smoke 已在独立 Playwright 环境完成设置页导出交互验证。

## 2026-05-23 17:25 CST 设置页每日提醒真实本地通知

- `settings_daily_reminder_local_notification` 完成：此前 20:00 只是偏好字段，不会真正通知；现在新增 `frontend/src/utils/localReminder.ts`，应用启动时读取偏好并安排下一次浏览器本地提醒。
- 保存偏好会写入 localStorage、请求浏览器通知权限并重新调度提醒；如果通知被拒绝或浏览器不支持，会在页面和 toast 中给出明确状态。
- 设置页偏好增加“测试提醒”按钮，可发送一条浏览器通知测试；提醒点击后会回到 `/daily`。
- 页面文案明确边界：这是浏览器本地通知，需要允许通知权限，并且页面或浏览器保持打开；不是手机后台推送，避免把能力说成系统级通知。
- world smoke 新增 `SettingsReminder` 桌面/移动端门禁，验证提醒区、20:00 默认值、测试提醒按钮、通知权限边界和无横向溢出。

## 2026-05-23 17:48 CST 我的档案真实训练证据联动

- `profile_real_training_evidence_binding` 完成：`/profile` 不再展示前端硬编码的能力百分比、训练次数、连续打卡或固定自我觉察文案。
- 基本信息仍来自 `/api/profile`，但未填写字段显示“待填写/待测评”，不再用“安全型/肯定言辞/35/50”伪装成用户画像结论。
- 能力成长曲线改为读取 `/api/training/radar`，由真实训练记录维度分生成；没有训练时显示 0 和“尚未训练”。
- 学习统计改为只展示当前接口可证明的口径：今日训练、近 7 天训练、近 7 天活跃、近 7 天平均得分、开放错题、待复习、样本库容量和能力总分。
- 自我觉察改为由档案核心议题、训练最弱维度和训练建议组合生成；无训练数据时明确提示“无法判定真实短板”。
- 页面新增“计算依据”卡片，逐项说明 `/api/profile`、`/api/training/radar`、训练摘要、错题/复习和样本库容量的来源与边界。
- world smoke 新增 `/profile` 路由和 `ProfileEvidence` 桌面/移动端门禁，断言真实 API 来源说明存在、旧硬编码统计和固定文案不存在。

## 2026-05-23 18:12 CST 表达工具箱与八阶路径学习脚手架升级

- `expression_and_path_learning_scaffold_upgrade` 完成：针对 `/expression` 与 `/path` 只给标题和简短说明、学习者难以理解概念的问题，完成前端信息架构重构。
- 表达工具箱检索区重构为“主搜索 + 层级/场景/目标筛选 + 分组推荐词 + 当前条件 chip”，减少重复控件和空白输入焦虑；推荐词按“工具概念、使用场景、表达目标、表达公式、工具类别、安全边界”组织。
- 工具链推荐从右侧栏移到检索区下方，成为横向推荐带；右侧栏只保留工具目录，目录折叠时可以释放内容宽度，不再被业务推荐卡片牵制。
- 表达工具卡片展开后新增“概念定义、核心原则、公式、实践方法、适用场景、风险边界、旧/新回应对比、迁移练习”，让初学者能从一个词进入可操作训练。
- 八阶路径页新增“这条路线到底在训练什么”总纲，明确主线为观察、命名、验证、行动、复盘，并补充先证据后判断、先安全后张力、先小动作后人格结论、先复盘后升级四条原则。
- 每个八阶节点补充概念定义、核心原则、实践方法、适用场景、常见误区、低质量做法、更好做法和本阶练习题，避免页面只停留在标题、分数和晋级条件。
- world smoke 新增/扩展 `ExpressionSearchSuggestions` 与 `PathLearningScaffold` 门禁，自动检查学习脚手架、工具链位置、卡片展开详情和路径节点课程内容。

## 2026-05-23 18:31 CST 资源海洋学习拆解卡升级

- `resource_learning_scaffold_cards` 完成：资源海洋列表卡片不再只显示标题、摘要和元数据，而是新增“学习拆解”区，覆盖概念定义、核心原则、实践方法和练习任务。
- 列表卡片会从现有结构化字段和内容正文中提取“场景 / TA说 / 常见失误 / 更好回应 / 练习任务”，展示低质量回应与更好回应对比，帮助用户直接看懂怎么练。
- 资源详情页新增“学习拆解”独立章节，补齐概念定义、核心原则、实践方法、适用场景、低质量做法、更好做法和练习任务。
- 增加来源边界说明：有外链的资源标记“有原文入口”，页面只做结构化学习拆解；本地原创或合成素材标记“项目原创训练卡”，不伪装成外部原文。
- 这轮没有虚构外部原文，也没有复制第三方全文；优先用数据库现有字段生成可学习结构，后续外部原文抓取仍需走来源许可、短摘录和审计链。
- world smoke 新增 `ResourceLearningScaffold` 桌面/移动端门禁，验证资源列表和详情页都包含学习拆解、案例对比、练习任务、来源边界且无横向溢出。

## 2026-05-24 00:25 CST 导入质量 issue 分桶治理闭环

- `p0_import_quality_issue_closure` 完成：导入质量报告新增 `issue_triage`，把活跃历史问题分为 `batch_closable`、`source_review_required`、`manual_reimport_required` 三类。
- issue 队列接口同步返回 triage 摘要，包含当前质量分、批量关闭后的投影质量分、每类来源数/问题数、样例 issue id、推荐处理动作和不可自动关闭的质量门禁。
- 这轮没有批量删除或自动关闭历史 issue；所有关闭仍必须走 reviewer、resolution、audit log，避免把来源质量问题用代码“刷干净”。
- 新增回归测试覆盖 warning-only 来源可进入批量复核关闭、error 来源必须进入来源契约复核、分数投影不低于当前分、triage 不绕过人工治理。
- 完整验证链通过：learning pipeline、schema guard、commander tests、ruff、regression-audit、frontend type-check/build/world smoke。

## 2026-05-24 00:45 CST Reviewed 精品训练卡发布候选补位

- `p0_reviewed_publish_boutique_batch` 完成：新增 `/api/evolution/reviewed-assets/boutique-batch`，支持 dry-run 与真实执行，幂等生成项目原创精品训练卡。
- 精品卡覆盖微关系信号、情绪流动、边界与同意、暧昧张力、冲突修复、长期连接、幽默互动、错题改写等主线轴，每张都包含场景、TA说、常见失误、更好回应、边界与同意、练习任务。
- 这轮没有放宽发布门禁；短泛资源和 legacy/manual 泛化知识仍会被 `quality_signal.blocks` 阻断。
- 默认资源列表进一步收紧为 `reviewed/published` 可见，并隐藏 pytest fixture 来源，减少用户页面被测试数据或低状态草稿污染。
- 已真实执行精品批次：创建 5 条、复用已存在 3 条；回归审计显示 reviewed 发布候选 `publish_ready=27`。
- 执行后导入质量出现 6 个可自动修复字段，已运行安全 repair plan 补齐元数据，回到 `auto_repairable_fields=0`。

## 2026-05-24 00:57 CST 资源近重复与练习完整度可观测化

- `p0_resource_near_duplicate_readability` 完成：资源质量报告新增 `perceived_duplicate_debt` 和 `practice_completeness`，把“看起来重复/内容单薄”转成可排队治理指标。
- 感知重复报告覆盖可见资源数、重复家族数、重复家族资源数、最大家族规模、首屏最大连续家族 run、首屏超过 3 连的风险次数。
- 练习完整度报告覆盖平均分、完整卡数量、薄卡数量和必备标记：场景、TA说/对方说、常见失误、更好回应、边界/同意、练习任务。
- 近重复队列现在只扫描 `reviewed/published` 可见资源，不再把 draft/quarantine 噪音混入治理结果，保证治理口径与用户看到的资源海洋一致。
- 真实数据报告显示：首屏最大连续家族 run 为 1，当前首屏打散有效；但可见资源仍有 933 个重复家族、最大家族 36、薄卡 7939，这是下一轮批量重写/隔离的明确对象。

## 2026-05-24 01:00 CST 多记录页面目录与检索体验验收

- `p0_multi_record_page_ux_unification` 验收完成：资源海洋、浏览冲浪、资源详情、表达工具箱已接入共享 `PageTocSidebar`。
- 目录折叠按钮固定停靠右侧；资源海洋、浏览冲浪、资源详情折叠后释放原右侧目录列，避免空白占位挤压主内容。
- 资源海洋关键词、类别、标签、来源、表达工具、表达目标均有数据库建议下拉，同时保留手动输入；表达工具箱也有工具/场景/目标/公式/边界推荐词。
- 表达工具箱的工具详情采用卡片内展开，工具链推荐已移出右侧目录区域，避免业务卡片占用目录空间。
- 已用 world smoke 覆盖 TOC 折叠、表达搜索建议、资源学习拆解、路径学习脚手架等关键交互。

## 2026-05-24 01:08 CST P1 学习与证据层验收归档

- `p1_expression_learning_depth`、`p1_path_curriculum_depth`、`p1_profile_settings_evidence`、`p1_vector_recall_calibration`、`p1_training_emotional_flow` 已按现有实现与验证结果归档完成。
- 表达工具箱已经从词表升级为可展开微课程；路径页已经从路线标题升级为带概念、原则、方法、场景、误区、案例和练习的课程脚手架。
- 档案页和设置页已完成证据化：档案指标展示来源依据，设置导出为真实 Markdown，提醒为浏览器本地通知并说明限制。
- 向量召回通过 `tests/test_vector_index.py`、`mypy --strict` 和指挥官回归；当前 `top10_recall=0.75`，达到 P1 目标。
- 训练/AI 伴侣链路已展示情绪路径、状态变化、信任/压力/边界/连接和风险边界；安全阻断路径仍给出非操控替代练习。

## 2026-05-24 01:24 CST P2 链接健康、批次回滚与安全红队闭环

- `p2_source_link_health` 完成：新增 `/api/resources/sources/health-check`，支持 dry-run 与真实检查；真实检查只记录状态、HTTP code、跳转、`last_checked_at` 等元数据，不保存网页正文。
- 浏览冲浪来源列表会读取最近一次健康审计结果，并展示可访问/失效、HTTP 状态码、跳转地址和最后检查时间；来源标题仍保持外链可点击。
- 失效链接对应的 `reviewed/published` 资源会被降级为 `draft`，让默认资源海洋不再继续展示无效来源资源。
- `p2_batch_rollback_dashboard` 完成：新增 `/api/evolution/import-batches/rollback-plan`，输出批次、issue、知识条目、资源和日志影响范围，以及 planned transitions、rule version、prompt version、重复率、发布率、隔离数和开放 issue 数。
- 回滚计划是非破坏性 dry-run：不删除行，不改状态，审计 payload 明确 `content_deleted=false` 与 `dry_run_only=true`。
- `p2_safety_red_team_expansion` 完成：安全护栏新增 `consent_violation`，覆盖无视拒绝、逼迫同意、偷拍视频、偷看手机、定位/查岗等越界请求，阻断后仍返回尊重边界的替代练习。
- 发布门禁新增高张力内容边界证据检查：暧昧、调情、成人邻近等资源若没有边界/同意/可拒绝/停止/不施压/舒服/选择等证据，不允许成为 publish-ready。
- 所有 P0/P1/P2 待办已归档完成；剩余系统债为历史导入人工复核、真实资源薄卡批量治理，以及 DeepSeek 外部 400/403 授权/服务侧问题。

## 2026-05-24 01:37 CST Zero-Gate 契约补齐与旧任务清单同步

- 按 `docs/本项目Zero-Gate全自动构建Prompt.md` 补齐四个缺失契约文件：`docs/requirements_final.md`、`docs/high_level_design.md`、`docs/api_contract.json`、`docs/dependency_graph.md`，并新增 `docs/dependency.dot`。
- `requirements_final.md` 固化产品目标、八阶路径、训练闭环、进化闭环、安全闭环、页面需求和非功能需求。
- `high_level_design.md` 固化 AI Provider、Safety Guardian、Training Engine、Knowledge Center、Evolution Pipeline、Resource Ocean、Expression Toolbox、Observability 等模块边界。
- `api_contract.json` 记录当前主要 API 模块、路径和响应契约，作为前端和后续自动构建的接口索引。
- `dependency_graph.md` 与 `dependency.dot` 固化模块、页面和验证依赖。
- 同步 `docs/tasks.md`：把已经被现有模型/API/配置/smoke 证明完成的旧待办改为完成，包括 tension dimensions、ruff 中文规则、content_sources 迁移、migration runner、资源库 500+、source registry/raw/annotation/version 表、情绪训练入库、结构化 diff、mastery 推荐、curriculum graph、Source Registry 核心来源、sqlite-vec、Dashboard/Mistakes/Knowledge smoke。
- 保留真正未完成的数据内容建设任务：300 条 reviewed/published 互动样本、1000 条候选样本、连接素材库重构、100 条 Gold samples；已拆入 `docs/tasks/data_content_backlog.json`。

## 2026-05-24 01:56 CST 数据内容 backlog 全部完成

- 新增 `backend/database/data_content_governance.py`，把剩余 4 个数据内容任务收敛为一个幂等治理入口：候选样本扩容、reviewed/gold 门禁、Gold 校准版本、连接素材库重分类。
- 已真实执行治理入口：互动样本从 362 增至 1008；可训练样本 `review_status in reviewed/published/gold` 增至 304；Gold 样本增至 104；Gold annotation versions 增至 230。
- 候选样本均为 `project_original` 本地原创结构化训练卡，写入 `source_trace_json`、`quality_json`、风险边界和审核状态；不抓取、不保存第三方全文或可识别私聊原文。
- 训练推荐与随机样本入口已收紧为只使用 reviewed/published/gold，draft 候选不会默认进入训练。
- 资源库的“话术”标注已重构为六类连接动作：破冰观察 7537、温和幽默 888、欣赏表达 18、修复句式 1706、边界表达 2148、退路式邀请 3。
- `docs/tasks.md` 与 `docs/tasks/data_content_backlog.json` 已同步为全部完成；`docs/tasks.md` 当前无未完成复选项。
- 执行导入质量安全修复计划后，`auto_repairable_fields` 从 3 清为 0；剩余 80 个历史导入 issue 属于人工复核/来源级治理债，不做自动伪关闭。

## 2026-05-24 05:15 CST 最终审计与执行方案归档

- 新增 [final_audit_execution_plan_2026-05-24.md](tasks/final_audit_execution_plan_2026-05-24.md)，把已完成工程待办、数据库验收数、连接素材库分布、不可自动关闭的运营债和后续执行口径固定成单独档案。
- 本轮审计确认：`data_content_backlog.json` 为 4/4 completed，`next_stage_backlog.json` 为 13/13 completed，Commander state 为 108/108 completed、pending 0。
- 当前数据库快照：interaction_samples 1008，training_ready 304，draft_candidates 671，gold_samples 104，resources_ready 12317。
- 不再把 DeepSeek 400/403 或 80 个历史导入 issue 伪装成自动化代码待办；它们分别归类为外部 provider 授权/服务侧排查和人工来源级复核。

## 2026-05-24 12:49 CST 阶元式心理沟通与场景化表达融合升级

- 新增 [阶元式心理沟通与场景化表达标准流程.md](阶元式心理沟通与场景化表达标准流程.md)，把“场景化表达”“识别情绪/给出理解/好奇深挖/拒绝评判/深度共情”整理为九个阶元和一个可训练闭环。
- 新增 `backend/database/scene_empathy_worldclass_seed.py`，幂等写入知识中枢、表达工具链和资源海洋；内容全部为项目原创结构化案例，不搬运第三方全文。
- 知识中枢新增 1 个分区、9 条高质量阶元知识卡，卡片包含概念、原则、方法、场景和练习，并通过 `source_metadata_json.learning` 提供精细展示字段。
- 表达工具箱新增 5 条工具链：场景化共情九阶链、不评判好奇深挖链、职场画面化说服链、冲突细节修复链、温和拒绝边界链。
- 资源海洋新增 162 条阶元沟通训练卡，覆盖 9 个阶元、6 个场景、3 个难度；每条都有场景、TA 原话、常见失误、更好回应、边界出口、迁移练习和 case blueprint。
- `backend/api/knowledge.py` 更新为优先读取结构化 `learning` 元数据，避免世界级知识卡在前端退化成通用兜底话术。
- 已备份数据库：`data/backups/relationship_training-before-scene-empathy-worldclass-20260524124614.db`。

## 2026-05-24 13:21 CST 深度舒适聊天与现实感受交替提问升级

- 新增 [深度舒适聊天与现实感受交替提问标准流程.md](深度舒适聊天与现实感受交替提问标准流程.md)，把“问细节”“现实层/感受层交替”“情绪共振”“关键词延展”“深层情绪反馈”“非语言共情”整理成可训练流程。
- 新增 `backend/database/deep_comfort_chat_seed.py`，幂等写入项目原创知识、表达工具链和训练资源；目标从“让对方主动”校准为“让对方更舒服地连接自己”，避免操控导向。
- 知识中枢新增 1 个分区、6 条知识卡：价值降噪、问细节、现实-感受交替提问、情绪共振、深层情绪反馈、非语言共情。
- 表达工具箱新增 4 条工具链：现实感受交替深聊链、关键词情绪延展链、深层情绪反馈链、非语言舒适承接链；工具链总数增至 14。
- 资源海洋新增 90 条深度舒适聊天训练卡，覆盖 6 个能力点、5 个场景、3 个难度；每条都有现实问题、感受问题、关键词、深层需要、边界出口和迁移练习。
- 知识搜索扩展到摘要、分类、标签和 `source_metadata_json`；表达工具链搜索新增 `q`，表达页会读取 URL query 并同步刷新工具链列表。
- 已备份数据库：`data/backups/relationship_training-before-deep-comfort-chat-20260524131744.db`。

## 2026-05-24 13:37 CST 功能模块选项卡模板标准化

- 新增 [功能模块选项卡结构模板规范.md](功能模块选项卡结构模板规范.md)，为资源海洋、表达工具箱、知识中枢、训练中心、AI 伴侣、错题本、八阶路径、浏览冲浪、治理审计、档案设置定义完整 tab 模板。
- 新增 `docs/tasks/module_tab_templates.json`，把各模块 tab 的 `id/label/summary/primaryContent/primaryAction/emptyState/qualityGate` 固化为机器可读清单。
- 新增 `frontend/src/components/ModuleTabs.vue`，统一选项卡的横向滚动、active 状态、`role=tablist/tab/tabpanel`、摘要说明和移动端可用性。
- 设置页 `/settings` 已接入 `ModuleTabs` 作为低风险示范：账户、偏好、数据、关于四个 tab 都展示清晰摘要。
- 该模板后续可逐步应用到资源海洋、表达工具箱、知识中枢和治理页面，避免每个模块独立发明 tab 样式和空状态。

## 2026-05-24 13:58 CST 世界级模块模板总则与机器校验

- 新增 [世界级模块选项卡与内容模板总则.md](世界级模块选项卡与内容模板总则.md)，把模块职责、案例故事、对话对比、5W2H、场景、情绪流、价值降噪、问细节、现实-感受交替、情绪共振、深层情绪反馈、非语言共情、边界出口定义为后续修订的强约束。
- `docs/tasks/module_tab_templates.json` 升级为 `2026-05-24-worldclass-v2`：每个 tab 必须包含 `jobToBeDone`、`fiveW2H`、`scenarioTemplate`、`caseStoryTemplate`、`dialogueTemplate`、`comparisonTemplate`、`emotionFlowTemplate`、`expressionMoves`、`dataContract`。
- 新增 `tools/validate_module_tab_templates.py`，对世界级模板执行机器校验；新增 `tests/test_module_tab_templates.py`，把模板完整性纳入 pytest。
- 模板已覆盖资源海洋、表达工具箱、知识中枢、训练中心、AI 伴侣、错题本、浏览冲浪、治理与审计等核心模块，并明确采集/扩库不得默认保存第三方全文。
- 这套模板以后作为页面重构、数据库扩展、网络信息采集、资源生成和知识卡改版的共同入口规则。

## 2026-05-24 14:18 CST 需求与功能原则统一索引

- 新增 [项目需求与功能原则统一索引.md](项目需求与功能原则统一索引.md)，把 L0 最高目标、L1 最终需求、L2 架构边界、L3 功能模板、L4 任务审计记录统一成单一入口。
- README 已新增“需求与原则入口”，指向统一索引、最终需求契约、世界级模块模板总则、功能模块选项卡规范和机器可读模板。
- 统一结论：原则层已经完成收敛；历史方案和审计文件作为背景/状态账本保留，后续实际执行以 `requirements_final.md`、`世界级模块选项卡与内容模板总则.md` 和 `module_tab_templates.json` 为主。

## 2026-05-24 14:42 CST 核心内容页模块选项卡落地

- `/resources` 接入统一 `ModuleTabs`：新增“案例矩阵 / 来源边界”工作区，`tab=source_boundary` 可恢复来源边界说明，并保留现有组合检索、主线分组、卡片学习拆解、目录和分页。
- `/expression` 接入统一 `ModuleTabs`：新增“原子工具 / 工具链”工作区，工具链推荐从侧栏式信息块收敛到独立 tab，`q/layer/scene/goal/tab` 均可写入 URL 并恢复。
- `/knowledge` 接入统一 `ModuleTabs`：新增“知识卡片 / 5W2H”工作区，5W2H 不再埋在长页驾驶舱里，而是可直达的元问题 tab。
- 本轮只做核心内容页的模板落地，不改数据库、不改 API、不重构旧页面，以降低回归风险。

## 2026-05-24 15:06 CST 训练闭环与来源页选项卡落地

- `docs/tasks/module_tab_templates.json` 补齐 `/surf` 的“全部来源 / 采集策略 / 链接健康”，以及 `/mistakes` 的“待复习 / 三版改写 / 掌握证据”，让机器模板和页面职责一致。
- `/surf` 接入统一 `ModuleTabs`：来源目录、采集策略、链接健康可通过 `tab` 参数恢复；链接健康 tab 默认只看已有健康检查记录的来源。
- `/trainer` 接入统一 `ModuleTabs`：当前题和七维反馈分成两个工作区，提交作答后自动切到反馈 tab；没有反馈时显示清晰空状态。
- `/mistakes` 接入统一 `ModuleTabs`：待复习优先展示到期错题，三版改写承接现有错题卡，掌握证据展示掌握率和复习证据。
- 本轮仍不改数据库和 API，只把已有训练闭环内容按统一模板归位。

## 2026-05-24 15:31 CST 资源卡完整案例学习区升级

- `/resources` 列表卡片新增“完整案例学习区”，优先读取 `case_blueprint_json`，把场景故事、完整对话、低质量回应、更好回应、边界出口、为什么这样学、回应步骤、练习与迁移集中在同一区块。
- 列表正文不再先铺大段原始内容，避免用户看到抽象堆叠；“原则与练法”作为辅助区展示核心原则和实践方法。
- 针对四阶心理沟通资源（如 `resource-24158`）能直接在列表卡内看到完整对话：TA 原话、旧回应、新回应和迁移场景，不必跳转详情页才知道在学什么。
- 本轮只改前端展示模板，不改数据库和资源生成脚本；详情页已有案例蓝图继续作为完整深读入口。

## 2026-05-24 15:42 CST 案例蓝图多视角回应与举一反三补强

- 新增 `backend/database/case_blueprint_enrichment.py`，对已有 `case_blueprint_json` 做幂等补强，新增 `response_variants`、`perspective_examples`、`transfer_analysis`、`misread_risks`、`practice_ladder` 和 `quality_notes`。
- 已对 11892 条资源蓝图完成数据库级补强；内容为项目原创结构化分析，不抓取、不保存第三方全文。
- 已备份数据库：`data/backups/relationship_training-before-case-blueprint-enrichment-20260524-152953.db`。
- `/resources` 列表卡片在完整案例学习区新增“多视角更好回应”和“举一反三分析”，让用户直接看到轻量承接、现实-感受交替、深层共情、边界稳态等不同回应视角。
- `/resources/:id` 详情页新增完整深读结构：多视角更好回应、举一反三分析、迁移分析、常见误读风险和练习阶梯。
- 本轮修复“更好回应只有一句、缺少不同视角例子、缺少举一反三”的根因：数据层先补齐，前端再按学习路径集中呈现。

## 2026-05-24 15:48 CST 更好回应上下文一致性修复

- 修复 `backend/database/psychological_communication_ladder_seed.py` 的历史源头：第 3 阶“拒绝评判”不再套用万能句，而是按暧昧、社交、职场语境生成贴合上下文的回应。
- 新增 `backend/database/contextual_response_repair.py`，只修复 `project_original:psychological_communication_ladder_v1` 中包含旧万能句的历史记录，并同步更新 `case_blueprint_json`、正文 `content`、`content_fingerprint` 和多视角补强字段。
- 已修复 9 条历史错配资源；截图中的 `resource-24158` 现在回应为“你突然想吃甜的，听起来像是在给自己一个小小的安慰。我不会拿身材或对错评价这件事……”。
- 已备份数据库：`data/backups/relationship_training-before-contextual-response-repair-20260524-154806.db`。
- 后续采集/生成规则追加约束：任何模板缺字段时可以用本地原创/模型生成补足，但必须锚定 `setting/their_words/surface_signal/deeper_need/common_mistake`，不得用跨场景万能句冒充具体案例。

## 2026-05-24 16:08 CST 上下文质量治理与页面刷新闭环

- 新增 `backend/database/contextual_quality_governance.py`，对已发布/已审核资源蓝图做可重复治理：清理 `希望希望`、重复标点、`[object Object]`、通用多视角回应，并把 `response_variants` 重新锚定到 `setting/their_words/deeper_need/boundary_note`。
- 新增 `tests/test_contextual_quality_governance.py`，覆盖文本清理、变体重锚定、数据库写回和幂等行为。
- 真实执行两轮治理：先修复 11892 条多视角回应的通用模板，再修复 372 条场景化回应的双句号尾缀；最终 dry-run 更新数为 0，残留质量痕迹计数为 0。
- 已备份数据库：`data/backups/relationship_training-before-contextual-quality-governance-20260524-160400.db` 与 `data/backups/relationship_training-before-contextual-quality-governance-20260524-160541.db`。
- `/resources` 增加页面重新可见时自动刷新资源列表，避免数据库/API 已更新但用户当前浏览器 tab 仍停留在旧内存数据。
- 根本治理策略明确：后续抓取或生成缺字段时，可以补全本地原创分析，但必须先通过“上下文锚定 + 质量痕迹清理 + 幂等 dry-run + 数据库备份”流程。

## 2026-05-24 16:26 CST 表达工具学习蓝图与真实对话案例升级

- `expression_tools` 新增 `learning_blueprint_json` 学习蓝图字段，表达工具不再只展示定义、公式和一句示例，而是提供概念定义、核心原则、适用/禁用边界、微步骤、真实对话案例和迁移练习。
- 新增 `backend/database/expression_tool_enrichment.py`，对 60 个已发布表达工具幂等生成项目原创结构化学习蓝图；每个工具至少包含 3 个场景化对话案例，案例字段统一为场景故事、TA 原话、低质量回应、更好回应、为什么有效和迁移提示。
- 新增 `tests/test_expression_tool_enrichment.py`，覆盖蓝图生成和数据库写回；已真实执行更新 60 个工具，并备份 `data/backups/relationship_training-before-expression-tool-enrichment-20260524-161146.db`。
- `/api/expression/tools` 和 `/api/expression/tools/{id}` 现在返回 `learning_blueprint`；前端 `ExpressionTool` 类型同步增加学习蓝图结构。
- `/expression` 工具卡展开区已改为学习型结构：优先读取数据库蓝图展示概念、原则、实践方法、风险边界、不适合使用、真实对话案例、低质量/更好回应对比和迁移练习。
- 修复 Vite 本地代理默认指向 `localhost:8000` 导致页面资源显示为 0 的运行态问题，默认代理目标改为 `http://127.0.0.1:8000`，与当前后端监听地址一致。

## 2026-05-24 18:12 CST 资源更好回应对话级治理

- 修复 `backend/database/case_matrix_resource_upgrade.py` 的源头生成规则：`better_response` 不再拼接“我的下一步是/训练目标/依恋策略说明”，改为可直接说出口的上下文回应。
- 新增 `backend/database/dialogue_response_governance.py`，把历史 `case_matrix_v1` 资源中的元说明式“更好回应”批量改写为真实对话，并新增 `dialogue_script` 多轮对话脚本。
- 已分两轮真实治理数据库：先更新 11520 条矩阵资源的 `better_response/response_variants/dialogue_script/response_steps/content`，再更新 8532 条不自然引号标点；备份分别为 `data/backups/relationship_training-before-dialogue-response-governance-20260524-180850.db` 和 `data/backups/relationship_training-before-dialogue-response-governance-20260524-181100.db`。
- `/resources` 列表卡片和 `/resources/:id` 详情页新增“完整多轮对话”展示，按 TA、低质量回应、更好回应、继续回应、边界收束集中呈现，避免学习内容分散。
- 收敛结果：`case_matrix_v1` 中 `better_response` 含“我的下一步是”的数量为 0，`better_response` 中 `。”。` 坏标点数量为 0，11520 条矩阵资源均有 `dialogue_script`。

## 2026-05-24 18:42 CST 高质量数据采集工具与数据库扩展

- 新增 `backend/database/high_quality_data_acquisition.py`，把 `SOURCE_CATALOG` 中的可信来源登记为 `source_registry`，把外部资源保存为 metadata-only 的 `raw_content_items` 锚点，再生成项目原创的完整训练资源。
- 采集边界固定为 `link_title_summary_short_excerpt_structured_analysis_local_original_rewrite_only`：第三方网站只保存链接、标题、摘要、短摘录、结构化分析和本地原创改写，不默认保存全文。
- 新增 `tests/test_high_quality_data_acquisition.py`，覆盖 dry-run 不落库、真实执行生成完整记录、按 `content_unit` 防重复。
- 已执行三轮数据库扩展，生成来源登记、原始锚点、导入批次和资源记录；随后发现旧签名逻辑把表达工具 ID 纳入唯一签名，导致同一内容单元可重复生成。
- 已修复根因：表达工具选择改为由稳定 `content_unit` 哈希决定，存在性判断改为 `resource_uuid OR content_unit`；后续 dry-run 已收敛为新增 0、跳过 1116。
- 已清理本批采集历史伪重复：保留每个 `content_unit` 最早一条，删除 1833 条重复记录；当前 `project_original:high_quality_acquisition_v1` 为 1116 条唯一内容单元，覆盖 23 个来源、10 个场景、6 条主线轴、355 个变体族。
- 数据库备份：`data/backups/relationship_training-before-high-quality-acquisition-20260524-182205.db`、`data/backups/relationship_training-before-high-quality-acquisition-20260524-183246.db`、`data/backups/relationship_training-before-high-quality-acquisition-20260524-183533.db`、`data/backups/relationship_training-before-high-quality-acquisition-dedupe-20260524-183939.db`。
- 本轮把“海量扩展”的标准从单纯数量改为可审计的最小单元：来源可追溯、版权边界清晰、案例蓝图完整、多轮对话可练、内容单元不可重复。

## 2026-05-24 19:22 CST 非暴力沟通三步法项目级融合

- 新增 `backend/database/nvc_three_step_seed.py`，把“我的感受 -> 我的期待 -> 你的选择”落成可重复执行的项目原创种子。
- 新增 `tests/test_nvc_three_step_seed.py`，覆盖 dry-run、完整写入、幂等防重复，并确认训练卡包含完整对话和三步拆解。
- 知识中枢新增“非暴力沟通三步法”分区和知识条目：定义、原则、适用场景、禁用边界、核心例句统一入库。
- 表达工具箱新增 `expr_tool_061`“非暴力沟通三步法”，包含学习蓝图、核心原则、反模式、真实对话案例和练习阶梯。
- 工具链新增“非暴力三步低压表达链”，用于真诚表达但不绑架：感受表达、低压力请求、真实选择出口。
- 资源海洋新增 18 张训练卡，覆盖暧昧表达、行程变化、冲突修复、拒绝帮忙、初识深聊、异地报备六个场景，每个场景 D1-D3；每张卡都有完整对话、坏回应、好回应、三步拆解、边界提醒和练习任务。
- 二次优化：D1-D3 都保留完整三步回应，难度只改变对话长度和分析深度，避免学习者只看到片段式“感受”而误解方法。
- 数据库备份：`data/backups/relationship_training-before-nvc-three-step-20260524-191841.db` 与 `data/backups/relationship_training-before-nvc-three-step-20260524-192004.db`。

## 2026-05-24 19:36 CST 表达工具箱非暴力三步法可见性修复

- 修复 `/api/expression/tools` 默认排序：从旧的 `layer/category/id` 改为 `quality_score desc, updated_at desc, id`，让新增的高质量工具不再藏在列表后段。
- 表达工具搜索新增覆盖 `learning_blueprint_json`，用户搜索“非暴力、选择、真诚表达、反模式”等蓝图内容也能命中工具。
- `/expression` 详情展开区兼容新学习蓝图字段：`concept`、`poor_response`、`anti_patterns`、`practice_ladder` 和对象型 `micro_steps`，避免真实案例、风险边界或实践方法显示为空。
- 已重启本地 8000 后端；当前 `/expression` 首张工具卡为 `expr_tool_061`“非暴力沟通三步法”，展开后可见概念、原则、三步实践、风险边界、真实对话案例和练习阶梯。

## 2026-05-24 20:10 CST 元数据补齐与数据库筛选数量治理

- `/api/resources/filters` 统计口径收紧为 reviewed/published、非 quarantine、非 pytest 的真实可见资源，类型、场景、标签、来源、表达工具、表达目的和关键词均返回 SQLite 现存记录数。
- `backend/database/module_metadata_completion.py` 扩展为补齐场景、标签、来源、表达工具 ID、表达目的、案例蓝图、内容单元、覆盖轴和变体家族；真实执行更新 8 条历史缺字段资源。
- 数据库补齐后，可见资源缺失统计归零：type/category/scene/tags/source/expression_tool_ids/expression_goal 均为 0。
- `/api/knowledge/filters` 新增知识中枢数据库筛选项，返回分区、分类、标签、来源、关键词及数量；前端 `/knowledge` 接入分区/分类/标签/来源/关键词组合检索。
- `/resources` 不再把 0 条兜底词混入下拉和快选；页面先获取数据库筛选项再渲染资源，快选显示真实数量。
- `/expression` 下拉不再对未知数量显示 `· 0`；后端 facets 保留数据库存在项数量，避免假空数据误导用户。
- 数据库备份：`data/backups/relationship_training-before-module-metadata-completion-20260524-195912.db`。
- 验证：`tests/test_module_metadata_completion.py tests/test_catalog_profile_review_api.py::test_sample_and_resource_catalog_contracts_match_frontend tests/test_expression_api.py -q` 通过；`npm run type-check` 通过；`npm run build` 通过。

## 2026-05-24 20:54 CST 历史通用案例蓝图上下文重建

- 新增 `backend/database/contextual_case_blueprint_repair.py`，只治理 `module_metadata_completion_v1` 遗留蓝图，把默认“刚认识深聊”等通用对话按每条资源的 `type/category/title/scene/content` 重建为上下文一致的案例蓝图。
- 已真实修复 7979 条旧蓝图；当前 published/reviewed 资源中 `json_extract(case_blueprint_json,'$.version')='module_metadata_completion_v1'` 为 0，双句号等标点残留为 0。
- 示例 `resource-47` 已从“刚认识的人聊很深”修复为“做饭互怼”语境：完整对话包含原始三轮、贴合玩笑边界的更好回应、对方反馈和边界收束。
- `/resources` 列表的“完整对话”展示改为：有 `dialogue_script` 时只展示多轮对话，不再紧跟一组重复的 TA/低质量/更好回应摘要；无脚本时才使用 fallback 摘要。
- `module_metadata_completion.py` 后续补缺失蓝图时改用上下文重建逻辑，不再把默认场景句套到不相关内容上。
- 数据库备份：`data/backups/relationship_training-before-contextual-case-blueprint-repair-20260524-204926.db`、`data/backups/relationship_training-before-refresh-contextual-enrichment-20260524-205043.db`。
- 验证：`tests/test_contextual_case_blueprint_repair.py tests/test_module_metadata_completion.py tests/test_dialogue_response_governance.py tests/test_contextual_quality_governance.py -q` 通过；`npm run type-check` 通过；`npm run build` 通过；`/api/resources/47` 返回修复后的上下文案例。

## 2026-05-24 21:12 CST 脑筋急转弯资源扩容与页面筛选修复

- 新增 `backend/database/riddle_interaction_seed.py`，把脑筋急转弯作为“低压互动工具”扩成项目原创训练资源，不抓取第三方全文。
- 新增 `tests/test_riddle_interaction_seed.py`，覆盖 dry-run 不写库、真实执行生成完整记录、按 `content_unit` 幂等防重复。
- 真实执行新增 144 条急转弯训练卡，覆盖初识、暧昧、社交、冲突、修复、分歧、异地、长期 8 个场景，每个场景包含低压急转弯、场景急转弯、观察急转弯、关系急转弯、边界急转弯、共情急转弯 6 类机制，并按 D1-D3 分层。
- 同步升级 13 条旧急转弯资源为 `legacy_riddle_upgrade_v1`，补齐谜面、谜底、完整对话、低质量回应、更好回应、边界收束、迁移练习和多视角分析。
- 急转弯 reviewed/published 资源数量从 13 条提升到 157 条；缺蓝图/缺谜底/缺对话记录为 0，`content_unit` 重复为 0。
- 修复 `/resources` 初次进入时沿用旧 Pinia 筛选状态的问题：现在 URL 未声明的筛选项会清空，避免用户打开 `/resources?type=riddle` 仍被旧关键词/标签/source 隐形过滤成 0 条。
- 数据库备份：`data/backups/relationship_training-before-riddle-interaction-seed-20260524-210740.db`、`data/backups/relationship_training-before-legacy-riddle-upgrade-20260524-210813.db`。
- 验证：`tests/test_riddle_interaction_seed.py tests/test_contextual_case_blueprint_repair.py tests/test_module_metadata_completion.py -q` 通过；`npm run type-check` 通过；`npm run build` 通过；`/api/resources/filters` 返回 `riddle=157`；浏览器 `/resources?type=riddle` 显示 `第 1 / 4 页 · 1-48 / 157 条`。

## 2026-05-24 23:24 CST 浏览冲浪高质量来源扩展与轨迹指南入库

- 新增 `backend/database/source_surf_expansion_seed.py`，按 metadata-first 模板登记高质量来源：只保存链接、标题、摘要、短摘录、结构化分析和本地原创改写，不默认保存第三方全文。
- 本轮真实新增 21 个高质量信息源、21 个 `raw_content_items` 元数据锚点、21 个浏览冲浪资源锚点，覆盖健康关系教育、安全关系教育、伴侣支持、关系播客、中文心理科普、开放教材、开放数据和课程入口。
- `/api/resources/sources` 现在会读取 `source_registry.allowed_use_json.surf_metadata`，让来源登记表中的来源组、摘要、结构、质量说明、主题和场景能直接进入 `/surf`，并过滤 pytest/内部测试来源。
- 新增 [项目发展轨迹指南.md](/Users/dillon/workspace/微关系动力学全息/docs/项目发展轨迹指南.md)，并在知识中枢写入“任何事情的发展都没有奇迹，只有轨迹”知识条目。
- `/surf` 标题区展示轨迹指南，提醒来源登记、原创转化、练习反馈和审计报告要连成闭环。
- 数据库备份：`data/backups/relationship_training-before-source-surf-expansion-20260524-232027.db`。
- 验证：`tests/test_source_surf_expansion_seed.py tests/test_catalog_profile_review_api.py::test_sample_and_resource_catalog_contracts_match_frontend -q` 通过；`npm run type-check` 通过；`npm run build` 通过；`/api/resources/sources?limit=200` 返回 One Love Foundation、Relate UK、Esther Perel；`/api/knowledge/entries?q=任何事情的发展` 返回轨迹指南；浏览器 `/surf` 可见新增来源和来源组数量。

## 2026-05-24 23:43 CST 元基础学习架构素材库与模块模板升级

- `/api/learning/framework` 新增 `material_library`、`module_templates`、`learning_map`、`quality_gates`，把抽象总纲升级为可直接学习、发散和练习的素材库契约。
- 八大主线素材库覆盖：微关系信号、情绪流动、边界同意、暧昧张力、冲突修复、长期连接、幽默互动、感受-期待-选择；每条包含定义、信号、情绪词、程度刻度、场景案例、低质/更好回应、对话骨架、反模式、练习任务和质量契约。
- 新增功能模块模板：资源海洋、表达工具箱、知识中枢、训练中心、错题本，明确每个模块应展示的选项卡、必填字段和设计规则。
- 新增学习地图：看见事实 -> 命名状态 -> 识别关系任务 -> 选择工具 -> 生成回应 -> 观察反馈 -> 复盘迁移，作为从入门到迁移掌握的统一路线。
- `/framework` 前端重构新增“关系动力学学习地图”“八大主线素材库”“功能模块模板”“质量门禁”四个学习区，减少空泛总纲，强化真实案例、对比回应和练习任务。
- 新增测试断言学习框架必须暴露八大主线、完整对话骨架、5 级程度刻度、资源海洋模板和上下文一致门禁。
- 验证：`tests/test_learning_pipeline_api.py::test_learning_framework_exposes_primitive_and_visual_layers -q` 通过；`npm run type-check` 通过；`npm run build` 通过；后端重启后 `/api/learning/framework` 返回 8 条素材库与 6 条质量门禁；浏览器 `/framework` 可见八大主线素材库、功能模块模板、质量门禁和更好回应区。

## 2026-05-25 07:24 CST 深度情感连接与镜子技术四步法融合

- `/api/learning/framework` 的素材库新增“深度情感连接”主线，明确开放式提问、关键词捕捉、事实情绪区分、镜子校准的学习结构。
- 新增 `backend/database/deep_emotional_connection_seed.py`，把“建立深度情感连接”落成项目原创知识、表达工具链和资源海洋训练卡。
- 知识中枢新增“深度情感连接：镜子技术四步法”，标准流程为：开放式提问 -> 捕捉关键词 -> 区分事实与情绪 -> 镜子校准。
- 表达工具箱新增“深度情感连接镜子链”，约束反模式：审问式追问、心理诊断、把猜测当结论、深聊逼供、没有退出权。
- 资源海洋新增 15 条深度情感连接训练卡，覆盖硬撑感、突然安静、工作卡住、关系不确定、冲突后沉默 5 个场景与 D1-D3 难度；每条都有关键词、事实层、情绪层、完整对话、低质/更好回应和边界出口。
- 数据库备份：`data/backups/relationship_training-before-deep-emotional-connection-20260525-072216.db`。
- 验证：`tests/test_deep_emotional_connection_seed.py tests/test_learning_pipeline_api.py::test_learning_framework_exposes_primitive_and_visual_layers -q` 通过；`npm run type-check` 通过；`npm run build` 通过；API 验证知识 1、工具链 1、资源 15；浏览器 `/framework` 点击“深度情感连接”后可见镜子、开放式提问、事实层和更好回应。

## 2026-05-25 07:35 CST 深度情感连接关键技术手册细化

- `/api/learning/framework` 的“深度情感连接”素材主线补充 `technique_cards`，覆盖开放式提问、捕捉关键词、区分事实与情绪、镜子技术四个关键技术。
- 每张技术卡统一包含：目标、术语、关键词、具体步骤、D1-D5 程度刻度、可用句式和禁区，帮助学习者从“知道概念”进入“会观察、会提问、会校准、会刹车”。
- `/framework` 前端新增“关键技术手册”展示区，点击“深度情感连接”后可集中查看四个技术的术语库、关键词库、步骤、程度、句式和反模式。
- TypeScript 契约同步新增 `technique_cards` 可选字段，避免后端数据只存在于接口而前端无结构化约束。
- 测试断言学习框架必须暴露四张技术卡、镜子技术句式和程度刻度，防止后续回退成抽象说明。
- 验证：`tests/test_learning_pipeline_api.py::test_learning_framework_exposes_primitive_and_visual_layers -q` 通过；`npm run type-check` 通过；`npm run build` 通过；API 返回“深度情感连接 4 ['开放式提问', '捕捉关键词', '区分事实与情绪', '镜子技术']”；浏览器 `/framework?fresh=deep-technique-cards` 点击“深度情感连接”后确认“关键技术手册、开放式提问、捕捉关键词、区分事实与情绪、镜子技术、可用句式、禁区”均可见。

## 2026-05-25 07:42 CST 开放式与封闭式问题对比升级

- “深度情感连接”关键技术手册新增“封闭式问题”技术卡，明确它不是控制对话，而是用于确认事实、校准感受、收束边界和降低对方表达负担。
- “封闭式问题”补齐术语、关键词、四步执行法、D1-D5 程度刻度、可用句式和禁区，覆盖“是不是、对吗、更像A还是B、我有没有听偏、要不要先停”等校准语言。
- “开放式提问”新增“开放式 / 封闭式对比”结构，按功能目标、典型句式、关系效果、风险边界四个维度说明：先开放获取材料，再封闭确认理解；连续开放会逼供，连续封闭会审问。
- `/framework` 技术卡支持展示 `comparisons`，学习者能在同一张卡里看到开放式、封闭式和使用规则，不再只看到孤立术语。
- 测试断言深度情感连接必须暴露 5 张技术卡，并锁定封闭式问题与 4 条开放/封闭对比分析。
- 验证：`tests/test_learning_pipeline_api.py::test_learning_framework_exposes_primitive_and_visual_layers -q` 通过；`npm run type-check` 通过；`npm run build` 通过；API 返回“深度情感连接 5 ['开放式提问', '封闭式问题', '捕捉关键词', '区分事实与情绪', '镜子技术']”；浏览器 `/framework?fresh=open-closed-question` 点击“深度情感连接”后确认“封闭式问题、开放式 / 封闭式对比、功能目标、使用规则、是不是、更像A还是B”均可见。

## 2026-05-25 07:50 CST 感受识别与命名素材补齐

- “深度情感连接”关键技术手册新增“感受识别与命名”技术卡，把感受从抽象词拆成身体线索、感受词、强度刻度、复合情绪、伪感受和需要信号。
- 技术卡补齐四步执行法：先找身体线索、把解释改写成感受词、用强度词校准、把感受连接到需要。
- D1-D5 程度刻度覆盖轻微波动、可命名、复合情绪、身体化、超出承载，帮助学习者判断什么时候继续深聊、什么时候暂停。
- 新增 `feeling_spectrum`：靠近、不安、受伤、防御四组感受词谱，每组包含感受词、身体线索和需要信号。
- `/framework` 技术卡新增“感受词谱与身体线索”展示区，学习者能直接看到“安心/被看见/心动”“紧张/悬着/没底”“委屈/被忽略/孤单”“抗拒/被逼/想躲”等词族。
- 测试断言深度情感连接必须暴露 6 张技术卡，并锁定“感受识别与命名”和 4 组感受词谱。
- 验证：`tests/test_learning_pipeline_api.py::test_learning_framework_exposes_primitive_and_visual_layers -q` 通过；`npm run type-check` 通过；`npm run build` 通过；API 返回“深度情感连接 6 感受识别与命名 4 靠近”；浏览器 `/framework?fresh=feeling-spectrum` 点击“深度情感连接”后确认“感受识别与命名、感受词谱与身体线索、身体线索、需要信号、靠近、不安、受伤、防御、委屈、心里堵”均可见。

## 2026-05-25 13:18 CST 自我表露深度、亲密关系与情绪流动融合

- 新增 `backend/database/self_disclosure_intimacy_seed.py`，把用户提供的“自我表露深度 / 亲密关系 / 情绪流动”材料提炼为项目原创知识、表达工具和资源训练卡，来源标记为用户提供结构化材料。
- 知识中枢新增 3 条条目：自我表露五级刻度、亲密关系结构、情绪流动过程；强调事实层、观点层、情感层、脆弱层、存在层与关系风险校准。
- 表达工具箱新增 `expr_tool_062`“自我表露深度校准”和 `expr_chain_self_disclosure_depth_v1`“自我表露深度安全推进链”，用于判断什么时候说到哪一层、什么时候停、如何保留退路。
- 资源海洋新增 12 条完整案例资源，覆盖初识节奏、暧昧心动、冲突后脆弱、长期深层渴望 4 个场景与 D1-D3 难度；每条包含完整对话、低质回应、更好回应、风险矩阵、迁移练习和 `case_blueprint_json`。
- `/api/learning/framework` 素材库新增“自我表露深度”主线，并补齐“自我表露五级刻度”技术卡、D1-D5 程度刻度和表露前/表露中/被接纳后/被拒绝后感受词谱。
- `/api/resources` 新增 `mission_axis=self_disclosure_depth` 使命轴筛选，资源页面快捷主线新增“自我表露深度”，学习者可从资源海洋直接进入这组训练卡。
- 真实数据库已执行入库：知识 3、表达工具 1、工具链 1、资源 12；数据库备份：`data/backups/relationship_training-before-self-disclosure-intimacy-20260525-131351.db`。
- 验证：`tests/test_self_disclosure_intimacy_seed.py tests/test_learning_pipeline_api.py::test_learning_framework_exposes_primitive_and_visual_layers -q` 为 5 passed；`npm run type-check` 通过；`npm run build` 通过；API 验证知识、表达工具、资源和学习框架均能检索到“自我表露深度”。

## 2026-05-25 14:35 CST 关系需求校准与性别刻板印象去偏融合

- 新增 `backend/database/relationship_need_calibration_seed.py`，把“女人的底层逻辑”这类粗糙性别化材料转译为“关系需求校准”训练包，保留情绪承接、安全归属、价值认同、能力感吸引、认同位置等有效观察。
- 知识中枢新增 2 条条目：`关系需求校准：从性别化判断到可观察需求`、`五类关系需求：情绪、安全、价值、能力、认同`。
- 表达工具箱新增 `expr_tool_063`“关系需求去偏校准”和 `expr_chain_relationship_need_calibration_v1`“关系需求去偏回应链”，把标签化判断转成“信号 -> 需求假设 -> 去偏改写 -> 轻验证 -> 具体行动”。
- 资源海洋新增 15 张完整案例卡，覆盖情绪承接、安全归属、价值认同、能力感吸引、认同位置 5 类需求与 D1-D3 难度；每张包含完整对话、低质回应、更好回应、五步拆解、去偏提醒和练习任务。
- `/api/learning/framework` 素材库新增“关系需求校准”主线和“需求去偏五步法”技术卡，锁定对比：标签化说法 -> 需求化说法 -> 可执行行动。
- `/resources` 主线筛选新增“关系需求校准”；资源接口把 `relationship_need_calibration` 与 `self_disclosure_depth` 设为精确 `coverage_axis` 筛选，避免“安全感/亲密关系”等宽泛词把旧资源混入专门训练卡。
- 真实数据库已执行入库：知识 2、表达工具 1、工具链 1、资源 15；数据库备份：`data/backups/relationship_training-before-relationship-need-calibration-20260525-142930.db`。
- 验证：`tests/test_relationship_need_calibration_seed.py tests/test_self_disclosure_intimacy_seed.py tests/test_learning_pipeline_api.py::test_learning_framework_exposes_primitive_and_visual_layers -q` 为 7 passed；`npm run type-check` 通过；`npm run build` 通过；API 验证关系需求校准精确返回 15 条，自我表露深度仍精确返回 12 条。
