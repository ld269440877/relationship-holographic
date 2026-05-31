<template>
  <div class="p-4 sm:p-6 lg:p-8">
    <div class="mb-8 flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
      <div>
        <p class="mb-2 text-sm font-semibold text-emerald-500">Release Governance / 发布治理</p>
        <h1 class="text-3xl font-bold text-gray-800 dark:text-white">Reviewed 资产发布操作台</h1>
        <p class="mt-2 max-w-3xl text-gray-500 dark:text-gray-400">
          {{ candidates?.principle || 'Reviewed 资产必须经过人工确认、撤回和复审审计，不能绕过状态机直接发布。' }}
        </p>
      </div>
      <div class="flex flex-col gap-2 sm:flex-row">
        <button
          class="rounded-lg border border-gray-200 px-4 py-2 text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-60 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
          :disabled="loading"
          @click="load"
        >
          {{ loading ? '刷新中...' : '刷新候选' }}
        </button>
        <button
          class="rounded-lg bg-emerald-500 px-4 py-2 text-white transition-colors hover:bg-emerald-600 disabled:opacity-60"
          :disabled="!selected || actionRunning"
          @click="runDryRun"
        >
          发布预演
        </button>
      </div>
    </div>

    <div
      v-if="loadError"
      class="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300"
    >
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p>{{ loadError }}</p>
        <button class="rounded-lg bg-red-500 px-3 py-2 text-white hover:bg-red-600" @click="load">
          重试候选
        </button>
      </div>
    </div>

    <div class="mb-8 grid grid-cols-1 gap-4 md:grid-cols-4">
      <MetricCard label="候选资产" :value="candidates?.total ?? 0" />
      <MetricCard label="可发布" :value="candidates?.publish_ready ?? 0" tone="emerald" />
      <MetricCard label="确认门禁" :value="candidates?.quality_gates.requires_manual_confirmation ? '人工' : '自动'" tone="blue" />
      <MetricCard label="最低阈值" :value="candidates?.quality_gates.minimum_priority_for_auto_publish ?? 0" tone="amber" />
    </div>

    <section class="card mb-8">
      <div class="mb-5 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p class="mb-2 text-sm font-semibold text-rose-500">Resource Similarity / 资源近重复治理</p>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white">近重复资源队列</h2>
          <p class="mt-1 max-w-3xl text-sm text-gray-500 dark:text-gray-400">
            {{ similarityQueue?.principle || '近重复队列用于发现同标题、同场景、同来源变体，不自动删除内容。' }}
          </p>
        </div>
        <button
          class="rounded-lg border border-gray-200 px-4 py-2 text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-60 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
          :disabled="similarityLoading"
          @click="loadSimilarityQueue"
        >
          {{ similarityLoading ? '扫描中...' : '刷新近重复' }}
        </button>
      </div>

      <div
        v-if="similarityError"
        class="mb-5 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300"
      >
        {{ similarityError }}
      </div>

      <div class="mb-5 grid grid-cols-1 gap-4 md:grid-cols-4">
        <MetricCard label="扫描资源" :value="similarityQueue?.summary.scanned ?? '-'" />
        <MetricCard label="重复簇" :value="similarityQueue?.summary.clusters ?? '-'" tone="amber" />
        <MetricCard label="候选项" :value="similarityQueue?.summary.queued_items ?? '-'" tone="rose" />
        <MetricCard label="阈值" :value="similarityQueue?.summary.threshold ?? '-'" tone="blue" />
      </div>

      <div class="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div class="space-y-3">
          <div
            v-for="cluster in similarityQueue?.clusters || []"
            :key="cluster.cluster_id"
            class="rounded-lg border border-gray-100 bg-white p-4 dark:border-gray-700 dark:bg-gray-900"
          >
            <div class="mb-3 flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div class="min-w-0">
                <div class="mb-2 flex flex-wrap items-center gap-2">
                  <span class="rounded bg-rose-50 px-2 py-1 text-xs text-rose-700 dark:bg-rose-900/20 dark:text-rose-300">
                    {{ similarityActionLabel(cluster.recommended_action) }}
                  </span>
                  <span class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                    {{ cluster.size }} 条
                  </span>
                  <span class="rounded bg-blue-50 px-2 py-1 text-xs text-blue-700 dark:bg-blue-900/20 dark:text-blue-300">
                    相似 {{ Math.round(cluster.highest_similarity * 100) }}%
                  </span>
                </div>
                <p class="break-words font-semibold text-gray-800 dark:text-white">{{ cluster.family_key }}</p>
                <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  pair={{ cluster.pair_count }} · avg={{ cluster.average_similarity }} · {{ cluster.kind }}
                </p>
              </div>
              <RouterLink
                :to="{ path: '/resources', query: { q: cluster.items[0]?.title || cluster.family_key } }"
                class="shrink-0 rounded-lg bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-100 dark:bg-rose-900/20 dark:text-rose-300"
              >
                查看资源
              </RouterLink>
            </div>

            <div class="mb-3 flex flex-wrap gap-2">
              <button
                class="rounded-lg border border-rose-200 px-3 py-2 text-xs font-semibold text-rose-700 transition-colors hover:bg-rose-50 disabled:opacity-60 dark:border-rose-900/50 dark:text-rose-300 dark:hover:bg-rose-900/20"
                :disabled="similarityActionRunning"
                @click="runSimilarityClusterAction(cluster, 'quarantine_variants', true)"
              >
                隔离变体预演
              </button>
              <button
                class="rounded-lg bg-rose-500 px-3 py-2 text-xs font-semibold text-white transition-colors hover:bg-rose-600 disabled:opacity-60"
                :disabled="similarityActionRunning"
                @click="runSimilarityClusterAction(cluster, 'quarantine_variants', false)"
              >
                隔离低质变体
              </button>
              <button
                class="rounded-lg border border-blue-200 px-3 py-2 text-xs font-semibold text-blue-700 transition-colors hover:bg-blue-50 disabled:opacity-60 dark:border-blue-900/50 dark:text-blue-300 dark:hover:bg-blue-900/20"
                :disabled="similarityActionRunning"
                @click="runSimilarityClusterAction(cluster, 'request_review', false)"
              >
                请求复审
              </button>
              <button
                class="rounded-lg border border-purple-200 px-3 py-2 text-xs font-semibold text-purple-700 transition-colors hover:bg-purple-50 disabled:opacity-60 dark:border-purple-900/50 dark:text-purple-300 dark:hover:bg-purple-900/20"
                :disabled="similarityActionRunning"
                @click="runSimilarityRewrite(cluster, true)"
              >
                重写补位预演
              </button>
              <button
                class="rounded-lg bg-purple-500 px-3 py-2 text-xs font-semibold text-white transition-colors hover:bg-purple-600 disabled:opacity-60"
                :disabled="similarityActionRunning"
                @click="runSimilarityRewrite(cluster, false)"
              >
                生成补位
              </button>
            </div>

            <div class="grid grid-cols-1 gap-2 lg:grid-cols-2">
              <RouterLink
                v-for="item in cluster.items.slice(0, 6)"
                :key="item.id"
                :to="{ path: '/resources', query: { q: item.title || '', source: item.source || '' } }"
                class="rounded-lg bg-gray-50 p-3 text-sm transition-colors hover:bg-gray-100 dark:bg-gray-800 dark:hover:bg-gray-700"
              >
                <p class="truncate font-medium text-gray-800 dark:text-white">#{{ item.id }} {{ item.title || '无标题' }}</p>
                <p class="mt-1 truncate text-xs text-gray-500 dark:text-gray-400">
                  {{ item.category }} · {{ item.applicable_scene || '未标场景' }} · {{ item.source || 'unknown' }}
                </p>
              </RouterLink>
            </div>
          </div>
          <div v-if="similarityLoading" class="rounded-lg bg-gray-50 p-8 text-center text-gray-500 dark:bg-gray-800">
            正在扫描近重复资源...
          </div>
          <div v-if="!similarityLoading && !similarityQueue?.clusters.length" class="rounded-lg bg-gray-50 p-8 text-center text-gray-500 dark:bg-gray-800">
            当前扫描窗口未发现近重复簇。
          </div>
        </div>

        <aside class="space-y-2">
          <div
            v-if="similarityActionError"
            class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300"
          >
            {{ similarityActionError }}
          </div>
          <div
            v-if="similarityActionResult"
            class="rounded-lg border border-emerald-100 bg-emerald-50 p-3 text-sm dark:border-emerald-900/40 dark:bg-emerald-900/20"
          >
            <p class="font-semibold text-emerald-700 dark:text-emerald-300">
              {{ similarityActionResult.dry_run ? '预演' : '已写入' }}：{{ similarityActionLabel(similarityActionResult.action) }}
            </p>
            <p class="mt-1 text-xs text-emerald-700 dark:text-emerald-300">
              影响 {{ similarityActionResult.governance_report.resource_count }} 条 · {{ similarityStatusSummary(similarityActionResult) }}
            </p>
            <p class="mt-2 break-words text-xs text-emerald-700 dark:text-emerald-300">
              reason {{ similarityActionResult.governance_report.reason_hash }}
            </p>
            <p v-if="similarityActionResult.audit_logs?.length" class="mt-1 text-xs text-emerald-700 dark:text-emerald-300">
              审计日志 {{ similarityActionResult.audit_logs.map((log) => `#${log.id}`).join(' ') }}
            </p>
            <p class="mt-2 text-xs text-emerald-700 dark:text-emerald-300">
              {{ similarityActionResult.governance_report.next_action }}
            </p>
          </div>
          <div
            v-if="similarityRewriteResult"
            class="rounded-lg border border-purple-100 bg-purple-50 p-3 text-sm dark:border-purple-900/40 dark:bg-purple-900/20"
          >
            <p class="font-semibold text-purple-700 dark:text-purple-300">
              {{ similarityRewriteResult.dry_run ? '补位预演' : '已生成补位' }}：{{ similarityRewriteResult.governance_report.replacement_count }} 条
            </p>
            <p class="mt-1 text-xs text-purple-700 dark:text-purple-300">
              场景 {{ similarityRewriteResult.governance_report.scenes.join(' / ') }} · reason {{ similarityRewriteResult.governance_report.reason_hash }}
            </p>
            <p v-if="similarityRewriteResult.audit_logs?.length" class="mt-1 text-xs text-purple-700 dark:text-purple-300">
              审计日志 {{ similarityRewriteResult.audit_logs.map((log) => `#${log.id}`).join(' ') }}
            </p>
            <p class="mt-2 text-xs text-purple-700 dark:text-purple-300">
              {{ similarityRewriteResult.governance_report.next_action }}
            </p>
          </div>
          <div
            v-for="item in similarityQueue?.next_actions || []"
            :key="item.action"
            class="rounded-lg border border-gray-100 p-3 dark:border-gray-700"
          >
            <div class="flex items-center justify-between gap-3">
              <p class="text-sm font-medium text-gray-800 dark:text-white">{{ item.action }}</p>
              <span class="text-xs text-gray-500">{{ item.priority }}</span>
            </div>
            <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ item.reason }}</p>
          </div>
        </aside>
      </div>
    </section>

    <div class="mb-8 grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
      <section class="card">
        <div class="mb-5 flex items-center justify-between gap-3">
          <div>
            <h2 class="text-xl font-bold text-gray-800 dark:text-white">发布候选</h2>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">按质量信号、优先级和 reviewed 状态排序。</p>
          </div>
          <ShieldCheck class="h-5 w-5 text-emerald-500" />
        </div>

        <div class="space-y-3">
          <EmptyState
            v-if="loadError && !candidates?.items.length && !loading"
            type="error"
            title="发布候选加载失败"
            description="Reviewed 资产候选暂时不可用，已保留页面其它治理模块。"
            action-text="重试候选"
            @action="load"
          />
          <button
            v-for="item in loadError ? [] : candidates?.items || []"
            :key="item.asset_type + item.id"
            class="w-full rounded-lg border p-4 text-left transition-colors"
            :class="selectedKey === candidateKey(item) ? 'border-emerald-300 bg-emerald-50 dark:border-emerald-800 dark:bg-emerald-900/20' : 'border-gray-200 bg-white hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:hover:bg-gray-800'"
            @click="selectCandidate(item)"
          >
            <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div class="min-w-0">
                <div class="mb-2 flex flex-wrap items-center gap-2">
                  <span class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">{{ assetTypeLabel(item.asset_type) }}</span>
                  <span class="rounded px-2 py-1 text-xs" :class="item.publish_ready ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'">
                    {{ item.publish_ready ? '可确认发布' : '需补质量信号' }}
                  </span>
                  <span class="text-xs text-gray-400">#{{ item.id }}</span>
                </div>
                <p class="truncate font-semibold text-gray-800 dark:text-white">{{ item.title }}</p>
                <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">{{ item.category }} · {{ item.review_status }}</p>
                <div class="mt-3 flex flex-wrap gap-2">
                  <span v-for="reason in item.priority.reasons" :key="reason" class="rounded bg-blue-50 px-2 py-1 text-xs text-blue-600 dark:bg-blue-900/20 dark:text-blue-300">
                    {{ reason }}
                  </span>
                </div>
              </div>
              <div class="shrink-0 text-left lg:text-right">
                <p class="text-xs text-gray-500">优先级</p>
                <p class="text-3xl font-bold" :class="priorityClass(item.priority.score)">{{ item.priority.score }}</p>
                <p class="mt-1 text-xs text-gray-400">{{ qualitySignal(item) }}</p>
              </div>
            </div>
          </button>
          <div v-if="!loading && !candidates?.items.length" class="rounded-lg bg-gray-50 p-8 text-center text-gray-500 dark:bg-gray-800">
            当前没有 reviewed 发布候选。
          </div>
          <div v-if="loading" class="rounded-lg bg-gray-50 p-8 text-center text-gray-500 dark:bg-gray-800">加载候选中...</div>
        </div>
      </section>

      <aside class="space-y-6">
        <section class="card">
          <div class="mb-5 flex items-center justify-between gap-3">
            <div>
              <h2 class="text-xl font-bold text-gray-800 dark:text-white">操作确认</h2>
              <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">先 dry-run，再真实写入审计日志。</p>
            </div>
            <ClipboardCheck class="h-5 w-5 text-blue-500" />
          </div>

          <div v-if="selected" class="space-y-4">
            <div class="rounded-lg bg-gray-50 p-4 dark:bg-gray-800">
              <p class="truncate font-semibold text-gray-800 dark:text-white">{{ selected.title }}</p>
              <p class="mt-1 text-sm text-gray-500">{{ assetTypeLabel(selected.asset_type) }} · {{ selected.review_status }}</p>
            </div>

            <label class="block">
              <span class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200">动作</span>
              <select v-model="action" class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-gray-800 dark:border-gray-700 dark:bg-gray-900 dark:text-white">
                <option value="confirm_publish">确认发布</option>
                <option value="withdraw">撤回到 reviewed</option>
                <option value="request_review">请求复审</option>
              </select>
            </label>

            <label class="block">
              <span class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200">审阅人</span>
              <input v-model="reviewerId" class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-gray-800 dark:border-gray-700 dark:bg-gray-900 dark:text-white" />
            </label>

            <label class="block">
              <span class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200">原因</span>
              <textarea v-model="reason" rows="3" class="w-full resize-none rounded-lg border border-gray-200 bg-white px-3 py-2 text-gray-800 dark:border-gray-700 dark:bg-gray-900 dark:text-white"></textarea>
            </label>

            <div class="grid grid-cols-2 gap-3">
              <button class="rounded-lg border border-gray-200 px-3 py-2 text-gray-700 hover:bg-gray-50 disabled:opacity-60 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800" :disabled="actionRunning" @click="runDryRun">
                Dry-run
              </button>
              <button class="rounded-lg bg-emerald-500 px-3 py-2 text-white hover:bg-emerald-600 disabled:opacity-60" :disabled="actionRunning || !dryRunResult" @click="runApply">
                写入审计
              </button>
            </div>
          </div>
          <div v-else class="rounded-lg bg-gray-50 p-6 text-center text-sm text-gray-500 dark:bg-gray-800">
            选择一个候选资产后开始治理操作。
          </div>
        </section>

        <section class="card">
          <h2 class="mb-4 text-xl font-bold text-gray-800 dark:text-white">审计结果</h2>
          <div v-if="actionError" class="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">{{ actionError }}</div>
          <div v-if="dryRunResult" class="mb-4 rounded-lg bg-blue-50 p-3 dark:bg-blue-900/20">
            <p class="font-semibold text-blue-700 dark:text-blue-300">预演：{{ dryRunResult.from_status }} -> {{ dryRunResult.to_status }}</p>
            <p class="mt-1 text-sm text-blue-600 dark:text-blue-300">{{ dryRunResult.principle }}</p>
          </div>
          <div v-if="applyResult" class="rounded-lg bg-emerald-50 p-3 dark:bg-emerald-900/20">
            <p class="font-semibold text-emerald-700 dark:text-emerald-300">已写入：{{ applyResult.from_status }} -> {{ applyResult.to_status }}</p>
            <p class="mt-1 text-sm text-emerald-600 dark:text-emerald-300">日志 #{{ applyResult.audit_log?.id }} · {{ applyResult.audit_log?.action }}</p>
          </div>
          <div v-if="!dryRunResult && !applyResult && !actionError" class="rounded-lg bg-gray-50 p-6 text-center text-sm text-gray-500 dark:bg-gray-800">
            暂无操作结果。
          </div>
        </section>

        <section class="card">
          <h2 class="mb-4 text-xl font-bold text-gray-800 dark:text-white">下一动作</h2>
          <div class="space-y-2">
            <div v-for="item in candidates?.next_actions || []" :key="item.action" class="rounded-lg border border-gray-100 p-3 dark:border-gray-700">
              <div class="flex items-center justify-between gap-3">
                <p class="text-sm font-medium text-gray-800 dark:text-white">{{ item.action }}</p>
                <span class="text-xs text-gray-500">{{ item.priority }}</span>
              </div>
              <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ item.reason }}</p>
            </div>
          </div>
        </section>
      </aside>
    </div>

    <div class="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
      <section class="card">
        <div class="mb-5 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p class="mb-2 text-sm font-semibold text-blue-500">Import Issue Governance / 来源问题治理</p>
            <h2 class="text-xl font-bold text-gray-800 dark:text-white">导入 Issue 复核队列</h2>
            <p class="mt-1 max-w-3xl text-sm text-gray-500 dark:text-gray-400">
              {{ importQueue?.principle || '历史导入 issue 必须带 reviewer 与 resolution 才能关闭，不允许用代码自动刷掉来源问题。' }}
            </p>
          </div>
          <button
            class="rounded-lg border border-gray-200 px-4 py-2 text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-60 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
            :disabled="issueLoading"
            @click="loadImportGovernance"
          >
            {{ issueLoading ? '刷新中...' : '刷新 Issue' }}
          </button>
        </div>

        <div
          v-if="issueLoadError"
          class="mb-5 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300"
        >
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <p>{{ issueLoadError }}</p>
            <button class="rounded-lg bg-red-500 px-3 py-2 text-white hover:bg-red-600" @click="loadImportGovernance">
              重试 Issue
            </button>
          </div>
        </div>

        <div class="mb-5 grid grid-cols-1 gap-4 md:grid-cols-4">
          <MetricCard label="导入质量分" :value="importQuality?.quality_score ?? '-'" tone="blue" />
          <MetricCard label="Active Issue" :value="importQueue?.summary.active ?? importQuality?.totals.active_issues ?? 0" tone="amber" />
          <MetricCard label="已关闭" :value="importQueue?.summary.resolved ?? importQuality?.quality_debt?.resolved_issues ?? 0" tone="emerald" />
          <MetricCard label="自动修复项" :value="importQuality?.quality_debt?.auto_repairable_fields ?? 0" />
        </div>

        <div class="mb-4 flex flex-wrap gap-2">
          <button
            v-for="status in issueStatuses"
            :key="status.value"
            class="rounded-lg border px-3 py-2 text-sm transition-colors"
            :class="issueStatus === status.value ? 'border-blue-300 bg-blue-50 text-blue-700 dark:border-blue-800 dark:bg-blue-900/20 dark:text-blue-300' : 'border-gray-200 text-gray-600 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800'"
            @click="setIssueStatus(status.value)"
          >
            {{ status.label }}
          </button>
          <button
            class="rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-600 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
            @click="selectVisibleIssues"
          >
            选择当前页
          </button>
          <button
            class="rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-600 transition-colors hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-800"
            @click="clearIssueSelection"
          >
            清空选择
          </button>
        </div>

        <div class="space-y-3">
          <EmptyState
            v-if="issueLoadError && !importQueue?.items.length && !issueLoading"
            type="error"
            title="导入 Issue 加载失败"
            description="导入质量队列暂时不可用，请稍后重试；已加载的发布候选不会被清空。"
            action-text="重试 Issue"
            @action="loadImportGovernance"
          />
          <button
            v-for="issue in issueLoadError ? [] : importQueue?.items || []"
            :key="issue.id"
            class="w-full rounded-lg border p-4 text-left transition-colors"
            :class="selectedIssueIds.includes(issue.id) ? 'border-blue-300 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20' : 'border-gray-200 bg-white hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-900 dark:hover:bg-gray-800'"
            @click="selectIssue(issue)"
          >
            <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div class="min-w-0">
                <div class="mb-2 flex flex-wrap items-center gap-2">
                  <span class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">#{{ issue.id }}</span>
                  <span class="rounded px-2 py-1 text-xs" :class="issueStatusClass(issue.status)">{{ issueStatusLabel(issue.status) }}</span>
                  <span class="rounded px-2 py-1 text-xs" :class="issue.severity === 'error' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'">
                    {{ issue.severity }}
                  </span>
                  <span v-if="selectedIssueIds.includes(issue.id)" class="rounded bg-blue-100 px-2 py-1 text-xs text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">已选</span>
                </div>
                <p class="truncate font-semibold text-gray-800 dark:text-white">{{ issue.source_name }}</p>
                <p class="mt-1 line-clamp-2 text-sm text-gray-500 dark:text-gray-400">{{ issue.message }}</p>
              </div>
              <div class="shrink-0 text-left text-xs text-gray-400 lg:text-right">
                <p>{{ issue.source_id || 'no source id' }}</p>
                <p class="mt-1">{{ formatDate(issue.updated_at || issue.created_at) }}</p>
              </div>
            </div>
          </button>
          <div v-if="!issueLoading && !importQueue?.items.length" class="rounded-lg bg-gray-50 p-8 text-center text-gray-500 dark:bg-gray-800">
            当前筛选下没有导入 issue。
          </div>
          <div v-if="issueLoading" class="rounded-lg bg-gray-50 p-8 text-center text-gray-500 dark:bg-gray-800">加载 issue 中...</div>
        </div>
      </section>

      <aside class="space-y-6">
        <section class="card">
          <div class="mb-5 flex items-center justify-between gap-3">
            <div>
              <h2 class="text-xl font-bold text-gray-800 dark:text-white">Issue 操作</h2>
              <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">关闭必须写入人工说明。</p>
            </div>
            <ClipboardCheck class="h-5 w-5 text-blue-500" />
          </div>

          <div v-if="selectedIssue" class="space-y-4">
            <div class="rounded-lg bg-gray-50 p-4 dark:bg-gray-800">
              <p class="truncate font-semibold text-gray-800 dark:text-white">{{ selectedIssue.source_name }}</p>
              <p class="mt-1 text-sm text-gray-500">{{ issueStatusLabel(selectedIssue.status) }} · {{ selectedIssue.severity }} · 已选 {{ selectedIssueIds.length }} 条</p>
            </div>

            <label class="block">
              <span class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200">动作</span>
              <select v-model="issueAction" class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-gray-800 dark:border-gray-700 dark:bg-gray-900 dark:text-white">
                <option value="resolve">确认关闭</option>
                <option value="request_review">请求复审</option>
                <option value="reopen">重新打开</option>
              </select>
            </label>

            <label class="block">
              <span class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200">审阅人</span>
              <input v-model="issueReviewerId" class="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-gray-800 dark:border-gray-700 dark:bg-gray-900 dark:text-white" />
            </label>

            <label class="block">
              <span class="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-200">处理说明</span>
              <textarea v-model="issueResolution" rows="4" class="w-full resize-none rounded-lg border border-gray-200 bg-white px-3 py-2 text-gray-800 dark:border-gray-700 dark:bg-gray-900 dark:text-white"></textarea>
            </label>

            <div class="grid grid-cols-2 gap-3">
              <button class="rounded-lg border border-gray-200 px-3 py-2 text-gray-700 hover:bg-gray-50 disabled:opacity-60 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800" :disabled="issueActionRunning" @click="runIssueDryRun">
                Dry-run
              </button>
              <button class="rounded-lg bg-blue-500 px-3 py-2 text-white hover:bg-blue-600 disabled:opacity-60" :disabled="issueActionRunning || !issueDryRunResult" @click="runIssueApply">
                写入审计
              </button>
            </div>
          </div>
          <div v-else class="rounded-lg bg-gray-50 p-6 text-center text-sm text-gray-500 dark:bg-gray-800">
            选择一个导入 issue 后开始复核。
          </div>
        </section>

        <section class="card">
          <h2 class="mb-4 text-xl font-bold text-gray-800 dark:text-white">Issue 审计</h2>
          <div v-if="issueActionError" class="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">{{ issueActionError }}</div>
          <div v-if="issueDryRunResult" class="mb-4 rounded-lg bg-blue-50 p-3 dark:bg-blue-900/20">
            <p class="font-semibold text-blue-700 dark:text-blue-300">预演：{{ issueTransitionText(issueDryRunResult) }}</p>
            <p class="mt-1 text-sm text-blue-600 dark:text-blue-300">影响 {{ issueDryRunResult.transitions.length }} 条 issue</p>
            <p class="mt-1 text-sm text-blue-600 dark:text-blue-300">{{ issueDryRunResult.governance_report.next_action }}</p>
            <p class="mt-1 text-sm text-blue-600 dark:text-blue-300">{{ issueDryRunResult.principle }}</p>
          </div>
          <div v-if="issueApplyResult" class="rounded-lg bg-emerald-50 p-3 dark:bg-emerald-900/20">
            <p class="font-semibold text-emerald-700 dark:text-emerald-300">已写入：{{ issueTransitionText(issueApplyResult) }}</p>
            <p class="mt-1 text-sm text-emerald-600 dark:text-emerald-300">影响 {{ issueApplyResult.transitions.length }} 条 issue</p>
            <p class="mt-1 text-sm text-emerald-600 dark:text-emerald-300">日志 {{ issueApplyResult.audit_logs?.map((log) => `#${log.id}`).join('、') }}</p>
            <p class="mt-1 break-all text-xs text-emerald-600 dark:text-emerald-300">说明哈希 {{ issueApplyResult.governance_report.resolution_hash || '-' }}</p>
          </div>
          <div v-if="!issueDryRunResult && !issueApplyResult && !issueActionError" class="rounded-lg bg-gray-50 p-6 text-center text-sm text-gray-500 dark:bg-gray-800">
            暂无 issue 操作结果。
          </div>
        </section>

        <section class="card">
          <div class="mb-4 flex items-start justify-between gap-3">
            <div>
              <h2 class="text-xl font-bold text-gray-800 dark:text-white">审计历史</h2>
              <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">只展示状态、哈希和安全标记。</p>
            </div>
            <span class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">
              {{ issueAudit?.summary.unsafe_log_count ?? 0 }} unsafe
            </span>
          </div>
          <div class="mb-3 rounded-lg bg-gray-50 p-3 text-xs text-gray-500 dark:bg-gray-800 dark:text-gray-400">
            {{ issueAudit?.principle || '导入 issue 审计历史不回显人工说明全文或来源原文。' }}
          </div>
          <div class="space-y-2">
            <div v-for="log in issueAudit?.items || []" :key="log.id" class="rounded-lg border border-gray-100 p-3 dark:border-gray-700">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate text-sm font-semibold text-gray-800 dark:text-white">#{{ log.issue_id }} · {{ issueActionLabel(log.action) }}</p>
                  <p class="mt-1 truncate text-xs text-gray-500 dark:text-gray-400">{{ log.source_name || 'unknown source' }}</p>
                </div>
                <span class="shrink-0 rounded px-2 py-1 text-xs" :class="issueStatusClass(log.to_status || '')">
                  {{ log.from_status || '-' }} -> {{ log.to_status || '-' }}
                </span>
              </div>
              <div class="mt-3 grid grid-cols-1 gap-2 text-xs text-gray-500 dark:text-gray-400">
                <p>reviewer: {{ log.reviewer_id || '-' }}</p>
                <p class="break-all">resolution: {{ log.resolution_hash || '-' }}</p>
                <p>{{ formatDate(log.created_at) }} · raw={{ log.safety.raw_source_text_saved ? 'yes' : 'no' }} · text={{ log.safety.resolution_text_returned ? 'yes' : 'no' }}</p>
              </div>
            </div>
            <div v-if="!issueAudit?.items.length" class="rounded-lg bg-gray-50 p-6 text-center text-sm text-gray-500 dark:bg-gray-800">
              暂无导入 issue 审计历史。
            </div>
          </div>
        </section>

        <section class="card">
          <h2 class="mb-4 text-xl font-bold text-gray-800 dark:text-white">来源优先级</h2>
          <div class="space-y-2">
            <button
              v-for="group in importQueue?.source_groups || []"
              :key="group.source_name"
              class="w-full rounded-lg border border-gray-100 p-3 text-left transition-colors hover:bg-gray-50 dark:border-gray-700 dark:hover:bg-gray-800"
              @click="selectGroupIssues(group.sample_issue_ids)"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate text-sm font-semibold text-gray-800 dark:text-white">{{ group.source_name }}</p>
                  <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ group.recommended_action }}</p>
                </div>
                <div class="shrink-0 text-right">
                  <p class="font-semibold text-amber-600 dark:text-amber-300">{{ group.active_issues }}</p>
                  <p class="text-xs text-gray-400">active</p>
                </div>
              </div>
              <div class="mt-3 flex flex-wrap gap-2">
                <span v-for="[status, count] in Object.entries(group.by_status)" :key="status" class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">
                  {{ issueStatusLabel(status) }} {{ count }}
                </span>
              </div>
              <div class="mt-3 rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
                <div class="mb-2 flex items-start justify-between gap-3">
                  <p class="text-xs font-semibold text-gray-700 dark:text-gray-200">来源复核包</p>
                  <span class="shrink-0 rounded px-2 py-1 text-xs" :class="group.review_packet.batch_action.can_close_batch ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300' : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'">
                    {{ group.review_packet.batch_action.default_action }}
                  </span>
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ group.review_packet.principle }}</p>
                <div class="mt-2 space-y-1">
                  <p
                    v-for="item in group.review_packet.evidence_checklist.slice(0, 3)"
                    :key="item.id"
                    class="text-xs text-gray-500 dark:text-gray-400"
                  >
                    {{ item.label }} · {{ item.required_for }}
                  </p>
                </div>
                <div class="mt-2 space-y-1">
                  <p
                    v-for="sample in group.review_packet.sample_evidence.slice(0, 2)"
                    :key="sample.issue_id"
                    class="break-all text-xs text-gray-500 dark:text-gray-400"
                  >
                    #{{ sample.issue_id }} · {{ sample.severity }} · {{ sample.message_hash }}
                  </p>
                </div>
              </div>
            </button>
            <div v-if="!importQueue?.source_groups.length" class="rounded-lg bg-gray-50 p-6 text-center text-sm text-gray-500 dark:bg-gray-800">
              暂无来源分组。
            </div>
          </div>
        </section>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref } from 'vue'
