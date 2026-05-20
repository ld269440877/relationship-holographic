import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

// 路由名称映射
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/pages/Dashboard.vue'),
    meta: { title: '仪表盘' }
  },
  {
    path: '/trainer',
    name: 'Trainer',
    component: () => import('@/pages/Trainer.vue'),
    meta: { title: '训练中心' }
  },
  {
    path: '/trainer-ai',
    name: 'TrainerAI',
    component: () => import('@/pages/TrainerAI.vue'),
    meta: { title: 'AI训练伴侣', fullscreen: true }
  },
  {
    path: '/daily',
    name: 'Daily',
    component: () => import('@/pages/Daily.vue'),
    meta: { title: '每日训练' }
  },
  {
    path: '/mistakes',
    name: 'Mistakes',
    component: () => import('@/pages/Mistakes.vue'),
    meta: { title: '错题本' }
  },
  {
    path: '/resources',
    name: 'Resources',
    component: () => import('@/pages/Resources.vue'),
    meta: { title: '资源海洋' }
  },
  {
    path: '/path',
    name: 'Path',
    component: () => import('@/pages/Path.vue'),
    meta: { title: '八阶路径' }
  },
  {
    path: '/journal',
    name: 'Journal',
    component: () => import('@/pages/Journal.vue'),
    meta: { title: '复盘日记' }
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/pages/Profile.vue'),
    meta: { title: '我的档案' }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/pages/Settings.vue'),
    meta: { title: '设置' }
  },
  {
    path: '/onboarding',
    name: 'Onboarding',
    component: () => import('@/pages/Onboarding.vue'),
    meta: { title: '欢迎引导', fullscreen: true }
  },
  // 重定向
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局前置守卫 - 路由开始
router.beforeEach((to, _from, next) => {
  // 更新页面标题
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} - 关系动力学全息` : '关系动力学全息'

  // 检查是否需要引导
  const hasCompletedOnboarding = localStorage.getItem('hasCompletedOnboarding')
  if (to.path !== '/onboarding' && !hasCompletedOnboarding) {
    next({ name: 'Onboarding' })
    return
  }

  next()
})

// 全局后置守卫 - 路由结束
router.afterEach((_to, _from) => {
  // 路由切换后的操作（如滚动到顶部）
  window.scrollTo({ top: 0, behavior: 'smooth' })
})

export default router
