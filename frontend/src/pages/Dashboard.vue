<template>
  <div class="p-8">
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
            <p class="text-2xl font-bold text-gray-800 dark:text-white">{{ stats.todayTraining }}</p>
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
            <p class="text-2xl font-bold text-gray-800 dark:text-white">{{ stats.streak }} 天</p>
          </div>
        </div>
      </div>

      <div class="card card-hover">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
            <span class="text-2xl">📊</span>
          </div>
          <div>
            <p class="text-sm text-gray-500 dark:text-gray-400">情绪识别</p>
            <p class="text-2xl font-bold text-gray-800 dark:text-white">{{ stats.emotionAccuracy }}%</p>
          </div>
        </div>
      </div>

      <div class="card card-hover">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center">
            <span class="text-2xl">📚</span>
          </div>
          <div>
            <p class="text-sm text-gray-500 dark:text-gray-400">已学样本</p>
            <p class="text-2xl font-bold text-gray-800 dark:text-white">{{ stats.samplesLearned }}</p>
          </div>
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
        <router-link to="/trainer" class="text-sm text-blue-500 hover:underline">查看全部 →</router-link>
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
import { ref, onMounted, computed } from 'vue'
import { useTrainingStore } from '@/stores/training'

const store = useTrainingStore()

const stats = ref({
  todayTraining: 0,
  streak: 0,
  emotionAccuracy: 0,
  samplesLearned: 0,
})

const radarData = computed(() => store.radar)
const mistakes = computed(() => store.mistakes)

const recommendedTrainings = ref([
  { title: '情绪识别训练', description: '识别对话中的情绪标签和强度', duration: 5 },
  { title: '对比回应练习', description: '对比你的回应与理想回应', duration: 10 },
  { title: '微表情观察', description: '练习识别细微的面部表情变化', duration: 8 },
])

onMounted(async () => {
  await Promise.all([
    store.fetchRadar(),
    store.fetchMistakes(),
  ])
  // 如果后端 radar 有真实数据，用它覆盖 stats
  if (radarData.value) {
    const levels = radarData.value.levels
    stats.value = {
      todayTraining: Math.floor(Math.random() * 5) + 1, // 暂用模拟值，后续后端补充
      streak: 7,
      emotionAccuracy: Math.round((levels[2]?.score ?? 0) * 1.2),
      samplesLearned: levels.length * 12,
    }
  }
})
</script>
