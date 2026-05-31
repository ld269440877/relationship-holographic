# 验证报告

更新时间：2026-05-21

## 已执行命令

```bash
.venv/bin/python -m pytest tests/test_ai_provider_safety.py tests/test_analytics_api.py tests/test_training_flow.py -q
```

最新结果：56 passed。覆盖 Provider 诊断、成功契约、probe readiness、AI 伴侣成功/降级分支；新增断言确认 HTTP 403 被归类为 `auth_or_model_permission`，provider failure fallback 仍返回 `expression_chain`、`related_resources` 和 `mistake_memory`。

```bash
.venv/bin/python -m mypy backend/ai/provider_client.py backend/api/analytics.py backend/api/training.py --strict
```

结果：通过。

```bash
.venv/bin/python -m ruff check backend/ai/provider_client.py backend/api/analytics.py backend/api/training.py tests/test_ai_provider_safety.py tests/test_analytics_api.py tests/test_training_flow.py
```

结果：通过。

```bash
.venv/bin/python -m tools.commander regression-audit --batch-limit 2
```

最新结果：通过。Provider diagnostics 现在同时报告 `http_400` 与 `http_403`，failure playbook 输出 `account_or_service_http_400` 与 `auth_or_model_permission`，quality gate 包含 `auth_or_permission_error=true`。

```bash
cd frontend && npm run type-check && npm run build
```

结果：通过。

```bash
python3 -m json.tool docs/tasks/next_stage_backlog.json
```

结果：通过，`docs/tasks/next_stage_backlog.json` 可解析；共 13 项 pending，第一项为 `p0_ai_provider_success_and_fallback_quality`。

```bash
.venv/bin/python -m tools.commander regression-audit --dry-run --batch-limit 2
```

结果：通过，规划 database_health、weekly_evolution、import_quality、reviewed_publish_candidates、vector_recall、gold_interrater、gold_conflict_queue、ai_quality、ai_failure_analysis、ai_provider_diagnostics 十类检查。

```bash
.venv/bin/python -m tools.commander regression-audit --batch-limit 2
```

结果：通过。关键质量债：AI success_rate 34.2%、fallback_rate 65.8%、provider_failure_rate 43.3%、DeepSeek HTTP 400 共 38 次；import quality 75.0、active issues 88；reviewed publish candidates `publish_ready=0`；vector top10 recall 0.5。

```bash
cd frontend && npm run type-check
```

结果：通过。

```bash
cd frontend && npm run build
```

结果：通过。

```bash
cd frontend && npm run smoke:world
```

结果：通过，`checked=61`，报告写入 `frontend/output/smoke/report.json`。

```bash
.venv/bin/python -m pytest -q
```

结果：31 passed，后端覆盖率 67%。

最新结果：38 passed，后端覆盖率 69%。

最新结果：40 passed，后端覆盖率 70%。

最新结果：42 passed，后端覆盖率 71%。

最新结果：43 passed，后端覆盖率 72%。

最新结果：44 passed，后端覆盖率 72%。

最新结果：44 passed，后端覆盖率 73%。

最新结果：57 passed，后端覆盖率 75%。

最新结果：65 passed，后端产品覆盖率 83%。

最新结果：69 passed，后端产品覆盖率 84%。

最新结果：77 passed，后端产品覆盖率 84%。

最新结果：79 passed，后端产品覆盖率 84%。

最新结果：80 passed，后端产品覆盖率 86%。

```bash
.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py tests/test_learning_pipeline_api.py -q
```

最新结果：19 passed，覆盖 reviewed/published 资产治理、回填、进化流水线契约和批量流水线回归。

```bash
.venv/bin/python -m pytest tests/test_training_flow.py::test_gold_sample_expert_review_queue_summary_and_submission tests/test_training_flow.py::test_gold_interrater_consistency_reports_agreement_and_conflicts -q
```

最新结果：2 passed，覆盖 Gold Set 专家复核、跨审阅者一致性、评分差和冲突样本报告。

```bash
.venv/bin/python -m pytest tests/test_commander.py -q
```

最新结果：7 passed，覆盖 commander DAG、weekly evolution dry-run、regression-audit dry-run 和真实本地回归审计。

```bash
.venv/bin/python -m tools.commander regression-audit --batch-limit 2
```

结果：通过，输出 database_health、weekly_evolution、vector_recall、gold_interrater、ai_quality 五类审计检查。

```bash
.venv/bin/python -m pytest tests/test_analytics_api.py -q
```

最新结果：3 passed，覆盖 AI 质量报表、AI 失败根因聚类和跨会话趋势。

```bash
.venv/bin/python -m mypy backend/api/analytics.py --strict
```

结果：通过。

```bash
cd frontend && npm run type-check
```

结果：通过。

```bash
cd frontend && npm run build
```

结果：通过，生成 `frontend/dist/`。

```bash
cd frontend && npm run smoke:world
```

结果：通过，16 项浏览器关键路径检查通过，报告写入 `frontend/output/smoke/report.json`。

```bash
.venv/bin/python -m ruff check backend/api/evolution.py backend/api/learning.py backend/database/seed.py tests/test_learning_pipeline_api.py
```

结果：通过。

```bash
.venv/bin/python -m ruff check backend/database/schema_guard.py backend/database/connection.py backend/api/database.py tests/test_database_schema_guard.py tests/test_content_import_database.py
```

结果：通过。

```bash
.venv/bin/python -m mypy backend/database/schema_guard.py backend/database/connection.py backend/api/database.py
```

结果：通过。

```bash
.venv/bin/python -m ruff check backend/api/training.py backend/core/emotion_engine.py backend/core/comparison_engine.py tests/test_training_flow.py
```

结果：通过。

```bash
.venv/bin/python -m mypy backend/core/emotion_engine.py backend/core/comparison_engine.py backend/api/training.py
```

结果：通过。

```bash
.venv/bin/python -m ruff check backend/models/training.py backend/models/__init__.py backend/database/schema_guard.py backend/api/training.py tests/test_training_flow.py
```

结果：通过。

```bash
.venv/bin/python -m mypy backend/models/training.py backend/api/training.py
```

结果：通过。

```bash
.venv/bin/python -m ruff check backend/api/evolution.py tests/test_evolution_api.py tests/test_learning_pipeline_api.py
```

结果：通过。

```bash
.venv/bin/python -m ruff check backend/api/evolution.py backend/database/import_json_content.py backend/database/import_knowledge_content.py backend/database/seed.py backend/models/knowledge.py backend/models/resource.py tests/test_catalog_profile_review_api.py
```

结果：通过。

```bash
.venv/bin/python -m pytest tests/test_evolution_api.py tests/test_learning_pipeline_api.py -q
```

结果：10 passed。

```bash
.venv/bin/python -m ruff check backend/api/training.py tests/test_training_flow.py
```

结果：通过。

```bash
.venv/bin/python -m mypy backend/models/training.py backend/api/training.py
```

结果：通过。

```bash
.venv/bin/python -m pytest tests/test_training_flow.py -q
```

结果：8 passed。

```bash
.venv/bin/python - <<'PY'
from backend.database.connection import create_db_and_tables, engine
from backend.database.schema_guard import audit_schema
create_db_and_tables()
print(audit_schema(engine))
PY
```

结果：真实数据库 `status=ok`，`foreign_keys=True`，`integrity_check=ok`，缺表/缺列为空，关键 JSON 字段无坏值。

```bash
VITE_API_PROXY_TARGET=http://127.0.0.1:8011 npm run dev -- --host 127.0.0.1 --port 5174
```

结果：浏览器 smoke 通过。完成引导后访问 `/framework` 与 `/evolution`，页面均能加载后端真实数据。

## 本轮新增验收点

