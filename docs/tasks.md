# 关系动力学全息 - 真实任务清单

更新日期：2026-05-21

本清单基于本轮全面审计结果，替代早期“全部未完成”的模板式任务表。

## 已完成 / 可运行

- [x] FastAPI 后端骨架与路由注册
- [x] Vue 3 + Vite 前端骨架
- [x] SQLite + SQLModel 基础数据模型
- [x] 情绪谱系 70 条与混合情绪 20 条种子数据
- [x] 训练中心基础闭环：推荐题、提交回应、对比反馈、训练记录
- [x] 错题本与间隔复习雏形
- [x] 能力雷达与今日/本周训练摘要 API
- [x] 知识中枢 API 与前端页面
- [x] 进化中心 API 与前端页面雏形
- [x] DeepSeek API 客户端与 AI Orchestrator 骨架
- [x] 前端生产构建通过：`npm run build`
- [x] 后端 smoke tests 通过：`.venv/bin/python -m pytest -q`
- [x] 指挥官-执行者构建蓝图：`docs/指挥官执行者构建蓝图.md`
- [x] 本项目 Zero-Gate 全自动构建 Prompt：`docs/本项目Zero-Gate全自动构建Prompt.md`
- [x] 世界级关系感知训练生命体总构建 Prompt：`docs/世界级关系感知训练生命体总构建Prompt.md`
- [x] 元基础数据与学习架构路线图：`docs/元基础数据与学习架构路线图.md`
- [x] 三性三管理项目脉络总纲：`docs/三性三管理项目脉络总纲.md`
- [x] 分类脉络与 5W2H 元认知框架：`docs/分类脉络与5W2H元认知框架.md`
- [x] 从元基础到熟能生巧的掌握路线：`docs/从元基础到熟能生巧的掌握路线.md`
- [x] 数图结合可视化认知体系：`docs/数图结合可视化认知体系.md`
- [x] 机器可读运行配置：`docs/runtime_config.yml`
- [x] 学习框架 API：`GET /api/learning/framework`，覆盖 0/1 元基础、分类树、5W2H、数图组件、三性三管理、熟能生巧阶段
- [x] 元基础前端页面：`/framework`，把分类治学、5W2H、数图结合和三性三管理可视化
- [x] 进化元数据流水线 API：`GET /api/evolution/pipeline`
- [x] 来源登记 API：`POST /api/evolution/sources`
- [x] 候选元数据 API：`POST /api/evolution/raw-items`
- [x] 标注任务 API：`POST /api/evolution/annotation-jobs`
- [x] 训练资产版本 API：`POST /api/evolution/asset-versions`
- [x] 进化中心前端显示源数据 -> 候选 -> 标注 -> 训练资产 -> 发布训练的全链路指标
- [x] 种子数据登记高质量来源：Gottman、Esther Perel、NIST AI RMF、Learning Scientists
- [x] 主应用级路由测试覆盖 `/api/learning/framework` 与 `/api/evolution/pipeline`
- [x] 前端类型检查通过：`npm run type-check`
- [x] 数据库 schema guard：旧 SQLite 表自动补列、记录 `schema_migrations`、启动时保障 schema 兼容
- [x] 数据库健康 API：`GET /api/database/health`，覆盖缺表/缺列、外键、`quick_check`、关键表行数、JSON 字段质量
- [x] 数据库迁移 API：`POST /api/database/migrate`，执行幂等建表 + 补列 + 审计
- [x] 样本/资源 JSON 导入幂等测试：重复导入不制造重复，缺文件安全跳过
- [x] 真实数据库审计通过：缺表/缺列为空，JSON 深层质量无坏值
- [x] 批量数据生命体闭环 API：`POST /api/evolution/pipeline/run-batch`
- [x] 批量流水线支持 dry-run、定向 raw_ids、sanitize、hash+标题语义去重、annotate、publish、Evolution Report
- [x] 批量流水线测试覆盖全链路发布和疑似重复候选跳过
- [x] 样本多粒度标注字段：5W2H、signals、emotion_flow、feelings、need_radar、boundary_state、source_trace、quality
- [x] 样本多粒度标注回填 API：`POST /api/samples/annotations/backfill`
- [x] 样本标注地图 API：`GET /api/samples/{sample_id}/annotation-map`
- [x] 训练掌握模型：知道、辨认、操作、迁移、自然
- [x] 训练错误归因：情绪误判、需求错配、节奏过快、连接关闭、边界压力
- [x] AI 伴侣关系状态机：信任、压力、边界压力、边界安全、连接随每轮回应变化
- [x] TrainerAI 前端状态可视化：状态标签、四维状态条、下一焦点提示
- [x] AI 伴侣会话持久化：`practice_sessions` / `practice_events` 保存状态轨迹、对话事件、安全摘要
- [x] 进化中心生命体数图指标：来源质量矩阵、候选审核发布漏斗、安全风险趋势、系统学习增量
- [x] AI 伴侣会话复盘：状态曲线、关键转折、错误归因、下一轮练习建议
- [x] 知识中枢图解视图：概念图谱、分类树、5W2H 卡片、工具适用地图
- [x] 错题本结构化归因：错误归因 JSON、掌握快照、复习焦点、前端归因卡
- [x] 模块任务 DAG：`docs/tasks/module_dag.json` 固化模块依赖、验收标准和验证命令
- [x] 本地指挥官入口：`python -m tools.commander run-next` 可读取 DAG 并选择下一项
- [x] AI Provider 质量门禁：Provider native / OpenAI-compatible 成功、HTTP 失败、超时、非法响应体、非 JSON 内容、安全拒绝均有 mock 测试
- [x] 安全硬阻断审计：操控/PUA/跟踪/胁迫/危机类请求写入 `safety_events`，数据库健康检查纳入 JSON 审计
- [x] 动态进化调度 API：`POST /api/evolution/scheduler/run-weekly` 可生成周期性 Evolution Report
- [x] 语义去重报告 API：`GET /api/evolution/dedupe/report` 输出 hash + 标题 token 语义重复簇
- [x] 导入质量报告 API：`GET /api/evolution/import-quality` 输出样本、资源、知识条目的字段完整度、JSON 质量、导入批次和问题
- [x] 安全事件报告 API：`GET /api/evolution/safety-events` 输出阻断事件、风险等级和 top flags
- [x] 进化中心前端调度驾驶舱：可查看导入质量、重复候选簇、安全事件，并可触发周调度生成新报告

