<template>
  <div class="p-4 sm:p-6 lg:p-8">
    <div class="mb-8 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
      <div>
        <p class="mb-2 text-sm font-semibold text-blue-500">Analytics Center / 质量分析中心</p>
        <h1 class="text-3xl font-bold text-gray-800 dark:text-white">系统质量与历史趋势</h1>
        <p class="mt-2 max-w-3xl text-gray-500 dark:text-gray-400">
          {{ center?.principle || '聚合 AI、Gold Set、导入质量、向量召回和训练趋势，只展示审计指标。' }}
        </p>
      </div>
      <button
        class="w-full rounded-lg bg-blue-500 px-4 py-2 text-white transition-colors hover:bg-blue-600 disabled:opacity-60 sm:w-auto"
        :disabled="loading"
        @click="load"
      >
        {{ loading ? '刷新中...' : '刷新指标' }}
      </button>
    </div>

    <EmptyState
      v-if="loadError && !center"
      type="error"
      title="分析中心加载失败"
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

    <template v-if="!loadError || center">
    <div class="mb-8 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
      <div
        v-for="metric in center?.scorecard || []"
        :key="metric.id"
        class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
      >
        <div class="mb-3 flex items-start justify-between gap-3">
          <div class="min-w-0">
            <p class="truncate text-sm text-gray-500 dark:text-gray-400">{{ metric.label }}</p>
            <p class="mt-1 text-3xl font-bold" :class="metricClass(metric.status)">{{ formatValue(metric) }}</p>
          </div>
          <span class="rounded px-2 py-1 text-xs" :class="statusBadge(metric.status)">
            {{ metric.status === 'passed' ? '通过' : '关注' }}
          </span>
        </div>
        <div class="h-2 overflow-hidden rounded bg-gray-100 dark:bg-gray-700">
          <div class="h-full rounded" :class="metric.status === 'passed' ? 'bg-emerald-500' : 'bg-amber-500'" :style="{ width: `${metricProgress(metric)}%` }"></div>
        </div>
        <p class="mt-2 text-xs text-gray-500 dark:text-gray-400">目标 {{ metricTarget(metric) }} · 差距 {{ oneDecimal(metric.gap) }}</p>
      </div>
    </div>

    <div class="mb-8 grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
      <div class="card">
        <div class="mb-5 flex items-center justify-between gap-3">
          <div>
            <h2 class="text-xl font-bold text-gray-800 dark:text-white">历史状态线</h2>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">所有关键质量域按同一阈值模型归一化展示。</p>
          </div>
          <Activity class="h-5 w-5 text-blue-500" />
        </div>
        <div class="space-y-4">
          <div v-for="point in center?.timeline || []" :key="point.id">
            <div class="mb-1 flex items-center justify-between gap-3 text-sm">
              <span class="font-medium text-gray-700 dark:text-gray-200">{{ point.label }}</span>
              <span :class="metricClass(point.status)">{{ point.value }}</span>
            </div>
            <div class="h-3 overflow-hidden rounded bg-gray-100 dark:bg-gray-700">
              <div class="h-full rounded" :class="point.status === 'passed' ? 'bg-emerald-500' : 'bg-orange-500'" :style="{ width: `${timelineWidth(point.value)}%` }"></div>
            </div>
          </div>
          <div v-if="!loading && !center?.timeline.length" class="py-8 text-center text-sm text-gray-400">暂无历史指标。</div>
        </div>
      </div>

      <div class="card">
        <div class="mb-5 flex items-center justify-between gap-3">
          <div>
            <h2 class="text-xl font-bold text-gray-800 dark:text-white">告警队列</h2>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ center?.alerts.length || 0 }} 个待处理质量信号</p>
          </div>
          <BellRing class="h-5 w-5 text-amber-500" />
        </div>
        <div class="space-y-3">
          <div
            v-for="alert in center?.alerts || []"
            :key="alert.metric + alert.title"
            class="rounded-lg border p-3"
            :class="alertClass(alert.priority)"
          >
            <div class="mb-1 flex items-center justify-between gap-3">
              <p class="font-semibold text-gray-800 dark:text-white">{{ alert.title }}</p>
              <span class="text-xs uppercase text-gray-500">{{ alert.priority }}</span>
            </div>
            <p class="text-sm text-gray-500 dark:text-gray-400">{{ alert.detail }}</p>
          </div>
          <div v-if="center && center.alerts.length === 0" class="rounded-lg bg-emerald-50 p-4 text-sm text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300">
            当前没有高优先级告警。
          </div>
          <div v-if="!center && loading" class="py-8 text-center text-sm text-gray-400">加载分析中心...</div>
        </div>
      </div>
    </div>

    <div v-if="center" class="grid grid-cols-1 gap-6 xl:grid-cols-2">
      <section class="card">
        <PanelTitle title="AI 质量与 Provider" subtitle="成功率、失败率、fallback 和配置诊断" :icon="Cpu" />
        <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
          <MetricPill label="运行" :value="center.sections.ai_quality.summary.runs" />
          <MetricPill label="成功率" :value="`${center.sections.ai_quality.summary.success_rate}%`" />
          <MetricPill label="降级率" :value="`${center.sections.ai_quality.summary.fallback_rate}%`" />
          <MetricPill label="失败率" :value="`${center.sections.ai_quality.summary.provider_failure_rate}%`" />
        </div>
        <div class="mt-5 rounded-lg bg-gray-50 p-4 dark:bg-gray-800">
          <div class="mb-2 flex items-center justify-between gap-3">
            <p class="font-semibold text-gray-800 dark:text-white">Provider 风险</p>
            <span class="rounded bg-gray-200 px-2 py-1 text-xs text-gray-600 dark:bg-gray-700 dark:text-gray-300">{{ center.sections.provider.risk_level }}</span>
          </div>
          <div class="space-y-2">
            <p v-for="item in diagnostics" :key="item" class="text-sm text-gray-500 dark:text-gray-400">{{ item }}</p>
          </div>
        </div>
        <div class="mt-4 rounded-lg border border-gray-100 p-4 dark:border-gray-700">
          <div class="mb-3 flex items-start justify-between gap-3">
            <div>
              <p class="font-semibold text-gray-800 dark:text-white">Provider Success Contract</p>
              <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ center.sections.provider.success_contract.principle }}</p>
            </div>
            <span class="shrink-0 rounded px-2 py-1 text-xs" :class="successContractClass(center.sections.provider.success_contract.quality_gate)">
              {{ center.sections.provider.success_contract.quality_gate.structured_success_ok ? 'stable' : 'watch' }}
            </span>
          </div>
          <div class="grid grid-cols-2 gap-2 md:grid-cols-4">
            <MetricPill label="结构成功" :value="`${center.sections.provider.success_contract.summary.structured_success_rate}%`" />
            <MetricPill label="Raw Text" :value="`${center.sections.provider.success_contract.summary.raw_text_rate}%`" />
            <MetricPill label="Provider Fail" :value="`${center.sections.provider.success_contract.summary.provider_failure_rate}%`" />
            <MetricPill label="可恢复" :value="`${center.sections.provider.success_contract.summary.recoverable_success_rate}%`" />
          </div>
          <div class="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2">
            <div
              v-for="gap in center.sections.provider.success_contract.contract_gaps.slice(0, 4)"
              :key="gap.id"
              class="rounded bg-gray-50 p-3 dark:bg-gray-800"
            >
              <div class="flex items-center justify-between gap-2">
                <p class="text-sm font-semibold text-gray-800 dark:text-white">{{ gap.id }}</p>
                <span class="text-xs uppercase text-gray-500">{{ gap.severity }}</span>
              </div>
              <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ gap.fix }}</p>
            </div>
          </div>
          <div class="mt-3 space-y-2">
            <div
              v-for="row in center.sections.provider.success_contract.task_matrix.slice(0, 3)"
              :key="row.task_type"
              class="rounded bg-gray-50 p-2 dark:bg-gray-800"
            >
              <div class="flex flex-wrap items-center justify-between gap-2 text-xs">
                <span class="font-semibold text-gray-700 dark:text-gray-200">{{ row.task_type }}</span>
                <span class="text-gray-500">runs {{ row.runs }} · success {{ row.structured_success_rate }}% · raw {{ row.raw_text_rate }}%</span>
              </div>
            </div>
          </div>
        </div>
        <div class="mt-4 rounded-lg border border-gray-100 p-4 dark:border-gray-700">
          <div class="mb-3 flex items-start justify-between gap-3">
            <div>
              <p class="font-semibold text-gray-800 dark:text-white">Live Probe Readiness</p>
              <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ center.sections.provider.probe_readiness.principle }}</p>
            </div>
            <span class="shrink-0 rounded px-2 py-1 text-xs" :class="probeStatusClass(center.sections.provider.probe_readiness.status)">
              {{ center.sections.provider.probe_readiness.status }}
            </span>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <MetricPill label="Configured" :value="center.sections.provider.probe_readiness.configured ? 'yes' : 'no'" />
            <MetricPill label="Live Enabled" :value="center.sections.provider.probe_readiness.live_probe_enabled ? 'yes' : 'no'" />
          </div>
          <div class="mt-3 space-y-2">
            <p v-for="blocker in center.sections.provider.probe_readiness.blockers.slice(0, 3)" :key="blocker.id" class="rounded bg-amber-50 p-2 text-xs text-amber-700 dark:bg-amber-900/20 dark:text-amber-300">
              {{ blocker.id }} · {{ blocker.detail }}
            </p>
          </div>
          <div class="mt-3 space-y-2">
            <div v-for="step in center.sections.provider.probe_readiness.runbook.slice(0, 4)" :key="step.step" class="rounded bg-gray-50 p-2 dark:bg-gray-800">
              <p class="text-xs font-semibold text-gray-700 dark:text-gray-200">{{ step.step }} · {{ step.title }}</p>
              <p class="mt-1 break-all text-xs text-gray-500 dark:text-gray-400">{{ step.command }}</p>
            </div>
          </div>
        </div>
        <div class="mt-4 rounded-lg border border-gray-100 p-4 dark:border-gray-700">
          <div class="mb-3 flex items-start justify-between gap-3">
            <div>
              <p class="font-semibold text-gray-800 dark:text-white">Provider Failure Playbook</p>
              <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ center.sections.provider.failure_playbook.principle }}</p>
            </div>
            <span class="shrink-0 rounded px-2 py-1 text-xs" :class="providerRiskClass(center.sections.provider.failure_playbook.risk_level)">
              {{ center.sections.provider.failure_playbook.risk_level }}
            </span>
          </div>
          <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div
              v-for="item in center.sections.provider.failure_playbook.root_cause_matrix.slice(0, 4)"
              :key="item.id"
              class="rounded bg-gray-50 p-3 dark:bg-gray-800"
            >
              <div class="mb-2 flex items-start justify-between gap-3">
                <p class="text-sm font-semibold text-gray-800 dark:text-white">{{ item.root_cause }}</p>
                <span class="shrink-0 text-xs uppercase text-gray-500">{{ item.severity }}</span>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ item.operator_action }}</p>
              <p class="mt-2 break-all text-xs text-blue-600 dark:text-blue-300">{{ item.regression_case }}</p>
            </div>
          </div>
          <div class="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2">
            <div
              v-for="step in center.sections.provider.failure_playbook.runbook.slice(0, 4)"
              :key="step.step"
              class="rounded bg-gray-50 p-2 dark:bg-gray-800"
            >
              <p class="text-xs font-semibold text-gray-700 dark:text-gray-200">{{ step.step }} · {{ step.title }}</p>
              <p class="mt-1 break-all text-xs text-gray-500 dark:text-gray-400">{{ step.command }}</p>
            </div>
          </div>
        </div>
        <ActionList class="mt-5" :items="center.sections.ai_quality.next_actions" />
      </section>

      <section class="card">
        <PanelTitle title="Gold Set 校准" subtitle="专家覆盖、一致率、冲突队列和严格门禁" :icon="BadgeCheck" />
        <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
          <MetricPill label="开放冲突" :value="center.sections.gold_set.open_conflicts" />
          <MetricPill label="Gold 样本" :value="summaryValue(center.sections.gold_set.summary, 'gold_samples')" />
          <MetricPill label="专家复核" :value="summaryValue(center.sections.gold_set.summary, 'expert_reviews')" />
          <MetricPill label="覆盖率" :value="`${summaryValue(center.sections.gold_set.summary, 'expert_coverage_rate')}%`" />
        </div>
        <div class="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2">
          <GateRow label="严格校准" :passed="Boolean(center.sections.gold_set.quality_gates.ready_for_strict_calibration)" />
          <GateRow label="冲突闭环" :passed="center.sections.gold_set.open_conflicts === 0" />
        </div>
        <ActionList class="mt-5" :items="center.sections.gold_set.next_actions" />
      </section>

      <section class="card">
        <PanelTitle title="导入质量与来源治理" subtitle="历史 issue、字段质量和批次债务" :icon="Database" />
        <div class="grid grid-cols-2 gap-3 md:grid-cols-3">
          <MetricPill label="质量分" :value="rounded(center.sections.import_quality.quality_score)" />
          <MetricPill label="样本" :value="summaryValue(center.sections.import_quality.totals, 'samples')" />
          <MetricPill label="资源" :value="summaryValue(center.sections.import_quality.totals, 'resources')" />
        </div>
        <div class="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2">
          <DebtTile v-for="debt in importDebt" :key="debt.name" :label="debt.name" :value="debt.value" />
        </div>
      </section>

      <section class="card">
        <PanelTitle title="向量召回与训练趋势" subtitle="语义检索健康度和跨会话长期能力画像" :icon="LineChart" />
        <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
          <MetricPill label="召回率" :value="`${summaryValue(center.sections.vector_recall.summary, 'recall_rate')}%`" />
          <MetricPill label="会话" :value="center.sections.training_trends.summary.sessions" />
          <MetricPill label="轮次" :value="center.sections.training_trends.summary.turns" />
          <MetricPill label="修复指数" :value="center.sections.training_trends.summary.repair_index" />
        </div>
        <div class="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-5">
          <DeltaTile label="信任" :value="center.sections.training_trends.average_state_delta.trust" />
          <DeltaTile label="压力" :value="center.sections.training_trends.average_state_delta.stress" reverse />
          <DeltaTile label="边界压力" :value="center.sections.training_trends.average_state_delta.boundary" reverse />
          <DeltaTile label="边界安全" :value="center.sections.training_trends.average_state_delta.boundary_safety" />
          <DeltaTile label="连接" :value="center.sections.training_trends.average_state_delta.connection" />
        </div>
        <div class="mt-5 space-y-2">
          <div
            v-for="session in center.sections.training_trends.session_trend.slice(0, 4)"
            :key="session.id"
            class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800"
          >
            <div class="flex items-center justify-between gap-3">
              <p class="truncate text-sm font-semibold text-gray-800 dark:text-white">{{ session.scenario_name }}</p>
              <span class="text-xs text-gray-500">{{ session.average_score }}分</span>
            </div>
            <p class="mt-1 truncate text-xs text-gray-500 dark:text-gray-400">{{ session.state_label }} · {{ session.next_focus }}</p>
          </div>
        </div>
      </section>

      <section class="card xl:col-span-2">
        <PanelTitle title="生产调度健康" subtitle="Commander 定时任务、审计快照、告警和恢复手册" :icon="TimerReset" />
        <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
          <MetricPill label="状态" :value="center.sections.scheduler.status" />
          <MetricPill label="任务" :value="center.sections.scheduler.jobs.length" />
          <MetricPill label="告警" :value="center.sections.scheduler.alerts.length" />
          <MetricPill label="已观察" :value="observedSchedulerJobs" />
        </div>
        <div class="mt-5 grid grid-cols-1 gap-3 lg:grid-cols-3">
          <div
            v-for="job in center.sections.scheduler.jobs"
            :key="job.id"
            class="rounded-lg border border-gray-100 p-3 dark:border-gray-700"
          >
            <div class="mb-2 flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="truncate text-sm font-semibold text-gray-800 dark:text-white">{{ job.name }}</p>
                <p class="mt-1 break-all text-xs text-gray-500 dark:text-gray-400">{{ job.id }}</p>
              </div>
              <span class="shrink-0 rounded px-2 py-1 text-xs" :class="schedulerJobClass(job)">
                {{ job.latest_status }}
              </span>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <GateRow label="已观察" :passed="job.observed" />
              <GateRow label="未过期" :passed="!job.stale" />
            </div>
            <p class="mt-3 break-all text-xs text-gray-500 dark:text-gray-400">{{ job.next_action || '保持调度观察。' }}</p>
          </div>
        </div>
        <div v-if="center.sections.scheduler.alerts.length" class="mt-5 space-y-2">
          <div
            v-for="alert in center.sections.scheduler.alerts"
            :key="alert.job_id + alert.reason"
            class="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-900/60 dark:bg-amber-900/20 dark:text-amber-300"
          >
            <p class="font-semibold">{{ alert.job_id }} · {{ alert.severity }}</p>
            <p class="mt-1">{{ alert.reason }}</p>
            <p class="mt-1 break-all">{{ alert.action }}</p>
          </div>
        </div>
        <div class="mt-5 grid grid-cols-1 gap-3 lg:grid-cols-3">
          <div
            v-for="step in center.sections.scheduler.recovery_runbook.slice(0, 3)"
            :key="step.step"
            class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800"
          >
            <p class="text-sm font-semibold text-gray-800 dark:text-white">{{ step.step }} · {{ step.title }}</p>
            <p class="mt-2 break-all text-xs text-gray-500 dark:text-gray-400">{{ step.command }}</p>
          </div>
        </div>
      </section>
    </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref } from 'vue'