import { ClipboardCheck, ShieldCheck } from 'lucide-vue-next'
import EmptyState from '@/components/EmptyState.vue'
import { evolutionApi, resourcesApi } from '@/utils/api'
import type {
  EvolutionImportQuality,
  ImportIssue,
  ImportIssueActionPayload,
  ImportIssueActionResult,
  ImportIssueAuditHistory,
  ImportIssueQueue,
  ImportIssueStatus,
  ResourceSimilarityActionPayload,
  ResourceSimilarityActionResult,
  ResourceSimilarityRewriteResult,
  ResourceSimilarityQueue,
  ReviewedAssetActionPayload,
  ReviewedAssetActionResult,
  ReviewedAssetCandidate,
  ReviewedAssetCandidates,
} from '@/utils/api'

const candidates = ref<ReviewedAssetCandidates | null>(null)
const selected = ref<ReviewedAssetCandidate | null>(null)
const action = ref<ReviewedAssetActionPayload['action']>('confirm_publish')
const reviewerId = ref('governance-console')
const reason = ref('quality gate accepted')
const loading = ref(false)
const loadError = ref('')
const actionRunning = ref(false)
const dryRunResult = ref<ReviewedAssetActionResult | null>(null)
const applyResult = ref<ReviewedAssetActionResult | null>(null)
const actionError = ref('')
const importQuality = ref<EvolutionImportQuality | null>(null)
const importQueue = ref<ImportIssueQueue | null>(null)
const issueStatus = ref<ImportIssueStatus>('active')
const selectedIssue = ref<ImportIssue | null>(null)
const selectedIssueIds = ref<number[]>([])
const issueAction = ref<ImportIssueActionPayload['action']>('resolve')
const issueReviewerId = ref('import-governance-console')
const issueResolution = ref('已核对来源登记与导入批次报告，确认该历史 issue 可关闭。')
const issueLoading = ref(false)
const issueLoadError = ref('')
const issueActionRunning = ref(false)
const issueDryRunResult = ref<ImportIssueActionResult | null>(null)
const issueApplyResult = ref<ImportIssueActionResult | null>(null)
const issueAudit = ref<ImportIssueAuditHistory | null>(null)
const issueActionError = ref('')
const similarityQueue = ref<ResourceSimilarityQueue | null>(null)
const similarityLoading = ref(false)
const similarityError = ref('')
const similarityActionRunning = ref(false)
const similarityActionError = ref('')
const similarityActionResult = ref<ResourceSimilarityActionResult | null>(null)
const similarityRewriteResult = ref<ResourceSimilarityRewriteResult | null>(null)

