/**
 * API 工具模块
 * 所有前端 API 调用集中管理
 */
import axios from 'axios'
import type { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios'
import { reportRuntimeEvent } from '@/utils/runtimeEvents'

// ─── axios 实例 ───────────────────────────────────────────
const http: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// 响应拦截器：统一错误处理
http.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const message = error.response?.data?.detail ?? error.message ?? '网络错误'
    console.error('[API Error]', message)
    reportRuntimeEvent({
      event_type: 'api_error',
      severity: error.response?.status && error.response.status >= 500 ? 'high' : 'medium',
      method: error.config?.method?.toUpperCase(),
      endpoint: error.config?.url,
      http_status: error.response?.status,
      message,
      context: {
        status_text: error.response?.statusText,
        online: typeof navigator !== 'undefined' ? navigator.onLine : undefined,
        retryable: !error.response || error.response.status >= 500,
      },
    })
    return Promise.reject(new Error(message))
  }
)

const api = {
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await http.get<T>(url, config)
    return response.data
  },
  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await http.post<T>(url, data, config)
    return response.data
  },
  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await http.put<T>(url, data, config)
    return response.data
  },
  async delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await http.delete<T>(url, config)
    return response.data
  },
}

// ─── 类型定义 ─────────────────────────────────────────────

export interface EmotionTag {
  spectrum: string
  word: string
  intensity: number
}

export interface InteractionSample {
  id: number
  sample_uuid: string
  scenario_category: string
  difficulty_level: number
  context: string
  their_words: string
  their_behavior?: string
  emotion_tags_json: string
  hidden_need?: string
  need_urgency?: number
  attachment_signal?: string
  boundary_test_level?: number
  bad_response: string
  bad_response_reason?: string
  good_response_soft: string
  good_response_tension?: string
  good_response_humor?: string
  principle_ref?: string
  source?: string
  created_at: string
}

export interface ResourceItem {
  id: number
  resource_uuid: string
  type: string
  category: string
  title?: string
  content: string
  emotional_tone_json?: string
  emotional_intensity?: number
  applicable_scene?: string
  difficulty_level?: number
  gender_target?: string
  attachment_suitability?: string
  usage_tip?: string
  effectiveness_rating?: number
  review_status?: string
  source?: string
  source_url?: string
  source_title?: string
  source_excerpt?: string
  source_summary?: string
  source_license?: string
  content_fingerprint?: string
  quality_score?: number
  tags?: string
  expression_tool_ids_json?: string
  expression_goal?: string
  expression_level?: string
  speech_act?: string
  mistake_pattern?: string
  recommended_drills_json?: string
  case_blueprint_json?: string
  variant_signature?: string
  content_unit?: string
  coverage_axis?: string
  variant_family?: string
  case_completeness_score?: number
  created_at: string
}

export interface ResourceSourceItem {
  source: string
  name?: string
  source_url: string
  count: number
  group?: string
  summary?: string
  structure?: string
  quality_notes?: string
  link_status?: 'verified_anchor' | 'registered_https' | 'registered_http' | 'unknown' | string
  health?: {
    source_url: string
    status: string
    http_code?: number | null
    redirect_url?: string | null
    redirected?: boolean
    last_checked_at?: string | null
    error_type?: string | null
  }
  themes?: string[]
  scenes?: string[]
}

export interface ResourceFilterOption {
  value: string
  label: string
  count: number
}

export interface ResourceExpressionToolOption {
  id: string
  name: string
  count: number
}

export interface ResourceFilterOptions {
  types: ResourceFilterOption[]
  categories: ResourceFilterOption[]
  scenes: ResourceFilterOption[]
  tags: ResourceFilterOption[]
  sources: ResourceFilterOption[]
  expression_goals: ResourceFilterOption[]
  expression_tools: ResourceExpressionToolOption[]
  keywords: ResourceFilterOption[]
  principle: string
}

export interface ResourceSimilarityQueue {
  summary: {
    scanned: number
    clusters: number
    queued_items: number
    threshold: number
    limit: number
    method: string
  }
  clusters: Array<{
    cluster_id: string
    kind: string
    family_key: string
    size: number
    highest_similarity: number
    average_similarity: number
    pair_count: number
    recommended_action: 'merge_or_hide_variants' | 'rewrite_family_with_distinct_cases' | 'keep_but_diversify_sorting' | string
    items: Array<{
      id: number
      resource_uuid: string
      title?: string | null
      type: string
      category: string
      applicable_scene?: string | null
      quality_score?: number | null
      review_status: string
      source?: string | null
      tags?: string | null
    }>
  }>
  principle: string
  next_actions: Array<{
    priority: 'high' | 'medium' | 'low'
    action: string
    reason: string
  }>
}

export interface ResourceSimilarityActionPayload {
  resource_ids: number[]
  action: 'quarantine_variants' | 'request_review' | 'restore_reviewed'
  reviewer_id: string
  reason: string
  dry_run: boolean
}

export interface ResourceSimilarityActionResult {
  dry_run: boolean
  action: string
  transitions: Array<{
    resource_id: number
    title?: string | null
    from_status: string
    to_status: string
    quality_score?: number | null
    family_key: string
  }>
  audit_logs?: Array<{
    id: number
    target_id: number
    action: string
    created_at: string
  }>
  governance_report: {
    resource_count: number
    reviewer_id: string
    reason_hash: string
    category_counts: Record<string, number>
    from_status_counts: Record<string, number>
    to_status_counts: Record<string, number>
    audit_log_ids: number[]
    next_action: string
    safety_flags: Record<string, boolean>
  }
  principle: string
}

export interface ResourceSimilarityRewritePayload {
  resource_ids: number[]
  reviewer_id: string
  reason: string
  dry_run: boolean
  mark_originals_quarantine: boolean
}

export interface ResourceSimilarityRewriteResult {
  dry_run: boolean
  created: number
  drafts?: Array<{
    resource_uuid: string
    type: string
    category: string
    title: string
    content: string
    applicable_scene: string
    quality_score: number
  }>
  items?: Array<{
    id: number
    resource_uuid: string
    title?: string | null
    category: string
    applicable_scene?: string | null
    review_status: string
    quality_score?: number | null
  }>
  audit_logs?: Array<{
    id: number
    target_id: number
    action: string
    created_at: string
  }>
  governance_report: {
    original_count: number
    replacement_count: number
    reviewer_id: string
    reason_hash: string
    mark_originals_quarantine: boolean
    scenes: string[]
    audit_log_ids: number[]
    safety_flags: Record<string, boolean>
    next_action: string
  }
  principle: string
}

