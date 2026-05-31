<template>
  <div class="h-full flex flex-col">
    <!-- 头部 -->
    <div class="shrink-0 p-6 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
      <div class="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 class="text-2xl font-bold text-gray-800 dark:text-white">AI 训练伴侣</h1>
          <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">与不同依恋类型的AI对话，练习回应策略</p>
        </div>
        <div class="flex w-full flex-wrap items-center gap-3 sm:w-auto sm:gap-4">
          <div class="max-w-full rounded-lg border border-gray-100 bg-gray-50 px-3 py-2 text-xs text-gray-600 dark:border-gray-700 dark:bg-gray-900/60 dark:text-gray-300">
            <p class="font-semibold">{{ providerStatus?.status_label || '正在检测 AI Provider' }}</p>
            <p class="mt-0.5 break-words">{{ providerStatusText }}</p>
          </div>
          <!-- 评分显示 -->
          <div class="flex min-w-0 items-center gap-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 px-3 py-2 text-white sm:px-4">
            <span class="truncate text-sm opacity-80">本次对话评分</span>
            <span class="text-2xl font-bold">{{ currentScore }}</span>
          </div>
          <!-- 设置按钮 -->
          <button
            @click="showSettings = !showSettings"
            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <Settings class="w-6 h-6 text-gray-500 dark:text-gray-400" />
          </button>
        </div>
      </div>
    </div>

    <!-- AI角色选择 -->
    <div v-if="!activeChat && !showSettings" class="p-6">
      <h2 class="text-lg font-bold text-gray-800 dark:text-white mb-4">选择训练场景</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="scenario in scenarios"
          :key="scenario.id"
          @click="startChat(scenario)"
          class="p-6 rounded-2xl border-2 border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-500 cursor-pointer transition-all hover:shadow-lg"
        >
          <div class="flex items-center gap-3 mb-4">
            <div class="w-12 h-12 rounded-full flex items-center justify-center text-2xl" :class="scenario.avatarBg">
              {{ scenario.avatar }}
            </div>
            <div>
              <h3 class="font-bold text-gray-800 dark:text-white">{{ scenario.name }}</h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">{{ scenario.style }}</p>
            </div>
          </div>
          <p class="text-sm text-gray-600 dark:text-gray-300 mb-4">{{ scenario.description }}</p>
          <div class="flex items-center gap-2 text-xs text-gray-400">
            <span>💬 {{ scenario.messageCount }}+ 对话</span>
            <span>📊 {{ scenario.difficulty }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 设置面板 -->
    <div v-if="showSettings" class="p-6">
      <div class="max-w-2xl mx-auto">
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-gray-800 dark:text-white">对话设置</h2>
          <button @click="showSettings = false" class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
            <ArrowLeft class="w-6 h-6 text-gray-500" />
          </button>
        </div>

        <div class="card space-y-6">
          <!-- 难度 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">对话难度</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="level in difficultyLevels"
                :key="level.value"
                @click="chatSettings.difficulty = level.value"
                class="min-w-[88px] flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors sm:flex-none"
                :class="[
                  chatSettings.difficulty === level.value
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                ]"
              >
                {{ level.label }}
              </button>
            </div>
          </div>

          <!-- 回应风格 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">期望回应风格</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="style in responseStyles"
                :key="style.value"
                @click="chatSettings.responseStyle = style.value"
                class="min-w-[104px] flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors sm:flex-none"
                :class="[
                  chatSettings.responseStyle === style.value
                    ? 'bg-purple-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                ]"
              >
                {{ style.icon }} {{ style.label }}
              </button>
            </div>
          </div>

          <!-- 话题偏好 -->
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">话题偏好</label>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="topic in topicOptions"
                :key="topic"
                @click="toggleTopic(topic)"
                class="px-3 py-1.5 rounded-full text-sm transition-colors"
                :class="[
                  chatSettings.topics.includes(topic)
                    ? 'bg-green-500 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                ]"
              >
                {{ topic }}
              </button>
            </div>
          </div>

          <button @click="applySettings" class="btn-primary w-full">
            开始对话
          </button>
        </div>
      </div>
    </div>

    <!-- 聊天区域 -->
    <div v-if="activeChat" class="min-h-0 flex-1 flex flex-col overflow-y-auto">
      <!-- 聊天头部 -->
      <div class="shrink-0 p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex items-center gap-4">
        <button @click="endChat" class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700">
          <ArrowLeft class="w-5 h-5 text-gray-500" />
        </button>
        <div class="w-10 h-10 rounded-full flex items-center justify-center text-xl" :class="activeChat.avatarBg">
          {{ activeChat.avatar }}
        </div>
        <div class="flex-1">
          <h3 class="font-bold text-gray-800 dark:text-white">{{ activeChat.name }}</h3>
          <p class="text-xs text-gray-500 dark:text-gray-400">{{ activeChat.style }}</p>
        </div>
        <div class="flex items-center gap-2">
          <span
            class="px-3 py-1 rounded-full text-xs font-medium"
            :class="[
              isTyping
                ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                : 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
            ]"
          >
            {{ isTyping ? '对方正在输入...' : '在线' }}
          </span>
        </div>
      </div>

      <!-- 关系状态机 -->
      <div
        v-if="relationshipState"
        class="shrink-0 px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50/90 dark:bg-gray-900/40"
      >
        <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <span
                class="px-2.5 py-1 rounded-md text-xs font-semibold"
                :class="stateBadgeClass(relationshipState.state_color)"
              >
                {{ relationshipState.state_label }}
              </span>
              <span class="text-xs text-gray-500 dark:text-gray-400">第 {{ relationshipState.turn_count }} 轮状态</span>
            </div>
            <p class="mt-1 text-xs text-gray-600 dark:text-gray-300 leading-relaxed">
              {{ relationshipState.interpretation }}
            </p>
            <p class="mt-1 text-xs text-blue-600 dark:text-blue-300">
              下一焦点：{{ relationshipState.next_focus }}
            </p>
          </div>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-3 lg:w-[520px]">
            <div v-for="metric in stateMetrics" :key="metric.key" class="min-w-0">
              <div class="flex items-center justify-between gap-2 text-xs">
                <span class="font-medium text-gray-600 dark:text-gray-300">{{ metric.label }}</span>
                <span class="text-gray-500 dark:text-gray-400">{{ metric.value }}</span>
              </div>
              <div class="mt-1 h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-300"
                  :class="metric.barClass"
                  :style="{ width: `${metric.value}%` }"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="sessionReview"
        class="shrink-0 px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-white/90 dark:bg-gray-900/70"
      >
        <div class="grid grid-cols-1 xl:grid-cols-[1.15fr_0.85fr] gap-5">
          <div class="min-w-0">
            <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
              <div>
                <p class="text-sm font-semibold text-gray-800 dark:text-white">会话状态曲线</p>
                <p class="text-xs text-gray-500 dark:text-gray-400">{{ sessionReview.principle }}</p>
              </div>
              <span class="text-xs text-blue-600 dark:text-blue-300">
                平均 {{ Math.round(sessionReview.session.average_score) }} 分 · {{ sessionReview.session.total_turns }} 轮
              </span>
            </div>
            <div class="flex items-end gap-2 h-24">
              <div
                v-for="point in sessionReview.state_curve"
                :key="point.turn"
                class="flex-1 min-w-0 flex flex-col items-center justify-end gap-1"
              >
                <div class="w-full flex items-end justify-center gap-0.5 h-16">
                  <span class="w-1.5 rounded-t bg-green-500" :style="{ height: `${reviewBarHeight(point.trust)}px` }"></span>
                  <span class="w-1.5 rounded-t bg-amber-500" :style="{ height: `${reviewBarHeight(point.stress)}px` }"></span>
                  <span class="w-1.5 rounded-t bg-red-500" :style="{ height: `${reviewBarHeight(point.boundary)}px` }"></span>
                  <span class="w-1.5 rounded-t bg-blue-500" :style="{ height: `${reviewBarHeight(point.connection)}px` }"></span>
                </div>
                <span class="text-[10px] text-gray-400 truncate">T{{ point.turn }}</span>
              </div>
            </div>
            <div class="mt-2 flex flex-wrap gap-3 text-[11px] text-gray-500 dark:text-gray-400">
              <span class="inline-flex items-center gap-1"><i class="w-2 h-2 rounded bg-green-500"></i>信任</span>
              <span class="inline-flex items-center gap-1"><i class="w-2 h-2 rounded bg-amber-500"></i>压力</span>
              <span class="inline-flex items-center gap-1"><i class="w-2 h-2 rounded bg-red-500"></i>边界压</span>
              <span class="inline-flex items-center gap-1"><i class="w-2 h-2 rounded bg-blue-500"></i>连接</span>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-3">
              <p class="text-xs font-semibold text-gray-700 dark:text-gray-200 mb-2">关键转折</p>
              <div class="space-y-2">
                <div v-for="point in sessionReview.turning_points.slice(0, 2)" :key="`${point.turn}-${point.title}`" class="text-xs">
                  <div class="flex items-center gap-2">
                    <span class="px-1.5 py-0.5 rounded" :class="turningSeverityClass(point.severity)">T{{ point.turn }}</span>
                    <span class="font-medium text-gray-700 dark:text-gray-100">{{ point.title }}</span>
                  </div>
                  <p class="text-gray-500 dark:text-gray-400 mt-1">{{ point.evidence }}</p>
                </div>
                <p v-if="sessionReview.turning_points.length === 0" class="text-xs text-gray-500">继续对话后识别转折。</p>
              </div>
            </div>
            <div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-3">
              <p class="text-xs font-semibold text-gray-700 dark:text-gray-200 mb-2">下一练习</p>
              <p class="text-sm font-semibold text-blue-600 dark:text-blue-300">{{ sessionReview.next_practice.focus }}</p>
              <p class="text-xs text-gray-600 dark:text-gray-300 mt-1">{{ sessionReview.next_practice.minimum_action }}</p>
              <div class="flex flex-wrap gap-1 mt-2">
                <span v-for="drill in sessionReview.next_practice.drills" :key="drill" class="px-2 py-1 rounded bg-white dark:bg-gray-900 text-[11px] text-gray-500 dark:text-gray-300">
                  {{ drill }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div
        v-if="sessionReviewError"
        class="mx-6 mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-900/20 dark:text-amber-200"
      >
        <div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p>{{ sessionReviewError }}</p>
          <button
            class="rounded-lg bg-amber-500 px-3 py-2 text-white hover:bg-amber-600 disabled:opacity-60"
            :disabled="reviewRetrying"
            @click="retrySessionReview"
          >
            {{ reviewRetrying ? '重试中...' : '重试复盘' }}
          </button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div ref="messageContainer" class="max-h-[420px] min-h-[220px] shrink-0 overflow-auto p-6 space-y-4">
        <div
          v-for="(message, index) in messages"
          :key="index"
          class="flex animate-fadeIn"
          :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <!-- AI消息 -->
          <div v-if="message.role === 'ai'" class="flex items-start gap-3 max-w-[80%]">
            <div class="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center" :class="activeChat.avatarBg">
              {{ activeChat.avatar }}
            </div>
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-sm font-medium text-gray-600 dark:text-gray-300">{{ activeChat.name }}</span>
                <span class="text-xs text-gray-400">{{ message.time }}</span>
              </div>
              <div class="p-4 rounded-2xl rounded-tl-none bg-white dark:bg-gray-700 shadow-sm">
                <p class="text-gray-800 dark:text-gray-100 whitespace-pre-wrap">{{ message.content }}</p>
              </div>
              <!-- 消息评分 -->
              <div v-if="message.score" class="flex items-center gap-2 mt-2">
                <span class="text-xs text-gray-500 dark:text-gray-400">本次回应评分</span>
                <div
                  class="px-2 py-0.5 rounded text-xs font-bold"
                  :class="[
                    message.score >= 80
                      ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                      : message.score >= 60
                      ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                      : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                  ]"
                >
                  {{ message.score }}
                </div>
                <span v-if="message.source" class="text-xs text-gray-400">{{ sourceLabel(message.source) }}</span>
              </div>
              <div v-if="message.expression_chain" class="mt-2 rounded-xl border border-indigo-100 bg-indigo-50/70 p-3 dark:border-indigo-900/50 dark:bg-indigo-950/20">
                <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p class="text-xs font-semibold text-indigo-600 dark:text-indigo-300">表达工具链 · {{ message.expression_chain.target_goal }}</p>
                    <p class="mt-1 text-xs leading-relaxed text-gray-600 dark:text-gray-300">{{ message.expression_chain.principle }}</p>
                  </div>
                  <span class="rounded bg-white px-2 py-1 text-xs text-indigo-700 dark:bg-gray-900 dark:text-indigo-300">{{ message.expression_chain.state_shift.label }}</span>
                </div>
                <div class="mt-2 flex flex-wrap gap-1.5">
                  <span v-for="tool in message.expression_chain.tool_names" :key="`${message.time}-${tool}`" class="rounded bg-white px-2 py-1 text-[11px] text-indigo-700 dark:bg-gray-900 dark:text-indigo-300">
                    {{ tool }}
                  </span>
                </div>
                <p v-if="message.expression_chain.context_observation" class="mt-2 text-xs leading-relaxed text-gray-600 dark:text-gray-300">
                  本轮观察：{{ message.expression_chain.context_observation }}
                </p>
                <div v-if="message.expression_chain.micro_plan?.length" class="mt-2 flex flex-wrap gap-1.5">
                  <span
                    v-for="step in message.expression_chain.micro_plan"
                    :key="`${message.time}-micro-${step}`"
                    class="rounded bg-white px-2 py-1 text-[11px] text-gray-600 dark:bg-gray-900 dark:text-gray-300"
                  >
                    {{ step }}
                  </span>
                </div>
                <p class="mt-2 text-xs text-gray-600 dark:text-gray-300">下一步：{{ message.expression_chain.next_move }}</p>
                <p class="mt-1 text-xs text-blue-600 dark:text-blue-300">{{ message.expression_chain.practice_prompt }}</p>
                <p v-if="message.expression_chain.example_next_reply" class="mt-1 rounded-lg bg-white/70 p-2 text-xs leading-relaxed text-emerald-700 dark:bg-gray-900 dark:text-emerald-300">
                  示例下一句：{{ message.expression_chain.example_next_reply }}
                </p>
                <p v-if="message.expression_chain.anti_pattern" class="mt-1 text-[11px] text-rose-600 dark:text-rose-300">
                  避免：{{ message.expression_chain.anti_pattern }}
                </p>
                <p class="mt-1 text-[11px] text-amber-700 dark:text-amber-300">{{ message.expression_chain.risk_boundary }}</p>
              </div>
              <div v-if="message.related_resources?.length" class="mt-2 rounded-xl border border-sky-100 bg-sky-50/70 p-3 dark:border-sky-900/50 dark:bg-sky-950/20">
                <p class="mb-2 text-xs font-semibold text-sky-700 dark:text-sky-300">关联资源</p>
                <div class="grid grid-cols-1 gap-2 sm:grid-cols-3">
                  <RouterLink
                    v-for="resource in message.related_resources"
                    :key="`${message.time}-${resource.id}-${resource.title}`"
                    :to="{ path: '/resources', query: resource.id ? { q: resource.title } : { q: resource.reason } }"
                    class="rounded-lg bg-white p-2 text-xs shadow-sm hover:bg-sky-100 dark:bg-gray-900 dark:hover:bg-sky-950/50"
                  >
                    <span class="block font-semibold text-sky-700 dark:text-sky-300">{{ resource.title }}</span>
                    <span class="mt-1 block text-gray-500 dark:text-gray-400">{{ resource.reason }}</span>
                  </RouterLink>
                </div>
              </div>
              <div v-if="message.mistake_memory?.cards?.length || message.mistake_memory?.weak_dimensions?.length" class="mt-2 rounded-xl border border-rose-100 bg-rose-50/70 p-3 dark:border-rose-900/50 dark:bg-rose-950/20">
                <div class="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p class="text-xs font-semibold text-rose-700 dark:text-rose-300">近期错题记忆</p>
                    <p class="mt-1 text-xs leading-relaxed text-gray-600 dark:text-gray-300">{{ message.mistake_memory.next_focus }}</p>
                  </div>
                  <RouterLink to="/mistakes" class="rounded bg-white px-2 py-1 text-xs text-rose-700 hover:bg-rose-100 dark:bg-gray-900 dark:text-rose-300 dark:hover:bg-rose-950/60">
                    打开错题本
                  </RouterLink>
                </div>
                <div v-if="message.mistake_memory.weak_dimensions?.length" class="mt-2 flex flex-wrap gap-1.5">
                  <span
                    v-for="dimension in message.mistake_memory.weak_dimensions"
                    :key="`${message.time}-${dimension.dimension}`"
                    class="rounded bg-white px-2 py-1 text-[11px] text-rose-700 dark:bg-gray-900 dark:text-rose-300"
                  >
                    {{ dimension.label }} {{ Math.round(dimension.score) }}
                  </span>
                </div>
                <div class="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                  <div
                    v-for="card in message.mistake_memory.cards.slice(0, 2)"
                    :key="`${message.time}-${card.mistake_id}-${card.their_words}`"
                    class="rounded-lg bg-white p-2 text-xs shadow-sm dark:bg-gray-900"
                  >
                    <div class="flex flex-wrap items-center gap-1.5">
                      <span class="font-semibold text-rose-700 dark:text-rose-300">{{ card.review_focus || card.emotion_mistake || '旧失误' }}</span>
                      <span v-if="card.scene" class="rounded bg-rose-100 px-1.5 py-0.5 text-[10px] text-rose-700 dark:bg-rose-900/40 dark:text-rose-200">{{ card.scene }}</span>
                    </div>
                    <p class="mt-1 text-gray-500 dark:text-gray-400">TA：{{ card.their_words }}</p>
                    <p class="mt-1 text-gray-500 dark:text-gray-400">旧回应：{{ card.user_bad_response }}</p>
                    <p v-if="card.expression_rewrite?.rewrite_versions?.[0]?.text" class="mt-1 text-rose-700 dark:text-rose-300">
                      这轮避坑：{{ card.expression_rewrite.rewrite_versions[0].text }}
                    </p>
                  </div>
                </div>
                <p class="mt-2 text-[11px] text-gray-500 dark:text-gray-400">{{ message.mistake_memory.principle }}</p>
              </div>
              <div v-if="message.suggestions?.length" class="mt-2 space-y-1">
                <p v-for="tip in message.suggestions" :key="tip" class="text-xs text-gray-500 dark:text-gray-400">{{ tip }}</p>
              </div>
            </div>
          </div>

          <!-- 用户消息 -->
          <div v-else class="flex items-start gap-3 max-w-[80%] justify-end">
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1 justify-end">
                <span class="text-xs text-gray-400">{{ message.time }}</span>
                <span class="text-sm font-medium text-gray-600 dark:text-gray-300">你</span>
              </div>
              <div class="p-4 rounded-2xl rounded-tr-none bg-blue-500 text-white shadow-sm">
                <p class="whitespace-pre-wrap">{{ message.content }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 加载指示 -->
        <div v-if="isTyping" class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center" :class="activeChat.avatarBg">
            {{ activeChat.avatar }}
          </div>
          <div class="p-4 rounded-2xl rounded-tl-none bg-white dark:bg-gray-700 shadow-sm">
            <div class="flex items-center gap-1">
              <div class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style="animation-delay: 0ms"></div>
              <div class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style="animation-delay: 150ms"></div>
              <div class="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style="animation-delay: 300ms"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 建议回复 -->
      <div v-if="suggestedReplies.length > 0" class="shrink-0 px-6 pb-2">
        <div class="flex items-center gap-2 mb-2">
          <span class="text-xs text-gray-500 dark:text-gray-400">建议回复</span>
        </div>
        <div class="flex gap-2 overflow-x-auto pb-2">
          <button
            v-for="(reply, index) in suggestedReplies"
            :key="index"
            @click="useSuggestedReply(reply)"
            class="flex-shrink-0 px-4 py-2 rounded-full bg-gray-100 dark:bg-gray-700 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
          >
            {{ reply }}
          </button>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="shrink-0 p-6 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
        <div
          v-if="sendError"
          class="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-900/20 dark:text-amber-200"
        >
          {{ sendError }}
        </div>
        <div class="flex items-end gap-4">
          <div class="flex-1">
            <textarea
              v-model="inputMessage"
              @keydown.enter.exact.prevent="sendMessage"
              class="input-mac min-h-[60px] max-h-[120px] resize-none"
              placeholder="输入你的回应..."
            ></textarea>
          </div>
          <button
            @click="sendMessage"
            :disabled="!inputMessage.trim() || isTyping"
            class="p-4 rounded-xl bg-blue-500 text-white hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            :title="isTyping ? '正在等待回应' : '发送回应'"
          >
            <Send class="w-5 h-5" />
          </button>
        </div>
        <div class="flex items-center justify-between mt-3 text-xs text-gray-400">
          <span>按 Enter 发送，Shift + Enter 换行</span>
          <span>对话轮次: {{ messageCount }}</span>
        </div>
      </div>
    </div>

    <!-- 评分统计弹窗 -->
    <Teleport to="body">
      <transition name="fade">
        <div
          v-if="showScoreModal"
          class="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          @click.self="showScoreModal = false"
        >
          <div class="bg-white dark:bg-gray-800 rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl text-center">
            <div class="text-6xl mb-4">{{ scoreEmoji }}</div>
            <h2 class="text-2xl font-bold text-gray-800 dark:text-white mb-2">对话结束</h2>
            <p class="text-gray-500 dark:text-gray-400 mb-6">你与 {{ activeChat?.name }} 的训练对话已完成</p>

            <div class="space-y-4 mb-8">
              <div class="flex justify-between items-center p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
                <span class="text-gray-600 dark:text-gray-300">总体评分</span>
                <span class="text-3xl font-bold text-blue-500">{{ finalScore }}</span>
              </div>
              <div class="flex justify-between items-center p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
                <span class="text-gray-600 dark:text-gray-300">对话轮次</span>
                <span class="text-xl font-bold text-gray-800 dark:text-white">{{ messageCount }}</span>
              </div>
              <div class="flex justify-between items-center p-4 rounded-xl bg-gray-50 dark:bg-gray-700/50">
                <span class="text-gray-600 dark:text-gray-300">用时</span>
                <span class="text-xl font-bold text-gray-800 dark:text-white">{{ conversationDuration }}</span>
              </div>
            </div>

            <div class="flex gap-4">
              <button @click="showScoreModal = false" class="flex-1 btn-secondary">
                查看详情
              </button>
              <button @click="restartChat" class="flex-1 btn-primary">
                再来一轮
              </button>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { Settings, ArrowLeft, Send } from 'lucide-vue-next'
import { useToast } from '@/utils/toast'
import { trainingApi } from '@/utils/api'
import type { PartnerExpressionChain, PartnerMistakeMemory, PartnerProviderStatus, PartnerRelatedResource, PartnerSessionReview, RelationshipState } from '@/utils/api'

const toast = useToast()

const showSettings = ref(false)
const activeChat = ref<typeof scenarios.value[0] | null>(null)
const messages = ref<Array<{ role: 'user' | 'ai'; content: string; time: string; score?: number; source?: string; suggestions?: string[]; expression_chain?: PartnerExpressionChain; related_resources?: PartnerRelatedResource[]; mistake_memory?: PartnerMistakeMemory }>>([])
const inputMessage = ref('')
const isTyping = ref(false)
const messageContainer = ref<HTMLElement | null>(null)
const messageCount = ref(0)
const showScoreModal = ref(false)
const finalScore = ref(0)
const conversationStartTime = ref<Date | null>(null)
const relationshipState = ref<RelationshipState | null>(null)
const activeSessionId = ref<number | null>(null)
const sessionReview = ref<PartnerSessionReview | null>(null)
const providerStatus = ref<PartnerProviderStatus | null>(null)
const sendError = ref('')
const sessionReviewError = ref('')
const reviewRetrying = ref(false)

const chatSettings = ref({
  difficulty: 'medium',
  responseStyle: 'soft',
  topics: ['日常沟通', '情绪支持', '冲突处理']
})

const scenarios = ref([
  {
    id: 'anxious',
    name: '小焦虑',
    avatar: '😰',
    avatarBg: 'bg-orange-100 dark:bg-orange-900/30',
    style: '焦虑型依恋',
    description: '渴望亲密但容易担心被抛弃，倾向于过度依赖或过度解读伴侣行为',
    messageCount: 120,
    difficulty: '中等'
  },
  {
    id: 'avoidant',
    name: '小回避',
    avatar: '🚪',
    avatarBg: 'bg-blue-100 dark:bg-blue-900/30',
    style: '回避型依恋',
    description: '重视独立空间，倾向于在情感上保持距离，对亲密关系有所保留',
    messageCount: 95,
    difficulty: '较难'
  },
  {
    id: 'secure',
    name: '小安心',
    avatar: '😊',
    avatarBg: 'bg-green-100 dark:bg-green-900/30',
    style: '安全型依恋',
    description: '在亲密关系中感到安心，能够开放表达情感，建立健康稳定的依恋关系',
    messageCount: 200,
    difficulty: '入门'
  },
  {
    id: 'fearful',
    name: '小纠结',
    avatar: '😨',
    avatarBg: 'bg-purple-100 dark:bg-purple-900/30',
    style: '恐惧型依恋',
    description: '既渴望亲密又害怕被伤害，在亲密和独立之间挣扎',
    messageCount: 80,
    difficulty: '困难'
  }
])

const difficultyLevels = [
  { value: 'easy', label: '入门' },
  { value: 'medium', label: '中等' },
  { value: 'hard', label: '困难' }
]

const responseStyles = [
  { value: 'soft', icon: '🌊', label: '柔和' },
  { value: 'tension', icon: '⚡', label: '张力' },
  { value: 'humor', icon: '😄', label: '幽默' }
]

const topicOptions = ['日常沟通', '情绪支持', '冲突处理', '亲密关系', '个人空间', '未来规划']

const suggestedReplies = ref<string[]>([])

const currentScore = computed(() => {
  if (messages.value.length === 0) return 0
  const scoredMessages = messages.value.filter(m => m.score !== undefined)
  if (scoredMessages.length === 0) return 0
  return Math.round(scoredMessages.reduce((sum, m) => sum + (m.score || 0), 0) / scoredMessages.length)
})

const scoreEmoji = computed(() => {
  if (finalScore.value >= 80) return '🏆'
  if (finalScore.value >= 60) return '👍'
  if (finalScore.value >= 40) return '💪'
  return '📚'
})

const conversationDuration = computed(() => {
  if (!conversationStartTime.value) return '0分钟'
  const diff = Date.now() - conversationStartTime.value.getTime()
  const minutes = Math.floor(diff / 60000)
  return `${minutes}分钟`
})

const stateMetrics = computed(() => {
  if (!relationshipState.value) return []
  return [
    { key: 'trust', label: '信任', value: Math.round(relationshipState.value.trust), barClass: 'bg-green-500' },
    { key: 'stress', label: '压力', value: Math.round(relationshipState.value.stress), barClass: 'bg-amber-500' },
    { key: 'boundary', label: '边界压', value: Math.round(relationshipState.value.boundary), barClass: 'bg-red-500' },
    { key: 'connection', label: '连接', value: Math.round(relationshipState.value.connection), barClass: 'bg-blue-500' },
  ]
})

const providerStatusText = computed(() => {
  if (!providerStatus.value) return 'provider 状态加载中'
  const risks = providerStatus.value.compatibility_risks.length
  return `${providerStatus.value.provider}/${providerStatus.value.mode} · ${providerStatus.value.model}${risks ? ` · ${risks} 个兼容风险` : ''}`
})

onMounted(() => {
  conversationStartTime.value = new Date()
  refreshProviderStatus()
})

async function refreshProviderStatus() {
  try {
    providerStatus.value = await trainingApi.partnerProviderStatus()
  } catch (error) {
    console.error('partnerProviderStatus failed', error)
  }
}

function toggleTopic(topic: string) {
  const index = chatSettings.value.topics.indexOf(topic)
  if (index > -1) {
    chatSettings.value.topics.splice(index, 1)
  } else {
    chatSettings.value.topics.push(topic)
  }
}

function applySettings() {
  showSettings.value = false
  toast.success('设置已保存，开始对话吧！')
}

function startChat(scenario: typeof scenarios.value[0]) {
  activeChat.value = scenario
  messageCount.value = 0
  messages.value = []
  relationshipState.value = createInitialRelationshipState(scenario)
  activeSessionId.value = null
  sessionReview.value = null
  sessionReviewError.value = ''
  sendError.value = ''
  conversationStartTime.value = new Date()

  const openingMessage = getOpeningMessage(scenario.id)
  addAiMessage(openingMessage)
  generateSuggestedReplies()
}

function getOpeningMessage(scenarioId: string): string {
  const openings: Record<string, string> = {
    anxious: '嗨...你在吗？我刚才给你发了好几条消息，你都没回我...你是不是不想理我了？',
    avoidant: '嗯，我今天比较忙，晚上再说吧。',
    secure: '嗨！今天过得怎么样？周末有什么计划吗？',
    fearful: '其实...我有点不知道该怎么跟你说。最近我们的关系让我有点困惑。'
  }
  return openings[scenarioId] || '你好，我们聊聊吧。'
}

function addAiMessage(content: string, score?: number, source?: string, suggestions: string[] = [], expressionChain?: PartnerExpressionChain, relatedResources: PartnerRelatedResource[] = [], mistakeMemory?: PartnerMistakeMemory) {
  messages.value.push({
    role: 'ai',
    content,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    score,
    source,
    suggestions,
    expression_chain: expressionChain,
    related_resources: relatedResources,
    mistake_memory: mistakeMemory,
  })
  messageCount.value++
}

function addUserMessage(content: string) {
  messages.value.push({
    role: 'user',
    content,
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  })
}

async function sendMessage() {
  if (!inputMessage.value.trim() || isTyping.value) return

  const userMessage = inputMessage.value
  inputMessage.value = ''
  sendError.value = ''
  addUserMessage(userMessage)
  scrollToBottom()

  isTyping.value = true
  suggestedReplies.value = []

  try {
    const partnerResponse = await requestPartnerResponse(userMessage)
    relationshipState.value = partnerResponse.relationship_state ?? relationshipState.value
    activeSessionId.value = partnerResponse.session_id ?? activeSessionId.value
    await refreshSessionReview()
    addAiMessage(partnerResponse.reply, partnerResponse.score, partnerResponse.source, partnerResponse.suggestions, partnerResponse.expression_chain, partnerResponse.related_resources, partnerResponse.mistake_memory)
    if (partnerResponse.source === 'local_error_fallback') {
      sendError.value = 'AI 伴侣接口暂时不可用，已切换为本地安全降级回应；你可以继续练习，稍后再试深度模拟。'
    }
    generateSuggestedReplies()
    scrollToBottom()
  } finally {
    isTyping.value = false
  }

  // 检查是否达到对话轮次上限
  if (messageCount.value >= 20) {
    showScoreModal.value = true
    finalScore.value = currentScore.value
  }
}

async function requestPartnerResponse(userMessage: string) {
  if (!activeChat.value) {
    return {
      session_id: activeSessionId.value,
      reply: '好的，我明白了。',
      score: 60,
      source: 'rule_fallback:no_active_chat',
      suggestions: [],
      relationship_state: relationshipState.value ?? createFallbackRelationshipState(),
      expression_chain: createFallbackExpressionChain(),
      related_resources: [],
      mistake_memory: createFallbackMistakeMemory(),
    }
  }
  try {
    return await trainingApi.simulatePartner({
      session_id: activeSessionId.value,
      scenario_id: activeChat.value.id,
      scenario_name: activeChat.value.name,
      attachment_style: activeChat.value.style,
      user_message: userMessage,
      history: messages.value.slice(-8).map(message => ({ role: message.role, content: message.content })),
      difficulty: chatSettings.value.difficulty,
      response_style: chatSettings.value.responseStyle,
      topics: chatSettings.value.topics,
      relationship_state: relationshipState.value,
    })
  } catch (error) {
    console.error('simulatePartner failed', error)
    toast.error('AI 伴侣暂时降级为本地安全模式')
    return {
      session_id: activeSessionId.value,
      reply: '我听到了。我们可以慢慢聊，但我也需要感觉到自己是被尊重的。',
      score: 62,
      source: 'local_error_fallback',
      suggestions: ['后端暂时不可用时，先练习情绪反射和退路式表达。'],
      relationship_state: relationshipState.value ?? createFallbackRelationshipState(),
      expression_chain: createFallbackExpressionChain(),
      related_resources: [],
      mistake_memory: createFallbackMistakeMemory(),
    }
  }
}

function createFallbackMistakeMemory(): PartnerMistakeMemory {
  return {
    cards: [],
    weak_dimensions: [],
    next_focus: '本地降级时暂无错题记忆，先保持低压、具体、可退出。',
    principle: 'AI 伴侣会参考近期错题，但只用于提醒训练动作，不把历史失误当成用户标签。',
  }
}

function createFallbackExpressionChain(): PartnerExpressionChain {
  const state = relationshipState.value ?? createFallbackRelationshipState()
  return {
    target_goal: '降低防御',
    state_shift: {
      label: state.state_label,
      trust: state.trust,
      stress: state.stress,
      boundary: state.boundary,
      connection: state.connection,
      interpretation: state.interpretation,
    },
    tool_ids: ['expr_tool_041', 'expr_tool_027'],
    tool_names: ['情绪标注', '请求结构'],
    why: ['本地降级时优先保持低压和边界。'],
    next_move: '先命名感受，再给一个可拒绝的小问题。',
    practice_prompt: '下一句只用「情绪标注」完成低压回应。',
    risk_boundary: '保持可拒绝、可退出、可慢一点。',
    principle: '表达链必须从本轮原话、对方回弹和关系状态里选动作；不要机械复读同一条训练提示。',
    context_observation: '本地降级时无法读取完整模型回弹，先按当前关系状态练低压承接。',
    micro_plan: ['命名感受', '给出退路', '只问一个问题'],
    example_next_reply: '我听见你这里有点不安，我们可以慢一点；你愿意先说最明显的一点吗？',
    anti_pattern: '不要套固定话术；先抓本轮关键词，再选择一个动作。',
  }
}

function generateSuggestedReplies() {
  if (!activeChat.value) return

  const suggestions: Record<string, string[]> = {
    anxious: ['我在这里。刚才没及时回让你不安了，对吗？', '我不想用空话安抚你，可以先给你一个明确时间。', '你最怕的是我不在，还是怕我变冷？'],
    avoidant: ['我给你空间，也会留一个可以回来聊的入口。', '我不会追着你要答案，但我想让你知道我在意。', '我们先说一件最轻的事，不急着聊深。'],
    secure: ['我喜欢这个节奏，我们把彼此真实的想法说清楚。', '我听见你的感受了，也想补充我的那部分。', '我们一起把下一步定得舒服一点。'],
    fearful: ['我们慢一点，我不会逼你马上相信。', '你想靠近又紧张，这两种感觉都可以在。', '我先稳定地待在这里，不急着证明什么。']
  }

  const pool = suggestions[activeChat.value.id] || ['好的']
  suggestedReplies.value = pool.slice(0, 3)
}

function useSuggestedReply(reply: string) {
  inputMessage.value = reply
  sendMessage()
}

function sourceLabel(source?: string) {
  if (!source) return ''
  if (source === 'ai_orchestrator') return 'AI深度模拟'
  if (source === 'safety_blocked') return '安全阻断'
  return '安全降级'
}

async function refreshSessionReview() {
  if (!activeSessionId.value) return
  try {
    sessionReviewError.value = ''
    sessionReview.value = await trainingApi.partnerSessionReview(activeSessionId.value)
  } catch (error) {
    console.error('partnerSessionReview failed', error)
    sessionReviewError.value = '会话复盘暂时不可用，但当前对话已保留，可以稍后重试复盘。'
  }
}

async function retrySessionReview() {
  if (!activeSessionId.value || reviewRetrying.value) return
  reviewRetrying.value = true
  try {
    await refreshSessionReview()
  } finally {
    reviewRetrying.value = false
  }
}

function createInitialRelationshipState(scenario: typeof scenarios.value[0]): RelationshipState {
  const baselines: Record<string, Pick<RelationshipState, 'trust' | 'stress' | 'boundary' | 'boundary_safety' | 'connection'>> = {
    anxious: { trust: 42, stress: 62, boundary: 48, boundary_safety: 46, connection: 58 },
    avoidant: { trust: 46, stress: 48, boundary: 68, boundary_safety: 42, connection: 36 },
    secure: { trust: 62, stress: 28, boundary: 32, boundary_safety: 72, connection: 58 },
    fearful: { trust: 38, stress: 64, boundary: 62, boundary_safety: 38, connection: 44 },
  }
  const values = baselines[scenario.id] ?? baselines.secure
  return {
    ...values,
    turn_count: 0,
    attachment_style: scenario.style,
    state_label: scenario.id === 'secure' ? '可对话窗口' : '谨慎试探',
    state_color: scenario.id === 'secure' ? 'blue' : 'yellow',
    last_delta: {},
    interpretation: `信任 ${values.trust}/100，压力 ${values.stress}/100，边界压力 ${values.boundary}/100，连接 ${values.connection}/100。`,
    next_focus: '先观察线索，再用轻问句验证。',
  }
}

function createFallbackRelationshipState(): RelationshipState {
  return {
    trust: 50,
    stress: 35,
    boundary: 35,
    boundary_safety: 65,
    connection: 45,
    turn_count: 0,
    attachment_style: '',
    state_label: '观察中',
    state_color: 'neutral',
    last_delta: {},
    interpretation: '关系状态正在建立基线。',
    next_focus: '先观察线索，再用轻问句验证。',
  }
}

function stateBadgeClass(color: string) {
  const classes: Record<string, string> = {
    green: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
    blue: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
    yellow: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
    orange: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
    red: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  }
  return classes[color] ?? 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300'
}

function turningSeverityClass(severity: string) {
  const classes: Record<string, string> = {
    green: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
    yellow: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-300',
    orange: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
    red: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
  }
  return classes[severity] ?? 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
}

function reviewBarHeight(value: number) {
  return Math.max(4, Math.round(Math.min(100, Math.max(0, value)) * 0.56))
}

function scrollToBottom() {
  nextTick(() => {
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight
    }
  })
}

function endChat() {
  showScoreModal.value = true
  finalScore.value = currentScore.value
}

function restartChat() {
  showScoreModal.value = false
  if (activeChat.value) {
    startChat(activeChat.value)
  }
}
</script>

<style scoped>
.animate-fadeIn {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
