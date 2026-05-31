<template>
  <div class="p-4 sm:p-6 lg:p-8">
    <div class="mb-8">
      <p class="text-sm font-semibold text-blue-500 mb-2">Living System / 系统进化中心</p>
      <h1 class="text-3xl font-bold text-gray-800 dark:text-white">关系动力学进化中心</h1>
      <p class="text-gray-500 dark:text-gray-400 mt-2">让系统像生命体一样持续吸收研究、案例、访谈与用户反馈。</p>
    </div>

    <div class="card mb-8 bg-gradient-to-r from-blue-500 to-purple-500 text-white">
      <div class="flex flex-col items-start justify-between gap-4 sm:flex-row sm:gap-6">
        <div>
          <h2 class="text-xl font-bold mb-2">单一数据源原则</h2>
          <p class="opacity-90">{{ latest?.principle || 'SQLite 是当前阶段唯一真数据源；API 是唯一数据出口。' }}</p>
        </div>
        <button
          @click="load"
          :disabled="loading"
          class="w-full rounded-xl bg-white/20 px-4 py-2 transition-colors hover:bg-white/30 disabled:opacity-60 sm:w-auto"
        >
          {{ loading ? '刷新中...' : '刷新' }}
        </button>
      </div>
    </div>

    <EmptyState
      v-if="loadError && !latest && !pipeline"
      type="error"
      title="进化中心加载失败"
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

    <template v-if="!loadError || latest || pipeline">
    <div v-if="latest?.latest_report" class="card mb-8">
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-1">最新进化报告 · {{ latest.latest_report.period_type }}</p>
      <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-2">{{ latest.latest_report.title }}</h2>
      <p class="text-gray-600 dark:text-gray-300">{{ latest.latest_report.summary }}</p>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      <div class="card"><p class="text-sm text-gray-500">进化条目</p><p class="text-3xl font-bold text-gray-800 dark:text-white mt-2">{{ latest?.items.length || 0 }}</p></div>
      <div class="card"><p class="text-sm text-gray-500">平均质量</p><p class="text-3xl font-bold text-green-500 mt-2">{{ averageQuality }}</p></div>
      <div class="card"><p class="text-sm text-gray-500">数据出口</p><p class="text-3xl font-bold text-blue-500 mt-2">API</p></div>
    </div>

    <div v-if="pipeline" class="card mb-8">
      <div class="flex items-start justify-between gap-4 mb-6">
        <div>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white">源数据到训练资产流水线</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ pipeline.principle }}</p>
        </div>
        <span class="px-3 py-1 rounded-full text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300">Meta Pipeline</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-5 gap-3 mb-6">
        <div
          v-for="stage in pipeline.stages"
          :key="stage.id"
          class="rounded-lg bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4"
        >
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ stage.name }}</p>
          <p class="text-3xl font-bold text-gray-800 dark:text-white mt-2">{{ stage.count }}</p>
          <p class="text-xs text-blue-500 mt-2">{{ stage.risk_gate }}</p>
        </div>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div>
          <h3 class="font-bold text-gray-800 dark:text-white mb-3">下一步动作</h3>
          <div class="space-y-2">
            <div v-for="action in pipeline.next_actions" :key="action.action" class="rounded-lg bg-white dark:bg-gray-900 p-3 border border-gray-100 dark:border-gray-700">
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full" :class="priorityDot(action.priority)"></span>
                <p class="font-semibold text-gray-800 dark:text-white text-sm">{{ action.action }}</p>
              </div>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ action.reason }}</p>
            </div>
          </div>
        </div>
        <div>
          <h3 class="font-bold text-gray-800 dark:text-white mb-3">分类轴</h3>
          <div class="flex flex-wrap gap-2">
            <span v-for="axis in pipeline.classification_axes" :key="axis" class="px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-sm text-gray-600 dark:text-gray-300">{{ axis }}</span>
          </div>
          <h3 class="font-bold text-gray-800 dark:text-white mt-5 mb-3">状态计数</h3>
          <div class="grid grid-cols-3 gap-3">
            <div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-3">
              <p class="text-xs text-gray-500">Raw</p>
              <p class="text-lg font-bold text-gray-800 dark:text-white">{{ totalCount(pipeline.status_counts.raw) }}</p>
            </div>
            <div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-3">
              <p class="text-xs text-gray-500">Annotation</p>
              <p class="text-lg font-bold text-gray-800 dark:text-white">{{ totalCount(pipeline.status_counts.annotation) }}</p>
            </div>
            <div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-3">
              <p class="text-xs text-gray-500">Assets</p>
              <p class="text-lg font-bold text-gray-800 dark:text-white">{{ totalCount(pipeline.status_counts.assets) }}</p>
            </div>
          </div>
        </div>
      </div>

      <div v-if="pipeline.recent_logs.length" class="mt-6">
        <h3 class="font-bold text-gray-800 dark:text-white mb-3">最近处理日志</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div v-for="log in pipeline.recent_logs.slice(0, 4)" :key="log.id" class="rounded-lg bg-white dark:bg-gray-900 p-3 border border-gray-100 dark:border-gray-700">
            <div class="flex items-center justify-between gap-3">
              <p class="font-semibold text-gray-800 dark:text-white text-sm">{{ log.action }}</p>
              <span class="text-xs text-gray-400">{{ log.target_type }} #{{ log.target_id }}</span>
            </div>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ log.from_status || 'unknown' }} → {{ log.to_status }}</p>
            <p v-if="log.message" class="text-xs text-blue-500 mt-2">{{ log.message }}</p>
          </div>
        </div>
      </div>
    </div>

    <div v-if="pipeline?.visual_metrics" class="space-y-6 mb-8">
      <div class="card">
        <div class="flex items-start justify-between gap-4 mb-5">
          <div>
            <h2 class="text-xl font-bold text-gray-800 dark:text-white">生命体数图指标</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ pipeline.visual_metrics.principle }}</p>
          </div>
          <span class="px-3 py-1 rounded-full text-xs bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300">Visual Metrics</span>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-4">
            <p class="text-sm text-gray-500">学习速度</p>
            <p class="text-3xl font-bold text-blue-500 mt-2">{{ pipeline.visual_metrics.learning_increment.learning_velocity }}</p>
            <p class="text-xs text-gray-500 mt-2">标注、发布和自动化事件的综合增量</p>
          </div>
          <div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-4">
            <p class="text-sm text-gray-500">新增标注</p>
            <p class="text-3xl font-bold text-purple-500 mt-2">{{ pipeline.visual_metrics.learning_increment.new_annotations }}</p>
            <p class="text-xs text-gray-500 mt-2">关系元基础结构化次数</p>
          </div>
          <div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-4">
            <p class="text-sm text-gray-500">发布资产</p>
            <p class="text-3xl font-bold text-green-500 mt-2">{{ pipeline.visual_metrics.learning_increment.published_assets }}</p>
            <p class="text-xs text-gray-500 mt-2">可进入训练系统的版本</p>
          </div>
          <div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-4">
            <p class="text-sm text-gray-500">风险事件</p>
            <p class="text-3xl font-bold text-red-500 mt-2">{{ totalRiskEvents }}</p>
            <p class="text-xs text-gray-500 mt-2">脱敏、重复、拒绝等质量门禁信号</p>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div class="card">
          <h3 class="font-bold text-gray-800 dark:text-white mb-4">候选审核发布漏斗</h3>
          <div class="space-y-3">
            <div v-for="stage in pipeline.visual_metrics.review_publish_funnel" :key="stage.id">
              <div class="flex items-center justify-between text-sm mb-1">
                <span class="font-medium text-gray-700 dark:text-gray-200">{{ stage.label }}</span>
                <span class="text-gray-500">{{ stage.count }} · {{ stage.conversion_from_previous }}%</span>
              </div>
              <div class="h-3 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
                <div
                  class="h-full rounded-full bg-blue-500 transition-all"
                  :style="{ width: `${Math.min(100, stage.percent_of_start)}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <h3 class="font-bold text-gray-800 dark:text-white mb-4">安全风险趋势</h3>
          <div class="flex items-end gap-2 h-40">
            <div
              v-for="point in pipeline.visual_metrics.safety_risk_trend"
              :key="point.date"
              class="flex-1 flex flex-col items-center justify-end gap-2 min-w-0"
            >
              <div class="w-full rounded-t bg-red-400 dark:bg-red-500" :style="{ height: `${riskBarHeight(point.risk_rate)}px` }"></div>
              <span class="text-[10px] text-gray-400 truncate w-full text-center">{{ point.date.slice(5) }}</span>
            </div>
          </div>
          <p class="text-xs text-gray-500 mt-3">柱高代表风险事件占比；空数据时保持零风险基线。</p>
        </div>
      </div>

      <div class="card">
        <h3 class="font-bold text-gray-800 dark:text-white mb-4">来源质量矩阵</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          <div
            v-for="source in pipeline.visual_metrics.source_quality_matrix"
            :key="source.id || source.name"
            class="rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4"
          >
            <div class="flex items-start justify-between gap-3 mb-3">
              <div class="min-w-0">
                <p class="font-semibold text-gray-800 dark:text-white truncate">{{ source.name }}</p>
                <p class="text-xs text-gray-500">{{ source.source_type }} · {{ quadrantLabel(source.quadrant) }}</p>
              </div>
              <span class="text-lg font-bold" :class="healthClass(source.health_score)">{{ rounded(source.health_score) }}</span>
            </div>
            <div class="grid grid-cols-3 gap-2 text-xs">
              <div><p class="text-gray-400">可信</p><p class="font-semibold text-gray-700 dark:text-gray-200">{{ source.trust_score }}%</p></div>
              <div><p class="text-gray-400">置信</p><p class="font-semibold text-gray-700 dark:text-gray-200">{{ source.avg_confidence }}%</p></div>
              <div><p class="text-gray-400">转化</p><p class="font-semibold text-gray-700 dark:text-gray-200">{{ ratioPercent(source.conversion_rate) }}</p></div>
              <div><p class="text-gray-400">候选</p><p class="font-semibold text-gray-700 dark:text-gray-200">{{ source.raw_count }}</p></div>
              <div><p class="text-gray-400">隐私风险</p><p class="font-semibold text-gray-700 dark:text-gray-200">{{ source.avg_privacy_risk }}%</p></div>
              <div><p class="text-gray-400">版权风险</p><p class="font-semibold text-gray-700 dark:text-gray-200">{{ source.avg_copyright_risk }}%</p></div>
            </div>
          </div>
          <div v-if="pipeline.visual_metrics.source_quality_matrix.length === 0" class="rounded-lg bg-gray-50 dark:bg-gray-800 p-6 text-center text-gray-500">
            等待来源登记后生成质量矩阵
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div class="card">
          <h3 class="font-bold text-gray-800 dark:text-white mb-4">分类轴覆盖</h3>
          <div class="flex flex-wrap gap-2">
            <span v-for="axis in pipeline.visual_metrics.learning_increment.axis_coverage" :key="axis.name" class="px-3 py-2 rounded-lg bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 text-sm">
              {{ axis.name }} · {{ axis.count }}
            </span>
          </div>
        </div>
        <div class="card">
          <h3 class="font-bold text-gray-800 dark:text-white mb-4">元层覆盖</h3>
          <div class="flex flex-wrap gap-2">
            <span v-for="layer in pipeline.visual_metrics.learning_increment.primitive_layer_coverage" :key="layer.name" class="px-3 py-2 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-sm">
              {{ layer.name }} · {{ layer.count }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="card mb-8">
      <div class="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4 mb-6">
        <div>
          <p class="text-sm font-semibold text-emerald-500 mb-2">Autonomous Evolution / 动态调度</p>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white">本地指挥官调度驾驶舱</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">周期周报、语义去重、导入质量和安全审计接在同一条进化回路上。</p>
        </div>
        <button
          @click="runScheduler"
          :disabled="schedulerRunning"
          class="px-4 py-2 rounded-lg bg-emerald-500 text-white hover:bg-emerald-600 disabled:opacity-60 transition-colors"
        >
          {{ schedulerRunning ? '运行中...' : '运行周调度' }}
        </button>
      </div>

      <div v-if="schedulerError" class="mb-5 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-900/20 dark:text-red-300">
        {{ schedulerError }}
      </div>

      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-4">
          <p class="text-sm text-gray-500">导入质量</p>
          <p class="text-3xl font-bold mt-2" :class="qualityClass(importQuality?.quality_score || 0)">{{ rounded(importQuality?.quality_score) }}</p>
          <p class="text-xs text-gray-500 mt-2">字段完整、JSON 合法、问题可追踪</p>
        </div>
        <div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-4">
          <p class="text-sm text-gray-500">相似簇</p>
          <p class="text-3xl font-bold text-amber-500 mt-2">{{ dedupeReport?.summary.clusters || 0 }}</p>
          <p class="text-xs text-gray-500 mt-2">hash + 标题语义近邻</p>
        </div>
        <div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-4">
          <p class="text-sm text-gray-500">安全阻断</p>
          <p class="text-3xl font-bold text-red-500 mt-2">{{ safetyEvents?.summary.blocked || 0 }}</p>
          <p class="text-xs text-gray-500 mt-2">操控、胁迫、跟踪等硬阻断审计</p>
        </div>
        <div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-4">
          <p class="text-sm text-gray-500">调度报告</p>
          <p class="text-3xl font-bold text-blue-500 mt-2">{{ schedulerResult?.report ? '1' : '0' }}</p>
          <p class="text-xs text-gray-500 mt-2">{{ schedulerResult?.report?.title || '等待本轮执行' }}</p>
        </div>
      </div>

      <div v-if="schedulerResult?.next_actions?.length" class="rounded-lg border border-emerald-100 dark:border-emerald-900/40 bg-emerald-50/60 dark:bg-emerald-900/10 p-4 mb-6">
        <h3 class="font-bold text-gray-800 dark:text-white mb-3">调度后的下一动作</h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div v-for="action in schedulerResult.next_actions" :key="action.action" class="rounded-lg bg-white dark:bg-gray-900 p-3">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 rounded-full" :class="priorityDot(action.priority)"></span>
              <p class="font-semibold text-sm text-gray-800 dark:text-white">{{ action.action }}</p>
            </div>
            <p class="text-xs text-gray-500 mt-1">{{ action.reason }}</p>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div>
          <h3 class="font-bold text-gray-800 dark:text-white mb-3">导入质量结构</h3>
          <div class="space-y-3">
            <div v-for="(block, name) in importQuality?.field_completeness || {}" :key="name" class="rounded-lg bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 p-3">
              <div class="flex items-center justify-between mb-2">
                <p class="font-semibold text-gray-700 dark:text-gray-200 text-sm">{{ qualityBlockName(String(name)) }}</p>
                <span class="text-xs text-gray-400">坏 JSON {{ block.json_invalid }}</span>
              </div>
              <div class="space-y-2">
                <div v-for="(rate, field) in block.required" :key="field">
                  <div class="flex justify-between text-xs mb-1">
                    <span class="text-gray-500">{{ field }}</span>
                    <span class="text-gray-500">{{ ratioPercent(rate) }}</span>
                  </div>
                  <div class="h-2 rounded-full bg-gray-100 dark:bg-gray-800 overflow-hidden">
                    <div class="h-full bg-blue-500 rounded-full" :style="{ width: safeRatioBarWidth(rate) }"></div>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="!importQuality" class="text-sm text-gray-500">加载导入质量中...</div>
          </div>
        </div>

        <div>
          <h3 class="font-bold text-gray-800 dark:text-white mb-3">重复候选簇</h3>
          <div class="space-y-3">
            <div v-for="cluster in dedupeReport?.clusters.slice(0, 5) || []" :key="cluster.kind + cluster.raw_uuids.join('-')" class="rounded-lg bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 p-3">
              <div class="flex items-center justify-between gap-3 mb-2">
                <p class="font-semibold text-sm text-gray-800 dark:text-white">{{ cluster.kind === 'hash' ? '精确重复' : '语义近邻' }}</p>
                <span class="text-xs text-amber-500">{{ cluster.item_ids.length }} 条</span>
              </div>
              <p class="text-xs text-gray-500 line-clamp-2">{{ cluster.titles.filter(Boolean).join(' / ') }}</p>
              <p class="text-xs text-blue-500 mt-2">{{ cluster.recommendation }}</p>
            </div>
            <div v-if="dedupeReport && dedupeReport.clusters.length === 0" class="rounded-lg bg-gray-50 dark:bg-gray-800 p-4 text-sm text-gray-500">当前未发现需复核重复簇。</div>
            <div v-if="!dedupeReport" class="text-sm text-gray-500">加载去重报告中...</div>
          </div>
        </div>

        <div>
          <h3 class="font-bold text-gray-800 dark:text-white mb-3">安全事件</h3>
          <div class="space-y-3">
            <div v-for="event in safetyEvents?.events.slice(0, 5) || []" :key="event.id" class="rounded-lg bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-700 p-3">
              <div class="flex items-center justify-between gap-3 mb-2">
                <p class="font-semibold text-sm text-gray-800 dark:text-white">{{ event.task_type }}</p>
                <span class="text-xs text-red-500">{{ event.risk_level }}</span>
              </div>
              <p class="text-xs text-gray-500 line-clamp-2">{{ event.payload_preview }}</p>
              <div class="flex flex-wrap gap-1 mt-2">
                <span v-for="flag in event.flags" :key="flag" class="px-2 py-0.5 rounded bg-red-50 dark:bg-red-900/20 text-red-500 text-[11px]">{{ flag }}</span>
              </div>
            </div>
            <div v-if="safetyEvents && safetyEvents.events.length === 0" class="rounded-lg bg-gray-50 dark:bg-gray-800 p-4 text-sm text-gray-500">暂无安全硬阻断事件。</div>
            <div v-if="!safetyEvents" class="text-sm text-gray-500">加载安全事件中...</div>
          </div>
        </div>
      </div>
    </div>

    <div class="space-y-4">
      <div v-for="item in latest?.items || []" :key="item.id" class="card card-hover">
        <div class="flex items-start justify-between gap-4 mb-3">
          <div>
            <span class="px-2 py-0.5 rounded text-xs bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">{{ item.category }}</span>
            <h3 class="text-lg font-bold text-gray-800 dark:text-white mt-2">{{ item.title }}</h3>
          </div>
          <div class="text-right shrink-0">
            <p class="text-sm text-gray-500">质量分</p>
            <p class="text-xl font-bold text-green-500">{{ rounded(item.quality_score) }}</p>
          </div>
        </div>
        <p class="text-gray-600 dark:text-gray-300 mb-3">{{ item.summary || item.content }}</p>
        <div class="flex flex-wrap gap-2">
          <span v-for="tag in item.tags" :key="tag" class="px-2 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-300">#{{ tag }}</span>
        </div>
      </div>

      <div v-if="!loading && (!latest || latest.items.length === 0)" class="card text-center py-16">
        <div class="text-6xl mb-4">🌱</div>
        <h3 class="text-xl font-bold text-gray-800 dark:text-white mb-2">进化中心等待内容</h3>
        <p class="text-gray-500 dark:text-gray-400">后续 Cronjob、JSON 导入和 AI 标注会持续向这里注入高质量知识。</p>
      </div>
    </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { evolutionApi } from '@/utils/api'
import { finiteNumber, ratioPercent, rounded, safeRatioBarWidth } from '@/utils/format'
import EmptyState from '@/components/EmptyState.vue'
import type {
  EvolutionDedupeReport,
  EvolutionImportQuality,
  EvolutionLatest,
  EvolutionPipeline,
  EvolutionSafetyEvents,
  EvolutionSchedulerResult,
} from '@/utils/api'

const latest = ref<EvolutionLatest | null>(null)
const pipeline = ref<EvolutionPipeline | null>(null)
const dedupeReport = ref<EvolutionDedupeReport | null>(null)
const importQuality = ref<EvolutionImportQuality | null>(null)
const safetyEvents = ref<EvolutionSafetyEvents | null>(null)
const schedulerResult = ref<EvolutionSchedulerResult | null>(null)
const loading = ref(false)
const schedulerRunning = ref(false)
const loadError = ref('')
const schedulerError = ref('')

const averageQuality = computed(() => {
  const items = latest.value?.items || []
  if (!items.length) return 0
  return rounded(items.reduce((sum, item) => sum + finiteNumber(item.quality_score), 0) / items.length)
})

const totalRiskEvents = computed(() => {
  const trend = pipeline.value?.visual_metrics.safety_risk_trend || []
  return trend.reduce((sum, point) => sum + finiteNumber(point.risk_events) + finiteNumber(point.blocked), 0)
})

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    const [latestData, pipelineData, dedupeData, qualityData, safetyData] = await Promise.all([
      evolutionApi.latest(),
      evolutionApi.pipeline(),
      evolutionApi.dedupeReport(120),
      evolutionApi.importQuality(),
      evolutionApi.safetyEvents(50),
    ])
    latest.value = latestData
    pipeline.value = pipelineData
    dedupeReport.value = dedupeData
    importQuality.value = qualityData
    safetyEvents.value = safetyData
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '进化中心加载失败，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function runScheduler() {
  schedulerRunning.value = true
  schedulerError.value = ''
  try {
    schedulerResult.value = await evolutionApi.runWeeklyScheduler({
      dry_run: false,
      batch_limit: 50,
      duplicate_policy: 'annotate_duplicates',
      period_type: 'weekly',
    })
    dedupeReport.value = schedulerResult.value.dedupe_report
    importQuality.value = schedulerResult.value.import_quality
    safetyEvents.value = schedulerResult.value.safety_events
    await load()
  } catch (error) {
    schedulerError.value = error instanceof Error ? error.message : '周调度执行失败，请稍后重试。'
  } finally {
    schedulerRunning.value = false
  }
}

