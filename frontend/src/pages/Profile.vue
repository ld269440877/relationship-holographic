<template>
  <div class="p-8">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-800 dark:text-white">我的档案</h1>
      <p class="text-gray-500 dark:text-gray-400 mt-2">了解自己，提升感知</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div class="card">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">基本信息</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
            <span class="text-gray-600 dark:text-gray-300">依恋类型</span>
            <span class="px-3 py-1 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
              {{ displayProfile.attachmentStyle }}
            </span>
          </div>
          <div class="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
            <span class="text-gray-600 dark:text-gray-300">爱语</span>
            <span class="text-gray-800 dark:text-white">{{ displayProfile.loveLanguage }}</span>
          </div>
          <div class="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
            <span class="text-gray-600 dark:text-gray-300">情绪词汇量</span>
            <span class="text-gray-800 dark:text-white">{{ displayProfile.emotionVocabSize }}</span>
          </div>
          <div class="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
            <span class="text-gray-600 dark:text-gray-300">感知基线</span>
            <span class="text-gray-800 dark:text-white">{{ displayProfile.perceptionBaseline }}</span>
          </div>
        </div>
      </div>

      <div class="card">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">能力成长曲线</h2>
        <div class="space-y-4">
          <div v-for="(skill, index) in skills" :key="index" class="space-y-2">
            <div class="flex items-center justify-between gap-4">
              <span class="text-sm text-gray-600 dark:text-gray-300">{{ skill.name }}</span>
              <span class="text-sm text-gray-500 dark:text-gray-400">{{ skill.value }}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-bar-fill" :style="{ width: skill.value + '%' }"></div>
            </div>
            <p class="text-xs text-gray-400 dark:text-gray-500">{{ skill.description }}</p>
          </div>
        </div>
        <p class="mt-5 text-xs leading-relaxed text-gray-500 dark:text-gray-400">
          {{ radarEvidenceText }}
        </p>
      </div>
    </div>

    <div class="card mt-6">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">学习统计</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div v-for="stat in stats" :key="stat.label" class="text-center p-4 rounded-xl" :class="stat.className">
          <p class="text-3xl font-bold" :class="stat.valueClass">{{ stat.value }}</p>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ stat.label }}</p>
          <p class="mt-2 text-xs text-gray-400 dark:text-gray-500">{{ stat.source }}</p>
        </div>
      </div>
    </div>

    <div class="card mt-6">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">自我觉察</h2>
      <div class="space-y-4">
        <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-2">我的惯性模式</p>
          <p class="text-gray-800 dark:text-white">{{ selfAwareness.pattern }}</p>
        </div>
        <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-2">需要提升的方面</p>
          <p class="text-gray-800 dark:text-white">{{ selfAwareness.improvement }}</p>
        </div>
        <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-2">当前建议</p>
          <p class="text-gray-800 dark:text-white">{{ selfAwareness.recommendation }}</p>
        </div>
      </div>
    </div>

    <div class="card mt-6">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">计算依据</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="item in evidenceItems" :key="item.title" class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
          <p class="font-semibold text-gray-800 dark:text-white">{{ item.title }}</p>
          <p class="mt-2 text-sm leading-relaxed text-gray-600 dark:text-gray-300">{{ item.description }}</p>
          <p class="mt-2 text-xs text-gray-400 dark:text-gray-500">{{ item.source }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProfileStore } from '@/stores/profile'
import { useTrainingStore } from '@/stores/training'
import { samplesApi } from '@/utils/api'

const profileStore = useProfileStore()
const trainingStore = useTrainingStore()
const profile = computed(() => profileStore.profile)
const sampleTotal = ref<number | null>(null)

const fallbackSkills = [
  { name: '情绪识别', score: 0, description: '尚未训练' },
  { name: '需求洞察', score: 0, description: '尚未训练' },
  { name: '安全回应', score: 0, description: '尚未训练' },
  { name: '连接延展', score: 0, description: '尚未训练' },
  { name: '边界尊重', score: 0, description: '尚未训练' },
  { name: '风格匹配', score: 0, description: '尚未训练' },
  { name: '修复能力', score: 0, description: '尚未训练' },
]

const displayProfile = computed(() => ({
  attachmentStyle: profile.value?.attachment_style || '待填写',
  loveLanguage: profile.value?.love_language || '待填写',
  emotionVocabSize: typeof profile.value?.emotion_vocab_size === 'number' ? `${profile.value.emotion_vocab_size} 个` : '待测评',
  perceptionBaseline: typeof profile.value?.perception_baseline === 'number' ? `${profile.value.perception_baseline} / 100` : '待测评',
}))

const skills = computed(() => {
  const levels = trainingStore.radar?.levels?.length ? trainingStore.radar.levels : fallbackSkills
  return levels.map((skill) => ({
    name: skill.name,
    value: Math.max(0, Math.min(100, Math.round(skill.score || 0))),
    description: skill.description || '等待更多训练记录生成趋势',
  }))
})

const radarEvidenceText = computed(() => {
  if (!trainingStore.weekSummary?.attempts_count) {
    return '能力曲线来自真实训练记录；当前近 7 天暂无训练，页面显示待启动基线。'
  }
  return `能力曲线由最近训练记录的维度分聚合生成，当前综合水平：${trainingStore.radar?.level || '待计算'}，近 7 天训练 ${trainingStore.weekSummary.attempts_count} 次。`
})