- `GET /api/learning/framework` 返回元基础粒度阶梯、分类树、5W2H、数图组件、三性三管理和掌握阶段。
- `GET /api/evolution/pipeline` 返回来源登记、候选元数据、标注任务、训练资产版本、状态计数和下一步动作。
- `/framework` 前端页面可构建进生产包。
- `/evolution` 前端页面显示元数据流水线指标。
- FastAPI 主应用已注册学习框架和进化流水线路由。
- 引导完成状态增加 localStorage/sessionStorage/cookie/内存多级兜底；画像 API 保存失败不会阻断进入本地训练模式。
- Vite API 代理支持 `VITE_API_PROXY_TARGET`，可避开旧后端进程或多端口开发场景。
- `POST /api/evolution/pipeline/advance` 可推进流水线状态并写入 `PipelineRunLog`。
- 样本与资源列表 API 与前端契约对齐，返回 `{items,total}`；静态路由优先级已修复。
- 每日复盘 API 正确解析 `review_date` 为日期对象，避免 SQLite date 写入错误。
- `GET /api/training/visual-map/{sample_id}` 可把训练样本派生为数图结合训练地图：信号高亮、情绪温度计、情绪流、需求雷达、边界色带、互动回路、5W2H 与轻验证问题。
- `GET /api/training/next` 随题返回 `visual_map`，训练中心可直接渲染多维感知图解。
- `/trainer` 浏览器 smoke 通过：页面加载真实样本图解，提交回应后出现综合得分与理想回应。
- 核心引擎测试覆盖情绪识别、强度标签、混合情绪、对比评分、差异报告和问题归因。
- `POST /api/evolution/pipeline/advance` 已从单纯状态推进升级为单项自动处理器：`sanitize` 风险降级，`dedupe` 重复检查，`annotate` 生成标注任务，`annotation_job.publish` 生成训练资产版本。
- 流水线处理器测试覆盖 raw -> annotation -> asset version 自动链路。
- `POST /api/training/compare` 返回 `metacognitive_review`，覆盖事实/解释分离、三假设、轻验证问题、下一步最小行动和复盘问题。
- 安全阻断反馈同样返回元认知复盘，引导用户转向非控制、尊重边界的表达。
- `POST /api/training/partner/simulate` 支持 AI 训练伴侣安全模拟：配置 DeepSeek 时走 `AIOrchestrator`，未配置/失败时规则降级，PUA/操控输入硬阻断。
- `TrainerAI` 前端已调用后端安全模拟接口，并显示评分来源和训练建议。
- 数据库启动链路已从 `create_all` 升级为 `create_all + schema_guard`，解决旧 SQLite 表不会自动补列的问题。
- `GET /api/database/health` 已覆盖 schema、完整性、外键、关键表行数和 JSON 字段质量。
- `POST /api/database/migrate` 已作为完整幂等入口执行建表、补列和审计。
- 数据库专项测试覆盖旧表补列、缺 JSON 列诊断、坏 JSON 标红、真实库审计、导入幂等和缺文件安全跳过。
- `POST /api/evolution/pipeline/run-batch` 支持批量数据生命体闭环：dry-run、定向候选、sanitize、hash+标题语义去重、annotate、publish、报告生成。
- 批量流水线测试覆盖完整发布链路和疑似重复候选跳过策略。
- 样本表已增加多粒度标注字段，历史样本可通过 `POST /api/samples/annotations/backfill` 回填为关系动力学标本。
- `GET /api/samples/{sample_id}/annotation-map` 返回持久化优先的多粒度训练地图。
- 数据库健康检查纳入样本多粒度 JSON 字段质量。
- `POST /api/training/compare` 返回 mastery 与 error_attribution，训练反馈从单次评分升级为掌握阶段和错误归因。
- `GET /api/training/radar` 返回整体 mastery，可用于前端展示“知道、辨认、操作、迁移、自然”的阶段。
- `POST /api/training/partner/simulate` 返回 `relationship_state`：信任、压力、边界压力、边界安全、连接、状态标签、下一焦点和本轮 delta。
- AI 伴侣状态机按安全型、焦虑型、回避型、恐惧-回避型建立不同基线；共情、确认、给空间、追问、施压、轻视等输入会推动状态变化。
- `TrainerAI` 前端展示状态标签、四维状态条和下一焦点，训练者能同时沉浸对话并置身其外观察关系动力。
- 训练核心链路 `training.py`、`emotion_engine.py`、`comparison_engine.py` 已通过 ruff 和 mypy strict。
- 新增 `practice_sessions` 与 `practice_events`，AI 伴侣模拟每轮写入会话、事件、评分、建议、安全信息和关系状态 JSON。
- `TrainerAI` 前端保存并传递后端返回的 `session_id`，多轮对话会持续写入同一会话。
- 数据库健康检查纳入 `practice_sessions`、`practice_events` 行数和 JSON 字段质量；真实库审计结果为 `status=ok`。
- `GET /api/evolution/pipeline` 与 `GET /api/evolution/summary` 返回 `visual_metrics`：来源质量矩阵、候选审核发布漏斗、安全风险趋势、系统学习增量。
- `/evolution` 浏览器 smoke 通过：生命体数图指标、候选审核发布漏斗、来源质量矩阵均可见，无前端运行时错误。
- `GET /api/training/partner/sessions/{session_id}/review` 返回 AI 伴侣会话复盘：状态曲线、状态 delta、关键转折、错误归因和下一练习。
- `TrainerAI` 浏览器 smoke 通过：真实会话请求后显示会话状态曲线、下一练习、状态标签和曲线图例，无前端运行时错误。
- `GET /api/knowledge/visual-map` 返回知识图解视图：概念图谱、分类树、5W2H 卡片、工具适用地图和覆盖率。
- `/knowledge` 浏览器 smoke 通过：知识数图驾驶舱、概念图谱、分类树、5W2H 元问题卡和工具适用地图均可见。
- `mistake_log` 新增结构化归因字段并纳入 schema guard JSON 审计，真实库审计显示新增 JSON 字段 invalid=0。
- `/mistakes` 浏览器 smoke 通过：结构化错误归因、复习焦点、能力维度和修复动作均可见。
- `docs/tasks/module_dag.json` 可被解析，`tools.commander` 能选择下一项任务并输出验证命令。
- `.venv/bin/python -m tools.commander run-next --dry-run` 通过，当前下一项为 `ai_provider_quality`。
- `tests/test_commander.py` 已改为使用临时 DAG 验证选择算法，真实 DAG 全完成或新增任务时不再造成陈旧断言。
- `tests/test_ai_provider_safety.py` 覆盖 DeepSeek OpenAI-compatible/native 成功、HTTP 失败、超时、非法响应体、非 JSON 内容、安全拒绝和 `safety_events` 落库。
- `POST /api/evolution/scheduler/run-weekly` 可生成周期性调度报告；测试覆盖 dry-run 与真实生成报告。
- `GET /api/evolution/dedupe/report` 可输出 hash 精确重复与标题 token 语义近邻重复簇。
- `GET /api/evolution/import-quality` 可输出样本、资源、知识条目的字段完整度、JSON 质量、导入批次和问题摘要。
- `GET /api/evolution/safety-events` 可输出安全硬阻断审计事件。
- `/evolution` 前端调度驾驶舱已接入新增 API，`npm run type-check && npm run build` 通过。
- 浏览器 smoke：`http://127.0.0.1:5178/evolution` 可见“本地指挥官调度驾驶舱 / 重复候选簇 / 导入质量结构 / 安全事件 / 运行周调度”；点击“运行周调度”后显示“调度后的下一动作”和新的动态进化调度报告，当前页面无 127.0.0.1:5178 控制台错误。
- 真实数据库审计：`status=ok`，缺表/缺列为空，`safety_events.flags_json` 与 `safety_events.alternatives_json` invalid=0。
- `.venv/bin/python -m tools.commander run-next --dry-run` 通过，当前下一项为 `quality_gate_80`。
- `quality_gate_80` 已完成：`.venv/bin/python -m pytest -q` 为 65 passed，产品覆盖率 83%；`backend/api/training.py` 相关 ruff 通过；训练核心 mypy strict 通过；前端 `npm run type-check && npm run build` 通过。
- 覆盖率口径已分层：`backend/database/expand_data.py` 与 `backend/database/expand_data_v2.py` 是离线海量数据扩展/生成脚本，不属于运行时产品链路，已从 coverage run omit 中排除；活动后端产品代码没有被隐藏。
- 新增训练边界测试覆盖：情绪识别无结果与多情绪路径、错题复习正确/错误间隔、到期错题优先推荐、AI 伴侣编排成功/失败/缺 reply 降级、会话复盘空状态/坏 JSON 状态降级、不同依恋状态焦点。
- `evolution_type_debt` 第一阶段完成：新增 `backend/core/evolution_intelligence.py`，严格类型承接去重报告、安全事件报告、调度下一动作、JSON helper 与语义 token；`tests/test_evolution_intelligence.py` 覆盖 typed core 与旧 helper 兼容层。
- 已执行：`mypy backend/core/evolution_intelligence.py backend/ai/provider_client.py backend/ai/orchestrator.py backend/ai/safety.py backend/ai/schemas.py --strict` 通过；`ruff check backend/core/evolution_intelligence.py backend/api/evolution.py tests/test_evolution_intelligence.py tests/test_learning_pipeline_api.py` 通过；进化专项 17 passed。
- 知识库测试修复：共享 SQLite 数据增长后，`list_entries()` 默认分页不保证包含刚导入的唯一条目；测试改为按唯一 section/title 查询，避免顺序偶然性。
- 课程图谱与进化专项回归：`.venv/bin/python -m pytest tests/test_training_flow.py tests/test_learning_pipeline_api.py tests/test_evolution_intelligence.py tests/test_evolution_api.py -q` 通过，32 passed。
- `RawDedupeCandidate` 兼容旧调用顺序并保留 `url` 元数据；`_raw_dedupe_candidate()` 已同步传入 URL，周调度和 dedupe report 不再因 typed core 字段漂移失败。
- `POST /api/evolution/sources/fetch` 已补齐合规来源抓取入口：dry-run 可预览，非 dry-run 只生成 metadata-only raw candidate；测试使用 mock HTTP 确认不保存第三方全文。
- 本地元数据向量签名测试通过：`metadata_vector_similarity()` 能稳定区分相近关系标题与无关工程标题，为 sqlite-vec 替换留下接口。
- 前端验收：`cd frontend && npm run type-check && npm run build` 通过。
- 下一支柱专项门禁已预跑：`.venv/bin/python -m pytest tests/test_database_schema_guard.py tests/test_content_import_database.py -q` 通过，7 passed；运行时数据库链路 ruff 通过。
- `docs/tasks/module_dag.json` 已通过 JSON 解析；`.venv/bin/python -m tools.commander run-next --dry-run` 当前返回 `formal_migration_and_content_sources`。
- 正式迁移与历史内容归档完成：`content_sources` 审计、schema revision plan、导入状态审计均纳入数据库健康报告；相关数据库专项测试通过。
- 样本版本与 Gold Set 校准完成：`SampleAnnotationVersion`、金样本脚手架和训练金标校准路径通过专项测试。
- 训练差异报告与掌握推荐器完成：结构化 diff、推荐上下文和情绪识别训练入库通过专项测试。
- 自动调度与指挥官循环完成：`.venv/bin/python -m tools.commander sync-state` 已写入 `docs/tasks/commander_state.json`；`weekly-evolution --dry-run --batch-limit 3` 通过。
- 前端世界级 smoke 完成：新增 `npm run smoke:world`，Playwright 覆盖 Dashboard、Trainer、TrainerAI、Path、Mistakes、Knowledge、Evolution、Framework 的桌面/移动双视口，无运行时错误、水平溢出或可见重叠。
- `docs/tasks/module_dag.json` 已切换：`frontend_world_class_smoke` 标记完成；`.venv/bin/python -m tools.commander run-next --dry-run` 当前返回 `ai_prompt_versioning_and_run_logging`。
- AI 提示版本与运行审计完成：新增 `AIPromptVersion` / `AIRunLog`，运行日志只保存 payload hash、字段摘要和响应摘要，不保存敏感原文；安全阻断会关联 `SafetyEvent`。
- AI 专项门禁通过：`.venv/bin/python -m pytest tests/test_ai_provider_safety.py tests/test_training_flow.py -q` 为 31 passed；`.venv/bin/python -m mypy backend/ai backend/core --strict` 通过；相关 ruff 通过。
- `docs/tasks/module_dag.json` 已切换：`ai_prompt_versioning_and_run_logging` 标记完成；下一项为 `world_class_release_gate`。
- 最终总体验收通过：`.venv/bin/python -m pytest -q` 为 80 passed，产品覆盖率 86%；`.venv/bin/python -m ruff check backend tests tools` 通过；前端 `npm run type-check && npm run build && npm run smoke:world` 通过。
- 新增 `tests/test_seed_data.py`，让种子数据初始化脚手架在空库中真实执行并验证幂等，覆盖率从 84% 提升到 86%。
- 新增 `docs/世界级总体验收报告.md`，明确能力、门禁、已知限制和下一轮进化循环。
- `docs/tasks/module_dag.json` 已切换：19/19 支柱全部 completed。
- V2 强化完成：新增 `GET /api/analytics/ai-quality`，按 `AIRunLog` 聚合成功率、降级率、安全阻断率、Provider 失败率、延迟、任务/Provider 分布、flags、趋势和下一动作，不返回敏感原文。
- V2 强化完成：新增 `GET /api/analytics/relationship-trends`，按 `PracticeSession` / `PracticeEvent` 聚合修复指数、状态增量、依恋分布、焦点分布、会话趋势和下一动作。
- Dashboard 已接入 AI 质量哨站与跨会话关系趋势；`npm run smoke:world` 重新通过，16 项关键路径无运行时错误、水平溢出或可见重叠。
- 新增 `tests/test_analytics_api.py`；`.venv/bin/python -m pytest -q` 为 82 passed，产品覆盖率 86%。
- Analytics 专项门禁通过：`.venv/bin/python -m pytest tests/test_analytics_api.py tests/test_ai_provider_safety.py tests/test_training_flow.py -q` 为 33 passed；`.venv/bin/python -m mypy backend/api/analytics.py --strict` 通过；相关 ruff 通过。
- `docs/tasks/module_dag.json` 已扩展：`ai_quality_and_relationship_trends` 标记 completed，当前 20/20 支柱全部 completed。
- Gold Set 专家复核闭环完成：`GET /api/samples/gold/summary` 输出覆盖率、信心、待复核、严格校准门禁和下一动作；`GET /api/samples/gold/review-queue` 输出按风险/难度/缺专家版本排序的复核队列；`POST /api/samples/gold/reviews` 新增专家复核版本并同步评分校准 gold label。
- Dashboard 已接入 Gold Set 校准台，展示 Gold 样本、专家复核、待复核、覆盖率、平均信心、复核队列和下一动作。
- Gold Set 专项门禁通过：`.venv/bin/python -m pytest tests/test_training_flow.py tests/test_catalog_profile_review_api.py -q` 为 20 passed；相关 ruff 通过。
- 全量门禁通过：`.venv/bin/python -m pytest -q` 为 83 passed，产品覆盖率 86%；前端 `npm run type-check && npm run build && npm run smoke:world` 通过。
- `docs/tasks/module_dag.json` 已扩展：`gold_set_expert_review_loop` 标记 completed，当前 21/21 支柱全部 completed。
- 正式迁移运行器完成：新增 `backend/database/migration_runner.py`，支持 migration plan、dry-run、真实 apply、SQLite 文件备份、`formal_migration_runs` 记录和健康报告 `formal_migration_status`。
- 数据库 API 新增 `GET /api/database/migration-plan` 与 `POST /api/database/migration-run`；默认 dry-run 不写入，真实执行会记录 applied revision 并可创建备份。
- 数据库专项门禁通过：`.venv/bin/python -m pytest tests/test_database_schema_guard.py -q` 为 8 passed；`mypy backend/database/migration_runner.py backend/database/schema_guard.py backend/api/database.py --strict` 通过；相关 ruff 通过。
- 全量门禁通过：`.venv/bin/python -m pytest -q` 为 85 passed，产品覆盖率 86%；前端 `npm run type-check && npm run build && npm run smoke:world` 通过。
- `docs/tasks/module_dag.json` 已扩展：`formal_migration_runner_and_backup_audit` 标记 completed，当前 22/22 支柱全部 completed。
- 持久化元数据向量索引完成：新增 `metadata_vector_index` 表、重建/搜索/报告核心和 Evolution API，当前不保存第三方全文，只保存 hash、元数据摘要和本地向量签名。
- 向量索引专项门禁通过：`.venv/bin/python -m pytest tests/test_vector_index.py tests/test_database_schema_guard.py -q` 为 10 passed；`.venv/bin/python -m mypy backend/core/vector_index.py --strict` 通过；相关 ruff 通过。
- 全量门禁通过：`.venv/bin/python -m pytest -q` 为 87 passed，产品覆盖率 86%。
- 真实数据库审计：`status=ok`，`quick_check=ok`，缺表/缺列为空，`metadata_vector_index` 行数为 1196，`metadata_vector_index.vector_json` invalid=0。
- `docs/tasks/module_dag.json` 已扩展：`persistent_metadata_vector_index` 标记 completed，当前 23/23 支柱全部 completed。
- sqlite-vec 原生 ANN 后端完成：`sqlite-vec>=0.1.9` 已加入依赖；向量重建会同步 `metadata_vector_index_vec` vec0 虚拟表，搜索优先走 sqlite-vec KNN，并在响应中暴露 `backend=sqlite_vec`、version、行数和 fallback 原因。
- schema guard 已跳过 sqlite-vec 虚拟表影子表的普通列审计，并新增 `vector_backend_status`，保持 `quick_check=ok` 与 JSON 审计稳定。
- Gold Set 队列稳定性修复：待复核队列按最近更新优先并扩大候选窗口，避免共享库里已批准样本过多导致新样本被漏检。
- sqlite-vec 专项门禁通过：`.venv/bin/python -m pytest tests/test_vector_index.py tests/test_database_schema_guard.py tests/test_training_flow.py::test_gold_sample_expert_review_queue_summary_and_submission -q` 为 11 passed；`mypy backend/core/vector_index.py backend/database/schema_guard.py --strict` 通过；相关 ruff 通过。
- 全量门禁通过：`.venv/bin/python -m pytest -q` 为 87 passed，产品覆盖率 86%；前端 `npm run type-check && npm run build && npm run smoke:world` 通过。
- `docs/tasks/module_dag.json` 已扩展：`sqlite_vec_ann_backend` 标记 completed，当前 24/24 支柱全部 completed。
- ANN 召回评测与阈值校准完成：`POST /api/evolution/vector-index/evaluate` 可输出 top-k recall、MRR、阈值命中率、per-type 弱点和推荐阈值，并对共享数据库中的近重复 `text_hash` 作等价命中处理。
- `docs/tasks/module_dag.json` 已扩展：`ann_recall_evaluation_and_threshold_calibration` 标记 completed，当前 25/25 支柱全部 completed。
- 导入质量修复计划完成：`GET /api/evolution/import-quality` 返回 `repair_plan`，`POST /api/evolution/import-quality/repair-plan` 支持 dry-run 与 apply，修复样本 provenance、资源 scene/format hint、知识 source metadata，并通过 `repair_source` 留痕。
- 导入质量专项门禁通过：`.venv/bin/python -m pytest tests/test_learning_pipeline_api.py::test_import_quality_and_safety_reports_are_auditable tests/test_learning_pipeline_api.py::test_import_quality_repair_plan_dry_run_and_apply -q` 为 2 passed；`.venv/bin/python -m ruff check backend/api/evolution.py tests/test_learning_pipeline_api.py` 通过。
- 导入质量回归审计完成：`tools.commander regression-audit` 新增 `import_quality` 检查，当前输出 `quality_score=75.0`、`issue_count=85`、`quality_debt.auto_repairable_fields=0`、`quality_debt.manual_review_issues=85`。
- 共享 SQLite 安全回填已执行：样本 43、资源 69、知识 1 条元数据被补全；repair plan 清零，剩余债务转为来源/历史 issue 复核。
- 导入质量债务分层专项通过：`.venv/bin/python -m pytest tests/test_learning_pipeline_api.py::test_import_quality_and_safety_reports_are_auditable tests/test_learning_pipeline_api.py::test_import_quality_repair_plan_dry_run_and_apply tests/test_commander.py -q` 为 9 passed；相关 ruff 通过；`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过。
- AI Provider 配置诊断完成：`GET /api/analytics/ai-provider-diagnostics` 输出脱敏 provider 配置、失败率、HTTP status 分布、风险等级、诊断项和下一动作，并避免泄露 API key、URL query secret、payload marker、raw payload 或响应全文。
- AI Provider 诊断已纳入回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 输出 `ai_provider_diagnostics`，真实库当前风险等级 high，HTTP 400 为高频失败模式。
- Analytics/Commander 专项通过：`.venv/bin/python -m pytest tests/test_analytics_api.py tests/test_commander.py -q` 为 11 passed；`.venv/bin/python -m mypy backend/api/analytics.py --strict` 通过；相关 ruff 通过。
- Gold Set 冲突复核队列完成：`GET /api/samples/gold/conflict-queue` 输出开放冲突、决策分歧、分数差、信心差、最新审阅版本、复议优先级和 consensus reviewer 建议。
- Gold 冲突队列已纳入回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 输出 `gold_conflict_queue`，真实库当前开放冲突 10 个，严格校准门禁为 false。
- Gold/Commander/Vector 稳定性专项通过：`.venv/bin/python -m pytest tests/test_training_flow.py::test_gold_interrater_consistency_reports_agreement_and_conflicts tests/test_commander.py tests/test_vector_index.py::test_metadata_vector_index_rebuild_search_and_audit -q` 通过；相关 ruff 通过。
- Reviewed 发布候选队列完成：`GET /api/evolution/reviewed-assets/publish-candidates` 输出 reviewed 资源/知识候选、质量信号、优先级理由、publish_ready 和人工确认门禁。
- 发布候选队列已纳入回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 输出 `reviewed_publish_candidates`，真实库当前 `publish_ready=19`，但仍要求人工确认。
- 发布候选专项通过：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_reviewed_asset_publish_candidates_are_auditable tests/test_commander.py -q` 通过；相关 ruff 通过。
- 全量后端门禁通过：`.venv/bin/python -m pytest -q` 为 96 passed，产品覆盖率 86%。
- `docs/tasks/module_dag.json` 已扩展：`import_quality_repair_plan`、`import_quality_regression_audit`、`ai_provider_diagnostics_gate`、`gold_conflict_queue_and_audit` 与 `reviewed_publish_candidate_gate` 标记 completed，当前 34/34 支柱全部 completed。

## 剩余风险