const selectedKey = computed(() => selected.value ? candidateKey(selected.value) : '')
const issueStatuses: Array<{ label: string; value: ImportIssueStatus }> = [
  { label: 'Active', value: 'active' },
  { label: 'Open', value: 'open' },
  { label: '复审中', value: 'review_requested' },
  { label: '已关闭', value: 'resolved' },
  { label: '已重开', value: 'reopened' },
]

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    candidates.value = await evolutionApi.publishCandidates(40)
    if (!selected.value && candidates.value.items.length) {
      selectCandidate(candidates.value.items[0])
    }
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '发布候选加载失败，请重试'
  } finally {
    loading.value = false
  }
}

async function loadImportGovernance() {
  issueLoading.value = true
  issueLoadError.value = ''
  try {
    const [quality, queue] = await Promise.all([
      evolutionApi.importQuality(),
      evolutionApi.importIssues(issueStatus.value, 100),
    ])
    importQuality.value = quality
    importQueue.value = queue
    issueAudit.value = await evolutionApi.importIssueAudit(30)
    if (!selectedIssue.value && queue.items.length) {
      selectIssue(queue.items[0])
    }
    if (selectedIssue.value && !queue.items.some((item) => item.id === selectedIssue.value?.id)) {
      selectedIssue.value = queue.items[0] ?? null
    }
    selectedIssueIds.value = selectedIssueIds.value.filter((id) => queue.items.some((item) => item.id === id))
    if (!selectedIssueIds.value.length && selectedIssue.value) {
      selectedIssueIds.value = [selectedIssue.value.id]
    }
  } catch (error) {
    issueLoadError.value = error instanceof Error ? error.message : '导入 Issue 加载失败，请重试'
  } finally {
    issueLoading.value = false
  }
}

