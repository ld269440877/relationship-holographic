<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center p-8">
    <div class="w-full max-w-2xl">
      <!-- 进度指示器 -->
      <div class="flex items-center justify-center mb-12">
        <div
          v-for="step in 5"
          :key="step"
          class="flex items-center"
        >
          <div
            class="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300"
            :class="[
              currentStep >= step
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-400'
            ]"
          >
            <CheckIcon v-if="currentStep > step" class="w-5 h-5" />
            <span v-else>{{ step }}</span>
          </div>
          <div
            v-if="step < 5"
            class="w-16 h-1 mx-2 rounded transition-all duration-300"
            :class="[
              currentStep > step
                ? 'bg-blue-500'
                : 'bg-gray-200 dark:bg-gray-700'
            ]"
          ></div>
        </div>
      </div>

      <!-- 欢迎步骤 -->
      <div v-if="currentStep === 1" class="animate-fadeIn">
        <div class="text-center mb-12">
          <div class="w-24 h-24 mx-auto mb-6 rounded-3xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-5xl shadow-lg">
            💑
          </div>
          <h1 class="text-4xl font-bold text-gray-800 dark:text-white mb-4">
            欢迎来到关系动力学全息
          </h1>
          <p class="text-lg text-gray-500 dark:text-gray-400 max-w-md mx-auto">
            通过科学的微训练，提升你的两性关系感知能力，成为更好的伴侣
          </p>
        </div>
        <div class="flex justify-center gap-4">
          <button @click="nextStep" class="btn-primary px-8 py-3 text-lg">
            开始探索 →
          </button>
        </div>
      </div>

      <!-- 依恋风格测试 -->
      <div v-else-if="currentStep === 2" class="animate-fadeIn">
        <div class="text-center mb-8">
          <h2 class="text-3xl font-bold text-gray-800 dark:text-white mb-2">
            探索你的依恋风格
          </h2>
          <p class="text-gray-500 dark:text-gray-400">
            了解自己在亲密关系中的行为模式
          </p>
        </div>

        <div class="space-y-4 mb-8">
          <div
            v-for="style in attachmentStyles"
            :key="style.id"
            @click="selectedAttachment = style.id"
            class="p-6 rounded-2xl border-2 cursor-pointer transition-all duration-200"
            :class="[
              selectedAttachment === style.id
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700'
            ]"
          >
            <div class="flex items-start gap-4">
              <div class="text-3xl">{{ style.icon }}</div>
              <div class="flex-1">
                <h3 class="text-lg font-bold text-gray-800 dark:text-white mb-1">
                  {{ style.name }}
                </h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  {{ style.description }}
                </p>
              </div>
              <div
                class="w-6 h-6 rounded-full border-2 flex items-center justify-center"
                :class="[
                  selectedAttachment === style.id
                    ? 'border-blue-500 bg-blue-500'
                    : 'border-gray-300 dark:border-gray-600'
                ]"
              >
                <CheckIcon v-if="selectedAttachment === style.id" class="w-4 h-4 text-white" />
              </div>
            </div>
          </div>
        </div>

        <div class="flex justify-between">
          <button @click="prevStep" class="btn-secondary px-6 py-2">
            ← 上一步
          </button>
          <button
            @click="nextStep"
            class="btn-primary px-6 py-2"
            :disabled="!selectedAttachment"
          >
            继续 →
          </button>
        </div>
      </div>

      <!-- 情绪词汇测试 -->
      <div v-else-if="currentStep === 3" class="animate-fadeIn">
        <div class="text-center mb-8">
          <h2 class="text-3xl font-bold text-gray-800 dark:text-white mb-2">
            你的情绪词汇量
          </h2>
          <p class="text-gray-500 dark:text-gray-400">
            选出你熟悉的情绪词汇，越多代表情绪感知能力越细腻
          </p>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-3 gap-3 mb-8">
          <button
            v-for="emotion in emotionWords"
            :key="emotion.word"
            @click="toggleEmotion(emotion)"
            class="p-4 rounded-xl border-2 text-left transition-all duration-200"
            :class="[
              selectedEmotions.includes(emotion.word)
                ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700'
            ]"
          >
            <div class="flex items-center gap-2">
              <span class="text-2xl">{{ emotion.icon }}</span>
              <span class="text-gray-700 dark:text-gray-200 font-medium">{{ emotion.word }}</span>
            </div>
          </button>
        </div>

        <div class="bg-gray-100 dark:bg-gray-800 rounded-xl p-4 mb-6">
          <div class="flex justify-between items-center">
            <span class="text-gray-600 dark:text-gray-300">已选择 {{ selectedEmotions.length }} / {{ emotionWords.length }}</span>
            <span class="text-blue-500 font-bold">{{ emotionLevel }}</span>
          </div>
          <div class="progress-bar mt-2">
            <div
              class="progress-bar-fill"
              :style="{ width: safeEmotionProgressWidth }"
            ></div>
          </div>
        </div>

        <div class="flex justify-between">
          <button @click="prevStep" class="btn-secondary px-6 py-2">
            ← 上一步
          </button>
          <button
            @click="nextStep"
            class="btn-primary px-6 py-2"
            :disabled="selectedEmotions.length < 3"
          >
            继续 →
          </button>
        </div>
      </div>

      <!-- 关系目标设定 -->
      <div v-else-if="currentStep === 4" class="animate-fadeIn">
        <div class="text-center mb-8">
          <h2 class="text-3xl font-bold text-gray-800 dark:text-white mb-2">
            设定你的成长目标
          </h2>
          <p class="text-gray-500 dark:text-gray-400">
            明确的目标让训练更有方向
          </p>
        </div>

        <div class="space-y-4 mb-8">
          <div
            v-for="goal in goals"
            :key="goal.id"
            @click="selectedGoals = [goal.id]"
            class="p-6 rounded-2xl border-2 cursor-pointer transition-all duration-200"
            :class="[
              selectedGoals.includes(goal.id)
                ? 'border-purple-500 bg-purple-50 dark:bg-purple-900/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-purple-300 dark:hover:border-purple-700'
            ]"
          >
            <div class="flex items-start gap-4">
              <div class="text-3xl">{{ goal.icon }}</div>
              <div class="flex-1">
                <h3 class="text-lg font-bold text-gray-800 dark:text-white mb-1">
                  {{ goal.title }}
                </h3>
                <p class="text-sm text-gray-500 dark:text-gray-400">
                  {{ goal.description }}
                </p>
              </div>
              <div
                class="w-6 h-6 rounded-full border-2 flex items-center justify-center"
                :class="[
                  selectedGoals.includes(goal.id)
                    ? 'border-purple-500 bg-purple-500'
                    : 'border-gray-300 dark:border-gray-600'
                ]"
              >
                <CheckIcon v-if="selectedGoals.includes(goal.id)" class="w-4 h-4 text-white" />
              </div>
            </div>
          </div>
        </div>

        <div class="flex justify-between">
          <button @click="prevStep" class="btn-secondary px-6 py-2">
            ← 上一步
          </button>
          <button
            @click="nextStep"
            class="btn-primary px-6 py-2"
            :disabled="selectedGoals.length === 0"
          >
            继续 →
          </button>
        </div>
      </div>

      <!-- 完成步骤 -->
      <div v-else-if="currentStep === 5" class="animate-fadeIn">
        <div class="text-center mb-12">
          <div class="w-32 h-32 mx-auto mb-6 rounded-full bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center text-white text-6xl shadow-lg animate-pulse">
            🎉
          </div>
          <h1 class="text-4xl font-bold text-gray-800 dark:text-white mb-4">
            准备就绪！
          </h1>
          <p class="text-lg text-gray-500 dark:text-gray-400 max-w-md mx-auto">
            让我们开始你的关系成长之旅吧
          </p>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-lg mb-8">
          <h3 class="text-lg font-bold text-gray-800 dark:text-white mb-4">你的初始档案</h3>
          <div class="space-y-3">
            <div class="flex justify-between">
              <span class="text-gray-500 dark:text-gray-400">依恋风格</span>
              <span class="font-medium text-gray-800 dark:text-white">
                {{ attachmentStyles.find(s => s.id === selectedAttachment)?.name }}
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500 dark:text-gray-400">情绪词汇量</span>
              <span class="font-medium text-gray-800 dark:text-white">
                {{ selectedEmotions.length }} 个 ({{ emotionLevel }})
              </span>
            </div>
            <div class="flex justify-between">
              <span class="text-gray-500 dark:text-gray-400">成长目标</span>
              <span class="font-medium text-gray-800 dark:text-white">
                {{ goals.find(g => g.id === selectedGoals[0])?.title }}
              </span>
            </div>
          </div>
        </div>

        <div class="flex justify-center gap-4">
          <button @click="prevStep" class="btn-secondary px-6 py-2">
            ← 上一步
          </button>
          <button @click="completeOnboarding" class="btn-primary px-8 py-2 text-lg">
            开始训练 🚀
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { CheckIcon } from 'lucide-vue-next'
import { useProfileStore } from '@/stores/profile'
import { useToast } from '@/utils/toast'
import { markOnboardingCompleted } from '@/utils/onboarding'
import { safeBarWidth } from '@/utils/format'

