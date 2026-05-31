<template>
  <div class="p-4 sm:p-6 lg:p-8">
    <div class="mb-6 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <RouterLink
          :to="{ path: '/resources', query: backQuery }"
          class="text-sm font-semibold text-blue-600 underline-offset-2 hover:underline dark:text-blue-300"
        >
          返回资源海洋
        </RouterLink>
        <h1 class="mt-3 text-3xl font-bold text-gray-800 dark:text-white">{{ resource?.title || '资源详情' }}</h1>
        <p class="mt-2 max-w-3xl text-gray-500 dark:text-gray-400">
          单条资源的完整内容、来源摘要、表达工具链和训练入口，适合收藏、分享和复盘。
        </p>
      </div>
      <div v-if="resource" class="flex flex-wrap gap-2">
        <RouterLink :to="{ path: '/trainer', query: { resource_id: resource.id, q: resource.title || resource.category } }" class="btn-primary">
          加入训练
        </RouterLink>
        <RouterLink :to="{ path: '/mistakes', query: { resource_id: resource.id, q: resource.mistake_pattern || resource.expression_goal || resource.title } }" class="btn-secondary">
          错题改写
        </RouterLink>
      </div>
    </div>

    <div v-if="loading" class="rounded-lg bg-white p-10 text-center text-gray-500 shadow-sm dark:bg-gray-800">
      加载资源详情...
    </div>

    <div v-else-if="error" class="rounded-lg border border-red-100 bg-red-50 p-6 text-red-700 dark:border-red-900/40 dark:bg-red-900/20 dark:text-red-200">
      <p class="font-semibold">资源加载失败</p>
      <p class="mt-2 text-sm">{{ error }}</p>
      <button class="btn-secondary mt-4" type="button" @click="loadResource">重试</button>
    </div>

    <div
      v-else-if="resource"
      class="grid grid-cols-1 gap-6 transition-[grid-template-columns] xl:grid-cols-[minmax(0,1fr)_280px]"
      :class="tocCollapsed ? 'xl:!grid-cols-1' : ''"
    >
      <main class="space-y-6">
        <section :id="sectionAnchor('overview')" class="card scroll-mt-24">
          <div class="mb-4 flex flex-wrap items-center gap-2">
            <span class="rounded bg-blue-100 px-2 py-1 text-xs font-semibold text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">{{ typeLabel(resource.type) }}</span>
            <span class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">{{ resource.category }}</span>
            <span v-if="resource.applicable_scene" class="rounded bg-emerald-50 px-2 py-1 text-xs text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300">{{ resource.applicable_scene }}</span>
            <span v-if="resource.quality_score" class="rounded bg-indigo-50 px-2 py-1 text-xs text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-300">质量分 {{ resource.quality_score }}</span>
            <span
              v-if="resource.review_status"
              class="rounded px-2 py-1 text-xs font-semibold"
              :class="resource.review_status === 'quarantine' ? 'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-200' : 'bg-sky-50 text-sky-700 dark:bg-sky-900/20 dark:text-sky-200'"
            >
              {{ statusLabel(resource.review_status) }}
            </span>
          </div>
          <p class="whitespace-pre-wrap break-words text-base leading-8 text-gray-700 dark:text-gray-200">{{ resource.content }}</p>
          <div class="mt-4 rounded-lg border border-emerald-100 bg-emerald-50 p-4 text-sm leading-7 text-emerald-900 dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:text-emerald-100">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <p class="font-semibold">来源边界</p>
              <span class="rounded bg-white px-2 py-1 text-xs font-semibold text-emerald-700 dark:bg-gray-900 dark:text-emerald-200">{{ sourceBoundaryLabel(resource) }}</span>
            </div>
            <p class="mt-2">{{ sourceBoundaryDescription(resource) }}</p>
          </div>
          <div v-if="resource.review_status === 'quarantine'" class="mt-4 rounded-lg border border-amber-100 bg-amber-50 p-4 text-sm leading-7 text-amber-900 dark:border-amber-900/40 dark:bg-amber-950/30 dark:text-amber-100">
            <p class="font-semibold">旧版隔离资源</p>
            <p class="mt-1">这条记录保留用于审计和追溯，不进入默认资源海洋。页面会尽量从旧正文抽取案例结构；正式学习优先使用带 `content_unit` 和 `variant_signature` 的案例矩阵资源。</p>
          </div>
        </section>

        <section v-if="caseBlueprint" :id="sectionAnchor('blueprint')" class="card scroll-mt-24">
          <div class="mb-4 flex flex-col gap-2 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <h2 class="text-xl font-bold text-gray-800 dark:text-white">案例蓝图</h2>
              <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">每张合格学习卡必须包含场景、原话、信号、错因、回应、边界和迁移练习。</p>
            </div>
            <span v-if="resource.content_unit" class="rounded bg-indigo-50 px-3 py-2 text-xs font-semibold text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-200">
              {{ resource.content_unit }}
            </span>
          </div>
          <div class="grid grid-cols-1 gap-3 lg:grid-cols-2">
            <InfoLine label="关系阶段" :value="stringField(caseBlueprint, 'relation_stage')" />
            <InfoLine label="触发事件" :value="stringField(caseBlueprint, 'trigger')" />
            <InfoLine label="具体场景" :value="stringField(caseBlueprint, 'setting')" wide />
            <InfoLine label="TA 原话" :value="stringField(caseBlueprint, 'their_words')" />
            <InfoLine label="表层信号" :value="stringField(caseBlueprint, 'surface_signal')" />
            <InfoLine label="深层可能" :value="stringField(caseBlueprint, 'deeper_need')" />
            <InfoLine label="常见失误" :value="stringField(caseBlueprint, 'common_mistake')" />
            <InfoLine label="为什么错" :value="stringField(caseBlueprint, 'why_wrong')" wide />
            <InfoLine label="更好回应" :value="stringField(caseBlueprint, 'better_response')" wide />
            <InfoLine label="边界提醒" :value="stringField(caseBlueprint, 'boundary_note')" wide />
            <InfoLine label="练习任务" :value="stringField(caseBlueprint, 'practice_task')" />
            <InfoLine label="迁移场景" :value="stringField(caseBlueprint, 'transfer_scene')" />
          </div>
          <div v-if="objectList(caseBlueprint, 'dialogue_script').length" class="mt-4 rounded-lg bg-indigo-50 p-4 text-sm leading-7 text-indigo-900 dark:bg-indigo-950/30 dark:text-indigo-100">
            <p class="font-semibold">完整多轮对话</p>
            <div class="mt-3 space-y-2">
              <div
                v-for="(turn, index) in objectList(caseBlueprint, 'dialogue_script')"
                :key="`dialogue-turn-${index}`"
                class="rounded-lg border bg-white p-3 dark:bg-gray-900"
                :class="dialogueTurnClass(turn.speaker)"
              >
                <div class="flex flex-wrap items-center gap-2">
                  <p class="text-xs font-semibold">{{ turn.speaker || '对话' }}</p>
                  <span v-if="turn.purpose" class="text-xs opacity-70">{{ turn.purpose }}</span>
                </div>
                <p class="mt-1">{{ turn.line }}</p>
              </div>
            </div>
          </div>
          <div v-if="stringList(caseBlueprint, 'response_steps').length" class="mt-4 rounded-lg bg-emerald-50 p-4 text-sm leading-7 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-100">
            <p class="font-semibold">回应拆解</p>
            <ol class="mt-2 space-y-1">
              <li v-for="(step, index) in stringList(caseBlueprint, 'response_steps')" :key="`step-${index}`">{{ index + 1 }}. {{ step }}</li>
            </ol>
          </div>
          <div v-if="objectList(caseBlueprint, 'response_variants').length" class="mt-4 rounded-lg bg-emerald-50 p-4 text-sm leading-7 text-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100">
            <p class="font-semibold">多视角更好回应</p>
            <div class="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <div
                v-for="variant in objectList(caseBlueprint, 'response_variants')"
                :key="`detail-variant-${variant.label}`"
                class="rounded-lg border border-emerald-100 bg-white p-3 dark:border-emerald-900/40 dark:bg-gray-900"
              >
                <p class="text-xs font-semibold text-emerald-700 dark:text-emerald-200">{{ variant.label || '回应变体' }}</p>
                <p class="mt-1">{{ variant.response }}</p>
                <p v-if="variant.perspective" class="mt-2 text-xs opacity-80">视角：{{ variant.perspective }}</p>
                <p v-if="variant.why_it_works" class="mt-1 text-xs opacity-80">有效点：{{ variant.why_it_works }}</p>
              </div>
            </div>
          </div>
          <div v-if="objectList(caseBlueprint, 'perspective_examples').length" class="mt-4 rounded-lg bg-sky-50 p-4 text-sm leading-7 text-sky-900 dark:bg-sky-950/30 dark:text-sky-100">
            <p class="font-semibold">举一反三分析</p>
            <div class="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <div
                v-for="example in objectList(caseBlueprint, 'perspective_examples')"
                :key="`detail-perspective-${example.label}`"
                class="rounded-lg border border-sky-100 bg-white p-3 dark:border-sky-900/40 dark:bg-gray-900"
              >
                <p class="text-xs font-semibold text-sky-700 dark:text-sky-200">{{ example.label || '迁移视角' }}</p>
                <p v-if="example.what_they_may_feel" class="mt-1">{{ example.what_they_may_feel }}</p>
                <p v-if="example.what_you_may_feel" class="mt-1">{{ example.what_you_may_feel }}</p>
                <p v-if="example.what_is_happening" class="mt-1">{{ example.what_is_happening }}</p>
                <p v-if="example.what_must_stay_safe" class="mt-1">{{ example.what_must_stay_safe }}</p>
                <p v-if="example.what_to_notice" class="mt-2 text-xs opacity-80">观察：{{ example.what_to_notice }}</p>
                <p v-if="example.learning_point" class="mt-1 text-xs opacity-80">学习点：{{ example.learning_point }}</p>
              </div>
            </div>
          </div>
          <div v-if="transferAnalysis.stable_principles.length" class="mt-4 rounded-lg bg-indigo-50 p-4 text-sm leading-7 text-indigo-900 dark:bg-indigo-950/30 dark:text-indigo-100">
            <p class="font-semibold">迁移分析</p>
            <div class="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-3">
              <div class="rounded-lg bg-white p-3 dark:bg-gray-900">
                <p class="text-xs font-semibold text-indigo-700 dark:text-indigo-200">不变原则</p>
                <ul class="mt-2 space-y-1">
                  <li v-for="item in transferAnalysis.stable_principles" :key="`stable-${item}`">- {{ item }}</li>
                </ul>
              </div>
              <div class="rounded-lg bg-white p-3 dark:bg-gray-900">
                <p class="text-xs font-semibold text-indigo-700 dark:text-indigo-200">可变参数</p>
                <ul class="mt-2 space-y-1">
                  <li v-for="item in transferAnalysis.changeable_parameters" :key="`change-${item}`">- {{ item }}</li>
                </ul>
              </div>
              <div class="rounded-lg bg-white p-3 dark:bg-gray-900">
                <p class="text-xs font-semibold text-indigo-700 dark:text-indigo-200">自检问题</p>
                <ul class="mt-2 space-y-1">
                  <li v-for="item in transferAnalysis.self_check_questions" :key="`check-${item}`">- {{ item }}</li>
                </ul>
              </div>
            </div>
          </div>
          <div v-if="objectList(caseBlueprint, 'misread_risks').length" class="mt-4 rounded-lg bg-rose-50 p-4 text-sm leading-7 text-rose-900 dark:bg-rose-950/30 dark:text-rose-100">
            <p class="font-semibold">常见误读风险</p>
            <div class="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
              <div
                v-for="risk in objectList(caseBlueprint, 'misread_risks')"
                :key="`risk-${risk.risk}`"
                class="rounded bg-white p-3 dark:bg-gray-900"
              >
                <p class="text-xs font-semibold">{{ risk.risk }}</p>
                <p class="mt-1 text-xs opacity-80">{{ risk.correction }}</p>
              </div>
            </div>
          </div>
          <div v-if="objectList(caseBlueprint, 'practice_ladder').length" class="mt-4 rounded-lg bg-violet-50 p-4 text-sm leading-7 text-violet-900 dark:bg-violet-950/30 dark:text-violet-100">
            <p class="font-semibold">练习阶梯</p>
            <div class="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
              <div
                v-for="drill in objectList(caseBlueprint, 'practice_ladder')"
                :key="`practice-ladder-${drill.level}`"
                class="rounded bg-white p-3 dark:bg-gray-900"
              >
                <p class="text-xs font-semibold">{{ drill.level }}</p>
                <p class="mt-1">{{ drill.task }}</p>
                <p v-if="drill.pass_rule" class="mt-1 text-xs opacity-80">通过标准：{{ drill.pass_rule }}</p>
              </div>
            </div>
          </div>
          <div v-if="stringList(caseBlueprint, 'variant_deltas').length" class="mt-4 rounded-lg bg-amber-50 p-4 text-sm leading-7 text-amber-800 dark:bg-amber-950/30 dark:text-amber-100">
            <p class="font-semibold">真实变体差异</p>
            <ul class="mt-2 space-y-1">
              <li v-for="(delta, index) in stringList(caseBlueprint, 'variant_deltas')" :key="`delta-${index}`">- {{ delta }}</li>
            </ul>
          </div>
          <div class="mt-4 rounded-lg bg-sky-50 p-4 text-sm leading-7 text-sky-800 dark:bg-sky-950/30 dark:text-sky-100">
            <p class="font-semibold">完整性检查</p>
            <div class="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
              <span
                v-for="check in completenessChecks"
                :key="check.label"
                class="rounded px-2 py-1 text-xs font-semibold"
                :class="check.ok ? 'bg-white text-sky-700 dark:bg-gray-900 dark:text-sky-200' : 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-200'"
              >
                {{ check.ok ? '已具备' : '需补充' }} · {{ check.label }}
              </span>
            </div>
          </div>
        </section>

        <section :id="sectionAnchor('learning')" class="card scroll-mt-24">
          <h2 class="mb-4 text-xl font-bold text-gray-800 dark:text-white">学习拆解</h2>
          <div class="grid grid-cols-1 gap-3 lg:grid-cols-2">
            <div class="rounded-lg bg-gray-50 p-4 text-sm leading-7 dark:bg-gray-800">
              <p class="font-semibold text-gray-800 dark:text-white">概念定义</p>
              <p class="mt-1 text-gray-600 dark:text-gray-300">{{ learningConcept(resource) }}</p>
            </div>
            <div class="rounded-lg bg-gray-50 p-4 text-sm leading-7 dark:bg-gray-800">
              <p class="font-semibold text-gray-800 dark:text-white">核心原则</p>
              <p class="mt-1 text-gray-600 dark:text-gray-300">{{ learningPrinciple(resource) }}</p>
            </div>
            <div class="rounded-lg bg-gray-50 p-4 text-sm leading-7 dark:bg-gray-800">
              <p class="font-semibold text-gray-800 dark:text-white">实践方法</p>
              <p class="mt-1 text-gray-600 dark:text-gray-300">{{ learningMethod(resource) }}</p>
            </div>
            <div class="rounded-lg bg-gray-50 p-4 text-sm leading-7 dark:bg-gray-800">
              <p class="font-semibold text-gray-800 dark:text-white">适用场景</p>
              <p class="mt-1 text-gray-600 dark:text-gray-300">{{ learningScene(resource) }}</p>
            </div>
          </div>

          <div class="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
            <div class="rounded-lg bg-red-50 p-4 text-sm leading-7 text-red-700 dark:bg-red-900/20 dark:text-red-300">
              <p class="font-semibold">低质量做法</p>
              <p class="mt-1">{{ caseComparison(resource).bad || fallbackBadExample(resource) }}</p>
            </div>
            <div class="rounded-lg bg-emerald-50 p-4 text-sm leading-7 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300">
              <p class="font-semibold">更好做法</p>
              <p class="mt-1">{{ caseComparison(resource).good || fallbackGoodExample(resource) }}</p>
            </div>
          </div>

          <div class="mt-4 rounded-lg bg-indigo-50 p-4 text-sm leading-7 text-indigo-800 dark:bg-indigo-950/30 dark:text-indigo-200">
            <p class="font-semibold">练习任务</p>
            <ol class="mt-2 space-y-1">
              <li v-for="(drill, index) in detailDrills(resource)" :key="`${resource.id}-drill-${drill}`">
                {{ index + 1 }}. {{ drill }}
              </li>
            </ol>
          </div>
        </section>

        <section v-if="resource.usage_tip || resource.expression_goal || toolIds.length" :id="sectionAnchor('practice')" class="card scroll-mt-24">
          <h2 class="mb-4 text-xl font-bold text-gray-800 dark:text-white">练习路径</h2>
          <div v-if="resource.usage_tip" class="rounded-lg bg-yellow-50 p-4 text-sm leading-7 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-200">
            <p class="font-semibold">使用提示</p>
            <p class="mt-1">{{ resource.usage_tip }}</p>
          </div>
          <div class="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
            <div v-if="resource.expression_goal" class="rounded-lg bg-indigo-50 p-4 text-sm text-indigo-800 dark:bg-indigo-900/20 dark:text-indigo-200">
              <p class="font-semibold">表达目标</p>
              <p class="mt-1">{{ resource.expression_goal }}</p>
            </div>
            <div v-if="resource.mistake_pattern" class="rounded-lg bg-rose-50 p-4 text-sm text-rose-800 dark:bg-rose-900/20 dark:text-rose-200">
              <p class="font-semibold">常见错题</p>
              <p class="mt-1">{{ resource.mistake_pattern }}</p>
            </div>
          </div>
          <div v-if="toolIds.length" class="mt-4">
            <p class="mb-2 text-sm font-semibold text-gray-800 dark:text-white">推荐表达工具</p>
            <div class="flex flex-wrap gap-2">
              <RouterLink
                v-for="toolId in toolIds"
                :key="toolId"
                :to="{ path: '/expression', hash: `#expression-tool-${toolId}` }"
                class="rounded bg-indigo-50 px-3 py-2 text-sm font-semibold text-indigo-700 underline-offset-2 hover:underline dark:bg-indigo-900/20 dark:text-indigo-200"
              >
                {{ toolDisplayName(toolId) }}
              </RouterLink>
            </div>
          </div>
        </section>

        <section v-if="resource.source_title || resource.source_summary || resource.source_url" :id="sectionAnchor('source')" class="card scroll-mt-24">
          <h2 class="mb-4 text-xl font-bold text-gray-800 dark:text-white">来源与导读</h2>
          <div class="mb-4 rounded-lg border border-sky-100 bg-sky-50 p-4 text-sm leading-7 text-sky-900 dark:border-sky-900/40 dark:bg-sky-950/30 dark:text-sky-100">
            <p class="font-semibold">第三方来源处理规则</p>
            <p class="mt-1">不默认搬运第三方全文。优先保存链接、标题、摘要、合规短摘录、结构化分析和本地原创改写；没有明确许可的内容只作为阅读入口和训练蓝图来源。</p>
          </div>
          <div class="space-y-3 text-sm leading-7 text-gray-600 dark:text-gray-300">
            <p v-if="resource.source_title"><span class="font-semibold text-gray-800 dark:text-white">来源标题：</span>{{ resource.source_title }}</p>
            <p v-if="resource.source_summary"><span class="font-semibold text-gray-800 dark:text-white">摘要：</span>{{ resource.source_summary }}</p>
            <p v-if="resource.source_excerpt"><span class="font-semibold text-gray-800 dark:text-white">导读片段：</span>{{ resource.source_excerpt }}</p>
            <p v-if="resource.source"><span class="font-semibold text-gray-800 dark:text-white">登记来源：</span>{{ resource.source }}</p>
            <p v-if="resource.source_license"><span class="font-semibold text-gray-800 dark:text-white">许可：</span>{{ resource.source_license }}</p>
            <a
              v-if="isHttpUrl(resource.source_url)"
              :href="resource.source_url"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex break-all text-sky-600 underline-offset-2 hover:underline dark:text-sky-300"
            >
              {{ resource.source_url }}
            </a>
          </div>
        </section>

        <section :id="sectionAnchor('metadata')" class="card scroll-mt-24">
          <h2 class="mb-4 text-xl font-bold text-gray-800 dark:text-white">结构化信息</h2>
          <div class="grid grid-cols-1 gap-3 text-sm md:grid-cols-2">
            <InfoLine label="资源 ID" :value="String(resource.id)" />
            <InfoLine label="UUID" :value="resource.resource_uuid" />
            <InfoLine label="难度" :value="formatOptional(resource.difficulty_level)" />
            <InfoLine label="情绪强度" :value="formatOptional(resource.emotional_intensity)" />
            <InfoLine label="效果评分" :value="formatOptional(resource.effectiveness_rating)" />
            <InfoLine label="依恋适配" :value="resource.attachment_suitability" />
            <InfoLine label="目标人群" :value="resource.gender_target" />
            <InfoLine label="表达等级" :value="resource.expression_level" />
            <InfoLine label="言语动作" :value="resource.speech_act" />
            <InfoLine label="覆盖主线" :value="resource.coverage_axis" />
            <InfoLine label="变体家族" :value="resource.variant_family" />
            <InfoLine label="完整度" :value="formatOptional(resource.case_completeness_score)" />
            <InfoLine label="变体签名" :value="resource.variant_signature" wide />
            <InfoLine label="指纹" :value="resource.content_fingerprint" wide />
            <InfoLine label="标签" :value="resource.tags" wide />
          </div>
        </section>
      </main>

      <PageTocSidebar v-model:collapsed="tocCollapsed" title="详情目录" :items="tocItems" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import PageTocSidebar from '@/components/PageTocSidebar.vue'
