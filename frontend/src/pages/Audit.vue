<template>
  <div class="p-4 sm:p-6 lg:p-8">
    <div class="mb-8 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div>
        <p class="mb-2 text-sm font-semibold text-blue-500">Audit Center / 统一审计中心</p>
        <h1 class="text-3xl font-bold text-gray-800 dark:text-white">运营审计时间线</h1>
        <p class="mt-2 max-w-3xl text-gray-500 dark:text-gray-400">
          {{ audit?.principle || '聚合运行、治理、AI、Provider 和调度审计信号，只展示可运营的结构化事实。' }}
        </p>
      </div>
      <div class="flex flex-col gap-2 sm:flex-row">
        <select
          v-model="moduleFilter"
          class="rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm text-gray-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
          @change="load"
        >
          <option value="all">全部模块</option>
          <option value="ai">AI</option>
          <option value="provider">Provider</option>
          <option value="runtime">运行时</option>
          <option value="import">导入</option>
          <option value="governance">发布治理</option>
          <option value="scheduler">调度</option>
          <option value="pipeline">流水线</option>
          <option value="migration">迁移</option>
        </select>
        <button
          class="rounded-lg bg-blue-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-600 disabled:opacity-60"
          :disabled="loading"
          @click="load"
        >
          {{ loading ? '刷新中...' : '刷新审计' }}
        </button>
      </div>
    </div>

    <div class="mb-8 grid grid-cols-2 gap-4 lg:grid-cols-4">
      <SummaryTile label="事件数" :value="audit?.summary.events || 0" />
      <SummaryTile label="需关注" :value="audit?.summary.needs_attention || 0" tone="warn" />
      <SummaryTile label="模块" :value="audit?.filters.modules.length || 0" />
      <SummaryTile label="最新" :value="latestLabel" compact />
    </div>

    <EmptyState
      v-if="loadError && !audit"
      type="error"
      title="审计中心加载失败"
      :description="loadError"
      action-text="重新加载"
      @action="load"
    />

    <div
      v-else-if="loadError"
      class="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-900/60 dark:bg-amber-900/20 dark:text-amber-300"
    >
      {{ loadError }}
    </div>

    <div v-if="!loadError || audit" class="mb-8 grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
        <div class="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 class="text-xl font-bold text-gray-800 dark:text-white">最近审计事件</h2>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">按时间倒序展示，只读，不改变任何状态。</p>
          </div>
          <ScrollText class="h-5 w-5 text-blue-500" />
        </div>

        <div class="overflow-hidden rounded-lg border border-gray-100 dark:border-gray-700">
          <div class="hidden grid-cols-[140px_120px_120px_minmax(0,1fr)_150px] gap-3 bg-gray-50 px-4 py-3 text-xs font-semibold text-gray-500 dark:bg-gray-900/60 md:grid">
            <span>时间</span>
            <span>模块</span>
            <span>状态</span>
            <span>摘要</span>
            <span>操作者</span>
          </div>
          <div class="divide-y divide-gray-100 dark:divide-gray-700">
            <button
              v-for="event in audit?.events || []"
              :key="event.id"
              class="grid w-full grid-cols-1 gap-2 px-4 py-3 text-left transition-colors hover:bg-gray-50 dark:hover:bg-gray-900/40 md:grid-cols-[140px_120px_120px_minmax(0,1fr)_150px] md:items-center md:gap-3"
              @click="selected = event"
            >
              <span class="text-xs text-gray-500 dark:text-gray-400">{{ formatTime(event.created_at) }}</span>
              <span class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-200">
                <component :is="moduleIcon(event.module)" class="h-4 w-4 shrink-0 text-gray-400" />
                {{ moduleName(event.module) }}
              </span>
              <span class="w-fit rounded px-2 py-1 text-xs" :class="statusClass(event.status)">
                {{ statusName(event.status) }}
              </span>
              <span class="min-w-0 text-sm text-gray-600 dark:text-gray-300">
                <span class="block truncate">{{ event.summary || event.action }}</span>
                <span class="mt-1 block truncate text-xs text-gray-400">{{ event.source }} · {{ event.action }}</span>
              </span>
              <span class="truncate text-xs text-gray-500 dark:text-gray-400">{{ event.actor }}</span>
            </button>
            <div v-if="audit && audit.events.length === 0" class="py-10 text-center text-sm text-gray-400">
              当前筛选没有审计事件。
            </div>
            <div v-if="loading && !audit" class="py-10 text-center text-sm text-gray-400">加载审计中心...</div>
          </div>
        </div>
      </section>

      <aside class="space-y-6">
        <section class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <div class="mb-4 flex items-center justify-between gap-3">
            <h2 class="text-lg font-bold text-gray-800 dark:text-white">下一步动作</h2>
            <ListChecks class="h-5 w-5 text-emerald-500" />
          </div>
          <div class="space-y-3">
            <div v-for="item in audit?.next_actions || []" :key="item.action" class="rounded-lg bg-gray-50 p-3 dark:bg-gray-900/50">
              <div class="mb-1 flex items-center justify-between gap-3">
                <p class="text-sm font-semibold text-gray-800 dark:text-white">{{ item.action }}</p>
                <span class="text-xs uppercase text-gray-500">{{ item.priority }}</span>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ item.reason }}</p>
            </div>
          </div>
        </section>

        <section class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <h2 class="mb-4 text-lg font-bold text-gray-800 dark:text-white">分布</h2>
          <Distribution title="模块" :items="audit?.filters.modules || []" />
          <Distribution class="mt-5" title="状态" :items="audit?.filters.statuses || []" />
          <Distribution class="mt-5" title="级别" :items="audit?.filters.severities || []" />
        </section>

        <section v-if="selected" class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <div class="mb-4 flex items-start justify-between gap-3">
            <div>
              <h2 class="text-lg font-bold text-gray-800 dark:text-white">事件详情</h2>
              <p class="mt-1 break-all text-xs text-gray-500">{{ selected.id }}</p>
            </div>
            <button class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 dark:bg-gray-700 dark:text-gray-300" @click="selected = null">关闭</button>
          </div>
          <div class="space-y-2 text-sm">
            <DetailRow label="对象" :value="`${selected.target.type}:${selected.target.id ?? '-'}`" />
            <DetailRow label="来源" :value="selected.source" />
            <DetailRow label="动作" :value="selected.action" />
            <DetailRow label="级别" :value="selected.severity" />
          </div>
          <pre class="mt-4 max-h-64 overflow-auto rounded-lg bg-gray-950 p-3 text-xs text-gray-100">{{ prettyDetails }}</pre>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref } from 'vue'