import { Activity, BadgeCheck, BellRing, Cpu, Database, LineChart, TimerReset } from 'lucide-vue-next'
import { analyticsApi } from '@/utils/api'
import { displayValue, finiteNumber, oneDecimal, rounded } from '@/utils/format'
import EmptyState from '@/components/EmptyState.vue'
import type { AnalyticsAction, AnalyticsCenter, AnalyticsCenterMetric } from '@/utils/api'

const center = ref<AnalyticsCenter | null>(null)
const loading = ref(false)
const loadError = ref('')

const diagnostics = computed(() => {
  const rows = center.value?.sections.provider.diagnostics || []
  return rows.slice(0, 4).map((row) => {
    const key = String(row.key ?? row.name ?? 'diagnostic')
    const value = String(row.value ?? row.status ?? row.message ?? '待校准')
    return `${key}: ${value}`
  })
})

const importDebt = computed(() => {
  const debt = center.value?.sections.import_quality.quality_debt || {}
  return Object.entries(debt).slice(0, 6).map(([name, value]) => ({ name, value: rounded(value) }))
})

const observedSchedulerJobs = computed(() => {
  return center.value?.sections.scheduler.jobs.filter((job) => job.observed).length || 0
})

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    center.value = await analyticsApi.center(120)
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '分析中心加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

