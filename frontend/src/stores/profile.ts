/**
 * 用户画像全局状态
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { profileApi } from '@/utils/api'
import type { UserProfile } from '@/utils/api'

export const useProfileStore = defineStore('profile', () => {
  const profile = ref<UserProfile | null>(null)
  const loading = ref(false)

  async function fetchProfile() {
    loading.value = true
    try {
      profile.value = await profileApi.get()
    } catch (e) {
      console.error('fetchProfile failed', e)
    } finally {
      loading.value = false
    }
  }

  async function updateProfile(data: Partial<UserProfile>) {
    try {
      profile.value = await profileApi.update(data)
    } catch (e) {
      console.error('updateProfile failed', e)
    }
  }

  return { profile, loading, fetchProfile, updateProfile }
})
