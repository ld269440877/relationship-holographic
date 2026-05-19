<template>
  <div class="p-8">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-800 dark:text-white">复盘日记</h1>
      <p class="text-gray-500 dark:text-gray-400 mt-2">每日复盘，持续进化</p>
    </div>

    <!-- 今日复盘 -->
    <div class="card mb-8">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">今日复盘</h2>

      <div class="space-y-6">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            今天发生了什么让你有感触的事？
          </label>
          <textarea v-model="reviewForm.highlight" class="input-mac" rows="3" placeholder="描述今天印象最深刻的一件事..."></textarea>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            你的情绪反应是什么？
          </label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="emotion in emotionOptions"
              :key="emotion"
              @click="toggleEmotion(emotion)"
              class="px-3 py-1 rounded-full text-sm transition-all"
              :class="reviewForm.emotions.includes(emotion)
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'"
            >
              {{ emotion }}
            </button>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            如果重来，你会怎么回应？
          </label>
          <textarea v-model="reviewForm.improvement" class="input-mac" rows="2" placeholder="更好的回应方式..."></textarea>
        </div>

        <div class="flex items-center justify-between">
          <div class="text-sm text-gray-500 dark:text-gray-400">
            情绪识别准确率：{{ reviewForm.accuracy }}%
          </div>
          <div class="flex gap-3">
            <input
              v-model.number="reviewForm.accuracy"
              type="range"
              min="0"
              max="100"
              class="w-32"
            />
            <button @click="saveReview" class="btn-primary">
              保存复盘
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 历史复盘 -->
    <div class="card">
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">历史复盘</h2>

      <div v-if="reviewStore.reviews.length > 0" class="space-y-4">
        <div
          v-for="(entry, index) in reviewStore.reviews"
          :key="index"
          class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-sm text-gray-500 dark:text-gray-400">{{ entry.review_date }}</span>
            <span class="text-sm text-blue-500">{{ entry.emotion_accuracy ?? 0 }}%</span>
          </div>
          <p class="text-gray-800 dark:text-white mb-2">{{ entry.highlight }}</p>
          <div class="flex flex-wrap gap-2 mb-2">
            <span
              v-for="emotion in (entry.emotions || [])"
              :key="emotion"
              class="px-2 py-1 rounded text-xs bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
            >
              {{ emotion }}
            </span>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-400">{{ entry.improvement }}</p>
        </div>
      </div>

      <div v-else class="text-center py-8 text-gray-400">
        <p class="text-4xl mb-4">📝</p>
        <p>暂无历史复盘，开始记录今天的吧</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useReviewStore } from '@/stores/review'
import { useToast } from '@/utils/toast'

const reviewStore = useReviewStore()
const toast = useToast()

const emotionOptions = ['开心', '失落', '紧张', '愤怒', '感动', '尴尬', '期待', '安心', '委屈', '无奈']

const reviewForm = ref({
  highlight: '',
  emotions: [] as string[],
  improvement: '',
  accuracy: 72,
})

function toggleEmotion(emotion: string) {
  const idx = reviewForm.value.emotions.indexOf(emotion)
  if (idx === -1) {
    reviewForm.value.emotions.push(emotion)
  } else {
    reviewForm.value.emotions.splice(idx, 1)
  }
}

async function saveReview() {
  if (!reviewForm.value.highlight.trim()) {
    toast.warning('请填写今日复盘内容')
    return
  }
  const today = new Date().toISOString().slice(0, 10)
  await reviewStore.createReview({
    review_date: today,
    highlight: reviewForm.value.highlight,
    emotions: reviewForm.value.emotions,
    improvement: reviewForm.value.improvement,
    emotion_accuracy: reviewForm.value.accuracy,
  })
  toast.success('复盘已保存！')
  // 重置表单
  reviewForm.value.highlight = ''
  reviewForm.value.emotions = []
  reviewForm.value.improvement = ''
}

onMounted(() => {
  reviewStore.fetchReviews()
})
</script>
