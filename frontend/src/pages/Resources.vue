<template>
  <div class="p-8">
    <div class="mb-8">
      <div class="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h1 class="text-3xl font-bold text-gray-800 dark:text-white">资源海洋</h1>
          <p class="text-gray-500 dark:text-gray-400 mt-2">话术、故事、练习、知识卡片和情绪流动素材</p>
        </div>
        <div class="rounded-lg bg-white px-4 py-3 text-sm text-gray-600 shadow-sm dark:bg-gray-800 dark:text-gray-300">
          第 <span class="font-semibold text-blue-600 dark:text-blue-300">{{ store.currentPage }}</span>
          / {{ store.totalPages }} 页 · {{ store.pageStart }}-{{ store.pageEnd }}
          / {{ store.total }} 条
        </div>
      </div>
    </div>

    <ModuleTabs
      v-model="activeTab"
      :tabs="resourceTabs"
      label="资源海洋选项卡"
      id-prefix="resources-tab"
      class="mb-4"
      @update:model-value="onTabChange"
    />

    <div
      v-if="activeTab === 'source_boundary'"
      class="mb-4 rounded-lg border border-sky-100 bg-sky-50 p-4 text-sm leading-6 text-sky-800 dark:border-sky-900/40 dark:bg-sky-900/20 dark:text-sky-200"
    >
      <p class="font-semibold">来源边界工作区</p>
      <p class="mt-1">
        当前列表优先展示来源标题、链接、摘要、短摘录、许可和本地原创改写边界。第三方网站不默认全文搬运，资源标题进入详情，来源链接单独打开。
      </p>
    </div>

    <!-- 筛选器 -->
    <div class="mb-4 rounded-lg bg-white p-4 shadow-sm dark:bg-gray-800">
      <div class="mb-3 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 class="text-sm font-bold text-gray-800 dark:text-white">主线分组</h2>
          <p class="text-xs text-gray-500 dark:text-gray-400">按微关系训练主轴筛选资源，先看方向，再进具体场景。</p>
        </div>
        <button
          v-if="store.selectedMissionAxis"
          class="text-xs font-semibold text-sky-600 underline-offset-2 hover:underline dark:text-sky-300"
          type="button"
          @click="selectMissionAxis('')"
        >
          清除主线
        </button>
      </div>
      <div class="flex flex-wrap gap-2">
        <button
          v-for="axis in missionAxes"
          :key="axis.value"
          type="button"
          class="rounded-md px-3 py-2 text-sm font-semibold transition-colors"
          :class="store.selectedMissionAxis === axis.value ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'"
          @click="selectMissionAxis(axis.value)"
        >
          {{ axis.label }}
        </button>
      </div>
    </div>

    <div class="mb-6 rounded-lg bg-white p-4 shadow-sm dark:bg-gray-800">
      <div class="mb-3 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 class="text-sm font-bold text-gray-800 dark:text-white">组合检索</h2>
          <p class="text-xs text-gray-500 dark:text-gray-400">下拉建议来自当前 SQLite 可见资源，也可以直接手动输入。</p>
        </div>
        <button class="btn-secondary text-xs" type="button" @click="clearFilters">清空筛选</button>
      </div>
      <div class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-[1.2fr_repeat(7,minmax(0,0.7fr))_auto]">
        <input
          v-model.trim="store.searchQuery"
          list="resource-keyword-options"
          @keyup.enter="applyFilters"
          class="input-mac"
          placeholder="关键词：边界、冷战、复联、可拒绝出口..."
        />
        <datalist id="resource-keyword-options">
          <option v-for="option in keywordOptions" :key="option.value" :value="option.value">
            {{ optionLabel(option) }}
          </option>
        </datalist>
      <select v-model="store.selectedType" @change="applyFilters" class="input-mac">
        <option value="">全部类型</option>
        <option v-for="option in typeOptions" :key="option.value" :value="option.value">
          {{ optionLabel(option, typeLabel(option.value)) }}
        </option>
      </select>
      <input
        v-model.trim="store.selectedCategory"
        list="resource-category-options"
        @keyup.enter="applyFilters"
        class="input-mac"
        placeholder="分类：冲突修复、幽默互动..."
      />
      <datalist id="resource-category-options">
        <option v-for="option in categoryOptions" :key="option.value" :value="option.value">
          {{ optionLabel(option) }}
        </option>
      </datalist>
      <select v-model="store.selectedScene" @change="applyFilters" class="input-mac">
        <option value="">全部场景</option>
        <option v-for="option in sceneOptions" :key="option.value" :value="option.value">
          {{ optionLabel(option) }}
        </option>
      </select>
      <input
        v-model.trim="store.selectedTag"
        list="resource-tag-options"
        @keyup.enter="applyFilters"
        class="input-mac"
        placeholder="标签：低压幽默、边界与同意..."
      />
      <datalist id="resource-tag-options">
        <option v-for="option in tagOptions" :key="option.value" :value="option.value">
          {{ optionLabel(option) }}
        </option>
      </datalist>
      <input
        v-model.trim="store.selectedSource"
        list="resource-source-options"
        @keyup.enter="applyFilters"
        class="input-mac"
        placeholder="来源：Gottman、CNVC、本地话题库..."
      />
      <datalist id="resource-source-options">
        <option v-for="option in sourceOptions" :key="option.value" :value="option.value">
          {{ optionLabel(option) }}
        </option>
      </datalist>
      <input
        v-model.trim="store.selectedExpressionTool"
        list="resource-expression-tool-options"
        @keyup.enter="applyFilters"
        class="input-mac"
        placeholder="表达工具ID/名称"
      />
      <datalist id="resource-expression-tool-options">
        <option v-for="option in expressionToolOptions" :key="option.id" :value="option.id">
          {{ expressionToolLabel(option, 'name') }}
        </option>
        <option v-for="option in expressionToolOptions" :key="`${option.id}-name`" :value="option.name">
          {{ expressionToolLabel(option, 'id') }}
        </option>
      </datalist>
      <input
        v-model.trim="store.selectedExpressionGoal"
        list="resource-expression-goal-options"
        @keyup.enter="applyFilters"
        class="input-mac"
        placeholder="表达目标"
      />
      <datalist id="resource-expression-goal-options">
        <option v-for="option in expressionGoalOptions" :key="option.value" :value="option.value">
          {{ optionLabel(option) }}
        </option>
      </datalist>
      <button @click="randomOne" class="btn-primary">
        🎲 随机一条
      </button>
      <button @click="applyFilters" class="btn-secondary">
        🔄 刷新
      </button>
      </div>
      <div class="mt-4 space-y-3 rounded-lg border border-gray-100 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-900/40">
        <div class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <p class="text-xs font-semibold text-gray-700 dark:text-gray-200">数据库存在项快选</p>
          <p class="text-[11px] text-gray-500 dark:text-gray-400">每个数字都是当前 SQLite 可见资源的记录数，点击即可筛选。</p>
        </div>
        <div class="grid grid-cols-1 gap-3 xl:grid-cols-2">
          <FilterCountGroup title="类型" :items="typeOptions.slice(0, 8)" :labeler="typeOptionLabel" @select="selectFilterValue('type', $event)" />
          <FilterCountGroup title="场景" :items="sceneOptions.slice(0, 10)" @select="selectFilterValue('scene', $event)" />
          <FilterCountGroup title="标签" :items="tagOptions.slice(0, 10)" @select="selectFilterValue('tag', $event)" />
          <FilterCountGroup title="来源" :items="sourceOptions.slice(0, 8)" @select="selectFilterValue('source', $event)" />
          <FilterCountGroup title="表达目的" :items="expressionGoalOptions.slice(0, 10)" @select="selectFilterValue('goal', $event)" />
          <div>
            <p class="mb-2 text-xs font-semibold text-gray-600 dark:text-gray-300">表达工具</p>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="option in expressionToolOptions.slice(0, 10)"
                :key="`quick-tool-${option.id}`"
                type="button"
                class="rounded-full bg-white px-3 py-1.5 text-xs text-gray-700 shadow-sm transition-colors hover:bg-indigo-50 hover:text-indigo-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-indigo-950/40 dark:hover:text-indigo-200"
                :class="store.selectedExpressionTool === option.id || store.selectedExpressionTool === option.name ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-200' : ''"
                @click="selectExpressionToolQuick(option)"
              >
                {{ option.name }} · {{ option.count ?? 0 }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="store.loading" class="text-center py-12 text-gray-400">
      <div class="animate-spin text-4xl mb-4">📚</div>
      <p>加载中...</p>
    </div>

    <div
      v-if="!store.loading && store.filteredItems.length > 0"
      class="grid grid-cols-1 gap-6 transition-[grid-template-columns] xl:grid-cols-[minmax(0,1fr)_280px]"
      :class="tocCollapsed ? 'xl:!grid-cols-1' : ''"
    >
      <div class="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <article
          v-for="(resource, index) in store.filteredItems"
          :id="resourceAnchor(resource)"
          :key="resource.id"
          class="card card-hover flex min-w-0 scroll-mt-24 flex-col"
        >
          <div class="flex flex-wrap items-center gap-2 mb-4">
            <span class="px-2 py-1 rounded text-xs font-medium bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
              {{ typeLabel(resource.type) }}
            </span>
            <span class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">
              {{ resource.category }}
            </span>
            <span v-if="resource.applicable_scene" class="rounded bg-green-50 px-2 py-1 text-xs text-green-700 dark:bg-green-900/20 dark:text-green-300">
              {{ resource.applicable_scene }}
            </span>
            <span v-if="resource.difficulty_level" class="rounded bg-purple-50 px-2 py-1 text-xs text-purple-700 dark:bg-purple-900/20 dark:text-purple-300">
              难度 {{ resource.difficulty_level }}
            </span>
            <a
              v-if="isHttpUrl(resource.source_url)"
              :href="resource.source_url"
              target="_blank"
              rel="noopener noreferrer"
              class="ml-auto inline-flex items-center rounded bg-sky-50 px-2 py-1 text-xs font-semibold text-sky-700 transition-colors hover:bg-sky-100 dark:bg-sky-900/20 dark:text-sky-300 dark:hover:bg-sky-900/40"
            >
              打开信息源
            </a>
          </div>
          <RouterLink
            :to="{ name: 'ResourceDetail', params: { id: resource.id } }"
            class="mb-2 block text-lg font-bold text-gray-800 underline-offset-4 hover:text-blue-600 hover:underline dark:text-white dark:hover:text-blue-300"
          >
            {{ index + store.pageStart }}. {{ resource.title || '无标题' }}
          </RouterLink>

          <section class="mb-4 rounded-lg border border-indigo-100 bg-indigo-50/70 p-4 text-sm leading-6 text-indigo-950 dark:border-indigo-900/40 dark:bg-indigo-950/20 dark:text-indigo-100">
            <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
              <p class="font-semibold">完整案例学习区</p>
              <span class="rounded bg-white px-2 py-1 text-xs font-semibold text-indigo-700 dark:bg-gray-900 dark:text-indigo-200">
                {{ caseBlueprint(resource).axis_label || resource.category }}
              </span>
            </div>
            <div class="grid grid-cols-1 gap-3">
              <div class="rounded bg-white/75 p-3 dark:bg-gray-900/60">
                <p class="text-xs font-semibold text-indigo-600 dark:text-indigo-300">场景故事</p>
                <p class="mt-1">{{ caseStory(resource) }}</p>
              </div>
              <div class="rounded bg-white/75 p-3 dark:bg-gray-900/60">
                <p class="text-xs font-semibold text-indigo-600 dark:text-indigo-300">完整对话</p>
                <div
                  v-if="dialogueScript(resource).length"
                  class="mt-2 space-y-2"
                >
                  <div
                    v-for="(turn, turnIndex) in dialogueScript(resource)"
                    :key="`${resource.id}-dialogue-${turnIndex}`"
                    class="rounded border p-2"
                    :class="dialogueTurnClass(turn.speaker)"
                  >
                    <div class="flex flex-wrap items-center gap-2">
                      <p class="text-[11px] font-semibold">{{ turn.speaker }}</p>
                      <span v-if="turn.purpose" class="text-[11px] opacity-70">{{ turn.purpose }}</span>
                    </div>
                    <p class="mt-1">{{ turn.line }}</p>
                  </div>
                </div>
                <div v-else class="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                  <div class="rounded border border-red-100 bg-red-50 p-2 text-red-800 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-200">
                    <p class="text-[11px] font-semibold">TA 说</p>
                    <p class="mt-1">{{ caseBlueprint(resource).their_words || fieldFromContent(resource, 'TA说') || '详见完整详情。' }}</p>
                    <p class="mt-2 text-[11px] font-semibold">低质量回应</p>
                    <p class="mt-1">{{ weakResponse(resource) }}</p>
                  </div>
                  <div class="rounded border border-emerald-100 bg-emerald-50 p-2 text-emerald-800 dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:text-emerald-200">
                    <p class="text-[11px] font-semibold">更好回应</p>
                    <p class="mt-1">{{ betterResponse(resource) }}</p>
                    <p class="mt-2 text-[11px] font-semibold">边界出口</p>
                    <p class="mt-1">{{ caseBlueprint(resource).boundary_note || '保留可拒绝、可跳过、可晚点再说。' }}</p>
                  </div>
                </div>
              </div>
              <div class="rounded bg-white/75 p-3 dark:bg-gray-900/60">
                <p class="text-xs font-semibold text-indigo-600 dark:text-indigo-300">为什么这样学</p>
                <p class="mt-1">{{ caseBlueprint(resource).why_wrong || learningPrinciple(resource) }}</p>
                <p
                  v-if="caseBlueprint(resource).de_bias_note"
                  class="mt-2 rounded border border-amber-100 bg-amber-50 p-2 text-xs leading-5 text-amber-900 dark:border-amber-900/40 dark:bg-amber-950/20 dark:text-amber-100"
                >
                  去偏提醒：{{ caseBlueprint(resource).de_bias_note }}
                </p>
                <ol v-if="caseResponseSteps(resource).length" class="mt-2 space-y-1">
                  <li v-for="(step, stepIndex) in caseResponseSteps(resource)" :key="`${resource.id}-step-${stepIndex}`">
                    {{ stepIndex + 1 }}. {{ step }}
                  </li>
                </ol>
              </div>
              <div
                v-if="responseVariants(resource).length"
                class="rounded bg-white/75 p-3 dark:bg-gray-900/60"
              >
                <p class="text-xs font-semibold text-indigo-600 dark:text-indigo-300">多视角更好回应</p>
                <div class="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                  <div
                    v-for="variant in responseVariants(resource).slice(0, 4)"
                    :key="`${resource.id}-variant-${variant.label}`"
                    class="rounded border border-emerald-100 bg-emerald-50 p-2 text-emerald-900 dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:text-emerald-100"
                  >
                    <p class="text-[11px] font-semibold">{{ variant.label }}</p>
                    <p class="mt-1">{{ variant.response }}</p>
                    <p v-if="variant.why_it_works" class="mt-2 text-[11px] leading-5 opacity-80">
                      {{ variant.why_it_works }}
                    </p>
                  </div>
                </div>
              </div>
              <div
                v-if="perspectiveExamples(resource).length"
                class="rounded bg-white/75 p-3 dark:bg-gray-900/60"
              >
                <p class="text-xs font-semibold text-indigo-600 dark:text-indigo-300">举一反三分析</p>
                <div class="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                  <div
                    v-for="example in perspectiveExamples(resource).slice(0, 4)"
                    :key="`${resource.id}-perspective-${example.label}`"
                    class="rounded border border-sky-100 bg-sky-50 p-2 text-sky-900 dark:border-sky-900/40 dark:bg-sky-950/20 dark:text-sky-100"
                  >
                    <p class="text-[11px] font-semibold">{{ example.label }}</p>
                    <p class="mt-1">{{ example.learning_point || example.what_to_notice || example.what_is_happening }}</p>
                    <p v-if="example.what_to_notice" class="mt-2 text-[11px] leading-5 opacity-80">
                      观察：{{ example.what_to_notice }}
                    </p>
                  </div>
                </div>
                <div v-if="transferAnalysis(resource).stable_principles.length" class="mt-3 rounded border border-indigo-100 bg-indigo-50 p-2 dark:border-indigo-900/40 dark:bg-indigo-950/30">
                  <p class="text-[11px] font-semibold text-indigo-700 dark:text-indigo-200">迁移不变原则</p>
                  <ul class="mt-1 space-y-1 text-xs leading-5">
                    <li
                      v-for="principle in transferAnalysis(resource).stable_principles.slice(0, 3)"
                      :key="`${resource.id}-principle-${principle}`"
                    >
                      - {{ principle }}
                    </li>
                  </ul>
                </div>
              </div>
              <div class="rounded bg-white/75 p-3 dark:bg-gray-900/60">
                <p class="text-xs font-semibold text-indigo-600 dark:text-indigo-300">练习与迁移</p>
                <p class="mt-1">{{ caseBlueprint(resource).practice_task || drillList(resource).slice(0, 1).join('') || fallbackDrill(resource) }}</p>
                <p class="mt-2 text-xs opacity-80">迁移：{{ caseBlueprint(resource).transfer_scene || '换到一个相邻真实场景，再写一次，不背同一句。' }}</p>
              </div>
            </div>
          </section>

          <div
            v-if="resource.source_summary || resource.source_excerpt"
            class="mb-3 rounded-lg border border-sky-100 bg-sky-50 p-3 text-sm leading-6 text-sky-800 dark:border-sky-900/40 dark:bg-sky-900/20 dark:text-sky-200"
          >
            <p v-if="resource.source_title" class="mb-1 font-semibold">{{ resource.source_title }}</p>
            <p v-if="resource.source_summary">{{ resource.source_summary }}</p>
            <p v-if="resource.source_excerpt" class="mt-2 text-xs text-sky-700 dark:text-sky-300">导读片段：{{ resource.source_excerpt }}</p>
          </div>
          <div v-if="resource.usage_tip" class="mb-3 p-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/20 text-sm leading-6 text-yellow-700 dark:text-yellow-300">
            <span class="font-semibold">使用提示：</span>{{ resource.usage_tip }}
          </div>
          <div class="mb-3 rounded-lg border border-emerald-100 bg-emerald-50/70 p-3 text-sm leading-6 text-emerald-900 dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:text-emerald-100">
            <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
              <p class="font-semibold">原则与练法</p>
              <span class="rounded bg-white px-2 py-1 text-xs font-semibold text-emerald-700 dark:bg-gray-900 dark:text-emerald-200">{{ sourceBoundaryLabel(resource) }}</span>
            </div>
            <div class="grid grid-cols-1 gap-2">
              <div class="rounded bg-white/70 p-2 dark:bg-gray-900/60">
                <p class="text-xs font-semibold text-emerald-700 dark:text-emerald-300">核心原则</p>
                <p class="mt-1 text-xs leading-5">{{ learningPrinciple(resource) }}</p>
              </div>
              <div class="rounded bg-white/70 p-2 dark:bg-gray-900/60">
                <p class="text-xs font-semibold text-emerald-700 dark:text-emerald-300">实践方法</p>
                <p class="mt-1 text-xs leading-5">{{ learningMethod(resource) }}</p>
              </div>
            </div>
          </div>
          <div
            v-if="resource.expression_goal || resource.expression_tool_ids_json"
            class="mb-3 rounded-lg border border-indigo-100 bg-indigo-50 p-3 text-sm leading-6 text-indigo-800 dark:border-indigo-900/40 dark:bg-indigo-900/20 dark:text-indigo-200"
          >
            <div class="mb-2 flex flex-wrap items-center gap-2">
              <span v-if="resource.expression_goal" class="rounded bg-white px-2 py-1 text-xs font-semibold text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-200">
                目标：{{ resource.expression_goal }}
              </span>
              <span v-if="resource.expression_level" class="rounded bg-white px-2 py-1 text-xs font-semibold text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-200">
                {{ resource.expression_level }}
              </span>
              <span v-if="resource.speech_act" class="rounded bg-white px-2 py-1 text-xs font-semibold text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-200">
                {{ resource.speech_act }}
              </span>
            </div>
            <p v-if="expressionToolIds(resource).length" class="break-words text-xs">
              推荐工具：
              <RouterLink
                v-for="toolId in expressionToolIds(resource)"
                :key="`${resource.id}-${toolId}`"
                :to="{ path: '/expression', query: { q: toolId } }"
                class="mr-2 font-semibold underline-offset-2 hover:underline"
              >
                {{ expressionToolDisplayName(toolId) }}
              </RouterLink>
            </p>
            <p v-if="resource.mistake_pattern" class="mt-1 text-xs">常见错题：{{ resource.mistake_pattern }}</p>
          </div>
          <div class="mt-auto grid grid-cols-1 gap-2 border-t border-gray-100 pt-3 text-xs text-gray-500 dark:border-gray-700 dark:text-gray-400 sm:grid-cols-2">
            <span v-if="resource.effectiveness_rating">
              效果: {{ resource.effectiveness_rating }}/10
            </span>
            <span v-if="resource.emotional_intensity">情绪强度: {{ resource.emotional_intensity }}/10</span>
            <span v-if="resource.attachment_suitability">依恋适配: {{ resource.attachment_suitability }}</span>
            <span v-if="resource.gender_target">目标: {{ resource.gender_target }}</span>
            <span v-if="resource.quality_score">质量分: {{ resource.quality_score }}</span>
            <span v-if="resource.source_license" class="break-words">许可: {{ resource.source_license }}</span>
            <span v-if="resource.source" class="break-words sm:col-span-2">来源: {{ resource.source }}</span>
            <a
              v-if="isHttpUrl(resource.source_url)"
              :href="resource.source_url"
              target="_blank"
              rel="noopener noreferrer"
              class="break-words text-sky-600 underline-offset-2 hover:underline dark:text-sky-300 sm:col-span-2"
            >
              信息源链接: {{ resource.source_url }}
            </a>
            <span v-if="resource.tags" class="break-words sm:col-span-2">标签: {{ resource.tags }}</span>
          </div>
          <div class="mt-4 flex flex-wrap gap-2 border-t border-gray-100 pt-3 dark:border-gray-700">
            <RouterLink :to="{ name: 'ResourceDetail', params: { id: resource.id } }" class="btn-secondary text-xs">
              查看完整详情
            </RouterLink>
            <RouterLink :to="{ path: '/trainer', query: { resource_id: resource.id, q: resource.title || resource.category } }" class="btn-primary text-xs">
              加入训练
            </RouterLink>
            <RouterLink :to="{ path: '/mistakes', query: { resource_id: resource.id, q: resource.mistake_pattern || resource.expression_goal || resource.title } }" class="btn-secondary text-xs">
              错题改写
            </RouterLink>
          </div>
        </article>
      </div>

      <PageTocSidebar v-model:collapsed="tocCollapsed" title="本页目录" :items="tocItems" />
    </div>

    <div
      v-if="!store.loading && store.totalPages > 1"
      class="mt-8 flex flex-col gap-3 rounded-lg bg-white p-4 shadow-sm dark:bg-gray-800 sm:flex-row sm:items-center sm:justify-between"
    >
      <div class="text-sm text-gray-500 dark:text-gray-400">
        当前第 {{ store.currentPage }} 页，显示 {{ store.pageStart }}-{{ store.pageEnd }} / {{ store.total }} 条
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <button class="btn-secondary" :disabled="store.currentPage <= 1" @click="goToPage(1)">首页</button>
        <button class="btn-secondary" :disabled="store.currentPage <= 1" @click="goToPage(store.currentPage - 1)">上一页</button>
        <button
          v-for="page in visiblePages"
          :key="page"
          class="rounded-md px-3 py-2 text-sm font-medium transition-colors"
          :class="page === store.currentPage ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'"
          @click="goToPage(page)"
        >
          {{ page }}
        </button>
        <button class="btn-secondary" :disabled="store.currentPage >= store.totalPages" @click="goToPage(store.currentPage + 1)">下一页</button>
        <button class="btn-secondary" :disabled="store.currentPage >= store.totalPages" @click="goToPage(store.totalPages)">末页</button>
        <form class="flex items-center gap-2" @submit.prevent="jumpToPage">
          <input v-model.number="jumpPage" class="input-mac w-24" min="1" :max="store.totalPages" type="number" />
          <button class="btn-secondary" type="submit">跳页</button>
        </form>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!store.loading && store.filteredItems.length === 0" class="card text-center py-12 text-gray-400">
      <p class="text-4xl mb-4">📭</p>
      <p>暂无匹配的资源，试试调整筛选条件</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, onBeforeUnmount, onMounted, ref, watch, type PropType } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import ModuleTabs from '@/components/ModuleTabs.vue'
