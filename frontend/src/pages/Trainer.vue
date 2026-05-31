<template>
  <div class="p-4 sm:p-6 lg:p-8">
    <div class="mb-8 flex flex-col items-start justify-between gap-4 sm:flex-row sm:gap-6">
      <div>
        <p class="text-sm font-semibold text-blue-500 mb-2">Deliberate Practice / 刻意练习</p>
        <h1 class="text-3xl font-bold text-gray-800 dark:text-white">训练中心</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-2">下一题推荐、七维评分、错题沉淀，构成真实训练闭环。</p>
      </div>
      <button @click="loadNext()" class="btn-secondary w-full sm:w-auto" :disabled="loading">{{ loading ? '加载中...' : '换一题' }}</button>
    </div>

    <div
      v-if="loadError"
      class="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300"
    >
      <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p>{{ loadError }}</p>
        <button class="rounded-lg bg-red-500 px-3 py-2 text-white hover:bg-red-600" @click="loadNext()">
          重新加载题目
        </button>
      </div>
    </div>

    <ModuleTabs
      v-model="activeTab"
      :tabs="trainerTabs"
      label="训练中心选项卡"
      id-prefix="trainer-tab"
      class="mb-6"
      @update:model-value="onTabChange"
    />

    <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
      <section class="xl:col-span-2 space-y-6">
        <template v-if="activeTab === 'current_question'">
        <div
          v-if="resourceContext"
          class="card border border-sky-100 bg-sky-50/70 dark:border-sky-900/50 dark:bg-sky-950/20"
        >
          <div class="mb-4 flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
            <div class="min-w-0">
              <p class="text-sm font-semibold text-sky-700 dark:text-sky-300">来自资源海洋的训练上下文</p>
              <h2 class="mt-1 break-words text-xl font-bold text-gray-800 dark:text-white">{{ resourceContext.title || '未命名资源' }}</h2>
              <p class="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">{{ resourcePracticePrompt }}</p>
            </div>
            <RouterLink
              :to="{ name: 'ResourceDetail', params: { id: resourceContext.id } }"
              class="shrink-0 rounded-lg bg-white px-3 py-2 text-sm font-semibold text-sky-700 shadow-sm hover:bg-sky-100 dark:bg-gray-900 dark:text-sky-300 dark:hover:bg-sky-950/60"
            >
              回看资源
            </RouterLink>
          </div>
          <div class="grid grid-cols-1 gap-3 lg:grid-cols-3">
            <div class="rounded-lg bg-white p-3 text-sm dark:bg-gray-900">
              <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">场景 / 分类</p>
              <p class="mt-1 text-gray-800 dark:text-gray-100">{{ resourceContext.applicable_scene || resourceContext.category }}</p>
            </div>
            <div class="rounded-lg bg-white p-3 text-sm dark:bg-gray-900">
              <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">表达目标</p>
              <p class="mt-1 text-gray-800 dark:text-gray-100">{{ resourceContext.expression_goal || '先接住情绪，再给退路' }}</p>
            </div>
            <div class="rounded-lg bg-white p-3 text-sm dark:bg-gray-900">
              <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">质量 / 难度</p>
              <p class="mt-1 text-gray-800 dark:text-gray-100">Q{{ resourceContext.quality_score || '-' }} · D{{ resourceContext.difficulty_level || '-' }}</p>
            </div>
          </div>
          <div class="mt-4 flex flex-wrap gap-2">
            <button class="btn-primary text-xs" type="button" @click="prefillFromResource">
              用资源提示预填回应
            </button>
            <button class="btn-secondary text-xs" type="button" @click="clearResourceContext">
              只做普通训练
            </button>
          </div>
        </div>

        <EmptyState
          v-if="!loading && !nextItem && loadError"
          type="error"
          title="训练题加载失败"
          description="下一题推荐暂时不可用，请重试；已经完成的训练记录不会丢失。"
          action-text="重新加载题目"
          @action="loadNext"
        />
        <div v-if="nextItem" class="card border border-blue-100 dark:border-blue-900/40">
          <div class="flex flex-wrap items-center gap-2 mb-4">
            <span class="px-2 py-1 rounded text-xs bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">{{ nextItem.type === 'review' ? '到期复习' : '智能推荐' }}</span>
            <span class="text-sm text-gray-500 dark:text-gray-400">{{ nextItem.reason }}</span>
          </div>

          <div v-if="sample" class="space-y-4">
            <div class="p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
              <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">场景</p>
              <p class="text-gray-800 dark:text-white">{{ sample.context }}</p>
            </div>
            <div class="p-4 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
              <p class="text-xs text-blue-600 dark:text-blue-400 mb-1">TA 说</p>
              <p class="text-xl text-gray-800 dark:text-white">{{ sample.their_words }}</p>
              <p v-if="sample.their_behavior" class="text-sm text-gray-500 dark:text-gray-400 mt-2">行为：{{ sample.their_behavior }}</p>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div class="p-3 rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700"><p class="text-gray-400">阶段</p><p class="font-medium text-gray-800 dark:text-white">{{ sample.scenario_category }}</p></div>
              <div class="p-3 rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700"><p class="text-gray-400">难度</p><p class="font-medium text-gray-800 dark:text-white">{{ sample.difficulty_level }}</p></div>
              <div class="p-3 rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700"><p class="text-gray-400">依恋信号</p><p class="font-medium text-gray-800 dark:text-white">{{ sample.attachment_signal || '待判断' }}</p></div>
              <div class="p-3 rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700"><p class="text-gray-400">边界等级</p><p class="font-medium text-gray-800 dark:text-white">{{ sample.boundary_test_level || '-' }}</p></div>
            </div>

            <div v-if="visualMap" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div class="p-4 rounded-xl border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800">
                <div class="flex items-center justify-between mb-3">
                  <div>
                    <p class="text-xs text-gray-400">Emotion Thermometer / 情绪温度计</p>
                    <h3 class="font-semibold text-gray-800 dark:text-white">{{ visualMap.emotion_thermometer.word }} · {{ visualMap.emotion_thermometer.zone }}</h3>
                  </div>
                  <span class="text-2xl font-bold text-blue-500">{{ visualMap.emotion_thermometer.average_intensity }}/10</span>
                </div>
                <div class="h-3 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
                  <div class="h-full rounded-full bg-gradient-to-r from-emerald-400 via-amber-400 to-red-500" :style="{ width: visualMap.emotion_thermometer.percent + '%' }"></div>
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-3">{{ visualMap.emotion_thermometer.principle }}</p>
              </div>

              <div class="p-4 rounded-xl border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800">
                <p class="text-xs text-gray-400 mb-3">Boundary Band / 边界色带</p>
                <div class="relative h-8 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700">
                  <div class="absolute inset-y-0 left-0 bg-emerald-400" style="width: 30%"></div>
                  <div class="absolute inset-y-0 left-[30%] bg-amber-400" style="width: 30%"></div>
                  <div class="absolute inset-y-0 left-[60%] bg-orange-500" style="width: 20%"></div>
                  <div class="absolute inset-y-0 left-[80%] bg-red-500" style="width: 20%"></div>
                  <div class="absolute top-0 h-8 w-1.5 bg-gray-950 dark:bg-white rounded" :style="boundaryMarkerStyle"></div>
                </div>
                <div class="flex justify-between text-[11px] text-gray-400 mt-1">
                  <span>开放</span><span>试探</span><span>高压</span><span>暂停</span>
                </div>
                <p class="text-sm font-medium mt-3" :class="boundaryZoneClass">{{ visualMap.boundary_band.label }} · {{ visualMap.boundary_band.level }}/10</p>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ visualMap.boundary_band.principle }}</p>
              </div>
            </div>

            <div v-if="visualMap" class="p-4 rounded-xl border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800">
              <div class="flex items-center justify-between mb-4">
                <div>
                  <p class="text-xs text-gray-400">Signal Map / 信号假设</p>
                  <h3 class="font-semibold text-gray-800 dark:text-white">从线索到轻验证</h3>
                </div>
                <span class="text-xs text-gray-400">假设，不是结论</span>
              </div>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div v-for="signal in visualMap.signal_highlights" :key="signal.label + signal.text" class="p-3 rounded-lg border border-gray-100 dark:border-gray-700">
                  <div class="flex items-center justify-between gap-2">
                    <span class="text-xs font-semibold" :class="signalToneClass(signal.type)">{{ signal.label }}</span>
                    <span class="text-xs text-gray-400">{{ Math.round(signal.weight * 100) }}%</span>
                  </div>
                  <p class="text-sm text-gray-800 dark:text-white mt-2">{{ signal.text }}</p>
                  <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">{{ signal.hypothesis }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-4">
            <h2 class="text-xl font-bold text-gray-800 dark:text-white">你的回应</h2>
            <div class="flex flex-wrap gap-2">
              <button v-for="type in responseTypes" :key="type.value" @click="responseType = type.value" class="px-3 py-1.5 rounded-lg text-sm" :class="responseType === type.value ? 'bg-blue-500 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'">{{ type.label }}</button>
            </div>
          </div>
          <textarea v-model="userResponse" class="input-mac min-h-[140px]" placeholder="先接住情绪，再回应需求。写下你会怎么说..."></textarea>
          <div
            v-if="submitError"
            class="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300"
          >
            {{ submitError }}
          </div>
          <button @click="submit" class="btn-primary w-full mt-4" :disabled="!userResponse.trim() || submitting || !sample">{{ submitting ? '评分中...' : '提交并生成七维反馈' }}</button>
        </div>
        </template>

        <div v-if="activeTab === 'feedback' && !comparison" class="card text-center py-16 text-gray-500">
          <p class="text-4xl mb-4">↳</p>
          <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-2">提交作答后生成七维反馈</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">反馈会包含分数、差异、表达工具适配、元认知复盘和下一步最小行动。</p>
          <button class="btn-secondary mt-4" type="button" @click="onTabChange('current_question')">回到当前题</button>
        </div>

        <div v-if="activeTab === 'feedback' && comparison" class="card">
          <div class="flex items-center justify-between mb-6">
            <div>
              <p class="text-sm text-gray-500 dark:text-gray-400">综合得分</p>
              <p class="text-5xl font-bold" :class="scoreClass">{{ Math.round(comparison.score) }}</p>
              <p class="text-xs text-gray-400 mt-2">评分来源：{{ scoringSourceLabel }}</p>
            </div>
            <div v-if="comparison.mistake_id" class="px-3 py-2 rounded-xl bg-orange-100 text-orange-600 dark:bg-orange-900/30 dark:text-orange-400 text-sm">已进入错题本 #{{ comparison.mistake_id }}</div>
          </div>

          <div v-if="comparison.dimension_scores" class="space-y-3 mb-6">
            <div v-for="item in dimensionRows" :key="item.key" class="grid grid-cols-[88px_1fr_48px] items-center gap-3">
              <span class="text-sm text-gray-500 dark:text-gray-400">{{ item.label }}</span>
              <div class="h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden"><div class="h-full rounded-full bg-gradient-to-r from-blue-500 to-purple-500" :style="{ width: item.value + '%' }"></div></div>
              <span class="text-sm font-medium text-gray-700 dark:text-gray-200">{{ Math.round(item.value) }}</span>
            </div>
          </div>

          <div class="p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 mb-4">
            <p class="text-sm text-green-600 dark:text-green-400 mb-2">理想回应</p>
            <p class="text-gray-800 dark:text-white">{{ comparison.ideal_response }}</p>
          </div>

          <div class="space-y-2 mb-4">
            <div v-for="(diff, index) in comparison.differences" :key="index" class="p-3 rounded-xl" :class="diff.type === 'problem' ? 'bg-red-50 dark:bg-red-900/20' : 'bg-green-50 dark:bg-green-900/20'">
              <p class="font-medium" :class="diff.type === 'problem' ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'">{{ diff.type === 'problem' ? '需要修正' : '做得不错' }} · {{ diff.name }}</p>
              <p class="text-sm text-gray-600 dark:text-gray-300 mt-1">{{ diff.desc }}</p>
            </div>
          </div>

          <div v-if="comparison.next_recommendation" class="p-4 rounded-xl bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-sm">
            下一步：{{ comparison.next_recommendation }}
          </div>

          <div v-if="transitionFeedback" class="mt-4 rounded-xl border border-teal-100 bg-teal-50/70 p-4 dark:border-teal-900/50 dark:bg-teal-950/20">
            <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p class="text-xs font-semibold text-teal-600 dark:text-teal-300">Developmental Emotion Transition / 发展性情绪跃迁</p>
                <h3 class="mt-1 text-lg font-bold text-gray-800 dark:text-white">{{ transitionFeedback.transition_type }}</h3>
                <p class="mt-1 text-sm text-gray-600 dark:text-gray-300">{{ transitionFeedback.transition_goal }}</p>
              </div>
              <div class="rounded-lg bg-white px-4 py-3 text-sm shadow-sm dark:bg-gray-800">
                <p class="font-semibold text-teal-700 dark:text-teal-200">{{ transitionScaffoldLabel }}</p>
                <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ transitionPhaseLabel }}</p>
              </div>
            </div>

            <div class="grid grid-cols-1 gap-3 lg:grid-cols-3">
              <div class="rounded-lg bg-white p-3 dark:bg-gray-800">
                <p class="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-200">情绪四维</p>
                <div class="space-y-1.5 text-xs text-gray-600 dark:text-gray-300">
                  <p>强度：{{ transitionIntensityLabel }}</p>
                  <p>效价：{{ transitionValenceLabel }}</p>
                  <p>指向：{{ transitionTargetLabel }}</p>
                  <p>时序：{{ transitionPhaseLabel }}</p>
                </div>
              </div>

              <div class="rounded-lg bg-white p-3 dark:bg-gray-800">
                <p class="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-200">缺失支架</p>
                <ul class="space-y-2">
                  <li v-for="move in transitionFeedback.missing_moves" :key="move" class="text-xs leading-relaxed text-gray-600 dark:text-gray-300">{{ move }}</li>
                </ul>
                <p v-if="transitionFeedback.missing_moves.length === 0" class="text-xs text-gray-500 dark:text-gray-400">这次回应覆盖了主要跃迁支架。</p>
              </div>

              <div class="rounded-lg bg-white p-3 dark:bg-gray-800">
                <p class="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-200">下一句</p>
                <p class="text-xs leading-relaxed text-gray-600 dark:text-gray-300">{{ transitionFeedback.next_sentence }}</p>
              </div>
            </div>
            <p class="mt-3 text-xs leading-relaxed text-teal-700 dark:text-teal-200">{{ transitionFeedback.principle }}</p>
          </div>

          <div v-if="comparison.expression_tool_scoring" class="mt-4 rounded-xl border border-indigo-100 bg-indigo-50/70 p-4 dark:border-indigo-900/50 dark:bg-indigo-950/20">
            <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <p class="text-xs font-semibold text-indigo-500 dark:text-indigo-300">Expression Tool Fit / 表达工具适配</p>
                <h3 class="mt-1 text-lg font-bold text-gray-800 dark:text-white">{{ comparison.expression_tool_scoring.target_goal }} · {{ comparison.expression_tool_scoring.stage }}</h3>
                <p class="mt-1 text-sm text-gray-600 dark:text-gray-300">{{ comparison.expression_tool_scoring.principle }}</p>
              </div>
              <div class="rounded-lg bg-white px-4 py-3 text-center shadow-sm dark:bg-gray-800">
                <p class="text-2xl font-bold text-indigo-600 dark:text-indigo-300">{{ Math.round(comparison.expression_tool_scoring.fit_score) }}</p>
                <p class="text-xs text-gray-400">工具适配分</p>
              </div>
            </div>

            <div class="grid grid-cols-1 gap-3 lg:grid-cols-3">
              <div class="rounded-lg bg-white p-3 dark:bg-gray-800">
                <p class="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-200">推荐工具</p>
                <div class="space-y-2">
                  <div v-for="tool in comparison.expression_tool_scoring.recommended_tools.slice(0, 3)" :key="tool.tool_uuid" class="rounded border border-gray-100 p-2 dark:border-gray-700">
                    <p class="text-sm font-semibold text-indigo-600 dark:text-indigo-300">{{ tool.name }}</p>
                    <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">{{ tool.formula || tool.category }}</p>
                  </div>
                </div>
              </div>

              <div class="rounded-lg bg-white p-3 dark:bg-gray-800">
                <p class="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-200">缺失动作</p>
                <ul class="space-y-2">
                  <li v-for="move in comparison.expression_tool_scoring.missing_moves" :key="move" class="text-xs leading-relaxed text-gray-600 dark:text-gray-300">{{ move }}</li>
                </ul>
                <p v-if="comparison.expression_tool_scoring.missing_moves.length === 0" class="text-xs text-gray-500 dark:text-gray-400">这次回应已经覆盖主要表达动作，下一步练迁移。</p>
              </div>

              <div class="rounded-lg bg-white p-3 dark:bg-gray-800">
                <p class="mb-2 text-sm font-semibold text-gray-700 dark:text-gray-200">三步练习</p>
                <div class="space-y-2">
                  <div v-for="step in comparison.expression_tool_scoring.practice_steps" :key="step.step" class="text-xs leading-relaxed text-gray-600 dark:text-gray-300">
                    <span class="font-semibold text-indigo-600 dark:text-indigo-300">{{ step.step }}：</span>{{ step.action }}
                  </div>
                </div>
              </div>
            </div>

            <div v-if="comparison.expression_tool_scoring.risk_notes.length" class="mt-3 rounded-lg border border-amber-100 bg-amber-50 p-3 dark:border-amber-900/40 dark:bg-amber-950/20">
              <p class="mb-1 text-xs font-semibold text-amber-700 dark:text-amber-300">边界提醒</p>
              <p class="text-xs leading-relaxed text-amber-700 dark:text-amber-200">{{ comparison.expression_tool_scoring.risk_notes.join(' ') }}</p>
            </div>
          </div>

          <div v-if="comparison.metacognitive_review" class="mt-4 p-4 rounded-xl border border-blue-100 dark:border-blue-900/50 bg-blue-50/60 dark:bg-blue-900/10">
            <div class="flex items-center justify-between gap-3 mb-3">
              <div>
                <p class="text-xs text-blue-500 dark:text-blue-400">Metacognition / 元认知复盘</p>
                <h3 class="font-bold text-gray-800 dark:text-white">大胆假设，小心求证</h3>
              </div>
              <span class="text-xs text-gray-400">事实 ≠ 解释</span>
            </div>
            <p class="text-sm text-gray-600 dark:text-gray-300 mb-4">{{ comparison.metacognitive_review.principle }}</p>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div class="p-3 rounded-lg bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700">
                <p class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">可观察事实</p>
                <ul class="space-y-1.5">
                  <li v-for="fact in comparison.metacognitive_review.fact_interpretation_split.observable_facts" :key="fact" class="text-xs text-gray-500 dark:text-gray-400">{{ fact }}</li>
                </ul>
              </div>
              <div class="p-3 rounded-lg bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700">
                <p class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">暂持解释</p>
                <ul class="space-y-1.5">
                  <li v-for="item in comparison.metacognitive_review.fact_interpretation_split.interpretations_to_hold_lightly" :key="item" class="text-xs text-gray-500 dark:text-gray-400">{{ item }}</li>
                </ul>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mt-3">
              <div v-for="hypothesis in comparison.metacognitive_review.three_hypotheses" :key="hypothesis.name" class="p-3 rounded-lg bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700">
                <p class="text-sm font-semibold text-blue-600 dark:text-blue-400">{{ hypothesis.name }}</p>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-1 leading-relaxed">{{ hypothesis.content }}</p>
              </div>
            </div>

            <div class="mt-3 p-3 rounded-lg bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700">
              <p class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">下一步最小行动</p>
              <p class="text-sm text-gray-600 dark:text-gray-300">{{ comparison.metacognitive_review.next_minimum_action }}</p>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
            <button @click="loadNext()" class="btn-primary">继续下一题推荐</button>
            <router-link to="/mistakes" class="btn-secondary text-center">查看错题闭环</router-link>
          </div>
        </div>
      </section>

      <aside class="space-y-6">
        <div v-if="visualMap" class="card">
          <h2 class="text-lg font-bold text-gray-800 dark:text-white mb-1">数图合参</h2>
          <p class="text-xs text-gray-500 dark:text-gray-400 mb-4">{{ visualMap.axiom }}</p>

          <div class="space-y-4">
            <div>
              <div class="flex justify-between items-center mb-2">
                <p class="text-sm font-semibold text-gray-700 dark:text-gray-200">情绪流曲线</p>
                <span class="text-xs text-gray-400">起点 → 落点</span>
              </div>
              <div class="grid grid-cols-4 gap-2">
                <div v-for="point in visualMap.emotion_flow_curve" :key="point.step" class="min-h-[116px] flex flex-col justify-end">
                  <div class="rounded-t-lg bg-blue-500/80 min-h-[8px]" :style="{ height: point.value * 8 + 'px' }"></div>
                  <p class="text-xs font-medium text-gray-700 dark:text-gray-200 mt-2">{{ point.step }}</p>
                  <p class="text-[11px] text-gray-400 leading-snug">{{ point.value }}/10</p>
                </div>
              </div>
            </div>

            <div>
              <p class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">需求雷达</p>
              <div class="space-y-2">
                <div v-for="need in visualMap.need_radar" :key="need.name">
                  <div class="flex justify-between text-xs mb-1">
                    <span class="text-gray-500 dark:text-gray-400">{{ need.name }}</span>
                    <span class="font-medium text-gray-700 dark:text-gray-200">{{ need.value }}</span>
                  </div>
                  <div class="h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                    <div class="h-full rounded-full bg-teal-500" :style="{ width: need.value + '%' }"></div>
                  </div>
                </div>
              </div>
            </div>

            <div>
              <p class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">互动回路</p>
              <div class="space-y-2">
                <div v-for="node in visualMap.interaction_loop_graph.nodes" :key="node.id" class="flex items-start gap-2">
                  <div class="mt-1 h-2.5 w-2.5 rounded-full bg-blue-500 shrink-0"></div>
                  <div>
                    <p class="text-xs font-medium text-gray-700 dark:text-gray-200">{{ node.label }}</p>
                    <p class="text-xs text-gray-500 dark:text-gray-400">{{ node.value }}</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="p-3 rounded-xl bg-gray-50 dark:bg-gray-700/50">
              <p class="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2">轻验证问题</p>
              <ul class="space-y-2">
                <li v-for="prompt in visualMap.verification_prompts" :key="prompt" class="text-xs text-gray-600 dark:text-gray-300 leading-relaxed">{{ prompt }}</li>
              </ul>
            </div>
          </div>
        </div>

        <div class="card">
          <h2 class="text-lg font-bold text-gray-800 dark:text-white mb-4">能力雷达</h2>
          <div v-if="radar" class="space-y-3">
            <div v-for="level in radar.levels" :key="level.name">
              <div class="flex justify-between text-sm mb-1"><span class="text-gray-500">{{ level.name }}</span><span class="font-medium">{{ level.score }}%</span></div>
              <div class="h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden"><div class="h-full bg-blue-500" :style="{ width: level.score + '%' }"></div></div>
            </div>
          </div>
        </div>
        <div class="card bg-gray-900 text-white">
          <h2 class="text-lg font-bold mb-2">训练原则</h2>
          <p class="text-sm text-gray-300">先识别情绪，再理解需求；先创造安全，再推动连接；先尊重边界，再表达张力。</p>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import ModuleTabs from '@/components/ModuleTabs.vue'