const stats = computed(() => [
  {
    label: '今日训练',
    value: trainingStore.todaySummary?.attempts_count ?? 0,
    source: '/api/training/summary/today',
    className: 'bg-blue-50 dark:bg-blue-900/20',
    valueClass: 'text-blue-600 dark:text-blue-400',
  },
  {
    label: '近 7 天训练',
    value: trainingStore.weekSummary?.attempts_count ?? 0,
    source: '/api/training/summary/week',
    className: 'bg-green-50 dark:bg-green-900/20',
    valueClass: 'text-green-600 dark:text-green-400',
  },
  {
    label: '近 7 天活跃',
    value: trainingStore.weekSummary?.active_days ?? 0,
    source: '按训练日期去重',
    className: 'bg-purple-50 dark:bg-purple-900/20',
    valueClass: 'text-purple-600 dark:text-purple-400',
  },
  {
    label: '平均得分',
    value: trainingStore.weekSummary?.average_score ?? trainingStore.radar?.total_score ?? 0,
    source: '近 7 天平均',
    className: 'bg-orange-50 dark:bg-orange-900/20',
    valueClass: 'text-orange-600 dark:text-orange-400',
  },
  {
    label: '开放错题',
    value: trainingStore.todaySummary?.mistakes_open ?? trainingStore.mistakes.length,
    source: '/api/training/mistakes',
    className: 'bg-rose-50 dark:bg-rose-900/20',
    valueClass: 'text-rose-600 dark:text-rose-400',
  },
  {
    label: '待复习',
    value: trainingStore.dueReviews.length,
    source: '/api/training/reviews/due',
    className: 'bg-amber-50 dark:bg-amber-900/20',
    valueClass: 'text-amber-600 dark:text-amber-400',
  },
  {
    label: '样本库容量',
    value: sampleTotal.value ?? 0,
    source: '/api/samples',
    className: 'bg-cyan-50 dark:bg-cyan-900/20',
    valueClass: 'text-cyan-600 dark:text-cyan-400',
  },
  {
    label: '能力总分',
    value: trainingStore.radar?.total_score ?? 0,
    source: '/api/training/radar',
    className: 'bg-slate-50 dark:bg-slate-700/40',
    valueClass: 'text-slate-700 dark:text-slate-200',
  },
])

const selfAwareness = computed(() => {
  const wound = profile.value?.core_wound
  const weakest = trainingStore.radar?.weakest_dimension
  const noTraining = !trainingStore.weekSummary?.attempts_count && !trainingStore.todaySummary?.attempts_count
  const minScore = Math.min(...skills.value.map((skill) => skill.value))
  const weakestName = skills.value.find((item) => item.value === minScore)?.name

  return {
    pattern: wound
      ? `档案记录的核心议题是「${wound}」。这属于用户手动资料，不由系统猜测。`
      : '尚未填写核心创伤/惯性模式；完成档案设置和训练后再生成更可靠的画像。',
    improvement: noTraining
      ? '暂无训练记录，无法判定真实短板。建议先完成一次对比回应训练，建立能力基线。'
      : `当前训练中最需要关注的是「${weakestName || weakest || '待计算'}」，系统根据训练维度平均分定位。`,
    recommendation: trainingStore.todaySummary?.recommendation
      || trainingStore.radar?.next_recommendation
      || '继续完成每日训练，积累足够样本后生成个性化建议。',
  }
})

const evidenceItems = computed(() => [
  {
    title: '手动档案资料',
    description: '依恋类型、爱语、核心议题、情绪词汇量和感知基线来自用户档案接口；未填写时显示待填写/待测评，不再用前端假默认值伪装成结论。',
    source: '/api/profile',
  },
  {
    title: '能力曲线',
    description: '能力成长曲线由后端按训练记录的情绪、需求、安全、连接、边界、风格、修复等维度分计算；没有训练记录时统一显示 0 和尚未训练。',
    source: '/api/training/radar',
  },
  {
    title: '学习统计',
    description: '今日训练、近 7 天训练、近 7 天活跃天数、平均得分来自训练摘要接口。当前还没有终身累计训练和连续签到专用接口，因此页面只展示能够被接口证明的指标。',
    source: '/api/training/summary/today + /api/training/summary/week',
  },
  {
    title: '错题与复习',
    description: '开放错题来自错题本，待复习来自间隔复习队列；它们会随着训练提交、错题复习结果实时变化。',
    source: '/api/training/mistakes + /api/training/reviews/due',
  },
  {
    title: '样本库容量',
    description: '样本库容量是系统可训练样本总量，不等于用户已完成学习量。个人学习量需要新增学习事件口径后才能独立统计。',
    source: '/api/samples?limit=1',
  },
])

onMounted(async () => {
  const [, , , , , samples] = await Promise.all([
    profileStore.fetchProfile(),
    trainingStore.fetchRadar(),
    trainingStore.fetchMistakes(),
    trainingStore.fetchDueReviews(),
    trainingStore.fetchSummaries(),
    samplesApi.list({ limit: 1 }).catch(() => null),
  ])
  sampleTotal.value = samples?.total ?? null
})
</script>
