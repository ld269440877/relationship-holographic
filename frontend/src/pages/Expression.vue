<template>
  <div class="p-4 sm:p-6 lg:p-8">
    <div class="mb-8 flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
      <div>
        <p class="mb-2 text-sm font-semibold text-indigo-500">Expression Toolbox / 表达工具箱</p>
        <h1 class="text-3xl font-bold text-gray-800 dark:text-white">表达工具箱</h1>
        <p class="mt-2 max-w-3xl text-gray-500 dark:text-gray-400">
          {{ tools?.principle || '从场景、目标和情绪出发选择表达工具，而不是背一句孤立话术。' }}
        </p>
      </div>
      <div class="grid grid-cols-3 gap-3 rounded-lg bg-white p-4 shadow-sm dark:bg-gray-800">
        <MetricPill label="工具" :value="tools?.total ?? 0" />
        <MetricPill label="工具链" :value="chains.length" />
        <MetricPill label="推荐" :value="recommendation?.tools.length ?? 0" />
      </div>
    </div>

    <ModuleTabs
      v-model="activeTab"
      :tabs="expressionTabs"
      label="表达工具箱选项卡"
      id-prefix="expression-tab"
      class="mb-6"
      @update:model-value="onTabChange"
    />

    <div class="mb-6 rounded-lg bg-white p-4 shadow-sm dark:bg-gray-800">
      <div class="mb-4 flex flex-col gap-2 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h2 class="text-lg font-bold text-gray-800 dark:text-white">检索与筛选</h2>
          <p class="mt-1 text-xs leading-5 text-gray-500 dark:text-gray-400">
            先用一个主搜索找概念、场景、目标、公式或边界，再用筛选收窄；下方推荐词按用途分组，不重复占用输入区。
          </p>
        </div>
        <div class="flex flex-wrap gap-2">
          <button type="button" class="rounded-lg bg-gray-100 px-3 py-2 text-xs font-semibold text-gray-600 hover:bg-gray-200 dark:bg-gray-900 dark:text-gray-300 dark:hover:bg-gray-700" @click="resetFilters">
            重置筛选
          </button>
          <button class="btn-primary" @click="applyFilters">应用筛选</button>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-3 lg:grid-cols-[minmax(0,1.4fr)_repeat(3,minmax(0,0.75fr))]">
        <div>
          <label class="mb-1 block text-xs font-semibold text-gray-500 dark:text-gray-400">主搜索</label>
          <div class="relative">
            <input
              v-model.trim="query"
              class="input-mac"
              placeholder="概念/工具/场景/目标/风险，例如：幽默自嘲、边界、修复、PREP"
              aria-haspopup="listbox"
              :aria-expanded="searchMenuOpen"
              @focus="openSearchMenu"
              @click="openSearchMenu"
              @input="openSearchMenu"
              @blur="closeSearchMenuSoon"
              @keyup.enter="applyFilters"
              @keydown.escape="searchMenuOpen = false"
            />
            <div
              v-if="searchMenuOpen && visibleSuggestionGroups.length"
              class="absolute left-0 right-0 top-full z-40 mt-2 max-h-96 overflow-auto rounded-lg border border-gray-100 bg-white p-3 shadow-xl dark:border-gray-700 dark:bg-gray-900"
              role="listbox"
              data-expression-search-menu
            >
              <div class="mb-2 flex items-center justify-between gap-2 border-b border-gray-100 pb-2 dark:border-gray-800">
                <p class="text-xs font-semibold text-gray-700 dark:text-gray-200">可直接选择，也可以继续手动输入</p>
                <span class="text-[11px] text-gray-400">Enter 搜索</span>
              </div>
              <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
                <div v-for="group in visibleSuggestionGroups" :key="group.name">
                  <div class="mb-1 flex items-center justify-between gap-2">
                    <p class="text-[11px] font-semibold text-gray-500 dark:text-gray-400">{{ group.name }}</p>
                    <span class="text-[11px] text-gray-400">{{ group.intent }}</span>
                  </div>
                  <div class="flex flex-wrap gap-2">
                    <button
                      v-for="item in group.items"
                      :key="`${group.name}-${item}`"
                      type="button"
                      class="rounded-full bg-gray-100 px-3 py-1.5 text-xs text-gray-700 hover:bg-indigo-100 hover:text-indigo-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-indigo-950/50 dark:hover:text-indigo-200"
                      :class="query === item ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-200' : ''"
                      :data-expression-search-suggestion="item"
                      @mousedown.prevent="applySearchSuggestion(item)"
                    >
                      {{ item }}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-gray-500 dark:text-gray-400">层级</label>
          <select v-model="selectedLayer" class="input-mac" @change="applyFilters">
            <option value="">全部层级</option>
            <option v-for="[key, label] in Object.entries(layerOptions)" :key="key" :value="key">{{ facetLabel(label, tools?.layer_counts?.[key]) }}</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-gray-500 dark:text-gray-400">场景</label>
          <select v-model="selectedScene" class="input-mac" @change="applyFilters">
            <option value="">全部场景</option>
            <option v-for="scene in sceneOptions" :key="scene" :value="scene">{{ facetLabel(scene, tools?.scene_counts?.[scene]) }}</option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-xs font-semibold text-gray-500 dark:text-gray-400">目标</label>
          <select v-model="selectedGoal" class="input-mac" @change="applyFilters">
            <option value="">全部目标</option>
            <option v-for="goal in goalOptions" :key="goal" :value="goal">{{ facetLabel(goal, tools?.goal_counts?.[goal]) }}</option>
          </select>
        </div>
      </div>

      <div v-if="activeFilterChips.length" class="mt-4 flex flex-wrap items-center gap-2 rounded-lg bg-indigo-50 px-3 py-2 text-sm text-indigo-700 dark:bg-indigo-950/30 dark:text-indigo-200">
        <span class="font-semibold">当前条件</span>
        <button
          v-for="chip in activeFilterChips"
          :key="chip.key"
          type="button"
          class="rounded bg-white px-2 py-1 text-xs font-semibold hover:bg-indigo-100 dark:bg-gray-900 dark:hover:bg-indigo-900/60"
          @click="clearFilter(chip.key)"
        >
          {{ chip.label }} ×
        </button>
      </div>

      <p class="mt-3 text-xs leading-5 text-gray-500 dark:text-gray-400">
        不确定搜什么时，点击主搜索会在输入框下方展开场景、目标或工具名；搜索会覆盖工具名称、公式、场景、微步骤、风险边界和示例。
      </p>
    </div>

    <section v-if="activeTab === 'tool_chains'" class="mb-6 rounded-lg bg-white p-4 shadow-sm dark:bg-gray-800">
      <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 class="text-lg font-bold text-gray-800 dark:text-white">工具链推荐</h2>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
            按当前场景和目标组合 2-3 个工具，先学顺序，再学单个工具。
          </p>
        </div>
        <button class="rounded-lg bg-indigo-500 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-600" @click="loadRecommendation">
          按当前条件推荐
        </button>
      </div>
      <div class="grid grid-cols-1 gap-3 xl:grid-cols-3">
        <div v-for="chain in recommendedChains" :key="chain.chain_uuid" class="rounded-lg border border-gray-100 p-4 dark:border-gray-700">
          <div class="mb-3 flex items-start justify-between gap-3">
            <div>
              <p class="font-semibold text-gray-800 dark:text-white">{{ chain.name }}</p>
              <p class="mt-1 text-xs text-gray-500">{{ chain.scene }} · {{ chain.goal }} · {{ chain.stage }}</p>
            </div>
            <span class="text-xs text-gray-400">Q{{ Math.round(chain.quality_score) }}</span>
          </div>
          <div class="flex flex-wrap gap-2">
            <span v-for="step in chain.sequence" :key="`${chain.chain_uuid}-${step.order}`" class="rounded bg-indigo-50 px-2 py-1 text-xs text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-300">
              {{ step.order }}. {{ step.tool }}
            </span>
          </div>
          <div v-if="chain.example_dialogue?.before || chain.example_dialogue?.after" class="mt-3 grid grid-cols-1 gap-2 text-sm">
            <p v-if="chain.example_dialogue?.before" class="rounded bg-red-50 p-2 text-red-700 dark:bg-red-900/20 dark:text-red-300">旧：{{ chain.example_dialogue.before }}</p>
            <p v-if="chain.example_dialogue?.after" class="rounded bg-emerald-50 p-2 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300">新：{{ chain.example_dialogue.after }}</p>
          </div>
        </div>
      </div>
    </section>

    <div
      v-if="activeTab === 'atomic_tools'"
      class="mb-8 grid grid-cols-1 gap-6 transition-[grid-template-columns] xl:grid-cols-[minmax(0,1fr)_300px]"
      :class="tocCollapsed ? 'xl:!grid-cols-[minmax(0,1fr)]' : ''"
    >
      <section class="space-y-4">
        <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <article
            v-for="tool in tools?.items || []"
            :id="toolAnchor(tool)"
            :key="tool.tool_uuid"
              class="card card-hover scroll-mt-24 text-left"
            :class="expandedToolId === tool.tool_uuid ? 'ring-2 ring-indigo-300 dark:ring-indigo-700 lg:col-span-2' : ''"
            @click="selectTool(tool)"
          >
            <div class="mb-3 flex flex-wrap items-center gap-2">
              <span class="rounded bg-indigo-50 px-2 py-1 text-xs font-semibold text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-300">{{ tool.layer_label }}</span>
              <span class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">{{ tool.category }}</span>
              <span class="ml-auto text-xs text-gray-400">Q{{ Math.round(tool.quality_score) }}</span>
            </div>
            <div class="flex items-start justify-between gap-3">
              <h2 class="text-lg font-bold text-gray-800 dark:text-white">{{ tool.name }}</h2>
              <span class="shrink-0 rounded bg-gray-100 px-2 py-1 text-xs text-gray-500 dark:bg-gray-800 dark:text-gray-300">
                {{ expandedToolId === tool.tool_uuid ? '收起' : '详情' }}
              </span>
            </div>
            <p class="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">{{ tool.description }}</p>
            <p v-if="tool.formula" class="mt-3 rounded-lg bg-gray-50 p-3 text-sm text-gray-600 dark:bg-gray-800 dark:text-gray-300">{{ tool.formula }}</p>
            <div class="mt-3 flex flex-wrap gap-2">
              <span v-for="scene in tool.best_scenes.slice(0, 4)" :key="scene" class="rounded bg-blue-50 px-2 py-1 text-xs text-blue-700 dark:bg-blue-900/20 dark:text-blue-300">{{ scene }}</span>
            </div>

            <div
              v-if="expandedToolId === tool.tool_uuid && selectedTool"
              class="mt-4 space-y-4 border-t border-gray-100 pt-4 dark:border-gray-700"
              @click.stop
            >
              <div class="grid grid-cols-1 gap-3 xl:grid-cols-3">
                <div class="rounded-lg bg-gray-50 p-3 text-sm dark:bg-gray-800">
                  <p class="font-semibold text-gray-800 dark:text-white">概念定义</p>
                  <p class="mt-1 leading-6 text-gray-600 dark:text-gray-300">{{ selectedTool.learning_blueprint?.definition || selectedTool.learning_blueprint?.concept || toolDefinition(selectedTool) }}</p>
                </div>
                <div class="rounded-lg bg-gray-50 p-3 text-sm dark:bg-gray-800">
                  <p class="font-semibold text-gray-800 dark:text-white">核心原则</p>
                  <ul v-if="selectedTool.learning_blueprint?.core_principles?.length" class="mt-1 space-y-1 leading-6 text-gray-600 dark:text-gray-300">
                    <li v-for="principle in selectedTool.learning_blueprint.core_principles" :key="principle">· {{ principle }}</li>
                  </ul>
                  <p v-else class="mt-1 leading-6 text-gray-600 dark:text-gray-300">{{ toolPrinciple(selectedTool) }}</p>
                </div>
                <div class="rounded-lg bg-gray-50 p-3 text-sm dark:bg-gray-800">
                  <p class="font-semibold text-gray-800 dark:text-white">公式</p>
                  <p class="mt-1 leading-6 text-gray-600 dark:text-gray-300">{{ selectedTool.formula || '-' }}</p>
                </div>
              </div>
              <div class="grid grid-cols-1 gap-3 xl:grid-cols-2">
                <div>
                  <p class="mb-2 text-sm font-semibold text-gray-800 dark:text-white">实践方法</p>
                  <ol class="space-y-2 text-sm text-gray-600 dark:text-gray-300">
                    <li v-for="(step, index) in toolMicroSteps(selectedTool)" :key="step" class="rounded bg-gray-50 p-2 dark:bg-gray-800">
                      {{ index + 1 }}. {{ step }}
                    </li>
                  </ol>
                </div>
                <div>
                  <p class="mb-2 text-sm font-semibold text-gray-800 dark:text-white">适用场景</p>
                  <div class="grid grid-cols-1 gap-2 text-sm text-gray-600 dark:text-gray-300">
                    <p v-for="scene in selectedTool.best_scenes" :key="scene" class="rounded bg-blue-50 p-2 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300">
                      {{ scene }}：{{ sceneUsage(scene, selectedTool) }}
                    </p>
                  </div>
                </div>
              </div>
              <div class="rounded-lg bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-900/20 dark:text-amber-200">
                <p class="font-semibold">风险边界</p>
                  <p class="mt-1 leading-6">{{ toolRiskBoundaries(selectedTool).join('；') || '保持可拒绝、可退出、可复盘。' }}</p>
              </div>
              <div v-if="selectedTool.learning_blueprint?.when_not_to_use?.length" class="rounded-lg bg-orange-50 p-3 text-sm text-orange-800 dark:bg-orange-950/30 dark:text-orange-200">
                <p class="font-semibold">不适合使用</p>
                <ul class="mt-1 space-y-1 leading-6">
                  <li v-for="item in selectedTool.learning_blueprint.when_not_to_use" :key="item">· {{ item }}</li>
                </ul>
              </div>
              <div class="grid grid-cols-1 gap-3 xl:grid-cols-2">
                <div class="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
                  <p class="font-semibold">旧回应</p>
                  <p class="mt-1 leading-6">{{ selectedTool.example_before || '暂无示例' }}</p>
                </div>
                <div class="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300">
                  <p class="font-semibold">更好回应</p>
                  <p class="mt-1 leading-6">{{ selectedTool.example_after || '暂无示例' }}</p>
                </div>
              </div>
              <div v-if="selectedTool.learning_blueprint?.dialogue_cases?.length" class="space-y-3 rounded-lg border border-indigo-100 bg-indigo-50/40 p-3 dark:border-indigo-900/60 dark:bg-indigo-950/20">
                <div>
                  <p class="text-sm font-semibold text-gray-800 dark:text-white">真实对话案例</p>
                  <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">每个案例都按同一个工具换场景，不复读同一句，方便举一反三。</p>
                </div>
                <div
                  v-for="dialogueCase in selectedTool.learning_blueprint.dialogue_cases"
                  :key="`${selectedTool.tool_uuid}-${dialogueCase.scene}`"
                  class="rounded-lg bg-white p-3 text-sm shadow-sm dark:bg-gray-900"
                >
                  <div class="mb-2 flex flex-wrap items-center gap-2">
                    <span class="rounded bg-indigo-100 px-2 py-1 text-xs font-semibold text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-200">{{ dialogueCase.scene }}</span>
                    <span class="text-xs text-gray-400">对话训练</span>
                  </div>
                  <p class="leading-6 text-gray-700 dark:text-gray-200"><span class="font-semibold">场景故事：</span>{{ dialogueCase.story }}</p>
                  <p class="mt-2 rounded bg-gray-50 p-2 leading-6 text-gray-700 dark:bg-gray-800 dark:text-gray-200"><span class="font-semibold">TA 说：</span>{{ dialogueCase.their_words }}</p>
                  <div class="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
                    <div class="rounded border border-red-100 bg-red-50 p-3 text-red-700 dark:border-red-900/50 dark:bg-red-950/20 dark:text-red-200">
                      <p class="font-semibold">低质量回应</p>
                      <p class="mt-1 leading-6">{{ lowQualityResponse(dialogueCase) }}</p>
                    </div>
                    <div class="rounded border border-emerald-100 bg-emerald-50 p-3 text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/20 dark:text-emerald-200">
                      <p class="font-semibold">更好回应</p>
                      <p class="mt-1 leading-6">{{ dialogueCase.better_response }}</p>
                    </div>
                  </div>
                  <p class="mt-3 leading-6 text-gray-600 dark:text-gray-300"><span class="font-semibold">为什么有效：</span>{{ dialogueCase.why_it_works }}</p>
                  <p v-if="dialogueCase.transfer_hint" class="mt-2 leading-6 text-gray-600 dark:text-gray-300"><span class="font-semibold">迁移提示：</span>{{ dialogueCase.transfer_hint }}</p>
                </div>
              </div>
              <div class="rounded-lg bg-indigo-50 p-3 text-sm text-indigo-800 dark:bg-indigo-950/30 dark:text-indigo-200">
                <p class="font-semibold">迁移练习</p>
                <ol v-if="selectedTool.learning_blueprint?.transfer_practice?.length" class="mt-1 space-y-1 leading-6">
                  <li v-for="(practice, index) in selectedTool.learning_blueprint.transfer_practice" :key="practice">{{ index + 1 }}. {{ practice }}</li>
                </ol>
                <ol v-else-if="selectedTool.learning_blueprint?.practice_ladder?.length" class="mt-1 space-y-1 leading-6">
                  <li v-for="(practice, index) in selectedTool.learning_blueprint.practice_ladder" :key="practice">{{ index + 1 }}. {{ practice }}</li>
                </ol>
                <p v-else class="mt-1 leading-6">{{ practicePrompt(selectedTool) }}</p>
              </div>
            </div>
          </article>
        </div>
        <div v-if="loading" class="rounded-lg bg-white p-8 text-center text-gray-500 shadow-sm dark:bg-gray-800">加载表达工具...</div>
        <div v-if="!loading && !tools?.items.length" class="card py-12 text-center text-gray-400">暂无匹配工具，试试放宽筛选。</div>
      </section>

      <aside class="space-y-6">
        <PageTocSidebar v-if="tocItems.length" v-model:collapsed="tocCollapsed" title="工具目录" :items="tocItems" />
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ModuleTabs from '@/components/ModuleTabs.vue'
import PageTocSidebar from '@/components/PageTocSidebar.vue'
import { expressionApi } from '@/utils/api'
import type { ExpressionRecommendation, ExpressionTool, ExpressionToolChain, ExpressionToolList } from '@/utils/api'

