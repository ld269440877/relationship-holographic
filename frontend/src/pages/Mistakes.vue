<template>
  <div class="p-8">
    <!-- 标题区 -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-800 dark:text-white">错题本</h1>
      <p class="text-gray-500 dark:text-gray-400 mt-2">从错误中学习，让每一次失误都成为成长的养分 📚</p>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="card">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
            <span class="text-2xl">📝</span>
          </div>
          <div>
            <p class="text-sm text-gray-500 dark:text-gray-400">总错题数</p>
            <p class="text-2xl font-bold text-gray-800 dark:text-white">{{ totalMistakes }}</p>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center">
            <span class="text-2xl">🔥</span>
          </div>
          <div>
            <p class="text-sm text-gray-500 dark:text-gray-400">本周新增</p>
            <p class="text-2xl font-bold text-gray-800 dark:text-white">{{ weeklyNew }}</p>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
            <span class="text-2xl">✅</span>
          </div>
          <div>
            <p class="text-sm text-gray-500 dark:text-gray-400">已纠正</p>
            <p class="text-2xl font-bold text-gray-800 dark:text-white">{{ correctedMistakes }}</p>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-xl bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
            <span class="text-2xl">📈</span>
          </div>
          <div>
            <p class="text-sm text-gray-500 dark:text-gray-400">正确率</p>
            <p class="text-2xl font-bold text-gray-800 dark:text-white">{{ accuracyRate }}%</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 错题分析图表 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      <!-- 错题类型分布 -->
      <div class="card">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">错题类型分布</h2>
        <div class="space-y-4">
          <div v-for="(type, index) in mistakeTypes" :key="index">
            <div class="flex items-center justify-between mb-1">
              <span class="text-sm text-gray-600 dark:text-gray-300">{{ type.name }}</span>
              <span class="text-sm font-medium text-gray-800 dark:text-white">{{ type.count }}道</span>
            </div>
            <div class="progress-bar">
              <div
                class="progress-bar-fill"
                :class="type.color"
                :style="{ width: (type.count / totalMistakes * 100) + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 进步趋势 -->
      <div class="card">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-6">每周进步趋势</h2>
        <div class="flex items-end justify-between h-40 px-4">
          <div
            v-for="(week, index) in weeklyProgress"
            :key="index"
            class="flex flex-col items-center gap-2"
          >
            <div
              class="w-12 rounded-t-lg transition-all duration-500"
              :class="week.improved ? 'bg-green-500' : 'bg-red-500'"
              :style="{ height: (week.correctRate * 100) + 'px' }"
            ></div>
            <span class="text-xs text-gray-500 dark:text-gray-400">{{ week.label }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选器 -->
    <div class="flex items-center gap-4 mb-6">
      <div class="flex items-center gap-2">
        <button
          v-for="filter in filters"
          :key="filter.value"
          @click="selectedFilter = filter.value"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="[
            selectedFilter === filter.value
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
          ]"
        >
          {{ filter.label }}
        </button>
      </div>
      <div class="flex-1"></div>
      <select
        v-model="sortBy"
        class="px-4 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200"
      >
        <option value="newest">最新在前</option>
        <option value="oldest">最早在前</option>
        <option value="difficulty">按难度</option>
      </select>
    </div>

    <!-- 错题列表 -->
    <div class="space-y-4 mb-8">
      <transition-group name="list">
        <div
          v-for="mistake in filteredMistakes"
          :key="mistake.id"
          class="card"
          :class="{ 'opacity-60': mistake.corrected }"
        >
          <div class="flex items-start gap-4">
            <!-- 序号 -->
            <div
              class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold flex-shrink-0"
              :class="mistake.corrected ? 'bg-green-500' : 'bg-red-500'"
            >
              <CheckIcon v-if="mistake.corrected" class="w-5 h-5" />
              <span v-else>{{ mistake.id }}</span>
            </div>

            <div class="flex-1 min-w-0">
              <!-- 场景标签 -->
              <div class="flex items-center gap-2 mb-2">
                <span
                  class="px-2 py-0.5 rounded text-xs font-medium"
                  :class="getCategoryClass(mistake.category)"
                >
                  {{ mistake.category }}
                </span>
                <span class="text-xs text-gray-400">
                  难度: {{ mistake.difficulty }}
                </span>
                <span v-if="mistake.corrected" class="px-2 py-0.5 rounded text-xs bg-green-100 dark:bg-green-900/50 text-green-600 dark:text-green-400">
                  已纠正
                </span>
              </div>

              <!-- 场景描述 -->
              <p class="text-gray-700 dark:text-gray-200 mb-3">{{ mistake.context }}</p>

              <!-- 对方言行 -->
              <div class="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 mb-3">
                <p class="text-sm text-blue-600 dark:text-blue-400 mb-1">TA说：</p>
                <p class="text-gray-800 dark:text-white">"{{ mistake.theirWords }}"</p>
              </div>

              <!-- 错误回应 vs 理想回应 -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div class="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                  <p class="text-sm text-red-600 dark:text-red-400 mb-1">❌ 你的回应：</p>
                  <p class="text-gray-700 dark:text-gray-200 text-sm">{{ mistake.badResponse }}</p>
                  <p v-if="mistake.badReason" class="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    原因：{{ mistake.badReason }}
                  </p>
                </div>
                <div class="p-3 rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
                  <p class="text-sm text-green-600 dark:text-green-400 mb-1">✅ 理想回应：</p>
                  <p class="text-gray-700 dark:text-gray-200 text-sm">{{ mistake.goodResponse }}</p>
                </div>
              </div>

              <!-- 关键原则 -->
              <div v-if="mistake.principle" class="p-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/20 mb-4">
                <p class="text-sm text-yellow-600 dark:text-yellow-400 mb-1">💡 关键原则：</p>
                <p class="text-gray-700 dark:text-gray-200 text-sm">{{ mistake.principle }}</p>
              </div>

              <!-- 操作按钮 -->
              <div class="flex items-center gap-4">
                <button
                  v-if="!mistake.corrected"
                  @click="markAsCorrected(mistake)"
                  class="px-4 py-2 rounded-lg bg-green-500 text-white text-sm font-medium hover:bg-green-600 transition-colors"
                >
                  ✓ 我已掌握
                </button>
                <button
                  @click="relearnMistake(mistake)"
                  class="px-4 py-2 rounded-lg bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-sm font-medium hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  再练习一遍
                </button>
                <span class="text-xs text-gray-400 ml-auto">
                  {{ mistake.createdAt }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </transition-group>

      <!-- 空状态 -->
      <div v-if="filteredMistakes.length === 0" class="text-center py-16">
        <div class="text-6xl mb-4">🎉</div>
        <h3 class="text-xl font-bold text-gray-800 dark:text-white mb-2">
          {{ selectedFilter === 'corrected' ? '暂无已纠正的错题' : '太棒了！没有错题了' }}
        </h3>
        <p class="text-gray-500 dark:text-gray-400">
          {{ selectedFilter === 'corrected' ? '去完成一些训练题来积累经验吧' : '继续保持，继续加油！' }}
        </p>
        <button
          v-if="selectedFilter !== 'all'"
          @click="selectedFilter = 'all'"
          class="mt-4 btn-primary"
        >
          查看全部错题
        </button>
      </div>
    </div>

    <!-- 底部统计 -->
    <div class="card bg-gradient-to-r from-blue-500 to-purple-500 text-white">
      <div class="flex items-center justify-between">
        <div>
          <h3 class="text-xl font-bold mb-1">📊 学习报告显示</h3>
          <p class="text-sm opacity-80">
            你在 {{ timeRange }} 内共练习了 {{ totalPractice }} 次，错误率从 {{ oldErrorRate }}% 下降到 {{ newErrorRate }}%
          </p>
        </div>
        <div class="text-4xl">📈</div>
      </div>
    </div>

    <!-- 确认弹窗 -->
    <Teleport to="body">
      <transition name="fade">
        <div
          v-if="showConfirmModal"
          class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          @click.self="showConfirmModal = false"
        >
          <div class="bg-white dark:bg-gray-800 rounded-2xl p-6 max-w-md w-full mx-4 shadow-2xl">
            <h3 class="text-xl font-bold text-gray-800 dark:text-white mb-4">确认纠正</h3>
            <p class="text-gray-600 dark:text-gray-300 mb-6">
              确定已经掌握这道题了吗？下次遇到类似场景你能够做出更好的回应。
            </p>
            <div class="flex gap-4">
              <button
                @click="showConfirmModal = false"
                class="flex-1 btn-secondary"
              >
                再想想
              </button>
              <button
                @click="confirmCorrected"
                class="flex-1 btn-primary"
              >
                确定掌握
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { CheckIcon } from 'lucide-vue-next'
import { useTrainingStore } from '@/stores/training'
import { useToast } from '@/utils/toast'

const store = useTrainingStore()
const toast = useToast()

const selectedFilter = ref('all')
const sortBy = ref('newest')
const showConfirmModal = ref(false)
const selectedMistakeForCorrection = ref<typeof mistakes.value[0] | null>(null)

const filters = [
  { label: '全部', value: 'all' },
  { label: '未纠正', value: 'uncorrected' },
  { label: '已纠正', value: 'corrected' }
]

const mistakeTypes = ref([
  { name: '情绪识别错误', count: 12, color: 'bg-red-500' },
  { name: '回应方式不当', count: 8, color: 'bg-orange-500' },
  { name: '边界意识不足', count: 5, color: 'bg-yellow-500' },
  { name: '沟通技巧欠缺', count: 7, color: 'bg-blue-500' }
])

const weeklyProgress = ref([
  { label: '第1周', correctRate: 0.45, improved: false },
  { label: '第2周', correctRate: 0.52, improved: true },
  { label: '第3周', correctRate: 0.58, improved: true },
  { label: '第4周', correctRate: 0.65, improved: true },
  { label: '本周', correctRate: 0.75, improved: true }
])

const mistakes = ref([
  {
    id: 1,
    category: '暧昧',
    difficulty: 2,
    context: '刚认识不久的对象主动约你吃饭，但在约定时间前突然说临时有事要改期。',
    theirWords: '抱歉啊，今天真的有事，能不能改到明天？',
    badResponse: '好吧，那你明天可别再放我鸽子了。',
    badReason: '语气带有指责和威胁，给对方压力',
    goodResponse: '没关系，工作要紧。明天见，期待哦～',
    principle: '给对方空间，不施压，用积极态度回应',
    corrected: false,
    createdAt: '2024-01-15'
  },
  {
    id: 2,
    category: '冲突',
    difficulty: 3,
    context: '伴侣因为工作压力大向你抱怨，你给了一些建议但对方似乎不太领情。',
    theirWords: '算了，跟你说也没用，你根本不懂。',
    badResponse: '我怎么不懂了？我不也是在给你想办法吗！',
    badReason: '防御性回应，否认对方感受',
    goodResponse: '听起来你真的很辛苦，不想说话也没关系，我就在这陪着你。',
    principle: '先共情后建议，情感支持优先',
    corrected: true,
    createdAt: '2024-01-10'
  },
  {
    id: 3,
    category: '热恋',
    difficulty: 1,
    context: '伴侣发来一张自拍，问你觉得怎么样。',
    theirWords: '你看我今天拍的照片怎么样？',
    badResponse: '还行吧，就普通照片。',
    badReason: '敷衍回应，忽视对方的分享欲',
    goodResponse: '太好看了吧！我的宝怎么拍都美，心里美滋滋的～',
    principle: '积极回应伴侣的分享，满足情感需求',
    corrected: false,
    createdAt: '2024-01-12'
  },
  {
    id: 4,
    category: '平淡',
    difficulty: 2,
    context: '在一起一段时间后，对话变得越来越简短，每天就是早安晚安。',
    theirWords: '嗯。',
    badResponse: '你能不能多说点话啊？这样聊天有什么意思。',
    badReason: '直接批评对方，制造压力',
    goodResponse: '今天工作累不累？要不要周末我们出去走走，换个环境聊聊天？',
    principle: '不批评不指责，用提议代替抱怨',
    corrected: false,
    createdAt: '2024-01-08'
  },
  {
    id: 5,
    category: '修复',
    difficulty: 4,
    context: '争吵后双方冷静下来，你想要修复关系但对方还在生闷气。',
    theirWords: '......',
    badResponse: '好了别生气了，都是我的错还不行吗？',
    badReason: '为了快速和解而敷衍认错，不真诚',
    goodResponse: '我知道你还在生气，我也反思了一下...不管怎样我很在乎你的感受，等你准备好了我们再聊聊可以吗？',
    principle: '真诚表达，给对方时间和空间',
    corrected: true,
    createdAt: '2024-01-05'
  }
])

const totalMistakes = computed(() => mistakes.value.length)
const weeklyNew = computed(() => Math.floor(Math.random() * 5) + 1)
const correctedMistakes = computed(() => mistakes.value.filter(m => m.corrected).length)
const accuracyRate = computed(() => Math.round((correctedMistakes.value / totalMistakes.value) * 100))

const timeRange = ref('过去一个月')
const totalPractice = ref(156)
const oldErrorRate = ref(45)
const newErrorRate = ref(25)

const filteredMistakes = computed(() => {
  let result = [...mistakes.value]
  
  if (selectedFilter.value === 'corrected') {
    result = result.filter(m => m.corrected)
  } else if (selectedFilter.value === 'uncorrected') {
    result = result.filter(m => !m.corrected)
  }
  
  if (sortBy.value === 'newest') {
    result.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
  } else if (sortBy.value === 'oldest') {
    result.sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime())
  } else if (sortBy.value === 'difficulty') {
    result.sort((a, b) => b.difficulty - a.difficulty)
  }
  
  return result
})

function getCategoryClass(category: string): string {
  const map: Record<string, string> = {
    '初识': 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    '暧昧': 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
    '热恋': 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
    '冲突': 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    '平淡': 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
    '修复': 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
  }
  return map[category] || 'bg-gray-100 text-gray-700'
}

function markAsCorrected(mistake: typeof mistakes.value[0]) {
  selectedMistakeForCorrection.value = mistake
  showConfirmModal.value = true
}

function confirmCorrected() {
  if (selectedMistakeForCorrection.value) {
    selectedMistakeForCorrection.value.corrected = true
    toast.success('太棒了！这道题你已经掌握了！')
  }
  showConfirmModal.value = false
  selectedMistakeForCorrection.value = null
}

function relearnMistake(mistake: typeof mistakes.value[0]) {
  toast.info('正在加载练习...')
}

onMounted(async () => {
  await store.fetchMistakes()
})
</script>

<style scoped>
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}

.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(-20px);
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
