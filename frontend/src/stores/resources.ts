/**
 * 资源库全局状态
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { resourcesApi } from '@/utils/api'
import type { ResourceItem } from '@/utils/api'

export const useResourcesStore = defineStore('resources', () => {
  const items = ref<ResourceItem[]>([])
  const total = ref(0)
  const loading = ref(false)
  const selectedType = ref('')
  const selectedScene = ref('')
  const currentPage = ref(1)
  const limit = ref(20)

  const filteredItems = computed(() => {
    return items.value.filter((r) => {
      if (selectedType.value && r.type !== selectedType.value) return false
      if (selectedScene.value && r.applicable_scene !== selectedScene.value) return false
      return true
    })
  })

  async function fetchResources() {
    loading.value = true
    try {
      const data = await resourcesApi.list({
        type: selectedType.value || undefined,
        applicable_scene: selectedScene.value || undefined,
        page: currentPage.value,
        limit: limit.value,
      })
      items.value = data.items
      total.value = data.total
    } catch (e) {
      console.error('fetchResources failed', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchRandom(type?: string) {
    return await resourcesApi.random({ type })
  }

  return {
    items, total, loading, selectedType, selectedScene, currentPage, limit,
    filteredItems, fetchResources, fetchRandom,
  }
})