async function loadSimilarityQueue() {
  similarityLoading.value = true
  similarityError.value = ''
  try {
    similarityQueue.value = await resourcesApi.similarity({ limit: 1000, threshold: 0.82, max_clusters: 12 })
  } catch (error) {
    similarityError.value = error instanceof Error ? error.message : '近重复队列加载失败，请重试'
  } finally {
    similarityLoading.value = false
  }
}

async function runSimilarityClusterAction(
  cluster: ResourceSimilarityQueue['clusters'][number],
  actionName: ResourceSimilarityActionPayload['action'],
  dryRun: boolean,
) {
  const sorted = [...cluster.items].sort((left, right) => (right.quality_score || 0) - (left.quality_score || 0))
  const resourceIds = actionName === 'quarantine_variants'
    ? sorted.slice(1).map((item) => item.id)
    : sorted.map((item) => item.id)
  if (!resourceIds.length) return
  similarityActionRunning.value = true
  similarityActionError.value = ''
  try {
    const result = await resourcesApi.similarityAction({
      resource_ids: resourceIds,
      action: actionName,
      reviewer_id: 'resource-similarity-console',
      reason: `${cluster.family_key} 近重复治理：${similarityActionLabel(actionName)}`,
      dry_run: dryRun,
    })
    similarityActionResult.value = result
    similarityRewriteResult.value = null
    if (!dryRun) {
      await loadSimilarityQueue()
    }
  } catch (error) {
    similarityActionError.value = error instanceof Error ? error.message : '近重复治理操作失败'
  } finally {
    similarityActionRunning.value = false
  }
}