export interface ExpressionTool {
  id: number
  tool_uuid: string
  name: string
  layer: string
  layer_label: string
  category: string
  formula?: string | null
  description: string
  best_scenes: string[]
  relationship_fit: string[]
  emotion_fit: string[]
  risk_flags: string[]
  micro_steps: Array<string | { name?: string; rule?: string; [key: string]: unknown }>
  mastery_stage: string
  review_status: string
  quality_score: number
  source: string
  source_url?: string | null
  example_before?: string | null
  example_after?: string | null
  learning_blueprint?: ExpressionToolLearningBlueprint | null
}

export interface ExpressionToolDialogueCase {
  scene: string
  story: string
  their_words: string
  poor_response?: string
  low_quality_response: string
  better_response: string
  why_it_works: string
  transfer_hint?: string
}

export interface ExpressionToolLearningBlueprint {
  version?: string
  concept?: string
  definition?: string
  core_principles?: string[]
  when_to_use?: string[]
  when_not_to_use?: string[]
  risk_boundaries?: string[]
  anti_patterns?: string[]
  practice_ladder?: string[]
  micro_steps?: Array<string | { name?: string; rule?: string; [key: string]: unknown }>
  dialogue_cases?: ExpressionToolDialogueCase[]
  transfer_practice?: string[]
  quality_notes?: Record<string, unknown>
}

export interface ExpressionToolChain {
  id: number
  chain_uuid: string
  name: string
  goal: string
  scene: string
  stage?: string | null
  tool_ids: string[]
  sequence: Array<{ order: number; tool: string }>
  forbidden_tools: string[]
  example_dialogue: Record<string, string>
  review_status: string
  quality_score: number
}

export interface ExpressionToolList {
  items: ExpressionTool[]
  total: number
  layers: Record<string, string>
  scenes: string[]
  goals: string[]
  layer_counts?: Record<string, number>
  scene_counts?: Record<string, number>
  goal_counts?: Record<string, number>
  principle: string
}

export interface ExpressionRecommendation {
  scene: string
  goal: string
  chains: ExpressionToolChain[]
  tools: ExpressionTool[]
  principle: string
}

export interface RadarData {
  levels: Array<{ name: string; score: number; description: string }>
  total_score: number
  level: string
  weakest_dimension?: string
  next_recommendation?: string
}

export interface ComparisonResult {
  score: number
  differences: Array<{ type: string; name: string; desc: string }>
  suggestions: string[]
  ideal_response: string
  diff_report: string
  dimension_scores?: Record<string, number>
  saved_attempt_id?: number
  mistake_id?: number
  next_recommendation?: string
  scoring_source?: 'hybrid' | 'rule_fallback' | 'rule'
  ai_feedback?: Record<string, unknown>
  safe_alternatives?: string[]
  metacognitive_review?: MetacognitiveReview
  expression_tool_scoring?: ExpressionToolScoring
  structured_diff?: StructuredDiff
}

export interface StructuredDiff {
  word_level?: Record<string, unknown>
  structure_level?: Record<string, unknown>
  emotion_path?: Record<string, unknown>
  developmental_emotion_transition?: DevelopmentalTransitionFeedback
  principle?: string
}

export interface DevelopmentalTransitionFeedback {
  axis: string
  emotion_dimensions: Record<string, unknown>
  transition_type: string
  transition_goal: string
  scaffold_level: Record<string, unknown>
  detected_moves: Record<string, boolean>
  missing_moves: string[]
  next_sentence: string
  principle: string
}

export interface ExpressionToolScoring {
  fit_score: number
  stage: string
  target_goal: string
  weak_dimensions: string[]
  detected_moves: Record<string, boolean>
  missing_moves: string[]
  recommended_tools: Array<{
    tool_uuid: string
    name: string
    layer: string
    category?: string
    formula?: string
    micro_steps?: string[]
    risk_flags?: string[]
    example_after?: string
  }>
  practice_steps: Array<{
    step: string
    action: string
  }>
  risk_notes: string[]
  principle: string
}

export interface MetacognitiveReview {
  principle: string
  fact_interpretation_split: {
    observable_facts: string[]
    interpretations_to_hold_lightly: string[]
  }
  three_hypotheses: Array<{
    name: string
    content: string
  }>
  verification_questions: string[]
  next_minimum_action: string
  reflection_questions: string[]
}

export interface PartnerSimulateResponse {
  session_id?: number | null
  reply: string
  score: number
  source: string
  suggestions: string[]
  safety: Record<string, unknown>
  safe_alternatives: string[]
  relationship_state: RelationshipState
  expression_chain: PartnerExpressionChain
  related_resources: PartnerRelatedResource[]
  mistake_memory: PartnerMistakeMemory
}

export interface PartnerExpressionChain {
  target_goal: string
  state_shift: {
    label: string
    trust: number
    stress: number
    boundary: number
    connection: number
    interpretation: string
  }
  tool_ids: string[]
  tool_names: string[]
  why: string[]
  next_move: string
  practice_prompt: string
  risk_boundary: string
  principle: string
  context_observation?: string
  micro_plan?: string[]
  example_next_reply?: string
  anti_pattern?: string
}

export interface PartnerRelatedResource {
  id?: number | null
  title: string
  type: string
  category: string
  scene?: string | null
  expression_goal?: string | null
  quality_score?: number | null
  source_title?: string | null
  source_url?: string | null
  usage_tip?: string | null
  reason: string
}

export interface PartnerMistakeMemory {
  cards: PartnerMistakeMemoryCard[]
  weak_dimensions: Array<{
    dimension: string
    label: string
    score: number
    recommendation: string
  }>
  next_focus: string
  principle: string
}

export interface PartnerMistakeMemoryCard {
  mistake_id?: number | null
  sample_id?: number | null
  scene?: string | null
  context?: string | null
  their_words: string
  user_bad_response: string
  correct_response: string
  review_focus?: string | null
  emotion_mistake?: string | null
  next_review?: string | null
  wrong_count?: number
  correct_count?: number
  match_terms?: string[]
  error_attribution?: Array<Record<string, unknown>>
  expression_rewrite?: {
    target_goal?: string
    primary_tool?: string
    rewrite_versions?: Array<{
      name: string
      text: string
      tool: string
    }>
    transfer_drill?: string
    forbidden_moves?: string[]
  }
}

export interface PartnerProviderStatus {
  configured: boolean
  provider: string
  mode: string
  model: string
  base_url: string
  chat_path: string
  live_probe_enabled: boolean
  compatibility_risks: string[]
  status_label: string
  principle: string
}

export interface RelationshipState {
  trust: number
  stress: number
  boundary: number
  boundary_safety: number
  connection: number
  turn_count: number
  attachment_style: string
  state_label: string
  state_color: 'green' | 'blue' | 'yellow' | 'orange' | 'red' | 'neutral' | string
  last_delta: Record<string, number>
  interpretation: string
  next_focus: string
}