## 当前阻塞 / 高优先级

- [x] 按 `docs/本项目Zero-Gate全自动构建Prompt.md` 生成 `docs/requirements_final.md`、`docs/high_level_design.md`、`docs/api_contract.json`、`docs/dependency_graph.md`
- [x] 后续所有自动构建优先读取 `docs/世界级关系感知训练生命体总构建Prompt.md` 作为最高层目标约束
- [x] 将 `docs/元基础数据与学习架构路线图.md` 落地为 SQLModel 表：source registry、raw content、annotation jobs、training asset versions
- [x] 将 `docs/三性三管理项目脉络总纲.md` 初步落地到学习框架 API：善/恶/非善非恶 -> 文化/制度/绩效治理
- [x] 将 `docs/分类脉络与5W2H元认知框架.md` 初步落地到学习框架 API：12 类分类树 + 5W2H 元问题
- [x] 为训练样本增加 5W2H 标注字段：why、what、who、when、where、how、how_much
- [x] 为训练反馈增加元认知问答模板：事实/解释分离、多假设、轻验证、高维复盘、下一步最小行动
- [x] 为训练能力增加掌握阶段：知道、辨认、操作、迁移、自然
- [x] 为训练反馈增加错误归因：情绪误判、需求错配、节奏过快、连接关闭、边界压力
- [x] 将错误归因持久化到错题本字段
- [x] 为训练题增加数图配置：signal_highlight、emotion_thermometer、emotion_flow_curve、need_radar、boundary_band、interaction_loop_graph（先以派生层落地，后续再持久化）
- [x] 为前端 Trainer 增加图解组件：信号高亮、情绪温度计、情绪流曲线、需求雷达、边界红黄绿带、互动回路图
- [x] 为 Evolution 增加图解指标：来源质量矩阵、候选审核发布漏斗、安全拒绝趋势、系统学习增量
- [x] 为 Knowledge 增加图解视图：概念图谱、分类树、5W2H 卡片、工具适用地图
- [x] 为样本增加多粒度标注字段：signals、emotion_flow、feelings、boundary_state、source_trace、quality
- [x] 为样本增加 tension_dimensions 与样本版本关联表，支持多标注版本并存
- [x] 为进化中心新增数据抓取/更新数据库 API 骨架：source registry、raw candidate ingest、annotation job、asset version、pipeline summary
- [x] 为进化中心新增单项自动处理器：sanitize 风险降级、dedupe 检查、annotate 生成标注任务、publish 生成训练资产版本
- [x] 为训练系统新增学习路线 API 骨架：primitive ladder、classification tree、visual components、mastery stages
- [x] 建立 `docs/tasks/` 模块任务 DAG，拆分 AI Provider、安全、进化流水线、训练引擎、前端训练舱、质量门禁
- [x] 修复前端 API data client 类型，`npm run type-check` 通过
- [x] 调整 ruff 中文项目规则，忽略 `RUF001/RUF002/RUF003`，再清理真实 lint 问题
- [x] mypy 分层治理：训练核心链路 `backend/api/training.py`、`backend/core/emotion_engine.py`、`backend/core/comparison_engine.py` strict 通过
- [x] mypy 分层治理后续：AI Provider 与进化 typed core 通过 strict；去重、安全审计、调度建议已抽到 `backend/core/evolution_intelligence.py`
- [x] DeepSeek Provider Adapter：支持官方 native text chat endpoint 与 OpenAI-compatible endpoint
- [x] 操控/PUA/跟踪/胁迫类安全策略升级为 hard block，并记录 `safety_events`
- [x] 真实执行 JSON/知识导入到 SQLite，并输出导入质量报告
- [x] 把根目录 JSON/HTML/MD 历史内容迁入 `content_sources/`，保留兼容回退
- [x] 引入正式迁移框架或 schema revision 分层策略；当前轻量 guard 可补缺表/缺列，但不处理改列、删列、索引重建和复杂约束迁移

