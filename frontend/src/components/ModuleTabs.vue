<template>
  <section class="rounded-lg bg-white p-3 shadow-sm dark:bg-gray-800" :aria-label="label">
    <div class="flex gap-2 overflow-x-auto" role="tablist" :aria-label="label">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        role="tab"
        class="min-w-max rounded-lg px-3 py-2 text-left text-sm transition-colors"
        :class="modelValue === tab.id ? 'bg-indigo-600 text-white shadow-sm' : 'bg-gray-100 text-gray-600 hover:bg-indigo-50 hover:text-indigo-700 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-indigo-950/40 dark:hover:text-indigo-200'"
        :aria-selected="modelValue === tab.id"
        :aria-controls="`${idPrefix}-${tab.id}-panel`"
        @click="$emit('update:modelValue', tab.id)"
      >
        <span class="block font-semibold">{{ tab.label }}</span>
        <span v-if="tab.summary" class="mt-0.5 block max-w-[13rem] truncate text-xs opacity-80">{{ tab.summary }}</span>
      </button>
    </div>
    <div
      v-if="activeTab?.summary"
      class="mt-3 rounded-lg bg-gray-50 px-3 py-2 text-xs leading-5 text-gray-500 dark:bg-gray-900 dark:text-gray-400"
      :id="`${idPrefix}-${activeTab.id}-panel`"
      role="tabpanel"
    >
      {{ activeTab.summary }}
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

export interface ModuleTabItem {
  id: string
  label: string
  summary?: string
}

const props = withDefaults(defineProps<{
  tabs: ModuleTabItem[]
  modelValue: string
  label?: string
  idPrefix?: string
}>(), {
  label: '模块选项卡',
  idPrefix: 'module-tab',
})

defineEmits<{
  'update:modelValue': [value: string]
}>()

const activeTab = computed(() => props.tabs.find((tab) => tab.id === props.modelValue))
</script>
