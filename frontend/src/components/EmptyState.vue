<template>
  <div class="flex flex-col items-center justify-center py-16 px-4 text-center">
    <!-- 图标 -->
    <div
      class="w-24 h-24 rounded-full flex items-center justify-center mb-6"
      :class="iconBgClass"
    >
      <component :is="iconComponent" class="w-12 h-12" :class="iconColorClass" />
    </div>

    <!-- 标题 -->
    <h3 class="text-xl font-bold text-gray-800 dark:text-white mb-2">
      {{ resolvedTitle }}
    </h3>

    <!-- 描述 -->
    <p class="text-gray-500 dark:text-gray-400 max-w-md mb-6">
      {{ resolvedDescription }}
    </p>

    <!-- 操作按钮 -->
    <button
      v-if="actionText"
      @click="$emit('action')"
      class="btn-primary"
    >
      {{ actionText }}
    </button>

    <!-- 自定义内容插槽 -->
    <slot v-else name="action"></slot>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Inbox, Search, FileQuestion, CheckCircle, AlertCircle } from 'lucide-vue-next'

interface Props {
  type?: 'empty' | 'no-results' | 'error' | 'success' | 'no-data'
  title?: string
  description?: string
  actionText?: string
  icon?: any
}

const props = withDefaults(defineProps<Props>(), {
  type: 'empty',
  title: undefined,
  description: undefined,
  actionText: ''
})

defineEmits<{
  action: []
}>()

const iconComponent = computed(() => {
  if (props.icon) return props.icon

  const icons = {
    'empty': Inbox,
    'no-results': Search,
    'error': AlertCircle,
    'success': CheckCircle,
    'no-data': FileQuestion
  }

  return icons[props.type] || Inbox
})

const iconBgClass = computed(() => {
  const classes = {
    'empty': 'bg-gray-100 dark:bg-gray-800',
    'no-results': 'bg-blue-100 dark:bg-blue-900/30',
    'error': 'bg-red-100 dark:bg-red-900/30',
    'success': 'bg-green-100 dark:bg-green-900/30',
    'no-data': 'bg-purple-100 dark:bg-purple-900/30'
  }
  return classes[props.type] || classes['empty']
})

const iconColorClass = computed(() => {
  const classes = {
    'empty': 'text-gray-400 dark:text-gray-500',
    'no-results': 'text-blue-500',
    'error': 'text-red-500',
    'success': 'text-green-500',
    'no-data': 'text-purple-500'
  }
  return classes[props.type] || classes['empty']
})

const resolvedTitle = computed(() => {
  if (props.title) return props.title
  const titles = {
    'empty': '暂无数据',
    'no-results': '没有找到结果',
    'error': '出错了',
    'success': '操作成功',
    'no-data': '暂无记录'
  }
  return titles[props.type] || '暂无数据'
})

const resolvedDescription = computed(() => {
  if (props.description) return props.description
  const descriptions = {
    'empty': '这里还没有任何内容，稍后再来看看吧',
    'no-results': '尝试调整搜索条件或筛选器',
    'error': '抱歉，发生了错误，请稍后再试',
    'success': '太好了，你已经完成了！',
    'no-data': '还没有相关记录，开始添加吧'
  }
  return descriptions[props.type] || ''
})
</script>

<script lang="ts">
// 导出类型
export type EmptyStateType = 'empty' | 'no-results' | 'error' | 'success' | 'no-data'
</script>