import { expressionApi, resourcesApi } from '@/utils/api'
import type { ResourceItem } from '@/utils/api'

const route = useRoute()
const resource = ref<ResourceItem | null>(null)
const loading = ref(false)
const error = ref('')
const tocCollapsed = ref(false)
const toolNames = ref<Record<string, string>>({})

const typeMap: Record<string, string> = {
  joke: '段子',
  flirty: '话术',
  story: '故事',
  riddle: '急转弯',
  game: '游戏',
  media: '媒体',
  phrase: '短句',
}

const backQuery = computed(() => {
  const query = { ...route.query }
  delete query.from
  return query
})

const toolIds = computed(() => expressionToolIds(resource.value?.expression_tool_ids_json))
const caseBlueprint = computed(() => parseCaseBlueprint(resource.value?.case_blueprint_json) || fallbackCaseBlueprint(resource.value))
const transferAnalysis = computed(() => {
  const analysis = objectField(caseBlueprint.value, 'transfer_analysis')
  return {
    stable_principles: stringList(analysis, 'stable_principles'),
    changeable_parameters: stringList(analysis, 'changeable_parameters'),
    self_check_questions: stringList(analysis, 'self_check_questions'),
  }
})
const completenessChecks = computed(() => {
  const blueprint = caseBlueprint.value
  const checks = [
    ['具体场景', 'setting'],
    ['TA 原话', 'their_words'],
    ['表层信号', 'surface_signal'],
    ['常见失误', 'common_mistake'],
    ['更好回应', 'better_response'],
    ['边界提醒', 'boundary_note'],
    ['练习任务', 'practice_task'],
    ['真实变体差异', 'variant_deltas'],
  ]
  return checks.map(([label, key]) => ({
    label,
    ok: key === 'variant_deltas' ? stringList(blueprint, key).length > 0 : Boolean(stringField(blueprint, key)),
  }))
})