import PageTocSidebar from '@/components/PageTocSidebar.vue'
import { useResourcesStore } from '@/stores/resources'
import { useToast } from '@/utils/toast'

interface TocItem {
  id: string
  anchor: string
  title: string
  indexLabel?: string
}

interface FilterOption {
  value: string
  label: string
  count?: number
}

interface ExpressionToolOption {
  id: string
  name: string
  count?: number
}

const store = useResourcesStore()
const toast = useToast()
const route = useRoute()
const router = useRouter()
const jumpPage = ref(1)
const applyingRoute = ref(false)
const tocCollapsed = ref(false)
const activeTab = ref('case_matrix')
let lastVisibleRefreshAt = 0

const resourceTabs = [
  { id: 'case_matrix', label: '案例矩阵', summary: '按主线、场景、能力点和难度浏览完整案例。' },
  { id: 'source_boundary', label: '来源边界', summary: '查看来源链接、许可、健康状态和本地原创改写边界。' },
]

const missionAxes = [
  { value: 'micro_signal', label: '微关系信号' },
  { value: 'emotion_flow', label: '情绪流动' },
  { value: 'boundary_consent', label: '边界同意' },
  { value: 'flirty_tension', label: '暧昧张力' },
  { value: 'conflict_repair', label: '冲突修复' },
  { value: 'long_connection', label: '长期连接' },
  { value: 'humor_interaction', label: '幽默互动' },
  { value: 'self_disclosure_depth', label: '自我表露深度' },
  { value: 'relationship_need_calibration', label: '关系需求校准' },
  { value: 'mistake_rewrite', label: '错题改写' },
]