const router = useRouter()
const profileStore = useProfileStore()
const toast = useToast()

const currentStep = ref(1)

const attachmentStyles = [
  {
    id: 'secure',
    name: '安全型',
    icon: '🔐',
    description: '在亲密关系中感到安心，能够开放表达情感，建立健康稳定的依恋关系'
  },
  {
    id: 'anxious',
    name: '焦虑型',
    icon: '😰',
    description: '渴望亲密但容易担心被抛弃，倾向于过度依赖或过度解读伴侣行为'
  },
  {
    id: 'avoidant',
    name: '回避型',
    icon: '🚪',
    description: '重视独立空间，倾向于在情感上保持距离，对亲密关系有所保留'
  },
  {
    id: 'fearful',
    name: '恐惧型',
    icon: '😨',
    description: '既渴望亲密又害怕被伤害，在亲密和独立之间挣扎'
  }
]

const emotionWords = [
  { word: '喜悦', icon: '😊' },
  { word: '悲伤', icon: '😢' },
  { word: '愤怒', icon: '😠' },
  { word: '恐惧', icon: '😨' },
  { word: '惊讶', icon: '😲' },
  { word: '厌恶', icon: '😒' },
  { word: '羞耻', icon: '😳' },
  { word: '愧疚', icon: '😔' },
  { word: '期待', icon: '🤩' },
  { word: '焦虑', icon: '😟' },
  { word: '失落', icon: '😞' },
  { word: '甜蜜', icon: '🥰' },
  { word: '委屈', icon: '🥺' },
  { word: '无奈', icon: '😮‍💨' },
  { word: '释然', icon: '😌' }
]