async function runSimilarityRewrite(cluster: ResourceSimilarityQueue['clusters'][number], dryRun: boolean) {
  const resourceIds = cluster.items.map((item) => item.id)
  if (!resourceIds.length) return
  similarityActionRunning.value = true
  similarityActionError.value = ''
  try {
    const result = await resourcesApi.similarityRewriteBatch({
      resource_ids: resourceIds,
      reviewer_id: 'resource-rewrite-console',
      reason: `${cluster.family_key} 近重复家族需要具体案例补位`,
      dry_run: dryRun,
      mark_originals_quarantine: true,
    })
    similarityRewriteResult.value = result
    similarityActionResult.value = null
    if (!dryRun) {
      await loadSimilarityQueue()
    }
  } catch (error) {
    similarityActionError.value = error instanceof Error ? error.message : '近重复重写补位失败'
  } finally {
    similarityActionRunning.value = false
  }
}

async function setIssueStatus(status: ImportIssueStatus) {
  issueStatus.value = status
  selectedIssue.value = null
  selectedIssueIds.value = []
  issueDryRunResult.value = null
  issueApplyResult.value = null
  issueActionError.value = ''
  await loadImportGovernance()
}

function selectCandidate(item: ReviewedAssetCandidate) {
  selected.value = item
  action.value = item.review_status === 'published' ? 'withdraw' : 'confirm_publish'
  dryRunResult.value = null
  applyResult.value = null
  actionError.value = ''
}

