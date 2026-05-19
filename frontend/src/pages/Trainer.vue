<template>
  <div class="p-8">
    <!-- 标题 -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-800 dark:text-white">训练中心</h1>
      <p class="text-gray-500 dark:text-gray-400 mt-2">通过对比驱动学习，提升你的关系感知能力</p>
    </div>

    <!-- 训练模式选择 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div
        v-for="mode in trainingModes"
        :key="mode.id"
        class="card card-hover cursor-pointer"
        @click="startTraining(mode.id)"
      >
        <div class="w-16 h-16 rounded-2xl flex items-center justify-center mb-4" :class="mode.bgClass">
          <span class="text-3xl">{{ mode.icon }}</span>
        </div>
        <h3 class="text-xl font-bold text-gray-800 dark:text-white mb-2">{{ mode.name }}</h3>
        <p class="text-gray-500 dark:text-gray-400">{{ mode.description }}</p>
      </div>
    </div>

    <!-- 训练区域 -->
    <div v-if="currentMode && currentSample" class="card">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white">
          {{ currentModeName }} — 第 {{ currentStep }} / {{ totalSteps }}
        </h2>
        <button
          @click="resetTraining"
          class="px-4 py-2 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          退出训练
        </button>
      </div>

      <!-- 场景信息 -->
      <div class="mb-6 p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
        <div class="flex items-center gap-2 mb-2">
          <span class="px-2 py-1 rounded text-xs font-medium" :class="scenarioCategoryClass">
            {{ currentSample.scenario_category }}
          </span>
          <span class="text-sm text-gray-500 dark:text-gray-400">
            难度: {{ currentSample.difficulty_level }}
          </span>
        </div>
        <p class="text-gray-700 dark:text-gray-200">{{ currentSample.context }}</p>
      </div>

      <!-- 对方表现 -->
      <div class="mb-6 p-4 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
        <p class="text-sm text-blue-600 dark:text-blue-400 mb-2">对方说：</p>
        <p class="text-lg text-gray-800 dark:text-white">{{ currentSample.their_words }}</p>
        <p v-if="currentSample.their_behavior" class="text-sm text-gray-500 dark:text-gray-400 mt-2">
          行为：{{ currentSample.their_behavior }}
        </p>
      </div>

      <!-- 情绪标注 -->
      <div class="mb-6 p-4 rounded-xl bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800">
        <p class="text-sm text-purple-600 dark:text-purple-400 mb-2">情绪标签：</p>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="(emotion, idx) in emotionTags"
            :key="idx"
            class="px-3 py-1 rounded-full text-sm"
            :class="getEmotionClass(emotion.spectrum)"
          >
            {{ emotion.word }} ({{ emotion.intensity }})
          </span>
        </div>
      </div>

      <!-- 回应类型选择 -->
      <div v-if="!showResult" class="mb-4 flex gap-3">
        <button
          v-for="rt in responseTypes"
          :key="rt.value"
          @click="selectedResponseType = rt.value"
          class="px-3 py-1.5 rounded-lg text-sm transition-all"
          :class="selectedResponseType === rt.value
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'"
        >
          {{ rt.label }}
        </button>
      </div>

      <!-- 用户回应输入 -->
      <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          你的回应：
        </label>
        <textarea
          v-model="userResponse"
          class="input-mac min-h-[100px]"
          :placeholder="inputPlaceholder"
        ></textarea>
      </div>

      <!-- 提交按钮 -->
      <button
        v-if="!showResult"
        @click="submitResponse"
        class="btn-primary w-full"
        :disabled="!userResponse.trim() || submitting"
      >
        {{ submitting ? '分析中...' : '提交并对比' }}
      </button>

      <!-- 对比结果 -->
      <div v-if="showResult && comparisonResult" class="space-y-6">
        <!-- 分数 -->
        <div class="text-center p-6 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white">
          <p class="text-sm opacity-80">你的得分</p>
          <p class="text-5xl font-bold">{{ Math.round(comparisonResult.score) }}</p>
          <p class="text-sm opacity-80 mt-2">/ 100</p>
        </div>

        <!-- 差异分析 -->
        <div class="space-y-3">
          <div
            v-for="(diff, idx) in comparisonResult.differences"
            :key="idx"
            class="p-4 rounded-xl"
            :class="diff.type === 'problem' ? 'bg-red-50 dark:bg-red-900/20' : 'bg-green-50 dark:bg-green-900/20'"
          >
            <p class="font-medium" :class="diff.type === 'problem' ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'">
              {{ diff.type === 'problem' ? '❌ ' : '✅ ' }}{{ diff.name }}
            </p>
            <p class="text-sm text-gray-600 dark:text-gray-300 mt-1">{{ diff.desc }}</p>
          </div>
        </div>

        <!-- 理想回应 -->
        <div class="p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
          <p class="text-sm text-green-600 dark:text-green-400 mb-2">理想回应（{{ responseTypeLabel }}）：</p>
          <p class="text-gray-800 dark:text-white">{{ comparisonResult.ideal_response }}</p>
        </div>

        <!-- 详细报告 -->
        <details class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
          <summary class="cursor-pointer text-sm font-medium text-gray-600 dark:text-gray-300">详细分析报告</summary>
          <pre class="mt-3 text-xs text-gray-600 dark:text-gray-400 whitespace-pre-wrap">{{ comparisonResult.diff_report }}</pre>
        </details>

        <!-- 改进建议 -->
        <div class="p-4 rounded-xl bg-yellow-50 dark:bg-yellow-900/20">
          <p class="text-sm text-yellow-600 dark:text-yellow-400 mb-2">改进建议：</p>
          <ul class="list-disc list-inside space-y-1">
            <li v-for="(sug, i) in comparisonResult.suggestions" :key="i" class="text-gray-700 dark:text-gray-200">
              {{ sug }}
            </li>
          </ul>
        </div>

        <!-- 下一题 -->
        <button @click="nextStep" class="btn-primary w-full">
          继续训练 →
        </button>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-else-if="loading" class="card text-center py-12 text-gray-500">
      <div class="animate-spin text-4xl mb-4">🧠</div>
      <p>加载训练题目中...</p>
    </div>

    <!-- 训练模式说明 -->
    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="card">
        <h3 class="text-lg font-bold text-gray-800 dark:text-white mb-4">情绪猜猜乐</h3>
        <p class="text-gray-600 dark:text-gray-300">给定一段对话，识别其中包含的情绪标签和强度。锻炼你的情绪感知能力。</p>
      </div>
      <div class="card">
        <h3 class="text-lg font-bold text-gray-800 dark:text-white mb-4">对比回应训练</h3>
        <p class="text-gray-600 dark:text-gray-300">看场景，练习回应，然后对比你的回应与专家的理想回应，发现差距并改进。</p>
      </div>
      <div class="card">
        <h3 class="text-lg font-bold text-gray-800 dark:text-white mb-4">AI伴侣模拟</h3>
        <p class="text-gray-600 dark:text-gray-300">与不同依恋类型的AI模拟对象对话，练习在不同情况下的回应策略。</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useTrainingStore } from '@/stores/training'