const tocItems = computed(() => [
  { id: 'overview', anchor: sectionAnchor('overview'), title: '完整内容', indexLabel: '1' },
  ...(caseBlueprint.value ? [{ id: 'blueprint', anchor: sectionAnchor('blueprint'), title: '案例蓝图', indexLabel: '2' }] : []),
  { id: 'learning', anchor: sectionAnchor('learning'), title: '学习拆解', indexLabel: caseBlueprint.value ? '3' : '2' },
  ...(resource.value?.usage_tip || resource.value?.expression_goal || toolIds.value.length
    ? [{ id: 'practice', anchor: sectionAnchor('practice'), title: '练习路径', indexLabel: caseBlueprint.value ? '4' : '3' }]
    : []),
  ...(resource.value?.source_title || resource.value?.source_summary || resource.value?.source_url
    ? [{ id: 'source', anchor: sectionAnchor('source'), title: '来源与导读', indexLabel: caseBlueprint.value ? '5' : '4' }]
    : []),
  { id: 'metadata', anchor: sectionAnchor('metadata'), title: '结构化信息', indexLabel: caseBlueprint.value ? '6' : '5' },
])

function sectionAnchor(name: string) {
  return `resource-detail-${name}`
}

function typeLabel(type?: string) {
  return type ? (typeMap[type] ?? type) : '-'
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    published: '已发布',
    reviewed: '已审核',
    draft: '草稿',
    quarantine: '隔离审计',
    withdrawn: '已撤回',
  }
  return labels[status] || status
}

