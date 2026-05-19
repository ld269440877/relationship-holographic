<template>
  <div class="p-8">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-800 dark:text-white">资源海洋</h1>
      <p class="text-gray-500 dark:text-gray-400 mt-2">段子、话术、故事、游戏，应有尽有</p>
    </div>

    <!-- 筛选器 -->
    <div class="flex flex-wrap gap-4 mb-6">
      <select v-model="store.selectedType" @change="store.fetchResources()" class="input-mac w-40">
        <option value="">全部类型</option>
        <option value="joke">段子</option>
        <option value="flirty">话术</option>
        <option value="story">故事</option>
        <option value="riddle">急转弯</option>
        <option value="game">游戏</option>
      </select>
      <select v-model="store.selectedScene" @change="store.fetchResources()" class="input-mac w-40">
        <option value="">全部场景</option>
        <option value="初识">初识</option>
        <option value="暧昧">暧昧</option>
        <option value="热恋">热恋</option>
        <option value="冲突">冲突</option>
        <option value="平淡">平淡</option>
        <option value="修复">修复</option>
      </select>
      <button @click="randomOne" class="btn-primary">
        🎲 随机一条
      </button>
      <button @click="store.fetchResources()" class="btn-secondary">
        🔄 刷新
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="store.loading" class="text-center py-12 text-gray-400">
      <div class="animate-spin text-4xl mb-4">📚</div>
      <p>加载中...</p>
    </div>

    <!-- 资源列表 -->
    <div v-else-if="store.filteredItems.length > 0" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="(resource, index) in store.filteredItems"
        :key="index"
        class="card card-hover"
      >
        <div class="flex items-center gap-2 mb-4">
          <span class="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
            {{ typeLabel(resource.type) }}
          </span>
          <span class="text-sm text-gray-500 dark:text-gray-400">
            {{ resource.category }}
          </span>
        </div>
        <h3 class="text-lg font-bold text-gray-800 dark:text-white mb-2">
          {{ resource.title || '无标题' }}
        </h3>
        <p class="text-gray-600 dark:text-gray-300 mb-4 line-clamp-3">{{ resource.content }}</p>
        <div v-if="resource.usage_tip" class="mb-3 p-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/20 text-sm text-yellow-700 dark:text-yellow-300">
          💡 {{ resource.usage_tip }}
        </div>
        <div class="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
          <span v-if="resource.effectiveness_rating">
            效果: {{ resource.effectiveness_rating }}/10
          </span>
          <span>{{ resource.applicable_scene || '' }}</span>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="card text-center py-12 text-gray-400">
      <p class="text-4xl mb-4">📭</p>
      <p>暂无匹配的资源，试试调整筛选条件</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useResourcesStore } from '@/stores/resources'
import { useToast } from '@/utils/toast'

const store = useResourcesStore()
const toast = useToast()

const typeMap: Record<string, string> = {
  joke: '段子',
  flirty: '话术',
  story: '故事',
  riddle: '急转弯',
  game: '游戏',
  media: '媒体',
}

function typeLabel(type: string) {
  return typeMap[type] ?? type
}

async function randomOne() {
  try {
    const resource = await store.fetchRandom(store.selectedType || undefined)
    if (resource) {
      toast.success(`${typeLabel(resource.type)}: ${resource.title || ''}\n\n${resource.content}`)
    }
  } catch {
    toast.error('获取随机资源失败')
  }
}

onMounted(() => {
  store.fetchResources()
})
</script>
