<template>
  <div class="p-8">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-800 dark:text-white">我的档案</h1>
      <p class="text-gray-500 dark:text-gray-400 mt-2">了解自己，提升感知</p>
    </div>

    <!-- 用户信息 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- 基本信息 -->
      <div class="card">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">基本信息</h2>
        <div class="space-y-4">
          <div class="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
            <span class="text-gray-600 dark:text-gray-300">依恋类型</span>
            <span class="px-3 py-1 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
              {{ profile?.attachment_style || '安全型' }}
            </span>
          </div>
          <div class="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
            <span class="text-gray-600 dark:text-gray-300">爱语</span>
            <span class="text-gray-800 dark:text-white">{{ profile?.love_language || '肯定言辞 / 优质时间' }}</span>
          </div>
          <div class="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
            <span class="text-gray-600 dark:text-gray-300">情绪词汇量</span>
            <span class="text-gray-800 dark:text-white">{{ profile?.emotion_vocab_size || 35 }} 个</span>
          </div>
          <div class="flex items-center justify-between p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
            <span class="text-gray-600 dark:text-gray-300">感知基线</span>
            <span class="text-gray-800 dark:text-white">{{ profile?.perception_baseline || 50 }} / 100</span>
          </div>
        </div>
      </div>

      <!-- 能力成长曲线 -->
      <div class="card">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">能力成长曲线</h2>
        <div class="space-y-4">
          <div v-for="(skill, index) in skills" :key="index" class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-sm text-gray-600 dark:text-gray-300">{{ skill.name }}</span>
              <span class="text-sm text-gray-500 dark:text-gray-400">{{ skill.value }}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-bar-fill" :style="{ width: skill.value + '%' }"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 学习统计 -->
    <div class="card mt-6">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">学习统计</h2>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="text-center p-4 rounded-xl bg-blue-50 dark:bg-blue-900/20">
          <p class="text-3xl font-bold text-blue-600 dark:text-blue-400">{{ stats.totalTraining }}</p>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">总训练次数</p>
        </div>
        <div class="text-center p-4 rounded-xl bg-green-50 dark:bg-green-900/20">
          <p class="text-3xl font-bold text-green-600 dark:text-green-400">{{ stats.samplesLearned }}</p>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">已学样本</p>
        </div>
        <div class="text-center p-4 rounded-xl bg-purple-50 dark:bg-purple-900/20">
          <p class="text-3xl font-bold text-purple-600 dark:text-purple-400">{{ stats.daysStreak }}</p>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">连续打卡</p>
        </div>
        <div class="text-center p-4 rounded-xl bg-orange-50 dark:bg-orange-900/20">
          <p class="text-3xl font-bold text-orange-600 dark:text-orange-400">{{ stats.avgScore }}</p>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">平均得分</p>
        </div>
      </div>
    </div>

    <!-- 核心创伤 -->
    <div class="card mt-6">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">自我觉察</h2>
      <div class="space-y-4">
        <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-2">我的惯性模式</p>
          <p class="text-gray-800 dark:text-white">面对冲突时倾向于回避，事后才反思如何改进</p>
        </div>
        <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
          <p class="text-sm text-gray-500 dark:text-gray-400 mb-2">需要提升的方面</p>
          <p class="text-gray-800 dark:text-white">情绪强度识别、即时反应速度、开放式提问</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProfileStore } from '@/stores/profile'
import { samplesApi } from '@/utils/api'

const profileStore = useProfileStore()
const profile = computed(() => profileStore.profile)

const skills = [
  { name: '情绪识别', value: 72 },
  { name: '共情表达', value: 58 },
  { name: '微表情观察', value: 45 },
  { name: '边界感知', value: 62 },
  { name: '需求洞察', value: 48 },
  { name: '回应质量', value: 55 },
]

const stats = ref({
  totalTraining: 156,
  samplesLearned: 89,
  daysStreak: 7,
  avgScore: 72,
})

onMounted(async () => {
  await profileStore.fetchProfile()
  // 从后端获取样本总数
  try {
    const data = await samplesApi.list({ limit: 1 })
    stats.value.samplesLearned = data.total
  } catch {
    // 忽略
  }
})
</script>