async function runDryRun() {
  await runAction(true)
}

async function runApply() {
  await runAction(false)
  await load()
}

async function runAction(dryRun: boolean) {
  if (!selected.value) return
  actionRunning.value = true
  actionError.value = ''
  try {
    const result = await evolutionApi.reviewedAssetAction({
      asset_type: selected.value.asset_type,
      asset_id: selected.value.id,
      action: action.value,
      reviewer_id: reviewerId.value,
      reason: reason.value,
      dry_run: dryRun,
    })
    if (dryRun) {
      dryRunResult.value = result
      applyResult.value = null
    } else {
      applyResult.value = result
      selected.value = result.asset
    }
  } catch (error) {
    actionError.value = error instanceof Error ? error.message : '操作失败'
  } finally {
    actionRunning.value = false
  }
}

function selectIssue(issue: ImportIssue) {
  selectedIssue.value = issue
  if (selectedIssueIds.value.includes(issue.id)) {
    selectedIssueIds.value = selectedIssueIds.value.filter((id) => id !== issue.id)
    if (!selectedIssueIds.value.length) {
      selectedIssueIds.value = [issue.id]
    }
  } else {
    selectedIssueIds.value = [...selectedIssueIds.value, issue.id]
  }
  issueAction.value = issue.status === 'resolved' ? 'reopen' : 'resolve'
  issueDryRunResult.value = null
  issueApplyResult.value = null
  issueActionError.value = ''
}