import { useTrainingStore } from '@/stores/training'
import EmptyState from '@/components/EmptyState.vue'
import { useToast } from '@/utils/toast'
import type { ComparisonResult } from '@/utils/api'
import { useResourceContextFromRoute } from '@/composables/useResourceContext'

const store = useTrainingStore()
const toast = useToast()
const { route, router, resourceContext, loadResourceContextFromRoute, clearResourceContext } = useResourceContextFromRoute({
  clearPath: '/trainer',
  onError: (message) => toast.error(message),
})
const userResponse = ref('')
const responseType = ref('soft')
const submitting = ref(false)
const comparison = ref<ComparisonResult | null>(null)
const loadError = ref('')
const submitError = ref('')
const activeTab = ref('current_question')

const trainerTabs = [
  { id: 'current_question', label: '当前题', summary: '完成本轮回应训练。' },
  { id: 'feedback', label: '七维反馈', summary: '看回应哪里好、哪里漏、下一步怎么改。' },
]

const responseTypes = [
  { value: 'soft', label: '柔和' },
  { value: 'tension', label: '张力' },
  { value: 'humor', label: '幽默' },
]

const sample = computed(() => store.currentSample)
const nextItem = computed(() => store.nextItem)
const visualMap = computed(() => nextItem.value?.visual_map || null)
const radar = computed(() => store.radar)
const loading = computed(() => store.loading)
const resourcePracticePrompt = computed(() => {
  if (!resourceContext.value) return ''
  return resourceContext.value.usage_tip
    || resourceContext.value.source_summary
    || '先把资源里的“场景、TA 原话、常见失误、更好回应”拆出来，再写一句低压、具体、可退出的回应。'
})
const scoreClass = computed(() => {
  const score = comparison.value?.score || 0
  if (score >= 80) return 'text-green-500'
  if (score >= 60) return 'text-blue-500'
  return 'text-orange-500'
})
const scoringSourceLabel = computed(() => {
  if (comparison.value?.scoring_source === 'hybrid') return '规则评分 + AI 深评'
  if (comparison.value?.scoring_source === 'rule_fallback') return '规则评分（AI 未配置或安全降级）'
  return '规则评分'
})
const transitionFeedback = computed(() => comparison.value?.structured_diff?.developmental_emotion_transition || null)
const transitionDimensions = computed(() => transitionFeedback.value?.emotion_dimensions || {})
const transitionIntensityLabel = computed(() => {
  const intensity = transitionDimensions.value.intensity as { value?: number; label?: string } | undefined
  if (!intensity) return '待识别'
  return `${intensity.label || '待识别'} · ${intensity.value ?? 0}/10`
})
const transitionValenceLabel = computed(() => {
  const valence = transitionDimensions.value.valence as { label?: string } | undefined
  return valence?.label || '待识别'
})
const transitionTargetLabel = computed(() => {
  const target = transitionDimensions.value.target as { label?: string } | undefined
  return target?.label || '待识别'
})
const transitionPhaseLabel = computed(() => {
  const phase = transitionDimensions.value.phase as { label?: string } | undefined
  return phase?.label || '待识别'
})
const transitionScaffoldLabel = computed(() => {
  const scaffold = transitionFeedback.value?.scaffold_level as { level?: string } | undefined
  return scaffold?.level || '支架待识别'
})
const dimensionRows = computed(() => {
  const scores = comparison.value?.dimension_scores || {}
  const labels: Record<string, string> = {
    emotion_score: '情绪识别',
    need_score: '需求洞察',
    safety_score: '安全回应',
    connection_score: '连接延展',
    boundary_score: '边界尊重',
    style_score: '风格匹配',
    repair_score: '修复能力',
  }
  return Object.entries(labels).map(([key, label]) => ({ key, label, value: scores[key] || 0 }))
})
const boundaryMarkerStyle = computed(() => {
  const percent = visualMap.value?.boundary_band.percent || 0
  return { left: `${Math.max(0, Math.min(96, percent - 1))}%` }
})
const boundaryZoneClass = computed(() => {
  const zone = visualMap.value?.boundary_band.zone
  if (zone === 'green') return 'text-emerald-600 dark:text-emerald-400'
  if (zone === 'yellow') return 'text-amber-600 dark:text-amber-400'
  if (zone === 'orange') return 'text-orange-600 dark:text-orange-400'
  return 'text-red-600 dark:text-red-400'
})