interface TocItem {
  id: string
  anchor: string
  title: string
  indexLabel?: string
}

const tools = ref<ExpressionToolList | null>(null)
const chains = ref<ExpressionToolChain[]>([])
const recommendation = ref<ExpressionRecommendation | null>(null)
const selectedTool = ref<ExpressionTool | null>(null)
const expandedToolId = ref('')
const loading = ref(false)
const query = ref('')
const selectedLayer = ref('')
const selectedScene = ref('')
const selectedGoal = ref('')
const tocCollapsed = ref(false)
const searchMenuOpen = ref(false)
const route = useRoute()
const router = useRouter()
const activeTab = ref('atomic_tools')
const expressionTabs = [
  { id: 'atomic_tools', label: '原子工具', summary: '学习单个表达工具的定义、公式、风险和练习。' },
  { id: 'tool_chains', label: '工具链', summary: '学习多个表达工具如何按顺序组合。' },
]
const defaultLayerOptions: Record<string, string> = {
  logic: '核心逻辑层',
  ammo: '内容弹药层',
  structure: '结构设计层',
  nonverbal: '非语言工具层',
  emotion: '情绪调节层',
  relationship: '关系管理层',
}
const defaultSceneOptions = ['初识', '暧昧', '热恋', '冲突', '修复', '长期', '分歧', '公开场合', '亲密推进', '价值观分歧', '约会邀约', '边界确认', '失望表达', '压力支持']
const defaultGoalOptions = ['说清事实', '命名感受', '确认边界', '降低防御', '提出请求', '修复信任', '引导深聊', '保留退路']
const commonToolSuggestions = ['情绪标注', 'PREP模型', 'SCQA模型', 'ORID聚焦法', '边界声明', '修复请求', '留白沉默', '幽默自嘲']
const commonFormulaSuggestions = ['事实', '感受', '边界', '退路', '轻验证', '承认影响', '下一步', '可拒绝']
const commonRiskSuggestions = ['不施压', '不贴标签', '不替对方做决定', '保留退路', '尊重边界']