export interface PartnerSessionReview {
  session: {
    id: number
    mode: string
    scenario_id: string
    scenario_name: string
    attachment_style: string
    difficulty: string
    response_style: string
    topics: string[]
    status: string
    total_turns: number
    average_score: number
    safety_summary: Record<string, unknown>
    started_at: string
    updated_at: string
    ended_at?: string | null
  }
  state_curve: Array<{
    turn: number
    score: number
    source: string
    state_label: string
    trust: number
    stress: number
    boundary: number
    boundary_safety: number
    connection: number
    created_at: string
  }>
  state_delta: {
    trust: number
    stress: number
    boundary: number
    boundary_safety: number
    connection: number
  }
  turning_points: Array<{
    turn: number
    title: string
    evidence: string
    user_message: string
    severity: string
  }>
  error_attribution: Array<{
    category: string
    dimension: string
    count: number
    reason: string
    repair: string
  }>
  next_practice: {
    focus: string
    minimum_action: string
    drills: string[]
    state_based_focus: string
  }
  principle: string
}

export interface AnalyticsAction {
  priority: string
  action: string
  reason: string
}

export interface AIQualityReport {
  summary: {
    runs: number
    success_rate: number
    fallback_rate: number
    safety_block_rate: number
    provider_failure_rate: number
    avg_latency_ms: number
  }
  outcome_breakdown: Array<{ name: string; count: number; rate: number }>
  task_type_breakdown: Array<{ name: string; count: number; rate: number }>
  provider_breakdown: Array<{ name: string; count: number; rate: number }>
  fallback_reasons: Array<{ name: string; count: number; rate: number }>
  safety_flags: Array<{ name: string; count: number; rate: number }>
  trend: Array<{
    date: string
    runs: number
    success: number
    fallback: number
    blocked: number
    success_rate: number
    fallback_rate: number
  }>
  recent_runs: Array<{
    id: number
    task_type: string
    provider: string
    model?: string | null
    outcome: string
    fallback_reason?: string | null
    safety_risk_level?: string | null
    latency_ms: number
    created_at: string
  }>
  next_actions: AnalyticsAction[]
  principle: string
}

export interface RelationshipTrends {
  summary: {
    sessions: number
    sessions_with_events: number
    turns: number
    average_score: number
    blocked_sessions: number
    repair_index: number
  }
  average_state_delta: {
    trust: number
    stress: number
    boundary: number
    boundary_safety: number
    connection: number
  }
  attachment_distribution: Array<{ name: string; count: number; rate: number }>
  session_trend: Array<{
    id: number
    scenario_name: string
    attachment_style: string
    difficulty: string
    status: string
    turns: number
    average_score: number
    safety_blocks: number
    state_label: string
    next_focus: string
    updated_at: string
    delta: Record<string, number>
  }>
  focus_distribution: Array<{ name: string; count: number; rate: number }>
  next_actions: AnalyticsAction[]
  principle: string
}

export interface AnalyticsCenterMetric {
  id: string
  label: string
  value: number
  target: number
  unit: string
  status: 'passed' | 'needs_attention' | string
  gap: number
}

export interface AnalyticsCenterAlert {
  priority: 'high' | 'medium' | 'low' | string
  metric: string
  title: string
  detail: string
}

export interface AnalyticsCenterTimelinePoint {
  id: string
  label: string
  value: number
  status: 'passed' | 'needs_attention' | string
}

export interface AnalyticsCenter {
  scorecard: AnalyticsCenterMetric[]
  alerts: AnalyticsCenterAlert[]
  timeline: AnalyticsCenterTimelinePoint[]
  sections: {
    ai_quality: {
      summary: AIQualityReport['summary']
      trend: AIQualityReport['trend']
      next_actions: AnalyticsAction[]
    }
    ai_failures: {
      summary: Record<string, unknown>
      clusters: Array<Record<string, unknown>>
    }
    provider: {
      provider: Record<string, unknown>
      recent: Record<string, unknown>
      risk_level: string
      diagnostics: Array<Record<string, unknown>>
      success_contract: {
        summary: {
          runs: number
          structured_success_rate: number
          raw_text_rate: number
          provider_failure_rate: number
          recoverable_success_rate: number
          post_fix_target: Record<string, number>
        }
        outcomes: Array<{ name: string; count: number; rate: number }>
        fallback_reasons: Array<{ name: string; count: number; rate: number }>
        task_matrix: Array<{
          task_type: string
          runs: number
          structured_success_rate: number
          raw_text_rate: number
          provider_failure_rate: number
          safety_block_rate: number
          top_response_keys: Array<{ name: string; count: number; rate: number }>
          top_fallback_reasons: Array<{ name: string; count: number; rate: number }>
        }>
        contract_gaps: Array<{
          id: string
          severity: string
          count: number
          fix: string
          evidence?: Array<{ name: string; count: number; rate: number }>
        }>
        quality_gate: Record<string, boolean>
        next_actions: AnalyticsAction[]
        principle: string
      }
      probe_readiness: {
        status: string
        live_probe_enabled: boolean
        configured: boolean
        blockers: Array<{ id: string; severity: string; detail: string }>
        runbook: Array<{ step: string; title: string; command: string; expected: string }>
        recent_probe_logs: Array<Record<string, unknown>>
        quality_gate: Record<string, boolean>
        principle: string
      }
      failure_playbook: {
        risk_level: string
        dominant_failure_reason: string
        http_statuses: Array<{ name: string; count: number; rate: number }>
        root_cause_matrix: Array<{
          id: string
          severity: string
          root_cause: string
          evidence: string[]
          operator_action: string
          regression_case: string
        }>
        regression_cases: Array<{ id: string; assertion: string }>
        runbook: Array<{ step: string; title: string; command: string }>
        quality_gate: Record<string, boolean>
        principle: string
      }
    }
    scheduler: {
      status: string
      checked_at?: string | null
      state_path?: string | null
      jobs: Array<{
        id: string
        name: string
        observed: boolean
        stale: boolean
        required: boolean
        latest_status: string
        latest_run_at?: string | null
        next_action: string
      }>
      alerts: Array<{ severity: string; job_id: string; reason: string; action: string }>
      recovery_runbook: Array<{ step: string; title: string; command: string; expected?: string }>
      quality_gate: Record<string, boolean>
      principle: string
    }
    gold_set: {
      summary: Record<string, unknown>
      quality_gates: Record<string, unknown>
      open_conflicts: number
      next_actions: AnalyticsAction[]
    }
    import_quality: {
      quality_score: number
      quality_debt: Record<string, unknown>
      totals: Record<string, unknown>
    }
    vector_recall: {
      summary: Record<string, unknown>
      recommendation: Record<string, unknown>
    }
    training_trends: {
      summary: RelationshipTrends['summary']
      average_state_delta: RelationshipTrends['average_state_delta']
      session_trend: RelationshipTrends['session_trend']
    }
  }
  principle: string
}

