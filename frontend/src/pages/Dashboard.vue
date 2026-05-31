<template>
  <div class="p-4 sm:p-6 lg:p-8">
    <!-- 标题区 -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-800 dark:text-white">仪表盘</h1>
      <p class="text-gray-500 dark:text-gray-400 mt-2">欢迎回来，今天也要加油哦 ✨</p>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="card card-hover">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
            <span class="text-2xl">🎯</span>
          </div>
          <div>
            <p class="text-sm text-gray-500 dark:text-gray-400">今日训练</p>
            <p class="text-2xl font-bold text-gray-800 dark:text-white">{{ store.todaySummary?.attempts_count ?? 0 }}</p>
          </div>
        </div>
      </div>

      <div class="card card-hover">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
            <span class="text-2xl">🔥</span>
          </div>
          <div>
            <p class="text-sm text-gray-500 dark:text-gray-400">连续打卡</p>
            <p class="text-2xl font-bold text-gray-800 dark:text-white">{{ store.weekSummary?.active_days ?? 0 }} 天</p>
          </div>
        </div>
      </div>

      <div class="card card-hover">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
            <span class="text-2xl">📊</span>
          </div>
          <div>
            <p class="text-sm text-gray-500 dark:text-gray-400">综合能力</p>
            <p class="text-2xl font-bold text-gray-800 dark:text-white">{{ radarData?.total_score ?? 0 }}%</p>
          </div>
        </div>
      </div>

      <div class="card card-hover">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center">
            <span class="text-2xl">📚</span>
          </div>
          <div>
            <p class="text-sm text-gray-500 dark:text-gray-400">本周训练</p>
            <p class="text-2xl font-bold text-gray-800 dark:text-white">{{ store.weekSummary?.attempts_count ?? 0 }}</p>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-8">
      <div class="card">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
          <div>
            <h2 class="text-xl font-bold text-gray-800 dark:text-white">AI 质量哨站</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">成功、降级、安全阻断和延迟的运行态势</p>
          </div>
          <span class="px-3 py-1 rounded bg-gray-100 dark:bg-gray-700 text-sm text-gray-600 dark:text-gray-300">
            {{ aiQuality?.summary.runs ?? 0 }} 次运行
          </span>
        </div>
        <div v-if="aiQuality" class="space-y-5">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricPill label="成功率" :value="`${aiQuality.summary.success_rate}%`" />
            <MetricPill label="降级率" :value="`${aiQuality.summary.fallback_rate}%`" />
            <MetricPill label="安全阻断" :value="`${aiQuality.summary.safety_block_rate}%`" />
            <MetricPill label="平均延迟" :value="`${aiQuality.summary.avg_latency_ms}ms`" />
          </div>
          <div class="space-y-3">
            <div v-for="item in aiQuality.outcome_breakdown.slice(0, 4)" :key="item.name" class="space-y-1">
              <div class="flex items-center justify-between text-sm">
                <span class="text-gray-600 dark:text-gray-300">{{ outcomeLabel(item.name) }}</span>
                <span class="text-gray-500">{{ item.count }} · {{ item.rate }}%</span>
              </div>
              <div class="h-2 rounded bg-gray-100 dark:bg-gray-700 overflow-hidden">
                <div class="h-full bg-emerald-500" :style="{ width: `${item.rate}%` }"></div>
              </div>
            </div>
          </div>
          <ActionList :items="aiQuality.next_actions" />
        </div>
        <div v-else class="text-center py-8 text-gray-400">加载中...</div>
      </div>

      <div class="card">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
          <div>
            <h2 class="text-xl font-bold text-gray-800 dark:text-white">跨会话关系趋势</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">长期观察信任、压力、边界和连接的变化</p>
          </div>
          <span class="px-3 py-1 rounded bg-blue-100 dark:bg-blue-900/30 text-sm text-blue-600 dark:text-blue-300">
            修复指数 {{ relationshipTrends?.summary.repair_index ?? 0 }}
          </span>
        </div>
        <div v-if="relationshipTrends" class="space-y-5">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricPill label="会话" :value="relationshipTrends.summary.sessions" />
            <MetricPill label="轮次" :value="relationshipTrends.summary.turns" />
            <MetricPill label="均分" :value="relationshipTrends.summary.average_score" />
            <MetricPill label="阻断会话" :value="relationshipTrends.summary.blocked_sessions" />
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-5 gap-3">
            <DeltaTile label="信任" :value="relationshipTrends.average_state_delta.trust" />
            <DeltaTile label="压力" :value="relationshipTrends.average_state_delta.stress" reverse />
            <DeltaTile label="边界压力" :value="relationshipTrends.average_state_delta.boundary" reverse />
            <DeltaTile label="边界安全" :value="relationshipTrends.average_state_delta.boundary_safety" />
            <DeltaTile label="连接" :value="relationshipTrends.average_state_delta.connection" />
          </div>
          <div v-if="relationshipTrends.session_trend.length" class="space-y-2">
            <div
              v-for="session in relationshipTrends.session_trend.slice(-3)"
              :key="session.id"
              class="p-3 rounded bg-gray-50 dark:bg-gray-700/50"
            >
              <div class="flex items-center justify-between gap-3">
                <p class="text-sm font-medium text-gray-800 dark:text-white truncate">{{ session.scenario_name }}</p>
                <span class="text-xs text-gray-500">{{ session.average_score }}分</span>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ session.state_label }} · {{ session.next_focus }}</p>
            </div>
          </div>
          <ActionList :items="relationshipTrends.next_actions" />
        </div>
        <div v-else class="text-center py-8 text-gray-400">加载中...</div>
      </div>
    </div>

    <div class="card mb-8">
      <div class="flex flex-col xl:flex-row xl:items-start xl:justify-between gap-6">
        <div class="xl:max-w-xl">
          <div class="flex items-center gap-3 mb-3">
            <h2 class="text-xl font-bold text-gray-800 dark:text-white">Gold Set 校准台</h2>
            <span
              v-if="goldSummary"
              class="px-3 py-1 rounded text-xs"
              :class="goldSummary.quality_gates.ready_for_strict_calibration ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'"
            >
              {{ goldSummary.quality_gates.ready_for_strict_calibration ? '可严格校准' : '复核建设中' }}
            </span>
          </div>
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ goldSummary?.principle || 'Gold Set 是评分校准证据层。' }}</p>
          <div v-if="goldSummary" class="grid grid-cols-2 md:grid-cols-5 gap-3 mt-5">
            <MetricPill label="Gold 样本" :value="goldSummary.summary.gold_samples" />
            <MetricPill label="专家复核" :value="goldSummary.summary.expert_reviews" />
            <MetricPill label="待复核" :value="goldSummary.summary.pending_review" />
            <MetricPill label="覆盖率" :value="`${goldSummary.summary.expert_coverage_rate}%`" />
            <MetricPill label="平均信心" :value="goldSummary.summary.average_confidence" />
          </div>
          <ActionList v-if="goldSummary" class="mt-5" :items="goldSummary.next_actions" />
        </div>
        <div class="xl:w-[520px]">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-bold text-gray-800 dark:text-white">复核队列</h3>
            <span class="text-xs text-gray-500">{{ goldQueue?.total ?? 0 }} 项</span>
          </div>
          <div v-if="goldQueue?.items.length" class="space-y-3">
            <div v-for="item in goldQueue.items.slice(0, 3)" :key="item.sample.id" class="p-3 rounded border border-gray-100 dark:border-gray-700">
              <div class="flex items-center justify-between gap-3">
                <p class="font-medium text-gray-800 dark:text-white truncate">{{ item.sample.scenario_category }} · {{ item.sample.their_words }}</p>
                <span class="text-xs text-blue-500">{{ item.review_priority.score }}</span>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">{{ item.sample.context }}</p>
              <div class="flex flex-wrap gap-2 mt-2">
                <span v-for="reason in item.review_priority.reasons" :key="reason" class="px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 text-xs text-gray-500">
                  {{ reason }}
                </span>
              </div>
            </div>
          </div>
          <div v-else class="text-sm text-gray-400 py-6 text-center">暂无待复核项</div>
        </div>
      </div>
    </div>

    <!-- 八阶进度 & 今日推荐 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <div class="card">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">八阶能力进度</h2>
        <div v-if="radarData" class="space-y-4">
          <div v-for="(level, index) in radarData.levels" :key="index" class="flex items-center gap-4">
            <span class="w-32 text-sm text-gray-600 dark:text-gray-300">{{ level.name }}</span>
            <div class="flex-1 progress-bar">
              <div class="progress-bar-fill" :style="{ width: level.score + '%' }"></div>
            </div>
            <span class="w-12 text-sm text-gray-500 dark:text-gray-400">{{ level.score }}%</span>
          </div>
        </div>
        <div v-else class="text-center py-8 text-gray-400">加载中...</div>
      </div>

      <div class="card">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">今日推荐训练</h2>
        <div class="space-y-4">
          <div
            v-for="(training, index) in recommendedTrainings"
            :key="index"
            class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors cursor-pointer"
            @click="$router.push('/trainer')"
          >
            <div class="flex items-center justify-between">
              <div>
                <h3 class="font-medium text-gray-800 dark:text-white">{{ training.title }}</h3>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ training.description }}</p>
              </div>
              <span class="text-sm text-blue-500">{{ training.duration }}分钟</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 错题本摘要 -->
    <div class="card">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white">错题本</h2>
        <router-link to="/mistakes" class="text-sm text-blue-500 hover:underline">查看全部 →</router-link>
      </div>
      <div v-if="mistakes.length > 0" class="space-y-4">
        <div
          v-for="(mistake, index) in mistakes"
          :key="index"
          class="p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800"
        >
          <div class="flex items-start gap-4">
            <div class="w-8 h-8 rounded-full bg-red-100 dark:bg-red-900/50 flex items-center justify-center text-red-600 dark:text-red-400 font-bold text-sm">
              {{ index + 1 }}
            </div>
            <div class="flex-1">
              <p class="text-gray-700 dark:text-gray-200">{{ mistake.context }}</p>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">
                <span class="text-red-500">你的回应:</span> {{ mistake.user_bad_response }}
              </p>
              <p class="text-sm text-green-600 dark:text-green-400 mt-1">
                <span>理想回应:</span> {{ mistake.correct_response }}
              </p>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="text-center py-8 text-gray-500 dark:text-gray-400">
        🎉 太棒了！暂无错题
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, defineComponent, h, ref } from 'vue'
import { useTrainingStore } from '@/stores/training'
import { analyticsApi, samplesApi } from '@/utils/api'
import type { AIQualityReport, AnalyticsAction, GoldReviewQueue, GoldSummary, RelationshipTrends } from '@/utils/api'

