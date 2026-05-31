# 2026-05-24 最终审计与执行方案

生成时间：2026-05-24 05:15 CST

## 审计结论

当前机器可读待办和真实数据库验收均显示：本阶段工程待办已全部完成，没有新的可自动化 pending 项。

- `docs/tasks/data_content_backlog.json`：4/4 completed
- `docs/tasks/next_stage_backlog.json`：13/13 completed
- `docs/tasks/commander_state.json`：108/108 completed，pending 0
- `docs/tasks.md` 与 `docs/tasks/*.json`：未发现未勾选项、`pending` 或 `in_progress`

## 数据验收快照

```text
interaction_samples: 1008
training_ready(reviewed/published/gold): 304
draft_candidates: 671
gold_samples: 104
resources_ready(reviewed/published): 12317
```

连接素材库动作分布：

```text
破冰观察: 7537
温和幽默: 888
欣赏表达: 18
修复句式: 1706
边界表达: 2148
退路式邀请: 3
```

## 完整待办事项列表与执行状态

| 任务 | 状态 | 执行方案 | 验收证据 |
|---|---|---|---|
| 互动样本扩展到 300 条 reviewed/published | 已完成 | 使用 `backend.database.data_content_governance` 对足够具体的样本补齐多粒度标注、质量和来源追踪；不合格样本保持 draft | 可训练样本 304 条 |
| 候选互动样本扩展到 1000 条 | 已完成 | 使用项目原创场景模板生成候选，覆盖场景、依恋、边界、情绪、需求；写入 `source_trace_json` 和 `quality_json` | 总样本 1008 条，draft 候选 671 条 |
| 话术库重构为连接素材库 | 已完成 | 按破冰观察、温和幽默、欣赏表达、修复句式、边界表达、退路式邀请重写 `speech_act`、表达目标、错题模式和练习任务 | 六类连接动作均有数据 |
| 建立 100 条 Gold samples | 已完成 | 从 reviewed/published 样本中挑选结构完整、安全边界清晰的样本，补齐 gold label 和 annotation version | Gold 样本 104 条 |
| 多记录页目录、检索、展开详情体验 | 已完成 | 使用共享 `PageTocSidebar`，目录可折叠，资源/表达搜索提供建议并保留手输，表达详情卡内展开 | `smoke:world checked=61` 已归档 |
| 表达工具箱学习深度 | 已完成 | 卡片补概念、原则、公式、方法、场景、风险、对比案例和迁移练习 | `ExpressionSearchSuggestions` 与路径学习 smoke 已归档 |
| 资源海洋学习拆解卡 | 已完成 | 资源卡展示概念定义、核心原则、实践方法、低质/更好回应和练习任务 | `ResourceLearningScaffold` smoke 已归档 |
| 设置导出和提醒说明 | 已完成 | 导出为真实 Markdown；提醒明确浏览器本地通知边界 | settings 相关 smoke 已归档 |
| 我的档案真实证据联动 | 已完成 | 档案指标绑定训练摘要、能力雷达和 profile API，移除不可证明硬编码指标 | profile evidence smoke 已归档 |
| 数据内容回归门禁 | 已完成 | 增加 `tests/test_data_content_governance.py`，覆盖 dry-run、目标达成、draft 不进训练 | 3 passed |

## 不自动关闭的真实运营债

以下问题不是当前可安全自动完成的代码待办，不能用脚本伪装关闭。

| 债务 | 当前证据 | 处理原则 |
|---|---|---|
| DeepSeek HTTP 400/403 | 回归审计显示本地请求形态通过，但 provider failure 仍较高 | 需要账号区域、模型授权、供应商策略或受控 live probe 排查；保持 fallback 生效，不保存 prompt/response 正文 |
| 历史导入 issue 人工复核 | import quality 仍有 80 个 active historical issues，`auto_repairable_fields=0` | 只可由 reviewer/source owner 做来源级复核；自动脚本不得批量伪关闭 |
| 发布候选人工确认 | reviewed publish candidates 仍要求人工确认 | 不绕过发布门禁，不把 reviewed 自动变 published |

## 后续执行口径

1. 如果新增明确任务，先写入机器可读 backlog，包含目标、验收标准、执行步骤和验证命令。
2. 只有出现 `pending`、失败测试、失败回归、或真实用户可见缺陷，才进入代码修改。
3. 对外部依赖问题，优先做诊断、fallback 和不泄密审计；不把供应商授权失败写成“本地代码已完全修复”。
4. 对历史导入 issue，自动化只做分桶、证据包和审计日志；是否关闭必须由人工复核决策。

## 本轮验证命令

```bash
python3 - <<'PY'
import json
from pathlib import Path
for path in ['docs/tasks/data_content_backlog.json','docs/tasks/next_stage_backlog.json','docs/tasks/commander_state.json']:
    data=json.loads(Path(path).read_text())
    if 'tasks' in data:
        counts={}
        for item in data['tasks']:
            counts[item.get('status','unknown')]=counts.get(item.get('status','unknown'),0)+1
        print(path, counts)
    else:
        print(path, data.get('summary') or {k:data.get(k) for k in ['total','completed','pending','completion_ratio']})
PY
rg -n "^- \[ \]|\"status\": \"pending\"|\"status\": \"in_progress\"" docs/tasks.md docs/tasks/*.json || true
sqlite3 data/relationship_training.db "select 'samples', count(*) from interaction_samples union all select 'training_ready', count(*) from interaction_samples where review_status in ('reviewed','published','gold') union all select 'gold', count(*) from interaction_samples where is_gold_sample=1 or review_status='gold' union all select 'resources_ready', count(*) from resource_library where review_status in ('reviewed','published');"
.venv/bin/python -m tools.commander regression-audit --batch-limit 2
```
