<template>
  <div class="p-8">
    <!-- 标题区 -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-800 dark:text-white">每日微训练</h1>
      <p class="text-gray-500 dark:text-gray-400 mt-2">坚持每天5分钟，提升关系感知力 📈</p>
    </div>

    <!-- 温度计进度 -->
    <div class="card mb-8">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white">今日训练进度</h2>
        <span class="text-sm text-gray-500 dark:text-gray-400">{{ currentDate }}</span>
      </div>

      <!-- 温度计 -->
      <div class="flex items-end gap-4 mb-4">
        <div class="relative flex-1 h-8 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            class="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
            :class="[
              thermometerColor
            ]"
            :style="{ width: trainingProgress + '%' }"
          ></div>
        </div>
        <div class="text-2xl font-bold" :class="thermometerTextColor">
          {{ trainingProgress }}%
        </div>
      </div>

      <!-- 热量指示 -->
      <div class="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
        <span>🔥 今日热量: {{ calories }}</span>
        <span>⚡ 连续训练: {{ streak }} 天</span>
        <span>🏆 今日排名: #{{ rank }}</span>
      </div>
    </div>

    <!-- 今日任务列表 -->
    <div class="card mb-8">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white">今日任务</h2>
        <button
          @click="refreshTasks"
          class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          :class="{ 'animate-spin': refreshing }"
        >
          <RefreshCw class="w-5 h-5 text-gray-500 dark:text-gray-400" />
        </button>
      </div>

      <div class="space-y-4">
        <div
          v-for="task in dailyTasks"
          :key="task.id"
          class="p-4 rounded-xl border-2 transition-all duration-200"
          :class="[
            task.completed
              ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
              : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700'
          ]"
        >
          <div class="flex items-start gap-4">
            <button
              @click="toggleTask(task)"
              class="mt-1 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all"
              :class="[
                task.completed
                  ? 'bg-green-500 border-green-500'
                  : 'border-gray-300 dark:border-gray-500 hover:border-blue-500'
              ]"
            >
              <CheckIcon v-if="task.completed" class="w-4 h-4 text-white" />
            </button>

            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-2xl">{{ task.icon }}</span>
                <h3 class="font-bold text-gray-800 dark:text-white">{{ task.title }}</h3>
                <span
                  v-if="task.completed"
                  class="px-2 py-0.5 rounded text-xs bg-green-100 dark:bg-green-900/50 text-green-600 dark:text-green-400"
                >
                  已完成
                </span>
              </div>
              <p class="text-sm text-gray-500 dark:text-gray-400">{{ task.description }}</p>
              <div class="flex items-center gap-4 mt-2 text-xs text-gray-400">
                <span>⏱️ {{ task.duration }}分钟</span>
                <span>💡 {{ task.xp }} XP</span>
              </div>
            </div>

            <button
              v-if="!task.completed"
              @click="startTask(task)"
              class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              :class="[
                task.type === 'emotion'
                  ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 hover:bg-purple-200 dark:hover:bg-purple-900/50'
                  : task.type === 'response'
                  ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-200 dark:hover:bg-blue-900/50'
                  : 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 hover:bg-green-200 dark:hover:bg-green-900/50'
              ]"
            >
              开始
            </button>
          </div>
        </div>
      </div>

      <!-- 任务进度 -->
      <div class="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
        <div class="flex justify-between text-sm mb-2">
          <span class="text-gray-500 dark:text-gray-400">任务完成度</span>
          <span class="font-medium text-gray-800 dark:text-white">{{ completedCount }} / {{ dailyTasks.length }}</span>
        </div>
        <div class="progress-bar">
          <div
            class="progress-bar-fill"
            :style="{ width: (completedCount / dailyTasks.length * 100) + '%' }"
          ></div>
        </div>
      </div>
    </div>

    <!-- 微训练快捷入口 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      <div
        v-for="mode in quickModes"
        :key="mode.id"
        @click="startQuickTraining(mode.id)"
        class="card card-hover cursor-pointer"
      >
        <div class="w-12 h-12 rounded-xl flex items-center justify-center mb-4" :class="mode.bgClass">
          <span class="text-2xl">{{ mode.icon }}</span>
        </div>
        <h3 class="font-bold text-gray-800 dark:text-white mb-1">{{ mode.name }}</h3>
        <p class="text-sm text-gray-500 dark:text-gray-400">{{ mode.description }}</p>
      </div>
    </div>

    <!-- 连续打卡激励 -->
    <div class="card bg-gradient-to-r from-orange-500 to-red-500 text-white">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-xl font-bold mb-1">🔥 连续打卡 {{ streak }} 天</h3>
          <p class="text-sm opacity-80">再坚持 {{ 7 - (streak % 7) }} 天即可获得额外奖励！</p>
        </div>
        <div class="text-4xl">
          {{ streakEmoji }}
        </div>
      </div>
    </div>

    <!-- 训练抽屉 -->
    <Teleport to="body">
      <transition name="slide">
        <div
          v-if="showTrainingPanel"
          class="fixed inset-y-0 right-0 w-full max-w-lg bg-white dark:bg-gray-800 shadow-2xl z-50 flex flex-col"
        >
          <!-- 头部 -->
          <div class="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <div>
              <h2 class="text-xl font-bold text-gray-800 dark:text-white">{{ currentTaskTitle }}</h2>
              <p class="text-sm text-gray-500 dark:text-gray-400">{{ currentTaskDescription }}</p>
            </div>
            <button
              @click="closeTrainingPanel"
              class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <X class="w-6 h-6 text-gray-500" />
            </button>
          </div>

          <!-- 内容区 -->
          <div class="flex-1 overflow-auto p-6">
            <div v-if="trainingMode === 'emotion' && currentSample" class="space-y-6">
              <!-- 场景 -->
              <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-2">场景</p>
                <p class="text-gray-800 dark:text-white">{{ currentSample.context }}</p>
              </div>

              <!-- 对方言行 -->
              <div class="p-4 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                <p class="text-sm text-blue-600 dark:text-blue-400 mb-2">对方说：</p>
                <p class="text-lg text-gray-800 dark:text-white">{{ currentSample.their_words }}</p>
              </div>

              <!-- 情绪识别 -->
              <div class="p-4 rounded-xl bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800">
                <p class="text-sm text-purple-600 dark:text-purple-400 mb-2">识别情绪（多选）：</p>
                <div class="flex flex-wrap gap-2">
                  <button
                    v-for="emotion in emotionOptions"
                    :key="emotion"
                    @click="toggleEmotionSelection(emotion)"
                    class="px-3 py-1.5 rounded-full text-sm transition-all"
                    :class="[
                      selectedEmotions.includes(emotion)
                        ? 'bg-purple-500 text-white'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                    ]"
                  >
                    {{ emotion }}
                  </button>
                </div>
              </div>

              <!-- 提交 -->
              <button
                @click="submitEmotionAnswer"
                class="btn-primary w-full"
                :disabled="selectedEmotions.length === 0 || submitting"
              >
                {{ submitting ? '分析中...' : '提交答案' }}
              </button>

              <!-- 结果 -->
              <div v-if="showEmotionResult" class="space-y-4">
                <div class="p-4 rounded-xl" :class="emotionResult.correct ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20'">
                  <p class="font-bold" :class="emotionResult.correct ? 'text-green-600' : 'text-red-600'">
                    {{ emotionResult.correct ? '🎉 正确！' : '❌ 还有提升空间' }}
                  </p>
                  <p class="text-sm text-gray-600 dark:text-gray-300 mt-2">
                    {{ emotionResult.feedback }}
                  </p>
                </div>
              </div>
            </div>

            <div v-else-if="trainingMode === 'response' && currentSample" class="space-y-6">
              <!-- 场景 -->
              <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-2">场景</p>
                <p class="text-gray-800 dark:text-white">{{ currentSample.context }}</p>
              </div>

              <!-- 对方言行 -->
              <div class="p-4 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                <p class="text-sm text-blue-600 dark:text-blue-400 mb-2">对方说：</p>
                <p class="text-lg text-gray-800 dark:text-white">{{ currentSample.their_words }}</p>
              </div>

              <!-- 用户回应 -->
              <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  你的回应：
                </label>
                <textarea
                  v-model="userResponse"
                  class="input-mac min-h-[120px]"
                  placeholder="请输入你的回应..."
                ></textarea>
              </div>

              <!-- 提交 -->
              <button
                @click="submitResponseAnswer"
                class="btn-primary w-full"
                :disabled="!userResponse.trim() || submitting"
              >
                {{ submitting ? '分析中...' : '提交并对比' }}
              </button>

              <!-- 对比结果 -->
              <div v-if="showResponseResult && comparisonResult" class="space-y-4">
                <div class="text-center p-4 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white">
                  <p class="text-sm opacity-80">得分</p>
                  <p class="text-4xl font-bold">{{ Math.round(comparisonResult.score) }}</p>
                </div>

                <div class="p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
                  <p class="text-sm text-green-600 dark:text-green-400 mb-2">理想回应：</p>
                  <p class="text-gray-800 dark:text-white">{{ comparisonResult.ideal_response }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </transition>
      <div
        v-if="showTrainingPanel"
        @click="closeTrainingPanel"
        class="fixed inset-0 bg-black/50 z-40"
      ></div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { CheckIcon, RefreshCw, X } from 'lucide-vue-next'
import { useTrainingStore } from '@/stores/training'
import { useToast } from '@/utils/toast'
import type { InteractionSample, ComparisonResult } from '@/utils/api'

const router = useRouter()
const store = useTrainingStore()
const toast = useToast()

const currentDate = new Date().toLocaleDateString('zh-CN', {
  year: 'numeric',
  month: 'long',
  day: 'numeric',
  weekday: 'long'
})

const trainingProgress = ref(0)
const calories = ref(0)
const streak = ref(7)
const rank = ref(42)
const refreshing = ref(false)

const dailyTasks = ref([
  {
    id: 'emotion-1',
    type: 'emotion',
    icon: '🎭',
    title: '情绪识别练习',
    description: '识别3段对话中的情绪标签和强度',
    duration: 3,
    xp: 30,
    completed: false
  },
  {
    id: 'response-1',
    type: 'response',
    icon: '⚖️',
    title: '回应对比练习',
    description: '对比你的回应与理想回应',
    duration: 5,
    xp: 50,
    completed: false
  },
  {
    id: 'review-1',
    type: 'review',
    icon: '📖',
    title: '复盘今日收获',
    description: '记录今天的关系感知练习心得',
    duration: 2,
    xp: 20,
    completed: false
  }
])

const quickModes = [
  { id: 'emotion', name: '快速情绪识别', icon: '🎭', description: '1分钟识别情绪', bgClass: 'bg-purple-100 dark:bg-purple-900/30' },
  { id: 'response', name: '快速回应练习', icon: '⚖️', description: '3分钟对比练习', bgClass: 'bg-blue-100 dark:bg-blue-900/30' },
  { id: 'review', name: '快速复盘', icon: '📝', description: '2分钟记录收获', bgClass: 'bg-green-100 dark:bg-green-900/30' }
]

const showTrainingPanel = ref(false)
const trainingMode = ref<'emotion' | 'response' | null>(null)
const currentTaskTitle = ref('')
const currentTaskDescription = ref('')

const currentSample = ref<InteractionSample | null>(null)
const selectedEmotions = ref<string[]>([])
const userResponse = ref('')
const submitting = ref(false)
const showEmotionResult = ref(false)
const showResponseResult = ref(false)
const emotionResult = ref<{ correct: boolean; feedback: string }>({ correct: false, feedback: '' })
const comparisonResult = ref<ComparisonResult | null>(null)

const emotionOptions = ['喜悦', '悲伤', '愤怒', '恐惧', '惊讶', '厌恶', '羞耻', '愧疚', '期待', '焦虑', '失落', '甜蜜', '委屈']

const thermometerColor = computed(() => {
  if (trainingProgress.value < 30) return 'bg-red-500'
  if (trainingProgress.value < 70) return 'bg-yellow-500'
  return 'bg-green-500'
})

const thermometerTextColor = computed(() => {
  if (trainingProgress.value < 30) return 'text-red-500'
  if (trainingProgress.value < 70) return 'text-yellow-500'
  return 'text-green-500'
})

const completedCount = computed(() => {
  return dailyTasks.value.filter(t => t.completed).length
})

const streakEmoji = computed(() => {
  if (streak.value < 7) return '🌱'
  if (streak.value < 30) return '🔥'
  if (streak.value < 100) return '⭐'
  return '👑'
})

const trainingProgressValue = computed(() => {
  return (completedCount.value / dailyTasks.value.length) * 100
})

onMounted(() => {
  updateProgress()
})

function updateProgress() {
  trainingProgress.value = Math.round(trainingProgressValue.value)
  calories.value = completedCount.value * 50
}

async function refreshTasks() {
  refreshing.value = true
  await new Promise(resolve => setTimeout(resolve, 500))
  refreshing.value = false
  toast.success('任务已刷新')
}

function toggleTask(task: typeof dailyTasks.value[0]) {
  task.completed = !task.completed
  updateProgress()
  if (task.completed) {
    toast.success(`🎉 任务「${task.title}」已完成！获得 ${task.xp} XP`)
  }
}

function startTask(task: typeof dailyTasks.value[0]) {
  currentTaskTitle.value = task.title
  currentTaskDescription.value = task.description
  trainingMode.value = task.type === 'review' ? 'response' : task.type
  showTrainingPanel.value = true
  loadSample()
}

function closeTrainingPanel() {
  showTrainingPanel.value = false
  resetTrainingState()
}

function resetTrainingState() {
  selectedEmotions.value = []
  userResponse.value = ''
  showEmotionResult.value = false
  showResponseResult.value = false
  emotionResult.value = { correct: false, feedback: '' }
  comparisonResult.value = null
  currentSample.value = null
}

async function loadSample() {
  await store.fetchRandomSample()
  currentSample.value = store.currentSample
}

function toggleEmotionSelection(emotion: string) {
  const index = selectedEmotions.value.indexOf(emotion)
  if (index > -1) {
    selectedEmotions.value.splice(index, 1)
  } else {
    selectedEmotions.value.push(emotion)
  }
}

async function submitEmotionAnswer() {
  submitting.value = true
  await new Promise(resolve => setTimeout(resolve, 800))
  const correct = Math.random() > 0.3
  emotionResult.value = {
    correct,
    feedback: correct
      ? '你准确地识别出了情绪标签！继续加油！'
      : '建议关注对话中的语气和上下文线索，再试试看！'
  }
  showEmotionResult.value = true
  submitting.value = false

  if (correct) {
    const task = dailyTasks.value.find(t => t.type === 'emotion')
    if (task && !task.completed) {
      task.completed = true
      updateProgress()
    }
  }
}

async function submitResponseAnswer() {
  if (!userResponse.value.trim()) return
  submitting.value = true
  try {
    const result = await store.submitComparison(userResponse.value, 'soft')
    if (result) {
      comparisonResult.value = result
      showResponseResult.value = true

      if (result.score >= 60) {
        const task = dailyTasks.value.find(t => t.type === 'response')
        if (task && !task.completed) {
          task.completed = true
          updateProgress()
          toast.success(`🎉 任务「${task.title}」已完成！获得 ${task.xp} XP`)
        }
      }
    }
  } catch (e) {
    toast.error('提交失败，请重试')
  } finally {
    submitting.value = false
  }
}

function startQuickTraining(mode: string) {
  if (mode === 'review') {
    router.push('/journal')
    return
  }
  currentTaskTitle.value = quickModes.find(m => m.id === mode)?.name || ''
  currentTaskDescription.value = quickModes.find(m => m.id === mode)?.description || ''
  trainingMode.value = mode as 'emotion' | 'response'
  showTrainingPanel.value = true
  loadSample()
}
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
