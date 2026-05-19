/**
 * 训练相关全局状态
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { trainingApi, samplesApi } from '@/utils/api'
import type { RadarData, ComparisonResult, MistakeItem, InteractionSample } from '@/utils/api'

export const useTrainingStore = defineStore('training', () => {
  // ─── 状态 ───────────────────────────────────────
  const radar = ref<RadarData | null>(null)
  const mistakes = ref<MistakeItem[]>([])
  const currentSample = ref<InteractionSample | null>(null)
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
    fetchRadar, fetchMistakes, fetchRandomSample, submitComparison, clearComparison,
  }
})