- 2026-05-21 22:22 CST 最新验证：
- Gold Set 共识关闭：`.venv/bin/python -m tools.commander resolve-gold-conflicts --apply --limit 100` 成功，新增 13 条 `consensus_review` 版本；开放冲突 13 -> 0，resolved conflict samples 19 -> 20，多审门禁通过。
- Gold/Commander 专项：`.venv/bin/python -m pytest tests/test_commander.py tests/test_training_flow.py::test_gold_interrater_consistency_reports_agreement_and_conflicts -q` 通过；相关 ruff 通过。
- AI Provider 硬化专项：`.venv/bin/python -m pytest tests/test_analytics_api.py tests/test_ai_provider_safety.py tests/test_commander.py -q` 为 30 passed；`.venv/bin/python -m mypy backend/api/analytics.py backend/ai/provider_client.py --strict` 通过；相关 ruff 通过。
- 前端门禁：`cd frontend && npm run type-check && npm run build` 通过。
- 全量后端门禁：`.venv/bin/python -m pytest -q` 为 99 passed，产品覆盖率 87%。
- 最新 commander regression-audit：整体 passed；数据库 `status=ok`、`integrity_check=ok`、缺表/缺列为空；vector backend `sqlite_vec`，top10 recall 1.0；Gold open conflicts 0；import quality score 75.0 且 auto-repairable 0。
- 当前仍需关注：AI Provider recent success_rate 18.3%、provider_failure_rate 42.5%、HTTP 400 31 次，配置形态已通过 compatibility，但外部账号能力/请求 schema/历史日志风险尚未解除；导入质量仍有 98 条历史 manual review issue；reviewed publish candidates 19 条仍需人工确认闭环。
- 2026-05-21 22:31 CST Reviewed 发布操作闭环验证：
- 发布治理专项：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_reviewed_asset_publish_candidates_are_auditable tests/test_catalog_profile_review_api.py::test_reviewed_asset_action_confirm_withdraw_and_request_review_are_audited tests/test_commander.py -q` 为 10 passed。
- 发布治理 ruff：`.venv/bin/python -m ruff check backend/api/evolution.py tests/test_catalog_profile_review_api.py` 通过。
- 前端门禁：`cd frontend && npm run type-check && npm run build` 通过。
- 全量后端门禁：`.venv/bin/python -m pytest -q` 为 100 passed，产品覆盖率 86%。
- 新增能力验证：`confirm_publish` 只允许 reviewed 且 publish_ready 的资产进入 published；重复发布返回 409；`withdraw` 从 published 回到 reviewed 并清空 `published_at`；`request_review` 把 reviewed 资产退回 draft；所有状态变化写入 `pipeline_run_logs`。
- 2026-05-21 22:44 CST 生产调度入口验证：
- APScheduler 调度专项：`.venv/bin/python -m pytest tests/test_commander.py -q` 为 10 passed。
- 调度 ruff：`.venv/bin/python -m ruff check backend/core/production_scheduler.py tools/commander.py tests/test_commander.py` 通过。
- 调度 strict mypy：`.venv/bin/python -m mypy backend/core/production_scheduler.py --strict --follow-imports=skip` 通过。
- 调度命令：`.venv/bin/python -m tools.commander scheduler-plan` 通过；`.venv/bin/python -m tools.commander scheduler-run-once weekly_evolution_dry_run --dry-run --batch-limit 2` 通过；`.venv/bin/python -m tools.commander scheduler-run-once regression_audit_daily --dry-run --batch-limit 2` 通过。
- 调度审计：`docs/tasks/production_scheduler_state.json` 已写入 run-once 快照，记录 job、ran_at、dry_run、batch_limit、result_status 和 result_summary。
- 全量后端门禁：`.venv/bin/python -m pytest -q` 为 102 passed，产品覆盖率 86%。
- 前端门禁：`cd frontend && npm run type-check && npm run build` 通过。
- 最新 regression-audit：整体 passed；Gold open conflicts 0；vector recall 1.0；Provider 配置形态通过但近期 HTTP 400 仍 high risk。
- 导入质量跟进：测试新增数据造成 `auto_repairable_fields=10` 后已再次安全回补，补全样本 2、资源 2、知识 1，回到 `auto_repairable_fields=0`；剩余 100 条为人工/来源复核 issue。
- 2026-05-21 23:03 CST 独立分析中心验证：
- 后端分析中心专项：`.venv/bin/python -m pytest tests/test_analytics_api.py -q` 为 6 passed。
- 后端分析中心类型与规范：`.venv/bin/python -m mypy backend/api/analytics.py --strict` 通过；`.venv/bin/python -m ruff check backend/api/analytics.py tests/test_analytics_api.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成 `Analytics-*.js` chunk。
- 浏览器验证：`http://127.0.0.1:5173/analytics` 标题为“分析中心 - 关系动力学全息”，可见“系统质量与历史趋势”“告警队列”和 scorecard，控制台 error 为空。
- 全量后端门禁：`.venv/bin/python -m pytest -q` 为 103 passed，产品覆盖率 86%。
- 新增能力验证：`GET /api/analytics/center` 聚合 AI 质量、Provider 诊断、Gold Set、导入质量、向量召回和训练趋势；测试确认不会泄露 payload/private marker。
- 2026-05-21 23:10 CST Reviewed 发布治理前端验证：
- 后端发布治理专项：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_reviewed_asset_publish_candidates_are_auditable tests/test_catalog_profile_review_api.py::test_reviewed_asset_action_confirm_withdraw_and_request_review_are_audited -q` 为 2 passed。
- 发布治理 ruff：`.venv/bin/python -m ruff check backend/api/evolution.py tests/test_catalog_profile_review_api.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成 `Governance-*.js` chunk。
- 浏览器验证：`http://127.0.0.1:5173/governance` 标题为“发布治理 - 关系动力学全息”，可见“Reviewed 资产发布操作台”“发布候选”和 Dry-run/发布预演控件，控制台 error 为空。
- 新增能力验证：`/governance` 不直接发布 reviewed 资产，必须先选择候选并可 dry-run 预演；真实执行仍通过后端 `reviewed-assets/action` 写入 SQLite 状态和 `pipeline_run_logs` 审计。
- 2026-05-21 23:15 CST migration 具体 revision 验证：
- 数据库专项：`.venv/bin/python -m pytest tests/test_database_schema_guard.py -q` 为 8 passed。
- 向量+迁移组合专项：`.venv/bin/python -m pytest tests/test_vector_index.py tests/test_database_schema_guard.py -q` 为 10 passed。
- migration runner 类型与规范：`.venv/bin/python -m mypy backend/database/migration_runner.py --strict --follow-imports=skip` 通过；`.venv/bin/python -m ruff check backend/database/migration_runner.py tests/test_database_schema_guard.py` 通过。
- 真实库 migration dry-run：pending revisions 为 `2026_05_21_formal_runner_v1` 与 `2026_05_21_metadata_vector_index_rebuild_v1`；dry-run 只报告 would_run，不写迁移记录。
- 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；导入质量因测试数据新增出现 16 个 auto repair 字段，已执行安全 metadata repair 后清零。
- 导入质量修复结果：补全样本 3、资源 3、知识 2；quality score 回到 75.0，`auto_repairable_fields=0`，剩余 100 条为历史 manual/source review issue。
- 2026-05-22 07:03 CST AI Provider 请求形态诊断验证：
- Provider/Analytics 专项：`.venv/bin/python -m pytest tests/test_ai_provider_safety.py tests/test_analytics_api.py -q` 为 25 passed。
- Commander/Provider/Analytics 组合专项：`.venv/bin/python -m pytest tests/test_commander.py tests/test_ai_provider_safety.py tests/test_analytics_api.py -q` 为 35 passed。
- 类型与规范：`.venv/bin/python -m mypy backend/ai/provider_client.py backend/api/analytics.py --strict` 通过；相关 ruff 通过。
- 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过，`ai_provider_diagnostics` 现在包含 request_shape。
- 真实诊断样例：`request_shape.url=https://api.deepseek.com/chat/completions`，`mode=openai`，`model=deepseek-v4-pro`，`payload_keys=["messages","model","temperature"]`，`message_roles=["system","user"]`，`compatibility_risks=[]`。
- 风险结论：当前 HTTP 400 不再优先归因为本地 endpoint/path/model/request schema 形态错误；下一步应做外部凭证可用性、模型授权、账号区域和真实最小请求探针验证。
- 2026-05-22 07:13 CST AI Provider 最小探针审计验证：
- AI/Analytics/DB 专项：`.venv/bin/python -m pytest tests/test_ai_provider_safety.py tests/test_analytics_api.py tests/test_database_schema_guard.py -q` 为 36 passed。
- Commander/Provider/Analytics/DB 组合专项：`.venv/bin/python -m pytest tests/test_commander.py tests/test_ai_provider_safety.py tests/test_analytics_api.py tests/test_database_schema_guard.py -q` 为 46 passed。
- 类型与规范：`.venv/bin/python -m mypy backend/ai/provider_client.py backend/api/analytics.py backend/models/ai.py --strict` 通过；相关 ruff 通过。
- 真实 dry-run 探针：`POST /api/analytics/ai-provider-probe?dry_run=true` 返回 `outcome=planned` 并写入 `ai_provider_probe_logs`；没有外部调用，没有 prompt 原文、API key、URL query secret 或响应全文。
- schema guard：数据库健康 row_counts 已纳入 `ai_provider_probe_logs`，JSON 质量纳入 `ai_provider_probe_logs.request_shape_json`。
- 2026-05-22 07:23 CST 历史导入 issue 治理验证：
- 学习流水线/数据库专项：`.venv/bin/python -m pytest tests/test_learning_pipeline_api.py tests/test_database_schema_guard.py -q` 为 24 passed。
- Commander/学习流水线/数据库组合：`.venv/bin/python -m pytest tests/test_commander.py tests/test_learning_pipeline_api.py tests/test_database_schema_guard.py -q` 为 34 passed。
- 导入 issue 路由/状态机专项：`.venv/bin/python -m pytest tests/test_learning_pipeline_api.py::test_import_issue_governance_resolve_reopen_and_audit_log tests/test_learning_pipeline_api.py::test_import_issue_governance_route_requires_resolution_to_resolve tests/test_commander.py -q` 为 12 passed。
- 规范检查：`.venv/bin/python -m ruff check backend/api/evolution.py backend/models/knowledge.py backend/database/schema_guard.py tools/commander.py tests/test_learning_pipeline_api.py tests/test_database_schema_guard.py` 通过。
- 全量后端门禁：`.venv/bin/python -m pytest -q` 为 110 passed，产品覆盖率 85%。
- 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；数据库 `status=ok`、`integrity_check=ok`、缺表/缺列为空；import quality `quality_score=75.0`、`auto_repairable_fields=0`、`active_issue_count=100`、`resolved_issue_count=0`。
- 共享库安全 repair：全量测试新增数据造成 `auto_repairable_fields=10` 后，已执行 metadata-only repair，补全样本 2、资源 2、知识 1；未保存第三方全文或敏感原文。
- 类型说明：本轮未宣称 `backend/api/evolution.py` strict mypy 通过；该旧大文件仍有历史类型债，当前本轮以 pytest、ruff、schema guard 和 commander 回归审计作为运行级门禁。
- 2026-05-22 07:30 CST 导入 issue 前端治理操作台验证：
- 后端治理/commander 专项：`.venv/bin/python -m pytest tests/test_learning_pipeline_api.py::test_import_issue_governance_resolve_reopen_and_audit_log tests/test_learning_pipeline_api.py::test_import_issue_governance_route_requires_resolution_to_resolve tests/test_commander.py -q` 为 12 passed。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成 `Governance-*.js` chunk。
- 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；import quality 仍为 100 active issue、0 resolved issue、auto repair 0，状态分布为 open/reopened。
- 浏览器验证：`http://127.0.0.1:3001/governance` 可见“Reviewed 资产发布操作台”“导入 Issue 复核队列”“Issue 操作”“Active Issue”；页面 `scrollWidth=clientWidth=1280`，控制台 error 为空。
- 新增能力验证：前端可筛选 active/open/review_requested/resolved/reopened issue，并对单条 issue 执行 dry-run 与真实写入操作；关闭仍要求 reviewer 和 resolution，不能绕过后端审计。
- 2026-05-22 07:35 CST 导入 issue 批量治理验证：
- 后端批量 action 覆盖：`.venv/bin/python -m pytest tests/test_learning_pipeline_api.py::test_import_issue_governance_resolve_reopen_and_audit_log tests/test_learning_pipeline_api.py::test_import_issue_governance_route_requires_resolution_to_resolve -q` 为 2 passed。
- 前端门禁：`cd frontend && npm run type-check && npm run build` 通过；`Governance-*.js` chunk 更新。
- 新增能力验证：`/governance` 可选择当前筛选页、清空选择、显示已选标记和已选数量；dry-run/apply 均发送 `issue_ids` 数组，并在审计结果中显示影响 issue 数。
- 2026-05-22 07:45 CST 生产调度服务化配置验证：
- 调度专项：`.venv/bin/python -m pytest tests/test_commander.py -q` 为 12 passed。
- 调度规范：`.venv/bin/python -m ruff check backend/core/production_scheduler.py tools/commander.py tests/test_commander.py` 通过。
- 调度 strict mypy：`.venv/bin/python -m mypy backend/core/production_scheduler.py --strict --follow-imports=skip` 通过。
- 服务配置预览：`.venv/bin/python -m tools.commander scheduler-service-plan` 通过，状态为 `planned`，未写系统目录。
- 服务配置生成：`.venv/bin/python -m tools.commander scheduler-service-plan --apply` 通过，写入 `docs/tasks/scheduler_service/` 下 launchd、systemd user 和 manifest 三个审计文件。
- 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；数据库健康 ok，import quality `auto_repairable_fields=0`，仍有 100 条 active issue 等待来源治理。
- 2026-05-22 07:50 CST AI Provider live probe 安全门验证：
- Provider/Analytics 专项：`.venv/bin/python -m pytest tests/test_ai_provider_safety.py tests/test_analytics_api.py -q` 为 30 passed。
- Provider 规范：`.venv/bin/python -m ruff check backend/ai/provider_client.py backend/api/analytics.py backend/database/connection.py tests/test_ai_provider_safety.py tests/test_analytics_api.py` 通过。
- Provider strict mypy：`.venv/bin/python -m mypy backend/ai/provider_client.py backend/api/analytics.py --strict` 通过。
- 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过。
- 新增能力验证：未设置 `DEEPSEEK_LIVE_PROBE_ENABLED=true` 时，`dry_run=false` live probe 返回 `blocked_by_policy`，API 返回 409 并写入脱敏 `ai_provider_probe_logs`；测试确认不会调用 httpx、不会泄露 API key 或响应体。
- 2026-05-22 07:55 CST 导入 issue 来源分组治理验证：
- 后端分组专项：`.venv/bin/python -m pytest tests/test_learning_pipeline_api.py::test_import_issue_queue_groups_by_source_for_batch_governance tests/test_learning_pipeline_api.py::test_import_issue_governance_resolve_reopen_and_audit_log tests/test_learning_pipeline_api.py::test_import_issue_governance_route_requires_resolution_to_resolve -q` 为 3 passed。
- 后端规范：`.venv/bin/python -m ruff check backend/api/evolution.py tests/test_learning_pipeline_api.py` 通过。
- 前端门禁：`cd frontend && npm run type-check && npm run build` 通过。
- 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；import quality `quality_score=75.0`，`auto_repairable_fields=0`，`active_issue_count=99`，`resolved_issue_count=1`。
- 新增能力验证：issue 队列返回 `source_groups`，包含来源级 active/resolved、状态/严重度分布、severity weight、样例 issue id 和 recommended action；前端 `/governance` 展示来源优先级并可选中来源样例 issue 进入批量治理。
- 2026-05-22 08:00 CST 导入 issue 批量关闭报告验证：
- 后端报告专项：`.venv/bin/python -m pytest tests/test_learning_pipeline_api.py::test_import_issue_governance_resolve_reopen_and_audit_log tests/test_learning_pipeline_api.py::test_import_issue_queue_groups_by_source_for_batch_governance -q` 为 2 passed。
- 后端规范：`.venv/bin/python -m ruff check backend/api/evolution.py tests/test_learning_pipeline_api.py` 通过。
- 前端门禁：`cd frontend && npm run type-check && npm run build` 通过。
- 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；import quality `quality_score=75.0`，`auto_repairable_fields=0`，`active_issue_count=98`，`resolved_issue_count=2`。
- 新增能力验证：dry-run/apply 返回 `governance_report`；报告只暴露 resolution hash、聚合计数、安全标记和日志 id，不返回 resolution 原文或第三方来源原文。
- 2026-05-22 08:10 CST 导入 issue 审计历史与日志脱敏验证：
- 后端审计专项：`.venv/bin/python -m pytest tests/test_learning_pipeline_api.py::test_import_issue_audit_history_redacts_resolution_text tests/test_learning_pipeline_api.py::test_import_issue_governance_resolve_reopen_and_audit_log tests/test_learning_pipeline_api.py::test_import_issue_queue_groups_by_source_for_batch_governance -q` 为 3 passed。
- 后端规范：`.venv/bin/python -m ruff check backend/api/evolution.py tests/test_learning_pipeline_api.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；import quality `quality_score=75.0`，`auto_repairable_fields=0`，`active_issue_count=95`，`resolved_issue_count=5`。
- 浏览器验证：`http://127.0.0.1:3001/governance` 标题为“发布治理 - 关系动力学全息”，可见“Reviewed 资产发布操作台”“导入 Issue 复核队列”“审计历史”和 resolution hash 区域；`scrollWidth=clientWidth=1280`。
- 新增能力验证：`GET /api/evolution/import-quality/issues/audit` 返回最近治理日志；新写入的 `pipeline_run_logs.result_json` 与 `message` 只保存 `resolution_hash`，测试确认不会泄露人工处理说明明文。
- 2026-05-22 08:13 CST 导入 issue 状态归一化 migration revision 验证：
- 数据库迁移专项：`.venv/bin/python -m pytest tests/test_database_schema_guard.py -q` 为 9 passed。
- 数据库迁移规范：`.venv/bin/python -m ruff check backend/database/migration_runner.py tests/test_database_schema_guard.py` 通过。
- 数据库迁移 strict mypy：`.venv/bin/python -m mypy backend/database/migration_runner.py --strict --follow-imports=skip` 通过。
- 真实库 formal runner dry-run：报告 3 个 active revision 待应用，包括 `2026_05_22_import_issue_status_normalization_v1`。
- 真实库 formal runner apply：创建备份 `data/backups/relationship_training-20260522081348.db`，应用 `2026_05_21_formal_runner_v1`、`2026_05_21_metadata_vector_index_rebuild_v1`、`2026_05_22_import_issue_status_normalization_v1`，errors 为空，pending_after 为空，schema_after `status=ok`、`integrity_check=ok`、缺表/缺列为空。
- 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；import quality `quality_score=75.0`，`auto_repairable_fields=0`，`active_issue_count=92`，`resolved_issue_count=8`。
- 新增能力验证：迁移 revision 把空/null issue status 落库为 `open`，回填 `updated_at`，并把 before/after 状态分布和安全标记写入 `formal_migration_revision_results`。
- 2026-05-22 16:44 CST AI Provider live probe readiness runbook 验证：
- Provider/Analytics 组合专项：`.venv/bin/python -m pytest tests/test_analytics_api.py tests/test_ai_provider_safety.py -q` 为 32 passed。
- Provider/Analytics 规范：`.venv/bin/python -m ruff check backend/api/analytics.py tests/test_analytics_api.py tests/test_ai_provider_safety.py` 通过。
- Analytics strict mypy：`.venv/bin/python -m mypy backend/api/analytics.py --strict` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成 `Analytics-*.js` chunk。
- 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；AI success rate `25.8%`，provider failure rate `34.2%`，Provider risk 仍为 high。
- 浏览器验证：`http://127.0.0.1:3001/analytics` 标题为“分析中心 - 关系动力学全息”，可见“系统质量与历史趋势”“Live Probe Readiness”和 `dry_run=true` 命令；`scrollWidth=clientWidth=1280`。
- 新增能力验证：`GET /api/analytics/ai-provider-probe-readiness` 不执行外部调用，只返回 configured/live_probe_enabled、blockers、脱敏 request_shape、recent probe logs、quality gate 和安全 runbook；测试确认不会泄露 API key、URL query secret、prompt text、response body 或 healthcheck 文本。
- 2026-05-22 17:03 CST 生产调度健康告警与恢复验证：
- 调度健康专项：`.venv/bin/python -m pytest tests/test_commander.py::test_commander_scheduler_plan_and_run_once_are_auditable tests/test_commander.py::test_scheduler_health_reports_missing_required_jobs tests/test_commander.py::test_scheduler_health_marks_run_once_history_as_observed tests/test_commander.py::test_production_scheduler_daemon_registers_expected_jobs -q` 为 4 passed。
- 调度健康规范：`.venv/bin/python -m ruff check backend/core/production_scheduler.py tools/commander.py tests/test_commander.py` 通过。
- 调度健康 strict mypy：`.venv/bin/python -m mypy backend/core/production_scheduler.py --strict --follow-imports=skip` 通过。
- 初始健康检查：`.venv/bin/python -m tools.commander scheduler-health` 返回 `status=needs_attention`，识别 `commander_sync_state_hourly` required job 无审计快照。
- 恢复动作：`.venv/bin/python -m tools.commander scheduler-run-once regression_audit_daily --dry-run --batch-limit 2` 写入 regression audit dry-run 快照；`.venv/bin/python -m tools.commander scheduler-run-once commander_sync_state_hourly --dry-run` 写入 commander sync 快照。
- 最终健康检查：`.venv/bin/python -m tools.commander scheduler-health` 返回 `status=healthy`，三个 job 均 observed，required job 均不 stale，alerts 为空，state 文件带有 `health` 与 `recovery_runbook`。
- 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；数据库健康 ok，import quality `quality_score=75.0`、`active_issue_count=92`、`resolved_issue_count=8`，AI Provider 仍 high risk。
- 2026-05-22 17:22 CST 分析中心生产调度健康控制台验证：
- Analytics 调度专项：`.venv/bin/python -m pytest tests/test_analytics_api.py::test_analytics_center_aggregates_quality_domains_without_payload_leakage -q` 为 1 passed。
- Analytics 规范：`.venv/bin/python -m ruff check backend/api/analytics.py tests/test_analytics_api.py` 通过。
- Analytics strict mypy：`.venv/bin/python -m mypy backend/api/analytics.py --strict` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成 `Analytics-*.js` chunk。
- 调度健康检查：`.venv/bin/python -m tools.commander scheduler-health` 返回 `status=healthy`，三个 job 均 observed，alerts 为空。
- 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；数据库健康 ok，Gold Set 门禁通过，向量召回 top10=1.0，import quality 仍为 75.0，AI Provider 仍 high risk。
- 新增能力验证：`GET /api/analytics/center` 返回 `sections.scheduler`，并把 `scheduler_health` 纳入 scorecard/timeline/alerts；前端 `/analytics` 展示“生产调度健康”、任务 freshness、告警和 recovery runbook，payload 只包含本地审计状态、摘要和命令。
- 2026-05-22 17:44 CST AI Provider 失败处置矩阵验证：
- Provider/Analytics 精准专项：`.venv/bin/python -m pytest tests/test_analytics_api.py::test_ai_provider_diagnostics_redacts_secret_and_flags_http_400 tests/test_analytics_api.py::test_ai_provider_failure_playbook_classifies_http_400_without_local_shape_risk tests/test_analytics_api.py::test_analytics_center_aggregates_quality_domains_without_payload_leakage -q` 为 3 passed。
- Provider/Analytics 组合专项：`.venv/bin/python -m pytest tests/test_analytics_api.py tests/test_ai_provider_safety.py -q` 为 33 passed。
- Commander 组合专项：`.venv/bin/python -m pytest tests/test_analytics_api.py::test_ai_provider_failure_playbook_classifies_http_400_without_local_shape_risk tests/test_commander.py -q` 为 15 passed。
- 规范与类型：`.venv/bin/python -m ruff check backend/api/analytics.py tools/commander.py tests/test_analytics_api.py` 通过；`.venv/bin/python -m mypy backend/api/analytics.py --strict` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成 `Analytics-*.js` chunk。
- 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；`ai_provider_diagnostics.failure_playbook.root_cause_matrix[0].id=account_or_service_http_400`，`http_400_without_local_shape_risk=true`，Provider 仍 high risk 但分类更精确。
- 浏览器验证：旧 `localhost:8000` 存在历史后端 500，因此本轮使用干净后端/前端 `127.0.0.1:8001/3002` 验证；`/analytics` 可见 `Provider Failure Playbook`、`controlled_live_probe`、安全 runbook，`scrollWidth=clientWidth=1280`，console errors 为空。
- 新增能力验证：`failure_playbook` 只返回聚合根因、回归样例、质量门禁和 runbook；测试确认不泄露 API key、URL query secret、payload marker、private response 或 prompt/response body。
- 2026-05-22 17:58 CST 导入 Issue 来源级复核包验证：
- 导入治理专项：`.venv/bin/python -m pytest tests/test_learning_pipeline_api.py::test_import_issue_queue_groups_by_source_for_batch_governance tests/test_learning_pipeline_api.py::test_import_issue_source_review_packet_allows_batch_closure_for_warning_only_source tests/test_learning_pipeline_api.py::test_import_issue_audit_history_redacts_resolution_text -q` 为 3 passed。
- 后端规范：`.venv/bin/python -m ruff check backend/api/evolution.py tests/test_learning_pipeline_api.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成 `Governance-*.js` chunk。
- 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；import quality `quality_score=75.0`、`active_issue_count=89`、`resolved_issue_count=11`、`auto_repairable_fields=0`。
- 浏览器验证：干净后端/前端 `127.0.0.1:8001/3002` 的 `/governance` 可见“来源复核包”和 `sha256` 样例 hash；`scrollWidth=clientWidth=1280`，console errors 为空。
- 新增能力验证：`source_groups.review_packet` 返回来源范围、证据清单、脱敏样例、批量动作建议和质量门禁；error 来源默认 `request_review`，warning-only 来源可作为关闭候选但仍要求 reviewer/resolution 且 `auto_close_allowed=false`；issue 队列不再返回 resolution 明文。
- 2026-05-22 18:08 CST 网站正常可用启动链路验证：
- 启动脚本语法：`bash -n start.sh` 通过。
- 真实启动验证：`./start.sh` 自动清理本项目旧 8000/3000 服务，后端 `/health` 返回 200，`/api/analytics/center?limit=20` 返回 200，前端 `http://127.0.0.1:3000` 就绪。
- 浏览器功能性验证：`/`、`/trainer`、`/analytics`、`/governance`、`/knowledge`、`/path` 均有应用外壳和内容；每页 `scrollWidth=clientWidth=1280`，console errors 为空。
- 前端构建：`cd frontend && npm run build` 通过。
- 后端关键回归：`.venv/bin/python -m pytest tests/test_analytics_api.py::test_analytics_center_aggregates_quality_domains_without_payload_leakage tests/test_learning_pipeline_api.py::test_import_issue_queue_groups_by_source_for_batch_governance -q` 为 2 passed。
- 新增能力验证：默认启动不再使用 uvicorn reload，减少旧 reloader 子进程残留；README 手动启动命令已改为项目根路径与正确 API 代理配置。
- 2026-05-22 18:25 CST 统一审计中心验证：
- Analytics 审计专项：`.venv/bin/python -m pytest tests/test_analytics_api.py -q` 为 12 passed，覆盖 audit center 聚合、模块分布、AI/provider/import 事件和敏感 marker/resolution 明文不泄漏。
- 后端规范：`.venv/bin/python -m ruff check backend/api/analytics.py tests/test_analytics_api.py` 通过。
- Analytics strict mypy：`.venv/bin/python -m mypy backend/api/analytics.py --strict` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成 `Audit-*.js` chunk。
- 浏览器验证：`http://127.0.0.1:3000/audit` 标题为“审计中心 - 关系动力学全息”，可见“运营审计时间线”“最近审计事件”“下一步动作”“分布”；`scrollWidth=clientWidth=1280`。
- 新增能力验证：`GET /api/analytics/audit-center` 返回统一事件结构、module 筛选、状态/级别/模块分布和下一步动作；事件详情只展示派生 hash 与结构化摘要，不返回 AI payload、人工 resolution 明文、第三方全文或密钥。
- 2026-05-22 20:58 CST 前端运行时/API 错误审计捕获验证：
- 后端专项：`.venv/bin/python -m pytest tests/test_analytics_api.py tests/test_database_schema_guard.py -q` 为 22 passed，覆盖 runtime event 写入、runtime 模块审计筛选、schema row count 和 `context_json` 质量。
- 后端规范：`.venv/bin/python -m ruff check backend/api/analytics.py backend/models/runtime.py backend/database/schema_guard.py tests/test_analytics_api.py` 通过。
- Analytics strict mypy：`.venv/bin/python -m mypy backend/api/analytics.py --strict` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成 `Audit-*.js` 与更新后的入口 chunk。
- 真实接口验证：`POST /api/analytics/runtime-events` 写入 `event_type=api_error`，返回 `status=recorded`、`severity=high`、`message_hash=sha256:*`，不返回 token 或 message 原文。
- 浏览器验证：`/audit` 下拉包含“运行时”，筛选后可见 `api_error` runtime events；摘要中的 `Bearer secret-*` 被展示为 `Bearer [redacted]`，`secret-demo` 不出现在页面文本中，`scrollWidth=clientWidth=1280`。
- 新增能力验证：前端 API 拦截器、Vue 全局 errorHandler、window error 和 unhandled rejection 会以节流方式写入 runtime event；上报接口自身失败不会递归影响用户流程。
- 2026-05-22 21:24 CST 前端 NaN/空态/运营标签治理验证：
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成 `format-*.js`、更新后的 `Analytics-*.js`、`Evolution-*.js`、`Daily-*.js`、`Onboarding-*.js`。
- 浏览器扫描：`/analytics`、`/evolution`、`/daily`、`/onboarding` 均返回 `hasNaN=false`、`hasUndefined=false`、`hasInfinity=false`、`scrollWidth=clientWidth=1280`。
- Analytics 标签复验：`/analytics` 不再出现 `75health`、`85score`、`70score` 这类单位拼接异常；目标显示为 `%`、数值或“通过”。
- 新增能力验证：`frontend/src/utils/format.ts` 统一收敛数字展示、百分比、比例进度条和 fallback；Daily/Onboarding 空数组进度条有保护，Analytics/Evolution 的关键运营指标有安全格式化。
- 2026-05-22 21:44 CST 关键页面可恢复错误态验证：
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `Analytics-*.js`、`Audit-*.js`、`Evolution-*.js` chunk。
- 真实启动验证：`./start.sh` 完成后后端 `/health`、`/api/analytics/center?limit=20` 和前端 `http://127.0.0.1:3000` 均就绪。
- 浏览器验证 `/analytics`：可见“系统质量与历史趋势”“告警队列”“AI 质量与 Provider”“生产调度健康”，`hasNaN=false`、`hasUndefined=false`、`hasInfinity=false`、`scrollWidth=clientWidth=1280`。
- 浏览器验证 `/audit`：可见“运营审计时间线”“最近审计事件”，`hasNaN=false`、`hasUndefined=false`、`hasInfinity=false`、`scrollWidth=clientWidth=1280`。
- 浏览器验证 `/evolution`：可见“进化中心”“学习速度”“运行周调度”，`hasNaN=false`、`hasUndefined=false`、`hasInfinity=false`、`scrollWidth=clientWidth=1280`。
- 新增能力验证：Analytics/Audit/Evolution 均具备页面级加载失败或刷新失败反馈，关键刷新/调度动作具备可恢复入口；本轮未把未模拟的外部故障路径声明为已通过，只确认正常加载路径未被错误态改动破坏。
- 2026-05-22 21:54 CST 治理台与训练中心可恢复反馈验证：
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `Governance-*.js` 与 `Trainer-*.js` chunk。
- 真实启动验证：`./start.sh` 完成后后端 `/health`、`/api/analytics/center?limit=20` 和前端 `http://127.0.0.1:3000` 均就绪。
- 浏览器验证 `/governance`：可见“Reviewed 资产发布操作台”“导入 Issue 复核队列”“Issue 操作”，`hasNaN=false`、`hasUndefined=false`、`hasInfinity=false`、`scrollWidth=clientWidth=1280`。
- 浏览器验证 `/trainer`：可见“训练中心”“你的回应”“提交并生成七维反馈”，`hasNaN=false`、`hasUndefined=false`、`hasInfinity=false`、`scrollWidth=clientWidth=1280`。
- 新增能力验证：Governance 的 reviewed 候选与 import issue 队列拥有独立错误横幅、重试按钮和页面级空态；Trainer 的题目加载失败与评分提交失败有页面内恢复提示，提交失败时不清空用户输入。
- 2026-05-22 21:58 CST 前端运营核心页面 smoke 门禁验证：
- Smoke 门禁：`cd frontend && npm run smoke:world` 通过，`checked=22`，报告写入 `frontend/output/smoke/report.json`。
- Smoke 覆盖升级：新增 `/analytics`、`/audit`、`/governance`，并继续覆盖 Dashboard、Trainer、TrainerAI、Path、Mistakes、Knowledge、Evolution、Framework 的桌面/移动视口。
- Mock 数据验证：smoke mock 层新增 `GET /api/analytics/center`、`GET /api/analytics/audit-center`、`GET /api/evolution/reviewed-assets/publish-candidates`、`GET /api/evolution/import-quality/issues`、`GET /api/evolution/import-quality/issues/audit` 的结构化响应。
- Smoke 检查项：每页验证 heading、横向溢出、可见元素重叠风险、console error 和 pageerror。
- 前端门禁复验：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 2026-05-22 22:12 CST AI 训练伴侣可恢复反馈与移动端设置优化验证：
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `TrainerAI-*.js` chunk。
- Smoke 门禁：`cd frontend && npm run smoke:world` 通过，`checked=22`，报告写入 `frontend/output/smoke/report.json`。
- 真实启动验证：`./start.sh` 完成后后端 `/health`、`/api/analytics/center?limit=20` 和前端 `http://127.0.0.1:3000` 均就绪。
- 浏览器验证 `/trainer-ai` 场景页：可见“AI 训练伴侣”“选择训练场景”“小焦虑”“本次对话评分”，无 `NaN`、`undefined`、`Infinity`。
- 浏览器验证 `/trainer-ai` 设置页：可见“对话设置”“对话难度”“期望回应风格”“话题偏好”“开始对话”，`scrollWidth=clientWidth=1280`。
- 新增能力验证：发送降级会给出页面内提示；会话复盘失败会展示可重试警告；发送流程用 finally 复位 typing；设置面板按钮可换行以适配小屏。
- 2026-05-22 22:21 CST AI 训练伴侣真实交互 smoke 门禁验证：
- Smoke 门禁初次执行捕获移动端真实问题：`TrainerAIInteraction/mobile` 中会话复盘“下一练习”和聊天消息存在可见重叠风险；随后修复聊天区域布局。
- 布局修复：`TrainerAI` 聊天主区域改为外层可滚动，消息列表定高独立滚动，头部、关系状态、会话复盘、建议回复和输入区设置为不压缩，避免小屏高度下互相覆盖。
- Smoke 门禁复验：`cd frontend && npm run smoke:world` 通过，`checked=24`，报告写入 `frontend/output/smoke/report.json`。
- 交互覆盖：桌面和移动视口均会选择“小回避”、发送“我理解你今天比较累，不急着回复，我在。”，等待伴侣回复“谢谢你这样说”、会话状态曲线、评分和输入框恢复可用。
- Mock 数据验证：smoke mock 层新增 `POST /api/training/partner/simulate` 与 `GET /api/training/partner/sessions/101/review`，覆盖关系状态、session review、关键转折和下一练习。
- 前端门禁复验：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 2026-05-22 22:33 CST 训练关键失败路径 smoke 门禁验证：
- Smoke 失败路径初次执行确认 UI 断言已通过，但预期 500/503 和应用错误日志被通用 runtime error 规则误判为失败；随后新增 `expectedFailureRuntimeErrors` 分类，只放行带有预期 marker 的失败路径日志。
- Smoke 门禁复验：`cd frontend && npm run smoke:world` 通过，`checked=30`，报告写入 `frontend/output/smoke/report.json`。
- Trainer 失败路径：模拟 `POST /api/training/compare` 返回 500，验证“评分提交失败”出现，且用户回应文本仍保留。
- TrainerAI 伴侣失败路径：模拟 `POST /api/training/partner/simulate` 返回 503，验证本地安全降级提示、降级回应和输入框恢复可用。
- TrainerAI 复盘失败路径：模拟 `GET /api/training/partner/sessions/101/review` 返回 503，验证“会话复盘暂时不可用”和“重试复盘”出现，且聊天输入未锁死。
- 前端门禁复验：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 2026-05-22 22:40 CST 项目需求审计与评估报告验证：
- 文档产出：新增 `docs/项目需求审计与评估报告.md`。
- 内容结构验证：报告包含项目摘要、SMART 核心目标、重难点分析、项目亮点、缺陷分析与优化改进步骤、功能需求明细表、待客户确认问题清单。
- 依据交叉验证：报告引用并综合 `docs/progress.md`、`docs/validation_report.md`、`docs/tasks/module_dag.json`、`docs/tasks/commander_state.json` 与当前实现能力。
- 状态边界验证：报告把 DAG 68/68、前端 smoke 30 项、训练/治理/审计/调度/迁移/AI 安全等已验证能力列为已完成；把 Provider live probe、真实专家复核、内容许可、生产部署等外部依赖标为待确认或阻塞。
- 全仓 ruff/mypy 仍有历史债务，集中在旧模型类型写法、一次性 `expand_data*` 扩展脚本和部分非核心 API；当前数据库触达文件与训练核心链路已通过 ruff 与 mypy strict。
- 覆盖率 86%，已达到最终 85%+ 目标；测试数 96。
- 进化流水线当前已有批量处理器、本地周调度入口、保守 metadata-only 来源抓取、持久化元数据向量索引、sqlite-vec 原生 ANN 后端和 ANN 召回/阈值校准报表；尚未接 APScheduler 后台定时和生产级长期回归计划。
- Trainer 的数图组件已嵌入每一道推荐训练题；样本多粒度字段已可持久化，但尚未建立多版本样本关联表。
- AI 伴侣会话轨迹已持久化，提供即时复盘面板与 Dashboard 跨会话趋势；后续还可继续扩展为独立历史详情页和更细粒度推荐。
- Gold Set 已从脚手架进入专家复核闭环；后续仍需要继续提高真实专家覆盖率与样本规模。
- 指挥官跨会话自动执行已有 `tools.commander`、机器可读 DAG、状态快照和每日自动推进任务；后续仍需在每轮完成后持续同步 DAG、进度和验证报告。
- 当前 schema guard 可处理缺表/缺列和 JSON 质量审计；正式 migration runner 已提供计划、dry-run、备份和审计记录。复杂 schema 变更如改列、删列、索引重建、历史数据重算仍需逐个实现 active revision。
- 本机此前 `localhost:8000` 存在旧后端进程；页面 smoke 使用干净端口完成验证。