function isHttpUrl(url?: string) {
  return Boolean(url && /^https?:\/\//i.test(url))
}

function formatOptional(value?: number | string | null) {
  if (value === undefined || value === null || value === '') return '-'
  return String(value)
}

function expressionToolIds(raw?: string) {
  if (!raw) return []
  try {
    const value = JSON.parse(raw)
    return Array.isArray(value) ? value.map(String).filter(Boolean) : []
  } catch {
    return []
  }
}

function toolDisplayName(toolId: string) {
  return toolNames.value[toolId] || toolId
}

function parseCaseBlueprint(raw?: string): Record<string, unknown> | null {
  if (!raw) return null
  try {
    const value = JSON.parse(raw)
    return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : null
  } catch {
    return null
  }
}

function fallbackCaseBlueprint(item: ResourceItem | null): Record<string, unknown> | null {
  if (!item) return null
  const setting = fieldFromContent(item, '场景')
  const theirWords = fieldFromContent(item, 'TA说')
  const mistake = fieldFromContent(item, '常见失误') || fieldFromContent(item, '低质量回应')
  const better = fieldFromContent(item, '更好回应') || fieldFromContent(item, '高质量回应')
  if (!setting || !theirWords || !mistake || !better) return null
  return {
    relation_stage: item.applicable_scene || item.category,
    trigger: '从旧版正文自动抽取，建议后续用案例矩阵样本替换。',
    setting,
    their_words: theirWords,
    surface_signal: fieldFromContent(item, '情绪信号') || '需要从原话、停顿、语气和上下文继续判断。',
    deeper_need: item.expression_goal || '需要被理解、被尊重边界，并保留继续或暂停的选择。',
    common_mistake: mistake,
    why_wrong: item.mistake_pattern || '旧回应容易把关系推向防御、追问或模板化处理。',
    better_response: better,
    response_steps: ['复述事实', '承接情绪', '说明边界', '给出可执行下一步'],
    boundary_note: fieldFromContent(item, '边界与同意') || '任何回应都要允许对方放慢、拒绝、改期或纠正你的理解。',
    practice_task: fieldFromContent(item, '练习任务') || '把旧回应改成包含事实、感受、边界和下一步的一句话。',
    transfer_scene: '换到相邻真实场景再写一次，避免背诵同一句。',
    variant_deltas: ['这是旧资源的结构化抽取视图', '新版案例矩阵会用 content_unit 和 variant_signature 保证真实差异'],
  }
}

function stringField(source: Record<string, unknown> | null, key: string) {
  const value = source?.[key]
  return typeof value === 'string' || typeof value === 'number' ? String(value) : ''
}

function stringList(source: Record<string, unknown> | null, key: string) {
  const value = source?.[key]
  return Array.isArray(value) ? value.map(String).filter(Boolean) : []
}

function objectList(source: Record<string, unknown> | null, key: string) {
  const value = source?.[key]
  return Array.isArray(value)
    ? value
        .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object' && !Array.isArray(item))
        .map((item) => Object.fromEntries(Object.entries(item).map(([entryKey, entryValue]) => [entryKey, String(entryValue ?? '')])))
    : []
}

function objectField(source: Record<string, unknown> | null, key: string) {
  const value = source?.[key]
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}
}

