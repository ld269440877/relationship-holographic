<template>
  <div class="h-full flex">
    <!-- 侧边栏 -->
    <aside class="w-64 bg-apple-gray-50 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      <!-- Logo -->
      <div class="p-6 border-b border-gray-200 dark:border-gray-700">
        <h1 class="text-xl font-bold text-gray-800 dark:text-white">关系动力学全息</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">两性关系感知训练系统</p>
      </div>

      <!-- 导航 -->
      <nav class="flex-1 p-4">
        <ul class="space-y-2">
          <li v-for="item in navItems" :key="item.path">
            <router-link
              :to="item.path"
              class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all"
              :class="[
                $route.path === item.path
                  ? 'bg-blue-500 text-white'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              ]"
            >
              <component :is="item.icon" class="w-5 h-5" />
              <span>{{ item.name }}</span>
            </router-link>
          </li>
        </ul>
      </nav>

      <!-- 底部信息 -->
      <div class="p-4 border-t border-gray-200 dark:border-gray-700">
        <div class="text-xs text-gray-400 dark:text-gray-500">
          <p>版本 1.0.0</p>
          <p class="mt-1">持续进化中...</p>
        </div>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="flex-1 bg-gray-50 dark:bg-gray-900 overflow-auto">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Toast 通知层 -->
    <ToastContainer />
  </div>
</template>

<script setup lang="ts">
import { LayoutDashboard, Brain, Library, Route, BookOpen, User } from 'lucide-vue-next'
import ToastContainer from '@/components/ToastContainer.vue'

const navItems = [
  { path: '/', name: '仪表盘', icon: LayoutDashboard },
  { path: '/trainer', name: '训练中心', icon: Brain },
  { path: '/resources', name: '资源海洋', icon: Library },
  { path: '/path', name: '八阶路径', icon: Route },
  { path: '/journal', name: '复盘日记', icon: BookOpen },
  { path: '/profile', name: '我的档案', icon: User },
]
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
