<template>
  <aside
    v-if="items.length > 0"
    class="hidden max-h-[calc(100vh-3rem)] self-start xl:block"
    :class="collapsed ? 'fixed right-4 top-36 z-40' : 'sticky top-6'"
  >
    <div
      class="max-h-[calc(100vh-3rem)] overflow-hidden rounded-lg border border-gray-100 bg-white shadow-sm transition-all dark:border-gray-700 dark:bg-gray-800"
      :class="collapsed ? 'w-12 shadow-lg' : 'w-full'"
    >
      <div class="flex items-center justify-between gap-2" :class="collapsed ? '' : 'mb-3'">
        <h2 v-if="!collapsed" class="px-4 pt-4 text-sm font-bold text-gray-800 dark:text-white">{{ title }}</h2>
        <span v-if="!collapsed" class="px-4 pt-4 text-xs text-gray-400">{{ items.length }} 条</span>
        <button
          class="m-2 rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white"
          type="button"
          :aria-label="collapsed ? '展开目录' : '折叠目录'"
          @click="toggleCollapsed"
        >
          {{ collapsed ? '☰' : '›' }}
        </button>
      </div>

      <nav v-if="!collapsed" class="max-h-[calc(100vh-8rem)] space-y-1 overflow-auto px-3 pb-4">
        <a
          v-for="item in items"
          :key="item.id"
          :href="`#${item.anchor}`"
          class="block rounded px-2 py-2 text-xs leading-5 text-gray-600 hover:bg-gray-100 hover:text-blue-600 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-blue-300"
        >
          <span v-if="item.indexLabel" class="text-gray-400">{{ item.indexLabel }}. </span>{{ item.title }}
        </a>
      </nav>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface TocItem {
  id: string
  anchor: string
  title: string
  indexLabel?: string
}

const props = defineProps<{
  title: string
  items: TocItem[]
  collapsed?: boolean
}>()

const emit = defineEmits<{
  'update:collapsed': [value: boolean]
}>()

const collapsed = ref(Boolean(props.collapsed))

watch(() => props.collapsed, (value) => {
  collapsed.value = Boolean(value)
})

function toggleCollapsed() {
  collapsed.value = !collapsed.value
  emit('update:collapsed', collapsed.value)
}
</script>