const layerOptions = computed(() => Object.keys(tools.value?.layers || {}).length ? tools.value?.layers || defaultLayerOptions : defaultLayerOptions)
const sceneOptions = computed(() => tools.value ? uniqueValues(tools.value.scenes || []) : defaultSceneOptions)
const goalOptions = computed(() => tools.value ? uniqueValues(tools.value.goals || []) : defaultGoalOptions)
const toolNameSuggestions = computed(() => uniqueValues([...commonToolSuggestions, ...(tools.value?.items || []).map(tool => tool.name)]).slice(0, 16))
const formulaSuggestions = computed(() => {
  const values = new Set<string>(commonFormulaSuggestions)
  for (const tool of tools.value?.items || []) {
    for (const part of (tool.formula || '').split(/->|→|[，,、/]/)) {
      const value = part.trim()
      if (value.length >= 2 && value.length <= 8) values.add(value)
    }
  }
  return [...values].slice(0, 12)
})
const categorySuggestions = computed(() => {
  const values = new Set((tools.value?.items || []).map(tool => tool.category).filter(Boolean))
  return [...values].slice(0, 10)
})
const riskSuggestions = computed(() => {
  const values = new Set<string>(commonRiskSuggestions)
  for (const tool of tools.value?.items || []) {
    for (const risk of tool.risk_flags || []) {
      if (risk.includes('退路')) values.add('退路')
      if (risk.includes('施压')) values.add('施压')
      if (risk.includes('边界')) values.add('边界')
      if (risk.includes('决定')) values.add('替对方做决定')
    }
  }
  return [...values].slice(0, 8)
})
const suggestionGroups = computed(() => [
  { name: '工具概念', intent: '我想学某个词', items: toolNameSuggestions.value.slice(0, 8) },
  { name: '使用场景', intent: '我要处理什么关系场面', items: sceneOptions.value.slice(0, 8) },
  { name: '表达目标', intent: '这句话要达成什么', items: goalOptions.value.slice(0, 8) },
  { name: '表达公式', intent: '想按结构练', items: formulaSuggestions.value.slice(0, 8) },
  { name: '工具类别', intent: '按能力类型找', items: categorySuggestions.value.slice(0, 8) },
  { name: '安全边界', intent: '避免越界和操控', items: riskSuggestions.value.slice(0, 8) },
].filter(group => group.items.length))
const visibleSuggestionGroups = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  if (!keyword) return suggestionGroups.value
  return suggestionGroups.value
    .map(group => ({
      ...group,
      items: group.items.filter(item => item.toLowerCase().includes(keyword)),
    }))
    .filter(group => group.items.length)
})
const tocItems = computed<TocItem[]>(() => (tools.value?.items || []).map((tool, index) => ({
  id: tool.tool_uuid,
  anchor: toolAnchor(tool),
  title: tool.name,
  indexLabel: String(index + 1),
})))
const activeFilterChips = computed(() => [
  query.value ? { key: 'query', label: `搜索：${query.value}` } : null,
  selectedLayer.value ? { key: 'layer', label: `层级：${layerOptions.value[selectedLayer.value] || selectedLayer.value}` } : null,
  selectedScene.value ? { key: 'scene', label: `场景：${selectedScene.value}` } : null,
  selectedGoal.value ? { key: 'goal', label: `目标：${selectedGoal.value}` } : null,
].filter(Boolean) as Array<{ key: string; label: string }>)
const recommendedChains = computed(() => (recommendation.value?.chains?.length ? recommendation.value.chains : chains.value).slice(0, 3))