function dialogueTurnClass(speaker: string) {
  if (speaker.includes('低质量')) return 'border-red-100 text-red-800 dark:border-red-900/40 dark:text-red-200'
  if (speaker.includes('更好') || speaker.includes('继续') || speaker.includes('边界')) return 'border-emerald-100 text-emerald-800 dark:border-emerald-900/40 dark:text-emerald-200'
  return 'border-gray-100 text-gray-800 dark:border-gray-800 dark:text-gray-200'
}

function fieldFromContent(resource: { content?: string }, label: string) {
  const text = resource.content || ''
  const pattern = new RegExp(`(?:^|\\n)${label}(?:（[^）]+）)?[：:]\\s*([^\\n]+)`, 'i')
  return text.match(pattern)?.[1]?.trim() || ''
}

function drillList(resource: { recommended_drills_json?: string }) {
  if (!resource.recommended_drills_json) return []
  try {
    const value = JSON.parse(resource.recommended_drills_json)
    if (!Array.isArray(value)) return []
    return value
      .map((item) => {
        if (typeof item === 'string') return item
        if (!item || typeof item !== 'object') return ''
        const drill = item as { prompt?: unknown; text?: unknown; label?: unknown; title?: unknown; type?: unknown }
        return String(drill.prompt || drill.text || drill.label || drill.title || drill.type || '').trim()
      })
      .filter(Boolean)
  } catch {
    return []
  }
}

