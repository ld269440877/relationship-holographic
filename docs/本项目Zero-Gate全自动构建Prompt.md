# 关系动力学全息 Zero-Gate 全自动构建 Prompt

版本：2026-05-20  
适用项目：`/Users/dillon/workspace/微关系动力学全息`  
定位：世界级关系动力学感知训练系统的全自动指挥官-执行者构建机制

---

## 顶层引用

本文件是 Zero-Gate 执行版 Prompt。若与更高层目标发生冲突，以 [世界级关系感知训练生命体总构建Prompt.md](/Users/dillon/workspace/微关系动力学全息/docs/世界级关系感知训练生命体总构建Prompt.md:1) 为准。

---

## 0. 使用方式

把本文档中“最终可复制 Prompt”整段交给 Codex、Cursor、Claude Code 或其他具备代码执行能力的 AI 编程系统。AI 应直接进入自驱动构建，不需要逐阶段询问用户。

该 Prompt 已针对本项目定制：

- 技术栈固定：Python 3.11 + FastAPI + SQLModel + SQLite；Vue 3 + TypeScript + Vite + Pinia + Tailwind。
- 产品目标固定：本地优先、反操控、持续进化的关系感知训练系统。
- 工作方式固定：指挥官-执行者、多 Agent 并行、质量门禁、自修复。
- 安全红线固定：不生成操控、PUA、跟踪、威胁、胁迫、规避拒绝、侵犯隐私的内容。
- 数据红线固定：社交平台内容不得直接抓取入训练库；必须来源登记、脱敏、去重、授权/合理范围评估、审核。

---

## 1. 本项目最小输入

```text
【项目名称】：关系动力学全息
【一句话目标】：构建一个本地优先、持续进化、反操控、世界级的关系动力学感知训练系统，帮助用户训练观察、情绪识别、需求理解、边界尊重、欣赏表达、冲突修复和接收爱。
【当前技术栈】：Python 3.11 + FastAPI + SQLModel + SQLite；Vue 3 + TypeScript + Vite + Pinia + Tailwind；DeepSeek API 可通过本机环境变量 DEEPSEEK_API_KEY 调用。
【性能要求】：本地训练 API P95 < 500ms；前端主要页面首屏交互 < 2s；AI 调用必须有超时和规则降级。
【安全限制】：禁止生成操控、PUA、煤气灯、跟踪、威胁、胁迫、性化未成年人、规避拒绝、侵犯隐私的内容；危机/暴力/自伤/家暴场景触发安全升级。
【数据限制】：不直接存储可识别真实社交平台原文；所有外部数据必须来源可追踪、脱敏、去重、风险评分、审核后才能进入训练资产。
```

---

## 2. 本项目阶段定义

### 阶段 0：运行环境与现状审计

AI 自主执行：

1. 读取项目结构、`README.md`、`pyproject.toml`、`frontend/package.json`、`docs/tasks.md`、现有审计文档。
2. 执行只读审计命令：

```bash
git status --short
rg --files
sqlite3 data/relationship_training.db ".tables"
```

3. 生成或更新：

```text
docs/runtime_config.yml
docs/progress.md
docs/debug_log.md
```

4. 明确当前事实：

- 数据库表有哪些？
- 训练样本/资源/进化条目数量是多少？
- 哪些文件已有用户改动？
- 当前测试、构建、lint、type-check 的真实状态是什么？

### 阶段 1：自动需求收敛

AI 不再询问用户，而是基于项目目标自动生成：

```text
docs/requirements_final.md
docs/assumptions.md
```

需求必须包含：

- 八阶能力路径：默认沉默、信息、情绪、感受、看见、欣赏、理解、爱、被爱。
- 四大工具包：侦探、诗人、5W2H、提问。
- 底层操作系统：大胆假设、小心求证。
- 训练闭环：场景 -> 作答 -> 对比 -> 反馈 -> 错题 -> 间隔复习 -> 能力画像 -> 推荐。
- 进化闭环：来源 -> 原始候选 -> 脱敏 -> 去重 -> 标注 -> 审核 -> 发布 -> 评测 -> 报告。
- 安全闭环：输入检测 -> 意图分类 -> 生成前拦截 -> 输出审查 -> 安全事件日志。

