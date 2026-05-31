<template>
  <div class="p-8">
    <div class="mb-8 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <h1 class="text-3xl font-bold text-gray-800 dark:text-white">浏览冲浪</h1>
        <p class="mt-2 text-gray-500 dark:text-gray-400">按高质量信息源浏览关系研究、课程、数据、故事和互动训练入口。</p>
        <p class="mt-1 text-sm text-sky-600 dark:text-sky-300">任何事情的发展都没有奇迹，只有轨迹：来源登记、原创转化、练习反馈和审计报告要连成闭环。</p>
      </div>
      <RouterLink to="/resources" class="btn-secondary">返回资源库</RouterLink>
    </div>

    <ModuleTabs
      v-model="activeTab"
      :tabs="surfTabs"
      label="浏览冲浪选项卡"
      id-prefix="surf-tab"
      class="mb-6"
      @update:model-value="onTabChange"
    />

    <div
      v-if="activeTab === 'collection_strategy'"
      class="mb-6 rounded-lg border border-sky-100 bg-sky-50 p-4 text-sm leading-6 text-sky-800 dark:border-sky-900/40 dark:bg-sky-900/20 dark:text-sky-200"
    >
      <p class="font-semibold">采集策略</p>
      <p class="mt-1">外部来源只转成链接、标题、摘要、短摘录、结构化分析和本地原创改写；不默认保存第三方全文，也不把摘要伪装成原文。</p>
    </div>

    <div class="mb-6 grid grid-cols-1 gap-3 rounded-lg bg-white p-4 shadow-sm dark:bg-gray-800 md:grid-cols-[1fr_260px]">
      <div class="relative">
        <input
          v-model.trim="query"
          class="input-mac"
          placeholder="搜索来源、主题、摘要、结构，例如：Gottman、边界、修复、沟通课程"
          aria-haspopup="listbox"
          :aria-expanded="searchMenuOpen"
          @focus="openSearchMenu"
          @click="openSearchMenu"
          @input="openSearchMenu"
          @blur="closeSearchMenuSoon"
          @keydown.escape="searchMenuOpen = false"
        />
        <div
          v-if="searchMenuOpen && visibleSearchSuggestionGroups.length"
          class="absolute left-0 right-0 top-full z-40 mt-2 max-h-96 overflow-auto rounded-lg border border-gray-100 bg-white p-3 shadow-xl dark:border-gray-700 dark:bg-gray-900"
          role="listbox"
          data-surf-search-menu
        >
          <div class="mb-2 flex items-center justify-between gap-2 border-b border-gray-100 pb-2 dark:border-gray-800">
            <p class="text-xs font-semibold text-gray-700 dark:text-gray-200">从当前数据库来源中选择，也可以继续手动输入</p>
            <span class="text-[11px] text-gray-400">{{ sources.length }} 个来源</span>
          </div>
          <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div v-for="suggestionGroup in visibleSearchSuggestionGroups" :key="suggestionGroup.name">
              <p class="mb-1 text-[11px] font-semibold text-gray-500 dark:text-gray-400">{{ suggestionGroup.name }}</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="item in suggestionGroup.items"
                  :key="`${suggestionGroup.name}-${item}`"
                  type="button"
                  class="rounded-full bg-gray-100 px-3 py-1.5 text-xs text-gray-700 hover:bg-sky-100 hover:text-sky-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-sky-950/50 dark:hover:text-sky-200"
                  :class="query === item ? 'bg-sky-100 text-sky-700 dark:bg-sky-950/60 dark:text-sky-200' : ''"
                  @mousedown.prevent="applySearchSuggestion(item)"
                >
                  {{ item }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      <select v-model="group" class="input-mac" @change="syncQueryToUrl">
        <option value="">全部来源组</option>
        <option v-for="option in groupOptions" :key="option.value" :value="option.value">
          {{ option.value }} · {{ option.count }}
        </option>
      </select>
    </div>

    <div v-if="loading" class="py-16 text-center text-gray-400">加载信息源...</div>
    <div v-else-if="loadError" class="rounded-lg border border-red-100 bg-red-50 p-6 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-200">
      <p class="font-semibold">信息源加载失败</p>
      <p class="mt-2 leading-6">{{ loadError }}</p>
      <button type="button" class="mt-4 rounded-lg bg-red-600 px-3 py-2 text-xs font-semibold text-white hover:bg-red-700" @click="loadSources">
        重新加载
      </button>
    </div>

    <div
      v-else
      class="grid grid-cols-1 gap-5 transition-[grid-template-columns] xl:grid-cols-[minmax(0,1fr)_280px]"
      :class="tocCollapsed ? 'xl:!grid-cols-1' : ''"
    >
      <div>
        <div class="mb-4 flex flex-col gap-2 rounded-lg border border-gray-100 bg-white p-4 text-sm text-gray-600 shadow-sm dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="font-semibold text-gray-800 dark:text-white">{{ activeTabTitle }}</p>
            <p class="mt-1">
              当前显示 {{ filteredSources.length }} / {{ sources.length }} 个信息源
              <span v-if="group"> · 来源组：{{ group }}</span>
              <span v-if="query"> · 搜索：{{ query }}</span>
            </p>
          </div>
          <button v-if="query || group" type="button" class="rounded-lg bg-gray-100 px-3 py-2 text-xs font-semibold text-gray-600 hover:bg-gray-200 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-700" @click="clearFilters">
            清空条件
          </button>
        </div>

        <div v-if="filteredSources.length === 0" class="rounded-lg border border-dashed border-gray-200 bg-white p-8 text-center text-sm text-gray-500 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-400">
          <p class="font-semibold text-gray-700 dark:text-gray-200">没有匹配的信息源</p>
          <p class="mt-2">请换一个关键词，或清空来源组筛选后重新浏览。</p>
          <button type="button" class="mt-4 btn-secondary" @click="clearFilters">清空条件</button>
        </div>

        <div v-else class="grid grid-cols-1 gap-5 xl:grid-cols-2">
        <article
          v-for="(source, index) in filteredSources"
          :id="sourceAnchor(source, index)"
          :key="`${source.source}-${source.source_url}`"
          class="scroll-mt-24 rounded-lg border border-gray-100 bg-white p-5 shadow-sm dark:border-gray-700 dark:bg-gray-800"
        >
          <div class="mb-3 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p class="text-xs font-semibold text-sky-600 dark:text-sky-300">{{ source.group || '信息源' }}</p>
              <h2 class="mt-1 text-lg font-bold">
                <a
                  :href="source.source_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="break-words text-gray-800 underline-offset-4 hover:text-sky-600 hover:underline dark:text-white dark:hover:text-sky-300"
                >
                  {{ index + 1 }}. {{ source.name || cleanSource(source.source) }}
                </a>
              </h2>
            </div>
            <a
              :href="source.source_url"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex shrink-0 items-center rounded-md bg-sky-50 px-3 py-2 text-sm font-semibold text-sky-700 hover:bg-sky-100 dark:bg-sky-900/20 dark:text-sky-300"
            >
              打开网站
            </a>
          </div>

          <p class="text-sm leading-7 text-gray-600 dark:text-gray-300">{{ source.summary || '暂无摘要。' }}</p>
          <div class="mt-3 space-y-2 text-xs leading-6 text-gray-500 dark:text-gray-400">
            <p v-if="source.structure"><span class="font-semibold text-gray-700 dark:text-gray-200">内容结构：</span>{{ source.structure }}</p>
            <p v-if="source.quality_notes"><span class="font-semibold text-gray-700 dark:text-gray-200">质量说明：</span>{{ source.quality_notes }}</p>
            <p><span class="font-semibold text-gray-700 dark:text-gray-200">链接状态：</span>{{ sourceHealthLabel(source) }}</p>
            <p v-if="source.health?.last_checked_at">
              <span class="font-semibold text-gray-700 dark:text-gray-200">最后检查：</span>{{ source.health.last_checked_at }}
            </p>
            <p v-if="source.health?.redirect_url" class="break-words">
              <span class="font-semibold text-gray-700 dark:text-gray-200">跳转到：</span>{{ source.health.redirect_url }}
            </p>
            <p><span class="font-semibold text-gray-700 dark:text-gray-200">库内资源：</span>{{ source.count }} 条</p>
            <p class="break-words"><span class="font-semibold text-gray-700 dark:text-gray-200">链接：</span>{{ source.source_url }}</p>
          </div>

          <div class="mt-4 flex flex-wrap gap-2">
            <button
              v-for="theme in source.themes || []"
              :key="theme"
              class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300"
              @click="openResourceSearch(theme, source.name || source.source)"
            >
              {{ theme }}
            </button>
          </div>
        </article>
        </div>
      </div>

      <PageTocSidebar v-model:collapsed="tocCollapsed" title="来源目录" :items="tocItems" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ModuleTabs from '@/components/ModuleTabs.vue'
import PageTocSidebar from '@/components/PageTocSidebar.vue'
import { resourcesApi } from '@/utils/api'
import type { ResourceSourceItem } from '@/utils/api'

interface TocItem {
  id: string
  anchor: string
  title: string
  indexLabel?: string
}

const router = useRouter()
const route = useRoute()
const sources = ref<ResourceSourceItem[]>([])
const loading = ref(false)
const loadError = ref('')
const query = ref('')
const group = ref('')
const tocCollapsed = ref(false)
const searchMenuOpen = ref(false)
const activeTab = ref('all_sources')

const surfTabs = [
  { id: 'all_sources', label: '全部来源', summary: '浏览当前数据库登记的全部外部信息源。' },
  { id: 'collection_strategy', label: '采集策略', summary: '把外部来源转成合规结构化素材。' },
  { id: 'link_health', label: '链接健康', summary: '查看来源是否可访问、是否跳转、是否需要复核。' },
]

const activeTabTitle = computed(() => {
  if (activeTab.value === 'link_health') return '链接健康清单'
  if (activeTab.value === 'collection_strategy') return '可采集来源清单'
  return '来源清单'
})

const groupOptions = computed(() => {
  const counts = new Map<string, number>()
  for (const source of sources.value) {
    const name = source.group?.trim()
    if (name) counts.set(name, (counts.get(name) || 0) + 1)
  }
  return Array.from(counts.entries())
    .map(([value, count]) => ({ value, count }))
    .sort((a, b) => b.count - a.count || a.value.localeCompare(b.value, 'zh-Hans-CN'))
})

const searchSuggestionGroups = computed(() => [
  { name: '来源名称', items: uniqueStrings(sources.value.map((source) => source.name || cleanSource(source.source))).slice(0, 18) },
  { name: '来源组', items: groupOptions.value.map((option) => option.value).slice(0, 12) },
  { name: '主题标签', items: uniqueStrings(sources.value.flatMap((source) => source.themes || [])).slice(0, 24) },
  { name: '适用场景', items: uniqueStrings(sources.value.flatMap((source) => source.scenes || [])).slice(0, 16) },
  { name: '网站域名', items: uniqueStrings(sources.value.map((source) => sourceHost(source.source_url))).slice(0, 18) },
])

const visibleSearchSuggestionGroups = computed(() => {
  const needle = query.value.toLowerCase()
  return searchSuggestionGroups.value
    .map((suggestionGroup) => ({
      ...suggestionGroup,
      items: suggestionGroup.items
        .filter((item) => !needle || item.toLowerCase().includes(needle))
        .slice(0, 10),
    }))
    .filter((suggestionGroup) => suggestionGroup.items.length > 0)
})

const filteredSources = computed(() => {
  const needle = query.value.toLowerCase()
  return sources.value.filter((source) => {
    if (group.value && source.group !== group.value) return false
    if (activeTab.value === 'link_health' && !source.health?.last_checked_at) return false
    if (!needle) return true
    return [
      source.name,
      source.source,
      source.source_url,
      source.summary,
      source.structure,
      source.quality_notes,
      sourceHost(source.source_url),
      ...(source.themes || []),
      ...(source.scenes || []),
    ].some((value) => String(value || '').toLowerCase().includes(needle))
  })
})

function uniqueStrings(values: Array<string | undefined | null>) {
  return Array.from(new Set(values.map((value) => value?.trim()).filter(Boolean) as string[])).sort((a, b) => a.localeCompare(b, 'zh-Hans-CN'))
}

function sourceHost(url?: string) {
  if (!url) return ''
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url.replace(/^https?:\/\//, '').split('/')[0]
  }
}

function cleanSource(source: string) {
  return source.replace('public_anchor:', '')
}

function sourceAnchor(source: ResourceSourceItem, index: number) {
  const base = `${source.name || source.source || 'source'}-${index}`
  return `surf-${base.toLowerCase().replace(/[^a-z0-9\u4e00-\u9fa5]+/g, '-')}`
}

const tocItems = computed<TocItem[]>(() => (
  filteredSources.value.map((source, index) => ({
    id: `${source.source}-${index}`,
    anchor: sourceAnchor(source, index),
    indexLabel: String(index + 1),
    title: source.name || cleanSource(source.source),
  }))
))

function openResourceSearch(theme: string, source: string) {
  router.push({ path: '/resources', query: { q: theme, source } })
}

function openSearchMenu() {
  searchMenuOpen.value = true
}

function closeSearchMenuSoon() {
  window.setTimeout(() => {
    searchMenuOpen.value = false
  }, 120)
}

function applySearchSuggestion(value: string) {
  query.value = value
  searchMenuOpen.value = false
  syncQueryToUrl()
}

function clearFilters() {
  query.value = ''
  group.value = ''
  syncQueryToUrl()
}

function normalizeTab(value: unknown) {
  const tab = typeof value === 'string' ? value : ''
  return surfTabs.some((item) => item.id === tab) ? tab : 'all_sources'
}

function onTabChange(value: string) {
  activeTab.value = normalizeTab(value)
  syncQueryToUrl()
}

function syncQueryToUrl() {
  const nextQuery: Record<string, string> = {}
  if (activeTab.value !== 'all_sources') nextQuery.tab = activeTab.value
  if (query.value) nextQuery.q = query.value
  if (group.value) nextQuery.group = group.value
  router.replace({ path: '/surf', query: nextQuery })
}

function linkStatusLabel(status?: string) {
  const labels: Record<string, string> = {
    verified_anchor: '核心锚点，已纳入高可信目录',
    registered_https: 'HTTPS 登记来源，进入周期审计',
    registered_http: 'HTTP 登记来源，进入周期审计',
    unknown: '待审计',
  }
  return labels[status || 'unknown'] || status
}

function sourceHealthLabel(source: ResourceSourceItem) {
  if (!source.health?.last_checked_at) return linkStatusLabel(source.link_status)
  const code = source.health.http_code ? `HTTP ${source.health.http_code}` : '无状态码'
  const status = source.health.status === 'ok' ? '可访问' : source.health.status === 'invalid' ? '失效/需复核' : '未知'
  return `${status} · ${code}`
}

async function loadSources() {
  loading.value = true
  loadError.value = ''
  try {
    const data = await resourcesApi.sources(200)
    sources.value = data.items
  } catch (error) {
    sources.value = []
    loadError.value = error instanceof Error ? error.message : '无法读取信息源目录，请稍后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  activeTab.value = normalizeTab(route.query.tab)
  query.value = typeof route.query.q === 'string' ? route.query.q : ''
  group.value = typeof route.query.group === 'string' ? route.query.group : ''
  loadSources()
})
</script>