export interface AuditCenterEvent {
  id: string
  module: string
  source: string
  action: string
  status: string
  severity: string
  target: {
    type: string
    id?: number | string | null
  }
  summary: string
  created_at: string
  actor: string
  details: Record<string, unknown>
}

export interface AuditCenter {
  summary: {
    events: number
    needs_attention: number
    latest_at?: string | null
    module_filter: string
  }
  filters: {
    modules: Array<{ name: string; count: number; rate: number }>
    statuses: Array<{ name: string; count: number; rate: number }>
    severities: Array<{ name: string; count: number; rate: number }>
  }
  events: AuditCenterEvent[]
  next_actions: AnalyticsAction[]
  principle: string
}

export interface GoldSummary {
  summary: {
    gold_samples: number
    annotation_versions: number
    scaffold_versions: number
    expert_reviews: number
    approved: number
    needs_revision: number
    rejected: number
    pending_review: number
    expert_coverage_rate: number
    average_confidence: number
  }
  quality_gates: {
    ready_for_strict_calibration: boolean
    minimum_expert_reviews: number
    target_expert_coverage_rate: number
    target_average_confidence: number
  }
  next_actions: AnalyticsAction[]
  principle: string
}

export interface GoldReviewQueue {
  items: Array<{
    sample: {
      id: number
      sample_uuid: string
      scenario_category: string
      difficulty_level: number
      context: string
      their_words: string
      hidden_need?: string | null
      attachment_signal?: string | null
      boundary_test_level?: number | null
      good_response_soft: string
      review_status: string
      updated_at: string
    }
    gold_label: Record<string, unknown>
    visual_map: {
      emotion_thermometer: Record<string, unknown>
      need_radar: Array<Record<string, unknown>>
      boundary_band: Record<string, unknown>
      tension_dimensions: Array<Record<string, unknown>>
    }
    latest_review?: Record<string, unknown> | null
    review_priority: {
      score: number
      reasons: string[]
    }
  }>
  total: number
  principle: string
}

export interface MistakeItem {
  id: number
  context: string
  their_words: string
  user_bad_response: string
  correct_response: string
  emotion_mistake?: string
  error_attribution?: Array<{
    category: string
    dimension: string
    reason: string
    repair: string
  }>
  mastery_snapshot?: Record<string, unknown>
  emotion_flow?: string[]
  rewrite_drills?: string[]
  expression_rewrite?: {
    target_goal: string
    primary_tool: string
    recommended_tools: Array<{
      tool_uuid: string
      name: string
      layer: string
      category?: string
      formula?: string
      micro_steps?: string[]
      risk_flags?: string[]
      example_after?: string
    }>
    rewrite_versions: Array<{
      name: string
      text: string
      tool: string
    }>
    transfer_drill: string
    forbidden_moves: string[]
    principle: string
  }
  resource_queries?: string[]
  review_focus?: string | null
  next_review?: string
  correct_count?: number
  wrong_count?: number
}

export interface NextTrainingItem {
  type: 'review' | 'new'
  reason: string
  sample: InteractionSample
  mistake_id?: number
  weakest_dimension?: string
  visual_map?: TrainingVisualMap
}

export interface TrainingVisualMap {
  axiom: string
  signal_highlights: Array<{
    type: string
    label: string
    text: string
    weight: number
    hypothesis: string
  }>
  emotion_thermometer: {
    spectrum: string
    word: string
    intensity: number
    average_intensity: number
    percent: number
    zone: string
    principle: string
  }
  developmental_emotion_transition?: {
    axis: string
    label: string
    dimensions: Record<string, unknown>
    transition_type: string
    transition_goal: string
    scaffold_level: Record<string, unknown>
    primary_emotion: string
    mixed_emotion: boolean
    support_steps: string[]
    response_contract: string
  }
  emotion_flow_curve: Array<{
    step: string
    value: number
    label: string
  }>
  need_radar: Array<{
    name: string
    value: number
    evidence: string
  }>
  boundary_band: {
    level: number
    percent: number
    zone: 'green' | 'yellow' | 'orange' | 'red'
    label: string
    principle: string
    bands: Array<{
      from: number
      to: number
      zone: string
      label: string
    }>
  }
  interaction_loop_graph: {
    nodes: Array<{
      id: string
      label: string
      value: string
    }>
    edges: Array<{
      from: string
      to: string
      meaning: string
    }>
  }
  five_w_two_h: {
    why: string
    what: string
    who: string
    when: string
    where: string
    how: string
    how_much: {
      emotion_intensity: number
      need_urgency: number
      boundary_level: number
    }
  }
  verification_prompts: string[]
  anti_manipulation_note: string
}

export interface DueReviewItem {
  mistake_id: number
  sample: InteractionSample
  next_review?: string
}

export interface EvolutionItem {
  id: number
  source_id?: number
  title: string
  content: string
  summary?: string
  category: string
  tags: string[]
  quality_score: number
  status: string
  created_at: string
}

export interface EvolutionVisualMetrics {
  principle: string
  source_quality_matrix: Array<{
    id?: number
    name: string
    source_type: string
    trust_score: number
    raw_count: number
    annotation_count: number
    asset_count: number
    published_assets: number
    avg_privacy_risk: number
    avg_copyright_risk: number
    avg_confidence: number
    conversion_rate: number
    health_score: number
    quadrant: string
  }>
  review_publish_funnel: Array<{
    id: string
    label: string
    count: number
    percent_of_start: number
    conversion_from_previous: number
  }>
  safety_risk_trend: Array<{
    date: string
    total: number
    blocked: number
    risk_events: number
    sanitized: number
    risk_rate: number
  }>
  learning_increment: {
    new_annotations: number
    published_assets: number
    automation_events: number
    axis_coverage: Array<{ name: string; count: number }>
    primitive_layer_coverage: Array<{ name: string; count: number }>
    learning_velocity: number
  }
}

export interface EvolutionPipelineSummary {
  heartbeat: {
    state: 'empty' | 'stalled' | 'congested' | 'learning' | 'stable'
    label: string
    message: string
  }
  totals: {
    sources: number
    active_sources: number
    items: number
    candidates: number
    published: number
    rejected: number
  }
  status_counts: Record<string, number>
  category_counts: Record<string, number>
  source_type_counts: Record<string, number>
  sources: Array<{
    id: number
    name: string
    source_type: string
    trust_score: number
    active: boolean
    items_count: number
    update_frequency: string
  }>
  quality: {
    average_score: number
    publish_rate: number
    distribution: {
      excellent: number
      strong: number
      usable: number
      needs_review: number
    }
  }
  next_actions: Array<{
    priority: 'high' | 'medium' | 'low'
    action: string
    reason: string
  }>
  visual_metrics: EvolutionVisualMetrics
  last_item_at?: string | null
}