import { useToast } from '@/utils/toast'
import type { EmotionTag } from '@/utils/api'

const trainingModes = [
  { id: 'emotion', name: '情绪猜猜乐', icon: '🎭', description: '识别对话中的情绪标签和强度', bgClass: 'bg-purple-100 dark:bg-purple-900/30' },
  { id: 'response', name: '对比回应', icon: '⚖️', description: '对比你的回应与理想回应', bgClass: 'bg-blue-100 dark:bg-blue-900/30' },
  { id: 'ai', name: 'AI伴侣模拟', icon: '🤖', description: '与不同类型的人对话', bgClass: 'bg-green-100 dark:bg-green-900/30' },
]

const responseTypes = [
  { value: 'soft', label: '柔和版' },
  { value: 'tension', label: '张力版' },
  { value: 'humor', label: '幽默版' },
]

const store = useTrainingStore()
const toast = useToast()

const currentMode = ref<string | null>(null)
const currentStep = ref(1)
const totalSteps = 10
const userResponse = ref('')
const showResult = ref(false)
const submitting = ref(false)
const selectedResponseType = ref('soft')
const comparisonResult = ref<{
  score: number
  differences: Array<{ type: string; name: string; desc: string }>
  suggestions: string[]
  ideal_response: string
  diff_report: string
} | null>(null)

const currentSample = computed(() => store.currentSample)
const loading = computed(() => store.loading)

const currentModeName = computed(() => {
  return trainingModes.find((m) => m.id === currentMode.value)?.name ?? ''
})

const responseTypeLabel = computed(() => {
  return responseTypes.find((r) => r.value === selectedResponseType.value)?.label ?? ''
})

const emotionTags = computed<EmotionTag[]>(() => {
  if (!currentSample.value?.emotion_tags_json) return []
  try {
    return JSON.parse(currentSample.value.emotion_tags_json)
  } catch {
    return []
  }
})

const scenarioCategoryClass = computed(() => {
  const category = currentSample.value?.scenario_category || '暧昧'
  const map: Record<string, string> = {
    '初识': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    '暧昧': 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
    '热恋': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    '冲突': 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    '平淡': 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
    '修复': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  }
  return map[category] || 'bg-gray-100 text-gray-700'
})

const inputPlaceholder = computed(() => {
  if (currentMode.value === 'emotion') return '请输入你识别出的情绪（如：委屈、期待、失落）...'
  return '请输入你的回应...'
})

function getEmotionClass(spectrum: string): string {
  const map: Record<string, string> = {
    '喜': 'bg-emotion-joy text-green-700',
    '怒': 'bg-emotion-anger text-red-700',
    '哀': 'bg-emotion-sadness text-blue-700',
    '惧': 'bg-emotion-fear text-purple-700',
    '爱': 'bg-emotion-love text-pink-700',
    '惊': 'bg-emotion-surprise text-orange-700',
    '羞': 'bg-emotion-shame text-indigo-700',
  }
  return map[spectrum] || 'bg-gray-100 text-gray-700'
}

async function startTraining(modeId: string) {
  currentMode.value = modeId
  currentStep.value = 1
  userResponse.value = ''
  showResult.value = false
  comparisonResult.value = null
  await store.fetchRandomSample()
}

function resetTraining() {
  currentMode.value = null
  userResponse.value = ''
  showResult.value = false
  comparisonResult.value = null
  store.clearComparison()
}

async function submitResponse() {
  if (!userResponse.value.trim()) return
  submitting.value = true
  try {
    const result = await store.submitComparison(userResponse.value, selectedResponseType.value)
    comparisonResult.value = result
    showResult.value = true
  } catch (e) {
    toast.error('提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

async function nextStep() {
  if (currentStep.value < totalSteps) {
    currentStep.value++
    userResponse.value = ''
    showResult.value = false
    comparisonResult.value = null
    await store.fetchRandomSample()
  } else {
    toast.success(`太棒了！完成了 ${totalSteps} 道训练题！`)
    resetTraining()
  }
}
</script>
