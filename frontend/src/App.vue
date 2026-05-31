<template>
  <div class="h-full flex">
    <!-- 侧边栏 - 非全屏路由显示 -->
    <aside
      v-if="!isFullscreen"
      class="hidden md:flex w-64 bg-apple-gray-50 dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex-col"
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
      class="mb-20 h-[calc(100%-5rem)] flex-1 min-w-0 overflow-auto bg-gray-50 dark:bg-gray-900 md:mb-0 md:h-auto"
      :class="{ 'w-full': isFullscreen, 'pb-20 md:pb-0': !isFullscreen }"
    >
      <header
        v-if="!isFullscreen"
        class="sticky top-0 z-20 flex items-center justify-between border-b border-gray-200 bg-white/95 px-4 py-3 backdrop-blur dark:border-gray-700 dark:bg-gray-900/95 md:hidden"
      >
        <div class="min-w-0">
          <p class="truncate text-sm font-semibold text-gray-800 dark:text-white">关系动力学全息</p>
          <p class="truncate text-xs text-gray-500 dark:text-gray-400">{{ currentTitle }}</p>
        </div>
        <button
          class="rounded-lg bg-gray-100 p-2 text-gray-600 transition-colors hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          aria-label="打开导航"
          @click="mobileMenuOpen = true"
        >
          <Menu class="h-5 w-5" />
        </button>
      </header>

      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <nav
      v-if="!isFullscreen"
      class="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-gray-200 bg-white/95 px-2 py-2 backdrop-blur dark:border-gray-700 dark:bg-gray-900/95 md:hidden"
      aria-label="移动端主导航"
    >
      <button
        v-for="item in mobilePrimaryItems"
        :key="item.path"
        class="flex min-w-0 flex-col items-center gap-1 rounded-lg px-1 py-1.5 text-[11px] transition-colors"
        :class="$route.path === item.path ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-300' : 'text-gray-500 dark:text-gray-400'"
        @click="navigateTo(item.path)"
      >
        <component :is="item.icon" class="h-5 w-5" />
        <span class="w-full truncate text-center">{{ item.name }}</span>
      </button>
    </nav>

    <Teleport to="body">
      <div v-if="mobileMenuOpen" class="fixed inset-0 z-40 md:hidden" @click.self="mobileMenuOpen = false">
        <div class="absolute inset-0 bg-black/40"></div>
        <div class="absolute bottom-0 left-0 right-0 max-h-[78vh] overflow-auto rounded-t-2xl bg-white p-4 shadow-2xl dark:bg-gray-900">
          <div class="mb-4 flex items-center justify-between">
            <div>
              <p class="font-bold text-gray-800 dark:text-white">全部导航</p>
              <p class="text-xs text-gray-500 dark:text-gray-400">训练、知识、路径和进化中心</p>
            </div>
            <button
              class="rounded-lg bg-gray-100 p-2 text-gray-600 dark:bg-gray-800 dark:text-gray-300"
              aria-label="关闭导航"
              @click="mobileMenuOpen = false"
            >
              <X class="h-5 w-5" />
            </button>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <button
              v-for="item in allNavItems"
              :key="item.path"
              class="flex min-w-0 items-center gap-3 rounded-xl border border-gray-100 bg-gray-50 p-3 text-left text-gray-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
              :class="$route.path === item.path ? 'border-blue-200 bg-blue-50 text-blue-600 dark:border-blue-800 dark:bg-blue-900/30 dark:text-blue-300' : ''"
              @click="navigateTo(item.path)"
            >
              <component :is="item.icon" class="h-5 w-5 shrink-0" />
              <span class="truncate text-sm font-medium">{{ item.name }}</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Toast 通知层 -->
    <ToastContainer />
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  LayoutDashboard,
  Brain,
  Library,
  Wrench,
  Route,
  BookOpen,
  Compass,
  User,
  Target,
  ListTodo,
  AlertTriangle,
  Settings,
  Sparkles,
  Orbit,
  Network,
  BarChart3,
  ShieldCheck,
  ScrollText,
  Menu,
  X
} from 'lucide-vue-next'
import ToastContainer from '@/components/ToastContainer.vue'
import NavItem from '@/components/NavItem.vue'

const router = useRouter()
const route = useRoute()
const mobileMenuOpen = ref(false)

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
  { path: '/journal', name: '复盘日记', icon: ListTodo, badge: null },
  { path: '/evolution', name: '进化中心', icon: Orbit, badge: 'Live' },
  { path: '/analytics', name: '分析中心', icon: BarChart3, badge: 'Audit' },
  { path: '/audit', name: '审计中心', icon: ScrollText, badge: 'Ops' },
  { path: '/governance', name: '发布治理', icon: ShieldCheck, badge: 'Gate' }
]

// 个人导航项
const personalNavItems = [
  { path: '/resources', name: '资源海洋', icon: Library, badge: null },
  { path: '/expression', name: '表达工具箱', icon: Wrench, badge: 'Tools' },
  { path: '/surf', name: '浏览冲浪', icon: Compass, badge: 'Source' },
  { path: '/knowledge', name: '知识中枢', icon: BookOpen, badge: 'DB' },
  { path: '/framework', name: '元基础', icon: Network, badge: '0/1' },
  { path: '/path', name: '八阶路径', icon: Route, badge: null },
  { path: '/profile', name: '我的档案', icon: User, badge: null },
  { path: '/settings', name: '设置', icon: Settings, badge: null }
]

const allNavItems = computed(() => [
  ...mainNavItems,
  ...trainingNavItems,
  ...personalNavItems,
])

const mobilePrimaryItems = computed(() => [
  mainNavItems[0],
  mainNavItems[2],
  trainingNavItems[0],
  trainingNavItems[1],
  personalNavItems[4],
])

const currentTitle = computed(() => route.meta.title as string || '关系训练系统')

function navigateTo(path: string) {
  mobileMenuOpen.value = false
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