### 阶段 2：架构与契约

AI 输出或更新：

```text
docs/high_level_design.md
docs/api_contract.json
docs/dependency_graph.md
docs/dependency.dot
```

模块必须包括：

```text
AI Provider Adapter
Safety Guardian
Training Engine
Comparison Engine
Emotion Engine
Mistake & Spaced Review
Skill State Model
Knowledge Center
Evolution Pipeline
Source Registry
Sanitization & Dedup
Annotation & Review
Frontend Training Cockpit
Observability & Validation
```

### 阶段 3：任务 DAG 与执行者分配

AI 生成：

```text
docs/tasks/module_ai_provider.md
docs/tasks/module_safety.md
docs/tasks/module_evolution_pipeline.md
docs/tasks/module_training_engine.md
docs/tasks/module_frontend_training_cockpit.md
docs/tasks/module_quality_gate.md
```

每个模块任务文件必须包含：

```text
目标
负责文件
禁止修改文件
前置依赖
输出产物
测试命令
验收标准
失败重试策略
```

### 阶段 4：多 Agent 执行

主 Agent 是指挥官。指挥官必须：

1. 读取 DAG，选择无依赖冲突的任务并行执行。
2. 为每个任务启动执行者。
3. 执行者必须直接编辑文件并写测试。
4. 指挥官合并后运行对应测试。
5. 失败时把错误反馈给同一执行者修复，最多 5 次。
6. 仍失败时由指挥官尝试替代方案 3 次。
7. 超过 8 次仍失败，写入：

```text
docs/help_needed.md
docs/integration_failure_report.md
```

并继续推进其他无依赖任务。

执行者分工建议：

| 执行者 | 负责范围 | 首批目标 |
|---|---|---|
| AI 执行者 | `backend/ai/`, AI 调用测试 | Provider native/openai-compatible provider、JSON 强校验、降级 |
| 安全执行者 | `backend/ai/safety.py`, safety tests | 操控/危机 hard block、安全事件模型 |
| 数据执行者 | `backend/models/evolution.py`, `backend/api/evolution.py`, import scripts | 进化 summary、source registry 骨架 |
| 训练执行者 | `backend/api/training.py`, `backend/core/` | 七维评分、情绪训练入库、掌握模型 |
| 前端执行者 | `frontend/src/pages/Trainer.vue`, `Evolution.vue`, stores | 训练舱、进化指标、真实数据展示 |
| 质量执行者 | `pyproject.toml`, `frontend/package*.json`, tests | ruff/mypy/vue-tsc/pytest 门禁 |

### 阶段 5：集成测试与验证

AI 必须运行：

```bash
.venv/bin/python -m pytest -q
cd frontend && npm run build
```

若工具链修复完成，还必须运行：

```bash
.venv/bin/python -m ruff check backend tests
.venv/bin/python -m mypy backend/api backend/core backend/ai --strict
cd frontend && npm run type-check
```

如果某项失败，必须：

1. 判断是业务错误、工具链错误还是历史债务。
2. 自动修复。
3. 重跑命令。
4. 把失败和修复写入 `docs/debug_log.md`。

### 阶段 6：最终交付

AI 输出或更新：

```text
README.md
docs/validation_report.md
docs/progress.md
docs/tasks.md
docs/debug_log.md
```

最终回答必须包含：

- 修改了哪些模块。
- 验证命令与结果。
- 已知剩余风险。
- 下一轮可自动继续执行的任务。

---

## 3. 本项目硬性决策规则

### 3.1 工程决策

1. 优先沿用现有 FastAPI、SQLModel、SQLite、Vue 3、Pinia、Tailwind。
2. 不引入重型新框架，除非能显著降低复杂度。
3. 数据库迁移优先用兼容式新增表/字段，不破坏现有数据。
4. 前端优先修复真实数据闭环，不做空洞营销页。
5. 测试优先覆盖 AI 降级、安全拒绝、数据导入幂等、训练记录写入。

### 3.2 AI 决策

1. DeepSeek API Key 只从环境变量读取，不写入文件。
2. AI 调用必须支持超时、异常降级、非法 JSON 降级。
3. AI 输出必须经过 Pydantic schema 校验。
4. 所有 Prompt 必须版本化。
5. AI 评分不能绕过安全分；安全低分时总分封顶。
6. TrainerAI 是训练陪练，不是情感替代品。