function formatValue(metric: AnalyticsCenterMetric) {
  const value = oneDecimal(metric.value)
  if (metric.unit === '%' || metric.unit === 'score' || metric.unit === 'health') return `${value}${metric.unit === '%' ? '%' : ''}`
  return displayValue(value)
}

function metricTarget(metric: AnalyticsCenterMetric) {
  const value = oneDecimal(metric.target)
  if (metric.unit === '%') return `${value}%`
  if (metric.unit === 'gate') return value === 100 ? '通过' : displayValue(value)
  return displayValue(value)
}

function metricProgress(metric: AnalyticsCenterMetric) {
  const target = finiteNumber(metric.target)
  if (target <= 0) return 0
  return Math.max(3, Math.min(100, rounded((finiteNumber(metric.value) / target) * 100)))
}

function timelineWidth(value: number) {
  return Math.max(3, Math.min(100, rounded(value)))
}

function metricClass(status: string) {
  return status === 'passed' ? 'text-emerald-600 dark:text-emerald-300' : 'text-amber-600 dark:text-amber-300'
}

function statusBadge(status: string) {
  return status === 'passed'
    ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
    : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
}

function probeStatusClass(status: string) {
  if (status === 'ready_for_live_probe') return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
  if (status === 'policy_blocked') return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
  return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
}

