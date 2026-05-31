# 关系动力学全息高层设计

更新日期：2026-05-24

## 1. 架构原则

系统采用本地优先的单体应用架构：

```text
Vue 3 前端
  -> FastAPI API 层
  -> 领域服务 / 核心引擎
  -> SQLModel 模型
  -> SQLite 主数据源
```

SQLite 是当前唯一主真源；历史 JSON/Markdown/HTML 只作为导入源或兼容回退。

## 2. 模块边界

### AI Provider Adapter

负责 DeepSeek / OpenAI-compatible 请求构建、诊断、超时、JSON 恢复和 fallback。

关键文件：

- `backend/ai/provider_client.py`
- `backend/ai/orchestrator.py`
- `backend/api/analytics.py`

### Safety Guardian

负责操控、胁迫、跟踪、侵犯同意、危机暴力等高风险输入阻断。

关键文件：

- `backend/ai/safety.py`
- `backend/models/training.py`

### Training Engine

负责推荐题、作答、对比评分、训练记录、能力快照、错题生成和复习。

关键文件：

- `backend/api/training.py`
- `backend/core/comparison_engine.py`
- `backend/core/emotion_engine.py`
- `backend/models/training.py`
- `backend/models/user.py`

### Knowledge Center

负责结构化知识、分区、条目、概念图谱、分类树和 5W2H 展示。

关键文件：

- `backend/api/knowledge.py`
- `backend/models/knowledge.py`
- `frontend/src/pages/Knowledge.vue`

### Evolution Pipeline

负责来源登记、候选内容、脱敏、去重、标注、版本、发布、导入质量、批次回滚和审计。

关键文件：

- `backend/api/evolution.py`
- `backend/models/evolution.py`
- `backend/core/vector_index.py`
- `backend/database/resource_quality_governance.py`

### Resource Ocean

负责资源浏览、检索、详情、来源目录、链接健康、近重复治理和资源到训练/错题的联动。

关键文件：

- `backend/api/resources.py`
- `backend/models/resource.py`
- `frontend/src/pages/Resources.vue`
- `frontend/src/pages/ResourceDetail.vue`
- `frontend/src/pages/ResourceSurf.vue`

### Expression Toolbox

负责表达工具本体、工具链、推荐、微课程和训练评分联动。

关键文件：

- `backend/api/expression.py`
- `backend/models/expression.py`
- `backend/database/expression_seed.py`
- `frontend/src/pages/Expression.vue`

### Observability & Validation

负责运行时事件、分析中心、审计中心、指挥官任务状态和世界级 smoke。

关键文件：

- `backend/api/analytics.py`
- `tools/commander.py`
- `frontend/scripts/world-class-smoke.mjs`
- `docs/tasks/module_dag.json`

## 3. 数据流

### 训练流

```text
InteractionSample
  -> TrainingAttempt
  -> CompareResponse
  -> MistakeLog
  -> AbilitySnapshot
  -> next training recommendation
```

### AI 伴侣流

```text
PartnerSimulateRequest
  -> SafetyGuardian
  -> AIOrchestrator / fallback
  -> PracticeSession + PracticeEvent
  -> relationship state curve
  -> mistake memory + related resources
```

### 内容进化流

```text
SourceRegistry
  -> RawContentItem
  -> AnnotationJob
  -> TrainingAssetVersion
  -> ResourceLibrary / KnowledgeEntry / InteractionSample
  -> reviewed/published gate
```

### 资源治理流

```text
ResourceLibrary
  -> quality report
  -> similarity queue
  -> quarantine/rewrite/review action
  -> PipelineRunLog audit
```

## 4. 安全设计

- 所有 AI 请求先经过 `SafetyGuardian.inspect()`。
- 高风险请求不调用外部 provider。
- 安全事件只保存摘要、hash、风险标记和替代建议。
- 高张力资源发布必须包含边界/同意/可拒绝/停止/不施压等证据。

## 5. 验证设计

核心门禁：

```bash
.venv/bin/python -m pytest tests/test_catalog_profile_review_api.py tests/test_learning_pipeline_api.py tests/test_ai_provider_safety.py -q
.venv/bin/python -m tools.commander regression-audit --batch-limit 2
cd frontend && npm run type-check && npm run build && npm run smoke:world
```

已知技术债：

- 部分大型 API 文件仍存在全文件 strict mypy 历史债。
- DeepSeek HTTP 400/403 当前更像外部账号/模型授权或服务侧策略问题，本地 fallback 已保持可用。
- 历史 import issue 仍需人工来源复核。