function selectVisibleIssues() {
  selectedIssueIds.value = (importQueue.value?.items || []).map((issue) => issue.id)
  selectedIssue.value = importQueue.value?.items[0] || null
  issueDryRunResult.value = null
  issueApplyResult.value = null
}

function clearIssueSelection() {
  selectedIssueIds.value = []
  selectedIssue.value = null
  issueDryRunResult.value = null
  issueApplyResult.value = null
  issueActionError.value = ''
}

function selectGroupIssues(issueIds: number[]) {
  selectedIssueIds.value = issueIds
  selectedIssue.value = (importQueue.value?.items || []).find((issue) => issueIds.includes(issue.id)) || selectedIssue.value
  issueDryRunResult.value = null
  issueApplyResult.value = null
  issueActionError.value = ''
}

async function runIssueDryRun() {
  await runIssueAction(true)
}

async function runIssueApply() {
  await runIssueAction(false)
  await loadImportGovernance()
}

async function runIssueAction(dryRun: boolean) {
  const issueIds = selectedIssueIds.value.length ? selectedIssueIds.value : (selectedIssue.value ? [selectedIssue.value.id] : [])
  if (!issueIds.length) return
  issueActionRunning.value = true
  issueActionError.value = ''
  try {
    const result = await evolutionApi.importIssueAction({
      issue_ids: issueIds,
      action: issueAction.value,
      reviewer_id: issueReviewerId.value,
      resolution: issueResolution.value,
      dry_run: dryRun,
    })
    if (dryRun) {
      issueDryRunResult.value = result
      issueApplyResult.value = null
    } else {
      issueApplyResult.value = result
      issueDryRunResult.value = null
    }
  } catch (error) {
    issueActionError.value = error instanceof Error ? error.message : 'Issue 操作失败'
  } finally {
    issueActionRunning.value = false
  }
}