const store = useTrainingStore()
const aiQuality = ref<AIQualityReport | null>(null)
const relationshipTrends = ref<RelationshipTrends | null>(null)
const goldSummary = ref<GoldSummary | null>(null)
const goldQueue = ref<GoldReviewQueue | null>(null)

const radarData = computed(() => store.radar)
const mistakes = computed(() => store.mistakes)

const recommendedTrainings = computed(() => [
  { title: '今日真实推荐', description: store.todaySummary?.recommendation || '完成一次对比回应训练', duration: 5 },
  { title: '下一题闭环训练', description: store.nextItem?.reason || '根据错题与最弱维度推荐', duration: 10 },
  { title: '错题间隔复习', description: `当前未掌握 ${store.todaySummary?.mistakes_open ?? mistakes.value.length} 题`, duration: 8 },
])

onMounted(async () => {
  await Promise.all([
    store.fetchRadar(),
    store.fetchMistakes(),
    store.fetchSummaries(),
    store.fetchNextTraining(),
    fetchAnalytics(),
  ])
})

async function fetchAnalytics() {
  const [quality, trends] = await Promise.all([
    analyticsApi.aiQuality(200),
    analyticsApi.relationshipTrends(50),
  ])
  aiQuality.value = quality
  relationshipTrends.value = trends
  const [summary, queue] = await Promise.all([
    samplesApi.goldSummary(),
    samplesApi.goldReviewQueue(5),
  ])
  goldSummary.value = summary
  goldQueue.value = queue
}