- 2026-05-22 23:26 CST 资源海洋扩容与 AI 伴侣活性增强验证：
- 扩库 dry-run：`.venv/bin/python -m backend.database.auto_expand_resources --dry-run --target-total 1200` 返回 `before=360`、`created=840`、`after=360`。
- 扩库 apply：`.venv/bin/python -m backend.database.auto_expand_resources --target-total 1200` 返回 `before=360`、`created=840`、`after=1200`。
- 数据库健康：`sqlite3 data/relationship_training.db "PRAGMA quick_check; SELECT count(*) FROM resource_library;"` 返回 `ok` 和 `1200`。
- 资源接口：`curl http://127.0.0.1:8000/api/resources?limit=3` 返回 `{items,total}`，`total=1200`。
- 后端专项：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py tests/test_training_flow.py::test_partner_simulation_degrades_safely_without_provider tests/test_training_flow.py::test_partner_state_machine_tracks_pressure_and_repair -q` 为 10 passed。
- 规范与类型：`.venv/bin/python -m ruff check backend/api/resources.py backend/api/training.py backend/database/auto_expand_resources.py` 通过；`.venv/bin/python -m mypy backend/database/auto_expand_resources.py --strict --follow-imports=skip` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `Resources-*.js` 与 `TrainerAI-*.js` chunk。
- 浏览器验证说明：本轮通过 in-app browser 连接验证页面外壳和资源页新文案已加载；由于验证期间当前标签被用户/应用导航切换到其他页面，未把资源页可见 1200 条声明为已通过，仅以接口和构建结果确认数据链路可用。

- 2026-05-22 23:40 CST 公开来源透明扩容验证：
- 扩库 dry-run：`.venv/bin/python -m backend.database.auto_expand_resources --dry-run --target-total 2400` 返回 `before=1200`、`created=1200`、`after=1200`。
- 扩库 apply：`.venv/bin/python -m backend.database.auto_expand_resources --target-total 2400` 返回 `before=1200`、`created=1200`、`after=2400`。
- 数据库健康：`PRAGMA quick_check` 返回 `ok`；`resource_library=2400`。
- 来源分布：公开 URL 资源包含 `public_anchor:Gottman Institute`、`public_anchor:Gottman Research`、`public_anchor:CNVC Feelings Inventory` 等来源；当前前 5 条资源均带 `https://www.cnvc.org/training/resource/feelings-inventory`。
- 后端契约：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_sample_and_resource_catalog_contracts_match_frontend -q` 通过。
- 类型与构建：`.venv/bin/python -m mypy backend/database/auto_expand_resources.py --strict --follow-imports=skip` 通过；`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 浏览器验证：`http://127.0.0.1:3000/resources` 显示 `1000 / 2400 条`，可见 `打开信息源`、`信息源链接` 与 `cnvc.org`；检测 `hasNaN=false`、`hasUndefined=false`、`hasHorizontalOverflow=false`。

- 2026-05-22 23:56 CST 资源分页与万条级扩容验证：
- 扩库 dry-run：`.venv/bin/python -m backend.database.auto_expand_resources --dry-run --target-total 10000` 返回 `before=2400`、`created=7600`、`skipped=1200`、`after=2400`。
- 扩库 apply：`.venv/bin/python -m backend.database.auto_expand_resources --target-total 10000` 返回 `before=2400`、`created=7600`、`skipped=1200`、`after=10000`。
- 数据库健康：`PRAGMA quick_check` 返回 `ok`；`resource_library=10000`；类型分布包含 `phrase=3113`、`story=3087`、`media=3074`、`joke=315`、`flirty=244`、`game=154`、`riddle=13`。
- 后端契约：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_sample_and_resource_catalog_contracts_match_frontend -q` 通过，覆盖分页返回字段和 sources 目录。
- 规范与构建：`.venv/bin/python -m ruff check backend/api/resources.py backend/database/auto_expand_resources.py tests/test_catalog_profile_review_api.py` 通过；`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 浏览器验证：`http://127.0.0.1:3000/resources` 显示 `第 1 / 209 页 · 1-48 / 10000 条`，页面 DOM 卡片数 48；可见 `开放信息源`、`上一页`、`下一页`、`末页`、`打开信息源`；检测 `hasNaN=false`、`hasUndefined=false`、`hasHorizontalOverflow=false`。

- 2026-05-23 00:52 CST 资源海洋运营级治理与训练活性修复验证：
- 数据修复：CNVC 旧 URL `https://www.cnvc.org/training/resource/*` 已合并到 `https://www.capitalnvc.org/*`，更新 1440 条资源记录。
- 数据概况：真实库 `resource_library=12000`、`distinct_content=11709`、历史重复内容债务 291 条。
- 资源接口：`GET /api/resources?page=1&limit=3&q=边界` 返回 200，分页字段和筛选总数正常；`GET /api/resources/sources?limit=5` 返回来源摘要、结构、质量说明与 `link_status`。
- AI Provider 状态接口：`GET /api/training/partner/provider-status` 返回 200，显示 `configured=true`、`provider=deepseek`、`mode=openai`、`model=deepseek-v4-pro`。
- 后端契约：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_sample_and_resource_catalog_contracts_match_frontend -q` 通过。
- 规范：`.venv/bin/python -m ruff check backend/api/resources.py backend/api/training.py backend/database/auto_expand_resources.py backend/core/resource_source_catalog.py tests/test_catalog_profile_review_api.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 额外 strict mypy：`backend/api/resources.py` 因 FastAPI 未类型化装饰器和历史 `dict` 泛型标注被 strict mypy 拦截，本轮未把该项列为通过；核心验收以 pytest、ruff、前端 type-check/build 和浏览器验证为准。
- 浏览器验证 `/resources?q=情绪流动&source=Gottman%20Institute`：显示 `第 1 / 5 页 · 1-48 / 240 条`、48 张资源卡、113 个外链、6 个筛选输入/选择控件，`hasNaN=false`、`hasUndefined=false`、`overflow=false`、console error 为空。
- 浏览器验证 `/surf`：显示“浏览冲浪”“打开网站”“内容结构”“质量说明”“链接状态：核心锚点，已纳入高可信目录”，17 个来源卡、17 个外链，`hasNaN=false`、`hasUndefined=false`、`overflow=false`、console error 为空。
- 浏览器验证 `/trainer-ai`：显示“已配置 DeepSeek，AI 深度模拟可用”“deepseek/openai · deepseek-v4-pro”，`hasNaN=false`、`hasUndefined=false`、`overflow=false`、console error 为空。
- 浏览器验证 `/mistakes`：显示“情绪流动动线”和“三步改写练习”，`hasNaN=false`、`hasUndefined=false`、`overflow=false`、console error 为空。

