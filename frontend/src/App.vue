<template>
  <div class="h-full flex">
    <!-- 侧边栏 - 非全屏路由显示 -->
    <aside
      v-if="!isFullscreen"
      class="w-64 bg-apple-gray-50 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col"
    >
      <!-- Logo -->
      <div class="p-6 border-b border-gray-200 dark:border-gray-700">
        <h1 class="text-xl font-bold text-gray-800 dark:text-white">关系动力学全息</h1>
        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">两性关系感知训练系统</p>
      </div>

      <!-- 导航分组 -->
      <nav class="flex-1 p-4 overflow-auto">
        <!-- 主要功能 -->
        <div class="mb-6">
          <p class="px-4 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-2">
            主要功能
          </p>
          <ul class="space-y-1">
            <NavItem
              v-for="item in mainNavItems"
              :key="item.path"
              :item="item"
              :isActive="$route.path === item.path"
              @click="navigateTo(item.path)"
            />
          </ul>
        </div>

        <!-- 训练模块 -->
        <div class="mb-6">
          <p class="px-4 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-2">
            训练
          </p>
          <ul class="space-y-1">
            <NavItem
              v-for="item in trainingNavItems"
              :key="item.path"
              :item="item"
              :isActive="$route.path === item.path"
              @click="navigateTo(item.path)"
            />
          </ul>
        </div>

        <!-- 个人 -->
        <div>
          <p class="px-4 text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-2">
            个人
          </p>
          <ul class="space-y-1">
            <NavItem
              v-for="item in personalNavItems"
              :key="item.path"
              :item="item"
              :isActive="$route.path === item.path"
              @click="navigateTo(item.path)"
            />
          </ul>
        </div>
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
    <main
      class="flex-1 bg-gray-50 dark:bg-gray-900 overflow-auto"
      :class="{ 'w-full': isFullscreen }"
    >
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
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  LayoutDashboard,
  Brain,
  Library,
  Route,
  BookOpen,
  User,
  Target,
  ListTodo,
  AlertTriangle,
  Settings,
  Sparkles
} from 'lucide-vue-next'
import ToastContainer from '@/components/ToastContainer.vue'
import NavItem from '@/components/NavItem.vue'

const router = useRouter()
const route = useRoute()

// 判断当前路由是否为全屏模式
const isFullscreen = computed(() => {
  return route.meta.fullscreen === true
})

// 主要导航项
const mainNavItems = [
  { path: '/', name: '仪表盘', icon: LayoutDashboard, badge: null },
  { path: '/daily', name: '每日训练', icon: Target, badge: '🔥 7天' },
  { path: '/trainer', name: '训练中心', icon: Brain, badge: null }
]

// 训练模块导航项
const trainingNavItems = [
  { path: '/trainer-ai', name: 'AI伴侣', icon: Sparkles, badge: 'New' },
  { path: '/mistakes', name: '错题本', icon: AlertTriangle, badge: null },
  { path: '/journal', name: '复盘日记', icon: ListTodo, badge: null }
]

// 个人导航项
const personalNavItems = [
  { path: '/resources', name: '资源海洋', icon: Library, badge: null },
  { path: '/path', name: '八阶路径', icon: Route, badge: null },
  { path: '/profile', name: '我的档案', icon: User, badge: null },
  { path: '/settings', name: '设置', icon: Settings, badge: null }
]

function navigateTo(path: string) {
  router.push(path)
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