function signalToneClass(type: string) {
  if (type === 'language') return 'text-blue-600 dark:text-blue-400'
  if (type === 'behavior') return 'text-purple-600 dark:text-purple-400'
  if (type === 'need') return 'text-teal-600 dark:text-teal-400'
  return 'text-orange-600 dark:text-orange-400'
}

async function loadNext(resetTab = true) {
  if (resetTab) {
    activeTab.value = 'current_question'
    syncQueryToUrl()
  }
  comparison.value = null
  loadError.value = ''
  submitError.value = ''
  userResponse.value = ''
  const next = await store.fetchNextTraining()
  await store.fetchRadar()
  if (!next) {
    loadError.value = '训练题加载失败，请检查后端服务或稍后重试。'
  }
}

async function loadAndPrefillResourceContext() {
  const resource = await loadResourceContextFromRoute()
  if (resource) {
    if (!userResponse.value.trim()) {
      prefillFromResource()
    }
  }
}

function prefillFromResource() {
  if (!resourceContext.value) return
  const goal = resourceContext.value.expression_goal || '低压承接'
  const scene = resourceContext.value.applicable_scene || resourceContext.value.category || '当前场景'
  const mistake = resourceContext.value.mistake_pattern ? `避开：${resourceContext.value.mistake_pattern}。` : '避开追问、逼迫和替对方下结论。'
  userResponse.value = `我先按「${scene}」练 ${goal}：我听见这里可能有情绪，也不急着让你马上回应。${mistake} 我会给你一个可以拒绝、也可以稍后再说的空间。`
}