function providerRiskClass(risk: string) {
  if (risk === 'low') return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
  if (risk === 'medium') return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
  return 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300'
}

function successContractClass(gate: Record<string, boolean>) {
  if (gate.structured_success_ok && !gate.raw_text_needs_review && !gate.provider_failure_needs_review) {
    return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
  }
  if (gate.raw_text_needs_review || gate.provider_failure_needs_review) {
    return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
  }
  return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
}

function schedulerJobClass(job: AnalyticsCenter['sections']['scheduler']['jobs'][number]) {
  if (job.latest_status === 'completed' && !job.stale) return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
  if (job.latest_status === 'missing' || job.stale) return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
  return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
}

function alertClass(priority: string) {
  if (priority === 'high') return 'border-red-200 bg-red-50 dark:border-red-900/60 dark:bg-red-900/20'
  if (priority === 'medium') return 'border-amber-200 bg-amber-50 dark:border-amber-900/60 dark:bg-amber-900/20'
  return 'border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800'
}

function summaryValue(source: Record<string, unknown>, key: string) {
  const value = source[key]
  if (typeof value === 'number') return oneDecimal(value)
  if (typeof value === 'string') return value
  return 0
}

const MetricPill = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: [String, Number], required: true },
  },
  setup(props) {
    return () => h('div', { class: 'rounded-lg bg-gray-50 p-3 dark:bg-gray-800' }, [
      h('p', { class: 'text-xs text-gray-500 dark:text-gray-400' }, props.label),
      h('p', { class: 'mt-1 text-lg font-bold text-gray-800 dark:text-white' }, String(props.value)),
    ])
  },
})