export interface EvolutionLatest {
  items: EvolutionItem[]
  latest_report?: {
    id: number
    period_type: string
    title: string
    summary: string
    new_items_count: number
    promoted_samples_count: number
    key_insights: string[]
    created_at: string
  } | null
  summary: EvolutionPipelineSummary
  principle: string
}

export interface EvolutionPipeline {
  principle: string
  stages: Array<{
    id: string
    name: string
    count: number
    risk_gate: string
  }>
  classification_axes: string[]
  status_counts: {
    raw: Record<string, number>
    annotation: Record<string, number>
    assets: Record<string, number>
  }
  sources: Array<Record<string, unknown>>
  raw_items: Array<Record<string, unknown>>
  annotation_jobs: Array<Record<string, unknown>>
  asset_versions: Array<Record<string, unknown>>
  recent_logs: Array<{
    id: number
    target_type: string
    target_id: number
    action: string
    from_status?: string | null
    to_status: string
    result: Record<string, unknown>
    message?: string | null
    created_at: string
  }>
  visual_metrics: EvolutionVisualMetrics
  next_actions: Array<{
    priority: 'high' | 'medium' | 'low'
    action: string
    reason: string
  }>
}

export interface EvolutionDedupeReport {
  principle: string
  method: {
    exact: string
    semantic: string
    vector_ready: string
  }
  summary: {
    scanned: number
    clusters: number
    exact_clusters: number
    semantic_clusters: number
    duplicate_review_needed: number
  }
  clusters: Array<{
    kind: string
    item_ids: number[]
    raw_uuids: string[]
    titles: Array<string | null>
    statuses: string[]
    recommendation: string
    similarity_scores?: number[]
  }>
}

export interface EvolutionImportQuality {
  principle: string
  totals: {
    samples: number
    resources: number
    knowledge_entries: number
    batches: number
    issues: number
    active_issues?: number
  }
  field_completeness: Record<string, {
    required: Record<string, number>
    enriched?: Record<string, number>
    json_invalid: number
  }>
  source_distribution: Record<string, Record<string, number>>
  issue_summary: {
    by_severity: Record<string, number>
    by_status?: Record<string, number>
    open?: number
    resolved?: number
    recent: Array<{
      id: number
      batch_id?: number | null
      source_name: string
      source_id?: string | null
      severity: string
      message: string
      status?: string
      reviewer_id?: string | null
      resolution?: string | null
      resolved_at?: string | null
      created_at: string
      updated_at?: string
    }>
  }
  latest_batches: Array<{
    id: number
    source_name: string
    source_type: string
    imported_sections: number
    imported_entries: number
    skipped_entries: number
    issues_count: number
    status: string
    report: Record<string, unknown>
    created_at: string
  }>
  quality_score: number
  quality_debt?: {
    auto_repairable_fields: number
    manual_review_issues: number
    resolved_issues: number
    issue_status: Record<string, number>
    status: string
    next_actions: string[]
  }
}

export interface EvolutionSafetyEvents {
  summary: {
    total: number
    blocked: number
    by_risk: Record<string, number>
    top_flags: string[]
  }
  events: Array<{
    id: number
    task_type: string
    source: string
    risk_level: string
    flags: string[]
    payload_hash: string
    payload_preview?: string | null
    message?: string | null
    alternatives: string[]
    blocked: boolean
    created_at: string
  }>
}

export interface EvolutionSchedulerResult {
  dry_run: boolean
  period_type: string
  lookback_days: number
  batch: Record<string, unknown>
  dedupe_report: EvolutionDedupeReport
  import_quality: EvolutionImportQuality
  safety_events: EvolutionSafetyEvents
  report?: EvolutionLatest['latest_report']
  next_actions: Array<{
    priority: 'high' | 'medium' | 'low'
    action: string
    reason: string
  }>
}

export interface ReviewedAssetCandidate {
  asset_type: 'resource' | 'knowledge_entry'
  id: number
  uuid: string
  title: string
  category: string
  review_status: string
  reviewed_at?: string | null
  published_at?: string | null
  quality_signal: Record<string, number | string | null>
  publish_ready: boolean
  priority: {
    score: number
    reasons: string[]
  }
}

export interface ReviewedAssetCandidates {
  items: ReviewedAssetCandidate[]
  total: number
  publish_ready: number
  quality_gates: {
    has_publish_candidates: boolean
    requires_manual_confirmation: boolean
    minimum_priority_for_auto_publish: number
  }
  next_actions: Array<{
    priority: 'high' | 'medium' | 'low'
    action: string
    reason: string
  }>
  principle: string
}

export interface ReviewedAssetActionPayload {
  asset_type: ReviewedAssetCandidate['asset_type']
  asset_id: number
  action: 'confirm_publish' | 'withdraw' | 'request_review'
  reviewer_id?: string
  reason?: string | null
  dry_run?: boolean
}

export interface ReviewedAssetActionResult {
  dry_run: boolean
  asset: ReviewedAssetCandidate
  from_status: string
  to_status: string
  would_log?: Record<string, unknown>
  audit_log?: {
    id: number
    action: string
    created_at: string
  }
  principle: string
}

export type ImportIssueStatus = 'active' | 'open' | 'review_requested' | 'resolved' | 'reopened' | 'all'

export interface ImportIssue {
  id: number
  batch_id?: number | null
  source_name: string
  source_id?: string | null
  severity: string
  message: string
  status: Exclude<ImportIssueStatus, 'active' | 'all'>
  reviewer_id?: string | null
  resolution_hash?: string | null
  resolved_at?: string | null
  created_at: string
  updated_at: string
}

export interface ImportIssueQueue {
  items: ImportIssue[]
  total: number
  status: ImportIssueStatus
  summary: {
    total: number
    active: number
    resolved: number
    by_status: Record<string, number>
    by_severity: Record<string, number>
    quality_gate: {
      requires_resolution_reason: boolean
      requires_reviewer: boolean
      auto_close_allowed: boolean
    }
  }
  source_groups: Array<{
    source_name: string
    total_issues: number
    active_issues: number
    resolved_issues: number
    by_status: Record<string, number>
    by_severity: Record<string, number>
    severity_weight: number
    oldest_active_at?: string | null
    latest_active_at?: string | null
    sample_issue_ids: number[]
    recommended_action: string
    review_packet: {
      source_name: string
      scope: {
        total_issues: number
        active_issues: number
        resolved_issues: number
        status_counts: Record<string, number>
        severity_counts: Record<string, number>
      }
      evidence_checklist: Array<{ id: string; label: string; required_for: string; evidence: string }>
      sample_evidence: Array<{
        issue_id: number
        source_id?: string | null
        severity: string
        status: string
        message_summary: string
        message_hash: string
        updated_at: string
      }>
      batch_action: {
        recommended_action: string
        candidate_issue_ids: number[]
        can_close_batch: boolean
        default_action: 'resolve' | 'request_review' | 'reopen' | string
        requires_resolution: boolean
        requires_reviewer: boolean
        auto_close_allowed: boolean
      }
      quality_gate: Record<string, boolean>
      principle: string
    }
  }>
  principle: string
}

