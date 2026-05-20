<template>
  <div class="h-full flex flex-col">
    <!-- 头部 -->
    <div class="p-6 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-800 dark:text-white">AI 训练伴侣</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">与不同依恋类型的AI对话，练习回应策略</p>
        </div>
        <div class="flex items-center gap-4">
          <!-- 评分显示 -->
          <div class="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white">
            <span class="text-sm opacity-80">本次对话评分</span>
            <span class="text-2xl font-bold">{{ currentScore }}</span>
          </div>
          <!-- 设置按钮 -->
          <button
            @click="showSettings = !showSettings"
            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <Settings class="w-6 h-6 text-gray-500 dark:text-gray-400" />
          </button>
        </div>
      </div>
    </div>

    <!-- AI角色选择 -->
    <div v-if="!activeChat && !showSettings" class="p-6">
      <h2 class="text-lg font-bold text-gray-800 dark:text-white mb-4">选择训练场景</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="scenario in scenarios"
          :key="scenario.id"
          @click="startChat(scenario)"
          class="p-6 rounded-2xl border-2 border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-500 cursor-pointer transition-all hover:shadow-lg"
        >
          <div class="flex items-center gap-3 mb-4">
            <div class="w-12 h-12 rounded-full flex items-center justify-center text-2xl" :class="scenario.avatarBg">
              {{ scenario.avatar }}
            </div>
            <div>
              <h3 class="font-bold text-gray-800 dark:text-white">{{ scenario.name }}</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ scenario.style }}</p>
            </div>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-300 mb-4">{{ scenario.description }}</p>
          <div class="flex items-center gap-2 text-xs text-gray-400">
            <span>💬 {{ scenario.messageCount }}+ 对话</span>
            <span>📊 {{ scenario.difficulty }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 设置面板 -->
    <div v-if="showSettings" class="p-6">
      <div class="max-w-2xl mx-auto">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-gray-800 dark:text-white">对话设置</h2>
          <button @click="showSettings = false" class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
            <ArrowLeft class="w-6 h-6 text-gray-500" />
          </button>
        </div>

        <div class="card space-y-6">
          <!-- 难度 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">对话难度</label>
            <div class="flex gap-2">
              <button
                v-for="level in difficultyLevels"
                :key="level.value"
                @click="chatSettings.difficulty = level.value"
                class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                :class="[
                  chatSettings.difficulty === level.value
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                ]"
              >
                {{ level.label }}
              </button>
            </div>
          </div>

          <!-- 回应风格 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">期望回应风格</label>
            <div class="flex gap-2">
              <button
                v-for="style in responseStyles"
                :key="style.value"
                @click="chatSettings.responseStyle = style.value"
                class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                :class="[
                  chatSettings.responseStyle === style.value
                    ? 'bg-purple-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                ]"
              >
                {{ style.icon }} {{ style.label }}
              </button>
            </div>
          </div>

          <!-- 话题偏好 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">话题偏好</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="topic in topicOptions"
                :key="topic"
                @click="toggleTopic(topic)"
                class="px-3 py-1.5 rounded-full text-sm transition-colors"
                :class="[
                  chatSettings.topics.includes(topic)
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                ]"
              >
                {{ topic }}
              </button>
            </div>
          </div>

          <button @click="applySettings" class="btn-primary w-full">
            开始对话
          </button>
        </div>
      </div>
    </div>

    <!-- 聊天区域 -->
    <div v-if="activeChat" class="flex-1 flex flex-col overflow-hidden">
      <!-- 聊天头部 -->
      <div class="p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex items-center gap-4">
        <button @click="endChat" class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
          <ArrowLeft class="w-5 h-5 text-gray-500" />
        </button>
        <div class="w-10 h-10 rounded-full flex items-center justify-center text-xl" :class="activeChat.avatarBg">
          {{ activeChat.avatar }}
        </div>
        <div class="flex-1">
          <h3 class="font-bold text-gray-800 dark:text-white">{{ activeChat.name }}</h3>
          <p class="text-xs text-gray-500 dark:text-gray-400">{{ activeChat.style }}</p>
        </div>
        <div class="flex items-center gap-2">
          <span
            class="px-3 py-1 rounded-full text-xs font-medium"
            :class="[
              isTyping
                ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
            ]"
          >
            {{ isTyping ? '对方正在输入...' : '在线' }}
          </span>
        </div>
      </div>

      <!-- 消息列表 -->
      <div ref="messageContainer" class="flex-1 overflow-auto p-6 space-y-4">
        <div
          v-for="(message, index) in messages"
          :key="index"
          class="flex animate-fadeIn"
          :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <!-- AI消息 -->
          <div v-if="message.role === 'ai'" class="flex items-start gap-3 max-w-[80%]">
            <div class="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center" :class="activeChat.avatarBg">
              {{ activeChat.avatar }}
            </div>
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-sm font-medium text-gray-600 dark:text-gray-300">{{ activeChat.name }}</span>
                <span class="text-xs text-gray-400">{{ message.time }}</span>
              </div>
              <div class="p-4 rounded-2xl rounded-tl-none bg-white dark:bg-gray-700 shadow-sm">
                <p class="text-gray-800 dark:text-gray-100 whitespace-pre-wrap">{{ message.content }}</p>
              </div>
              <!-- 消息评分 -->
              <div v-if="message.score" class="flex items-center gap-2 mt-2">
                <span class="text-xs text-gray-500 dark:text-gray-400">本次回应评分</span>
                <div
                  class="px-2 py-0.5 rounded text-xs font-bold"
                  :class="[
                    message.score >= 80
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                      : message.score >= 60
                      ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                      : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                  ]"
                >
                  {{ message.score }}
                </div>
              </div>
            </div>
          </div>

          <!-- 用户消息 -->
          <div v-else class="flex items-start gap-3 max-w-[80%] justify-end">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1 justify-end">
                <span class="text-xs text-gray-400">{{ message.time }}</span>
                <span class="text-sm font-medium text-gray-600 dark:text-gray-300">你</span>
              </div>
              <div class="p-4 rounded-2xl rounded-tr-none bg-blue-500 text-white shadow-sm">
                <p class="whitespace-pre-wrap">{{ message.content }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 加载指示 -->
        <div v-if="isTyping" class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center" :class="activeChat.avatarBg">
            {{ activeChat.avatar }}
          </div>
          <div class="p-4 rounded-2xl rounded-tl-none bg-white dark:bg-gray-700 shadow-sm">
            <div class="flex items-center gap-1">
              <div class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style="animation-delay: 0ms"></div>
              <div class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style="animation-delay: 150ms"></div>
              <div class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style="animation-delay: 300ms"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 建议回复 -->
      <div v-if="suggestedReplies.length > 0" class="px-6 pb-2">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs text-gray-500 dark:text-gray-400">建议回复</span>
        </div>
        <div class="flex gap-2 overflow-x-auto pb-2">
          <button
            v-for="(reply, index) in suggestedReplies"
            :key="index"
            @click="useSuggestedReply(reply)"
            class="flex-shrink-0 px-4 py-2 rounded-full bg-gray-100 dark:bg-gray-700 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            {{ reply }}
          </button>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="p-6 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div class="flex items-end gap-4">
          <div class="flex-1">
            <textarea
              v-model="inputMessage"
              @keydown.enter.exact.prevent="sendMessage"
              class="input-mac min-h-[60px] max-h-[120px] resize-none"
              placeholder="输入你的回应..."
            ></textarea>
          </div>
          <button
            @click="sendMessage"
            :disabled="!inputMessage.trim() || isTyping"
            class="p-4 rounded-xl bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send class="w-5 h-5" />
          </button>
        </div>
        <div class="flex items-center justify-between mt-3 text-xs text-gray-400">
          <span>按 Enter 发送，Shift + Enter 换行</span>
          <span>对话轮次: {{ messageCount }}</span>
        </div>
      </div>
    </div>

    <!-- 评分统计弹窗 -->
    <Teleport to="body">
      <transition name="fade">
        <div
          v-if="showScoreModal"
          class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          @click.self="showScoreModal = false"
        >
          <div class="bg-white dark:bg-gray-800 rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl text-center">
            <div class="text-6xl mb-4">{{ scoreEmoji }}</div>
            <h2 class="text-2xl font-bold text-gray-800 dark:text-white mb-2">对话结束</h2>
            <p class="text-gray-500 dark:text-gray-400 mb-6">你与 {{ activeChat?.name }} 的训练对话已完成</p>

            <div class="space-y-4 mb-8">
              <div class="flex justify-between items-center p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
                <span class="text-gray-600 dark:text-gray-300">总体评分</span>
                <span class="text-3xl font-bold text-blue-500">{{ finalScore }}</span>
              </div>
              <div class="flex justify-between items-center p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
                <span class="text-gray-600 dark:text-gray-300">对话轮次</span>
                <span class="text-xl font-bold text-gray-800 dark:text-white">{{ messageCount }}</span>
              </div>
              <div class="flex justify-between items-center p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
                <span class="text-gray-600 dark:text-gray-300">用时</span>
                <span class="text-xl font-bold text-gray-800 dark:text-white">{{ conversationDuration }}</span>
              </div>
            </div>

            <div class="flex gap-4">
              <button @click="showScoreModal = false" class="flex-1 btn-secondary">
                查看详情
              </button>
              <button @click="restartChat" class="flex-1 btn-primary">
                再来一轮
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { Settings, ArrowLeft, Send } from 'lucide-vue-next'
import { useToast } from '@/utils/toast'

const toast = useToast()

const showSettings = ref(false)
const activeChat = ref<typeof scenarios.value[0] | null>(null)
const messages = ref<Array<{ role: 'user' | 'ai'; content: string; time: string; score?: number }>>([])
const inputMessage = ref('')
const isTyping = ref(false)
const messageContainer = ref<HTMLElement | null>(null)
const messageCount = ref(0)
const showScoreModal = ref(false)
const finalScore = ref(0)
const conversationStartTime = ref<Date | null>(null)

const chatSettings = ref({
  difficulty: 'medium',
  responseStyle: 'soft',
  topics: ['日常沟通', '情绪支持', '冲突处理']
})

const scenarios = ref([
  {
    id: 'anxious',
    name: '小焦虑',
    avatar: '😰',
    avatarBg: 'bg-orange-100 dark:bg-orange-900/30',
    style: '焦虑型依恋',
    description: '渴望亲密但容易担心被抛弃，倾向于过度依赖或过度解读伴侣行为',
    messageCount: 120,
    difficulty: '中等'
  },
  {
    id: 'avoidant',
    name: '小回避',
    avatar: '🚪',
    avatarBg: 'bg-blue-100 dark:bg-blue-900/30',
    style: '回避型依恋',
    description: '重视独立空间，倾向于在情感上保持距离，对亲密关系有所保留',
    messageCount: 95,
    difficulty: '较难'
  },
  {
    id: 'secure',
    name: '小安心',
    avatar: '😊',
    avatarBg: 'bg-green-100 dark:bg-green-900/30',
    style: '安全型依恋',
    description: '在亲密关系中感到安心，能够开放表达情感，建立健康稳定的依恋关系',
    messageCount: 200,
    difficulty: '入门'
  },
  {
    id: 'fearful',
    name: '小纠结',
    avatar: '😨',
    avatarBg: 'bg-purple-100 dark:bg-purple-900/30',
    style: '恐惧型依恋',
    description: '既渴望亲密又害怕被伤害，在亲密和独立之间挣扎',
    messageCount: 80,
    difficulty: '困难'
  }
])

const difficultyLevels = [
  { value: 'easy', label: '入门' },
  { value: 'medium', label: '中等' },
  { value: 'hard', label: '困难' }
]

const responseStyles = [
  { value: 'soft', icon: '🌊', label: '柔和' },
  { value: 'tension', icon: '⚡', label: '张力' },
  { value: 'humor', icon: '😄', label: '幽默' }
]

const topicOptions = ['日常沟通', '情绪支持', '冲突处理', '亲密关系', '个人空间', '未来规划']

const suggestedReplies = ref<string[]>([])

const currentScore = computed(() => {
  if (messages.value.length === 0) return 0
  const scoredMessages = messages.value.filter(m => m.score !== undefined)
  if (scoredMessages.length === 0) return 0
  return Math.round(scoredMessages.reduce((sum, m) => sum + (m.score || 0), 0) / scoredMessages.length)
})

const scoreEmoji = computed(() => {
  if (finalScore.value >= 80) return '🏆'
  if (finalScore.value >= 60) return '👍'
  if (finalScore.value >= 40) return '💪'
  return '📚'
})

const conversationDuration = computed(() => {
  if (!conversationStartTime.value) return '0分钟'
  const diff = Date.now() - conversationStartTime.value.getTime()
  const minutes = Math.floor(diff / 60000)
  return `${minutes}分钟`
})

onMounted(() => {
  conversationStartTime.value = new Date()
})

function toggleTopic(topic: string) {
  const index = chatSettings.value.topics.indexOf(topic)
  if (index > -1) {
    chatSettings.value.topics.splice(index, 1)
  } else {
    chatSettings.value.topics.push(topic)
  }
}

function applySettings() {
  showSettings.value = false
  toast.success('设置已保存，开始对话吧！')
}

function startChat(scenario: typeof scenarios.value[0]) {
  activeChat.value = scenario
  messageCount.value = 0
  messages.value = []
  conversationStartTime.value = new Date()

  const openingMessage = getOpeningMessage(scenario.id)
  addAiMessage(openingMessage)
  generateSuggestedReplies()
}

function getOpeningMessage(scenarioId: string): string {
  const openings: Record<string, string> = {
    anxious: '嗨...你在吗？我刚才给你发了好几条消息，你都没回我...你是不是不想理我了？',
    avoidant: '嗯，我今天比较忙，晚上再说吧。',
    secure: '嗨！今天过得怎么样？周末有什么计划吗？',
    fearful: '其实...我有点不知道该怎么跟你说。最近我们的关系让我有点困惑。'
  }
  return openings[scenarioId] || '你好，我们聊聊吧。'
}

function addAiMessage(content: string, score?: number) {
  messages.value.push({
    role: 'ai',
    content,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    score
  })
  messageCount.value++
}

function addUserMessage(content: string) {
  messages.value.push({
    role: 'user',
    content,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  })
}

async function sendMessage() {
  if (!inputMessage.value.trim() || isTyping.value) return

  const userMessage = inputMessage.value
  inputMessage.value = ''
  addUserMessage(userMessage)
  scrollToBottom()

  // 计算本次回应评分
  const score = calculateResponseScore(userMessage)

  isTyping.value = true
  suggestedReplies.value = []

  // 模拟AI回复延迟
  await new Promise(resolve => setTimeout(resolve, 1500))

  const aiResponse = generateAiResponse(userMessage)
  addAiMessage(aiResponse, score)
  isTyping.value = false
  generateSuggestedReplies()
  scrollToBottom()

  // 检查是否达到对话轮次上限
  if (messageCount.value >= 20) {
    showScoreModal.value = true
    finalScore.value = currentScore.value
  }
}

function calculateResponseScore(response: string): number {
  let score = 60 + Math.random() * 30

  // 检查是否有共情表达
  if (response.includes('理解') || response.includes('懂') || response.includes('感受')) {
    score += 10
  }

  // 检查是否有积极态度
  if (response.includes('支持') || response.includes('陪伴') || response.includes('相信')) {
    score += 10
  }

  // 检查是否过于简短
  if (response.length < 10) {
    score -= 20
  }

  // 检查是否有防御性表达
  if (response.includes('你怎么') || response.includes('不是我的错')) {
    score -= 15
  }

  return Math.round(Math.min(100, Math.max(0, score)))
}

function generateAiResponse(userMessage: string): string {
  if (!activeChat.value) return '好的，我明白了。'

  const responses: Record<string, string[]> = {
    anxious: [
      '真的吗？你真的不会离开我吗？',
      '对不起，我知道我又想太多了...',
      '你能这样说我真的很开心！',
      '可是万一以后你不想理我了怎么办...'
    ],
    avoidant: [
      '嗯，知道了。',
      '我自己可以处理的，不用担心。',
      '好吧，那就这样吧。',
      '我需要一点自己的空间。'
    ],
    secure: [
      '太好了！我也很期待',
      '听起来不错，你怎么想到的？',
      '谢谢你理解我！',
      '我们可以一起想办法'
    ],
    fearful: [
      '其实我也不知道自己想要什么...',
      '你说的有道理，让我想想',
      '我很想靠近，但又害怕受伤',
      '我们能不能慢慢来...'
    ]
  }

  const pool = responses[activeChat.value.id] || ['好的，我明白了。']
  return pool[Math.floor(Math.random() * pool.length)]
}

function generateSuggestedReplies() {
  if (!activeChat.value) return

  const suggestions: Record<string, string[]> = {
    anxious: ['我在这里，不会离开你的', '你能告诉我你在担心什么吗？', '我刚才在忙，但看到消息了'],
    avoidant: ['好的，你需要空间的时候我给你', '我理解你忙碌的生活', '等你准备好了再聊'],
    secure: ['一起计划一下吧！', '我也有同感', '很高兴你愿意分享'],
    fearful: ['没关系，慢慢来', '我尊重你的感受', '我们可以一起面对']
  }

  const pool = suggestions[activeChat.value.id] || ['好的']
  suggestedReplies.value = pool.slice(0, 3)
}

function useSuggestedReply(reply: string) {
  inputMessage.value = reply
  sendMessage()
}

function scrollToBottom() {
  nextTick(() => {
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight
    }
  })
}

function endChat() {
  showScoreModal.value = true
  finalScore.value = currentScore.value
}

function restartChat() {
  showScoreModal.value = false
  if (activeChat.value) {
    startChat(activeChat.value)
  }
}
</script>

<style scoped>
.animate-fadeIn {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