const DeltaTile = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: Number, required: true },
    reverse: { type: Boolean, default: false },
  },
  setup(props) {
    return () => {
      const value = oneDecimal(props.value)
      const good = props.reverse ? value <= 0 : value >= 0
      const color = good ? 'text-emerald-600 dark:text-emerald-300' : 'text-orange-600 dark:text-orange-300'
      const prefix = value > 0 ? '+' : ''
      return h('div', { class: 'rounded-lg bg-gray-50 p-3 dark:bg-gray-800' }, [
        h('p', { class: 'text-xs text-gray-500 dark:text-gray-400' }, props.label),
        h('p', { class: `mt-1 text-lg font-bold ${color}` }, `${prefix}${value}`),
      ])
    }
  },
})

const ActionList = defineComponent({
  props: {
    items: { type: Array as () => AnalyticsAction[], required: true },
  },
  setup(props) {
    return () => h('div', { class: 'space-y-2' }, props.items.slice(0, 3).map((item) => h('div', {
      class: 'rounded-lg border border-gray-100 p-3 dark:border-gray-700',
    }, [
      h('div', { class: 'flex items-center justify-between gap-3' }, [
        h('p', { class: 'text-sm font-medium text-gray-800 dark:text-white' }, item.action),
        h('span', { class: 'text-xs text-gray-500' }, item.priority),
      ]),
      h('p', { class: 'mt-1 text-xs text-gray-500 dark:text-gray-400' }, item.reason),
    ])))
  },
})

