<template>
  <div class="p-4 sm:p-6 lg:p-8">
    <div class="mb-8 flex flex-col items-start justify-between gap-4 sm:flex-row sm:gap-6">
      <div>
        <h1 class="text-3xl font-bold text-gray-800 dark:text-white">错题本</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-2">用间隔重复把每一次失误转化为关系直觉。</p>
      </div>
      <button @click="refresh" class="btn-secondary w-full sm:w-auto" :disabled="loading">
        {{ loading ? '刷新中...' : '刷新错题' }}
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="card"><p class="text-sm text-gray-500">未掌握错题</p><p class="text-3xl font-bold text-gray-800 dark:text-white mt-2">{{ mistakes.length }}</p></div>
      <div class="card"><p class="text-sm text-gray-500">今日到期</p><p class="text-3xl font-bold text-orange-500 mt-2">{{ dueReviews.length }}</p></div>
      <div class="card"><p class="text-sm text-gray-500">累计答对</p><p class="text-3xl font-bold text-green-500 mt-2">{{ totalCorrect }}</p></div>
      <div class="card"><p class="text-sm text-gray-500">累计答错</p><p class="text-3xl font-bold text-red-500 mt-2">{{ totalWrong }}</p></div>
    </div>

    <ModuleTabs
      v-model="activeTab"
      :tabs="mistakeTabs"
      label="错题本选项卡"
      id-prefix="mistakes-tab"
      class="mb-6"
      @update:model-value="onTabChange"
    />

    <div v-if="activeTab === 'due_review' && dueReviews.length" class="card mb-8 border border-orange-200 dark:border-orange-800 bg-orange-50/60 dark:bg-orange-900/10">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4">今日优先复习</h2>
      <div class="space-y-3">
        <div v-for="item in dueReviews" :key="item.mistake_id" class="p-4 rounded-xl bg-white dark:bg-gray-800 flex items-start justify-between gap-4">
          <div>
            <p class="text-sm text-orange-600 dark:text-orange-400 mb-1">到期错题 #{{ item.mistake_id }}</p>
            <p class="font-medium text-gray-800 dark:text-white">{{ item.sample.their_words }}</p>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ item.sample.context }}</p>
          </div>
          <div class="flex shrink-0 flex-col gap-2 sm:flex-row">
            <button @click="submitReview(item.mistake_id, false)" class="px-3 py-2 rounded-lg bg-red-100 text-red-600 text-sm">还没掌握</button>
            <button @click="submitReview(item.mistake_id, true)" class="px-3 py-2 rounded-lg bg-green-500 text-white text-sm">已掌握</button>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="activeTab !== 'mastery_evidence' && resourceContext"
      class="card mb-8 border border-sky-100 bg-sky-50/70 dark:border-sky-900/50 dark:bg-sky-950/20"
    >
      <div class="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div class="min-w-0">
          <p class="text-sm font-semibold text-sky-700 dark:text-sky-300">来自资源海洋的错题改写上下文</p>
          <h2 class="mt-1 break-words text-xl font-bold text-gray-800 dark:text-white">{{ resourceContext.title || '未命名资源' }}</h2>
          <p class="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">{{ resourceMistakeGuidance }}</p>
        </div>
        <div class="flex shrink-0 flex-wrap gap-2">
          <RouterLink
            :to="{ name: 'ResourceDetail', params: { id: resourceContext.id } }"
            class="rounded-lg bg-white px-3 py-2 text-sm font-semibold text-sky-700 shadow-sm hover:bg-sky-100 dark:bg-gray-900 dark:text-sky-300 dark:hover:bg-sky-950/60"
          >
            回看资源
          </RouterLink>
          <RouterLink
            :to="{ path: '/trainer', query: { resource_id: resourceContext.id, q: resourceContext.title || resourceContext.category } }"
            class="rounded-lg bg-sky-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-sky-700"
          >
            带入训练
          </RouterLink>
          <button class="rounded-lg bg-white px-3 py-2 text-sm font-semibold text-gray-600 shadow-sm hover:bg-gray-100 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-800" type="button" @click="clearResourceContext">
            只看全部错题
          </button>
        </div>
      </div>
      <div class="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-4">
        <div class="rounded-lg bg-white p-3 text-sm dark:bg-gray-900">
          <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">改写焦点</p>
          <p class="mt-1 text-gray-800 dark:text-gray-100">{{ resourceContext.mistake_pattern || '把失误改成可练动作' }}</p>
        </div>
        <div class="rounded-lg bg-white p-3 text-sm dark:bg-gray-900">
          <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">表达目标</p>
          <p class="mt-1 text-gray-800 dark:text-gray-100">{{ resourceContext.expression_goal || '低压承接' }}</p>
        </div>
        <div class="rounded-lg bg-white p-3 text-sm dark:bg-gray-900">
          <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">场景 / 分类</p>
          <p class="mt-1 text-gray-800 dark:text-gray-100">{{ resourceContext.applicable_scene || resourceContext.category }}</p>
        </div>
        <div class="rounded-lg bg-white p-3 text-sm dark:bg-gray-900">
          <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">质量 / 难度</p>
          <p class="mt-1 text-gray-800 dark:text-gray-100">Q{{ resourceContext.quality_score || '-' }} · D{{ resourceContext.difficulty_level || '-' }}</p>
        </div>
      </div>
      <div v-if="resourceContext.usage_tip || resourceContext.source_summary" class="mt-3 rounded-lg bg-white p-3 text-sm leading-6 text-gray-600 dark:bg-gray-900 dark:text-gray-300">
        {{ resourceContext.usage_tip || resourceContext.source_summary }}
      </div>
    </div>

    <div v-if="activeTab !== 'mastery_evidence'" class="flex flex-wrap items-center gap-3 mb-6">
      <button v-for="filter in filters" :key="filter.value" @click="selectedFilter = filter.value" class="px-4 py-2 rounded-lg text-sm font-medium transition-colors" :class="selectedFilter === filter.value ? 'bg-blue-500 text-white' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300'">
        {{ filter.label }}
      </button>
    </div>

    <div v-if="activeTab === 'mastery_evidence'" class="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <div class="card">
        <p class="text-sm text-gray-500">掌握率</p>
        <p class="mt-2 text-4xl font-bold text-green-500">{{ masteryRate }}%</p>
        <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">按累计答对 / 总复习次数估算，只作为训练证据，不当人格标签。</p>
      </div>
      <div class="card lg:col-span-2">
        <h2 class="mb-4 text-xl font-bold text-gray-800 dark:text-white">掌握证据</h2>
        <div v-if="mistakes.length" class="space-y-3">
          <div v-for="mistake in mistakes.slice(0, 8)" :key="`evidence-${mistake.id}`" class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <p class="font-semibold text-gray-800 dark:text-white">#{{ mistake.id }} {{ mistake.review_focus || mistake.emotion_mistake || '回应差异' }}</p>
              <span class="text-xs text-gray-400">对 {{ mistake.correct_count || 0 }} / 错 {{ mistake.wrong_count || 0 }}</span>
            </div>
            <p class="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">{{ mistake.their_words }}</p>
            <p v-if="mistake.next_review" class="mt-1 text-xs text-gray-400">下次复习：{{ mistake.next_review }}</p>
          </div>
        </div>
        <p v-else class="text-sm text-gray-500">暂无掌握证据，先完成一次训练或错题复习。</p>
      </div>
    </div>

    <div v-else class="space-y-4">
      <div v-for="mistake in focusedMistakes" :key="mistake.id" class="card border border-red-100 dark:border-red-900/50">
        <div class="flex items-start gap-4">
          <div class="w-10 h-10 rounded-full bg-red-500 text-white flex items-center justify-center font-bold shrink-0">{{ mistake.id }}</div>
          <div class="flex-1 min-w-0">
            <div class="flex flex-wrap items-center gap-2 mb-3">
              <span class="px-2 py-0.5 rounded text-xs bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400">{{ mistake.emotion_mistake || '回应差异' }}</span>
              <span v-if="mistake.review_focus" class="px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-300">{{ mistake.review_focus }}</span>
              <span v-if="mistake.next_review" class="text-xs text-gray-400">下次复习：{{ mistake.next_review }}</span>
            </div>
            <p class="text-gray-700 dark:text-gray-200 mb-3">{{ mistake.context }}</p>
            <div class="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 mb-3">
              <p class="text-xs text-blue-600 dark:text-blue-400 mb-1">TA 说</p>
              <p class="text-gray-800 dark:text-white">{{ mistake.their_words }}</p>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div class="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                <p class="text-sm text-red-600 dark:text-red-400 mb-1">你的回应</p>
                <p class="text-sm text-gray-700 dark:text-gray-200">{{ mistake.user_bad_response }}</p>
              </div>
              <div class="p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
                <p class="text-sm text-green-600 dark:text-green-400 mb-1">理想回应</p>
                <p class="text-sm text-gray-700 dark:text-gray-200">{{ mistake.correct_response }}</p>
              </div>
            </div>
            <div v-if="mistake.error_attribution?.length" class="mb-4 rounded-lg bg-gray-50 dark:bg-gray-800 p-3">
              <p class="text-sm font-semibold text-gray-800 dark:text-white mb-2">结构化错误归因</p>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                <div v-for="item in mistake.error_attribution" :key="`${mistake.id}-${item.category}-${item.dimension}`" class="rounded-lg bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 p-3">
                  <div class="flex items-center justify-between gap-2 mb-1">
                    <span class="text-sm font-medium text-gray-800 dark:text-white">{{ item.category }}</span>
                    <span class="text-xs text-blue-500">{{ dimensionLabel(item.dimension) }}</span>
                  </div>
                  <p class="text-xs text-gray-500 dark:text-gray-400">{{ item.reason }}</p>
                  <p class="text-xs text-green-600 dark:text-green-300 mt-2">{{ item.repair }}</p>
                </div>
              </div>
            </div>
            <div class="mb-4 grid grid-cols-1 gap-3 lg:grid-cols-3">
              <div v-if="mistake.emotion_flow?.length" class="rounded-lg bg-indigo-50 p-3 dark:bg-indigo-900/20">
                <p class="mb-2 text-sm font-semibold text-indigo-700 dark:text-indigo-300">情绪流动动线</p>
                <ol class="space-y-2 text-xs leading-5 text-gray-600 dark:text-gray-300">
                  <li v-for="(step, index) in mistake.emotion_flow" :key="`${mistake.id}-flow-${index}`">
                    {{ index + 1 }}. {{ step }}
                  </li>
                </ol>
              </div>
              <div v-if="mistake.rewrite_drills?.length" class="rounded-lg bg-emerald-50 p-3 dark:bg-emerald-900/20">
                <p class="mb-2 text-sm font-semibold text-emerald-700 dark:text-emerald-300">三步改写练习</p>
                <ol class="space-y-2 text-xs leading-5 text-gray-600 dark:text-gray-300">
                  <li v-for="(drill, index) in mistake.rewrite_drills" :key="`${mistake.id}-drill-${index}`">
                    {{ index + 1 }}. {{ drill }}
                  </li>
                </ol>
              </div>
              <div v-if="mistake.resource_queries?.length" class="rounded-lg bg-sky-50 p-3 dark:bg-sky-900/20">
                <p class="mb-2 text-sm font-semibold text-sky-700 dark:text-sky-300">关联资源检索</p>
                <div class="flex flex-wrap gap-2">
                  <RouterLink
                    v-for="query in mistake.resource_queries"
                    :key="`${mistake.id}-${query}`"
                    :to="{ path: '/resources', query: { q: query } }"
                    class="rounded bg-white px-2 py-1 text-xs text-sky-700 shadow-sm hover:bg-sky-100 dark:bg-gray-900 dark:text-sky-300"
                  >
                    {{ query }}
                  </RouterLink>
                </div>
              </div>
            </div>
            <div v-if="mistake.expression_rewrite" class="mb-4 rounded-lg border border-indigo-100 bg-indigo-50/70 p-3 dark:border-indigo-900/50 dark:bg-indigo-950/20">
              <div class="mb-3 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p class="text-xs font-semibold text-indigo-500 dark:text-indigo-300">表达工具改写链</p>
                  <h3 class="text-base font-bold text-gray-800 dark:text-white">{{ mistake.expression_rewrite.target_goal }} · {{ mistake.expression_rewrite.primary_tool }}</h3>
                  <p class="mt-1 text-xs leading-relaxed text-gray-600 dark:text-gray-300">{{ mistake.expression_rewrite.principle }}</p>
                </div>
                <RouterLink
                  :to="{ path: '/expression', query: { goal: mistake.expression_rewrite.target_goal } }"
                  class="rounded bg-white px-3 py-2 text-xs font-semibold text-indigo-700 shadow-sm hover:bg-indigo-100 dark:bg-gray-900 dark:text-indigo-300"
                >
                  查看工具箱
                </RouterLink>
              </div>

              <div class="grid grid-cols-1 gap-3 xl:grid-cols-3">
                <div v-for="version in mistake.expression_rewrite.rewrite_versions" :key="`${mistake.id}-${version.name}`" class="rounded-lg bg-white p-3 dark:bg-gray-900">
                  <p class="text-sm font-semibold text-indigo-600 dark:text-indigo-300">{{ version.name }}</p>
                  <p class="mt-2 text-sm leading-relaxed text-gray-700 dark:text-gray-200">{{ version.text }}</p>
                  <p class="mt-2 text-xs text-gray-400">{{ version.tool }}</p>
                </div>
              </div>

              <div class="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
                <div class="rounded-lg bg-white p-3 dark:bg-gray-900">
                  <p class="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-200">推荐工具</p>
                  <div class="flex flex-wrap gap-2">
                    <span v-for="tool in mistake.expression_rewrite.recommended_tools" :key="`${mistake.id}-${tool.tool_uuid}`" class="rounded bg-indigo-100 px-2 py-1 text-xs text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-200">
                      {{ tool.name }}
                    </span>
                  </div>
                </div>
                <div class="rounded-lg bg-white p-3 dark:bg-gray-900">
                  <p class="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-200">迁移与禁区</p>
                  <p class="text-xs leading-relaxed text-gray-600 dark:text-gray-300">{{ mistake.expression_rewrite.transfer_drill }}</p>
                  <ul class="mt-2 space-y-1">
                    <li v-for="move in mistake.expression_rewrite.forbidden_moves" :key="`${mistake.id}-${move}`" class="text-xs text-amber-700 dark:text-amber-300">{{ move }}</li>
                  </ul>
                </div>
              </div>
            </div>
            <div class="flex flex-wrap items-center gap-3">
              <button @click="submitReview(mistake.id, false)" class="px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-sm">继续复习</button>
              <button @click="submitReview(mistake.id, true)" class="px-4 py-2 rounded-lg bg-green-500 text-white text-sm">标记掌握</button>
              <span class="text-xs text-gray-400 ml-auto">对 {{ mistake.correct_count || 0 }} / 错 {{ mistake.wrong_count || 0 }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="focusedMistakes.length === 0" class="card text-center py-16">
        <div class="text-5xl mb-4">{{ resourceContext ? '⌕' : '🎉' }}</div>
        <h3 class="text-xl font-bold text-gray-800 dark:text-white mb-2">{{ resourceContext ? '暂无匹配错题' : '暂无错题' }}</h3>
        <p class="text-gray-500 dark:text-gray-400">{{ resourceContext ? '这个资源还没有匹配到历史错题，可以先带入训练生成新的练习记录。' : '完成训练后，系统会自动把需要复习的题加入这里。' }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import ModuleTabs from '@/components/ModuleTabs.vue'
import { useTrainingStore } from '@/stores/training'
import { useToast } from '@/utils/toast'
import { useResourceContextFromRoute } from '@/composables/useResourceContext'

const store = useTrainingStore()
const toast = useToast()
const { route, router, resourceContext, loadResourceContextFromRoute, clearResourceContext } = useResourceContextFromRoute({
  clearPath: '/mistakes',
  onError: (message) => toast.error(message),
})
const loading = ref(false)
const selectedFilter = ref<'all' | 'due'>('all')
const activeTab = ref('due_review')

const mistakeTabs = [
  { id: 'due_review', label: '待复习', summary: '优先处理今天到期和仍未掌握的错题。' },
  { id: 'rewrite', label: '三版改写', summary: '把同一旧回应改成轻、稳、深三版。' },
  { id: 'mastery_evidence', label: '掌握证据', summary: '查看错题是否真的被修复，而不是只被标记完成。' },
]

const filters = [
  { label: '全部错题', value: 'all' },
  { label: '今日到期', value: 'due' },
] as const

const mistakes = computed(() => store.mistakes)
const dueReviews = computed(() => store.dueReviews)
const totalCorrect = computed(() => mistakes.value.reduce((sum, item) => sum + (item.correct_count || 0), 0))
const totalWrong = computed(() => mistakes.value.reduce((sum, item) => sum + (item.wrong_count || 0), 0))
const masteryRate = computed(() => {
  const total = totalCorrect.value + totalWrong.value
  return total ? Math.round((totalCorrect.value / total) * 100) : 0
})
const dueIds = computed(() => new Set(dueReviews.value.map(item => item.mistake_id)))
const filteredMistakes = computed(() => {
  if (activeTab.value === 'due_review') return mistakes.value.filter(item => dueIds.value.has(item.id))
  if (selectedFilter.value === 'due') return mistakes.value.filter(item => dueIds.value.has(item.id))
  return mistakes.value
})
const resourceFocusTerms = computed(() => {
  if (!resourceContext.value) return []
  return [
    resourceContext.value.mistake_pattern,
    resourceContext.value.expression_goal,
    resourceContext.value.applicable_scene,
    resourceContext.value.category,
    resourceContext.value.title,
  ]
    .filter((value): value is string => Boolean(value && value.trim()))
    .flatMap(value => value.split(/[｜|,，、\s]+/))
    .map(value => value.trim())
    .filter(value => value.length >= 2)
})
const focusedMistakes = computed(() => {
  if (!resourceContext.value || resourceFocusTerms.value.length === 0) return filteredMistakes.value
  const terms = resourceFocusTerms.value
  const matched = filteredMistakes.value.filter((mistake) => {
    const haystack = [
      mistake.context,
      mistake.their_words,
      mistake.user_bad_response,
      mistake.correct_response,
      mistake.emotion_mistake,
      mistake.review_focus || '',
      ...(mistake.resource_queries || []),
      ...(mistake.emotion_flow || []),
      ...(mistake.rewrite_drills || []),
    ].join(' ')
    return terms.some(term => haystack.includes(term))
  })
  return matched.length ? matched : filteredMistakes.value
})
const resourceMistakeGuidance = computed(() => {
  if (!resourceContext.value) return ''
  const mistake = resourceContext.value.mistake_pattern || '把反应式回应改成可验证、可退出的表达'
  const goal = resourceContext.value.expression_goal || '低压承接'
  const scene = resourceContext.value.applicable_scene || resourceContext.value.category || '当前场景'
  return `围绕“${scene}”复盘错题：先识别“${mistake}”，再把回应改成“${goal}”。重点不是背话术，而是把旧反射改成更安全、更具体、更有人味的下一句。`
})

async function refresh() {
  loading.value = true
  await Promise.all([store.fetchMistakes(), store.fetchDueReviews(), store.fetchRadar(), loadResourceContextFromRoute()])
  loading.value = false
}

async function submitReview(mistakeId: number, correct: boolean) {
  const result = await store.submitReview(mistakeId, correct)
  if (result) {
    toast.success(correct ? '已进入更长间隔复习' : '已安排明日继续复习')
  } else {
    toast.error('提交失败，请稍后重试')
  }
}

function normalizeTab(value: unknown) {
  const tab = typeof value === 'string' ? value : ''
  return mistakeTabs.some((item) => item.id === tab) ? tab : 'due_review'
}

function onTabChange(value: string) {
  activeTab.value = normalizeTab(value)
  const query = { ...route.query }
  if (activeTab.value === 'due_review') delete query.tab
  else query.tab = activeTab.value
  router.replace({ path: '/mistakes', query })
}

onMounted(() => {
  activeTab.value = normalizeTab(route.query.tab)
  refresh()
})

watch(
  () => route.query.resource_id,
  () => {
    loadResourceContextFromRoute()
  }
)

function dimensionLabel(dimension: string) {
  const labels: Record<string, string> = {
    emotion_score: '情绪识别',
    need_score: '需求洞察',
    safety_score: '安全回应',
    connection_score: '连接延展',
    boundary_score: '边界尊重',
    style_score: '风格匹配',
    repair_score: '修复能力',
  }
  return labels[dimension] || dimension
}
</script>