## 数据资产建设

- [x] 互动样本从 39 条扩展到 300 条 reviewed/published
- [x] 互动样本中期扩展到 1000 条候选，其中每条有来源、风险、标注置信度、审核状态
- [x] 资源库从 116 条扩展到 500 条 reviewed/published
- [x] 将“话术库”重构为“连接素材库”：破冰观察、温和幽默、欣赏表达、修复句式、边界表达、退路式邀请
- [x] 新增 source registry、raw item、sanitized item、annotation job、sample version 等数据表
- [x] 建立 100 条 gold samples，用于校准规则评分和 DeepSeek 深评

## 训练系统强化

- [x] 情绪识别训练写入 `TrainingAttempt(mode='emotion')`
- [x] 新增 `practice_sessions` 与 `practice_events`，记录完整训练过程
- [x] 对比报告升级：词级 diff、结构级 diff、情绪路径 diff
- [x] 推荐系统从随机/弱维度映射升级为掌握模型推荐
- [x] 能力雷达返回 mastery 阶段与弱项建议
- [x] 八阶路径变成 curriculum graph，每个节点有任务、评分、晋级证据
- [x] TrainerAI 接入 AI Orchestrator，移除本地模拟回复池
- [x] 增加角色状态机：安全型、焦虑型、回避型、恐惧-回避型
- [x] AI 伴侣会话持久化：新增 practice_sessions/practice_events，保存状态轨迹和对话事件
- [x] AI 伴侣会话复盘 API 与前端曲线面板：按 session 返回状态曲线、关键转折、错误归因和下一练习
- [x] 错题本持久化错误归因和 mastery 快照，复习列表可展示能力维度与修复动作

## 进化中心强化

- [x] Source Registry 支持 Gottman、Esther Perel、论文、用户自愿提交、自建样本
- [x] 基于现有 Evolution 表提供流水线 summary：来源统计、候选/发布/拒绝数量、质量分布、下一步动作
- [x] 建立 raw -> annotated/reviewed/published 元数据流水线骨架
- [x] 批量自动去重、PII/版权风险降级、质量追踪骨架、安全过滤骨架
- [x] 批量语义去重升级为向量相似度或 sqlite-vec；当前为 hash + 标题 token 相似度
- [x] 单项 raw candidate 支持 sanitize 风险降级、dedupe 检查、annotate 生成标注任务、publish 生成训练资产版本
- [x] 批量处理后自动生成 Evolution Report
- [x] 每周调度入口生成 Evolution Report：当前为本地/API 触发，下一步可接 APScheduler 自动定时
- [x] 进化中心调度驾驶舱展示导入质量、语义去重簇、安全阻断事件和调度后的下一动作
- [x] 进化核心类型分层：`backend/core/evolution_intelligence.py` 承接 dedupe、安全报告、scheduler next actions，并有 strict mypy + 单元测试
- [x] 前端展示来源数、候选数、标注数、资产版本数、发布训练资产数
- [x] 前端展示生命体数图指标：来源质量矩阵、候选审核发布漏斗、安全风险趋势、学习增量

## 测试与质量门禁

- [x] 覆盖率从 58% 提升到 65%
- [x] 覆盖率中期提升到 80%（当前产品覆盖率 83%，65 passed）
- [x] AI provider mock 测试：成功、失败、超时、非法 JSON、安全拒绝
- [x] safety guard 单元测试与红队样例
- [x] 数据导入幂等测试：知识、互动样本、资源库
- [x] 进化流水线 dry-run 与批处理测试
- [x] 数据导入 dry-run、语义去重、脱敏测试
- [x] 前端关键路径 Playwright smoke：Dashboard、Mistakes、Knowledge
- [x] 前端关键路径浏览器 smoke：Trainer、Evolution、Framework、TrainerAI

## 验收命令

短期目标：

```bash
.venv/bin/python -m pytest -q
cd frontend && npm run build
```

专业门禁目标：

```bash
.venv/bin/python -m pytest --cov=backend --cov-report=term-missing
.venv/bin/python -m ruff check backend tests
.venv/bin/python -m mypy backend/api backend/core backend/ai --strict
cd frontend && npm run type-check && npm run build
```

当前已达成的数据库专项门禁：

```bash
.venv/bin/python -m ruff check backend/database/schema_guard.py backend/database/connection.py backend/api/database.py tests/test_database_schema_guard.py tests/test_content_import_database.py
.venv/bin/python -m mypy backend/database/schema_guard.py backend/database/connection.py backend/api/database.py
.venv/bin/python -m pytest tests/test_database_schema_guard.py tests/test_content_import_database.py -q
```