function toolAnchor(tool: ExpressionTool) {
  return `expression-tool-${tool.tool_uuid}`
}

function uniqueValues(values: string[]) {
  const seen = new Set<string>()
  return values
    .map(value => value.trim())
    .filter((value) => {
      if (!value || seen.has(value)) return false
      seen.add(value)
      return true
    })
}

function facetLabel(label: string, count?: number) {
  return typeof count === 'number' ? `${label} · ${count}` : label
}

async function applySearchSuggestion(value: string) {
  query.value = value
  searchMenuOpen.value = false
  await loadTools()
  await loadChains()
  syncQueryToUrl()
}

function openSearchMenu() {
  searchMenuOpen.value = true
}

function closeSearchMenuSoon() {
  window.setTimeout(() => {
    searchMenuOpen.value = false
  }, 120)
}

async function clearFilter(key: string) {
  if (key === 'query') query.value = ''
  if (key === 'layer') selectedLayer.value = ''
  if (key === 'scene') selectedScene.value = ''
  if (key === 'goal') selectedGoal.value = ''
  await loadTools()
  await loadChains()
  await loadRecommendation()
  syncQueryToUrl()
}

async function resetFilters() {
  query.value = ''
  selectedLayer.value = ''
  selectedScene.value = ''
  selectedGoal.value = ''
  await loadTools()
  await loadChains()
  await loadRecommendation()
  syncQueryToUrl()
}

