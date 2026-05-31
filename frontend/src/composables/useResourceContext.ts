import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { resourcesApi } from '@/utils/api'
import type { ResourceItem } from '@/utils/api'

interface ResourceContextOptions {
  clearPath: string
  onError?: (message: string) => void
}

function firstQueryValue(value: unknown) {
  if (Array.isArray(value)) return value[0]
  return value
}

export function useResourceContextFromRoute(options: ResourceContextOptions) {
  const route = useRoute()
  const router = useRouter()
  const resourceContext = ref<ResourceItem | null>(null)
  const resourceLoadError = ref('')

  async function loadResourceContextFromRoute() {
    const rawId = firstQueryValue(route.query.resource_id)
    const resourceId = typeof rawId === 'string' ? Number(rawId) : Number.NaN
    resourceLoadError.value = ''
    if (!Number.isFinite(resourceId) || resourceId <= 0) {
      resourceContext.value = null
      return null
    }
    try {
      resourceContext.value = await resourcesApi.get(resourceId)
      return resourceContext.value
    } catch (error) {
      resourceContext.value = null
      resourceLoadError.value = error instanceof Error ? error.message : '资源上下文加载失败'
      options.onError?.(resourceLoadError.value)
      return null
    }
  }

  async function clearResourceContext() {
    resourceContext.value = null
    resourceLoadError.value = ''
    const query = { ...route.query }
    delete query.resource_id
    await router.replace({ path: options.clearPath, query })
  }

  return {
    route,
    router,
    resourceContext,
    resourceLoadError,
    loadResourceContextFromRoute,
    clearResourceContext,
  }
}