export interface ImportIssueActionPayload {
  issue_ids: number[]
  action: 'resolve' | 'request_review' | 'reopen'
  reviewer_id?: string
  resolution?: string | null
  dry_run?: boolean
}

export interface ImportIssueActionResult {
  dry_run: boolean
  action: ImportIssueActionPayload['action']
  transitions: Array<{
    issue_id: number
    from_status: string
    to_status: string
    reviewer_id: string
    requires_resolution: boolean
  }>
  audit_logs?: Array<{
    id: number
    target_id: number
    action: string
    created_at: string
  }>
  governance_report: {
    action: ImportIssueActionPayload['action']
    issue_count: number
    reviewer_id: string
    resolution_hash?: string | null
    source_counts: Record<string, number>
    severity_counts: Record<string, number>
    from_status_counts: Record<string, number>
    to_status_counts: Record<string, number>
    audit_log_ids: number[]
    next_action: string
    safety: {
      raw_source_text_saved: boolean
      resolution_text_returned: boolean
      auto_close_allowed: boolean
    }
  }
  summary: ImportIssueQueue['summary']
  principle: string
}

export interface ImportIssueAuditHistory {
  items: Array<{
    id: number
    issue_id: number
    action: ImportIssueActionPayload['action']
    source_name?: string | null
    source_id?: string | null
    severity?: string | null
    from_status?: string | null
    to_status?: string | null
    reviewer_id?: string | null
    resolution_hash?: string | null
    safety: {
      raw_source_text_saved: boolean
      resolution_text_returned: boolean
      auto_close_allowed: boolean
    }
    created_at: string
  }>
  total: number
  summary: {
    actions: Record<string, number>
    to_status: Record<string, number>
    sources: Record<string, number>
    severity: Record<string, number>
    reviewers: Record<string, number>
    unsafe_log_count: number
  }
  quality_gate: {
    raw_source_text_saved: boolean
    resolution_text_returned: boolean
    requires_pipeline_log: boolean
    auto_close_allowed: boolean
  }
  principle: string
}

export interface LearningFramework {
  version: string
  axiom: string
  primitive_ladder: Array<{
    level: number
    name: string
    unit: string
    question: string
    visual: string
  }>
  classification_tree: Array<{
    id: string
    name: string
    axis: string[]
    children: string[]
  }>
  five_w_two_h: Array<{
    key: string
    label: string
    question: string
  }>
  visual_components: Array<{
    id: string
    name: string
    numeric: string[]
    visual: string
    training_use: string
  }>
  mastery_stages: Array<{
    level: number
    name: string
    definition: string
    test: string
  }>
  three_natures_management: Array<{
    nature: string
    management: string
    relationship_use: string
  }>
  question_templates: Array<{
    scene: string
    template: string
  }>
  material_library: Array<{
    id: string
    name: string
    purpose: string
    beginner_definition: string
    expert_definition: string
    signals: string[]
    emotion_words: string[]
    degree_scale: Array<{ level: number; label: string; cue: string }>
    technique_cards?: Array<{
      id: string
      name: string
      goal: string
      terms: string[]
      keywords: string[]
      steps: string[]
      degree_scale: Array<{ level: number; label: string; cue: string }>
      sentence_patterns: string[]
      bad_patterns: string[]
      comparisons?: Array<{
        axis: string
        open_question: string
        closed_question: string
        use_rule: string
      }>
      feeling_spectrum?: Array<{
        family: string
        words: string[]
        body_cues: string[]
        need_signal: string
      }>
    }>
    scene_example: {
      context: string
      poor_response: string
      better_response: string
      why: string
    }
    dialogue_template: Array<{ speaker: string; line: string }>
    practice_drills: string[]
    anti_patterns: string[]
    quality_contract: string
  }>
  module_templates: Array<{
    module: string
    tabs: string[]
    required_fields: string[]
    design_rule: string
  }>
  learning_map: Array<{
    step: string
    name: string
    action: string
  }>
  quality_gates: Array<{
    gate: string
    rule: string
  }>
}

export interface CurriculumGraph {
  version: string
  axiom: string
  current_node_id: string
  current_stage: CurriculumNode
  overall_progress: number
  nodes: CurriculumNode[]
  edges: Array<{
    from: string
    to: string
    label: string
    gate: string
    unlocked: boolean
  }>
  practice_plan: {
    focus_node_id: string
    focus: string
    minimum_action: string
    drills: string[]
    reflection: string
  }
  evidence_summary: {
    training_attempts: number
    open_mistakes: number
    partner_sessions: number
    partner_events: number
    safety_blocks: number
    principle: string
  }
  visual_layers: Array<{
    id: string
    name: string
    use: string
  }>
}

export interface CurriculumNode {
  id: string
  index: number
  name: string
  primitive: string
  description: string
  tools: string[]
  tasks: string[]
  promotion_rule: string
  progress: number
  status: 'completed' | 'current' | 'locked' | string
  is_completed: boolean
  is_current: boolean
  difficulty: 'foundation' | 'integration' | 'advanced' | string
  score_formula: string
  evidence: {
    attempts_count: number
    average_training_score: number
    open_mistakes: number
    partner_sessions: number
    partner_turns: number
    safety_blocks: number
    evidence_label: string
  }
  next_action: string
}

export interface KnowledgeSection {
  id: number
  section_uuid: string
  name: string
  description?: string
  icon?: string
  sort_order: number
  source: string
  source_id?: string
}

export interface KnowledgeEntry {
  id: number
  entry_uuid: string
  section_id: number
  title: string
  subtitle?: string
  summary?: string
  content?: string
  category: string
  tags: string[]
  quality_score: number
  source: string
  source_id?: string
  created_at: string
  learning?: {
    concept: string
    principle: string
    method: string[]
    scene: string
    drill: string
  }
}

export interface KnowledgeImportLatest {
  latest?: {
    id: number
    source_name: string
    source_type: string
    imported_sections: number
    imported_entries: number
    skipped_entries: number
    issues_count: number
    status: string
    report: Record<string, unknown>
    created_at: string
  } | null
  principle: string
}