function learningConcept(resource: ResourceItem) {
  const scene = resource.applicable_scene || resource.category || '关系互动'
  const goal = resource.expression_goal || resource.speech_act || '提升关系中的感知与回应质量'
  return `这是一张${typeLabel(resource.type)}学习卡，用于“${scene}”场景。它的核心不是记住文本，而是理解“什么时候、为什么、怎样”完成${goal}。`
}

function learningPrinciple(resource: ResourceItem) {
  if (resource.mistake_pattern) return `本卡先暴露常见错题“${resource.mistake_pattern}”，再训练把回应改成事实清楚、情绪可承接、边界可退出的表达。`
  if ((resource.expression_goal || '').includes('修复')) return '修复的顺序是承认影响、减少辩解、给出可靠行动；不能把补偿当成要求对方立刻原谅的筹码。'
  if ((resource.category || resource.applicable_scene || '').includes('边界')) return '边界与同意类资源必须保留可拒绝出口，任何推进都要允许对方放慢、拒绝或改期。'
  return '先识别具体信号，再选择表达工具；所有内容都要服务于更清晰、更尊重边界的互动。'
}

function learningMethod(resource: ResourceItem) {
  const scene = fieldFromContent(resource, '场景')
  const theirWords = fieldFromContent(resource, 'TA说')
  if (scene && theirWords) return `第一步读场景，第二步标出“${theirWords}”里的情绪和边界信号，第三步按“${resource.speech_act || resource.expression_goal || '事实-感受-边界-下一步'}”改写回应。`
  return resource.usage_tip || `先提取一个具体场景，再写旧回应和新回应，最后检查是否有事实、感受、边界和下一步。`
}