const typeMap: Record<string, string> = {
  joke: '段子',
  flirty: '话术',
  story: '故事',
  riddle: '急转弯',
  game: '游戏',
  media: '媒体',
  phrase: '短句',
}

const defaultTypes = Object.keys(typeMap).map((value) => ({ value, label: typeMap[value] }))
const defaultCategories = ['深度聊天话题库', '情绪流动故事库', '从之前到之后对话诊断库', '公开来源情绪流', '冲突修复', '幽默互动', '边界与同意', '暧昧张力'].map(toOption)
const defaultScenes = ['初识', '暧昧', '热恋', '冲突', '修复', '长期', '分歧', '公开场合', '亲密推进', '价值观分歧', '压力支持', '失望表达', '约会邀约', '边界确认'].map(toOption)
const defaultTags = ['具体案例', '非模板化训练', '低压幽默', '边界与同意', '情绪流动', '冲突修复', '暧昧张力', '错题改写', '长期连接', '可拒绝出口'].map(toOption)
const defaultSources = ['local_anchor:深度聊天话题库', 'local_anchor:情绪流动故事库', 'synthetic://relationship-training/deep-conversation-topics', 'project_original', 'Gottman', 'CNVC', 'APA Relationships'].map(toOption)
const defaultExpressionGoals = ['说清事实', '命名感受', '确认边界', '降低防御', '提出请求', '修复信任', '引导深聊', '保留退路', '打开低压入口'].map(toOption)
const defaultKeywords = ['边界', '冷战', '复联', '可拒绝出口', '失望修复', '低压幽默', '情绪标注', '暧昧', '承认影响', '具体补偿'].map(toOption)
const defaultExpressionTools = [
  { id: 'expr_tool_015', name: '情绪标注' },
  { id: 'expr_tool_016', name: '幽默自嘲' },
  { id: 'expr_tool_027', name: '请求结构' },
  { id: 'expr_tool_041', name: '情绪标注' },
  { id: 'expr_tool_054', name: '自我揭露' },
  { id: 'expr_tool_019', name: '留白沉默' },
]

