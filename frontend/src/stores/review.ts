/**
 * 复盘日记全局状态
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { reviewApi } from '@/utils/api'
import type { DailyReview } from '@/utils/api'

export const useReviewStore = defineStore('review', () => {
  const reviews = ref<DailyReview[]>([])
  const loading = ref(false)

  async function fetchReviews() {
    loading.value = true
    try {
      reviews.value = await reviewApi.list()
    } catch (e) {
      console.error('fetchReviews failed', e)
    } finally {
      loading.value = false
    }
  }

  async function createReview(data: DailyReview) {
    try {
      const created = await reviewApi.create(data)
      reviews.value.unshift(created)
      return created
    } catch (e) {
      console.error('createReview failed', e)
      return null
    }
  }

  async function deleteReview(id: number) {
    try {
      await reviewApi.delete(id)
      reviews.value = reviews.value.filter((r) => r.id !== id)
    } catch (e) {
      console.error('deleteReview failed', e)
    }
  }

  return { reviews, loading, fetchReviews, createReview, deleteReview }
})
