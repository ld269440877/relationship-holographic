<template>
  <div class="p-8">
    <!-- 标题区 -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-800 dark:text-white">设置</h1>
      <p class="text-gray-500 dark:text-gray-400 mt-2">管理你的账户偏好和数据 📊</p>
    </div>

    <!-- 设置选项卡 -->
    <div class="flex items-center gap-2 mb-8 border-b border-gray-200 dark:border-gray-700 pb-4">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="activeTab = tab.id"
        class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        :class="[
          activeTab === tab.id
            ? 'bg-blue-500 text-white'
            : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
        ]"
      >
        <component :is="tab.icon" class="w-4 h-4 inline mr-2" />
        {{ tab.name }}
      </button>
    </div>

    <!-- 账户设置 -->
    <div v-if="activeTab === 'account'" class="card max-w-2xl">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">账户信息</h2>

      <div class="space-y-6">
        <!-- 头像 -->
        <div class="flex items-center gap-6">
          <div class="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-3xl font-bold">
            {{ userInitial }}
          </div>
          <div>
            <button class="btn-primary mb-2">更换头像</button>
            <p class="text-xs text-gray-500 dark:text-gray-400">支持 JPG、PNG 格式，最大 2MB</p>
          </div>
        </div>

        <!-- 用户名 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">用户名</label>
          <input
            v-model="profile.username"
            type="text"
            class="input-mac"
            placeholder="输入用户名"
          />
        </div>

        <!-- 邮箱 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">邮箱</label>
          <input
            v-model="profile.email"
            type="email"
            class="input-mac"
            placeholder="输入邮箱"
          />
        </div>

        <!-- 依恋风格 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">我的依恋风格</label>
          <select v-model="profile.attachmentStyle" class="input-mac">
            <option value="">未设置</option>
            <option value="secure">安全型</option>
            <option value="anxious">焦虑型</option>
            <option value="avoidant">回避型</option>
            <option value="fearful">恐惧型</option>
          </select>
        </div>

        <!-- 核心创伤 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">核心创伤（可选）</label>
          <input
            v-model="profile.coreWound"
            type="text"
            class="input-mac"
            placeholder="描述你的核心创伤"
          />
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">了解自己的核心创伤有助于针对性成长</p>
        </div>

        <!-- 爱的语言 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">主要爱的语言</label>
          <div class="grid grid-cols-2 md:grid-cols-5 gap-2">
            <button
              v-for="lang in loveLanguages"
              :key="lang.id"
              @click="profile.loveLanguage = lang.id"
              class="p-3 rounded-xl border-2 text-center transition-all"
              :class="[
                profile.loveLanguage === lang.id
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-700'
              ]"
            >
              <div class="text-2xl mb-1">{{ lang.icon }}</div>
              <div class="text-xs text-gray-600 dark:text-gray-300">{{ lang.name }}</div>
            </button>
          </div>
        </div>

        <button @click="saveProfile" class="btn-primary" :disabled="saving">
          {{ saving ? '保存中...' : '保存更改' }}
        </button>
      </div>
    </div>

    <!-- 偏好设置 -->
    <div v-else-if="activeTab === 'preferences'" class="card max-w-2xl">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">训练偏好</h2>

      <div class="space-y-6">
        <!-- 每日目标 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            每日训练目标
          </label>
          <div class="flex items-center gap-4">
            <input
              v-model.number="preferences.dailyGoal"
              type="range"
              min="5"
              max="60"
              step="5"
              class="flex-1"
            />
            <span class="w-16 text-center font-bold text-blue-500">{{ preferences.dailyGoal }}分钟</span>
          </div>
        </div>

        <!-- 难度偏好 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            训练难度偏好
          </label>
          <div class="flex gap-2">
            <button
              v-for="level in difficultyLevels"
              :key="level.value"
              @click="preferences.difficulty = level.value"
              class="flex-1 px-4 py-3 rounded-xl border-2 text-center transition-all"
              :class="[
                preferences.difficulty === level.value
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-200 dark:border-gray-700'
              ]"
            >
              <div class="text-lg font-bold text-gray-800 dark:text-white">{{ level.label }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">{{ level.desc }}</div>
            </button>
          </div>
        </div>

        <!-- 提醒设置 -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <div class="font-medium text-gray-800 dark:text-white">每日提醒</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">在指定时间提醒你训练</div>
            </div>
            <button
              @click="preferences.dailyReminder = !preferences.dailyReminder"
              class="relative w-14 h-8 rounded-full transition-colors"
              :class="preferences.dailyReminder ? 'bg-blue-500' : 'bg-gray-300 dark:bg-gray-600'"
            >
              <div
                class="absolute top-1 w-6 h-6 rounded-full bg-white shadow transition-transform"
                :class="preferences.dailyReminder ? 'translate-x-7' : 'translate-x-1'"
              ></div>
            </button>
          </div>

          <div v-if="preferences.dailyReminder" class="pl-4 border-l-2 border-blue-500">
            <label class="block text-sm text-gray-600 dark:text-gray-300 mb-2">提醒时间</label>
            <input
              v-model="preferences.reminderTime"
              type="time"
              class="input-mac max-w-[200px]"
            />
          </div>
        </div>

        <!-- 声音设置 -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <div class="font-medium text-gray-800 dark:text-white">完成音效</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">训练完成时播放音效</div>
            </div>
            <button
              @click="preferences.soundEnabled = !preferences.soundEnabled"
              class="relative w-14 h-8 rounded-full transition-colors"
              :class="preferences.soundEnabled ? 'bg-blue-500' : 'bg-gray-300 dark:bg-gray-600'"
            >
              <div
                class="absolute top-1 w-6 h-6 rounded-full bg-white shadow transition-transform"
                :class="preferences.soundEnabled ? 'translate-x-7' : 'translate-x-1'"
              ></div>
            </button>
          </div>

          <div class="flex items-center justify-between">
            <div>
              <div class="font-medium text-gray-800 dark:text-white">震动反馈</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">完成操作时震动提醒</div>
            </div>
            <button
              @click="preferences.vibrationEnabled = !preferences.vibrationEnabled"
              class="relative w-14 h-8 rounded-full transition-colors"
              :class="preferences.vibrationEnabled ? 'bg-blue-500' : 'bg-gray-300 dark:bg-gray-600'"
            >
              <div
                class="absolute top-1 w-6 h-6 rounded-full bg-white shadow transition-transform"
                :class="preferences.vibrationEnabled ? 'translate-x-7' : 'translate-x-1'"
              ></div>
            </button>
          </div>
        </div>

        <!-- 主题选择 -->
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            外观主题
          </label>
          <div class="grid grid-cols-3 gap-4">
            <button
              v-for="theme in themes"
              :key="theme.id"
              @click="setTheme(theme.id)"
              class="p-4 rounded-xl border-2 text-center transition-all"
              :class="[
                preferences.theme === theme.id
                  ? 'border-blue-500'
                  : 'border-gray-200 dark:border-gray-700'
              ]"
            >
              <div class="w-10 h-10 rounded-full mx-auto mb-2" :class="theme.preview"></div>
              <div class="text-sm font-medium text-gray-800 dark:text-white">{{ theme.name }}</div>
            </button>
          </div>
        </div>

        <button @click="savePreferences" class="btn-primary" :disabled="saving">
          {{ saving ? '保存中...' : '保存偏好' }}
        </button>
      </div>
    </div>

    <!-- 数据管理 -->
    <div v-else-if="activeTab === 'data'" class="card max-w-2xl">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">数据管理</h2>

      <div class="space-y-6">
        <!-- 数据统计 -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50 text-center">
            <div class="text-2xl font-bold text-blue-500">{{ dataStats.trainingDays }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">训练天数</div>
          </div>
          <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50 text-center">
            <div class="text-2xl font-bold text-green-500">{{ dataStats.totalMinutes }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">总训练分钟</div>
          </div>
          <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50 text-center">
            <div class="text-2xl font-bold text-purple-500">{{ dataStats.mistakesReviewed }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">复习错题数</div>
          </div>
          <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50 text-center">
            <div class="text-2xl font-bold text-orange-500">{{ dataStats.currentStreak }}</div>
            <div class="text-xs text-gray-500 dark:text-gray-400">当前连续</div>
          </div>
        </div>

        <!-- 导出数据 -->
        <div class="p-4 rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="font-medium text-gray-800 dark:text-white">导出我的数据</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">下载你的所有训练记录和个人信息</p>
            </div>
            <button @click="exportData" class="btn-secondary">
              <Download class="w-4 h-4 inline mr-2" />
              导出
            </button>
          </div>
        </div>

        <!-- 清除缓存 -->
        <div class="p-4 rounded-xl border-2 border-dashed border-gray-300 dark:border-gray-600">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="font-medium text-gray-800 dark:text-white">清除缓存</h3>
              <p class="text-sm text-gray-500 dark:text-gray-400">清除本地缓存的临时数据</p>
            </div>
            <button @click="clearCache" class="btn-secondary">
              <Trash2 class="w-4 h-4 inline mr-2" />
              清除
            </button>
          </div>
        </div>

        <!-- 重置进度 -->
        <div class="p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="font-medium text-red-600 dark:text-red-400">重置训练进度</h3>
              <p class="text-sm text-red-500 dark:text-red-400">清除所有训练记录和错题本，此操作不可逆</p>
            </div>
            <button @click="showResetConfirm = true" class="px-4 py-2 rounded-lg bg-red-500 text-white hover:bg-red-600">
              重置
            </button>
          </div>
        </div>

        <!-- 注销账户 -->
        <div class="p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <div class="flex items-center justify-between">
            <div>
              <h3 class="font-medium text-red-600 dark:text-red-400">注销账户</h3>
              <p class="text-sm text-red-500 dark:text-red-400">永久删除你的账户和所有数据，此操作不可逆</p>
            </div>
            <button @click="showDeleteConfirm = true" class="px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700">
              注销
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 关于 -->
    <div v-else-if="activeTab === 'about'" class="card max-w-2xl">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">关于</h2>

      <div class="space-y-6">
        <!-- Logo和名称 -->
        <div class="text-center py-8">
          <div class="w-24 h-24 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-4xl shadow-lg">
            💑
          </div>
          <h3 class="text-2xl font-bold text-gray-800 dark:text-white">关系动力学全息</h3>
          <p class="text-gray-500 dark:text-gray-400 mt-1">两性关系感知训练系统</p>
          <p class="text-sm text-gray-400 dark:text-gray-500 mt-2">版本 1.0.0</p>
        </div>

        <!-- 功能介绍 -->
        <div class="space-y-4">
          <h4 class="font-bold text-gray-800 dark:text-white">核心功能</h4>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
              <div class="text-2xl mb-2">🎯</div>
              <h5 class="font-medium text-gray-800 dark:text-white">精准评估</h5>
              <p class="text-sm text-gray-500 dark:text-gray-400">科学的依恋风格测试和能力评估</p>
            </div>
            <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
              <div class="text-2xl mb-2">🧠</div>
              <h5 class="font-medium text-gray-800 dark:text-white">微训练</h5>
              <p class="text-sm text-gray-500 dark:text-gray-400">每日5分钟，持续提升关系感知</p>
            </div>
            <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
              <div class="text-2xl mb-2">📝</div>
              <h5 class="font-medium text-gray-800 dark:text-white">错题本</h5>
              <p class="text-sm text-gray-500 dark:text-gray-400">从错误中学习，温故知新</p>
            </div>
            <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
              <div class="text-2xl mb-2">🤖</div>
              <h5 class="font-medium text-gray-800 dark:text-white">AI伴侣</h5>
              <p class="text-sm text-gray-500 dark:text-gray-400">模拟真实对话场景的AI训练</p>
            </div>
          </div>
        </div>

        <!-- 致谢 -->
        <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
          <h4 class="font-bold text-gray-800 dark:text-white mb-3">技术栈</h4>
          <div class="flex flex-wrap gap-2">
            <span class="px-3 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-sm">Vue 3</span>
            <span class="px-3 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 text-sm">TypeScript</span>
            <span class="px-3 py-1 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 text-sm">Tailwind CSS</span>
            <span class="px-3 py-1 rounded-full bg-orange-100 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 text-sm">Pinia</span>
            <span class="px-3 py-1 rounded-full bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-sm">Vite</span>
          </div>
        </div>

        <!-- 版权 -->
        <div class="text-center text-sm text-gray-400 dark:text-gray-500">
          <p>© 2024 关系动力学全息. 保留所有权利.</p>
          <p class="mt-2">持续进化中... 🚀</p>
        </div>
      </div>
    </div>

    <!-- 重置确认弹窗 -->
    <Teleport to="body">
      <transition name="fade">
        <div
          v-if="showResetConfirm"
          class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          @click.self="showResetConfirm = false"
        >
          <div class="bg-white dark:bg-gray-800 rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl">
            <h3 class="text-xl font-bold text-red-600 dark:text-red-400 mb-4">⚠️ 确认重置</h3>
            <p class="text-gray-600 dark:text-gray-300 mb-6">
              确定要重置所有训练进度吗？这将清除所有训练记录和错题本，但你的账户数据将保留。此操作不可逆。
            </p>
            <div class="flex gap-4">
              <button @click="showResetConfirm = false" class="flex-1 btn-secondary">取消</button>
              <button @click="confirmReset" class="flex-1 px-4 py-2 rounded-lg bg-red-500 text-white hover:bg-red-600">确认重置</button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>

    <!-- 注销确认弹窗 -->
    <Teleport to="body">
      <transition name="fade">
        <div
          v-if="showDeleteConfirm"
          class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          @click.self="showDeleteConfirm = false"
        >
          <div class="bg-white dark:bg-gray-800 rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl">
            <h3 class="text-xl font-bold text-red-600 dark:text-red-400 mb-4">⚠️ 确认注销</h3>
            <p class="text-gray-600 dark:text-gray-300 mb-6">
              确定要注销你的账户吗？所有数据将被永久删除，包括训练记录和个人设置。此操作不可逆。
            </p>
            <div class="flex gap-4">
              <button @click="showDeleteConfirm = false" class="flex-1 btn-secondary">取消</button>
              <button @click="confirmDelete" class="flex-1 px-4 py-2 rounded-lg bg-red-600 text-white hover:bg-red-700">确认注销</button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { User, Sliders, Database, Info, Download, Trash2 } from 'lucide-vue-next'
import { useProfileStore } from '@/stores/profile'
import { useToast } from '@/utils/toast'

const profileStore = useProfileStore()
const toast = useToast()

const activeTab = ref('account')
const saving = ref(false)
const showResetConfirm = ref(false)
const showDeleteConfirm = ref(false)

const tabs = [
  { id: 'account', name: '账户', icon: User },
  { id: 'preferences', name: '偏好', icon: Sliders },
  { id: 'data', name: '数据', icon: Database },
  { id: 'about', name: '关于', icon: Info }
]

const loveLanguages = [
  { id: 'words', name: '肯定', icon: '💬' },
  { id: 'time', name: '陪伴', icon: '⏰' },
  { id: 'gifts', name: '礼物', icon: '🎁' },
  { id: 'help', name: '服务', icon: '🤝' },
  { id: 'touch', name: '接触', icon: '🤗' }
]

const difficultyLevels = [
  { value: 'easy', label: '入门', desc: '打好基础' },
  { value: 'medium', label: '进阶', desc: '逐步提升' },
  { value: 'hard', label: '挑战', desc: '突破极限' }
]

const themes = [
  { id: 'light', name: '浅色', preview: 'bg-gray-100' },
  { id: 'dark', name: '深色', preview: 'bg-gray-800' },
  { id: 'system', name: '自动', preview: 'bg-gradient-to-r from-gray-100 to-gray-800' }
]

const profile = ref({
  username: '',
  email: '',
  attachmentStyle: '',
  coreWound: '',
  loveLanguage: ''
})

const preferences = ref({
  dailyGoal: 15,
  difficulty: 'medium',
  dailyReminder: true,
  reminderTime: '20:00',
  soundEnabled: true,
  vibrationEnabled: true,
  theme: 'system'
})

const dataStats = ref({
  trainingDays: 42,
  totalMinutes: 1234,
  mistakesReviewed: 89,
  currentStreak: 7
})

const userInitial = computed(() => {
  return profile.value.username?.charAt(0)?.toUpperCase() || 'U'
})

onMounted(async () => {
  await profileStore.fetchProfile()
  if (profileStore.profile) {
    profile.value = {
      username: '用户',
      email: profileStore.profile.email || 'user@example.com',
      attachmentStyle: profileStore.profile.attachment_style || '',
      coreWound: profileStore.profile.core_wound || '',
      loveLanguage: profileStore.profile.love_language || ''
    }
  }
})

async function saveProfile() {
  saving.value = true
  try {
    await profileStore.updateProfile({
      attachment_style: profile.value.attachmentStyle || undefined,
      core_wound: profile.value.coreWound || undefined,
      love_language: profile.value.loveLanguage || undefined
    })
    toast.success('个人资料已保存')
  } catch (e) {
    toast.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

async function savePreferences() {
  saving.value = true
  try {
    localStorage.setItem('preferences', JSON.stringify(preferences.value))
    toast.success('偏好设置已保存')
  } catch (e) {
    toast.error('保存失败')
  } finally {
    saving.value = false
  }
}

function setTheme(themeId: string) {
  preferences.value.theme = themeId
  if (themeId === 'dark') {
    document.documentElement.classList.add('dark')
  } else if (themeId === 'light') {
    document.documentElement.classList.remove('dark')
  } else {
    if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }
}

function exportData() {
  const data = {
    profile: profile.value,
    preferences: preferences.value,
    stats: dataStats.value,
    exportDate: new Date().toISOString()
  }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `relationship-training-data-${new Date().toISOString().split('T')[0]}.json`
  a.click()
  URL.revokeObjectURL(url)
  toast.success('数据已导出')
}

function clearCache() {
  localStorage.clear()
  toast.success('缓存已清除')
}

function confirmReset() {
  showResetConfirm.value = false
  toast.success('进度已重置')
}

function confirmDelete() {
  showDeleteConfirm.value = false
  toast.info('账户注销功能开发中...')
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