async function applyFilters() {
  await loadTools()
  await loadChains()
  await loadRecommendation()
  syncQueryToUrl()
}

async function loadTools() {
  loading.value = true
  try {
    tools.value = await expressionApi.listTools({
      layer: selectedLayer.value || undefined,
      scene: selectedScene.value || undefined,
      goal: selectedGoal.value || undefined,
      q: query.value || undefined,
      limit: 80,
    })
    if (expandedToolId.value && !tools.value.items.some((tool) => tool.tool_uuid === expandedToolId.value)) {
      expandedToolId.value = ''
      selectedTool.value = null
    }
  } finally {
    loading.value = false
  }
}

async function loadChains() {
  const data = await expressionApi.chains({
    scene: selectedScene.value || undefined,
    goal: selectedGoal.value || undefined,
    q: query.value || undefined,
    limit: 20,
  })
  chains.value = data.items
}

async function selectTool(tool: ExpressionTool) {
  if (expandedToolId.value === tool.tool_uuid) {
    expandedToolId.value = ''
    selectedTool.value = null
    return
  }
  expandedToolId.value = tool.tool_uuid
  selectedTool.value = await expressionApi.getTool(tool.tool_uuid)
}

async function expandToolFromHash() {
  const hash = route.hash || window.location.hash
  if (!hash.startsWith('#expression-tool-')) return
  const toolId = hash.replace('#expression-tool-', '')
  const tool = tools.value?.items.find((item) => item.tool_uuid === toolId)
  if (!tool) return
  await selectTool(tool)
  await nextTick()
  document.getElementById(toolAnchor(tool))?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function loadRecommendation() {
  recommendation.value = await expressionApi.recommend({
    scene: selectedScene.value || '修复',
    goal: selectedGoal.value || '修复信任',
    limit: 3,
  })
}

function normalizeTab(value: unknown) {
  const tab = typeof value === 'string' ? value : ''
  return expressionTabs.some((item) => item.id === tab) ? tab : 'atomic_tools'
}

function onTabChange(value: string) {
  activeTab.value = normalizeTab(value)
  syncQueryToUrl()
}

function syncQueryToUrl() {
  const nextQuery: Record<string, string> = {}
  if (activeTab.value !== 'atomic_tools') nextQuery.tab = activeTab.value
  if (query.value) nextQuery.q = query.value
  if (selectedLayer.value) nextQuery.layer = selectedLayer.value
  if (selectedScene.value) nextQuery.scene = selectedScene.value
  if (selectedGoal.value) nextQuery.goal = selectedGoal.value
  router.replace({ path: '/expression', query: nextQuery, hash: route.hash })
}

function toolDefinition(tool: ExpressionTool) {
  return `${tool.name}不是一句固定话术，而是一种表达动作：在${tool.best_scenes.slice(0, 2).join('、') || '具体互动'}中，用“${tool.formula || tool.category}”把事实、感受、边界和下一步组织清楚。`
}

function toolPrinciple(tool: ExpressionTool) {
  if (tool.layer === 'emotion') return '先承接情绪，再谈解释和行动；任何判断都要允许对方纠正。'
  if (tool.layer === 'relationship') return '关系工具的底线是可拒绝、可退出、可复盘，不能把善意包装成控制。'
  if (tool.layer === 'nonverbal') return '非语言只负责降低压迫感和增强清晰度，不能替代明确同意。'
  if (tool.layer === 'structure') return '结构用于减轻混乱，不用于逼对方按你的结论走。'
  if (tool.layer === 'ammo') return '内容要具体、有画面、有退路；幽默和故事不能拿来转移责任。'
  return '先说清楚，再说温柔；先给证据，再留空间。'
}

function sceneUsage(scene: string, tool: ExpressionTool) {
  if (scene.includes('冲突') || scene.includes('修复')) return `先降低防御，再用${tool.name}组织事实和下一步。`
  if (scene.includes('暧昧') || scene.includes('初识')) return `轻一点使用，重点是打开空间，而不是制造压力。`
  if (scene.includes('长期')) return `适合沉淀成共同约定，避免每次都从头争。`
  return `用于把模糊感受转成可被讨论的小动作。`
}

function formatMicroStep(step: string | { name?: string; rule?: string; [key: string]: unknown }) {
  if (typeof step === 'string') return step
  const name = typeof step.name === 'string' ? step.name : ''
  const rule = typeof step.rule === 'string' ? step.rule : ''
  return [name, rule].filter(Boolean).join('：') || JSON.stringify(step)
}

function toolMicroSteps(tool: ExpressionTool) {
  const steps = tool.learning_blueprint?.micro_steps?.length ? tool.learning_blueprint.micro_steps : tool.micro_steps
  return steps.map(formatMicroStep)
}

function toolRiskBoundaries(tool: ExpressionTool) {
  if (tool.learning_blueprint?.risk_boundaries?.length) return tool.learning_blueprint.risk_boundaries
  if (tool.learning_blueprint?.anti_patterns?.length) return tool.learning_blueprint.anti_patterns.map(item => `避免：${item}`)
  return tool.risk_flags
}

function lowQualityResponse(dialogueCase: { low_quality_response?: string; poor_response?: string }) {
  return dialogueCase.low_quality_response || dialogueCase.poor_response || '暂无低质量回应示例'
}

function practicePrompt(tool: ExpressionTool) {
  const scene = tool.best_scenes[0] || '当前关系场景'
  return `选一个${scene}里的真实小片段，先写一句旧回应，再按“${tool.formula || tool.name}”改写成 30 字以内的新回应，最后检查：是否给了对方退路，是否没有替对方做决定。`
}

const MetricPill = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: [String, Number], required: true },
  },
  setup(props) {
    return () => h('div', { class: 'text-center' }, [
      h('p', { class: 'text-xs text-gray-500 dark:text-gray-400' }, props.label),
      h('p', { class: 'mt-1 text-2xl font-bold text-indigo-600 dark:text-indigo-300' }, String(props.value)),
    ])
  },
})

