/**
 * 资源库全局状态
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { resourcesApi } from '@/utils/api'
import type { ResourceFilterOptions, ResourceItem, ResourceSourceItem } from '@/utils/api'

export const useResourcesStore = defineStore('resources', () => {
  const items = ref<ResourceItem[]>([])
  const total = ref(0)
  const loading = ref(false)
  const sources = ref<ResourceSourceItem[]>([])
  const filterOptions = ref<ResourceFilterOptions | null>(null)
  const sourcesLoading = ref(false)
  const filtersLoading = ref(false)
  const selectedType = ref('')
  const selectedCategory = ref('')
  const selectedScene = ref('')
  const selectedMissionAxis = ref('')
  const searchQuery = ref('')
  const selectedTag = ref('')
  const selectedSource = ref('')
  const selectedExpressionTool = ref('')
  const selectedExpressionGoal = ref('')
  const currentPage = ref(1)
  const limit = ref(48)

  const filteredItems = computed(() => items.value)
  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / limit.value)))
  const pageStart = computed(() => (total.value === 0 ? 0 : (currentPage.value - 1) * limit.value + 1))
  const pageEnd = computed(() => Math.min(total.value, currentPage.value * limit.value))

  async function fetchResources() {
    loading.value = true
    try {
      const data = await resourcesApi.list({
        type: selectedType.value || undefined,
        category: selectedCategory.value || undefined,
        applicable_scene: selectedScene.value || undefined,
        mission_axis: selectedMissionAxis.value || undefined,
        q: searchQuery.value || undefined,
        tag: selectedTag.value || undefined,
        source: selectedSource.value || undefined,
        expression_tool: selectedExpressionTool.value || undefined,
        expression_goal: selectedExpressionGoal.value || undefined,
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

  async function fetchSources() {
    sourcesLoading.value = true
    try {
      const data = await resourcesApi.sources(48)
      sources.value = data.items
    } catch (e) {
      console.error('fetchSources failed', e)
    } finally {
      sourcesLoading.value = false
    }
  }

  async function fetchFilterOptions() {
    filtersLoading.value = true
    try {
      filterOptions.value = await resourcesApi.filters(160)
    } catch (e) {
      console.error('fetchFilterOptions failed', e)
    } finally {
      filtersLoading.value = false
    }
  }

  async function resetAndFetch() {
    currentPage.value = 1
    await fetchResources()
  }

  async function goToPage(page: number) {
    const nextPage = Math.min(Math.max(1, page), totalPages.value)
    if (nextPage === currentPage.value && items.value.length > 0) return
    currentPage.value = nextPage
    await fetchResources()
  }

  async function fetchRandom(type?: string) {
    return await resourcesApi.random({ type })
  }

  return {
    items, total, loading, sources, sourcesLoading, selectedType, selectedCategory, selectedScene, selectedMissionAxis,
    filterOptions, filtersLoading, searchQuery, selectedTag, selectedSource, selectedExpressionTool, selectedExpressionGoal, currentPage, limit,
    filteredItems, totalPages, pageStart, pageEnd, fetchResources, fetchSources, fetchFilterOptions, resetAndFetch, goToPage, fetchRandom,
  }
})