const typeOptions = computed(() => mergeOptions(store.filterOptions?.types, defaultTypes, store.filterOptions === null))
const keywordOptions = computed(() => mergeOptions(store.filterOptions?.keywords, defaultKeywords, store.filterOptions === null))
const categoryOptions = computed(() => mergeOptions(store.filterOptions?.categories, defaultCategories, store.filterOptions === null))
const sceneOptions = computed(() => mergeOptions(store.filterOptions?.scenes, defaultScenes, store.filterOptions === null))
const tagOptions = computed(() => mergeOptions(store.filterOptions?.tags, defaultTags, store.filterOptions === null))
const sourceOptions = computed(() => mergeOptions(store.filterOptions?.sources, defaultSources, store.filterOptions === null))
const expressionGoalOptions = computed(() => mergeOptions(store.filterOptions?.expression_goals, defaultExpressionGoals, store.filterOptions === null))
const expressionToolOptions = computed(() => mergeExpressionToolOptions(store.filterOptions?.expression_tools, defaultExpressionTools, store.filterOptions === null))
const expressionToolNameById = computed(() => {
  const pairs = expressionToolOptions.value.map((option) => [option.id, option.name] as const)
  return new Map(pairs)
})

function typeLabel(type: string) {
  return typeMap[type] ?? type
}

