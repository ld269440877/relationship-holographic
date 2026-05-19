import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Dashboard',
    component: () => import('@/pages/Dashboard.vue'),
  },
  {
    path: '/trainer',
    name: 'Trainer',
    component: () => import('@/pages/Trainer.vue'),
  },
  {
    path: '/resources',
    name: 'Resources',
    component: () => import('@/pages/Resources.vue'),
  },
  {
    path: '/path',
    name: 'Path',
    component: () => import('@/pages/Path.vue'),
  },
  {
    path: '/journal',
    name: 'Journal',
    component: () => import('@/pages/Journal.vue'),
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/pages/Profile.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router