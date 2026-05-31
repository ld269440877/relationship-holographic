<template>
  <div class="p-8">
    <!-- 标题区 -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-800 dark:text-white">设置</h1>
      <p class="text-gray-500 dark:text-gray-400 mt-2">管理你的账户偏好和数据 📊</p>
    </div>

    <ModuleTabs v-model="activeTab" :tabs="tabs" label="设置选项卡" id-prefix="settings-tab" class="mb-8" />

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
            <div class="flex flex-col gap-3 sm:flex-row sm:items-center">
              <input
                v-model="preferences.reminderTime"
                type="time"
                class="input-mac max-w-[200px]"
              />
              <button
                type="button"
                class="btn-secondary"
                :disabled="testingReminder"
                @click="testReminder"
              >
                {{ testingReminder ? '发送中...' : '测试提醒' }}
              </button>
            </div>
            <div class="mt-3 rounded-lg bg-gray-50 p-3 text-xs leading-5 text-gray-600 dark:bg-gray-900 dark:text-gray-300">
              <p class="font-semibold text-gray-800 dark:text-white">本地浏览器提醒</p>
              <p class="mt-1">{{ reminderStatusText }}</p>
              <p class="mt-1 text-gray-500 dark:text-gray-400">
                这是浏览器本地通知：需要允许通知权限，并且页面或浏览器保持打开。不是手机后台推送。
              </p>
            </div>
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
            <button @click="exportData" class="btn-secondary" :disabled="exporting">
              <Download class="w-4 h-4 inline mr-2" />
              {{ exporting ? '生成中...' : '导出' }}
            </button>
          </div>
          <div
            v-if="exportResult"
            class="mt-4 rounded-xl border border-blue-100 bg-blue-50/70 p-4 text-sm dark:border-blue-900/50 dark:bg-blue-950/20"
          >
            <div class="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div class="min-w-0">
                <p class="font-semibold text-blue-700 dark:text-blue-300">{{ exportResult.statusTitle }}</p>
                <p class="mt-1 break-words text-gray-700 dark:text-gray-200">{{ exportResult.filename }}</p>
                <p class="mt-2 text-xs leading-5 text-gray-500 dark:text-gray-400">
                  大小 {{ exportResult.sizeLabel }} · {{ exportResult.recordCount }} 条结构化记录 · {{ exportResult.createdAt }}
                </p>
                <p class="mt-2 text-xs leading-5 text-gray-500 dark:text-gray-400">
                  {{ exportResult.locationHint }}
                </p>
              </div>
              <div class="flex shrink-0 flex-col gap-2 sm:items-end">
                <button
                  type="button"
                  class="rounded-lg bg-blue-600 px-3 py-2 text-center text-sm font-semibold text-white hover:bg-blue-700"
                  @click="saveExportFile"
                >
                  选择位置保存
                </button>
                <a
                  :href="exportResult.url"
                  :download="exportResult.filename"
                  class="rounded-lg bg-white px-3 py-2 text-center text-xs font-semibold text-blue-700 hover:bg-blue-50 dark:bg-gray-900 dark:text-blue-300 dark:hover:bg-gray-800"
                >
                  下载到默认目录
                </a>
              </div>
            </div>
            <p v-if="exportResult.fallbackDownload" class="mt-3 text-xs leading-5 text-amber-700 dark:text-amber-300">
              当前浏览器未开放系统保存窗口，已使用下载目录兜底。若没有弹窗，请查看浏览器默认下载目录。
            </p>
            <div class="mt-3 rounded-lg bg-white p-3 dark:bg-gray-900">
              <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">校验指纹</p>
              <p class="mt-1 break-all font-mono text-xs text-gray-700 dark:text-gray-200">{{ exportResult.sha256 }}</p>
            </div>
            <div class="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
              <div
                v-for="item in exportResult.coverage"
                :key="item.label"
                class="rounded-lg bg-white px-3 py-2 text-xs text-gray-600 dark:bg-gray-900 dark:text-gray-300"
              >
                <span class="font-semibold text-gray-800 dark:text-white">{{ item.label }}：</span>{{ item.value }}
              </div>
            </div>
          </div>
          <div
            v-if="exportError"
            class="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300"
          >
            {{ exportError }}
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
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { User, Sliders, Database, Info, Download, Trash2 } from 'lucide-vue-next'
import ModuleTabs from '@/components/ModuleTabs.vue'
import { useProfileStore } from '@/stores/profile'
import { useTrainingStore } from '@/stores/training'
import { useToast } from '@/utils/toast'
import {
  formatReminderTime,
  requestAndScheduleDailyTrainingReminder,
  scheduleDailyTrainingReminder,
  sendTestTrainingReminder,
  type ReminderScheduleResult,
} from '@/utils/localReminder'