- 2026-05-23 01:20 CST 资源海洋职责切分与原文级导读治理验证：
- Schema 自动补列：`create_db_and_tables()` 返回 `status=ok`，资源表新增导读、许可、指纹、质量字段后数据库可正常启动。
- 资源治理 dry-run：识别 12000 条需要回填导读字段；首次 apply 后删除 291 条精确重复，重复债务归零。
- 生成器修复：公开来源资源正文加入来源入口差异，随后 `--rebuild-generated --target-total 12000` 重建生成资源。
- 最终质量治理：`total=12000`、`distinct_fingerprints=12000`、`exact_duplicate_debt=0`、`missing_guidance=0`、`avg_quality_score=99.5`。
- 新质量接口：`GET /api/resources/quality-report` 返回 200，并输出 `total=12000`、`distinct_fingerprints=12000`、`exact_duplicate_debt=0`、`missing_guidance=0`。
- 后端契约：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_sample_and_resource_catalog_contracts_match_frontend -q` 通过。
- 规范：`.venv/bin/python -m ruff check backend/api/resources.py backend/database/auto_expand_resources.py backend/database/resource_quality_governance.py backend/models/resource.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 启动验证：`./start.sh` 重启后后端 `/health`、`/api/analytics/center?limit=20` 和前端 `http://127.0.0.1:3000` 就绪。
- 浏览器验证 `/resources`：顶部“开放信息源”模块已消失；显示 `第 1 / 250 页 · 1-48 / 12000 条`、48 张资源卡、96 个原站外链；可见 `导读片段`、`质量分`、`许可`；`hasNaN=false`、`hasUndefined=false`、`overflow=false`、console error 为空。

- 2026-05-23 07:28 CST 资源库使命对齐纠偏验证：
- 数据分布审计：纠偏前公开来源几乎均为 720 条，且包含 CDC、WHO、ONS、YRBS、TalkingData、Zenodo 等背景源；资源类型被 `story/phrase/media` 三类模板主导。
- 生成器收敛：`MISSION_PUBLIC_SOURCE_NAMES` 排除泛统计/公共卫生/行业数据背景源；公开来源卡正文强制围绕微关系训练轴。
- 轮转生成验证：四个本地训练库分别约 `1052/1052/1051/1051` 条，不再由单一“深度聊天话题库”占据剩余容量。
- 最终质量报告：`total=12000`、`distinct_fingerprints=12000`、`exact_duplicate_debt=0`、`missing_guidance=0`、`avg_quality_score=94.5`、`avg_mission_alignment=82.9`、`off_mission_count=76`。
- 后端契约：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_sample_and_resource_catalog_contracts_match_frontend -q` 通过。
- 规范：`.venv/bin/python -m ruff check backend/database/auto_expand_resources.py backend/database/resource_quality_governance.py backend/api/resources.py backend/models/resource.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 浏览器验证 `/resources`：第一页资源回到“情绪流动故事库”“深度聊天话题库”等训练内容；`hasTrainingLanguage=true`、`hasOffMissionPublicHealth=false`、`hasOpenSourceBlock=false`、`hasNaN=false`、`hasUndefined=false`、`overflow=false`、console error 为空。

- 2026-05-23 08:04 CST 资源库具体案例化与浏览导航修复验证：
- 生成器重建：`.venv/bin/python -m backend.database.auto_expand_resources --target-total 12000 --rebuild-generated` 返回 `before=114`、`created=11886`、`deleted=11886`、`after=12000`。
- 质量治理：`.venv/bin/python -m backend.database.resource_quality_governance` 返回 `total=12000`、`distinct_fingerprints=12000`、`exact_duplicate_debt=0`、`missing_guidance=0`、`avg_quality_score=97.4`、`avg_mission_alignment=87.6`。
- 默认资源接口：`GET /api/resources?limit=6` 返回具体案例卡，内容包含“场景”“TA说”“常见失误”“更好回应”“情绪信号”“边界与同意”“练习任务”。
- 来源目录代码侧确认：`SOURCE_CATALOG` 当前 23 个来源，新增中文/工具/开源入口包括情感网、恋小帮、中文幽默王、52笑话网、哄哄模拟器、Paired、ChatRel、ChineseNlpCorpus。
- 后端契约：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_sample_and_resource_catalog_contracts_match_frontend -q` 通过。
- 规范：`.venv/bin/python -m ruff check backend/api/resources.py backend/database/auto_expand_resources.py backend/core/resource_source_catalog.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 启动验证：`BACKEND_RELOAD=1 ./start.sh` 重启后后端 `/health`、分析中心 API 和前端 `http://127.0.0.1:3000` 就绪。
- 浏览器验证 `/resources`：首屏显示具体训练案例，卡片包含完整场景、原话、失误、改写、情绪信号、边界与练习任务；可见“到顶部”“到底部”；总量显示 `1-48 / 4206`，表示默认视图优先展示具体案例资源。
- 浏览器验证 `/surf`：可见中文来源组，标题 `h2 a` 共 26 个且前 8 个标题 href 均为真实外链；页面显示“到顶部”“到底部”、网站摘要、内容结构、质量说明、链接状态和库内资源数。

- 2026-05-23 08:18 CST 表达工具箱贯通架构方案验证：
- 文档产出：新增 `docs/表达工具箱贯通架构方案.md`。
- 覆盖结构：文档包含定位、世界级总架构、六层表达模型、12 类分类树映射、表达工具本体库、表达场景矩阵、训练闭环、页面功能划分、数据库方案、API 方案、前端组件方案、内容扩容方案、DAG 任务拆分、优先级实施顺序和验收标准。
- 项目一致性：方案明确引用并贯通现有元基础、5W2H、八阶路径、资源海洋、浏览冲浪、Trainer、AI 伴侣、错题本、知识中枢和 commander/DAG。
- 执行边界：本轮为架构与需求拆解文档，不宣称 schema/API/页面已经实现；下一轮可从 `toc_sidebar_unification`、`expression_schema`、`expression_seed_tools` 开始落地。

- 2026-05-23 08:36 CST 下一阶段统一产品架构与执行蓝图验证：
- 文档产出：新增 `docs/下一阶段统一产品架构与执行蓝图.md`。
- 整合范围：文档合并内容质量治理、资源海洋页面、浏览冲浪、数据库与采集治理、AI 伴侣与训练联动、运营后台与审计、表达工具箱七类需求，避免两份任务清单重复或冲突。
- 细粒度结构：文档给出统一数据模型、新增表、资源表增强字段、训练尝试增强字段、API 规划、页面规划、复用组件、P0/P1/P2 DAG 任务和每项验收标准。
- 执行边界：本轮为统一架构与任务拆解，不宣称具体 schema/API/页面已经实现；下一轮建议执行 `toc_sidebar_unification`。

- 2026-05-23 09:58 CST 资源浏览与近重复治理 P0 验证：
- 后端新增 `GET /api/resources/similarity`，返回近重复治理队列；真实服务调用 `GET /api/resources/similarity?limit=1000&threshold=0.82&max_clusters=3` 返回 200，摘要为 `scanned=1000`、`clusters=3`、`queued_items=998`，首簇最高相似度 `0.988`。
- 单元测试：`.venv/bin/python -m pytest tests/test_vector_index.py -q` 通过，覆盖向量索引、资源近重复队列和资源 similarity route。
- 规范检查：`.venv/bin/python -m ruff check backend/core/vector_index.py backend/api/resources.py tests/test_vector_index.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 浏览器验证 `/resources`：页面真实渲染主线分组、具体案例卡、分页和本页目录；`hasUndefined=false`、`overflow=false`。
- 浏览器验证 `/governance`：新增“近重复资源队列”，可见 `扫描资源 1000`、`重复簇 12`、`候选项 1000`、`合并/隐藏变体`、簇内资源样例；`hasUndefined=false`、`overflow=false`。
- 执行边界：近重复队列只输出治理证据，不自动删除或改写资源；后续应接批量隐藏/重写/打散排序策略。

- 2026-05-23 10:08 CST 表达工具箱 SQLite 主真源与页面验证：
- Schema 验证：`create_db_and_tables()` 返回 `status=ok`，新增 `expression_tools` 与 `expression_tool_chains` 表可由 schema guard 管理。
- 真实 API 种子：`POST /api/expression/seed` 返回 200，`created=60`、`total_tools=60`、`chains.total=5`。
- 真实 API 查询：`GET /api/expression/tools?layer=emotion&limit=3` 返回情绪层工具；`POST /api/expression/recommend` 输入 `scene=修复`、`goal=修复信任` 返回“失望修复三步链”和关联工具。
- 单元测试：`.venv/bin/python -m pytest tests/test_expression_api.py tests/test_database_schema_guard.py -q` 通过。
- 规范检查：`.venv/bin/python -m ruff check backend/models/expression.py backend/database/expression_seed.py backend/api/expression.py backend/main.py backend/models/__init__.py backend/database/schema_guard.py backend/database/connection.py tests/test_expression_api.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成 `Expression-*.js` chunk。
- 浏览器验证 `/expression`：可见 `工具 60`、`工具链 5`、`推荐 2`、工具详情、风险边界和工具链推荐；`hasUndefined=false`、`overflow=false`。
- 执行边界：本轮已完成工具箱主数据、API 和页面；尚未把工具标签回填到资源卡、Trainer 评分、AI 伴侣和错题归因。

- 2026-05-23 10:42 CST 资源表达标签与 Trainer 表达评分验证：
- 资源治理执行：真实库已回填表达标签字段；质量报告为 `total=12019`、`distinct_fingerprints=12004`、`exact_duplicate_debt=15`、`missing_guidance=0`。
- 真实资源 API：`GET /api/resources?expression_tool=expr_tool_041&limit=2` 返回 200，资源项包含 `expression_tool_ids_json`、`expression_goal`、`expression_level`、`speech_act`、`mistake_pattern`、`recommended_drills_json`。
- API 合同测试：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_sample_and_resource_catalog_contracts_match_frontend tests/test_expression_api.py -q` 通过，并断言表达工具筛选与字段返回。
- 训练流测试：`.venv/bin/python -m pytest tests/test_training_flow.py::test_training_flow_smoke tests/test_expression_api.py -q` 通过，并断言 `expression_tool_scoring` 包含适配分、阶段、目标、推荐工具、练习步骤和原则。
- 规范检查：`.venv/bin/python -m ruff check backend/api/resources.py backend/database/resource_quality_governance.py backend/models/resource.py tests/test_catalog_profile_review_api.py` 通过；`.venv/bin/python -m ruff check backend/api/training.py backend/database/seed.py tests/test_training_flow.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `Resources-*.js` 与 `Trainer-*.js` chunk。
- 真实训练 API：`POST /api/training/compare` 返回 200，响应包含 `expression_tool_scoring.fit_score`、`recommended_tools`、`practice_steps`、`risk_notes`。
- 浏览器验证 `/resources?expression_tool=expr_tool_041`：显示 48 张资源卡、表达目标、推荐工具和常见错题；`hasUndefined=false`、`horizontalOverflow=false`。右侧目录在当前 1188px 视口按响应式规则隐藏，顶部/底部导航可见。
- 浏览器验证 `/trainer`：页面加载、题目与文本框可见；浏览器自动点击提交时控制层超时，未把提交后 UI 卡片可见性标记为已通过。本轮 Trainer 结果区以 API、type-check、build 和单测作为验收依据。

- 2026-05-23 10:58 CST 错题本表达工具三版改写验证：
- 单项训练流：`.venv/bin/python -m pytest tests/test_training_flow.py::test_training_flow_smoke -q` 通过，并断言错题卡包含 `expression_rewrite.target_goal`、`recommended_tools`、3 个 `rewrite_versions`、`transfer_drill` 和 `forbidden_moves`。
- 规范检查：`.venv/bin/python -m ruff check backend/api/training.py tests/test_training_flow.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `Mistakes-*.js` chunk。
- 真实 API：`GET /api/training/mistakes` 返回 20 条错题，首条 `expression_rewrite` 包含 `target_goal=引导深聊`、`primary_tool=轻调侃`、4 个推荐工具、低压承接/边界清晰/行动修复 3 个改写版本、迁移练习和 3 条禁区提醒。
- 综合回归：`.venv/bin/python -m pytest tests/test_training_flow.py::test_training_flow_smoke tests/test_catalog_profile_review_api.py::test_sample_and_resource_catalog_contracts_match_frontend tests/test_expression_api.py -q` 通过，4 passed。
- 执行边界：本轮没有新增表字段，`expression_rewrite` 为 API 派生结构；后续如需审计历史版本，可再持久化到 `mistake_log` 或独立 mistake rewrite version 表。

- 2026-05-23 11:14 CST AI 伴侣表达工具链验证：
- 后端专项：`.venv/bin/python -m pytest tests/test_training_flow.py::test_partner_simulation_degrades_safely_without_provider tests/test_training_flow.py::test_partner_ai_orchestrator_success_and_fallback_branches -q` 通过，覆盖未配置 provider 降级与 AI 编排成功路径的 `expression_chain`。
- 规范检查：`.venv/bin/python -m ruff check backend/api/training.py tests/test_training_flow.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `TrainerAI-*.js` chunk。
- 真实 API：`POST /api/training/partner/simulate` 返回 200；在当前 provider 响应缺少 `reply` 的情况下，系统返回 `source=rule_fallback:AI 响应缺少 reply`，但仍包含 `expression_chain.target_goal=引导深聊`、状态 `谨慎试探`、工具链 `场景化表达/轻调侃/留白沉默/距离调节`、`practice_prompt` 与 `risk_boundary`。
- 执行边界：本轮尚未把资源卡检索引用嵌入 AI 伴侣回复；下一步可接 `partner_resource_retrieval_context`。

- 2026-05-23 11:28 CST AI 伴侣资源检索上下文验证：
- 后端专项：`.venv/bin/python -m pytest tests/test_training_flow.py::test_partner_simulation_degrades_safely_without_provider tests/test_training_flow.py::test_partner_ai_orchestrator_success_and_fallback_branches -q` 通过，断言未配置 provider 和 AI 成功路径均返回 `related_resources`。
- 规范检查：`.venv/bin/python -m ruff check backend/api/training.py tests/test_training_flow.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `TrainerAI-*.js` chunk。
- 真实 API：`POST /api/training/partner/simulate` 返回 `related_count=3`，前两条资源包含 `id/title/type/category/scene/expression_goal/quality_score/source_title/source_url/usage_tip/reason`，匹配原因包括 `边界`、`情绪流动`。
- 执行边界：资源推荐为 SQLite 本地检索，不抓取第三方全文；页面跳转使用资源海洋 query 入口。

- 2026-05-23 11:38 CST AI 伴侣近期错题记忆上下文验证：
- 后端专项：`.venv/bin/python -m pytest tests/test_training_flow.py::test_partner_simulation_degrades_safely_without_provider tests/test_training_flow.py::test_partner_ai_orchestrator_success_and_fallback_branches -q` 通过，断言 provider 降级和 AI 成功路径均返回 `mistake_memory`。
- 规范检查：`.venv/bin/python -m ruff check backend/api/training.py tests/test_training_flow.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `TrainerAI-*.js` chunk。
- 真实 API：`POST /api/training/partner/simulate` 在当前 provider 返回非 JSON/缺 reply 时降级为 `rule_fallback:AI 响应缺少 reply`，仍返回 `memory_cards=3`、`weak_dimensions=3`、`next_focus` 和首条错题 `review_focus=对话关闭 · 连接延展`。
- 浏览器验证 `/trainer-ai`：页面显示 AI 训练伴侣与 provider 状态，`hasUndefined=false`、`hasNaN=false`、`overflow=false`。
- 执行边界：错题记忆为 SQLite 本地派生结构，尚未把 memory 摘要持久化到 `practice_events`；当前事件仍保留回复、状态、安全和建议，错题记忆可由主真源重算。

- 2026-05-23 11:49 CST AI Provider 包裹 JSON 响应修复验证：
- Provider 专项：`.venv/bin/python -m pytest tests/test_ai_provider_safety.py::test_chat_json_recovers_json_object_wrapped_in_provider_text tests/test_ai_provider_safety.py::test_chat_json_embedded_json_parser_respects_braces_inside_strings tests/test_ai_provider_safety.py::test_openai_compatible_chat_json_success tests/test_ai_provider_safety.py::test_chat_json_non_json_content_returns_raw_text -q` 通过。
- 规范检查：`.venv/bin/python -m ruff check backend/ai/provider_client.py tests/test_ai_provider_safety.py` 通过。
- strict 类型检查：`.venv/bin/python -m mypy backend/ai/provider_client.py --strict` 通过。
- 修复范围：`chat_json()` 能从“说明文字 + JSON 对象 + 尾巴”中恢复结构化对象，并能处理 JSON 字符串字段内部的花括号；纯非 JSON 仍返回 `raw_text`，保持原降级语义。
- 执行边界：本轮只修 provider 文本包裹 JSON 的恢复能力；尚未做训练伴侣 response schema 字段别名归一化。

- 2026-05-23 11:58 CST 训练伴侣 AI 响应字段归一化验证：
- 后端专项：`.venv/bin/python -m pytest tests/test_training_flow.py::test_partner_ai_orchestrator_success_and_fallback_branches -q` 通过，覆盖标准 `reply/score/suggestions`、别名 `message/rating/advice`、provider not-ok 和缺 reply fallback。
- 规范检查：`.venv/bin/python -m ruff check backend/api/training.py tests/test_training_flow.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 验证结果：别名响应会被归一为 `source=ai_orchestrator`、`reply=我听见你没有急着推我...`、`score=84`、`suggestions=[保留低压节奏, 下一句只问一个轻问题]`，不再触发缺 reply 降级。
- 执行边界：本轮是字段别名与类型归一化；真实 provider 成功率仍需要 live probe policy 允许后继续观测。

- 2026-05-23 12:58 CST Provider 成功契约与近重复治理动作验证：
- Provider 成功契约专项：`.venv/bin/python -m pytest tests/test_analytics_api.py::test_ai_provider_success_contract_reports_shape_gaps_without_payload_leakage tests/test_analytics_api.py::test_analytics_center_includes_provider_probe_readiness -q` 通过。
- Provider 成功契约规范：`.venv/bin/python -m ruff check backend/api/analytics.py tests/test_analytics_api.py` 通过。
- Provider 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 真实 API：`GET /api/analytics/center?limit=20` 返回 `success_contract.summary.structured_success_rate`、`contract_gaps` 和 `quality_gate`。
- 资源近重复治理专项：`.venv/bin/python -m pytest tests/test_vector_index.py::test_resource_similarity_action_quarantines_variants_without_deleting_content tests/test_vector_index.py::test_resource_similarity_route_is_registered -q` 通过。
- 资源近重复规范：`.venv/bin/python -m ruff check backend/api/resources.py tests/test_vector_index.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `Governance-*.js` chunk。
- 数据库健康：`create_db_and_tables()` 后 `audit_schema(engine)` 返回 `status=ok`，缺表/缺列为空。
- 真实 API dry-run：`POST /api/resources/similarity/action` 对资源 `[8036,8033]` 返回 `dry_run=true`、`to_status=quarantine`、`reason_hash=sha256:...`、`content_deleted=false`、`raw_source_text_saved=false`。
- 浏览器验证 `/governance`：可见“近重复资源队列”“隔离变体预演”“隔离低质变体”“请求复审”；`hasUndefined=false`、`hasNaN=false`、`overflow=false`。