function outcomeLabel(value: string) {
  const map: Record<string, string> = {
    success: '结构化成功',
    success_raw_text: '文本降级成功',
    provider_failure: 'Provider 失败',
    blocked_safety: '安全阻断',
  }
  return map[value] ?? value
}

const MetricPill = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: [String, Number], required: true },
  },
  setup(props) {
    return () => h('div', { class: 'p-3 rounded bg-gray-50 dark:bg-gray-700/50' }, [
      h('p', { class: 'text-xs text-gray-500 dark:text-gray-400' }, props.label),
      h('p', { class: 'text-lg font-bold text-gray-800 dark:text-white mt-1' }, String(props.value)),
    ])
  },
})

const DeltaTile = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: Number, required: true },
    reverse: { type: Boolean, default: false },
  },
  setup(props) {
    return () => {
      const good = props.reverse ? props.value <= 0 : props.value >= 0
      const color = good ? 'text-emerald-600 dark:text-emerald-300' : 'text-orange-600 dark:text-orange-300'
      const prefix = props.value > 0 ? '+' : ''
      return h('div', { class: 'p-3 rounded bg-gray-50 dark:bg-gray-700/50' }, [
        h('p', { class: 'text-xs text-gray-500 dark:text-gray-400' }, props.label),
        h('p', { class: `text-lg font-bold mt-1 ${color}` }, `${prefix}${props.value}`),
      ])
    }
  },
})

const ActionList = defineComponent({
  props: {
    items: { type: Array as () => AnalyticsAction[], required: true },
  },
  setup(props) {
    return () => h('div', { class: 'space-y-2' }, props.items.slice(0, 3).map((item) => h('div', {
      class: 'p-3 rounded border border-gray-100 dark:border-gray-700',
    }, [
      h('div', { class: 'flex items-center justify-between gap-3' }, [
        h('p', { class: 'text-sm font-medium text-gray-800 dark:text-white' }, item.action),
        h('span', { class: 'text-xs text-gray-500' }, item.priority),
      ]),
      h('p', { class: 'text-xs text-gray-500 dark:text-gray-400 mt-1' }, item.reason),
    ])))
  },
})
</script>