const PanelTitle = defineComponent({
  props: {
    title: { type: String, required: true },
    subtitle: { type: String, required: true },
    icon: { type: Object, required: true },
  },
  setup(props) {
    return () => h('div', { class: 'mb-5 flex items-start justify-between gap-3' }, [
      h('div', [
        h('h2', { class: 'text-xl font-bold text-gray-800 dark:text-white' }, props.title),
        h('p', { class: 'mt-1 text-sm text-gray-500 dark:text-gray-400' }, props.subtitle),
      ]),
      h(props.icon, { class: 'h-5 w-5 text-blue-500 shrink-0' }),
    ])
  },
})

const GateRow = defineComponent({
  props: {
    label: { type: String, required: true },
    passed: { type: Boolean, required: true },
  },
  setup(props) {
    return () => h('div', { class: 'flex items-center justify-between rounded-lg bg-gray-50 p-3 dark:bg-gray-800' }, [
      h('span', { class: 'text-sm text-gray-600 dark:text-gray-300' }, props.label),
      h('span', {
        class: props.passed
          ? 'rounded bg-emerald-100 px-2 py-1 text-xs text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
          : 'rounded bg-amber-100 px-2 py-1 text-xs text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
      }, props.passed ? '通过' : '待加强'),
    ])
  },
})

const DebtTile = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: Number, required: true },
  },
  setup(props) {
    return () => h('div', { class: 'flex items-center justify-between rounded-lg bg-gray-50 p-3 dark:bg-gray-800' }, [
      h('span', { class: 'truncate text-sm text-gray-600 dark:text-gray-300' }, props.label),
      h('span', { class: 'font-bold text-amber-600 dark:text-amber-300' }, String(props.value)),
    ])
  },
})

onMounted(load)
</script>