- 2026-05-23 13:10 CST 近重复资源重写补位验证：
- 后端专项：`.venv/bin/python -m pytest tests/test_vector_index.py::test_resource_similarity_rewrite_batch_creates_project_original_replacements tests/test_vector_index.py::test_resource_similarity_action_quarantines_variants_without_deleting_content -q` 通过。
- 规范检查：`.venv/bin/python -m ruff check backend/api/resources.py tests/test_vector_index.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 真实 API dry-run：`POST /api/resources/similarity/rewrite-batch` 返回 `dry_run=true`、`drafts[0].content` 包含“场景 / TA说 / 常见失误 / 更好回应 / 情绪信号 / 边界与同意 / 练习任务”，`project_original_only=true`、`third_party_full_text_saved=false`。
- 浏览器验证 `/governance`：可见“重写补位预演”“生成补位”和近重复队列，`hasUndefined=false`、`hasNaN=false`、`overflow=false`。
- Commander 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；报告提示导入质量 `auto_repairable_fields=9`，需要后续安全回补。

- 2026-05-23 13:13 CST 导入质量安全元数据回补验证：
- dry-run：`POST /api/evolution/import-quality/repair-plan {"limit":1000,"dry_run":true}` 返回 samples `source_trace_json=3/quality_json=3`、resources `applicable_scene=3/usage_tip=27/emotional_tone_json=27`、knowledge `source_metadata_json=3`。
- apply：`POST /api/evolution/import-quality/repair-plan {"limit":1000,"dry_run":false}` 返回 `updated.samples=3`、`updated.resources=27`、`updated.knowledge_entries=3`，回填原则明确不保存敏感原文或第三方全文。
- 复查：`GET /api/evolution/import-quality` 返回 `quality_score=75.0`、`quality_debt.auto_repairable_fields=0`、`manual_review_issues=88`、`resolved_issues=12`。
- 专项测试：`.venv/bin/python -m pytest tests/test_learning_pipeline_api.py::test_import_quality_repair_plan_dry_run_and_apply -q` 通过。
- 规范检查：`.venv/bin/python -m ruff check backend/api/evolution.py tests/test_learning_pipeline_api.py` 通过。
- 数据库健康：`audit_schema(engine)` 返回 `status=ok`、`integrity_check=ok`、缺表/缺列为空。
- Commander 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；import quality 状态为 `manual_review_required`，剩余 88 active issue 需要来源级治理。

- 2026-05-23 13:21 CST Reviewed 发布候选泛内容门禁验证：
- 共享库测试资产清理：已将 `rewrite:similarity-rewrite-*` 测试补位资源置为 `quarantine`，避免测试生成物进入发布候选池。
- 后端专项：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_reviewed_asset_publish_candidates_are_auditable tests/test_catalog_profile_review_api.py::test_legacy_generic_knowledge_is_not_publish_ready_without_curation tests/test_catalog_profile_review_api.py::test_reviewed_asset_action_confirm_withdraw_and_request_review_are_audited -q` 通过。
- 规范检查：`.venv/bin/python -m ruff check backend/api/evolution.py tests/test_catalog_profile_review_api.py` 通过。
- 真实 API：`GET /api/evolution/reviewed-assets/publish-candidates?limit=20` 返回 `total=40`、`publish_ready=20`；扩大到回归审计窗口后泛 legacy 内容被 blocking，Commander 审计中 publish-ready 从 20 收紧为 10。
- Commander 回归审计：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；`reviewed_publish_candidates.publish_ready=10`，候选首项为真实训练资源而非 legacy/manual 泛章节。

- 2026-05-23 13:31 CST 资源发布具体性门禁与误发布召回验证：
- 后端专项：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_short_generic_resource_is_not_publish_ready_without_concrete_practice_evidence tests/test_catalog_profile_review_api.py::test_reviewed_asset_action_confirm_withdraw_and_request_review_are_audited -q` 通过。
- 发布治理全文件：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py -q` 通过，10 passed。
- 规范检查：`.venv/bin/python -m ruff check backend/api/evolution.py tests/test_catalog_profile_review_api.py` 通过。
- 真实 API：`GET /api/evolution/reviewed-assets/publish-candidates?limit=20` 返回 `publish_ready=0`、`total=40`；前列 legacy/manual 条目和短句资源均携带 `quality_signal.blocks`，不会被确认发布。
- 共享库状态复查：71-80 号短句资源均不再是 `published`；本轮验证插入的 `generic-resource-*`、`publishable-resource-*`、`publishable-debug-*` 已通过治理动作退回 `draft`，未删除内容并留下审计日志。
- 执行边界：本轮收紧发布门禁，不把现有短句资源从数据库删除；它们仍可作为待策展素材，后续应通过重写补位生成具体案例后再进入 reviewed/published。

- 2026-05-23 13:41 CST 资源具体化多样补位发布批次验证：
- 召回操作：第一批低多样性补位资源 `12284-12307` 已通过 `POST /api/resources/similarity/action` 置为 `quarantine`，返回 `content_deleted=false`、`default_listing_hides_quarantine=true`。
- 重写多样性 dry-run：24 条低具体性 reviewed 资源生成 24 条草案，主题基数为 18，覆盖沉默陪伴、失望修复、越界修复、初次邀约、复联、道歉、表白承接、吃醋非控制、忙碌期协议等。
- 真实 apply：`POST /api/resources/similarity/rewrite-batch` 创建 24 条 `project_original:resource_similarity_rewrite` 补位资源，并把原资源 quarantine；随后通过 `POST /api/evolution/reviewed-assets/action` 逐条确认发布。
- 状态复查：最近 24 条已发布项目原创补位资源有 18 个不同主题；第一批 `12284-12307` 均为 quarantine。
- 后端专项：`.venv/bin/python -m pytest tests/test_vector_index.py::test_resource_similarity_rewrite_batch_creates_project_original_replacements tests/test_vector_index.py::test_resource_similarity_rewrite_batch_uses_diverse_scenarios_for_larger_batches tests/test_catalog_profile_review_api.py::test_short_generic_resource_is_not_publish_ready_without_concrete_practice_evidence tests/test_catalog_profile_review_api.py::test_reviewed_asset_action_confirm_withdraw_and_request_review_are_audited -q` 通过。
- 规范检查：`.venv/bin/python -m ruff check backend/api/resources.py backend/api/evolution.py tests/test_vector_index.py tests/test_catalog_profile_review_api.py` 通过。

- 2026-05-23 13:45 CST 资源页测试资产可见性治理验证：
- 共享库清理：`POST /api/resources/similarity/action` 对 40 条 active `source=pytest` 资源执行 quarantine，返回 `content_deleted=false`。
- 后端专项：`.venv/bin/python -m pytest tests/test_vector_index.py::test_resource_similarity_queue_groups_review_candidates tests/test_vector_index.py::test_resource_similarity_action_quarantines_variants_without_deleting_content tests/test_vector_index.py::test_resource_similarity_rewrite_batch_uses_diverse_scenarios_for_larger_batches -q` 通过。
- 规范检查：`.venv/bin/python -m ruff check tests/test_vector_index.py backend/api/resources.py` 通过。
- 真实 API：`GET /api/resources?source=pytest&limit=5` 返回 `total=0`；`GET /api/resources?mission_axis=boundary_consent&limit=20` 和 `conflict_repair` 首页来源均不包含 `pytest`。
- 执行边界：本轮只是可见性治理，不删除测试资产；后续测试生成物会在测试内自动置为 quarantine。

- 2026-05-23 14:50 CST 多记录页人性化目录、筛选建议与卡片内详情验证：
- 后端专项：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_sample_and_resource_catalog_contracts_match_frontend tests/test_vector_index.py::test_resource_similarity_route_is_registered -q` 通过，2 passed。
- 规范检查：`.venv/bin/python -m ruff check backend/api/resources.py tests/test_catalog_profile_review_api.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 真实浏览器验证 `/resources`：右侧“本页目录”为 sticky，移除“到顶部/到底部”；关键词/分类/标签/来源/表达工具/表达目标 datalist 均来自数据库建议，数量分别为 160/144/160/25/34/7；`overflow=false`。
- 真实浏览器验证 `/surf`：右侧“来源目录”为 sticky，来源标题为可点击外链，`overflow=false`。
- 真实浏览器验证 `/expression#expression-tool-expr_tool_015`：hash 自动展开工具卡片内详情，显示“微步骤 / 风险边界 / 更好回应”；右侧“工具目录”为 sticky，`overflow=false`。
- 浏览器验证期间出现 Codex 浏览器插件 Statsig/Cloudflare 外部网络日志，与本项目页面代码无关；项目页面 DOM 检查未发现横向溢出或顶部/底部跳转按钮残留。

- 2026-05-23 15:05 CST 资源详情页与筛选 URL 可恢复流验证：
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成 `ResourceDetail-*.js` 和更新后的 `Resources-*.js`。
- 后端契约：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_sample_and_resource_catalog_contracts_match_frontend -q` 通过，确认 `/api/resources/{id}` 详情契约仍可用。
- 浏览器验证 `/resources`：默认列表存在 96 个 `/resources/:id` 详情链接，卡片含“加入训练”和“错题改写”，`overflow=false`。
- 浏览器验证 URL 状态：`/resources?q=边界&category=冲突修复&page=2` 保留查询参数，分类筛选输入存在，无顶部/底部跳转按钮，`overflow=false`。
- 浏览器验证 `/resources/1?q=边界&category=冲突修复&page=2`：详情页显示“详情目录”“来源与导读”“结构化信息”“加入训练”“错题改写”；返回资源海洋链接为 `/resources?q=边界&category=冲突修复&page=2`；`overflow=false`。

- 2026-05-23 15:18 CST 资源详情与多记录页世界级 smoke 门禁验证：
- 自动前端 smoke：`cd frontend && npm run smoke:world` 通过，`checked=38`，报告路径 `frontend/output/smoke/report.json`。
- smoke 新增覆盖：Resources、ResourceDetail、Expression、ResourceSurf 桌面/移动端；同时保持 TrainerAI 交互和训练失败路径覆盖。
- smoke mock 合约补齐：resources list/detail/filter/source/similarity、expression tools/chains/recommend/detail、training partner provider-status、AI 伴侣 expression_chain/related_resources/mistake_memory。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 规范检查：`.venv/bin/python -m ruff check backend/api/resources.py tests/test_catalog_profile_review_api.py` 通过。
- 备注：首次扩展 smoke 暴露出历史 mock 缺口（Provider success contract/probe readiness、resource similarity summary、partner provider status），已修复 mock 合约后通过。

- 2026-05-23 15:45 CST 资源进入训练上下文闭环验证：
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `Trainer-*.js` 与 smoke 报告。
- 后端契约：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_sample_and_resource_catalog_contracts_match_frontend -q` 通过，确认 `/api/resources/{id}` 详情契约仍可供 Trainer 读取。
- 自动前端 smoke：`cd frontend && npm run smoke:world` 通过，`checked=40`，新增桌面/移动端 `TrainerResourceContext` 交互覆盖。
- smoke 断言：`/trainer?resource_id=1&q=边界&category=冲突修复&page=2` 显示“来自资源海洋的训练上下文”，点击“用资源提示预填回应”后文本框包含场景、表达目标和常见失误；“回看资源”指向 `/resources/1`；点击“只做普通训练”会移除 `resource_id` 并保留 `q/category` 筛选 query。
- 执行边界：本轮没有改数据库、未新增外部抓取，也未把 AI Provider 成功率说成已解决；仅把资源阅读到训练实践的前端闭环做实并纳入回归门禁。

- 2026-05-23 15:58 CST 资源错题改写上下文闭环验证：
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `Mistakes-*.js`、`Resources-*.js` 与 `ResourceDetail-*.js`。
- 后端契约：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_sample_and_resource_catalog_contracts_match_frontend -q` 通过，资源详情契约仍支持错题页上下文读取。
- 自动前端 smoke：`cd frontend && npm run smoke:world` 通过，`checked=42`，新增桌面/移动端 `MistakeResourceContext` 交互覆盖。
- smoke 断言：`/mistakes?resource_id=1&q=过早解释` 显示“来自资源海洋的错题改写上下文”，可见资源标题、过早解释、修复信任和失望修复；“回看资源”指向 `/resources/1`；“带入训练”指向携带同一资源的 Trainer；点击“只看全部错题”移除 `resource_id` 且保留 `q=过早解释`。
- 执行边界：本轮仍未新增外部抓取或修改数据库；只强化资源、错题、训练之间的前端转化闭环和回归门禁。

- 2026-05-23 16:03 CST 资源上下文统一 Query 契约验证：
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，构建新增 `useResourceContext-*.js` 共享 chunk。
- 自动前端 smoke：`cd frontend && npm run smoke:world` 通过，`checked=42`；资源进入 Trainer 与资源进入 Mistakes 的桌面/移动端交互仍全部通过。
- 重构范围：`Trainer.vue` 与 `Mistakes.vue` 共用 `useResourceContextFromRoute`，统一 `resource_id` 解析、资源加载、错误回调和清除上下文保留 query 的行为。
- 执行边界：本轮是维护性收束，没有改变数据库、后端接口或外部抓取策略。

- 2026-05-23 16:18 CST 设置页真实数据导出闭环验证：
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `Settings-*.js`。
- 自动前端 smoke：`cd frontend && npm run smoke:world` 通过，`checked=46`；新增 Settings 页面路由覆盖和 `SettingsExport` 桌面/移动端交互覆盖。
- smoke 断言：点击“数据 -> 导出”后页面显示“导出包已生成”“校验指纹”“个人资料/错题记录/训练摘要”，保存文件链接为 `blob:`，download 文件名包含 `relationship-training-export`。
- 真实浏览器验证：`/settings` 数据页点击“导出”后出现导出结果区，包含 SHA-256/降级 checksum 指纹、覆盖范围和 `relationship-training-export-2026-05-23.json` 保存文件链接，`horizontalOverflow=0`。
- 执行边界：导出包在浏览器本地生成，不上传文件；本轮没有实现重置进度/注销账户后端删除能力，这两个危险操作仍需单独治理。

- 2026-05-23 16:36 CST 表达工具箱搜索建议与引导闭环验证：
- 后端专项：`.venv/bin/python -m pytest tests/test_expression_api.py -q` 通过，覆盖表达工具种子、列表、详情、推荐，并断言 `q=冲突` 与 `q=退路` 能检索到具体工具。
- 规范检查：`.venv/bin/python -m ruff check backend/api/expression.py tests/test_expression_api.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 自动前端 smoke：`cd frontend && npm run smoke:world` 通过，`checked=48`；新增 `ExpressionSearchSuggestions` 桌面/移动端交互覆盖。
- smoke 断言：`/expression` 存在 `input[list="expression-search-suggestions"]`、datalist 选项、推荐分组、引导文案；点击“情绪标注”后输入框值同步、筛选结果包含“先命名对方可能的感受”，并显示“当前搜索 / 清除”。
- 真实浏览器验证：`/expression` 搜索框 placeholder 为“可选下拉，也可手输：情绪标注、PREP、退路、冲突...”，datalist 选项数为 46，包含“情绪标注”“PREP模型”，页面可见“工具 / 场景 / 目标 / 公式”分组与“不确定搜什么时”引导。
- 执行边界：本轮未新增数据库内容、未改变表达工具安全原则；只是让已有 SQLite 表达工具更容易被发现和检索。

- 2026-05-23 16:52 CST 多记录页目录折叠释放布局空间验证：
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `PageTocSidebar`、`Resources`、`ResourceSurf`、`ResourceDetail`、`Expression` chunks。
- 自动前端 smoke：`cd frontend && npm run smoke:world` 通过，`checked=51`；新增 3 条桌面 `TocCollapseLayout` 回归覆盖。
- smoke 断言：`/resources`、`/surf`、`/resources/1` 点击“折叠目录”后 `280px/300px` 目录列消失，出现“展开目录”按钮，按钮距右侧不超过 40px，横向溢出不超过 2px。
- 真实浏览器验证 `/resources`：折叠前 `gridTemplateColumns=973px 280px`，折叠后无 280px 右列，主内容为 `1277px` 单列，展开按钮距右侧约 25px，`overflow=0`。
- 真实浏览器验证 `/surf`：折叠前 `977px 280px`，折叠后无 280px 右列，主内容为 `1277px` 单列，展开按钮距右侧约 25px，`overflow=0`。
- 真实浏览器验证 `/resources/1`：折叠前 `973px 280px`，折叠后无 280px 右列，主内容为 `1277px` 单列，展开按钮距右侧约 25px，`overflow=0`。
- 真实浏览器验证 `/expression`：折叠后展开按钮距右侧约 25px，无横向溢出；右栏业务内容“工具链推荐”仍可见，因此该页保留右栏布局而只浮动目录按钮。
- 执行边界：本轮只修改目录折叠布局与回归门禁，不改数据库、不改资源内容、不改变分页或筛选语义。

- 2026-05-23 17:10 CST 设置页 Markdown 可读导出与保存位置提示验证：
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `Settings-*.js`。
- 自动前端 smoke：`cd frontend && npm run smoke:world` 通过，`checked=51`；SettingsExport 断言已切换到 Markdown 导出体验。
- smoke 断言：点击“数据 -> 导出”后显示“Markdown 导出已生成”、`.md` 文件名、“选择位置保存”“下载到默认目录”、校验指纹、个人资料/错题记录/训练摘要覆盖范围；默认下载链接为 `blob:`，download 文件名为 `relationship-training-export-2026-05-23.md`。
- 可读性验证：导出内容由 `buildExportMarkdown()` 生成，包含概览表、个人资料、偏好设置、训练摘要、错题记录、到期复习和原始审计 JSON 代码块。
- 真实浏览器备注：in-app browser 旧标签触发原生保存/下载交互后 CDP 点击被阻塞；已避免导出按钮自动打开系统保存窗口，改为用户主动点击“选择位置保存”时才打开，自动化最终以 smoke 作为交互门禁。
- 执行边界：本轮没有改变后端数据，也没有上传导出文件；导出仍完全在浏览器本地生成。