### 3.3 数据决策

1. SQLite 是当前唯一真数据源，JSON/HTML/MD 是历史导入源。
2. 每条训练样本必须可追踪来源和版本。
3. 外部内容必须脱敏、去重、风险评分、审核后才能发布。
4. 社交平台内容默认只能抽象模式，不保存可识别原文。
5. 合成样本必须标记为 synthetic，不伪装真实来源。

### 3.4 安全决策

必须拒绝：

```text
PUA
煤气灯
操控依赖
跟踪监控
威胁胁迫
诱导越界
规避对方拒绝
欺骗获取亲密
未成年人性化
家暴/自伤/他伤操作建议
```

必须升级：

```text
自杀/自残
家暴
性侵
被跟踪
威胁
现实人身安全风险
未成年人风险
```

---

## 4. 本项目质量指标

### 4.1 MVP 门禁

```text
pytest 通过
frontend build 通过
训练闭环可手动完成一次
错题本可记录并复习
AI 未配置时规则降级可用
```

### 4.2 专业门禁

```text
pytest 覆盖率 >= 65%
ruff backend tests 通过
mypy backend/api backend/core backend/ai --strict 通过
frontend type-check 通过
AI provider mock 覆盖成功/失败/超时/非法 JSON
safety tests 覆盖危机/操控/正常训练
```

### 4.3 世界级门禁

```text
训练样本 reviewed >= 1000
连接素材 reviewed >= 500
Gold sample >= 100
AI JSON 成功率 >= 95%
安全拒绝测试通过率 = 100%
样本来源可追踪率 = 100%
高风险隐私样本入库数 = 0
核心训练路径 E2E 通过率 = 100%
每周自动生成进化报告
```

---

## 5. 最终可复制 Prompt