async function submit() {
  if (!userResponse.value.trim()) return
  submitting.value = true
  submitError.value = ''
  const result = await store.submitComparison(userResponse.value, responseType.value)
  submitting.value = false
  if (result) {
    comparison.value = result
    activeTab.value = 'feedback'
    syncQueryToUrl()
    await store.fetchRadar()
    if (result.mistake_id) toast.info('这题已进入错题本，后续会按间隔重复复习')
  } else {
    submitError.value = '评分提交失败，请稍后重试；你输入的回应仍保留在文本框中。'
    toast.error('提交失败，请重试')
  }
}

function normalizeTab(value: unknown) {
  const tab = typeof value === 'string' ? value : ''
  return trainerTabs.some((item) => item.id === tab) ? tab : 'current_question'
}

function onTabChange(value: string) {
  activeTab.value = normalizeTab(value)
  syncQueryToUrl()
}

function syncQueryToUrl() {
  const query = { ...route.query }
  if (activeTab.value === 'current_question') delete query.tab
  else query.tab = activeTab.value
  router.replace({ path: '/trainer', query })
}

onMounted(async () => {
  activeTab.value = normalizeTab(route.query.tab)
  await loadNext(false)
  await loadAndPrefillResourceContext()
})

watch(
  () => route.query.resource_id,
  () => {
    loadAndPrefillResourceContext()
  }
)
</script>
