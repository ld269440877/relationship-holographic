<template>
  <div
    class="card overflow-hidden"
    :class="{ 'animate-pulse': animation }"
  >
    <!-- 头部骨架 -->
    <div v-if="showHeader" class="flex items-center gap-4 mb-4">
      <div class="w-12 h-12 rounded-xl bg-gray-200 dark:bg-gray-700"></div>
      <div class="flex-1">
        <div class="h-4 w-24 rounded bg-gray-200 dark:bg-gray-700 mb-2"></div>
        <div class="h-3 w-16 rounded bg-gray-200 dark:bg-gray-700"></div>
      </div>
    </div>

    <!-- 内容骨架 -->
    <div class="space-y-3">
      <!-- 段落骨架 -->
      <template v-if="lines === 'auto'">
        <div
          v-for="i in 3"
          :key="i"
          class="h-3 rounded"
          :class="i === 3 ? 'w-2/3' : 'w-full'"
          :style="{ opacity: 1 - (i - 1) * 0.2 }"
        ></div>
      </template>
      <template v-else>
        <div
          v-for="i in lines"
          :key="i"
          class="h-3 rounded"
          :class="i === lines ? 'w-2/3' : 'w-full'"
        ></div>
      </template>
    </div>

    <!-- 图片骨架 -->
    <div
      v-if="showImage"
      class="mt-4 w-full rounded-xl bg-gray-200 dark:bg-gray-700"
      :style="{ height: imageHeight + 'px' }"
    ></div>

    <!-- 按钮骨架 -->
    <div v-if="showButton" class="mt-6 flex gap-3">
      <div class="h-10 w-20 rounded-lg bg-gray-200 dark:bg-gray-700"></div>
      <div class="h-10 w-20 rounded-lg bg-gray-200 dark:bg-gray-700"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  showHeader?: boolean
  showImage?: boolean
  showButton?: boolean
  lines?: 'auto' | number
  imageHeight?: number
  animation?: boolean
}

withDefaults(defineProps<Props>(), {
  showHeader: true,
  showImage: false,
  showButton: false,
  lines: 'auto',
  imageHeight: 200,
  animation: true
})
</script>

<style scoped>
.animate-pulse > * {
  @apply bg-gray-200 dark:bg-gray-700;
}
</style>