export interface KnowledgeFilterOption {
  value: string
  label: string
  count: number
  id?: number
}

export interface KnowledgeFilterOptions {
  sections: KnowledgeFilterOption[]
  categories: KnowledgeFilterOption[]
  tags: KnowledgeFilterOption[]
  sources: KnowledgeFilterOption[]
  keywords: KnowledgeFilterOption[]
  principle: string
}

export interface KnowledgeVisualMap {
  principle: string
  concept_graph: {
    nodes: Array<{
      id: string
      label: string
      type: 'root' | 'section' | 'category' | 'tag' | string
      weight: number
      x?: number
      y?: number
    }>
    edges: Array<{
      from: string
      to: string
      label: string
    }>
  }
  classification_tree: Array<{
    id: string
    name: string
    kind: string
    count: number
    quality: number
    children: Array<{
      id: string
      name: string
      kind: string
      count: number
    }>
  }>
  five_w_two_h_cards: Array<{
    key: string
    label: string
    question: string
    answer: string
  }>
  tool_fit_map: Array<{
    tool: string
    use: string
    matched_entries: number
    signal: number
    fit_score: number
    examples: string[]
  }>
  coverage: {
    sections: number
    entries: number
    categories: number
    tags: number
    average_quality: number
  }
}

export interface TrainingTodaySummary {
  date: string
  attempts_count: number
  average_score: number
  mistakes_open: number
  completed: boolean
  recommendation: string
}

export interface TrainingWeekSummary {
  start_date: string
  end_date: string
  attempts_count: number
  active_days: number
  average_score: number
  streak_hint: string
}

export interface DailyReview {
  id?: number
  review_date: string
  five_whys_json?: string
  emotion_accuracy?: number
  highlight: string
  improvement: string
  resource_used_id?: number
  emotions?: string[]
}

export interface UserProfile {
  id: number
  email?: string
  attachment_style?: string
  core_wound?: string
  love_language?: string
  perception_baseline?: number
  emotion_vocab_size?: number
  progress_json?: string
}

// ─── Emotions API ──────────────────────────────────────────

export const emotionsApi = {
  /** 获取所有情绪谱系，可选按 spectrum / intensity 过滤 */
  getSpectrum(params?: { spectrum?: string; intensity?: number }) {
    return api.get<EmotionTag[]>('/emotions/spectrum', { params })
  },

  /** 获取单条谱系 */
  getSpectrumByName(spectrum: string) {
    return api.get<EmotionTag[]>(`/emotions/spectrum/${spectrum}`)
  },

  /** 获取所有混合情绪 */
  getMixed() {
    return api.get<Array<{
      id: number; name: string
      component1: { spectrum: string; word: string; intensity: number }
      component2: { spectrum: string; word: string; intensity: number }
      typical_scenario: string; response_principle: string
    }>>('/emotions/mixed')
  },

  /** 获取七条谱系名列表 */
  getSpectraList() {
    return api.get<string[]>('/emotions/spectra-list')
  },
}

// ─── Samples API ──────────────────────────────────────────

export const samplesApi = {
  /** 分页查询样本 */
  list(params?: {
    scenario_category?: string
    difficulty_level?: number
    attachment_signal?: string
    page?: number
    limit?: number
  }) {
    return api.get<{ items: InteractionSample[]; total: number }>('/samples', { params })
  },

  /** 获取单条 */
  get(id: number) {
    return api.get<InteractionSample>(`/samples/${id}`)
  },

  /** 随机抽取一条用于训练 */
  random(params?: { scenario_category?: string; difficulty_level?: number }) {
    return api.get<InteractionSample>('/samples/random', { params })
  },

  getCategories() {
    return api.get<string[]>('/samples/categories')
  },

  getAttachments() {
    return api.get<string[]>('/samples/attachments')
  },

  goldSummary() {
    return api.get<GoldSummary>('/samples/gold/summary')
  },

  goldReviewQueue(limit = 5) {
    return api.get<GoldReviewQueue>('/samples/gold/review-queue', { params: { limit } })
  },
}

// ─── Resources API ────────────────────────────────────────

export const resourcesApi = {
  list(params?: {
    type?: string
    category?: string
    applicable_scene?: string
    mission_axis?: string
    q?: string
    tag?: string
    source?: string
    expression_tool?: string
    expression_goal?: string
    page?: number
    limit?: number
  }) {
    return api.get<{ items: ResourceItem[]; total: number; page: number; limit: number; offset: number }>('/resources', { params })
  },

  get(id: number) {
    return api.get<ResourceItem>(`/resources/${id}`)
  },

  random(params?: { type?: string }) {
    return api.get<ResourceItem>('/resources/random', { params })
  },

  getTypes() {
    return api.get<string[]>('/resources/types')
  },

  sources(limit = 48) {
    return api.get<{ items: ResourceSourceItem[]; total: number }>('/resources/sources', { params: { limit } })
  },

  sourceHealthCheck(payload: { source_urls?: string[]; limit?: number; timeout_seconds?: number; dry_run?: boolean }) {
    return api.post<{ items: Array<NonNullable<ResourceSourceItem['health']>>; summary: Record<string, number>; dry_run: boolean; audit_log_id?: number }>(
      '/resources/sources/health-check',
      payload,
    )
  },

  filters(limit = 120) {
    return api.get<ResourceFilterOptions>('/resources/filters', { params: { limit } })
  },

  similarity(params: { limit?: number; threshold?: number; max_clusters?: number } = {}) {
    return api.get<ResourceSimilarityQueue>('/resources/similarity', { params })
  },

  similarityAction(payload: ResourceSimilarityActionPayload) {
    return api.post<ResourceSimilarityActionResult>('/resources/similarity/action', payload)
  },

  similarityRewriteBatch(payload: ResourceSimilarityRewritePayload) {
    return api.post<ResourceSimilarityRewriteResult>('/resources/similarity/rewrite-batch', payload)
  },
}

// ─── Expression API ────────────────────────────────────────

export const expressionApi = {
  listTools(params?: { layer?: string; category?: string; scene?: string; goal?: string; q?: string; limit?: number }) {
    return api.get<ExpressionToolList>('/expression/tools', { params })
  },

  getTool(id: number | string) {
    return api.get<ExpressionTool>(`/expression/tools/${id}`)
  },

  chains(params?: { scene?: string; goal?: string; q?: string; limit?: number }) {
    return api.get<{ items: ExpressionToolChain[]; total: number }>('/expression/chains', { params })
  },

  recommend(payload: { scene?: string; goal?: string; emotion?: string; limit?: number }) {
    return api.post<ExpressionRecommendation>('/expression/recommend', payload)
  },
}

// ─── Training API ──────────────────────────────────────────