function priorityDot(priority: 'high' | 'medium' | 'low') {
  if (priority === 'high') return 'bg-red-500'
  if (priority === 'medium') return 'bg-yellow-500'
  return 'bg-green-500'
}

function totalCount(counts: Record<string, number>) {
  return Object.values(counts).reduce((sum, count) => sum + count, 0)
}

function riskBarHeight(rate: number) {
  return Math.max(4, rounded(Math.min(1, Math.max(0, finiteNumber(rate))) * 120))
}

function quadrantLabel(quadrant: string) {
  const labels: Record<string, string> = {
    high_quality_low_risk: '高质低风险',
    promising_needs_review: '可用待复核',
    risk_quarantine: '风险隔离',
    low_signal: '低信号',
  }
  return labels[quadrant] || '待校准'
}

function healthClass(score: number) {
  const value = finiteNumber(score)
  if (value >= 75) return 'text-green-500'
  if (value >= 60) return 'text-blue-500'
  if (value >= 40) return 'text-yellow-500'
  return 'text-red-500'
}

function qualityClass(score: number) {
  const value = finiteNumber(score)
  if (value >= 85) return 'text-green-500'
  if (value >= 70) return 'text-blue-500'
  if (value >= 50) return 'text-yellow-500'
  return 'text-red-500'
}

function qualityBlockName(name: string) {
  const labels: Record<string, string> = {
    samples: '互动样本',
    resources: '连接素材',
    knowledge_entries: '知识条目',
  }
  return labels[name] || name
}

onMounted(load)
</script>