import { Bot, Boxes, Database, ListChecks, RadioTower, ScrollText, ShieldCheck, TimerReset, Workflow } from 'lucide-vue-next'
import { analyticsApi } from '@/utils/api'
import EmptyState from '@/components/EmptyState.vue'
import type { AuditCenter, AuditCenterEvent } from '@/utils/api'

const audit = ref<AuditCenter | null>(null)
const selected = ref<AuditCenterEvent | null>(null)
const loading = ref(false)
const loadError = ref('')
const moduleFilter = ref('all')

const latestLabel = computed(() => audit.value?.summary.latest_at ? formatTime(audit.value.summary.latest_at) : '-')
const prettyDetails = computed(() => selected.value ? JSON.stringify(selected.value.details, null, 2) : '')

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    audit.value = await analyticsApi.auditCenter(100, moduleFilter.value)
    selected.value = audit.value.events[0] || null
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '审计中心加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

function formatTime(value?: string | null) {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function moduleName(module: string) {
  const names: Record<string, string> = {
    ai: 'AI',
    provider: 'Provider',
    runtime: '运行时',
    import: '导入',
    governance: '治理',
    scheduler: '调度',
    pipeline: '流水线',
    migration: '迁移',
  }
  return names[module] || module
}

function moduleIcon(module: string) {
  const icons: Record<string, unknown> = {
    ai: Bot,
    provider: RadioTower,
    runtime: ScrollText,
    import: Database,
    governance: ShieldCheck,
    scheduler: TimerReset,
    pipeline: Workflow,
    migration: Boxes,
  }
  return icons[module] || ScrollText
}

function statusName(status: string) {
  const names: Record<string, string> = {
    passed: '通过',
    failed: '失败',
    blocked: '阻断',
    planned: '预演',
    needs_attention: '关注',
  }
  return names[status] || status
}

function statusClass(status: string) {
  if (status === 'passed') return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
  if (status === 'planned') return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
  if (status === 'failed' || status === 'blocked') return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
  return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
}

const SummaryTile = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: [String, Number], required: true },
    tone: { type: String, default: 'normal' },
    compact: { type: Boolean, default: false },
  },
  setup(props) {
    return () => h('div', { class: 'rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800' }, [
      h('p', { class: 'text-xs text-gray-500 dark:text-gray-400' }, props.label),
      h('p', {
        class: [
          'mt-1 truncate font-bold',
          props.compact ? 'text-base' : 'text-2xl',
          props.tone === 'warn' ? 'text-amber-600 dark:text-amber-300' : 'text-gray-800 dark:text-white',
        ].join(' '),
      }, String(props.value)),
    ])
  },
})

const Distribution = defineComponent({
  props: {
    title: { type: String, required: true },
    items: { type: Array as () => Array<{ name: string; count: number; rate: number }>, required: true },
  },
  setup(props) {
    return () => h('div', [
      h('p', { class: 'mb-2 text-sm font-semibold text-gray-700 dark:text-gray-200' }, props.title),
      h('div', { class: 'space-y-2' }, props.items.slice(0, 6).map((item) => h('div', [
        h('div', { class: 'mb-1 flex items-center justify-between gap-3 text-xs text-gray-500 dark:text-gray-400' }, [
          h('span', { class: 'truncate' }, item.name),
          h('span', item.count),
        ]),
        h('div', { class: 'h-2 overflow-hidden rounded bg-gray-100 dark:bg-gray-700' }, [
          h('div', { class: 'h-full rounded bg-blue-500', style: { width: `${Math.max(4, Math.min(100, item.rate))}%` } }),
        ]),
      ]))),
    ])
  },
})

const DetailRow = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: String, required: true },
  },
  setup(props) {
    return () => h('div', { class: 'flex items-start justify-between gap-3 rounded bg-gray-50 p-2 dark:bg-gray-900/50' }, [
      h('span', { class: 'shrink-0 text-gray-500 dark:text-gray-400' }, props.label),
      h('span', { class: 'min-w-0 break-all text-right text-gray-800 dark:text-gray-200' }, props.value),
    ])
  },
})

onMounted(load)
</script>