export const trainingApi = {
  /** 下一题推荐 */
  getNext() {
    return api.get<NextTrainingItem>('/training/next')
  },

  /** 情绪识别 */
  recognize(text: string) {
    return api.post<{
      emotions: EmotionTag[]
      mixed_emotion?: Record<string, unknown>
      intensity_label: string
      behavioral_anchor: string
    }>('/training/recognize', { text })
  },

  /** 对比用户回应 vs 理想回应 */
  compare(original_response: string, sample_id: number, response_type = 'soft') {
    return api.post<ComparisonResult>('/training/compare', {
      original_response,
      sample_id,
      response_type,
    })
  },

  /** 八阶雷达图数据 */
  getRadar() {
    return api.get<RadarData>('/training/radar')
  },

  getVisualMap(sampleId: number) {
    return api.get<TrainingVisualMap>(`/training/visual-map/${sampleId}`)
  },

  simulatePartner(data: {
    session_id?: number | null
    scenario_id: string
    scenario_name: string
    attachment_style: string
    user_message: string
    history: Array<{ role: string; content: string }>
    difficulty: string
    response_style: string
    topics: string[]
    relationship_state?: RelationshipState | null
  }) {
    return api.post<PartnerSimulateResponse>('/training/partner/simulate', data)
  },

  partnerSessionReview(sessionId: number) {
    return api.get<PartnerSessionReview>(`/training/partner/sessions/${sessionId}/review`)
  },

  partnerProviderStatus() {
    return api.get<PartnerProviderStatus>('/training/partner/provider-status')
  },

  /** 错题本列表 */
  getMistakes() {
    return api.get<MistakeItem[]>('/training/mistakes')
  },

  /** 到期错题 */
  getDueReviews() {
    return api.get<DueReviewItem[]>('/training/reviews/due')
  },

  /** 提交复习结果 */
  submitReview(mistakeId: number, correct: boolean) {
    return api.post<{ ok: boolean; next_review: string; reviewed: boolean }>(`/training/reviews/${mistakeId}`, { correct })
  },

  getTodaySummary() {
    return api.get<TrainingTodaySummary>('/training/summary/today')
  },

  getWeekSummary() {
    return api.get<TrainingWeekSummary>('/training/summary/week')
  },
}

// ─── Analytics API ──────────────────────────────────────────

export const analyticsApi = {
  aiQuality(limit = 200) {
    return api.get<AIQualityReport>('/analytics/ai-quality', { params: { limit } })
  },
  relationshipTrends(limit = 50) {
    return api.get<RelationshipTrends>('/analytics/relationship-trends', { params: { limit } })
  },
  center(limit = 120) {
    return api.get<AnalyticsCenter>('/analytics/center', { params: { limit } })
  },
  auditCenter(limit = 80, module = 'all') {
    return api.get<AuditCenter>('/analytics/audit-center', { params: { limit, module } })
  },
}

// ─── Evolution API ──────────────────────────────────────────

export const evolutionApi = {
  latest() {
    return api.get<EvolutionLatest>('/evolution/latest')
  },
  summary() {
    return api.get<EvolutionPipelineSummary>('/evolution/summary')
  },
  pipeline() {
    return api.get<EvolutionPipeline>('/evolution/pipeline')
  },
  runWeeklyScheduler(payload: { dry_run?: boolean; batch_limit?: number; duplicate_policy?: string; period_type?: string } = {}) {
    return api.post<EvolutionSchedulerResult>('/evolution/scheduler/run-weekly', payload)
  },
  dedupeReport(limit = 120) {
    return api.get<EvolutionDedupeReport>('/evolution/dedupe/report', { params: { limit } })
  },
  importQuality() {
    return api.get<EvolutionImportQuality>('/evolution/import-quality')
  },
  importIssues(status: ImportIssueStatus = 'active', limit = 100) {
    return api.get<ImportIssueQueue>('/evolution/import-quality/issues', { params: { status, limit } })
  },
  importIssueAction(payload: ImportIssueActionPayload) {
    return api.post<ImportIssueActionResult>('/evolution/import-quality/issues/action', payload)
  },
  importIssueAudit(limit = 50) {
    return api.get<ImportIssueAuditHistory>('/evolution/import-quality/issues/audit', { params: { limit } })
  },
  safetyEvents(limit = 50) {
    return api.get<EvolutionSafetyEvents>('/evolution/safety-events', { params: { limit } })
  },
  publishCandidates(limit = 30) {
    return api.get<ReviewedAssetCandidates>('/evolution/reviewed-assets/publish-candidates', { params: { limit } })
  },
  reviewedAssetAction(payload: ReviewedAssetActionPayload) {
    return api.post<ReviewedAssetActionResult>('/evolution/reviewed-assets/action', payload)
  },
  list(params?: { category?: string; status?: string; limit?: number }) {
    return api.get<EvolutionItem[]>('/evolution/items', { params })
  },
}

// ─── Learning Framework API ──────────────────────────────────────────

export const learningApi = {
  framework() {
    return api.get<LearningFramework>('/learning/framework')
  },
  curriculumGraph() {
    return api.get<CurriculumGraph>('/learning/curriculum-graph')
  },
}

// ─── Knowledge API ──────────────────────────────────────────

export const knowledgeApi = {
  sections() {
    return api.get<KnowledgeSection[]>('/knowledge/sections')
  },
  entries(params?: { section_id?: number; category?: string; tag?: string; source?: string; q?: string; limit?: number }) {
    return api.get<KnowledgeEntry[]>('/knowledge/entries', { params })
  },
  entry(id: number) {
    return api.get<KnowledgeEntry>(`/knowledge/entries/${id}`)
  },
  filters(limit = 120) {
    return api.get<KnowledgeFilterOptions>('/knowledge/filters', { params: { limit } })
  },
  latestImport() {
    return api.get<KnowledgeImportLatest>('/knowledge/imports/latest')
  },
  visualMap() {
    return api.get<KnowledgeVisualMap>('/knowledge/visual-map')
  },
}

// ─── Review API ────────────────────────────────────────────

export const reviewApi = {
  list() {
    return api.get<DailyReview[]>('/reviews')
  },
  create(data: DailyReview) {
    return api.post<DailyReview>('/reviews', data)
  },
  update(id: number, data: Partial<DailyReview>) {
    return api.put<DailyReview>(`/reviews/${id}`, data)
  },
  delete(id: number) {
    return api.delete(`/reviews/${id}`)
  },
}

// ─── Profile API ───────────────────────────────────────────

export const profileApi = {
  get() {
    return api.get<UserProfile>('/profile')
  },
  update(data: Partial<UserProfile>) {
    return api.put<UserProfile>('/profile', data)
  },
}

export default api