onMounted(async () => {
  activeTab.value = normalizeTab(route.query.tab)
  query.value = typeof route.query.q === 'string' ? route.query.q : ''
  selectedLayer.value = typeof route.query.layer === 'string' ? route.query.layer : ''
  selectedScene.value = typeof route.query.scene === 'string' ? route.query.scene : ''
  selectedGoal.value = typeof route.query.goal === 'string' ? route.query.goal : ''
  await Promise.all([loadTools(), loadChains()])
  await expandToolFromHash()
  await loadRecommendation()
})

watch(
  () => route.query,
  async (value) => {
    const nextTab = normalizeTab(value.tab)
    const nextQuery = typeof value.q === 'string' ? value.q : ''
    const nextLayer = typeof value.layer === 'string' ? value.layer : ''
    const nextScene = typeof value.scene === 'string' ? value.scene : ''
    const nextGoal = typeof value.goal === 'string' ? value.goal : ''
    if (
      nextTab === activeTab.value &&
      nextQuery === query.value &&
      nextLayer === selectedLayer.value &&
      nextScene === selectedScene.value &&
      nextGoal === selectedGoal.value
    ) return
    activeTab.value = nextTab
    query.value = nextQuery
    selectedLayer.value = nextLayer
    selectedScene.value = nextScene
    selectedGoal.value = nextGoal
    await applyFilters()
  },
)
</script>
