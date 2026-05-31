# 关系动力学全息依赖图

更新日期：2026-05-24

## 1. 模块依赖

```text
database/schema_guard
  -> models
  -> seed/import
  -> api
  -> frontend
  -> smoke/regression
```

```text
Safety Guardian
  -> AI Orchestrator
  -> TrainerAI
  -> SafetyEvent audit
  -> Analytics / Audit
```

```text
Source Registry
  -> RawContentItem
  -> AnnotationJob
  -> TrainingAssetVersion
  -> ResourceLibrary / KnowledgeEntry / InteractionSample
  -> reviewed/published governance
```

```text
InteractionSample
  -> TrainingAttempt
  -> CompareResponse
  -> MistakeLog
  -> AbilitySnapshot
  -> Dashboard / Profile / Path
```

```text
ExpressionTool
  -> ResourceLibrary.expression_tool_ids_json
  -> Trainer expression scoring
  -> Mistake rewrite
  -> TrainerAI expression chain
```

## 2. 前端路由依赖

| 页面 | 主要 API | 依赖数据 |
|---|---|---|
| Dashboard | `/api/analytics/*`, `/api/training/summary/*` | AI 质量、趋势、Gold Set、训练摘要 |
| Trainer | `/api/training/next`, `/api/training/compare` | 样本、视觉地图、对比评分 |
| TrainerAI | `/api/training/partner/simulate` | AI/fallback、安全、资源、错题记忆 |
| Mistakes | `/api/training/mistakes`, `/api/resources/{id}` | 错题、复习、资源上下文 |
| Resources | `/api/resources`, `/api/resources/filters` | 资源列表、筛选建议 |
| ResourceSurf | `/api/resources/sources` | 来源目录、链接健康 |
| Expression | `/api/expression/tools`, `/api/expression/chains` | 表达工具、工具链 |
| Path | `/api/learning/curriculum-graph` | 课程节点、晋级证据 |
| Knowledge | `/api/knowledge/*` | 知识分区、条目、图谱 |
| Evolution | `/api/evolution/*` | 进化流水线、导入质量、向量索引 |
| Governance | `/api/resources/similarity`, `/api/evolution/reviewed-assets/*` | 近重复、发布候选、导入 issue |

## 3. 验证依赖

```text
pytest focused tests
  -> ruff focused files
  -> frontend type-check
  -> frontend build
  -> smoke:world
  -> tools.commander regression-audit
```

`mypy --strict` 当前按分层文件执行，不对全部大型 API 文件强制一次性清零历史债。