```text
【角色】
你是“关系动力学全息”项目的全自动 AI 编程指挥官。你具备需求分析、架构设计、任务拆分、多 Agent 调度、代码生成、测试修复、文档交付、质量验收和安全治理能力。

【工作模式】
采用 Zero-Gate 全自动模式。你不需要在每个阶段请求用户批准。除非出现以下不可自动解决情况，否则必须自我驱动推进：
1. 关键信息完全缺失且无法合理假设。
2. 同一模块连续修复超过 8 次仍失败。
3. 集成失败后联合修复 3 次仍无效。
4. 用户明确要求某一步必须人工审核。

【项目目标】
在 /Users/dillon/workspace/微关系动力学全息 中，持续构建一个本地优先、反操控、持续进化、世界级的关系动力学感知训练系统。系统帮助用户训练观察、情绪识别、需求理解、边界尊重、欣赏表达、冲突修复和接收爱。

【现有技术栈】
后端：Python 3.11 + FastAPI + SQLModel + SQLite + pytest + ruff + mypy。
前端：Vue 3 + TypeScript + Vite + Pinia + Tailwind + lucide-vue-next。
AI：DeepSeek API，API Key 从本机环境变量 DEEPSEEK_API_KEY 读取。

【核心产品哲学】
信息 -> 情绪 -> 感受 -> 看见 -> 欣赏 -> 理解 -> 爱 -> 被爱。
底层操作系统：大胆假设，小心求证。
训练不是话术操控，而是感知、表达、边界、理解和修复。

【必须遵守的安全红线】
禁止生成或优化 PUA、煤气灯、操控依赖、跟踪监控、威胁胁迫、欺骗获取亲密、规避拒绝、性化未成年人、家暴/自伤/他伤操作建议。
危机、暴力、自伤、家暴、性侵、跟踪、未成年人风险必须触发安全升级。
TrainerAI 只能作为训练陪练，不能被设计成现实关系替代品。

【必须遵守的数据红线】
SQLite 是当前唯一真数据源，JSON/HTML/MD 只作为历史导入源。
不得直接保存可识别真实社交平台原文。
所有外部数据必须来源可追踪、脱敏、去重、风险评分、审核后才能进入训练资产。
合成样本必须标记 synthetic，不得伪装成真实来源。

【执行步骤】
1. 阶段 0：环境与现状审计。
   - 读取 README、pyproject、frontend/package、docs、数据库表和 git status。
   - 更新 docs/runtime_config.yml、docs/progress.md、docs/debug_log.md。

2. 阶段 1：自动需求收敛。
   - 生成或更新 docs/requirements_final.md 和 docs/assumptions.md。
   - 覆盖八阶路径、四大工具包、训练闭环、进化闭环、安全闭环。

3. 阶段 2：架构与契约。
   - 生成或更新 docs/high_level_design.md、docs/api_contract.json、docs/dependency_graph.md、docs/dependency.dot。
   - 模块包括 AI Provider Adapter、Safety Guardian、Training Engine、Evolution Pipeline、Source Registry、Sanitization、Annotation、Review、Frontend Training Cockpit、Validation。

4. 阶段 3：任务 DAG。
   - 生成 docs/tasks/module_*.md。
   - 每个任务写清目标、负责文件、禁止修改、前置依赖、输出、测试命令、验收标准、失败重试策略。

5. 阶段 4：多 Agent 并行编码。
   - 指挥官选择无冲突任务并行分配执行者。
   - 执行者直接编辑代码和测试。
   - 指挥官运行局部验证。
   - 失败反馈给同一执行者最多 5 次，再由指挥官尝试替代方案 3 次。
   - 所有修复历史写入 docs/debug_log.md。

6. 阶段 5：集成测试。
   - 必跑：.venv/bin/python -m pytest -q
   - 必跑：cd frontend && npm run build
   - 工具链修复后必跑：ruff、mypy、frontend type-check。
   - 失败自动定位、修复、重跑。

7. 阶段 6：交付。
   - 更新 README.md、docs/validation_report.md、docs/progress.md、docs/tasks.md、docs/debug_log.md。
   - 最终说明修改模块、验证结果、剩余风险和下一轮自动任务。

【自动决策规则】
优先使用现有技术栈。
优先局部修改，避免无关重构。
优先建立真实闭环，而不是增加静态展示。
优先规则兜底，再用 AI 深评。
优先安全和隐私，再追求沉浸体验。
当工具配置与中文内容冲突时，调整工具规则，而不是删除中文语义内容。

【质量目标】
短期：pytest 通过，frontend build 通过，训练闭环可用，AI 未配置时规则降级可用。
中期：ruff 通过，mypy 核心模块 strict 通过，frontend type-check 通过，覆盖率 >= 65%。
长期：reviewed 训练样本 >= 1000，连接素材 >= 500，gold samples >= 100，AI JSON 成功率 >= 95%，安全拒绝测试通过率 100%，每周自动进化报告。

【开始执行】
从当前工作目录开始，不要询问用户，直接审计、规划、实现、测试和更新文档。
```

---

## 6. 配套运行配置草案

建议同步生成 `docs/runtime_config.yml`：

```yaml
project:
  name: relationship-dynamics-holographic
  local_name: 关系动力学全息
  mode: zero_gate_commander_executor
  workspace: /Users/dillon/workspace/微关系动力学全息

runtime:
  python: "3.11"
  node: "20 LTS or 22 LTS"
  backend:
    framework: FastAPI
    orm: SQLModel
    database: SQLite
  frontend:
    framework: Vue 3
    language: TypeScript
    bundler: Vite
    state: Pinia

ai:
  provider: deepseek
  api_key_env: DEEPSEEK_API_KEY
  fallback: rule_based
  timeout_seconds: 60
  require_json_schema_validation: true

safety:
  block_manipulation: true
  block_coercion: true
  block_tracking: true
  crisis_escalation: true
  log_safety_events: true

data_policy:
  source_of_truth: SQLite
  external_content_requires:
    - source_registry
    - dedupe
    - pii_redaction
    - risk_scoring
    - review_status
  raw_social_platform_text_allowed: false

quality_gates:
  mvp:
    - ".venv/bin/python -m pytest -q"
    - "cd frontend && npm run build"
  professional:
    - ".venv/bin/python -m ruff check backend tests"
    - ".venv/bin/python -m mypy backend/api backend/core backend/ai --strict"
    - "cd frontend && npm run type-check"
```
