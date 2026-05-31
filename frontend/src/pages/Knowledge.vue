<template>
  <div class="p-4 sm:p-6 lg:p-8">
    <div class="mb-8 flex flex-col items-start justify-between gap-4 sm:flex-row sm:gap-6">
      <div>
        <p class="text-sm font-semibold text-indigo-500 mb-2">Knowledge Base / 结构化知识库</p>
        <h1 class="text-3xl font-bold text-gray-800 dark:text-white">知识中枢</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-2">SQLite 是知识内容唯一数据源；HTML 仅保留为旧版 legacy 手册。</p>
      </div>
      <a href="/manual" target="_blank" class="btn-secondary w-full text-center sm:w-auto">旧版 HTML 手册</a>
    </div>

    <ModuleTabs
      v-model="activeTab"
      :tabs="knowledgeTabs"
      label="知识中枢选项卡"
      id-prefix="knowledge-tab"
      class="mb-6"
      @update:model-value="onTabChange"
    />

    <div v-if="activeTab === 'five_w_two_h'" class="space-y-6 mb-8">
      <div class="card">
        <h2 class="text-xl font-bold text-gray-800 dark:text-white">5W2H 元问题工作区</h2>
        <p class="mt-2 text-sm leading-6 text-gray-500 dark:text-gray-400">
          用 Why/What/Who/When/Where/How/How much 把一个概念从“听过”拆成“知道何时用、怎么练、练到什么程度”。
        </p>
      </div>
      <div v-if="visualMap" class="grid grid-cols-1 gap-3 md:grid-cols-2">
        <div v-for="card in visualMap.five_w_two_h_cards" :key="card.key" class="rounded-lg bg-white p-4 shadow-sm dark:bg-gray-800">
          <p class="text-xs font-bold text-indigo-500">{{ card.label }}</p>
          <p class="mt-1 text-base font-semibold text-gray-800 dark:text-white">{{ card.question }}</p>
          <p class="mt-2 text-sm leading-6 text-gray-500 dark:text-gray-400">{{ card.answer }}</p>
        </div>
      </div>
      <div v-else class="card text-center text-gray-500">等待知识导入后生成 5W2H。</div>
    </div>

    <div v-if="activeTab === 'concept_cards' && visualMap" class="space-y-6 mb-8">
      <div class="card">
        <div class="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
          <div>
            <h2 class="text-xl font-bold text-gray-800 dark:text-white">知识数图驾驶舱</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ visualMap.principle }}</p>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-5 gap-3 xl:w-[560px]">
            <div v-for="metric in coverageMetrics" :key="metric.label" class="rounded-lg bg-gray-50 dark:bg-gray-800 p-3">
              <p class="text-xs text-gray-500">{{ metric.label }}</p>
              <p class="text-xl font-bold text-indigo-500 mt-1">{{ metric.value }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-[1.15fr_0.85fr] gap-6">
        <div class="card">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-bold text-gray-800 dark:text-white">概念图谱</h3>
            <span class="text-xs text-gray-500">节点大小代表覆盖量</span>
          </div>
          <div class="relative h-80 rounded-lg bg-gray-50 dark:bg-gray-900 overflow-hidden border border-gray-100 dark:border-gray-700">
            <svg viewBox="0 0 100 100" class="absolute inset-0 w-full h-full">
              <line
                v-for="edge in graphEdges"
                :key="`${edge.from}-${edge.to}-${edge.label}`"
                :x1="edge.x1"
                :y1="edge.y1"
                :x2="edge.x2"
                :y2="edge.y2"
                class="stroke-gray-300 dark:stroke-gray-700"
                stroke-width="0.4"
              />
              <g v-for="node in graphNodes" :key="node.id">
                <circle
                  :cx="node.x"
                  :cy="node.y"
                  :r="nodeRadius(node.weight)"
                  :class="nodeClass(node.type)"
                  class="stroke-white dark:stroke-gray-950"
                  stroke-width="0.8"
                />
                <text
                  :x="node.x"
                  :y="node.y + nodeRadius(node.weight) + 3"
                  text-anchor="middle"
                  class="fill-gray-700 dark:fill-gray-200"
                  style="font-size: 3px"
                >
                  {{ shortLabel(node.label) }}
                </text>
              </g>
            </svg>
          </div>
        </div>

        <div class="card">
          <h3 class="font-bold text-gray-800 dark:text-white mb-4">工具适用地图</h3>
          <div class="space-y-3">
            <div v-for="tool in visualMap.tool_fit_map" :key="tool.tool" class="rounded-lg bg-gray-50 dark:bg-gray-800 p-3">
              <div class="flex items-center justify-between gap-3 mb-2">
                <div>
                  <p class="font-semibold text-gray-800 dark:text-white">{{ tool.tool }}</p>
                  <p class="text-xs text-gray-500">{{ tool.use }} · {{ tool.matched_entries }} 条</p>
                </div>
                <span class="text-lg font-bold text-indigo-500">{{ tool.fit_score }}</span>
              </div>
              <div class="h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                <div class="h-full rounded-full bg-indigo-500" :style="{ width: `${Math.min(100, tool.fit_score)}%` }"></div>
              </div>
              <p v-if="tool.examples.length" class="text-xs text-gray-500 mt-2 truncate">{{ tool.examples.map(displayKnowledgeLabel).join(' / ') }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div class="card">
          <h3 class="font-bold text-gray-800 dark:text-white mb-2">主题覆盖</h3>
          <p class="mb-4 text-sm text-gray-500 dark:text-gray-400">把知识库按可学习、可筛选、可训练的主题重组，隐藏内部导入分区。</p>
          <div class="space-y-3">
            <button
              v-for="topic in topicCoverage"
              :key="topic.id"
              type="button"
              class="w-full rounded-lg border border-gray-100 p-3 text-left transition-colors hover:border-indigo-200 hover:bg-indigo-50/60 dark:border-gray-700 dark:hover:border-indigo-800 dark:hover:bg-indigo-950/20"
              @click="selectTopic(topic.id)"
            >
              <div class="flex items-center justify-between gap-3">
                <p class="font-semibold text-gray-800 dark:text-white">{{ topic.icon }} {{ topic.label }}</p>
                <span class="text-xs text-gray-500">{{ topic.count }} 条</span>
              </div>
              <p class="mt-2 text-xs leading-5 text-gray-500 dark:text-gray-400">{{ topic.description }}</p>
              <div class="mt-3 h-2 overflow-hidden rounded-full bg-gray-100 dark:bg-gray-800">
                <div class="h-full rounded-full bg-indigo-500" :style="{ width: `${topic.width}%` }"></div>
              </div>
            </button>
          </div>
        </div>

        <div class="card">
          <h3 class="font-bold text-gray-800 dark:text-white mb-4">5W2H 元问题卡</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div v-for="card in visualMap.five_w_two_h_cards" :key="card.key" class="rounded-lg bg-gray-50 dark:bg-gray-800 p-3">
              <p class="text-xs font-bold text-indigo-500">{{ card.label }}</p>
              <p class="text-sm font-semibold text-gray-800 dark:text-white mt-1">{{ card.question }}</p>
              <p class="text-xs text-gray-500 dark:text-gray-400 mt-2 leading-relaxed">{{ card.answer }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'concept_cards'" class="grid grid-cols-1 xl:grid-cols-4 gap-6">
      <aside class="xl:col-span-1 space-y-4">
        <div class="card">
          <h2 class="font-bold text-gray-800 dark:text-white mb-2">知识主题</h2>
          <p class="mb-4 text-xs leading-5 text-gray-500 dark:text-gray-400">这里按学习用途筛选，不展示内部导入分区和机器编号。</p>
          <button
            v-for="topic in knowledgeTopics"
            :key="topic.id"
            @click="selectTopic(topic.id)"
            class="w-full text-left p-3 rounded-xl mb-2 transition-colors"
            :class="selectedTopicId === topic.id ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300' : 'bg-gray-50 dark:bg-gray-700/50 text-gray-700 dark:text-gray-200'"
          >
            <span class="mr-2">{{ topic.icon }}</span>{{ topic.label }}
            <span class="float-right text-xs opacity-70">{{ topicCount(topic.id) }} 条</span>
            <p class="mt-1 pl-7 text-xs opacity-75">{{ topic.description }}</p>
          </button>
        </div>
        <div class="card bg-gray-900 text-white">
          <h2 class="font-bold mb-2">导入状态</h2>
          <p class="text-sm text-gray-300">{{ importInfo?.principle || '等待导入知识内容' }}</p>
          <p v-if="importInfo?.latest" class="text-xs text-gray-400 mt-3">
            最新导入：{{ displayImportSource(importInfo.latest.source_name) }} · {{ importInfo.latest.imported_entries }} 条
          </p>
        </div>
      </aside>

      <section class="xl:col-span-3 space-y-4">
        <div class="card">
          <div class="mb-3">
            <h2 class="text-sm font-bold text-gray-800 dark:text-white">知识检索</h2>
            <p class="mt-1 text-xs leading-5 text-gray-500 dark:text-gray-400">
              {{ filters?.principle || '筛选建议来自 SQLite，可选择也可手动输入。' }}
            </p>
          </div>
          <div class="grid grid-cols-1 gap-3 lg:grid-cols-[minmax(0,1.2fr)_repeat(4,minmax(0,0.7fr))_auto]">
            <input v-model="query" list="knowledge-keyword-options" class="input-mac" placeholder="搜索知识条目、原则、案例..." @keyup.enter="loadEntries" />
            <datalist id="knowledge-keyword-options">
              <option v-for="option in filters?.keywords || []" :key="option.value" :value="option.value">{{ filterLabel(option) }}</option>
            </datalist>
            <select v-model="selectedSectionId" class="input-mac" @change="loadEntries">
              <option value="">全部分区</option>
              <option v-for="option in filters?.sections || []" :key="option.value" :value="option.value">{{ filterLabel(option) }}</option>
            </select>
            <input v-model="selectedCategory" list="knowledge-category-options" class="input-mac" placeholder="分类" @keyup.enter="loadEntries" />
            <datalist id="knowledge-category-options">
              <option v-for="option in filters?.categories || []" :key="option.value" :value="option.value">{{ filterLabel(option) }}</option>
            </datalist>
            <input v-model="selectedTag" list="knowledge-tag-options" class="input-mac" placeholder="标签" @keyup.enter="loadEntries" />
            <datalist id="knowledge-tag-options">
              <option v-for="option in filters?.tags || []" :key="option.value" :value="option.value">{{ filterLabel(option) }}</option>
            </datalist>
            <input v-model="selectedSource" list="knowledge-source-options" class="input-mac" placeholder="来源" @keyup.enter="loadEntries" />
            <datalist id="knowledge-source-options">
              <option v-for="option in filters?.sources || []" :key="option.value" :value="option.value">{{ filterLabel(option) }}</option>
            </datalist>
            <button @click="loadEntries" class="btn-primary">搜索</button>
          </div>
          <div class="mt-3 flex flex-wrap gap-2">
            <button
              v-for="option in quickKnowledgeOptions"
              :key="`quick-knowledge-${option.value}`"
              type="button"
              class="rounded-full bg-gray-50 px-3 py-1.5 text-xs text-gray-700 transition-colors hover:bg-indigo-50 hover:text-indigo-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-indigo-950/40 dark:hover:text-indigo-200"
              @click="selectQuickKnowledge(option.value)"
            >
              {{ filterLabel(option) }}
            </button>
            <button v-if="hasKnowledgeFilters" type="button" class="rounded-full bg-gray-100 px-3 py-1.5 text-xs font-semibold text-gray-600 hover:bg-gray-200 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-700" @click="clearFilters">
              清空筛选
            </button>
          </div>
        </div>

        <div v-if="loading" class="card text-center text-gray-500">加载中...</div>
        <div v-else-if="loadError" class="card text-center text-red-500">
          <p class="font-semibold">知识条目加载失败</p>
          <p class="mt-2 text-sm">{{ loadError }}</p>
          <button class="btn-secondary mt-4" @click="loadPage">重试</button>
        </div>
        <div v-else-if="entries.length === 0" class="card text-center text-gray-500">
          <p class="font-semibold">当前筛选没有知识条目</p>
          <p class="mt-2 text-sm">请切换到“全部知识”，或换一个搜索关键词。</p>
          <button v-if="selectedTopicId !== 'all' || query" class="btn-secondary mt-4" @click="clearFilters">查看全部知识</button>
        </div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <article v-for="entry in entries" :key="entry.id" class="card card-hover cursor-pointer" @click="openEntry(entry.id)">
            <div class="flex items-center justify-between gap-3 mb-2">
              <h3 class="font-bold text-gray-800 dark:text-white">{{ displayKnowledgeLabel(entry.title) }}</h3>
              <span class="text-xs px-2 py-1 rounded bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-300">{{ entry.quality_score }}</span>
            </div>
            <p v-if="entry.subtitle" class="text-sm text-gray-500 dark:text-gray-400 mb-2">{{ entry.subtitle }}</p>
            <p class="text-sm text-gray-600 dark:text-gray-300 line-clamp-2">{{ entry.learning?.concept || entry.summary || '点击查看完整结构化内容' }}</p>
            <div class="mt-3 grid grid-cols-1 gap-2 text-xs leading-5 text-gray-500 dark:text-gray-400">
              <div class="rounded-lg bg-gray-50 p-2 dark:bg-gray-800">
                <span class="font-semibold text-gray-700 dark:text-gray-200">原则：</span>{{ entry.learning?.principle || learningPrincipleFallback(entry) }}
              </div>
              <div class="rounded-lg bg-gray-50 p-2 dark:bg-gray-800">
                <span class="font-semibold text-gray-700 dark:text-gray-200">方法：</span>{{ (entry.learning?.method || learningMethodFallback(entry)).slice(0, 3).join(' -> ') }}
              </div>
              <div class="rounded-lg bg-indigo-50 p-2 text-indigo-700 dark:bg-indigo-950/30 dark:text-indigo-200">
                <span class="font-semibold">练习：</span>{{ entry.learning?.drill || `用自己的经历写一个“${displayKnowledgeLabel(entry.title)}”的正例和反例。` }}
              </div>
            </div>
            <div class="flex flex-wrap gap-2 mt-3">
              <span v-for="tag in entry.tags" :key="tag" class="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-700 text-gray-500">{{ displayKnowledgeLabel(tag) }}</span>
            </div>
          </article>
        </div>
      </section>
    </div>

    <Teleport to="body">
      <div v-if="activeEntry" class="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-6" @click.self="activeEntry = null">
        <div class="bg-white dark:bg-gray-800 rounded-2xl max-w-3xl max-h-[85vh] overflow-auto p-6 shadow-2xl">
          <div class="flex items-start justify-between gap-4 mb-4">
            <div>
              <h2 class="text-2xl font-bold text-gray-800 dark:text-white">{{ displayKnowledgeLabel(activeEntry.title) }}</h2>
              <p class="text-sm text-gray-500 mt-1">{{ activeEntry.source }} · {{ activeEntry.category }}</p>
            </div>
            <button class="btn-secondary" @click="activeEntry = null">关闭</button>
          </div>
          <div v-if="activeEntry.learning" class="mb-4 grid grid-cols-1 gap-3 md:grid-cols-2">
            <div class="rounded-lg bg-gray-50 p-3 text-sm dark:bg-gray-900">
              <p class="font-semibold text-gray-800 dark:text-white">概念定义</p>
              <p class="mt-1 leading-6 text-gray-600 dark:text-gray-300">{{ activeEntry.learning.concept }}</p>
            </div>
            <div class="rounded-lg bg-gray-50 p-3 text-sm dark:bg-gray-900">
              <p class="font-semibold text-gray-800 dark:text-white">核心原则</p>
              <p class="mt-1 leading-6 text-gray-600 dark:text-gray-300">{{ activeEntry.learning.principle }}</p>
            </div>
            <div class="rounded-lg bg-gray-50 p-3 text-sm dark:bg-gray-900">
              <p class="font-semibold text-gray-800 dark:text-white">实践方法</p>
              <ol class="mt-1 space-y-1 leading-6 text-gray-600 dark:text-gray-300">
                <li v-for="(step, index) in activeEntry.learning.method" :key="step">{{ index + 1 }}. {{ step }}</li>
              </ol>
            </div>
            <div class="rounded-lg bg-indigo-50 p-3 text-sm text-indigo-800 dark:bg-indigo-950/30 dark:text-indigo-200">
              <p class="font-semibold">适用场景与练习</p>
              <p class="mt-1 leading-6">{{ activeEntry.learning.scene }}</p>
              <p class="mt-2 leading-6">{{ activeEntry.learning.drill }}</p>
            </div>
          </div>
          <pre class="whitespace-pre-wrap text-sm leading-7 text-gray-700 dark:text-gray-200 font-sans">{{ activeEntry.content }}</pre>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ModuleTabs from '@/components/ModuleTabs.vue'
import { knowledgeApi } from '@/utils/api'
import type { KnowledgeEntry, KnowledgeFilterOptions, KnowledgeImportLatest, KnowledgeVisualMap } from '@/utils/api'

const entries = ref<KnowledgeEntry[]>([])
const activeEntry = ref<KnowledgeEntry | null>(null)
const importInfo = ref<KnowledgeImportLatest | null>(null)
const visualMap = ref<KnowledgeVisualMap | null>(null)
const filters = ref<KnowledgeFilterOptions | null>(null)
const selectedTopicId = ref('all')
const selectedSectionId = ref('')
const selectedCategory = ref('')
const selectedTag = ref('')
const selectedSource = ref('')
const query = ref('')
const loading = ref(false)
const loadError = ref('')
const route = useRoute()
const router = useRouter()
const activeTab = ref('concept_cards')

const knowledgeTabs = [
  { id: 'concept_cards', label: '知识卡片', summary: '学习概念、原则、方法和练习。' },
  { id: 'five_w_two_h', label: '5W2H', summary: '用元问题理解一个模块或概念。' },
]

const knowledgeTopics = [
  { id: 'all', icon: '🌐', label: '全部知识', description: '查看当前知识库的高质量条目。' },
  { id: 'boundary', icon: '🛡️', label: '边界与修复', description: '边界、修复、低压力邀请。', category: 'boundary' },
  { id: 'empathy', icon: '🤝', label: '共情承接', description: '先接住情绪，再处理事情。', q: '共情' },
  { id: 'repair', icon: '🧩', label: '冲突修复', description: '道歉、重新约定、关系回温。', q: '修复' },
  { id: 'manual', icon: '📘', label: '旧版手册精华', description: '从 legacy 手册迁移的结构化知识。', category: 'legacy_manual' },
  { id: 'unit', icon: '🧱', label: '单元知识', description: '适合做概念卡和基础训练的知识点。', q: '单元知识' },
]

const coverageMetrics = computed(() => {
  if (!visualMap.value) return []
  const coverage = visualMap.value.coverage
  return [
    { label: '分区', value: coverage.sections },
    { label: '条目', value: coverage.entries },
    { label: '分类', value: coverage.categories },
    { label: '标签', value: coverage.tags },
    { label: '质量', value: coverage.average_quality },
  ]
})

const graphNodes = computed(() => {
  const nodes = visualMap.value?.concept_graph.nodes || []
  return nodes.map((node, index) => ({
    ...node,
    label: displayKnowledgeLabel(node.label),
    x: node.x ?? 10 + (index % 6) * 16,
    y: node.y ?? 15 + Math.floor(index / 6) * 14,
  }))
})

const graphEdges = computed(() => {
  const nodeById = new Map(graphNodes.value.map(node => [node.id, node]))
  return (visualMap.value?.concept_graph.edges || [])
    .map(edge => {
      const from = nodeById.get(edge.from)
      const to = nodeById.get(edge.to)
      if (!from || !to) return null
      return { ...edge, x1: from.x, y1: from.y, x2: to.x, y2: to.y }
    })
    .filter((edge): edge is NonNullable<typeof edge> => Boolean(edge))
})

const topicCoverage = computed(() => {
  const categoryCounts = new Map<string, number>()
  const tagCounts = new Map<string, number>()
  for (const branch of visualMap.value?.classification_tree || []) {
    const branchName = displayKnowledgeLabel(branch.name)
    categoryCounts.set(branchName, (categoryCounts.get(branchName) || 0) + branch.count)
    for (const child of branch.children || []) {
      const childName = displayKnowledgeLabel(child.name)
      categoryCounts.set(childName, (categoryCounts.get(childName) || 0) + child.count)
    }
  }
  for (const card of visualMap.value?.tool_fit_map || []) {
    if (card.tool.includes('边界')) tagCounts.set('边界与修复', Math.max(tagCounts.get('边界与修复') || 0, card.matched_entries))
    if (card.tool.includes('诗人')) tagCounts.set('共情承接', Math.max(tagCounts.get('共情承接') || 0, card.matched_entries))
  }
  const rows = knowledgeTopics.map((topic) => {
    const count = topic.id === 'all'
      ? visualMap.value?.coverage.entries || 0
      : topic.id === 'manual'
        ? categoryCounts.get('旧版手册') || 0
        : topic.id === 'boundary'
          ? tagCounts.get('边界与修复') || categoryCounts.get('边界与修复') || 0
          : topic.id === 'empathy'
            ? tagCounts.get('共情承接') || 0
            : topic.id === 'repair'
              ? categoryCounts.get('修复') || tagCounts.get('边界与修复') || 0
              : categoryCounts.get(topic.label) || 0
    return { ...topic, count }
  })
  const maxCount = Math.max(...rows.map((topic) => topic.count), 1)
  return rows.map((topic) => ({ ...topic, width: Math.max(6, Math.round((topic.count / maxCount) * 100)) }))
})

const topicCountById = computed(() => new Map(topicCoverage.value.map((topic) => [topic.id, topic.count])))
const quickKnowledgeOptions = computed(() => [
  ...(filters.value?.categories || []).slice(0, 5),
  ...(filters.value?.tags || []).slice(0, 5),
])
const hasKnowledgeFilters = computed(() => Boolean(
  query.value || selectedSectionId.value || selectedCategory.value || selectedTag.value || selectedSource.value || selectedTopicId.value !== 'all',
))

function topicCount(id: string) {
  return topicCountById.value.get(id) || 0
}

async function loadEntries() {
  loading.value = true
  loadError.value = ''
  try {
    const topic = knowledgeTopics.find((item) => item.id === selectedTopicId.value)
    entries.value = await knowledgeApi.entries({
      section_id: selectedSectionId.value ? Number(selectedSectionId.value) : undefined,
      category: selectedCategory.value || topic?.category,
      tag: selectedTag.value || undefined,
      source: selectedSource.value || undefined,
      q: query.value || topic?.q,
      limit: 80,
    })
  } catch (error) {
    entries.value = []
    loadError.value = error instanceof Error ? error.message : '无法读取知识条目，请稍后重试。'
  } finally {
    loading.value = false
  }
}

async function selectTopic(id: string) {
  selectedTopicId.value = id
  selectedSectionId.value = ''
  selectedCategory.value = ''
  selectedTag.value = ''
  selectedSource.value = ''
  await loadEntries()
}

async function openEntry(id: number) {
  activeEntry.value = await knowledgeApi.entry(id)
}

function clearFilters() {
  selectedTopicId.value = 'all'
  selectedSectionId.value = ''
  selectedCategory.value = ''
  selectedTag.value = ''
  selectedSource.value = ''
  query.value = ''
  loadEntries()
}

async function selectQuickKnowledge(value: string) {
  query.value = value
  selectedTopicId.value = 'all'
  await loadEntries()
}

function filterLabel(option: { label: string; value: string; count: number }) {
  return `${option.label || option.value} · ${option.count}`
}

function normalizeTab(value: unknown) {
  const tab = typeof value === 'string' ? value : ''
  return knowledgeTabs.some((item) => item.id === tab) ? tab : 'concept_cards'
}

function onTabChange(value: string) {
  activeTab.value = normalizeTab(value)
  const nextQuery: Record<string, string> = {}
  if (activeTab.value !== 'concept_cards') nextQuery.tab = activeTab.value
  router.replace({ path: '/knowledge', query: nextQuery })
}

async function loadPage() {
  loadError.value = ''
  try {
    await Promise.all([
      knowledgeApi.latestImport().then(data => { importInfo.value = data }),
      knowledgeApi.visualMap().then(data => { visualMap.value = data }),
      knowledgeApi.filters(160).then(data => { filters.value = data }),
    ])
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : '无法读取知识中枢数据，请稍后重试。'
  }
  await loadEntries()
}

onMounted(() => {
  activeTab.value = normalizeTab(route.query.tab)
  loadPage()
})

watch(
  () => route.query.tab,
  (value) => {
    activeTab.value = normalizeTab(value)
  },
)

function nodeRadius(weight: number) {
  return Math.max(2.8, Math.min(8.5, 2.8 + Math.sqrt(Math.max(0, weight)) * 0.9))
}

function nodeClass(type: string) {
  const classes: Record<string, string> = {
    root: 'fill-indigo-500',
    section: 'fill-blue-500',
    category: 'fill-emerald-500',
    tag: 'fill-amber-500',
  }
  return classes[type] || 'fill-gray-400'
}

function shortLabel(label: string) {
  return label.length > 8 ? `${label.slice(0, 8)}…` : label
}

function displayKnowledgeLabel(label: string) {
  return label
    .replace(/^legacy_manual$/i, '旧版手册')
    .replace(/^boundary$/i, '边界与修复')
    .replace(/^manual$/i, '手册')
    .replace(/^legacy$/i, '旧版迁移')
    .replace(/^单元知识\d+$/, '单元知识')
    .replace(/[a-f0-9]{16,}/gi, '')
    .replace(/\s{2,}/g, ' ')
    .trim()
}

function displayImportSource(sourceName: string) {
  return sourceName
    .replace(/_[a-f0-9]{16,}(?=\.|$)/gi, '')
    .replace(/[a-f0-9]{16,}/gi, '')
    .replace(/pytest_issue_governance/i, '治理导入批次')
    .replace(/\.json$/i, '')
}

function learningPrincipleFallback(entry: KnowledgeEntry) {
  if (entry.tags.includes('边界')) return '先尊重选择权，再提出可拒绝的轻验证。'
  if (entry.tags.includes('共情')) return '先接住情绪，再处理事情。'
  if (entry.tags.includes('修复')) return '先承担影响，再给出具体修复动作。'
  return '把抽象概念落到事实、动作和复盘证据上。'
}

function learningMethodFallback(entry: KnowledgeEntry) {
  if (entry.tags.includes('边界')) return ['观察事实', '承接空间', '轻问验证', '给出退路']
  if (entry.tags.includes('共情')) return ['复述处境', '命名感受', '校准理解', '询问需要']
  if (entry.tags.includes('修复')) return ['承认影响', '承担部分', '说明改法', '具体补偿']
  return ['定义概念', '匹配场景', '改成一句话', '记录反馈']
}
</script>