function learningScene(resource: ResourceItem) {
  return `适合 ${resource.applicable_scene || resource.category || '关系训练'}；难度 ${resource.difficulty_level || '-'}；依恋适配 ${resource.attachment_suitability || '通用'}；目标 ${resource.gender_target || '通用'}。`
}

function caseComparison(resource: ResourceItem) {
  return {
    bad: fieldFromContent(resource, '常见失误') || fieldFromContent(resource, '低质量回应'),
    good: fieldFromContent(resource, '更好回应') || fieldFromContent(resource, '高质量回应'),
  }
}

function fallbackBadExample(resource: ResourceItem) {
  return resource.mistake_pattern ? `围绕“${resource.mistake_pattern}”继续解释、追问或施压。` : '只说结论，不说明事实、感受、边界和下一步。'
}

function fallbackGoodExample(resource: ResourceItem) {
  return resource.expression_goal ? `围绕“${resource.expression_goal}”补足事实、感受、边界和可执行下一步。` : '先承接情绪，再给一个可拒绝、可复盘的小行动。'
}

function detailDrills(resource: ResourceItem) {
  const drills = drillList(resource)
  if (drills.length) return drills
  return [
    `用一句话复述本卡的核心场景：${resource.applicable_scene || resource.category || '当前关系场景'}。`,
    '写一句低质量回应，故意暴露一个常见失误。',
    `按“${resource.speech_act || resource.expression_goal || '事实-感受-边界-下一步'}”改写成更好回应。`,
  ]
}