function toOption(value: string): FilterOption {
  return { value, label: value }
}

function mergeOptions(primary: FilterOption[] | undefined, fallback: FilterOption[], includeFallback: boolean) {
  const seen = new Set<string>()
  return [...(primary || []), ...(includeFallback ? fallback : [])].filter((option) => {
    const value = String(option.value || '').trim()
    if (!value || seen.has(value)) return false
    seen.add(value)
    return true
  })
}

function mergeExpressionToolOptions(primary: ExpressionToolOption[] | undefined, fallback: ExpressionToolOption[], includeFallback: boolean) {
  const seen = new Set<string>()
  return [...(primary || []), ...(includeFallback ? fallback : [])].filter((option) => {
    const id = String(option.id || '').trim()
    if (!id || seen.has(id)) return false
    seen.add(id)
    return true
  })
}

function optionLabel(option: FilterOption, label = option.label || option.value) {
  return typeof option.count === 'number' ? `${label} · ${option.count}` : label
}

function typeOptionLabel(option: FilterOption) {
  return typeLabel(option.value)
}

async function selectFilterValue(kind: 'type' | 'scene' | 'tag' | 'source' | 'goal', value: string) {
  if (kind === 'type') store.selectedType = store.selectedType === value ? '' : value
  if (kind === 'scene') store.selectedScene = store.selectedScene === value ? '' : value
  if (kind === 'tag') store.selectedTag = store.selectedTag === value ? '' : value
  if (kind === 'source') store.selectedSource = store.selectedSource === value ? '' : value
  if (kind === 'goal') store.selectedExpressionGoal = store.selectedExpressionGoal === value ? '' : value
  await applyFilters()
}

