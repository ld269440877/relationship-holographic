/**
 * API 工具模块
 * 所有前端 API 调用集中管理
 */
import axios from 'axios'
import type { AxiosInstance, AxiosError } from 'axios'

// ─── axios 实例 ───────────────────────────────────────────
const api: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

// 响应拦截器：统一错误处理
api.interceptors.response.use(
  (response) => response.data,
  (error: AxiosError<{ detail?: string }>) => {
    const message = error.response?.data?.detail ?? error.message ?? '网络错误'
    console.error('[API Error]', message)
    return Promise.reject(new Error(message))
  }
)

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
  source?: string
  tags?: string
  created_at: string
}

export interface RadarData {
  levels: Array<{ name: string; score: number; description: string }>
  total_score: number
  level: string
}

export interface ComparisonResult {
  score: number
  differences: Array<{ type: string; name: string; desc: string }>
  suggestions: string[]
  ideal_response: string
  diff_report: string
}

export interface MistakeItem {
  id: number
  context: string
  their_words: string
  user_bad_response: string
  correct_response: string
  emotion_mistake?: string
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
}

// ─── Resources API ────────────────────────────────────────

export const resourcesApi = {
  list(params?: {
    type?: string
    category?: string
    applicable_scene?: string
    page?: number
    limit?: number
  }) {
    return api.get<{ items: ResourceItem[]; total: number }>('/resources', { params })
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
}

// ─── Training API ──────────────────────────────────────────

export const trainingApi = {
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

  /** 错题本列表 */
  getMistakes() {
    return api.get<MistakeItem[]>('/training/mistakes')
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