- 2026-05-23 17:25 CST 设置页每日提醒真实本地通知验证：
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，新增 `localReminder` chunk 并更新 `Settings` 与主入口。
- 自动前端 smoke：`cd frontend && npm run smoke:world` 通过，`checked=53`；新增桌面/移动端 `SettingsReminder` 覆盖。
- smoke 断言：设置页偏好 tab 显示“每日提醒 / 提醒时间 / 测试提醒”，默认时间为 `20:00`，页面包含“浏览器本地通知”“需要允许通知权限”“页面或浏览器保持打开”“不是手机后台推送”，且无横向溢出。
- 功能边界验证：`main.ts` 启动时调用 `scheduleDailyTrainingReminder(loadReminderPreferences())`；保存偏好时调用 `requestAndScheduleDailyTrainingReminder()`；测试按钮调用 `sendTestTrainingReminder()`。
- 执行边界：这是浏览器本地通知，不是 Service Worker/Push API 后台推送；页面或浏览器关闭后无法保证触发，页面已明确说明。

- 2026-05-23 17:48 CST 我的档案真实训练证据联动验证：
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `Profile-*.js` 和 world smoke 脚本。
- 自动前端 smoke：`cd frontend && npm run smoke:world` 通过，`checked=57`；新增 `/profile` 路由覆盖和桌面/移动端 `ProfileEvidence` 交互覆盖。
- smoke 断言：`/profile` 显示“计算依据”、`/api/profile`、`/api/training/radar`、`/api/training/summary/week`，并显示 mock 真实值 `边界焦虑`、`128 个`、近 7 天训练 `11`、近 7 天活跃 `4`、平均得分 `76`。
- 回归断言：页面不再出现旧固定统计 `156`，不再展示旧固定自我觉察“面对冲突时倾向于回避，事后才反思如何改进”。
- 真实 in-app browser 复查：`http://127.0.0.1:3000/profile` 标题为“我的档案 - 关系动力学全息”，`overflow=0`，页面含“计算依据”和真实数据源说明，旧硬编码文案与 `156` 均不存在。
- 执行边界：当前仍没有终身累计训练、连续签到和个人已完成学习量专用后端口径；页面已改为不展示这些不可证明指标，并在“计算依据”里说明边界。

- 2026-05-23 18:12 CST 表达工具箱与八阶路径学习脚手架升级验证：
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `Expression-*.js` 与 `Path-*.js`。
- 自动前端 smoke：`cd frontend && npm run smoke:world` 通过，`checked=59`；扩展 `ExpressionSearchSuggestions` 并新增桌面/移动端 `PathLearningScaffold` 覆盖。
- smoke 断言：`/expression` 存在“检索与筛选”“重置筛选”“应用筛选”，推荐词分组包含“工具概念 / 使用场景 / 表达目标 / 表达公式”，工具链推荐位于检索区下方并可按当前条件推荐。
- smoke 断言：点击表达工具详情后显示“概念定义 / 核心原则 / 实践方法 / 适用场景 / 迁移练习”，确保卡片不再只是标题和简短描述。
- smoke 断言：`/path` 显示“这条路线到底在训练什么”，包含“先证据后判断 / 先安全后张力”，节点内容包含“概念定义 / 核心原则 / 实践方法 / 适用场景 / 常见误区 / 低质量做法 / 更好做法 / 本阶练习题”。
- 真实浏览器备注：本轮最终 in-app browser 自动导航到 `127.0.0.1:3000` 时被客户端规则返回 `net::ERR_BLOCKED_BY_CLIENT`；独立 Playwright smoke 已在 Chromium 环境完成桌面和移动端回归验证。

- 2026-05-23 18:31 CST 资源海洋学习拆解卡升级验证：
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过，生成更新后的 `Resources-*.js` 与 `ResourceDetail-*.js`。
- 自动前端 smoke：`cd frontend && npm run smoke:world` 通过，`checked=61`；新增桌面/移动端 `ResourceLearningScaffold` 覆盖。
- smoke 断言：`/resources` 列表卡片包含“学习拆解 / 概念定义 / 核心原则 / 实践方法 / 练习任务”，并展示“低质量回应 / 更好回应”对比。
- smoke 断言：`/resources/1` 详情页包含独立“学习拆解”章节，覆盖概念定义、核心原则、实践方法、适用场景、低质量做法、更好做法和练习任务。
- smoke 断言：资源页展示“有原文入口 / 项目原创训练卡 / 结构化导读卡”等来源边界，详情页说明“结构化学习拆解，不复制第三方全文”或“不伪装为外部原文”。
- 执行边界：本轮未新增外部抓取，也未把摘要冒充原文；只是基于已有数据库字段和内容正文生成可学习展示结构。

- 2026-05-24 00:25 CST 导入质量 issue 分桶治理验证：
- 后端专项：`.venv/bin/python -m pytest tests/test_learning_pipeline_api.py -q` 通过，20 passed；新增 triage 测试确认 warning-only 来源进入 `batch_closable`，error 来源进入 `source_review_required`，投影分不低于当前分。
- 后端治理门禁：`.venv/bin/python -m pytest tests/test_database_schema_guard.py tests/test_commander.py -q` 通过，23 passed。
- 规范检查：`.venv/bin/python -m ruff check backend/api/evolution.py backend/database/schema_guard.py tools/commander.py tests/test_learning_pipeline_api.py tests/test_commander.py` 通过。
- 指挥官回归：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；导入质量仍诚实显示 `quality_score=75.0`、`active_issues=86`，没有被自动刷掉。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过；`cd frontend && npm run smoke:world` 通过，`checked=61`。
- 执行边界：本轮只增加可审计治理分桶和分数投影，不自动关闭历史 issue，不存储第三方全文，不回显 resolution prose。

- 2026-05-24 00:45 CST Reviewed 精品训练卡发布候选补位验证：
- 后端专项：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py tests/test_vector_index.py -q` 通过，19 passed；覆盖精品批次 dry-run/执行、publish-ready 统计、低质资源阻断、默认资源列表隐藏 pytest 与草稿。
- 规范检查：`.venv/bin/python -m ruff check backend/api/evolution.py backend/api/resources.py tests/test_catalog_profile_review_api.py tests/test_vector_index.py` 通过。
- 数据执行：真实运行 `/api/evolution/reviewed-assets/boutique-batch` 等价调用，创建 5 条、复用 3 条，批次 8 条均 publish-ready；随后 safe repair plan 更新 samples/resources/knowledge 元数据并把 `auto_repairable_fields` 清回 0。
- 指挥官回归：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；`reviewed_publish_candidates.publish_ready=27`，top candidates 为项目原创精品训练卡，质量门禁仍要求人工确认。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过；`cd frontend && npm run smoke:world` 通过，`checked=61`。
- 执行边界：精品卡为项目原创训练内容，不抓取、不保存第三方全文；低质短泛资源和 legacy/manual 泛化知识没有被放行。

- 2026-05-24 00:57 CST 资源近重复与练习完整度可观测化验证：
- 后端专项：`.venv/bin/python -m pytest tests/test_vector_index.py tests/test_catalog_profile_review_api.py -q` 通过，21 passed；覆盖相似队列只扫描 reviewed/published、draft/quarantine 噪音不入队、质量报告输出感知重复与练习完整度。
- 规范检查：`.venv/bin/python -m ruff check backend/core/vector_index.py backend/database/resource_quality_governance.py backend/api/resources.py tests/test_vector_index.py tests/test_catalog_profile_review_api.py` 通过。
- 真实质量报告：`exact_duplicate_debt=178`；`duplicate_families=933`；`largest_family_size=36`；`first_page_max_continuous_family_run=1`；`first_page_runs_over_three=0`；`thin_cards=7939`；`avg_mission_alignment=87.2`。
- 指挥官回归：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；测试数据产生的 `auto_repairable_fields=6` 已通过 safe repair plan 回到 0。
- 前端门禁：`cd frontend && npm run smoke:world` 通过，`checked=61`。
- 执行边界：本轮没有删除资源内容；近重复治理仍通过 quarantine/rewrite/action 和 audit log 管理，而不是静默清库。

- 2026-05-24 01:00 CST 多记录页面目录与检索体验验收：
- 前端门禁：`cd frontend && npm run type-check && npm run build && npm run smoke:world` 通过，`checked=61`。
- smoke 覆盖：`TocCollapseLayout` 覆盖 `/resources`、`/surf`、`/resources/1`；`ExpressionSearchSuggestions` 覆盖表达搜索建议；`ResourceLearningScaffold` 覆盖资源卡学习拆解；`PathLearningScaffold` 覆盖路径页课程脚手架。
- 后端关联验收：`.venv/bin/python -m pytest tests/test_expression_api.py tests/test_training_flow.py tests/test_learning_pipeline_api.py -q` 通过，39 passed。
- 代码审计：`PageTocSidebar` 被 Resources、ResourceSurf、ResourceDetail、Expression 复用；Resources 与 Expression 均存在 datalist 建议源。
- 执行边界：本轮以验收归档为主，没有重写页面结构或引入新的 UI 框架。

- 2026-05-24 01:08 CST P1 学习与证据层验收归档：
- 表达/路径/训练后端：`.venv/bin/python -m pytest tests/test_expression_api.py tests/test_training_flow.py tests/test_learning_pipeline_api.py -q` 通过，39 passed。
- 向量校准：`.venv/bin/python -m pytest tests/test_vector_index.py -q` 通过；`.venv/bin/python -m mypy backend/core/vector_index.py --strict` 通过；`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过，`vector_recall.top10_recall=0.75`。
- 前端体验：`cd frontend && npm run type-check && npm run build && npm run smoke:world` 通过，覆盖 Expression、Path、Profile、Settings、TrainerAI 等关键体验。
- 数据卫生：测试产生的 `auto_repairable_fields=3` 已通过 safe repair plan 回到 0。
- 执行边界：本轮归档基于已存在并验证通过的实现，没有为凑状态新增伪功能。

- 2026-05-24 01:24 CST P2 链接健康、批次回滚与安全红队验证：
- 后端专项：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py tests/test_learning_pipeline_api.py tests/test_ai_provider_safety.py -q` 通过，60 passed。
- 新增链接健康覆盖：失效来源检查写入 `pipeline_run_logs`，返回 `status/http_code/redirect/last_checked_at`，日志明确 `body_saved=false`，并把对应 published 资源降级为 draft。
- 新增批次回滚覆盖：`/api/evolution/import-batches/rollback-plan` 返回影响范围、planned transitions、rule/prompt version、duplicate/publish/quarantine/open issue 指标，且测试确认原知识/资源/issue 状态未被修改。
- 新增安全红队覆盖：`SafetyGuardian` 对侵犯同意请求硬阻断并返回替代练习；高张力资源缺少边界/同意证据时不能 publish-ready，补齐可拒绝/不施压/边界证据后可通过。
- 规范检查：`.venv/bin/python -m ruff check backend/api/resources.py backend/api/evolution.py backend/ai/safety.py tests/test_catalog_profile_review_api.py tests/test_learning_pipeline_api.py tests/test_ai_provider_safety.py` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过；`cd frontend && npm run smoke:world` 通过，`checked=61`。
- 指挥官回归：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；导入 `auto_repairable_fields=0`，`reviewed_publish_candidates.publish_ready=25`，AI provider 仍暴露 DeepSeek HTTP 400/403 外部配置/授权债。
- 类型检查备注：尝试 `.venv/bin/python -m mypy backend/api/resources.py backend/api/evolution.py backend/ai/safety.py --strict` 时暴露大量既有 SQLModel/泛型类型债，不作为本轮 P2 验收门槛；本轮没有进行大面积类型重构以避免偏离手术式修改原则。

- 2026-05-24 01:37 CST Zero-Gate 契约补齐与旧任务同步验证：
- 契约文件验证：`python3 -m json.tool docs/api_contract.json >/tmp/api_contract.valid.json` 通过；`docs/requirements_final.md`、`docs/high_level_design.md`、`docs/dependency_graph.md`、`docs/dependency.dot` 均存在且非空。
- 旧任务清单复核：`rg -n "^- \\[ \\]" docs/tasks.md` 当前只剩 4 个真实数据内容任务：300 条 reviewed/published 互动样本、1000 条候选样本、连接素材库重构、100 条 Gold samples。
- 新增机器可读 backlog：`docs/tasks/data_content_backlog.json` 已记录上述 4 项的目标、验收标准、执行步骤和验证命令。
- 前端门禁：`cd frontend && npm run type-check && npm run smoke:world` 通过，`checked=61`。
- 指挥官回归：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过，数据库健康、导入质量、发布候选、向量召回、Gold Set、AI 质量诊断均返回 passed。

- 2026-05-24 01:56 CST 数据内容 backlog 完成验证：
- 真实执行：`.venv/bin/python -m backend.database.data_content_governance` 通过，回填结果为 `candidate_samples_created=638`、`samples_promoted_reviewed=233`、`gold_samples_added=33`、`resources_reclassified=12300`。
- 最终核数：`interaction_samples=1008`、`reviewed_visible=304`、`draft_candidates=671`、`gold_samples=104`、`gold_versions=230`。
- 连接动作核数：破冰观察 7537、温和幽默 888、欣赏表达 18、修复句式 1706、边界表达 2148、退路式邀请 3。
- 新增专项测试：`.venv/bin/python -m pytest tests/test_data_content_governance.py -q` 通过，3 passed；覆盖 dry-run 不变更、治理目标达成、训练推荐忽略 draft。
- 训练链路：`.venv/bin/python -m pytest tests/test_training_flow.py -q` 通过，17 passed。
- 目录/资源/学习相关回归：`.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py::test_sample_and_resource_catalog_contracts_match_frontend tests/test_data_content_governance.py -q` 通过，3 passed；`.venv/bin/python -m pytest tests/test_learning_pipeline_api.py tests/test_vector_index.py -q` 通过，30 passed。
- 规范检查：`.venv/bin/python -m ruff check backend/database/data_content_governance.py backend/api/training.py backend/api/samples.py tests/test_data_content_governance.py` 通过。
- JSON 门禁：`python3 -m json.tool docs/tasks/data_content_backlog.json >/tmp/data_content_backlog.valid.json` 通过。
- 指挥官回归：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过，数据库健康 ok、导入质量通过、向量召回通过、Gold open conflicts 0、AI 质量诊断通过。
- 导入质量安全修复：执行 `import_quality_repair_plan(dry_run=false, limit=1000)` 后 `auto_repairable_fields=0`；剩余 `manual_review_issues=80` 不自动关闭。
- 残余风险：DeepSeek Provider 仍有外部 HTTP 400/403 高风险，当前本地请求形态通过诊断且 fallback 生效；需要账号区域、模型授权或供应商侧 live probe 排查。

- 2026-05-24 05:15 CST 最终审计与执行方案归档验证：
- 归档文件：`docs/tasks/final_audit_execution_plan_2026-05-24.md` 已创建，记录完整待办状态、执行方案、验收证据、不可自动关闭债务和后续执行口径。
- 待办扫描：`data_content_backlog.json` 为 4/4 completed；`next_stage_backlog.json` 为 13/13 completed；`commander_state.json` 为 108/108 completed、pending 0；`rg` 未发现未勾选、pending 或 in_progress。
- 数据库核数：interaction_samples 1008、training_ready 304、draft_candidates 671、gold 104、resources_ready 12317；六类连接素材均有数据。
- 指挥官回归：`.venv/bin/python -m tools.commander regression-audit --batch-limit 2` 通过；数据库健康 ok、Gold open conflicts 0、vector recall 0.75、import auto_repairable_fields 0。
- 边界说明：DeepSeek HTTP 400/403 和 80 个历史导入 issue 均不是当前可安全自动关闭的代码项，继续保留在运营债和人工复核通道。

- 2026-05-24 12:49 CST 阶元式心理沟通与场景化表达融合升级验证：
- 编译门禁：`.venv/bin/python -m py_compile backend/database/scene_empathy_worldclass_seed.py backend/api/knowledge.py` 通过。
- dry-run：`.venv/bin/python -m backend.database.scene_empathy_worldclass_seed --dry-run` 首次预计新增知识 9、工具链 5、资源 162；真实执行后再次 dry-run 显示知识更新 9、工具链更新 5、资源跳过 162，证明脚本幂等。
- 数据库门禁：`PRAGMA integrity_check=ok`；新增来源 `project_original:scene_empathy_worldclass_v1` 下知识 9、资源 162、缺失 blueprint 0；`source_metadata_json`、`sequence_json`、`case_blueprint_json` 均无坏 JSON。
- API 验证：`/api/knowledge/entries?q=阶元&limit=2` 返回“阶元 0：元意图”“阶元 1：场景观察”，learning 字段展示专属原则和方法；`/api/resources?q=阶元沟通&limit=2` 返回 total 162；`/api/expression/chains?scene=暧昧&limit=8` 返回新工具链。
- 前端门禁：`cd frontend && npm run type-check` 通过。
- 浏览器 smoke：Playwright 访问 `/knowledge`、`/expression?q=场景化表达`、`/resources?q=阶元沟通` 均命中新内容；表达工具箱显示工具 60、工具链 10，资源海洋显示 162 条阶元沟通资源。
- 服务状态：后端 8000 已重启到最新代码，PID 写入 `data/backend-8000.pid`，日志在 `data/backend-8000.log`。

- 2026-05-24 13:21 CST 深度舒适聊天与现实感受交替提问升级验证：
- 编译门禁：`.venv/bin/python -m py_compile backend/database/deep_comfort_chat_seed.py backend/api/expression.py backend/api/knowledge.py` 通过。
- dry-run：`.venv/bin/python -m backend.database.deep_comfort_chat_seed --dry-run` 首次预计新增知识 6、工具链 4、资源 90；真实执行后再次 dry-run 显示知识更新 6、工具链更新 4、资源跳过 90，证明脚本幂等。
- 数据库门禁：`PRAGMA integrity_check=ok`；新增来源 `project_original:deep_comfort_chat_v1` 下知识 6、资源 90、缺失 blueprint 0、content units 30；`source_metadata_json`、`sequence_json`、`case_blueprint_json` 均无坏 JSON。
- API 验证：`/api/knowledge/entries?q=现实感受交替&limit=3` 返回价值降噪、问细节、现实-感受交替提问；`/api/resources?q=深度舒适聊天&limit=2` 返回 total 90；`/api/expression/chains?q=现实感受交替&limit=5` 返回“现实感受交替深聊链”。
- 前端门禁：`cd frontend && npm run type-check` 通过。
- 浏览器 smoke：Playwright 访问 `/knowledge`、`/expression?q=现实感受交替`、`/resources?q=深度舒适聊天` 均命中新内容；表达页在该关键词下展示工具链 1，资源海洋展示 90 条深度舒适聊天资源。
- 服务状态：后端 8000 已重启到最新代码，PID 写入 `data/backend-8000.pid`。

- 2026-05-24 13:37 CST 功能模块选项卡模板标准化验证：
- JSON 门禁：`python3 -m json.tool docs/tasks/module_tab_templates.json >/tmp/module_tab_templates.valid.json` 通过。
- 前端门禁：`cd frontend && npm run type-check` 通过。
- 文件核验：`docs/功能模块选项卡结构模板规范.md` 161 行，`docs/tasks/module_tab_templates.json` 292 行，`frontend/src/components/ModuleTabs.vue` 54 行。
- 浏览器 smoke：Playwright 打开 `/settings`，检测到 4 个 `role=tab`，当前选中“账户”，并显示“管理头像、用户名、依恋风格和爱语。”摘要。
- 执行边界：本轮没有强行重构所有页面，只新增通用模板和在设置页做可验证示范，避免大面积 UI 回归。

- 2026-05-24 13:58 CST 世界级模块模板总则与机器校验：
- JSON 门禁：`python3 -m json.tool docs/tasks/module_tab_templates.json >/tmp/module_tab_templates.v2.valid.json` 通过。
- 模板校验：`.venv/bin/python tools/validate_module_tab_templates.py` 通过，确认每个 tab 具备必填字段、5W2H、对话模板和数据契约。
- 专项测试：`.venv/bin/python -m pytest tests/test_module_tab_templates.py -q` 通过，1 passed。
- 前端门禁：`cd frontend && npm run type-check` 通过。
- 执行边界：本轮聚焦模板规则和校验器，没有把所有页面一次性大改；后续页面、采集、数据库扩展可按该模板逐步实施。

- 2026-05-24 14:18 CST 需求与功能原则统一索引验证：
- 文档产出：新增 `docs/项目需求与功能原则统一索引.md`。
- 统一范围：文件明确 L0 最高目标、L1 产品需求契约、L2 架构/API/依赖、L3 功能原则与内容模板、L4 任务/审计/进度记录的层级关系。
- README 入口：README 已新增“需求与原则入口”，避免后续只从历史任务或阶段方案进入实现。
- 校验边界：本轮没有改业务代码、数据库或页面行为，只做需求/原则文档入口收口和验证。

- 2026-05-24 14:42 CST 核心内容页模块选项卡落地验证：
- 前端类型检查：`cd frontend && npm run type-check` 通过。
- 模板门禁：`.venv/bin/python tools/validate_module_tab_templates.py` 通过；`.venv/bin/python -m pytest tests/test_module_tab_templates.py -q` 通过，1 passed。
- 浏览器 smoke：Playwright 访问 `/resources?tab=source_boundary&q=四阶心理沟通`，检测到“来源边界” tab `aria-selected=true` 且页面包含“来源边界工作区”。
- 浏览器 smoke：Playwright 访问 `/expression?tab=tool_chains&q=现实感受交替`，检测到“工具链” tab `aria-selected=true` 且页面包含“工具链推荐”。
- 浏览器 smoke：Playwright 访问 `/knowledge?tab=five_w_two_h`，检测到“5W2H” tab `aria-selected=true` 且页面包含“5W2H 元问题工作区”。
- 执行边界：本轮只把统一模板落地到 `/resources`、`/expression`、`/knowledge` 三个核心内容页；未改数据库、API 或采集脚本。

- 2026-05-24 15:06 CST 训练闭环与来源页选项卡落地验证：
- 模板 JSON：`python3 -m json.tool docs/tasks/module_tab_templates.json >/tmp/module_tab_templates.valid.json` 通过。
- 模板门禁：`.venv/bin/python tools/validate_module_tab_templates.py` 通过；`.venv/bin/python -m pytest tests/test_module_tab_templates.py -q` 通过，1 passed。
- 前端类型检查：`cd frontend && npm run type-check` 通过。
- 生产构建：`cd frontend && npm run build` 通过。
- 浏览器 smoke：Playwright 访问 `/surf?tab=collection_strategy`，检测到“采集策略” tab `aria-selected=true`。
- 浏览器 smoke：Playwright 访问 `/trainer?tab=feedback`，检测到“七维反馈” tab `aria-selected=true`，且反馈空状态可见。
- 浏览器 smoke：Playwright 访问 `/mistakes?tab=mastery_evidence`，检测到“掌握证据” tab `aria-selected=true`。
- 执行边界：本轮只做 `/surf`、`/trainer`、`/mistakes` 的工作区归位和 URL 状态；未改数据库、API、评分逻辑或复习算法。

- 2026-05-24 15:31 CST 资源卡完整案例学习区验证：
- 前端类型检查：`cd frontend && npm run type-check` 通过。
- 生产构建：`cd frontend && npm run build` 通过。
- 浏览器 smoke：Playwright 访问 `/resources?q=第3阶拒绝评判` 并检查 `#resource-24158`，确认卡片包含“完整案例学习区 / 场景故事 / 完整对话 / 低质量回应 / 更好回应 / 练习与迁移”。
- 数据核验：`resource_library.id=24158` 已有 `case_blueprint_json`，包含 `setting/their_words/common_mistake/better_response/boundary_note/practice_task/transfer_scene/response_steps/variant_deltas`。
- 执行边界：本轮未搬运第三方全文、未改数据库、未改 API，只把已有结构化案例蓝图集中展示到列表卡片。