async function selectExpressionToolQuick(option: ExpressionToolOption) {
  store.selectedExpressionTool = store.selectedExpressionTool === option.id ? '' : option.id
  await applyFilters()
}

function expressionToolLabel(option: ExpressionToolOption, mode: 'id' | 'name') {
  const label = mode === 'id' ? option.id : option.name
  return typeof option.count === 'number' ? `${label} · ${option.count}` : label
}

const FilterCountGroup = defineComponent({
  props: {
    title: { type: String, required: true },
    items: { type: Array as PropType<FilterOption[]>, required: true },
    labeler: { type: Function as PropType<(option: FilterOption) => string>, default: null },
  },
  emits: ['select'],
  setup(props, { emit }) {
    return () => h('div', [
      h('p', { class: 'mb-2 text-xs font-semibold text-gray-600 dark:text-gray-300' }, props.title),
      h('div', { class: 'flex flex-wrap gap-2' }, props.items.map((option) => h(
        'button',
        {
          key: `${props.title}-${option.value}`,
          type: 'button',
          class: 'rounded-full bg-white px-3 py-1.5 text-xs text-gray-700 shadow-sm transition-colors hover:bg-indigo-50 hover:text-indigo-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-indigo-950/40 dark:hover:text-indigo-200',
          onClick: () => emit('select', option.value),
        },
        `${props.labeler ? props.labeler(option) : option.label || option.value} · ${option.count ?? 0}`,
      ))),
    ])
  },
})

function expressionToolDisplayName(toolId: string) {
  return expressionToolNameById.value.get(toolId) || toolId
}

function isHttpUrl(url?: string) {
  return Boolean(url && /^https?:\/\//i.test(url))
}

function expressionToolIds(resource: { expression_tool_ids_json?: string }) {
  if (!resource.expression_tool_ids_json) return []
  try {
    const value = JSON.parse(resource.expression_tool_ids_json)
    return Array.isArray(value) ? value.map(String).slice(0, 4) : []
  } catch {
    return []
  }
}

function parseJsonObject(raw?: string) {
  if (!raw) return {}
  try {
    const value = JSON.parse(raw)
    return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}
  } catch {
    return {}
  }
}

function stringField(source: Record<string, unknown>, key: string) {
  const value = source[key]
  return typeof value === 'string' || typeof value === 'number' ? String(value) : ''
}

function stringList(source: Record<string, unknown>, key: string) {
  const value = source[key]
  return Array.isArray(value) ? value.map(String).filter(Boolean) : []
}

function objectList(source: Record<string, unknown>, key: string) {
  const value = source[key]
  return Array.isArray(value)
    ? value
        .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object' && !Array.isArray(item))
        .map((item) => Object.fromEntries(Object.entries(item).map(([entryKey, entryValue]) => [entryKey, String(entryValue ?? '')])))
    : []
}

function objectField(source: Record<string, unknown>, key: string) {
  const value = source[key]
  return value && typeof value === 'object' && !Array.isArray(value) ? value as Record<string, unknown> : {}
}