function sourceBoundaryLabel(resource: ResourceItem) {
  if (isHttpUrl(resource.source_url)) return '有原文入口'
  const source = resource.source || ''
  if (source.startsWith('project_original') || source.startsWith('local_anchor') || source.startsWith('synthetic')) return '项目原创训练卡'
  return '结构化导读卡'
}

function sourceBoundaryDescription(resource: ResourceItem) {
  if (isHttpUrl(resource.source_url)) return '本页展示结构化学习拆解和本地原创改写；外部原文请通过来源链接打开，项目不复制受版权保护的全文。'
  return '本卡为项目内原创训练素材或结构化导读，不伪装为第三方原文；用于训练概念、原则、场景和回应改写。'
}

async function loadResource() {
  const id = Number(route.params.id)
  if (!Number.isFinite(id)) {
    error.value = '资源 ID 无效'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const [loadedResource, filters, expressionTools] = await Promise.all([
      resourcesApi.get(id),
      resourcesApi.filters(160),
      expressionApi.listTools({ limit: 200 }),
    ])
    resource.value = loadedResource
    toolNames.value = {
      ...Object.fromEntries(expressionTools.items.map((tool) => [tool.tool_uuid, tool.name])),
      ...Object.fromEntries(filters.expression_tools.map((tool) => [tool.id, tool.name])),
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '无法加载资源'
  } finally {
    loading.value = false
  }
}

const InfoLine = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: String, required: false, default: '' },
    wide: { type: Boolean, required: false, default: false },
  },
  setup(props) {
    return () => h('div', { class: ['rounded-lg bg-gray-50 p-3 dark:bg-gray-800', props.wide ? 'md:col-span-2' : ''] }, [
      h('p', { class: 'text-xs font-semibold text-gray-500 dark:text-gray-400' }, props.label),
      h('p', { class: 'mt-1 break-words text-gray-800 dark:text-gray-100' }, props.value || '-'),
    ])
  },
})

onMounted(loadResource)

watch(
  () => route.params.id,
  () => {
    loadResource()
  }
)
</script>
