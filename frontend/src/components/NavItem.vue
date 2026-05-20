<template>
  <li>
    <button
      @click="handleClick"
      class="w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all group"
      :class="[
        isActive
          ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30'
          : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
      ]"
    >
      <!-- 图标 -->
      <component
        :is="item.icon"
        class="w-5 h-5 flex-shrink-0 transition-colors"
        :class="[
          isActive
            ? 'text-white'
            : 'text-gray-400 dark:text-gray-500 group-hover:text-gray-600 dark:group-hover:text-gray-300'
        ]"
      />

      <!-- 名称 -->
      <span class="flex-1 text-left font-medium">{{ item.name }}</span>

      <!-- 徽章 -->
      <span
        v-if="item.badge"
        class="px-2 py-0.5 rounded-full text-xs font-medium"
        :class="[
          isActive
            ? 'bg-white/20 text-white'
            : 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
        ]"
      >
        {{ item.badge }}
      </span>
    </button>
  </li>
</template>

<script setup lang="ts">
import { type Component } from 'vue'

interface NavItemType {
  path: string
  name: string
  icon: Component
  badge?: string | null
}

interface Props {
  item: NavItemType
  isActive?: boolean
}

withDefaults(defineProps<Props>(), {
  isActive: false
})

const emit = defineEmits<{
  click: [path: string]
}>()

function handleClick() {
  emit('click', '')
}
</script>

<style scoped>
/* 可选的动画效果 */
button {
  @apply relative overflow-hidden;
}

button::before {
  content: '';
  @apply absolute inset-0 bg-white/0 transition-colors duration-200;
}

button:not(.bg-blue-500):hover::before {
  @apply bg-white/5;
}
</style>