function caseBlueprint(resource: { case_blueprint_json?: string; content?: string; applicable_scene?: string; category?: string; expression_goal?: string }) {
  const parsed = parseJsonObject(resource.case_blueprint_json)
  return {
    axis_label: stringField(parsed, 'axis_label'),
    relation_stage: stringField(parsed, 'relation_stage') || resource.applicable_scene || resource.category || '',
    trigger: stringField(parsed, 'trigger'),
    setting: stringField(parsed, 'setting') || fieldFromContent(resource, '场景'),
    their_words: stringField(parsed, 'their_words') || fieldFromContent(resource, 'TA说'),
    surface_signal: stringField(parsed, 'surface_signal') || fieldFromContent(resource, '表层信号') || fieldFromContent(resource, '情绪信号'),
    deeper_need: stringField(parsed, 'deeper_need') || fieldFromContent(resource, '深层可能') || resource.expression_goal || '',
    common_mistake: stringField(parsed, 'common_mistake') || fieldFromContent(resource, '常见失误') || fieldFromContent(resource, '低质量回应'),
    why_wrong: stringField(parsed, 'why_wrong') || fieldFromContent(resource, '为什么错'),
    better_response: stringField(parsed, 'better_response') || fieldFromContent(resource, '更好回应') || fieldFromContent(resource, '高质量回应'),
    boundary_note: stringField(parsed, 'boundary_note') || fieldFromContent(resource, '边界提醒') || fieldFromContent(resource, '边界与同意'),
    de_bias_note: stringField(parsed, 'de_bias_note') || fieldFromContent(resource, '去偏提醒'),
    practice_task: stringField(parsed, 'practice_task') || fieldFromContent(resource, '练习任务'),
    transfer_scene: stringField(parsed, 'transfer_scene') || fieldFromContent(resource, '迁移场景'),
    response_steps: stringList(parsed, 'response_steps'),
    variant_deltas: stringList(parsed, 'variant_deltas'),
    dialogue_script: objectList(parsed, 'dialogue_script'),
    response_variants: objectList(parsed, 'response_variants'),
    perspective_examples: objectList(parsed, 'perspective_examples'),
    transfer_analysis: objectField(parsed, 'transfer_analysis'),
  }
}

function dialogueScript(resource: { case_blueprint_json?: string; content?: string; applicable_scene?: string; category?: string; expression_goal?: string }) {
  return caseBlueprint(resource).dialogue_script
}

function dialogueTurnClass(speaker: string) {
  if (speaker.includes('低质量')) return 'border-red-100 bg-red-50 text-red-800 dark:border-red-900/40 dark:bg-red-950/20 dark:text-red-200'
  if (speaker.includes('更好') || speaker.includes('继续') || speaker.includes('边界')) return 'border-emerald-100 bg-emerald-50 text-emerald-800 dark:border-emerald-900/40 dark:bg-emerald-950/20 dark:text-emerald-200'
  return 'border-gray-100 bg-gray-50 text-gray-800 dark:border-gray-800 dark:bg-gray-950/40 dark:text-gray-200'
}

function responseVariants(resource: { case_blueprint_json?: string; content?: string; applicable_scene?: string; category?: string; expression_goal?: string }) {
  return caseBlueprint(resource).response_variants
}

function perspectiveExamples(resource: { case_blueprint_json?: string; content?: string; applicable_scene?: string; category?: string; expression_goal?: string }) {
  return caseBlueprint(resource).perspective_examples
}

function transferAnalysis(resource: { case_blueprint_json?: string; content?: string; applicable_scene?: string; category?: string; expression_goal?: string }) {
  const analysis = caseBlueprint(resource).transfer_analysis
  return {
    stable_principles: stringList(analysis, 'stable_principles'),
    changeable_parameters: stringList(analysis, 'changeable_parameters'),
    self_check_questions: stringList(analysis, 'self_check_questions'),
  }
}

function caseStory(resource: { title?: string; applicable_scene?: string; category?: string; content?: string; case_blueprint_json?: string; expression_goal?: string }) {
  const blueprint = caseBlueprint(resource)
  const setting = blueprint.setting || resource.title || '一个具体关系片段'
  const signal = blueprint.surface_signal ? `表层信号是：${blueprint.surface_signal}` : '需要先观察对方的语气、停顿和上下文。'
  const need = blueprint.deeper_need ? `深层可能是：${blueprint.deeper_need}` : '深层需要暂时只当假设，不直接下结论。'
  return `${setting}${signal} ${need}`
}

function weakResponse(resource: { content?: string; case_blueprint_json?: string; applicable_scene?: string; category?: string; expression_goal?: string }) {
  const mistake = caseBlueprint(resource).common_mistake || caseComparison(resource).bad
  if (!mistake) return '只给评价、建议或玩笑，没有接住对方正在表达的感受。'
  const match = mistake.match(/旧回应通常会说[：:](.+)$/)
  return match?.[1]?.trim() || mistake
}

function betterResponse(resource: { content?: string; case_blueprint_json?: string; applicable_scene?: string; category?: string; expression_goal?: string }) {
  return caseBlueprint(resource).better_response || caseComparison(resource).good || '先承接一个情绪点，再给对方可拒绝、可晚点说的空间。'
}

