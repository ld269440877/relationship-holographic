/**
 * 训练相关全局状态
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { trainingApi, samplesApi } from '@/utils/api'
import type { RadarData, ComparisonResult, MistakeItem, InteractionSample, NextTrainingItem, DueReviewItem, TrainingTodaySummary, TrainingWeekSummary } from '@/utils/api'

export const useTrainingStore = defineStore('training', () => {
  // ─── 状态 ───────────────────────────────────────
  const radar = ref<RadarData | null>(null)
  const mistakes = ref<MistakeItem[]>([])
  const currentSample = ref<InteractionSample | null>(null)
  const nextItem = ref<NextTrainingItem | null>(null)
  const dueReviews = ref<DueReviewItem[]>([])
  const todaySummary = ref<TrainingTodaySummary | null>(null)
  const weekSummary = ref<TrainingWeekSummary | null>(null)
  const lastComparison = ref<ComparisonResult | null>(null)
  const loading = ref(false)

  // ─── 动作 ───────────────────────────────────────
  async function fetchRadar() {
    try {
      radar.value = await trainingApi.getRadar()
    } catch (e) {
      console.error('fetchRadar failed', e)
    }
  }

  async function fetchMistakes() {
    try {
      mistakes.value = await trainingApi.getMistakes()
    } catch (e) {
      console.error('fetchMistakes failed', e)
    }
  }

  async function fetchNextTraining() {
    loading.value = true
    try {
      nextItem.value = await trainingApi.getNext()
      currentSample.value = nextItem.value.sample
      return nextItem.value
    } catch (e) {
      console.error('fetchNextTraining failed', e)
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchDueReviews() {
    try {
      dueReviews.value = await trainingApi.getDueReviews()
      return dueReviews.value
    } catch (e) {
      console.error('fetchDueReviews failed', e)
      return []
    }
  }

  async function submitReview(mistakeId: number, correct: boolean) {
    try {
      const result = await trainingApi.submitReview(mistakeId, correct)
      await Promise.all([fetchMistakes(), fetchDueReviews(), fetchRadar(), fetchSummaries()])
      return result
    } catch (e) {
      console.error('submitReview failed', e)
      return null
    }
  }

  async function fetchSummaries() {
    try {
      const [today, week] = await Promise.all([
        trainingApi.getTodaySummary(),
        trainingApi.getWeekSummary(),
      ])
      todaySummary.value = today
      weekSummary.value = week
      return { today, week }
    } catch (e) {
      console.error('fetchSummaries failed', e)
      return null
    }
  }

  async function fetchRandomSample(params?: { scenario_category?: string; difficulty_level?: number }) {
    loading.value = true
    try {
      currentSample.value = await samplesApi.random(params)
    } catch (e) {
      console.error('fetchRandomSample failed', e)
    } finally {
      loading.value = false
    }
  }

  async function submitComparison(original: string, responseType = 'soft') {
    if (!currentSample.value) return
    try {
      lastComparison.value = await trainingApi.compare(
        original,
        currentSample.value.id,
        responseType
      )
      await Promise.all([fetchMistakes(), fetchDueReviews(), fetchRadar(), fetchSummaries()])
      return lastComparison.value
    } catch (e) {
      console.error('submitComparison failed', e)
      return null
    }
  }

  function clearComparison() {
    lastComparison.value = null
  }

  return {
    radar, mistakes, currentSample, lastComparison, loading,
    nextItem, dueReviews, todaySummary, weekSummary,
    fetchRadar, fetchMistakes, fetchNextTraining, fetchDueReviews, submitReview, fetchSummaries, fetchRandomSample, submitComparison, clearComparison,
  }
})