const goals = [
  {
    id: 'emotion',
    title: '提升情绪感知',
    icon: '🎯',
    description: '更准确地识别和理解自己及伴侣的情绪状态'
  },
  {
    id: 'communication',
    title: '改善沟通方式',
    icon: '💬',
    description: '学会更有效地表达需求和倾听伴侣的心声'
  },
  {
    id: 'boundary',
    title: '建立健康边界',
    icon: '🛡️',
    description: '在亲密和独立之间找到平衡，建立相互尊重的关系'
  },
  {
    id: 'conflict',
    title: '提升冲突处理',
    icon: '🤝',
    description: '学会建设性地处理分歧，将冲突转化为成长机会'
  }
]

const selectedAttachment = ref<string | null>(null)
const selectedEmotions = ref<string[]>([])
const selectedGoals = ref<string[]>([])

const emotionLevel = computed(() => {
  const count = selectedEmotions.value.length
  if (count < 5) return '基础'
  if (count < 10) return '良好'
  return '丰富'
})
const safeEmotionProgressWidth = computed(() => safeBarWidth(emotionWords.length ? (selectedEmotions.value.length / emotionWords.length) * 100 : 0))

function toggleEmotion(emotion: { word: string; icon: string }) {
  const index = selectedEmotions.value.indexOf(emotion.word)
  if (index > -1) {
    selectedEmotions.value.splice(index, 1)
  } else {
    selectedEmotions.value.push(emotion.word)
  }
}

function nextStep() {
  if (currentStep.value < 5) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

async function completeOnboarding() {
  markOnboardingCompleted()
  try {
    await profileStore.updateProfile({
      attachment_style: selectedAttachment.value ?? undefined,
      emotion_vocab_size: selectedEmotions.value.length,
      perception_baseline: selectedEmotions.value.length * 5
    })
    toast.success('欢迎开始你的成长之旅！')
  } catch (e) {
    toast.error('画像保存失败，已先进入本地训练模式')
  }
  router.push('/')
}
</script>

<style scoped>
.animate-fadeIn {
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
