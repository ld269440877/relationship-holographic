import { spawn } from 'node:child_process'
import { mkdir, writeFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { chromium } from 'playwright'

const port = Number(process.env.SMOKE_PORT || 4174)
const baseURL = `http://127.0.0.1:${port}`
const reportDir = new URL('../output/smoke/', import.meta.url)

const routes = [
  { path: '/', name: 'Dashboard' },
  { path: '/trainer', name: 'Trainer' },
  { path: '/trainer-ai', name: 'TrainerAI' },
  { path: '/path', name: 'Path' },
  { path: '/mistakes', name: 'Mistakes' },
  { path: '/resources', name: 'Resources' },
  { path: '/resources/1?q=边界&category=冲突修复&page=2', name: 'ResourceDetail' },
  { path: '/expression#expression-tool-expr_tool_015', name: 'Expression' },
  { path: '/surf', name: 'ResourceSurf' },
  { path: '/profile', name: 'Profile' },
  { path: '/knowledge', name: 'Knowledge' },
  { path: '/evolution', name: 'Evolution' },
  { path: '/framework', name: 'Framework' },
  { path: '/analytics', name: 'Analytics' },
  { path: '/audit', name: 'Audit' },
  { path: '/governance', name: 'Governance' },
  { path: '/settings', name: 'Settings' },
]

const viewports = [
  { name: 'desktop', width: 1440, height: 960 },
  { name: 'mobile', width: 390, height: 844 },
]

const sample = {
  id: 1,
  sample_uuid: 'smoke-sample',
  scenario_category: '暧昧推进',
  difficulty_level: 3,
  context: '对方最近回复变慢，但仍然愿意分享日常。',
  their_words: '我这两天有点累，不太想一直聊天。',
  their_behavior: '回复间隔变长，语气仍然柔和。',
  emotion_tags_json: '[{"spectrum":"疲惫","word":"累","intensity":6}]',
  hidden_need: '空间感和被理解',
  need_urgency: 6,
  attachment_signal: '回避倾向',
  boundary_test_level: 4,
  bad_response: '你是不是不喜欢我了？',
  good_response_soft: '听起来你需要一点空间，我在，也不用急着回复。',
  good_response_tension: '那我先把想你这件事收好一点，等你充好电再来找我。',
  good_response_humor: '收到，今天给你开省电模式。',
  principle_ref: '先接住情绪，再尊重边界。',
  source: 'smoke',
  created_at: '2026-05-21T00:00:00',
}

const visualMap = {
  axiom: '先看见信号，再提出轻验证。',
  signal_highlights: [
    { type: 'language', label: '语言', text: '有点累', weight: 0.78, hypothesis: 'TA 需要降低互动密度' },
    { type: 'behavior', label: '行为', text: '回复变慢', weight: 0.62, hypothesis: '边界需求上升' },
  ],
  emotion_thermometer: {
    spectrum: '疲惫',
    word: '累',
    intensity: 6,
    average_intensity: 6,
    percent: 60,
    zone: 'yellow',
    principle: '强度中等时先承接，不急推结论。',
  },
  emotion_flow_curve: [
    { step: '听见', value: 4, label: '识别' },
    { step: '承接', value: 6, label: '共情' },
    { step: '边界', value: 5, label: '尊重' },
    { step: '连接', value: 7, label: '推进' },
  ],
  need_radar: [
    { name: '安全', value: 72, evidence: '不想一直聊天' },
    { name: '空间', value: 86, evidence: '有点累' },
    { name: '连接', value: 58, evidence: '仍分享日常' },
  ],
  boundary_band: {
    level: 4,
    percent: 40,
    zone: 'yellow',
    label: '需要减压',
    principle: '边界不等于拒绝。',
    bands: [],
  },
  interaction_loop_graph: {
    nodes: [
      { id: 'signal', label: '信号', value: '回复慢' },
      { id: 'need', label: '需求', value: '空间' },
      { id: 'response', label: '回应', value: '低压承接' },
    ],
    edges: [],
  },
  five_w_two_h: {
    why: '疲惫',
    what: '降低密度',
    who: '对方',
    when: '最近两天',
    where: '聊天场景',
    how: '温和回应',
    how_much: { emotion_intensity: 6, need_urgency: 6, boundary_level: 4 },
  },
  verification_prompts: ['我理解你想缓一缓，是这样吗？'],
  anti_manipulation_note: '不压迫、不惩罚、不冷暴力。',
}

const radar = {
  levels: [
    { name: '情绪识别', score: 76, description: '稳定' },
    { name: '需求洞察', score: 68, description: '持续提升' },
    { name: '边界尊重', score: 82, description: '优秀' },
  ],
  total_score: 75,
  level: '进阶',
  weakest_dimension: '需求洞察',
  next_recommendation: '练习把解释改成验证问题。',
}

const partnerRelationshipState = {
  trust: 58,
  stress: 32,
  boundary: 36,
  boundary_safety: 70,
  connection: 62,
  turn_count: 1,
  attachment_style: '回避型依恋',
  state_label: '连接修复',
  state_color: 'green',
  last_delta: { trust: 8, stress: -6, boundary: -5, boundary_safety: 9, connection: 10 },
  interpretation: '低压承接降低了压力，也保留了连接窗口。',
  next_focus: '继续用轻验证确认对方需要的空间。',
}

const partnerSimulateResponse = {
  session_id: 101,
  reply: '谢谢你这样说，我会轻松一点。你不用一直在线，但这样表达让我感觉被尊重。',
  score: 82,
  source: 'rule_fallback:smoke',
  suggestions: ['可以补一句退路：你不用急着回。', '继续保持低压表达。'],
  safety: { blocked: false, risk_level: 'low' },
  safe_alternatives: [],
  relationship_state: partnerRelationshipState,
  expression_chain: {
    target_goal: '降低防御',
    state_shift: { label: '连接修复', trust: 58, stress: 32, boundary: 36, connection: 62, interpretation: '低压承接降低压力。' },
    tool_ids: ['expr_tool_015'],
    tool_names: ['情绪标注'],
    why: ['先命名感受，避免追问。'],
    next_move: '问一个可拒绝的小问题。',
    practice_prompt: '下一句只做轻验证。',
    risk_boundary: '不逼对方立刻解释或承诺。',
    principle: '每轮说明表达工具链。',
  },
  related_resources: [
    { id: 1, title: '失望后的重新约定｜三步训练｜安全型D3', type: 'story', category: '冲突修复', scene: '失望修复', expression_goal: '修复信任', quality_score: 93, source_title: 'Gottman Institute', source_url: 'https://www.gottman.com/', usage_tip: '先承认影响。', reason: '匹配边界与修复训练' },
  ],
  mistake_memory: {
    cards: [
      { mistake_id: 7, sample_id: 1, scene: '边界', their_words: sample.their_words, user_bad_response: sample.bad_response, correct_response: sample.good_response_soft, review_focus: '边界压力', emotion_mistake: '过度确认', expression_rewrite: { rewrite_versions: [{ name: '低压版', text: '我理解你累了，不急着回复。', tool: '情绪标注' }] } },
    ],
    weak_dimensions: [{ dimension: 'boundary_score', label: '边界尊重', score: 68, recommendation: '先给退路。' }],
    next_focus: '本轮先避开追问和催促。',
    principle: '错题记忆只用于训练提示。',
  },
}

const providerStatus = {
  configured: true,
  provider: 'deepseek',
  mode: 'openai',
  model: 'deepseek-v4-pro',
  base_url: 'https://api.deepseek.com',
  chat_path: '/chat/completions',
  live_probe_enabled: false,
  compatibility_risks: [],
  status_label: 'AI Provider 已配置，当前 smoke 使用安全模拟',
  principle: 'Provider 状态只展示脱敏配置。',
}

const partnerSessionReview = {
  session: {
    id: 101,
    mode: 'partner_simulation',
    scenario_id: 'avoidant',
    scenario_name: '小回避',
    attachment_style: '回避型依恋',
    difficulty: 'medium',
    response_style: 'soft',
    topics: ['日常沟通', '情绪支持'],
    status: 'active',
    total_turns: 1,
    average_score: 82,
    safety_summary: { blocked: 0 },
    started_at: '2026-05-22T00:00:00',
    updated_at: '2026-05-22T00:01:00',
    ended_at: null,
  },
  state_curve: [
    { turn: 1, score: 82, source: 'rule_fallback:smoke', state_label: '连接修复', trust: 58, stress: 32, boundary: 36, boundary_safety: 70, connection: 62, created_at: '2026-05-22T00:01:00' },
  ],
  state_delta: { trust: 8, stress: -6, boundary: -5, boundary_safety: 9, connection: 10 },
  turning_points: [{ turn: 1, title: '压力下降', evidence: '低压承接并给出退路。', user_message: '我理解你想休息，不急着回复。', severity: 'green' }],
  error_attribution: [],
  next_practice: {
    focus: '轻验证',
    minimum_action: '补一句“你希望我怎么配合会更舒服？”',
    drills: ['承接一句', '退路一句'],
    state_based_focus: '维持连接窗口',
  },
  principle: '会话复盘看状态变化、转折和下一练习。',
}

const mistake = {
  id: 7,
  context: sample.context,
  their_words: sample.their_words,
  user_bad_response: sample.bad_response,
  correct_response: sample.good_response_soft,
  emotion_mistake: '边界压力',
  review_focus: 'boundary_score',
  next_review: '2026-05-22',
  correct_count: 1,
  wrong_count: 2,
  error_attribution: [
    { category: '过度确认', dimension: 'boundary_score', reason: '把疲惫解释成拒绝。', repair: '先承接空间需求。' },
  ],
}

const evolutionVisualMetrics = {
  principle: '看来源、漏斗、风险和学习速度。',
  source_quality_matrix: [
    {
      id: 1,
      name: '内部金样本',
      source_type: 'gold',
      trust_score: 95,
      raw_count: 12,
      annotation_count: 10,
      asset_count: 8,
      published_assets: 6,
      avg_privacy_risk: 5,
      avg_copyright_risk: 3,
      avg_confidence: 88,
      conversion_rate: 0.62,
      health_score: 91,
      quadrant: 'high_quality_low_risk',
    },
  ],
  review_publish_funnel: [
    { id: 'raw', label: 'Raw', count: 12, percent_of_start: 100, conversion_from_previous: 100 },
    { id: 'reviewed', label: 'Reviewed', count: 10, percent_of_start: 83, conversion_from_previous: 83 },
    { id: 'published', label: 'Published', count: 6, percent_of_start: 50, conversion_from_previous: 60 },
  ],
  safety_risk_trend: [{ date: '2026-05-21', total: 12, blocked: 1, risk_events: 1, sanitized: 2, risk_rate: 0.08 }],
  learning_increment: {
    new_annotations: 10,
    published_assets: 6,
    automation_events: 3,
    axis_coverage: [{ name: '边界', count: 6 }],
    primitive_layer_coverage: [{ name: '情绪', count: 5 }],
    learning_velocity: 19,
  },
}

const aiQuality = {
  summary: {
    runs: 14,
    success_rate: 78.6,
    fallback_rate: 21.4,
    safety_block_rate: 7.1,
    provider_failure_rate: 7.1,
    avg_latency_ms: 238,
  },
  outcome_breakdown: [
    { name: 'success', count: 11, rate: 78.6 },
    { name: 'blocked_safety', count: 1, rate: 7.1 },
    { name: 'provider_failure', count: 1, rate: 7.1 },
  ],
  task_type_breakdown: [{ name: 'partner_simulation', count: 14, rate: 100 }],
  provider_breakdown: [{ name: 'deepseek', count: 14, rate: 100 }],
  fallback_reasons: [{ name: 'AI 编排器降级', count: 1, rate: 7.1 }],
  safety_flags: [{ name: 'manipulation', count: 1, rate: 7.1 }],
  trend: [{ date: '2026-05-21', runs: 14, success: 11, fallback: 3, blocked: 1, success_rate: 78.6, fallback_rate: 21.4 }],
  recent_runs: [],
  next_actions: [{ priority: 'medium', action: '扩充安全替代表达训练', reason: '安全阻断 1 次，继续强化非控制表达。' }],
  principle: 'AI 质量要看成功率、降级率、安全阻断、延迟和任务分布。',
}

const relationshipTrends = {
  summary: {
    sessions: 4,
    sessions_with_events: 4,
    turns: 15,
    average_score: 78,
    blocked_sessions: 0,
    repair_index: 76,
  },
  average_state_delta: { trust: 6.4, stress: -4.2, boundary: -2.1, boundary_safety: 5.8, connection: 7.3 },
  attachment_distribution: [{ name: 'avoidant', count: 2, rate: 50 }],
  session_trend: [
    {
      id: 1,
      scenario_name: '低压承接练习',
      attachment_style: 'avoidant',
      difficulty: 'medium',
      status: 'active',
      turns: 4,
      average_score: 78,
      safety_blocks: 0,
      state_label: '连接修复',
      next_focus: '继续轻验证',
      updated_at: '2026-05-21T00:00:00',
      delta: { trust: 8, stress: -5, boundary: -3, boundary_safety: 7, connection: 9 },
    },
  ],
  focus_distribution: [{ name: '继续轻验证', count: 4, rate: 100 }],
  next_actions: [{ priority: 'low', action: '进入迁移练习', reason: '长期趋势稳定，可切换不同依恋风格。' }],
  principle: '单次会话看转折，跨会话趋势看能力是否长期改善。',
}

const goldSummary = {
  summary: {
    gold_samples: 100,
    annotation_versions: 120,
    scaffold_versions: 100,
    expert_reviews: 42,
    approved: 36,
    needs_revision: 5,
    rejected: 1,
    pending_review: 58,
    expert_coverage_rate: 36,
    average_confidence: 0.86,
  },
  quality_gates: {
    ready_for_strict_calibration: false,
    minimum_expert_reviews: 30,
    target_expert_coverage_rate: 70,
    target_average_confidence: 0.8,
  },
  next_actions: [{ priority: 'high', action: '推进专家复核队列', reason: '仍有 58 条 Gold 样本缺专家版本。' }],
  principle: 'Gold Set 必须从脚手架进入专家复核。',
}

const goldQueue = {
  items: [
    {
      sample: {
        id: 1,
        sample_uuid: 'gold-smoke',
        scenario_category: '冲突',
        difficulty_level: 3,
        context: sample.context,
        their_words: sample.their_words,
        hidden_need: sample.hidden_need,
        attachment_signal: sample.attachment_signal,
        boundary_test_level: sample.boundary_test_level,
        good_response_soft: sample.good_response_soft,
        review_status: 'gold',
        updated_at: '2026-05-21T00:00:00',
      },
      gold_label: {},
      visual_map: { emotion_thermometer: visualMap.emotion_thermometer, need_radar: visualMap.need_radar, boundary_band: visualMap.boundary_band, tension_dimensions: [] },
      latest_review: null,
      review_priority: { score: 86, reasons: ['缺专家复核', '高难度'] },
    },
  ],
  total: 1,
  principle: '复核优先处理高难度、高边界压力、缺专家版本或上次需要修订的样本。',
}

const analyticsCenter = {
  principle: '分析中心只展示聚合质量信号，不返回敏感原文。',
  scorecard: [
    { id: 'ai_success', label: 'AI 成功率', value: 78.6, target: 75, unit: '%', status: 'passed', gap: 0 },
    { id: 'import_quality', label: '导入质量', value: 88, target: 85, unit: 'score', status: 'passed', gap: 0 },
    { id: 'scheduler_health', label: '调度健康', value: 100, target: 100, unit: 'health', status: 'passed', gap: 0 },
  ],
  alerts: [{ priority: 'low', metric: 'import_quality', title: '继续来源复核', detail: '保持历史来源治理节奏。' }],
  timeline: [
    { id: 'ai', label: 'AI 质量', value: 78.6, status: 'passed' },
    { id: 'import', label: '导入质量', value: 88, status: 'passed' },
    { id: 'scheduler', label: '生产调度', value: 100, status: 'passed' },
  ],
  sections: {
    ai_quality: { summary: aiQuality.summary, trend: aiQuality.trend, next_actions: aiQuality.next_actions },
    ai_failures: { summary: { total: 1 }, clusters: [{ priority: 'low', action: 'fallback', reason: 'smoke' }] },
    provider: {
      provider: { name: 'deepseek', configured: true },
      recent: { success_rate: 78.6 },
      risk_level: 'low',
      diagnostics: [{ id: 'request_shape', status: 'passed' }],
      success_contract: {
        summary: {
          structured_success_rate: 78.6,
          raw_text_rate: 0,
          provider_failure_rate: 7.1,
          recoverable_success_rate: 92.9,
        },
        quality_gate: {
          structured_success_ok: true,
          raw_text_needs_review: false,
          provider_failure_needs_review: false,
        },
        contract_gaps: [{ id: 'fallback_watch', severity: 'low', fix: '保持降级路径和字段归一化回归。' }],
        task_matrix: [{ task_type: 'partner_simulation', runs: 14, structured_success_rate: 78.6, raw_text_rate: 0 }],
        principle: 'Provider 成功契约只看结构化结果和降级原因。',
      },
      probe_readiness: {
        status: 'ready_for_dry_run',
        live_probe_enabled: false,
        configured: true,
        blockers: [],
        runbook: [{ step: '1', title: 'Run dry-run probe', command: 'POST /api/analytics/ai-provider-probe?dry_run=true', expected: 'planned' }],
        recent_probe_logs: [],
        quality_gate: { dry_run_first: true },
        principle: '先 dry-run，再受控 live probe。',
      },
      failure_playbook: {
        risk_level: 'low',
        dominant_failure_reason: 'none',
        http_statuses: [],
        root_cause_matrix: [{ id: 'fallback_ok', severity: 'low', root_cause: '无高频失败', evidence: ['smoke'], operator_action: '保持观察', regression_case: 'controlled_live_probe' }],
        regression_cases: [{ id: 'controlled_live_probe', assertion: 'live probe must be explicitly enabled' }],
        runbook: [{ step: '1', title: 'Confirm local request shape', command: 'GET /api/analytics/ai-provider-diagnostics' }],
        quality_gate: { no_payload_leakage: true },
        principle: '只返回聚合根因。',
      },
    },
    scheduler: {
      status: 'healthy',
      checked_at: '2026-05-22T00:00:00',
      state_path: 'docs/tasks/production_scheduler_state.json',
      jobs: [
        { id: 'commander_sync_state_hourly', name: 'Commander 状态同步', observed: true, stale: false, required: true, latest_status: 'passed', latest_run_at: '2026-05-22T00:00:00', next_action: '保持调度观察。' },
      ],
      alerts: [],
      recovery_runbook: [{ step: '1', title: 'Inspect scheduler health', command: '.venv/bin/python -m tools.commander scheduler-health', expected: 'healthy' }],
      quality_gate: { required_jobs_observed: true },
      principle: '调度健康来自本地审计快照。',
    },
    gold_set: { summary: goldSummary.summary, quality_gates: goldSummary.quality_gates, open_conflicts: 0, next_actions: goldSummary.next_actions },
    import_quality: { quality_score: 88, quality_debt: { auto_repairable_fields: 0, manual_review_issues: 3, resolved_issues: 2 }, totals: { samples: 151, resources: 228, knowledge_entries: 170, active_issues: 3 } },
    vector_recall: { summary: { top10_recall: 1 }, recommendation: { threshold: 0.82 } },
    training_trends: { summary: relationshipTrends.summary, average_state_delta: relationshipTrends.average_state_delta, session_trend: relationshipTrends.session_trend },
  },
}

const auditCenter = {
  principle: '统一审计中心只展示结构化摘要和派生哈希。',
  summary: { events: 3, needs_attention: 1, latest_at: '2026-05-22T00:00:00', module_filter: 'all' },
  filters: {
    modules: [{ name: 'runtime', count: 1, rate: 33.3 }, { name: 'import', count: 1, rate: 33.3 }, { name: 'scheduler', count: 1, rate: 33.3 }],
    statuses: [{ name: 'recorded', count: 2, rate: 66.7 }, { name: 'needs_attention', count: 1, rate: 33.3 }],
    severities: [{ name: 'low', count: 2, rate: 66.7 }, { name: 'medium', count: 1, rate: 33.3 }],
  },
  events: [
    { id: 'runtime:1', module: 'runtime', source: 'frontend', action: 'api_error', status: 'recorded', severity: 'medium', target: { type: 'endpoint', id: '/api/smoke' }, summary: 'api_error · sha256:smoke', created_at: '2026-05-22T00:00:00', actor: 'runtime', details: { message_hash: 'sha256:smoke' } },
    { id: 'import:1', module: 'import', source: 'pipeline_run_logs', action: 'resolve', status: 'recorded', severity: 'low', target: { type: 'issue', id: 1 }, summary: 'import issue resolved', created_at: '2026-05-22T00:00:00', actor: 'smoke', details: { resolution_hash: 'sha256:resolution' } },
  ],
  next_actions: [{ priority: 'low', action: '继续运营审计', reason: '保持事件可追踪。' }],
}

const reviewedCandidates = {
  principle: 'Reviewed 资产必须经过人工确认、撤回和复审审计。',
  items: [
    { asset_type: 'resource', id: 1, uuid: 'resource-smoke', title: '低压承接素材', category: 'boundary', review_status: 'reviewed', reviewed_at: '2026-05-22T00:00:00', published_at: null, quality_signal: { quality_score: 92, source_trust: 'high' }, publish_ready: true, priority: { score: 91, reasons: ['高质量', '来源可信'] } },
  ],
  total: 1,
  publish_ready: 1,
  quality_gates: { has_publish_candidates: true, requires_manual_confirmation: true, minimum_priority_for_auto_publish: 90 },
  next_actions: [{ priority: 'medium', action: 'confirm_publish', reason: '人工确认后发布。' }],
}

const resourceSmoke = {
  id: 1,
  resource_uuid: 'resource-smoke-1',
  type: 'story',
  category: '冲突修复',
  title: '失望后的重新约定｜三步训练｜安全型D3',
  content: '场景：临时改约后，对方只回了一个“嗯”。\nTA说：嗯，知道了。\n常见失误：你别这样，我也不是故意的。\n更好回应：这个“嗯”我听着有失望。今晚我先不解释，先补一个确定的新时间：周六六点，可以吗？\n边界与同意：修复不是逼对方马上原谅，而是先承担影响并给出可靠行动。',
  emotional_intensity: 7,
  applicable_scene: '失望修复',
  difficulty_level: 3,
  gender_target: '通用',
  attachment_suitability: '安全型',
  usage_tip: '先承认影响，再给一个可执行的新约定。',
  effectiveness_rating: 9,
  source: 'project_original:smoke',
  source_url: 'https://www.gottman.com/',
  source_title: 'Gottman Institute',
  source_excerpt: '导读强调修复尝试和稳定行动。',
  source_summary: '用于冲突修复训练的来源导读，不保存第三方全文。',
  source_license: 'metadata_only',
  content_fingerprint: 'sha256:resource-smoke',
  quality_score: 93,
  tags: '具体案例,冲突修复,边界与同意',
  expression_tool_ids_json: '["expr_tool_015","expr_tool_027"]',
  expression_goal: '修复信任',
  expression_level: 'D3',
  speech_act: '承认影响',
  mistake_pattern: '过早解释',
  recommended_drills_json: '["影响承认","新约定"]',
  created_at: '2026-05-23T00:00:00',
}

const resourceFilters = {
  types: [{ value: 'story', label: '故事', count: 2 }],
  categories: [{ value: '冲突修复', label: '冲突修复', count: 2 }],
  scenes: [{ value: '失望修复', label: '失望修复', count: 2 }],
  tags: [{ value: '边界与同意', label: '边界与同意', count: 2 }],
  sources: [{ value: 'project_original:smoke', label: 'project_original:smoke', count: 2 }],
  expression_goals: [{ value: '修复信任', label: '修复信任', count: 2 }],
  expression_tools: [{ id: 'expr_tool_015', name: '情绪标注', count: 2 }],
  keywords: [{ value: '边界', label: '边界', count: 2 }],
  principle: '筛选建议来自 SQLite。',
}

const resourceSources = {
  items: [
    {
      source: 'public_anchor:gottman',
      name: 'Gottman Institute',
      source_url: 'https://www.gottman.com/',
      count: 2,
      group: '关系研究',
      summary: '关系修复和伴侣互动研究入口。',
      structure: '研究文章、训练课程、关系工具。',
      quality_notes: '高可信来源，metadata-only 使用。',
      link_status: 'verified_anchor',
      themes: ['冲突修复', '长期连接'],
      scenes: ['失望修复'],
    },
  ],
  total: 1,
}

const expressionToolSmoke = {
  id: 15,
  tool_uuid: 'expr_tool_015',
  name: '情绪标注',
  layer: 'emotion',
  layer_label: '情绪调节层',
  category: '降温承接',
  formula: '事实 -> 感受 -> 允许',
  description: '先命名对方可能的感受，再保留对方修正空间。',
  best_scenes: ['冲突', '修复'],
  relationship_fit: ['安全型', '焦虑型'],
  emotion_fit: ['失望', '委屈'],
  risk_flags: ['不得替对方定性'],
  micro_steps: ['观察原话', '轻命名感受', '允许对方修正', '给下一步'],
  mastery_stage: 'D3',
  review_status: 'published',
  quality_score: 94,
  source: 'project_original:expression_seed',
  source_url: 'https://example.com/expression',
  example_before: '你别这样。',
  example_after: '这个“嗯”我听着有点失望，如果我理解错你可以纠正我。',
}

const expressionTools = {
  items: [expressionToolSmoke],
  total: 1,
  layers: { emotion: '情绪调节层' },
  scenes: ['冲突', '修复'],
  goals: ['修复信任'],
  principle: '从场景、目标和情绪出发选择表达工具。',
}

const expressionChains = {
  items: [
    {
      id: 1,
      chain_uuid: 'chain-smoke',
      name: '修复信任三步链',
      goal: '修复信任',
      scene: '冲突',
      stage: 'D3',
      tool_ids: ['expr_tool_015'],
      sequence: [{ order: 1, tool: '情绪标注' }],
      forbidden_tools: ['逼迫原谅'],
      example_dialogue: { after: '我听见这里可能有失望，我们先把新时间定稳。' },
      review_status: 'published',
      quality_score: 92,
    },
  ],
  total: 1,
}

const expressionRecommendation = {
  scene: '修复',
  goal: '修复信任',
  chains: expressionChains.items,
  tools: [expressionToolSmoke],
  principle: '先承接，再修复。',
}

const importIssue = {
  id: 1,
  batch_id: 1,
  source_name: 'legacy-json',
  source_id: 'legacy-1',
  severity: 'warning',
  message: '历史来源缺少 reviewed evidence。',
  status: 'open',
  reviewer_id: null,
  resolution_hash: null,
  resolved_at: null,
  created_at: '2026-05-22T00:00:00',
  updated_at: '2026-05-22T00:00:00',
}

const importIssuesQueue = {
  principle: '历史导入 issue 必须带 reviewer 与 resolution 才能关闭。',
  items: [importIssue],
  total: 1,
  status: 'active',
  summary: {
    total: 1,
    active: 1,
    resolved: 0,
    by_status: { open: 1 },
    by_severity: { warning: 1 },
    quality_gate: { requires_resolution_reason: true, requires_reviewer: true, auto_close_allowed: false },
  },
  source_groups: [
    {
      source_name: 'legacy-json',
      total_issues: 1,
      active_issues: 1,
      resolved_issues: 0,
      by_status: { open: 1 },
      by_severity: { warning: 1 },
      severity_weight: 1,
      oldest_active_at: '2026-05-22T00:00:00',
      latest_active_at: '2026-05-22T00:00:00',
      sample_issue_ids: [1],
      recommended_action: '可按来源复核后批量关闭',
      review_packet: {
        source_name: 'legacy-json',
        scope: { total_issues: 1, active_issues: 1, resolved_issues: 0, status_counts: { open: 1 }, severity_counts: { warning: 1 } },
        evidence_checklist: [{ id: 'source_contract', label: '来源合同', required_for: 'resolve', evidence: 'metadata-only' }],
        sample_evidence: [{ issue_id: 1, source_id: 'legacy-1', severity: 'warning', status: 'open', message_summary: '历史来源缺少 reviewed evidence', message_hash: 'sha256:issue', updated_at: '2026-05-22T00:00:00' }],
        batch_action: { recommended_action: 'resolve', candidate_issue_ids: [1], can_close_batch: true, default_action: 'resolve', requires_resolution: true, requires_reviewer: true, auto_close_allowed: false },
        quality_gate: { no_raw_text: true },
        principle: '复核来源证据后再关闭。',
      },
    },
  ],
}

const importIssueAudit = {
  principle: '导入 issue 审计历史不回显人工说明全文或来源原文。',
  items: [
    { id: 1, issue_id: 1, action: 'resolve', source_name: 'legacy-json', source_id: 'legacy-1', severity: 'warning', from_status: 'open', to_status: 'resolved', reviewer_id: 'smoke', resolution_hash: 'sha256:resolution', safety: { raw_source_text_saved: false, resolution_text_returned: false, auto_close_allowed: false }, created_at: '2026-05-22T00:00:00' },
  ],
  total: 1,
  summary: { actions: { resolve: 1 }, to_status: { resolved: 1 }, sources: { 'legacy-json': 1 }, severity: { warning: 1 }, reviewers: { smoke: 1 }, unsafe_log_count: 0 },
  quality_gate: { raw_source_text_saved: false, resolution_text_returned: false, requires_pipeline_log: true, auto_close_allowed: false },
}

function json(data) {
  return { status: 200, contentType: 'application/json', body: JSON.stringify(data) }
}

function errorJson(status, detail) {
  return { status, contentType: 'application/json', body: JSON.stringify({ detail }) }
}

function mockFor(url, method, scenario = 'happy') {
  const path = new URL(url).pathname
  if (scenario === 'trainer_compare_failure' && method === 'POST' && path === '/api/training/compare') return errorJson(500, 'smoke compare failure')
  if (scenario === 'partner_simulate_failure' && method === 'POST' && path === '/api/training/partner/simulate') return errorJson(503, 'smoke partner failure')
  if (scenario === 'partner_review_failure' && path === '/api/training/partner/sessions/101/review') return errorJson(503, 'smoke review failure')
  if (method === 'POST' && path.includes('/training/reviews/')) return json({ ok: true, next_review: '2026-05-23', reviewed: true })
  if (method === 'POST' && path === '/api/training/partner/simulate') return json(partnerSimulateResponse)
  if (path === '/api/training/partner/sessions/101/review') return json(partnerSessionReview)
  if (path === '/api/training/partner/provider-status') return json(providerStatus)
  if (method === 'POST' && path === '/api/training/compare') return json({
    score: 82,
    differences: [{ type: 'strength', name: '边界尊重', desc: '回应里给了对方空间。' }],
    suggestions: ['补一句轻验证。'],
    ideal_response: sample.good_response_soft,
    diff_report: '整体低压承接有效。',
    dimension_scores: { emotion_score: 80, need_score: 76, safety_score: 86, connection_score: 78, boundary_score: 88, style_score: 80, repair_score: 74 },
    next_recommendation: '继续练习轻验证。',
    scoring_source: 'rule_fallback',
    metacognitive_review: {
      principle: '事实和解释分离。',
      fact_interpretation_split: { observable_facts: ['对方说累了'], interpretations_to_hold_lightly: ['不一定是不在乎'] },
      three_hypotheses: [{ name: '疲惫', content: '对方可能需要休息。' }],
      verification_questions: ['你是想先休息一下吗？'],
      next_minimum_action: '承接后给退路。',
      reflection_questions: ['我有没有把解释当事实？'],
    },
  })
  if (path === '/api/training/radar') return json(radar)
  if (path === '/api/training/mistakes') return json([mistake])
  if (path === '/api/training/reviews/due') return json([{ mistake_id: 7, sample, next_review: '2026-05-22' }])
  if (path === '/api/training/summary/today') return json({ date: '2026-05-21', attempts_count: 3, average_score: 74, mistakes_open: 1, completed: false, recommendation: '完成一次边界承接训练' })
  if (path === '/api/training/summary/week') return json({ start_date: '2026-05-18', end_date: '2026-05-24', attempts_count: 11, active_days: 4, average_score: 76, streak_hint: '保持节奏' })
  if (path === '/api/training/next') return json({ type: 'new', reason: '最弱维度：需求洞察', sample, weakest_dimension: 'need_score', visual_map: visualMap })
  if (path === '/api/profile') return json({ id: 1, email: 'smoke@example.com', attachment_style: 'secure', core_wound: '边界焦虑', love_language: 'words', perception_baseline: 76, emotion_vocab_size: 128, progress_json: '{}' })
  if (path === '/api/resources') return json({ items: [resourceSmoke, { ...resourceSmoke, id: 2, resource_uuid: 'resource-smoke-2', title: '边界确认后的低压修复' }], total: 2, page: 1, limit: 48, offset: 0 })
  if (path === '/api/resources/filters') return json(resourceFilters)
  if (path === '/api/resources/sources') return json(resourceSources)
  if (path === '/api/resources/random') return json(resourceSmoke)
  if (path === '/api/resources/types') return json(['story'])
  if (path === '/api/resources/similarity') return json({
    summary: { scanned: 2, clusters: 1, queued_items: 2, threshold: 0.82, limit: 1000, method: 'smoke' },
    clusters: [
      {
        cluster_id: 'resource-similarity-smoke',
        kind: 'semantic_family',
        family_key: '冲突修复::失望修复',
        size: 2,
        highest_similarity: 0.91,
        average_similarity: 0.86,
        pair_count: 1,
        recommended_action: 'keep_but_diversify_sorting',
        items: [
          { id: 1, resource_uuid: 'resource-smoke-1', title: resourceSmoke.title, type: 'story', category: '冲突修复', applicable_scene: '失望修复', quality_score: 93, review_status: 'published', source: 'project_original:smoke', tags: '具体案例' },
          { id: 2, resource_uuid: 'resource-smoke-2', title: '边界确认后的低压修复', type: 'story', category: '冲突修复', applicable_scene: '失望修复', quality_score: 91, review_status: 'published', source: 'project_original:smoke', tags: '具体案例' },
        ],
      },
    ],
    principle: '近重复队列用于审计，不自动删除。',
    next_actions: [{ priority: 'low', action: '保持多样化排序', reason: 'smoke 数据仅用于门禁。' }],
  })
  if (path.startsWith('/api/resources/') && /^\/api\/resources\/\d+$/.test(path)) return json(resourceSmoke)
  if (path === '/api/expression/tools') return json(expressionTools)
  if (path === '/api/expression/chains') return json(expressionChains)
  if (path === '/api/expression/recommend') return json(expressionRecommendation)
  if (path.startsWith('/api/expression/tools/')) return json(expressionToolSmoke)
  if (path === '/api/analytics/ai-quality') return json(aiQuality)
  if (path === '/api/analytics/relationship-trends') return json(relationshipTrends)
  if (path === '/api/analytics/center') return json(analyticsCenter)
  if (path === '/api/analytics/audit-center') return json(auditCenter)
  if (path === '/api/samples/gold/summary') return json(goldSummary)
  if (path === '/api/samples/gold/review-queue') return json(goldQueue)
  if (path === '/api/learning/framework') return json(mockFramework())
  if (path === '/api/learning/curriculum-graph') return json(mockCurriculumGraph())
  if (path === '/api/knowledge/sections') return json([{ id: 1, section_uuid: 's1', name: '关系元基础', description: '底层概念', icon: 'K', sort_order: 1, source: 'smoke' }])
  if (path === '/api/knowledge/entries') return json([{ id: 1, entry_uuid: 'e1', section_id: 1, title: '边界不是拒绝', subtitle: '承接与空间', summary: '用低压方式保护连接。', content: '边界是让关系可持续的结构。', category: 'boundary', tags: ['边界'], quality_score: 91, source: 'smoke', created_at: '2026-05-21T00:00:00' }])
  if (path === '/api/knowledge/imports/latest') return json({ latest: { id: 1, source_name: 'smoke.json', source_type: 'json', imported_sections: 1, imported_entries: 3, skipped_entries: 0, issues_count: 0, status: 'completed', report: {}, created_at: '2026-05-21T00:00:00' }, principle: '导入可追踪。' })
  if (path === '/api/knowledge/visual-map') return json(mockKnowledgeVisualMap())
  if (path.startsWith('/api/knowledge/entries/')) return json({ id: 1, entry_uuid: 'e1', section_id: 1, title: '边界不是拒绝', content: '边界是让关系可持续的结构。', category: 'boundary', tags: ['边界'], quality_score: 91, source: 'smoke', created_at: '2026-05-21T00:00:00' })
  if (path === '/api/evolution/latest') return json(mockEvolutionLatest())
  if (path === '/api/evolution/pipeline') return json(mockEvolutionPipeline())
  if (path === '/api/evolution/dedupe/report') return json({ principle: '重复先审计。', method: { exact: 'hash', semantic: 'title', vector_ready: 'ready' }, summary: { scanned: 8, clusters: 1, exact_clusters: 0, semantic_clusters: 1, duplicate_review_needed: 1 }, clusters: [] })
  if (path === '/api/evolution/import-quality') return json({ principle: '导入质量闭环。', totals: { samples: 151, resources: 228, knowledge_entries: 170, batches: 20, issues: 1, active_issues: 1 }, field_completeness: { samples: { required: { context: 1 }, enriched: { quality_json: 0.8 }, json_invalid: 0 } }, source_distribution: {}, issue_summary: { by_severity: { warning: 1 }, by_status: { open: 1 }, open: 1, resolved: 0, recent: [importIssue] }, latest_batches: [], quality_score: 88, quality_debt: { auto_repairable_fields: 0, manual_review_issues: 1, resolved_issues: 0, issue_status: { open: 1 }, status: 'needs_review', next_actions: ['按来源复核'] } })
  if (path === '/api/evolution/import-quality/issues') return json(importIssuesQueue)
  if (path === '/api/evolution/import-quality/issues/audit') return json(importIssueAudit)
  if (path === '/api/evolution/reviewed-assets/publish-candidates') return json(reviewedCandidates)
  if (path === '/api/evolution/safety-events') return json({ summary: { total: 1, blocked: 1, by_risk: { high: 1 }, top_flags: ['manipulation'] }, events: [] })
  return json({})
}

function mockFramework() {
  return {
    version: '1.0',
    axiom: '人性无限，学习必须分类。',
    primitive_ladder: [1, 2, 3, 4, 5].map((level) => ({ level, name: `第${level}层`, unit: '信号', question: '此刻发生了什么？', visual: '节点' })),
    classification_tree: [{ id: 'boundary', name: '边界', axis: ['安全', '连接'], children: ['低压承接', '轻验证'] }],
    five_w_two_h: [{ key: 'why', label: 'Why', question: '为什么此刻需要空间？' }],
    visual_components: [{ id: 'thermo', name: '情绪温度计', numeric: ['强度'], visual: '色带', training_use: '判断回应强度' }],
    mastery_stages: [{ level: 1, name: '识别', definition: '能看见信号', test: '说出事实' }],
    three_natures_management: [{ nature: '趋利', management: '奖励', relationship_use: '正向反馈' }],
    question_templates: [{ scene: '边界', template: '你希望我怎么陪你更舒服？' }],
  }
}

function mockCurriculumGraph() {
  const nodes = Array.from({ length: 8 }, (_, index) => ({
    id: `stage-${index + 1}`,
    index: index + 1,
    name: `第${index + 1}阶`,
    primitive: '情绪-需求-边界',
    description: '用证据推进关系能力。',
    tools: ['训练中心', '错题本'],
    tasks: ['识别', '回应'],
    promotion_rule: '连续三次达到 80 分',
    progress: index < 2 ? 100 : index === 2 ? 55 : 0,
    status: index < 2 ? 'completed' : index === 2 ? 'current' : 'locked',
    is_completed: index < 2,
    is_current: index === 2,
    difficulty: index < 4 ? 'foundation' : 'advanced',
    score_formula: 'score = attempts + review',
    evidence: { attempts_count: 3, average_training_score: 76, open_mistakes: 1, partner_sessions: 1, partner_turns: 4, safety_blocks: 0, evidence_label: '证据有效' },
    next_action: '完成一次边界承接训练',
  }))
  return {
    version: '1.0',
    axiom: '每一阶都有任务、评分、证据和晋级条件。',
    current_node_id: 'stage-3',
    current_stage: nodes[2],
    overall_progress: 32,
    nodes,
    edges: [],
    practice_plan: { focus_node_id: 'stage-3', focus: '需求洞察', minimum_action: '写一个轻验证问题', drills: ['承接一句', '验证一句'], reflection: '事实和解释分离' },
    evidence_summary: { training_attempts: 11, open_mistakes: 1, partner_sessions: 1, partner_events: 4, safety_blocks: 0, principle: '用证据而非感觉晋级。' },
    visual_layers: [{ id: 'gate', name: '关口', use: '判断当前阶段' }],
  }
}

function mockKnowledgeVisualMap() {
  return {
    principle: '知识必须可检索、可解释、可训练。',
    concept_graph: {
      nodes: [
        { id: 'root', label: '关系元基础', type: 'root', weight: 8, x: 50, y: 20 },
        { id: 'boundary', label: '边界', type: 'section', weight: 6, x: 35, y: 55 },
        { id: 'need', label: '需求', type: 'category', weight: 5, x: 65, y: 55 },
      ],
      edges: [{ from: 'root', to: 'boundary', label: '包含' }, { from: 'root', to: 'need', label: '包含' }],
    },
    classification_tree: [{ id: 'boundary', name: '边界', kind: 'section', count: 6, quality: 91, children: [{ id: 'space', name: '空间', kind: 'tag', count: 3 }] }],
    five_w_two_h_cards: [{ key: 'why', label: 'Why', question: '为什么？', answer: '先看需求。' }],
    tool_fit_map: [{ tool: '轻验证', use: '降低误读', matched_entries: 4, signal: 80, fit_score: 88, examples: ['你是想先休息一下吗？'] }],
    coverage: { sections: 1, entries: 3, categories: 2, tags: 4, average_quality: 91 },
  }
}

function mockEvolutionLatest() {
  return {
    items: [{ id: 1, title: '边界样本', content: '低压承接', summary: '新增金样本', category: 'boundary', tags: ['边界'], quality_score: 92, status: 'published', created_at: '2026-05-21T00:00:00' }],
    latest_report: { id: 1, period_type: 'weekly', title: '周进化报告', summary: '完成来源审计和发布漏斗。', new_items_count: 4, promoted_samples_count: 2, key_insights: ['边界样本增长'], created_at: '2026-05-21T00:00:00' },
    summary: { heartbeat: { state: 'learning', label: '学习中', message: '稳定吸收新样本' }, totals: { sources: 1, active_sources: 1, items: 4, candidates: 3, published: 2, rejected: 0 }, status_counts: {}, category_counts: {}, source_type_counts: {}, sources: [], quality: { average_score: 90, publish_rate: 0.5, distribution: { excellent: 2, strong: 1, usable: 1, needs_review: 0 } }, next_actions: [], visual_metrics: evolutionVisualMetrics, last_item_at: '2026-05-21T00:00:00' },
    principle: 'SQLite 是唯一真数据源。',
  }
}

function mockEvolutionPipeline() {
  return {
    principle: '从来源到训练资产全链路可审计。',
    stages: [
      { id: 'raw', name: '原始候选', count: 12, risk_gate: '脱敏' },
      { id: 'review', name: '结构标注', count: 10, risk_gate: '复核' },
      { id: 'asset', name: '训练资产', count: 6, risk_gate: '发布门禁' },
    ],
    classification_axes: ['边界', '需求', '安全'],
    status_counts: { raw: { pending: 2 }, annotation: { reviewed: 10 }, assets: { published: 6 } },
    sources: [],
    raw_items: [],
    annotation_jobs: [],
    asset_versions: [],
    recent_logs: [{ id: 1, target_type: 'asset', target_id: 1, action: 'publish', from_status: 'reviewed', to_status: 'published', result: {}, message: '进入训练闭环', created_at: '2026-05-21T00:00:00' }],
    visual_metrics: evolutionVisualMetrics,
    next_actions: [{ priority: 'high', action: '增加金样本', reason: '提升泛化质量' }],
  }
}

async function waitForServer() {
  const deadline = Date.now() + 20000
  while (Date.now() < deadline) {
    try {
      const response = await fetch(baseURL)
      if (response.ok) return
    } catch {
      // Vite is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 250))
  }
  throw new Error(`Vite server did not start on ${baseURL}`)
}

async function inspectPage(page) {
  return page.evaluate(() => {
    const viewportWidth = window.innerWidth
    const rootOverflow = Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - viewportWidth
    const visible = Array.from(document.querySelectorAll('h1,h2,h3,p,button,a,input,textarea'))
      .filter((el) => {
        const rect = el.getBoundingClientRect()
        const style = window.getComputedStyle(el)
        const inViewport = rect.bottom > 0 && rect.top < window.innerHeight && rect.right > 0 && rect.left < window.innerWidth
        if (!inViewport || rect.width <= 4 || rect.height <= 4 || style.visibility === 'hidden' || style.display === 'none') return false
        const x = Math.min(window.innerWidth - 1, Math.max(0, rect.left + rect.width / 2))
        const y = Math.min(window.innerHeight - 1, Math.max(0, rect.top + rect.height / 2))
        const hit = document.elementFromPoint(x, y)
        return Boolean(hit && (el.contains(hit) || hit.contains(el)))
      })
      .map((el) => ({ el, rect: el.getBoundingClientRect(), label: (el.textContent || el.getAttribute('placeholder') || el.tagName).trim().slice(0, 60) }))

    const overlaps = []
    for (let i = 0; i < visible.length; i += 1) {
      for (let j = i + 1; j < visible.length; j += 1) {
        const a = visible[i]
        const b = visible[j]
        if (a.el.contains(b.el) || b.el.contains(a.el)) continue
        const left = Math.max(a.rect.left, b.rect.left)
        const right = Math.min(a.rect.right, b.rect.right)
        const top = Math.max(a.rect.top, b.rect.top)
        const bottom = Math.min(a.rect.bottom, b.rect.bottom)
        const area = Math.max(0, right - left) * Math.max(0, bottom - top)
        const minArea = Math.min(a.rect.width * a.rect.height, b.rect.width * b.rect.height)
        if (area > 24 && area / Math.max(1, minArea) > 0.35) {
          overlaps.push({ a: a.label, b: b.label })
        }
      }
    }
    return {
      horizontalOverflow: rootOverflow > 2 ? rootOverflow : 0,
      overlaps: overlaps.slice(0, 5),
      hasHeading: Boolean(document.querySelector('h1')),
      title: document.title,
    }
  })
}

async function exerciseTrainerAI(page) {
  await page.goto(`${baseURL}/trainer-ai`, { waitUntil: 'domcontentloaded' })
  await page.getByText('小回避', { exact: true }).click()
  await page.locator('textarea[placeholder="输入你的回应..."]').fill('我理解你今天比较累，不急着回复，我在。')
  await page.locator('button[title="发送回应"]').click()
  await page.getByText('谢谢你这样说', { exact: false }).waitFor({ state: 'visible', timeout: 8000 })
  await page.getByText('会话状态曲线', { exact: false }).waitFor({ state: 'visible', timeout: 8000 })
  const inspection = await inspectPage(page)
  const text = await page.locator('body').innerText()
  return {
    ...inspection,
    hasPartnerReply: text.includes('谢谢你这样说'),
    hasSessionReview: text.includes('会话状态曲线'),
    hasScore: text.includes('82'),
    hasInputUnlocked: await page.locator('textarea[placeholder="输入你的回应..."]').isEnabled(),
  }
}

async function exerciseTrainerFailure(page) {
  await page.goto(`${baseURL}/trainer`, { waitUntil: 'domcontentloaded' })
  await page.locator('textarea[placeholder="先接住情绪，再回应需求。写下你会怎么说..."]').fill('我理解你累了，不急着回复。')
  await page.getByText('提交并生成七维反馈', { exact: true }).click()
  await page.getByText('评分提交失败', { exact: false }).waitFor({ state: 'visible', timeout: 8000 })
  const inspection = await inspectPage(page)
  const responseValue = await page.locator('textarea[placeholder="先接住情绪，再回应需求。写下你会怎么说..."]').inputValue()
  const text = await page.locator('body').innerText()
  return {
    ...inspection,
    hasSubmitError: text.includes('评分提交失败'),
    preservedResponse: responseValue.includes('我理解你累了'),
  }
}

async function exerciseTrainerResourceContext(page) {
  await page.goto(`${baseURL}/trainer?resource_id=1&q=边界&category=冲突修复&page=2`, { waitUntil: 'domcontentloaded' })
  await page.getByText('来自资源海洋的训练上下文', { exact: false }).waitFor({ state: 'visible', timeout: 8000 })
  await page.getByText('用资源提示预填回应', { exact: true }).click()
  const inspection = await inspectPage(page)
  const text = await page.locator('body').innerText()
  const responseValue = await page.locator('textarea[placeholder="先接住情绪，再回应需求。写下你会怎么说..."]').inputValue()
  const resourceHref = await page.getByText('回看资源', { exact: true }).evaluate((el) => el.closest('a')?.getAttribute('href') || '')
  await page.getByText('只做普通训练', { exact: true }).click()
  await page.waitForURL((url) => url.pathname === '/trainer' && !url.searchParams.has('resource_id'), { timeout: 8000 })
  const afterClearText = await page.locator('body').innerText()
  return {
    ...inspection,
    hasResourceContext: text.includes('来自资源海洋的训练上下文') && text.includes(resourceSmoke.title),
    hasPrefill: responseValue.includes('失望修复') && responseValue.includes('修复信任') && responseValue.includes('过早解释'),
    resourceHref,
    clearedResourceContext: !afterClearText.includes('来自资源海洋的训练上下文'),
    keptFilterQuery: new URL(page.url()).searchParams.get('q') === '边界' && new URL(page.url()).searchParams.get('category') === '冲突修复',
  }
}

async function exerciseMistakeResourceContext(page) {
  await page.goto(`${baseURL}/mistakes?resource_id=1&q=过早解释`, { waitUntil: 'domcontentloaded' })
  await page.getByText('来自资源海洋的错题改写上下文', { exact: false }).waitFor({ state: 'visible', timeout: 8000 })
  const inspection = await inspectPage(page)
  const text = await page.locator('body').innerText()
  const resourceHref = await page.getByText('回看资源', { exact: true }).evaluate((el) => el.closest('a')?.getAttribute('href') || '')
  const trainerHref = await page.getByText('带入训练', { exact: true }).evaluate((el) => el.closest('a')?.getAttribute('href') || '')
  await page.getByText('只看全部错题', { exact: true }).click()
  await page.waitForURL((url) => url.pathname === '/mistakes' && !url.searchParams.has('resource_id'), { timeout: 8000 })
  const afterClearText = await page.locator('body').innerText()
  return {
    ...inspection,
    hasResourceMistakeContext: text.includes('来自资源海洋的错题改写上下文') && text.includes(resourceSmoke.title),
    hasGuidance: text.includes('过早解释') && text.includes('修复信任') && text.includes('失望修复'),
    resourceHref,
    trainerHref,
    clearedResourceContext: !afterClearText.includes('来自资源海洋的错题改写上下文'),
    keptSearchQuery: new URL(page.url()).searchParams.get('q') === '过早解释',
  }
}

async function exerciseSettingsExport(page) {
  await page.goto(`${baseURL}/settings`, { waitUntil: 'domcontentloaded' })
  await page.locator('button').filter({ hasText: '数据' }).click()
  await page.getByText('导出我的数据', { exact: true }).waitFor({ state: 'visible', timeout: 8000 })
  await page.locator('button').filter({ hasText: '导出' }).click()
  await page.getByText('Markdown 导出已生成', { exact: true }).waitFor({ state: 'visible', timeout: 8000 })
  const inspection = await inspectPage(page)
  const text = await page.locator('body').innerText()
  const downloadName = await page.getByText('下载到默认目录', { exact: true }).evaluate((el) => el.closest('a')?.getAttribute('download') || '')
  const downloadHref = await page.getByText('下载到默认目录', { exact: true }).evaluate((el) => el.closest('a')?.getAttribute('href') || '')
  return {
    ...inspection,
    hasExportPanel: text.includes('Markdown 导出已生成') && text.includes('校验指纹') && text.includes('结构化记录'),
    hasCoverage: text.includes('个人资料') && text.includes('错题记录') && text.includes('训练摘要'),
    hasMarkdownFormat: text.includes('.md') && text.includes('选择位置保存') && text.includes('下载到默认目录'),
    hasLocationHint: text.includes('浏览器默认下载目录') || text.includes('你刚才在系统窗口中选择的位置'),
    downloadHrefIsBlob: downloadHref.startsWith('blob:'),
    downloadName,
  }
}

async function exerciseSettingsReminder(page) {
  await page.goto(`${baseURL}/settings`, { waitUntil: 'domcontentloaded' })
  await page.locator('button').filter({ hasText: '偏好' }).click()
  await page.getByText('训练偏好', { exact: true }).waitFor({ state: 'visible', timeout: 8000 })
  const inspection = await inspectPage(page)
  const text = await page.locator('body').innerText()
  const reminderTime = await page.locator('input[type="time"]').inputValue()
  return {
    ...inspection,
    hasReminderSection: text.includes('每日提醒') && text.includes('提醒时间'),
    hasLocalBoundary: text.includes('浏览器本地通知') && text.includes('不是手机后台推送'),
    hasPermissionBoundary: text.includes('需要允许通知权限') && text.includes('页面或浏览器保持打开'),
    hasTestButton: text.includes('测试提醒'),
    reminderTime,
  }
}

async function exerciseExpressionSearchSuggestions(page) {
  await page.goto(`${baseURL}/expression`, { waitUntil: 'domcontentloaded' })
  await page.getByRole('heading', { name: '表达工具箱' }).waitFor({ state: 'visible', timeout: 8000 })
  const searchInput = page.locator('input[placeholder*="幽默自嘲"]').first()
  await searchInput.click()
  const before = await page.evaluate(() => {
    const input = document.querySelector('input[placeholder*="幽默自嘲"]')
    const menu = document.querySelector('[data-expression-search-menu]')
    const options = Array.from(document.querySelectorAll('[data-expression-search-suggestion]')).map((button) => button.getAttribute('data-expression-search-suggestion') || '')
    const body = document.body.innerText
    return {
      hasDatalistInput: Boolean(input),
      optionCount: options.length,
      hasToolSuggestion: options.includes('情绪标注'),
      hasGuidance: body.includes('输入框下方展开') && body.includes('微步骤'),
      hasSuggestionGroups: Boolean(menu) && body.includes('工具概念') && body.includes('使用场景') && body.includes('表达目标') && body.includes('表达公式'),
      hasSearchWorkbench: body.includes('检索与筛选') && body.includes('重置筛选') && body.includes('应用筛选'),
      hasChainAboveList: body.includes('工具链推荐') && body.includes('按当前条件推荐'),
    }
  })
  await page.locator('[data-expression-search-suggestion="情绪标注"]').click()
  await searchInput.evaluate((input) => input.value).then((value) => {
    if (value !== '情绪标注') throw new Error(`expression search value mismatch: ${value}`)
  })
  await page.getByRole('heading', { name: '情绪标注' }).waitFor({ state: 'visible', timeout: 8000 })
  const inspection = await inspectPage(page)
  const text = await page.locator('body').innerText()
  await page.getByText('详情', { exact: true }).first().click()
  await page.getByText('概念定义', { exact: true }).waitFor({ state: 'visible', timeout: 8000 })
  const expandedText = await page.locator('body').innerText()
  return {
    ...inspection,
    ...before,
    filteredToTool: text.includes('情绪标注') && text.includes('先命名对方可能的感受'),
    hasActiveSearchChip: text.includes('当前条件') && text.includes('搜索：情绪标注'),
    hasLearningDetails: expandedText.includes('概念定义') && expandedText.includes('核心原则') && expandedText.includes('实践方法') && expandedText.includes('适用场景') && expandedText.includes('迁移练习'),
  }
}

async function exercisePathLearningScaffold(page) {
  await page.goto(`${baseURL}/path`, { waitUntil: 'domcontentloaded' })
  await page.getByRole('heading', { name: '从默认沉默到被爱的证据路线' }).waitFor({ state: 'visible', timeout: 8000 })
  await page.getByRole('heading', { name: '这条路线到底在训练什么' }).waitFor({ state: 'visible', timeout: 8000 })
  const inspection = await inspectPage(page)
  const text = await page.locator('body').innerText()
  return {
    ...inspection,
    hasLearningOverview: text.includes('八阶路径不是恋爱技巧清单') && text.includes('先证据后判断') && text.includes('先安全后张力'),
    hasStageScaffold: text.includes('概念定义') && text.includes('核心原则') && text.includes('实践方法') && text.includes('适用场景') && text.includes('常见误区'),
    hasExamples: text.includes('低质量做法') && text.includes('更好做法') && text.includes('本阶练习题'),
    hasConcreteStage: text.includes('信息阶训练事实交换') && text.includes('把一个查户口式问题改成') || text.includes('默认沉默指注意力缩回自己脑内') && text.includes('今天任选一个场景，写下 3 个外部事实'),
  }
}

async function exerciseResourceLearningScaffold(page) {
  await page.goto(`${baseURL}/resources`, { waitUntil: 'domcontentloaded' })
  await page.getByRole('heading', { name: '资源海洋' }).waitFor({ state: 'visible', timeout: 8000 })
  await page.getByText('学习拆解', { exact: true }).first().waitFor({ state: 'visible', timeout: 8000 })
  const listInspection = await inspectPage(page)
  const listText = await page.locator('body').innerText()

  await page.goto(`${baseURL}/resources/1?q=边界&category=冲突修复&page=2`, { waitUntil: 'domcontentloaded' })
  await page.getByRole('heading', { name: resourceSmoke.title }).waitFor({ state: 'visible', timeout: 8000 })
  await page.getByRole('heading', { name: '学习拆解' }).waitFor({ state: 'visible', timeout: 8000 })
  const detailInspection = await inspectPage(page)
  const detailText = await page.locator('body').innerText()

  return {
    list: listInspection,
    detail: detailInspection,
    hasListScaffold: listText.includes('学习拆解') && listText.includes('概念定义') && listText.includes('核心原则') && listText.includes('实践方法') && listText.includes('练习任务'),
    hasListComparison: listText.includes('低质量回应') && listText.includes('更好回应') && listText.includes('你别这样，我也不是故意的'),
    hasSourceBoundary: listText.includes('有原文入口') || listText.includes('项目原创训练卡') || listText.includes('结构化导读卡'),
    hasDetailScaffold: detailText.includes('学习拆解') && detailText.includes('概念定义') && detailText.includes('核心原则') && detailText.includes('实践方法') && detailText.includes('适用场景'),
    hasDetailExamples: detailText.includes('低质量做法') && detailText.includes('更好做法') && detailText.includes('练习任务'),
    hasCopyrightBoundary: detailText.includes('本页展示的是结构化学习拆解') || detailText.includes('不伪装为外部原文'),
    horizontalOverflow: Math.max(listInspection.horizontalOverflow, detailInspection.horizontalOverflow),
    overlaps: [...listInspection.overlaps, ...detailInspection.overlaps],
    hasHeading: listInspection.hasHeading && detailInspection.hasHeading,
  }
}

async function exerciseTocCollapseLayout(page, path) {
  await page.goto(`${baseURL}${path}`, { waitUntil: 'domcontentloaded' })
  await page.getByRole('button', { name: '折叠目录' }).waitFor({ state: 'visible', timeout: 8000 })
  const before = await page.evaluate(() => {
    const wideColumns = Array.from(document.querySelectorAll('.grid'))
      .map((el) => getComputedStyle(el).gridTemplateColumns)
      .filter((columns) => columns.includes('280px') || columns.includes('300px'))
    const button = document.querySelector('button[aria-label="折叠目录"]')
    const rect = button?.getBoundingClientRect()
    return {
      wideColumns,
      buttonRight: rect ? Math.round(window.innerWidth - rect.right) : null,
    }
  })
  await page.getByRole('button', { name: '折叠目录' }).click()
  const after = await page.evaluate(() => {
    const wideColumns = Array.from(document.querySelectorAll('.grid'))
      .map((el) => getComputedStyle(el).gridTemplateColumns)
      .filter((columns) => columns.includes('280px') || columns.includes('300px'))
    const button = document.querySelector('button[aria-label="展开目录"]')
    const rect = button?.getBoundingClientRect()
    return {
      wideColumns,
      buttonRight: rect ? Math.round(window.innerWidth - rect.right) : null,
      hasExpandButton: Boolean(button),
      horizontalOverflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth),
    }
  })
  return {
    before,
    after,
    releasedSidebarColumn: before.wideColumns.length > 0 && after.wideColumns.length === 0,
    fixedToRight: typeof after.buttonRight === 'number' && after.buttonRight <= 40,
    noOverflow: after.horizontalOverflow <= 2,
  }
}

async function exerciseProfileEvidence(page) {
  await page.goto(`${baseURL}/profile`, { waitUntil: 'domcontentloaded' })
  await page.getByRole('heading', { name: '我的档案' }).waitFor({ state: 'visible', timeout: 8000 })
  await page.getByRole('heading', { name: '计算依据' }).waitFor({ state: 'visible', timeout: 8000 })
  const inspection = await inspectPage(page)
  const text = await page.locator('body').innerText()
  return {
    ...inspection,
    hasProfileHeading: text.includes('我的档案'),
    hasRadar: text.includes('能力成长曲线') && text.includes('需求洞察') && text.includes('76%'),
    hasRealStats: text.includes('今日训练') && text.includes('近 7 天训练') && text.includes('近 7 天活跃') && text.includes('平均得分'),
    hasMockValues: text.includes('边界焦虑') && text.includes('128 个') && text.includes('11') && text.includes('4') && text.includes('76'),
    hasEvidence: text.includes('/api/profile') && text.includes('/api/training/radar') && text.includes('/api/training/summary/week'),
    removedHardcodedStats: !text.includes('总训练次数') && !text.includes('连续打卡') && !text.includes('已学样本') && !text.includes('156'),
    removedStaticAwareness: !text.includes('面对冲突时倾向于回避，事后才反思如何改进') && !text.includes('情绪强度识别、即时反应速度、开放式提问'),
  }
}

async function exerciseTrainerAIPartnerFailure(page) {
  await page.goto(`${baseURL}/trainer-ai`, { waitUntil: 'domcontentloaded' })
  await page.getByText('小回避', { exact: true }).click()
  await page.locator('textarea[placeholder="输入你的回应..."]').fill('我理解你今天比较累，不急着回复，我在。')
  await page.locator('button[title="发送回应"]').click()
  await page.getByText('本地安全降级回应', { exact: false }).waitFor({ state: 'visible', timeout: 8000 })
  const inspection = await inspectPage(page)
  const text = await page.locator('body').innerText()
  return {
    ...inspection,
    hasFallbackNotice: text.includes('本地安全降级回应') || text.includes('本地安全模式'),
    hasFallbackReply: text.includes('我听到了。我们可以慢慢聊'),
    hasInputUnlocked: await page.locator('textarea[placeholder="输入你的回应..."]').isEnabled(),
  }
}

async function exerciseTrainerAIReviewFailure(page) {
  await page.goto(`${baseURL}/trainer-ai`, { waitUntil: 'domcontentloaded' })
  await page.getByText('小回避', { exact: true }).click()
  await page.locator('textarea[placeholder="输入你的回应..."]').fill('我理解你今天比较累，不急着回复，我在。')
  await page.locator('button[title="发送回应"]').click()
  await page.getByText('重试复盘', { exact: true }).waitFor({ state: 'visible', timeout: 8000 })
  const inspection = await inspectPage(page)
  const text = await page.locator('body').innerText()
  return {
    ...inspection,
    hasReviewError: text.includes('会话复盘暂时不可用'),
    hasRetryReview: text.includes('重试复盘'),
    hasInputUnlocked: await page.locator('textarea[placeholder="输入你的回应..."]').isEnabled(),
  }
}

function expectedFailureRuntimeErrors(errors, marker) {
  return errors.every((error) => {
    if (error.includes('Failed to load resource: the server responded with a status of')) return true
    return error.includes(marker)
  })
}

async function run() {
  await mkdir(reportDir, { recursive: true })
  const server = spawn('npm', ['run', 'dev', '--', '--host', '127.0.0.1', '--port', String(port), '--strictPort'], {
    cwd: new URL('../', import.meta.url),
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, BROWSER: 'none' },
  })
  const serverOutput = []
  server.stdout.on('data', (chunk) => serverOutput.push(chunk.toString()))
  server.stderr.on('data', (chunk) => serverOutput.push(chunk.toString()))

  try {
    await waitForServer()
    const browser = await chromium.launch()
    const results = []
    const failures = []

    for (const viewport of viewports) {
      const context = await browser.newContext({ viewport })
      await context.addInitScript(() => {
        localStorage.setItem('hasCompletedOnboarding', 'true')
        sessionStorage.setItem('hasCompletedOnboarding', 'true')
      })
      const page = await context.newPage()
      const runtimeErrors = []
      page.on('pageerror', (error) => runtimeErrors.push(error.message))
      page.on('console', (message) => {
        if (message.type() === 'error') runtimeErrors.push(message.text())
      })
      let mockScenario = 'happy'
      await page.route('**/api/**', (route) => route.fulfill(mockFor(route.request().url(), route.request().method(), mockScenario)))

      for (const route of routes) {
        runtimeErrors.length = 0
        await page.goto(`${baseURL}${route.path}`, { waitUntil: 'domcontentloaded' })
        await page.locator('main h1').first().waitFor({ state: 'visible', timeout: 8000 })
        await page.waitForTimeout(350)
        const inspection = await inspectPage(page)
        const record = { route: route.name, path: route.path, viewport: viewport.name, ...inspection, runtimeErrors: [...runtimeErrors] }
        results.push(record)
        if (!inspection.hasHeading || inspection.horizontalOverflow || inspection.overlaps.length || runtimeErrors.length) {
          failures.push(record)
          await page.screenshot({ path: fileURLToPath(new URL(`${route.name}-${viewport.name}-failure.png`, reportDir)), fullPage: true })
        }
      }

      runtimeErrors.length = 0
      const trainerAIInteraction = await exerciseTrainerAI(page)
      const interactionRecord = { route: 'TrainerAIInteraction', path: '/trainer-ai', viewport: viewport.name, ...trainerAIInteraction, runtimeErrors: [...runtimeErrors] }
      results.push(interactionRecord)
      if (
        !trainerAIInteraction.hasHeading ||
        trainerAIInteraction.horizontalOverflow ||
        trainerAIInteraction.overlaps.length ||
        runtimeErrors.length ||
        !trainerAIInteraction.hasPartnerReply ||
        !trainerAIInteraction.hasSessionReview ||
        !trainerAIInteraction.hasInputUnlocked
      ) {
        failures.push(interactionRecord)
        await page.screenshot({ path: fileURLToPath(new URL(`TrainerAIInteraction-${viewport.name}-failure.png`, reportDir)), fullPage: true })
      }

      runtimeErrors.length = 0
      const trainerResourceContext = await exerciseTrainerResourceContext(page)
      const trainerResourceRecord = { route: 'TrainerResourceContext', path: '/trainer?resource_id=1', viewport: viewport.name, ...trainerResourceContext, runtimeErrors: [...runtimeErrors] }
      results.push(trainerResourceRecord)
      if (
        !trainerResourceContext.hasHeading ||
        trainerResourceContext.horizontalOverflow ||
        trainerResourceContext.overlaps.length ||
        runtimeErrors.length ||
        !trainerResourceContext.hasResourceContext ||
        !trainerResourceContext.hasPrefill ||
        trainerResourceContext.resourceHref !== '/resources/1' ||
        !trainerResourceContext.clearedResourceContext ||
        !trainerResourceContext.keptFilterQuery
      ) {
        failures.push(trainerResourceRecord)
        await page.screenshot({ path: fileURLToPath(new URL(`TrainerResourceContext-${viewport.name}-failure.png`, reportDir)), fullPage: true })
      }

      runtimeErrors.length = 0
      const mistakeResourceContext = await exerciseMistakeResourceContext(page)
      const mistakeResourceRecord = { route: 'MistakeResourceContext', path: '/mistakes?resource_id=1', viewport: viewport.name, ...mistakeResourceContext, runtimeErrors: [...runtimeErrors] }
      results.push(mistakeResourceRecord)
      if (
        !mistakeResourceContext.hasHeading ||
        mistakeResourceContext.horizontalOverflow ||
        mistakeResourceContext.overlaps.length ||
        runtimeErrors.length ||
        !mistakeResourceContext.hasResourceMistakeContext ||
        !mistakeResourceContext.hasGuidance ||
        mistakeResourceContext.resourceHref !== '/resources/1' ||
        mistakeResourceContext.trainerHref !== '/trainer?resource_id=1&q=%E5%A4%B1%E6%9C%9B%E5%90%8E%E7%9A%84%E9%87%8D%E6%96%B0%E7%BA%A6%E5%AE%9A%EF%BD%9C%E4%B8%89%E6%AD%A5%E8%AE%AD%E7%BB%83%EF%BD%9C%E5%AE%89%E5%85%A8%E5%9E%8BD3' ||
        !mistakeResourceContext.clearedResourceContext ||
        !mistakeResourceContext.keptSearchQuery
      ) {
        failures.push(mistakeResourceRecord)
        await page.screenshot({ path: fileURLToPath(new URL(`MistakeResourceContext-${viewport.name}-failure.png`, reportDir)), fullPage: true })
      }

      runtimeErrors.length = 0
      const settingsExport = await exerciseSettingsExport(page)
      const settingsExportRecord = { route: 'SettingsExport', path: '/settings', viewport: viewport.name, ...settingsExport, runtimeErrors: [...runtimeErrors] }
      results.push(settingsExportRecord)
      if (
        !settingsExport.hasHeading ||
        settingsExport.horizontalOverflow ||
        settingsExport.overlaps.length ||
        runtimeErrors.length ||
        !settingsExport.hasExportPanel ||
        !settingsExport.hasCoverage ||
        !settingsExport.hasMarkdownFormat ||
        !settingsExport.hasLocationHint ||
        !settingsExport.downloadHrefIsBlob ||
        !settingsExport.downloadName.includes('relationship-training-export') ||
        !settingsExport.downloadName.endsWith('.md')
      ) {
        failures.push(settingsExportRecord)
        await page.screenshot({ path: fileURLToPath(new URL(`SettingsExport-${viewport.name}-failure.png`, reportDir)), fullPage: true })
      }

      runtimeErrors.length = 0
      const settingsReminder = await exerciseSettingsReminder(page)
      const settingsReminderRecord = { route: 'SettingsReminder', path: '/settings', viewport: viewport.name, ...settingsReminder, runtimeErrors: [...runtimeErrors] }
      results.push(settingsReminderRecord)
      if (
        !settingsReminder.hasHeading ||
        settingsReminder.horizontalOverflow ||
        settingsReminder.overlaps.length ||
        runtimeErrors.length ||
        !settingsReminder.hasReminderSection ||
        !settingsReminder.hasLocalBoundary ||
        !settingsReminder.hasPermissionBoundary ||
        !settingsReminder.hasTestButton ||
        settingsReminder.reminderTime !== '20:00'
      ) {
        failures.push(settingsReminderRecord)
        await page.screenshot({ path: fileURLToPath(new URL(`SettingsReminder-${viewport.name}-failure.png`, reportDir)), fullPage: true })
      }

      runtimeErrors.length = 0
      const expressionSearch = await exerciseExpressionSearchSuggestions(page)
      const expressionSearchRecord = { route: 'ExpressionSearchSuggestions', path: '/expression', viewport: viewport.name, ...expressionSearch, runtimeErrors: [...runtimeErrors] }
      results.push(expressionSearchRecord)
      if (
        !expressionSearch.hasHeading ||
        expressionSearch.horizontalOverflow ||
        expressionSearch.overlaps.length ||
        runtimeErrors.length ||
        !expressionSearch.hasDatalistInput ||
        expressionSearch.optionCount < 4 ||
        !expressionSearch.hasToolSuggestion ||
        !expressionSearch.hasGuidance ||
        !expressionSearch.hasSuggestionGroups ||
        !expressionSearch.hasSearchWorkbench ||
        !expressionSearch.hasChainAboveList ||
        !expressionSearch.filteredToTool ||
        !expressionSearch.hasActiveSearchChip ||
        !expressionSearch.hasLearningDetails
      ) {
        failures.push(expressionSearchRecord)
        await page.screenshot({ path: fileURLToPath(new URL(`ExpressionSearchSuggestions-${viewport.name}-failure.png`, reportDir)), fullPage: true })
      }

      runtimeErrors.length = 0
      const pathLearning = await exercisePathLearningScaffold(page)
      const pathLearningRecord = { route: 'PathLearningScaffold', path: '/path', viewport: viewport.name, ...pathLearning, runtimeErrors: [...runtimeErrors] }
      results.push(pathLearningRecord)
      if (
        !pathLearning.hasHeading ||
        pathLearning.horizontalOverflow ||
        pathLearning.overlaps.length ||
        runtimeErrors.length ||
        !pathLearning.hasLearningOverview ||
        !pathLearning.hasStageScaffold ||
        !pathLearning.hasExamples ||
        !pathLearning.hasConcreteStage
      ) {
        failures.push(pathLearningRecord)
        await page.screenshot({ path: fileURLToPath(new URL(`PathLearningScaffold-${viewport.name}-failure.png`, reportDir)), fullPage: true })
      }

      runtimeErrors.length = 0
      const resourceLearning = await exerciseResourceLearningScaffold(page)
      const resourceLearningRecord = { route: 'ResourceLearningScaffold', path: '/resources', viewport: viewport.name, ...resourceLearning, runtimeErrors: [...runtimeErrors] }
      results.push(resourceLearningRecord)
      if (
        !resourceLearning.hasHeading ||
        resourceLearning.horizontalOverflow ||
        resourceLearning.overlaps.length ||
        runtimeErrors.length ||
        !resourceLearning.hasListScaffold ||
        !resourceLearning.hasListComparison ||
        !resourceLearning.hasSourceBoundary ||
        !resourceLearning.hasDetailScaffold ||
        !resourceLearning.hasDetailExamples ||
        !resourceLearning.hasCopyrightBoundary
      ) {
        failures.push(resourceLearningRecord)
        await page.screenshot({ path: fileURLToPath(new URL(`ResourceLearningScaffold-${viewport.name}-failure.png`, reportDir)), fullPage: true })
      }

      runtimeErrors.length = 0
      const profileEvidence = await exerciseProfileEvidence(page)
      const profileEvidenceRecord = { route: 'ProfileEvidence', path: '/profile', viewport: viewport.name, ...profileEvidence, runtimeErrors: [...runtimeErrors] }
      results.push(profileEvidenceRecord)
      if (
        !profileEvidence.hasHeading ||
        profileEvidence.horizontalOverflow ||
        profileEvidence.overlaps.length ||
        runtimeErrors.length ||
        !profileEvidence.hasProfileHeading ||
        !profileEvidence.hasRadar ||
        !profileEvidence.hasRealStats ||
        !profileEvidence.hasMockValues ||
        !profileEvidence.hasEvidence ||
        !profileEvidence.removedHardcodedStats ||
        !profileEvidence.removedStaticAwareness
      ) {
        failures.push(profileEvidenceRecord)
        await page.screenshot({ path: fileURLToPath(new URL(`ProfileEvidence-${viewport.name}-failure.png`, reportDir)), fullPage: true })
      }

      if (viewport.name === 'desktop') {
        for (const tocPath of ['/resources', '/surf', '/resources/1']) {
          runtimeErrors.length = 0
          const tocLayout = await exerciseTocCollapseLayout(page, tocPath)
          const tocRecord = { route: 'TocCollapseLayout', path: tocPath, viewport: viewport.name, ...tocLayout, runtimeErrors: [...runtimeErrors] }
          results.push(tocRecord)
          if (
            runtimeErrors.length ||
            !tocLayout.releasedSidebarColumn ||
            !tocLayout.fixedToRight ||
            !tocLayout.noOverflow ||
            !tocLayout.after.hasExpandButton
          ) {
            failures.push(tocRecord)
            await page.screenshot({ path: fileURLToPath(new URL(`TocCollapseLayout-${tocPath.replace(/[^a-z0-9]+/gi, '-')}-${viewport.name}-failure.png`, reportDir)), fullPage: true })
          }
        }
      }

      const failureExercises = [
        {
          name: 'TrainerCompareFailure',
          scenario: 'trainer_compare_failure',
          run: exerciseTrainerFailure,
          assert: (record) => record.hasSubmitError && record.preservedResponse,
          expectedErrorMarker: 'smoke compare failure',
        },
        {
          name: 'TrainerAIPartnerFailure',
          scenario: 'partner_simulate_failure',
          run: exerciseTrainerAIPartnerFailure,
          assert: (record) => record.hasFallbackNotice && record.hasFallbackReply && record.hasInputUnlocked,
          expectedErrorMarker: 'smoke partner failure',
        },
        {
          name: 'TrainerAIReviewFailure',
          scenario: 'partner_review_failure',
          run: exerciseTrainerAIReviewFailure,
          assert: (record) => record.hasReviewError && record.hasRetryReview && record.hasInputUnlocked,
          expectedErrorMarker: 'smoke review failure',
        },
      ]

      for (const exercise of failureExercises) {
        runtimeErrors.length = 0
        mockScenario = exercise.scenario
        const exercised = await exercise.run(page)
        const failureRecord = { route: exercise.name, path: exercise.name.includes('TrainerAI') ? '/trainer-ai' : '/trainer', viewport: viewport.name, ...exercised, runtimeErrors: [...runtimeErrors] }
        results.push(failureRecord)
        if (
          !exercised.hasHeading ||
          exercised.horizontalOverflow ||
          exercised.overlaps.length ||
          !expectedFailureRuntimeErrors(runtimeErrors, exercise.expectedErrorMarker) ||
          !exercise.assert(exercised)
        ) {
          failures.push(failureRecord)
          await page.screenshot({ path: fileURLToPath(new URL(`${exercise.name}-${viewport.name}-failure.png`, reportDir)), fullPage: true })
        }
      }
      mockScenario = 'happy'
      await context.close()
    }

    await browser.close()
    await writeFile(new URL('report.json', reportDir), `${JSON.stringify({ generated_at: new Date().toISOString(), results }, null, 2)}\n`)
    if (failures.length) {
      console.error(JSON.stringify({ status: 'failed', failures }, null, 2))
      process.exitCode = 1
      return
    }
    console.log(JSON.stringify({ status: 'passed', checked: results.length, report: fileURLToPath(new URL('report.json', reportDir)) }, null, 2))
  } finally {
    server.kill('SIGTERM')
    await new Promise((resolve) => setTimeout(resolve, 250))
    if (process.exitCode) {
      console.error(serverOutput.join('').slice(-4000))
    }
  }
}

run().catch((error) => {
  console.error(error)
  process.exit(1)
})
