<template>
  <div class="p-8">
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-gray-800 dark:text-white">八阶路径</h1>
      <p class="text-gray-500 dark:text-gray-400 mt-2">从默认沉默到无话不谈的完整进阶指南</p>
    </div>

    <!-- 当前阶段 -->
    <div class="card mb-8 p-6 bg-gradient-to-r from-blue-500 to-purple-500 text-white">
      <div class="flex items-center justify-between">
        <div>
          <p class="text-sm opacity-80">当前阶段</p>
          <h2 class="text-2xl font-bold">第二阶：情绪</h2>
          <p class="mt-2 opacity-90">识别情绪标签并反射，让对方感到被理解</p>
        </div>
        <div class="text-center">
          <p class="text-4xl font-bold">55%</p>
          <p class="text-sm opacity-80">完成度</p>
        </div>
      </div>
    </div>

    <!-- 八阶列表 -->
    <div class="space-y-4">
      <div 
        v-for="(level, index) in levels" 
        :key="index"
        class="card p-6 transition-all"
        :class="{ 'border-2 border-blue-500': level.isCurrent }"
      >
        <div class="flex items-start gap-4">
          <div 
            class="w-12 h-12 rounded-xl flex items-center justify-center font-bold text-lg"
            :class="level.isCompleted ? 'bg-green-500 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'"
          >
            {{ index }}
          </div>
          <div class="flex-1">
            <div class="flex items-center gap-3 mb-2">
              <h3 class="text-xl font-bold text-gray-800 dark:text-white">{{ level.name }}</h3>
              <span v-if="level.isCurrent" class="px-2 py-1 rounded text-xs bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                当前
              </span>
              <span v-if="level.isCompleted" class="px-2 py-1 rounded text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400">
                已完成
              </span>
            </div>
            <p class="text-gray-600 dark:text-gray-300 mb-4">{{ level.description }}</p>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">目标</p>
                <p class="text-gray-800 dark:text-white text-sm">{{ level.goal }}</p>
              </div>
              <div class="p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">工具</p>
                <p class="text-gray-800 dark:text-white text-sm">{{ level.tools }}</p>
              </div>
              <div class="p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">升级条件</p>
                <p class="text-gray-800 dark:text-white text-sm">{{ level.upgradeCondition }}</p>
              </div>
            </div>

            <!-- 进度条 -->
            <div class="mt-4">
              <div class="progress-bar">
                <div class="progress-bar-fill" :style="{ width: level.progress + '%' }"></div>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ level.progress }}%</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const levels = [
  { name: '第零阶：沉默', description: '起点状态，没话题、注意力在自己、感知钝化', goal: '将注意力转向外部', tools: '侦探模式启动', upgradeCondition: '开始关注外部线索', progress: 100, isCompleted: true, isCurrent: false },
  { name: '第一阶：信息', description: '交换基本信息，建立初步连接', goal: '能交换5个以上事实', tools: '侦探+提问(L1)', upgradeCondition: '连续3次对话无冷场>30秒', progress: 100, isCompleted: true, isCurrent: false },
  { name: '第二阶：情绪', description: '识别情绪标签并反射，让对方感到被理解', goal: '识别准确率>50%', tools: '侦探(情绪识别)+诗人', upgradeCondition: '连续5次准确识别主要情绪', progress: 55, isCompleted: false, isCurrent: true },
  { name: '第三阶：感受', description: '让她感到"你和我在一起"', goal: '她主动延长分享3次以上', tools: '共情+提问(退路式)', upgradeCondition: '她说"对，就是这样"', progress: 40, isCompleted: false, isCurrent: false },
  { name: '第四阶：看见', description: '照出她未意识到的细微状态', goal: '她眼睛睁大/呼吸变浅', tools: '侦探(微表情)+诗人', upgradeCondition: '她说"你真的很懂我"', progress: 30, isCompleted: false, isCurrent: false },
  { name: '第五阶：欣赏', description: '用具体真诚的光照亮她', goal: '每周3次以上有效欣赏', tools: '侦探(发现优点)+诗人', upgradeCondition: '她开始主动为你做类似的事', progress: 25, isCompleted: false, isCurrent: false },
  { name: '第六阶：理解', description: '建立她的内在模型，知道根源', goal: '能准确预测她的1个需求', tools: '5W2H+侦探(模式识别)', upgradeCondition: '她向你倾诉从未告诉别人的经历', progress: 15, isCompleted: false, isCurrent: false },
  { name: '第七阶：爱', description: '稳定的行动，不忽冷忽热', goal: '她脆弱时你能稳住', tools: '框架+诗人(行动翻译)', upgradeCondition: '她说"有你在真好"', progress: 10, isCompleted: false, isCurrent: false },
  { name: '第八阶：被爱', description: '安心接收并回馈爱的循环', goal: '能安心接收，不欠债感', tools: '侦探(识别爱意)+诗人', upgradeCondition: '记录被爱的瞬间≥3次/周', progress: 5, isCompleted: false, isCurrent: false },
]
</script>

<style scoped>
.progress-bar {
  @apply h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden;
}
.progress-bar-fill {
  @apply h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500;
}
</style>