- 2026-05-24 15:42 CST 案例蓝图多视角回应与举一反三补强验证：
- 专项测试：`.venv/bin/python -m pytest tests/test_case_blueprint_enrichment.py -q` 通过，4 passed；覆盖蓝图字段补强、保留已有字段、dry-run 不改库、真实写入备份。
- dry-run：`.venv/bin/python -m backend.database.case_blueprint_enrichment --dry-run` 扫描 11892 条、预计更新 11892 条、坏 JSON 0。
- 真实执行：`.venv/bin/python -m backend.database.case_blueprint_enrichment` 扫描 11892 条、更新 11892 条、坏 JSON 0，并生成备份 `data/backups/relationship_training-before-case-blueprint-enrichment-20260524-152953.db`。
- 数据核验：`resource_library.id=24158` 的 `response_variants=5`、`perspective_examples=4`，`transfer_analysis.stable_principles[0]` 为“先承接一个可观察信号，再提出一个低压力问题。”；全库 11892 条蓝图均包含 `response_variants/perspective_examples/transfer_analysis`。
- 前端类型检查：`cd frontend && npm run type-check` 通过。
- 模板门禁：`.venv/bin/python tools/validate_module_tab_templates.py` 通过。
- 生产构建：`cd frontend && npm run build` 通过。
- 浏览器 smoke：Playwright 设置 `hasCompletedOnboarding=true` 后访问 `/resources?fresh=case-enrichment`，首张资源卡包含“完整案例学习区 / 多视角更好回应 / 举一反三分析 / 迁移不变原则”；访问 `/resources/24158?fresh=case-enrichment`，详情页包含“多视角更好回应 / 举一反三分析 / 迁移分析 / 常见误读风险 / 练习阶梯”。
- 执行边界：本轮补强为本地原创结构化分析，没有调用外部抓取或保存第三方全文。

- 2026-05-24 15:48 CST 更好回应上下文一致性修复验证：
- 专项测试：`.venv/bin/python -m pytest tests/test_contextual_response_repair.py tests/test_case_blueprint_enrichment.py -q` 通过，6 passed；覆盖社交蛋糕语境回应、历史记录修复、正文与蓝图同步更新。
- dry-run：`.venv/bin/python -m backend.database.contextual_response_repair --dry-run` 扫描 9 条、预计更新 9 条、坏 JSON 0。
- 真实执行：`.venv/bin/python -m backend.database.contextual_response_repair` 扫描 9 条、更新 9 条、坏 JSON 0，并生成备份 `data/backups/relationship_training-before-contextual-response-repair-20260524-154806.db`。
- 数据核验：`resource_library.id in (24156,24157,24158)` 的 `better_response` 已包含“你突然想吃甜的，听起来像是在给自己一个小小的安慰”；全库旧句“我不会急着判断你这样对不对”计数为 0；`PRAGMA integrity_check=ok`。
- 编译门禁：`.venv/bin/python -m py_compile backend/database/psychological_communication_ladder_seed.py backend/database/contextual_response_repair.py` 通过。
- 前端类型检查：`cd frontend && npm run type-check` 通过。
- 生产构建：`cd frontend && npm run build` 通过。
- 浏览器 smoke：Playwright 访问 `/resources?q=第3阶拒绝评判&fresh=context-repair` 并检查 `#resource-24158`，确认展示“你突然想吃甜的，听起来像是在给自己一个小小的安慰”，且旧万能句不再可见。
- 执行边界：本轮只修复已确认上下文错配的 9 条历史记录和对应源头模板，没有批量改写无关资源。

- 2026-05-24 16:08 CST 上下文质量治理与页面刷新闭环验证：
- 专项测试：`.venv/bin/python -m pytest tests/test_contextual_quality_governance.py tests/test_contextual_response_repair.py tests/test_case_blueprint_enrichment.py -q` 通过，9 passed。
- 第一轮 dry-run：`.venv/bin/python -m backend.database.contextual_quality_governance --dry-run` 扫描 11892 条、预计更新 11892 条、坏 JSON 0；真实执行生成备份 `data/backups/relationship_training-before-contextual-quality-governance-20260524-160400.db`。
- 第二轮 dry-run：修正场景化双句号后预计更新 372 条；真实执行生成备份 `data/backups/relationship_training-before-contextual-quality-governance-20260524-160541.db`。
- 收敛验证：最终 `.venv/bin/python -m backend.database.contextual_quality_governance --dry-run` 扫描 11892 条、更新 0、坏 JSON 0。
- 残留计数：已发布/已审核资源蓝图中 `希望希望 / 。。 / ？。 / ！。 / 当时具体发生了什么？ / 我脑子里有个画面 / [object Object]` 命中数为 0。
- 数据核验：`resource_library.id=24158` 的多视角回应锚定当前蛋糕场景，场景化回应不再出现双句号。
- SQLite 门禁：`PRAGMA integrity_check=ok`。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 浏览器 smoke：Playwright 访问 `/resources?q=第3阶拒绝评判&fresh=quality-governance` 并检查 `#resource-24158`，确认展示新上下文回应，且旧万能句、重复词、重复标点和对象字符串均不可见。
- 页面刷新闭环：`/resources` 已加入 `visibilitychange` 自动刷新，降低长时间打开页面看到旧内存列表的概率。

- 2026-05-24 16:26 CST 表达工具学习蓝图与真实对话案例升级验证：
- 专项测试：`.venv/bin/python -m pytest tests/test_expression_tool_enrichment.py -q` 通过，2 passed。
- 编译门禁：`.venv/bin/python -m py_compile backend/database/expression_tool_enrichment.py backend/api/expression.py backend/models/expression.py` 通过。
- dry-run：`.venv/bin/python -m backend.database.expression_tool_enrichment --dry-run` 扫描 60 个表达工具、预计更新 60 个；真实执行扫描 60、更新 60，并生成备份 `data/backups/relationship_training-before-expression-tool-enrichment-20260524-161146.db`。
- API 验证：重启后端后，`/api/expression/tools?q=对比表达&limit=1` 返回 `expr_tool_020`，且包含 `learning_blueprint.dialogue_cases[0].their_words = 我周末一般就随便待着。`。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 代理门禁：Vite 默认代理目标改为 `http://127.0.0.1:8000`；`http://127.0.0.1:3000/api/expression/tools?q=对比表达&limit=1` 返回 200，避免资源页因代理 500 显示 0 条。
- 浏览器 smoke：Playwright 设置 `hasCompletedOnboarding=true` 后访问 `/expression?q=对比表达&fresh=expression-blueprint-cli`，展开 `#expression-tool-expr_tool_020`，确认卡片包含“真实对话案例 / TA 说 / 低质量回应 / 更好回应 / 迁移练习 / 我周末一般就随便待着”。
- 执行边界：本轮只给表达工具补齐项目原创结构化案例蓝图，没有抓取或保存第三方全文；前端展示从数据库字段读取，不做纯装饰性占位。

- 2026-05-24 18:12 CST 资源更好回应对话级治理验证：
- 专项测试：`.venv/bin/python -m pytest tests/test_dialogue_response_governance.py -q` 通过，2 passed。
- 编译门禁：`.venv/bin/python -m py_compile backend/database/dialogue_response_governance.py backend/database/case_matrix_resource_upgrade.py` 通过。
- 第一轮 dry-run：`.venv/bin/python -m backend.database.dialogue_response_governance --dry-run` 扫描 11892 条、预计更新 11520 条；真实执行更新 11520 条，备份 `data/backups/relationship_training-before-dialogue-response-governance-20260524-180850.db`。
- 第二轮标点 dry-run：预计更新 8532 条；真实执行更新 8532 条，备份 `data/backups/relationship_training-before-dialogue-response-governance-20260524-181100.db`。
- 收敛验证：最终 `.venv/bin/python -m backend.database.dialogue_response_governance --dry-run` 扫描 11892 条、更新 0、坏 JSON 0。
- 数据库计数：`case_matrix_v1` 中 `json_extract(case_blueprint_json,'$.better_response') like '%我的下一步是%'` 为 0；`better_response like '%。”。%'` 为 0；`dialogue_script` 覆盖 11520 条。
- SQLite 门禁：`PRAGMA integrity_check=ok`。
- 前端门禁：`cd frontend && npm run type-check` 通过；`cd frontend && npm run build` 通过。
- 浏览器 smoke：Playwright 访问 `/resources?q=我有点紧张&fresh=dialogue-governance`，确认资源卡包含“完整对话 / 继续回应 / 边界收束 / 我听见你说‘我有点紧张，不是不喜欢’”，且页面不含“我的下一步是”和 `。”。`。
- 执行边界：本轮只修复项目原创矩阵资源和生成源头，没有搬运第三方全文；后续采集或生成同样必须把 `better_response` 当作角色可说出口的对话，而不是训练说明。

- 2026-05-24 18:42 CST 高质量数据采集工具与数据库扩展验证：
- 专项测试：`.venv/bin/python -m pytest tests/test_high_quality_data_acquisition.py -q` 通过，3 passed；覆盖 dry-run、真实写入、按 `content_unit` 防重复。
- 编译门禁：`.venv/bin/python -m py_compile backend/database/high_quality_data_acquisition.py` 通过。
- 数据扩展：真实执行 `.venv/bin/python -m backend.database.high_quality_data_acquisition --target-new 720`、`--target-new 1440`、`--target-new 10000`；导入批次分别记录 720、1115、1114 条资源。
- 重复治理：发现旧逻辑导致 `2949` 条采集资源只有 `1116` 个唯一 `content_unit`；已备份 `data/backups/relationship_training-before-high-quality-acquisition-dedupe-20260524-183939.db`，删除 1833 条本批伪重复，保留每个 `content_unit` 最早完整记录。
- 收敛 dry-run：`.venv/bin/python -m backend.database.high_quality_data_acquisition --target-new 10000 --dry-run` 返回 `created_resources=0`、`skipped_resources=1116`、`issues_count=0`。
- SQLite 门禁：`PRAGMA integrity_check=ok`。
- 数据库计数：`project_original:high_quality_acquisition_v1` 为 `1116` 条，`count(distinct content_unit)=1116`，重复内容单元为 0；`missing_blueprint=0`、`missing_policy=0`、`bad_fulltext_policy=0`。
- 覆盖核验：本批采集资源覆盖 23 个来源 URL、10 个场景、6 条主线轴、355 个变体族。
- API 抽样：`/api/resources?q=high_quality_acquisition_v1&limit=1` 返回 200，样本包含 `完整对话`、来源边界、`case_blueprint_json` 和本地原创回应内容。
- 执行边界：外部来源没有保存第三方全文；采集资源的 `source_license` 固定为 `link_title_summary_short_excerpt_structured_analysis_local_original_rewrite_only`。

- 2026-05-24 19:22 CST 非暴力沟通三步法项目级融合验证：
- 专项测试：`.venv/bin/python -m pytest tests/test_nvc_three_step_seed.py -q` 通过，3 passed；覆盖 dry-run 不落库、真实写入完整学习记录、重复执行不新增重复 `content_unit`。
- 编译门禁：`.venv/bin/python -m py_compile backend/database/nvc_three_step_seed.py` 通过。
- dry-run：`.venv/bin/python -m backend.database.nvc_three_step_seed --dry-run` 返回新增 1 个知识分区、1 条知识条目、1 个表达工具、1 条工具链和 18 张资源卡。
- 真实执行：首次执行新增知识/工具/工具链/18 张资源卡，备份 `data/backups/relationship_training-before-nvc-three-step-20260524-191841.db`；二次执行更新工具和已有资源模板，不新增重复，备份 `data/backups/relationship_training-before-nvc-three-step-20260524-192004.db`。
- SQLite 门禁：`PRAGMA integrity_check=ok`。
- 数据库计数：`project_original:nvc_three_step_choice_v1` 资源为 18 条，`count(distinct content_unit)=18`；知识条目 1 条；表达工具 `expr_tool_061` 存在，公式为“我的感受 -> 我的期待 -> 你的选择”。
- API 抽样：`/api/knowledge/entries?q=非暴力沟通三步法` 返回知识条目；`/api/expression/tools?q=非暴力` 返回 `expr_tool_061` 及 `learning_blueprint`；`/api/resources?q=非暴力沟通` 返回训练卡，正文包含“完整对话 / 三步拆解 / 边界提醒 / 练习任务”。
- 内容核验：D1 训练卡同样包含完整三步回应，例如“心跳有点快...希望慢慢相处...不用现在回应”，避免低难度资源只剩片段式感受表达。
- 执行边界：本轮为用户提供模式的项目原创结构化转化，不抓取、不保存第三方全文。

- 2026-05-24 19:36 CST 表达工具箱非暴力三步法可见性修复验证：
- 后端编译：`.venv/bin/python -m py_compile backend/api/expression.py` 通过。
- 前端类型检查：`cd frontend && npm run type-check` 通过。
- 前端生产构建：`cd frontend && npm run build` 通过。
- 重启后 API 验证：`/api/expression/tools?limit=5` 和前端代理 `/api/expression/tools?limit=5` 的第一项均为 `expr_tool_061`“非暴力沟通三步法”，总数为 61。
- 浏览器验证：in-app browser 访问 `/expression?fresh=nvc-visibility`，页面正文包含“非暴力沟通三步法”和“我的感受 -> 我的期待 -> 你的选择”。
- 展开验证：点击 `#expression-tool-expr_tool_061` 后，详情包含“真实对话案例”、概念“不剥夺对方选择”、低质量回应“那你是不是也喜欢我”、更好回应“当然你不用现在回应”、练习阶梯“D1：把一句指责改成我的感受”。
- 根因说明：数据库和 API 已有数据，但旧默认排序把新增工具放在后段；前端详情模板只兼容旧蓝图字段，导致部分新蓝图内容不可见。