const profileStore = useProfileStore()
const trainingStore = useTrainingStore()
const toast = useToast()

type SaveFilePickerWindow = Window & typeof globalThis & {
  showSaveFilePicker?: (options: {
    suggestedName?: string
    types?: Array<{
      description?: string
      accept: Record<string, string[]>
    }>
  }) => Promise<{
    createWritable: () => Promise<{
      write: (data: string) => Promise<void>
      close: () => Promise<void>
    }>
  }>
}

const activeTab = ref('account')
const saving = ref(false)
const exporting = ref(false)
const exportError = ref('')
const showResetConfirm = ref(false)
const showDeleteConfirm = ref(false)
const reminderStatus = ref<ReminderScheduleResult | null>(null)
const testingReminder = ref(false)
const exportResult = ref<{
  filename: string
  url: string
  sha256: string
  sizeLabel: string
  recordCount: number
  createdAt: string
  markdown: string
  statusTitle: string
  locationHint: string
  fallbackDownload: boolean
  coverage: Array<{ label: string; value: string }>
} | null>(null)

const tabs = [
  { id: 'account', label: '账户', summary: '管理头像、用户名、依恋风格和爱语。', icon: User },
  { id: 'preferences', label: '偏好', summary: '设置训练目标、难度、主题、提醒和界面偏好。', icon: Sliders },
  { id: 'data', label: '数据', summary: '导出 Markdown 档案、清理缓存和管理本地数据。', icon: Database },
  { id: 'about', label: '关于', summary: '查看版本、产品边界和隐私说明。', icon: Info }
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

const reminderStatusText = computed(() => {
  if (!preferences.value.dailyReminder) return '每日提醒已关闭。'
  if (!reminderStatus.value) return '提醒时间会在保存偏好后生效。'
  if (reminderStatus.value.nextAt) {
    return `${reminderStatus.value.message}（${formatReminderTime(reminderStatus.value.nextAt)}）`
  }
  return reminderStatus.value.message
})

onMounted(async () => {
  await profileStore.fetchProfile()
  loadStoredPreferences()
  if (profileStore.profile) {
    profile.value = {
      username: '用户',
      email: profileStore.profile.email || 'user@example.com',
      attachmentStyle: profileStore.profile.attachment_style || '',
      coreWound: profileStore.profile.core_wound || '',
      loveLanguage: profileStore.profile.love_language || ''
    }
  }
  reminderStatus.value = scheduleDailyTrainingReminder(preferences.value)
})

onBeforeUnmount(() => {
  revokeExportUrl()
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
    reminderStatus.value = await requestAndScheduleDailyTrainingReminder(preferences.value)
    toast.success(preferences.value.dailyReminder ? '偏好已保存，提醒设置已更新' : '偏好设置已保存')
  } catch (e) {
    toast.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function testReminder() {
  testingReminder.value = true
  try {
    const result = await sendTestTrainingReminder()
    reminderStatus.value = result
    if (result.enabled) {
      toast.success(result.message)
    } else {
      toast.warning(result.message)
    }
  } finally {
    testingReminder.value = false
  }
}

function loadStoredPreferences() {
  try {
    const raw = localStorage.getItem('preferences')
    if (!raw) return
    preferences.value = {
      ...preferences.value,
      ...JSON.parse(raw),
    }
  } catch {
    // Keep defaults if local preferences are malformed.
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

async function exportData() {
  exporting.value = true
  exportError.value = ''
  try {
    await Promise.all([
      trainingStore.fetchMistakes(),
      trainingStore.fetchDueReviews(),
      trainingStore.fetchSummaries(),
      trainingStore.fetchRadar(),
    ])
    const exportedAt = new Date()
    const payload = buildExportPayload(exportedAt)
    const markdown = buildExportMarkdown(payload, exportedAt)
    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
    const sha256 = await digestText(markdown)
    const filename = `relationship-training-export-${exportedAt.toISOString().slice(0, 10)}.md`
    revokeExportUrl()
    const url = URL.createObjectURL(blob)
    exportResult.value = {
      filename,
      url,
      sha256,
      sizeLabel: formatBytes(blob.size),
      recordCount: payload.manifest.record_count,
      createdAt: exportedAt.toLocaleString(),
      markdown,
      statusTitle: 'Markdown 导出已生成',
      locationHint: '点击“选择位置保存”可指定保存位置；点击“下载到默认目录”会进入浏览器默认下载目录。',
      fallbackDownload: false,
      coverage: [
        { label: '个人资料', value: payload.profile ? '已包含' : '未加载' },
        { label: '偏好设置', value: '已包含' },
        { label: '错题记录', value: `${payload.training.mistakes.length} 条` },
        { label: '到期复习', value: `${payload.training.due_reviews.length} 条` },
        { label: '训练摘要', value: payload.training.today_summary || payload.training.week_summary ? '已包含' : '暂无' },
      ],
    }
    toast.success('Markdown 导出已生成，可选择保存位置')
  } catch (error) {
    exportError.value = error instanceof Error ? error.message : '导出失败，请稍后重试'
    toast.error(exportError.value)
  } finally {
    exporting.value = false
  }
}

async function saveExportFile() {
  if (!exportResult.value) return
  const saveResult = await writeFileWithPicker(exportResult.value.markdown, exportResult.value.filename)
  if (!saveResult.saved) {
    triggerDownload(exportResult.value.url, exportResult.value.filename)
    exportResult.value = {
      ...exportResult.value,
      statusTitle: 'Markdown 导出已生成',
      locationHint: '备用下载已再次触发；实际位置取决于浏览器的默认下载目录或下载提示。',
      fallbackDownload: true,
    }
    toast.info('已触发备用下载，请查看浏览器下载目录')
    return
  }
  exportResult.value = {
    ...exportResult.value,
    statusTitle: 'Markdown 导出已保存',
    locationHint: '文件已保存到你刚才在系统窗口中选择的位置。',
    fallbackDownload: false,
  }
  toast.success('Markdown 文件已保存')
}

async function writeFileWithPicker(markdown: string, filename: string) {
  const picker = (window as SaveFilePickerWindow).showSaveFilePicker
  if (!picker) return { saved: false, reason: 'unsupported' }
  try {
    const handle = await picker({
      suggestedName: filename,
      types: [
        {
          description: 'Markdown 文件',
          accept: { 'text/markdown': ['.md'] },
        },
      ],
    })
    const writable = await handle.createWritable()
    await writable.write(markdown)
    await writable.close()
    return { saved: true, reason: 'file-system-access-api' }
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      return { saved: false, reason: 'cancelled' }
    }
    return { saved: false, reason: 'failed' }
  }
}

function buildExportPayload(exportedAt: Date) {
  const mistakes = trainingStore.mistakes
  const dueReviews = trainingStore.dueReviews
  return {
    manifest: {
      schema_version: 'settings_export.v1',
      app_name: '关系动力学全息',
      exported_at: exportedAt.toISOString(),
      export_scope: [
        'profile',
        'preferences',
        'data_stats',
        'training_summaries',
        'mistakes',
        'due_reviews',
        'radar',
        'local_runtime_flags',
      ],
      record_count: mistakes.length + dueReviews.length + (trainingStore.todaySummary ? 1 : 0) + (trainingStore.weekSummary ? 1 : 0) + (trainingStore.radar ? 1 : 0),
      privacy_note: '导出文件优先保存到你选择的位置；如果浏览器不支持系统保存窗口，则进入默认下载目录。本页面不会上传导出包。',
    },
    profile: {
      ...profile.value,
      server_profile: profileStore.profile,
    },
    preferences: preferences.value,
    data_stats: dataStats.value,
    training: {
      today_summary: trainingStore.todaySummary,
      week_summary: trainingStore.weekSummary,
      radar: trainingStore.radar,
      mistakes,
      due_reviews: dueReviews,
    },
    local_runtime: {
      has_completed_onboarding: localStorage.getItem('hasCompletedOnboarding') === 'true',
      theme: preferences.value.theme,
    },
  }
}

function buildExportMarkdown(payload: ReturnType<typeof buildExportPayload>, exportedAt: Date) {
  const lines: string[] = []
  lines.push('# 关系动力学全息训练数据导出')
  lines.push('')
  lines.push(`- 导出时间：${exportedAt.toLocaleString()}`)
  lines.push(`- Schema：${payload.manifest.schema_version}`)
  lines.push(`- 记录数：${payload.manifest.record_count}`)
  lines.push(`- 隐私说明：${payload.manifest.privacy_note}`)
  lines.push('')
  lines.push('## 概览')
  lines.push('')
  lines.push('| 项目 | 值 |')
  lines.push('| --- | --- |')
  lines.push(`| 训练天数 | ${payload.data_stats.trainingDays} |`)
  lines.push(`| 总训练分钟 | ${payload.data_stats.totalMinutes} |`)
  lines.push(`| 复习错题数 | ${payload.data_stats.mistakesReviewed} |`)
  lines.push(`| 当前连续 | ${payload.data_stats.currentStreak} |`)
  lines.push('')
  lines.push('## 个人资料')
  lines.push('')
  lines.push(`- 用户名：${payload.profile.username || '-'}`)
  lines.push(`- 邮箱：${payload.profile.email || '-'}`)
  lines.push(`- 依恋风格：${payload.profile.attachmentStyle || '-'}`)
  lines.push(`- 核心创伤：${payload.profile.coreWound || '-'}`)
  lines.push(`- 主要爱的语言：${payload.profile.loveLanguage || '-'}`)
  lines.push('')
  lines.push('## 偏好设置')
  lines.push('')
  lines.push('| 偏好 | 当前值 |')
  lines.push('| --- | --- |')
  lines.push(`| 每日训练目标 | ${payload.preferences.dailyGoal} 分钟 |`)
  lines.push(`| 难度 | ${payload.preferences.difficulty} |`)
  lines.push(`| 每日提醒 | ${payload.preferences.dailyReminder ? '开启' : '关闭'} |`)
  lines.push(`| 提醒时间 | ${payload.preferences.reminderTime || '-'} |`)
  lines.push(`| 完成音效 | ${payload.preferences.soundEnabled ? '开启' : '关闭'} |`)
  lines.push(`| 震动反馈 | ${payload.preferences.vibrationEnabled ? '开启' : '关闭'} |`)
  lines.push(`| 主题 | ${payload.preferences.theme} |`)
  lines.push('')
  lines.push('## 训练摘要')
  lines.push('')
  lines.push('### 今日摘要')
  lines.push('')
  lines.push(formatMarkdownBlock(payload.training.today_summary))
  lines.push('')
  lines.push('### 本周摘要')
  lines.push('')
  lines.push(formatMarkdownBlock(payload.training.week_summary))
  lines.push('')
  lines.push('### 能力雷达')
  lines.push('')
  lines.push(formatMarkdownBlock(payload.training.radar))
  lines.push('')
  lines.push(`## 错题记录（${payload.training.mistakes.length} 条）`)
  lines.push('')
  for (const [index, mistake] of payload.training.mistakes.entries()) {
    lines.push(`### ${index + 1}. ${readableField(mistake, ['sample_title', 'title', 'mistake_type'], '错题记录')}`)
    lines.push('')
    lines.push(formatMarkdownBlock(mistake))
    lines.push('')
  }
  lines.push(`## 到期复习（${payload.training.due_reviews.length} 条）`)
  lines.push('')
  for (const [index, review] of payload.training.due_reviews.entries()) {
    lines.push(`### ${index + 1}. ${readableField(review, ['sample_title', 'title', 'review_type'], '复习记录')}`)
    lines.push('')
    lines.push(formatMarkdownBlock(review))
    lines.push('')
  }
  lines.push('## 原始审计 JSON')
  lines.push('')
  lines.push('```json')
  lines.push(JSON.stringify(payload, null, 2))
  lines.push('```')
  lines.push('')
  return lines.join('\n')
}

function readableField(value: unknown, keys: string[], fallback: string) {
  if (!value || typeof value !== 'object') return fallback
  const record = value as Record<string, unknown>
  for (const key of keys) {
    const field = record[key]
    if (field !== undefined && field !== null && String(field).trim()) return String(field)
  }
  return fallback
}

function formatMarkdownBlock(value: unknown) {
  if (value === undefined || value === null || value === '') return '_暂无数据_'
  if (typeof value === 'string') return value
  return `\`\`\`json\n${JSON.stringify(value, null, 2)}\n\`\`\``
}

async function digestText(text: string) {
  if (!crypto?.subtle) return `checksum:${simpleChecksum(text)}`
  const bytes = new TextEncoder().encode(text)
  const digest = await crypto.subtle.digest('SHA-256', bytes)
  return `sha256:${Array.from(new Uint8Array(digest)).map(byte => byte.toString(16).padStart(2, '0')).join('')}`
}

function simpleChecksum(text: string) {
  let hash = 0
  for (let index = 0; index < text.length; index += 1) {
    hash = (hash * 31 + text.charCodeAt(index)) >>> 0
  }
  return hash.toString(16).padStart(8, '0')
}

function formatBytes(size: number) {
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function triggerDownload(url: string, filename: string) {
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.rel = 'noopener'
  document.body.appendChild(link)
  link.click()
  link.remove()
}

function revokeExportUrl() {
  if (exportResult.value?.url) URL.revokeObjectURL(exportResult.value.url)
  exportResult.value = null
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