function candidateKey(item: ReviewedAssetCandidate) {
  return `${item.asset_type}:${item.id}`
}

function assetTypeLabel(type: string) {
  return type === 'resource' ? '连接素材' : '知识条目'
}

function priorityClass(score: number) {
  if (score >= 85) return 'text-emerald-600 dark:text-emerald-300'
  if (score >= 70) return 'text-blue-600 dark:text-blue-300'
  return 'text-amber-600 dark:text-amber-300'
}

function issueStatusLabel(status: string) {
  const labels: Record<string, string> = {
    active: 'Active',
    open: 'Open',
    review_requested: '复审中',
    resolved: '已关闭',
    reopened: '已重开',
    all: '全部',
  }
  return labels[status] || status
}

function issueStatusClass(status: string) {
  if (status === 'resolved') return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
  if (status === 'review_requested') return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
  if (status === 'reopened') return 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300'
  return 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
}

function issueTransitionText(result: ImportIssueActionResult) {
  const transition = result.transitions[0]
  return transition ? `${transition.from_status} -> ${transition.to_status}` : result.action
}

function issueActionLabel(action: string) {
  const labels: Record<string, string> = {
    resolve: '确认关闭',
    request_review: '请求复审',
    reopen: '重新打开',
  }
  return labels[action] || action
}

function formatDate(value: string) {
  return new Date(value).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

function qualitySignal(item: ReviewedAssetCandidate) {
  return Object.entries(item.quality_signal)
    .map(([key, value]) => `${key}: ${value ?? '-'}`)
    .join(' · ')
}

function similarityActionLabel(action: string) {
  const labels: Record<string, string> = {
    merge_or_hide_variants: '合并/隐藏变体',
    rewrite_family_with_distinct_cases: '重写为不同案例',
    keep_but_diversify_sorting: '保留但打散',
    quarantine_variants: '隔离低质变体',
    request_review: '请求复审',
    restore_reviewed: '恢复 reviewed',
  }
  return labels[action] || action
}

function similarityStatusSummary(result: ResourceSimilarityActionResult) {
  return Object.entries(result.governance_report.to_status_counts)
    .map(([status, count]) => `${status} ${count}`)
    .join(' · ')
}

const MetricCard = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: [String, Number], required: true },
    tone: { type: String, default: 'gray' },
  },
  setup(props) {
    const toneClass = computed(() => {
      if (props.tone === 'emerald') return 'text-emerald-600 dark:text-emerald-300'
      if (props.tone === 'blue') return 'text-blue-600 dark:text-blue-300'
      if (props.tone === 'amber') return 'text-amber-600 dark:text-amber-300'
      return 'text-gray-800 dark:text-white'
    })
    return () => h('div', { class: 'rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800' }, [
      h('p', { class: 'text-sm text-gray-500 dark:text-gray-400' }, props.label),
      h('p', { class: `mt-2 text-3xl font-bold ${toneClass.value}` }, String(props.value)),
    ])
  },
})

onMounted(() => {
  void load()
  void loadSimilarityQueue()
  void loadImportGovernance()
})
</script>