function caseResponseSteps(resource: { case_blueprint_json?: string; content?: string; applicable_scene?: string; category?: string; expression_goal?: string }) {
  const steps = caseBlueprint(resource).response_steps
  if (steps.length) return steps
  return ['先复述可观察事实', '命名一个可能感受', '补一个边界出口', '只问一个开放问题']
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

function learningPrinciple(resource: {
  expression_goal?: string
  mistake_pattern?: string
  applicable_scene?: string
  category?: string
}) {
  if (resource.mistake_pattern) return `先识别常见错题“${resource.mistake_pattern}”，再把回应改成事实清楚、情绪可承接、边界可退出的表达。`
  if ((resource.expression_goal || '').includes('修复')) return '修复类资源遵循“承认影响、减少辩解、给出可靠下一步”，不能逼对方立刻原谅。'
  if ((resource.category || resource.applicable_scene || '').includes('边界')) return '边界类资源的底线是清晰同意、可拒绝出口和不替对方做决定。'
  return '先看见具体情境，再选择表达动作；不把技巧用于操控、施压或制造不安全感。'
}

function learningMethod(resource: { content?: string; usage_tip?: string; speech_act?: string; expression_level?: string }) {
  const scene = fieldFromContent(resource, '场景')
  const theirWords = fieldFromContent(resource, 'TA说')
  if (scene && theirWords) return `先读场景和原话，标出情绪信号，再按“${resource.speech_act || '事实-感受-边界-下一步'}”改写。`
  return resource.usage_tip || `按${resource.expression_level || '当前难度'}做一轮：读内容、找信号、写旧回应、改成更好回应。`
}

function fallbackDrill(resource: { expression_goal?: string; applicable_scene?: string }) {
  return `围绕“${resource.applicable_scene || resource.expression_goal || '当前场景'}”写一句低质量回应，再改写成包含退路的新回应。`
}

function caseComparison(resource: { content?: string }) {
  return {
    bad: fieldFromContent(resource, '常见失误') || fieldFromContent(resource, '低质量回应'),
    good: fieldFromContent(resource, '更好回应') || fieldFromContent(resource, '高质量回应'),
  }
}

function sourceBoundaryLabel(resource: { source?: string; source_url?: string }) {
  if (isHttpUrl(resource.source_url)) return '有原文入口'
  const source = resource.source || ''
  if (source.startsWith('project_original') || source.startsWith('local_anchor') || source.startsWith('synthetic')) return '项目原创训练卡'
  return '结构化导读卡'
}

function resourceAnchor(resource: { id: number }) {
  return `resource-${resource.id}`
}

const tocItems = computed<TocItem[]>(() => (
  store.filteredItems.map((resource, index) => ({
    id: `resource-${resource.id}`,
    anchor: resourceAnchor(resource),
    indexLabel: String(index + store.pageStart),
    title: resource.title || '无标题',
  }))
))

const visiblePages = computed(() => {
  const pages: number[] = []
  const start = Math.max(1, store.currentPage - 2)
  const end = Math.min(store.totalPages, store.currentPage + 2)
  for (let page = start; page <= end; page += 1) pages.push(page)
  return pages
})

async function randomOne() {
  try {
    const resource = await store.fetchRandom(store.selectedType || undefined)
    if (resource) {
      toast.success(`${typeLabel(resource.type)}: ${resource.title || ''}\n\n${resource.content}`)
    }
  } catch {
    toast.error('获取随机资源失败')
  }
}

function jumpToPage() {
  goToPage(Number(jumpPage.value) || 1)
}

async function selectMissionAxis(axis: string) {
  store.selectedMissionAxis = store.selectedMissionAxis === axis ? '' : axis
  await applyFilters()
}

async function clearFilters() {
  store.searchQuery = ''
  store.selectedType = ''
  store.selectedCategory = ''
  store.selectedScene = ''
  store.selectedTag = ''
  store.selectedSource = ''
  store.selectedExpressionTool = ''
  store.selectedExpressionGoal = ''
  store.selectedMissionAxis = ''
  await applyFilters()
}

async function applyFilters() {
  await store.resetAndFetch()
  syncQueryToUrl()
}

async function goToPage(page: number) {
  await store.goToPage(page)
  jumpPage.value = store.currentPage
  syncQueryToUrl()
}

function normalizeTab(value: unknown) {
  const tab = typeof value === 'string' ? value : ''
  return resourceTabs.some((item) => item.id === tab) ? tab : 'case_matrix'
}

function onTabChange(value: string) {
  activeTab.value = normalizeTab(value)
  syncQueryToUrl()
}

function syncQueryToUrl() {
  if (applyingRoute.value) return
  const query: Record<string, string> = {}
  if (activeTab.value !== 'case_matrix') query.tab = activeTab.value
  if (store.searchQuery) query.q = store.searchQuery
  if (store.selectedType) query.type = store.selectedType
  if (store.selectedCategory) query.category = store.selectedCategory
  if (store.selectedScene) query.scene = store.selectedScene
  if (store.selectedTag) query.tag = store.selectedTag
  if (store.selectedSource) query.source = store.selectedSource
  if (store.selectedMissionAxis) query.mission_axis = store.selectedMissionAxis
  if (store.selectedExpressionTool) query.expression_tool = store.selectedExpressionTool
  if (store.selectedExpressionGoal) query.expression_goal = store.selectedExpressionGoal
  if (store.currentPage > 1) query.page = String(store.currentPage)
  router.replace({ path: '/resources', query })
}

onMounted(() => {
  applyingRoute.value = true
  const routeQuery = route.query
  activeTab.value = normalizeTab(routeQuery.tab)
  applyRouteFilters(routeQuery)
  const pageFromRoute = Number(routeQuery.page)
  store.currentPage = Number.isFinite(pageFromRoute) && pageFromRoute > 0 ? pageFromRoute : 1
  jumpPage.value = store.currentPage
  applyingRoute.value = false
  store.fetchFilterOptions().then(() => store.fetchResources())
  document.addEventListener('visibilitychange', refreshWhenVisible)
})

onBeforeUnmount(() => {
  document.removeEventListener('visibilitychange', refreshWhenVisible)
})

function refreshWhenVisible() {
  if (document.visibilityState !== 'visible') return
  const now = Date.now()
  if (now - lastVisibleRefreshAt < 3000) return
  lastVisibleRefreshAt = now
  store.fetchResources()
}

watch(
  () => route.query,
  async (query) => {
    if (route.path !== '/resources') return
    applyingRoute.value = true
    activeTab.value = normalizeTab(query.tab)
    applyRouteFilters(query)
    const page = Number(query.page)
    store.currentPage = Number.isFinite(page) && page > 0 ? page : 1
    jumpPage.value = store.currentPage
    applyingRoute.value = false
    await store.fetchResources()
  }
)

function applyRouteFilters(query: typeof route.query) {
  store.searchQuery = typeof query.q === 'string' ? query.q : ''
  store.selectedSource = typeof query.source === 'string' ? query.source : ''
  store.selectedTag = typeof query.tag === 'string' ? query.tag : ''
  store.selectedMissionAxis = typeof query.mission_axis === 'string' ? query.mission_axis : ''
  store.selectedExpressionTool = typeof query.expression_tool === 'string' ? query.expression_tool : ''
  store.selectedExpressionGoal = typeof query.expression_goal === 'string' ? query.expression_goal : ''
  store.selectedType = typeof query.type === 'string' ? query.type : ''
  store.selectedCategory = typeof query.category === 'string' ? query.category : ''
  store.selectedScene = typeof query.scene === 'string' ? query.scene : ''
}
</script>
