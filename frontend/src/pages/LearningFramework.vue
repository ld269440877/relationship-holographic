<template>
  <div class="p-4 sm:p-6 lg:p-8 space-y-8">
    <div class="flex flex-col items-start justify-between gap-4 sm:flex-row sm:gap-6">
      <div>
        <p class="text-sm font-semibold text-cyan-500 mb-2">Primitive Map / 元基础学习架构</p>
        <h1 class="text-3xl font-bold text-gray-800 dark:text-white">从 0/1 到高维关系系统</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-2 max-w-3xl">{{ framework?.axiom || '人性无限，学习必须分类；数图结合才能看得见也算得清。' }}</p>
        <p class="mt-2 max-w-3xl text-sm text-gray-500 dark:text-gray-400">按“看见事实 → 命名状态 → 识别关系任务 → 选择工具 → 生成回应 → 观察反馈 → 复盘迁移”学习，不背孤立话术。</p>
      </div>
      <button @click="load" class="btn-secondary w-full sm:w-auto">刷新</button>
    </div>

    <div v-if="loading" class="card text-center text-gray-500">加载元基础框架...</div>
    <div v-else-if="loadError" class="card text-center text-red-500">
      <p class="font-semibold">元基础框架加载失败</p>
      <p class="mt-2 text-sm">{{ loadError }}</p>
      <button class="btn-secondary mt-4" @click="load">重试</button>
    </div>

    <template v-else-if="framework">
      <section class="card">
        <div class="mb-5 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 class="text-xl font-bold text-gray-800 dark:text-white">关系动力学学习地图</h2>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">把抽象能力拆成连续动作，学习者知道自己正在练哪一步。</p>
          </div>
          <span class="text-sm text-gray-400">v{{ framework.version }}</span>
        </div>
        <div class="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-7">
          <div
            v-for="step in framework.learning_map"
            :key="step.step"
            class="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800"
          >
            <span class="flex h-8 w-8 items-center justify-center rounded-md bg-gray-900 text-sm font-bold text-white">{{ step.step }}</span>
            <h3 class="mt-3 font-bold text-gray-800 dark:text-white">{{ step.name }}</h3>
            <p class="mt-2 text-sm leading-6 text-gray-500 dark:text-gray-400">{{ step.action }}</p>
          </div>
        </div>
      </section>

      <section class="card">
        <div class="mb-5 flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h2 class="text-xl font-bold text-gray-800 dark:text-white">主线素材库</h2>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">每条主线都给出术语、信号、情绪词、程度、场景、对话模板、反模式和练习。</p>
          </div>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="item in framework.material_library"
              :key="item.id"
              type="button"
              class="rounded-md px-3 py-2 text-xs font-semibold transition-colors"
              :class="activeMaterialId === item.id ? 'bg-cyan-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'"
              @click="activeMaterialId = item.id"
            >
              {{ item.name }}
            </button>
          </div>
        </div>

        <div v-if="activeMaterial" class="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
          <div class="space-y-4">
            <div class="rounded-lg border border-cyan-100 bg-cyan-50 p-4 dark:border-cyan-900/50 dark:bg-cyan-950/20">
              <p class="text-sm font-semibold text-cyan-700 dark:text-cyan-200">{{ activeMaterial.purpose }}</p>
              <p class="mt-3 text-sm leading-7 text-gray-700 dark:text-gray-300">{{ activeMaterial.beginner_definition }}</p>
              <p class="mt-2 text-sm leading-7 text-gray-600 dark:text-gray-400">{{ activeMaterial.expert_definition }}</p>
            </div>

            <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
                <h3 class="font-bold text-gray-800 dark:text-white">可观察信号</h3>
                <div class="mt-3 flex flex-wrap gap-2">
                  <span v-for="signal in activeMaterial.signals" :key="signal" class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">{{ signal }}</span>
                </div>
              </div>
              <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
                <h3 class="font-bold text-gray-800 dark:text-white">情绪与状态词</h3>
                <div class="mt-3 flex flex-wrap gap-2">
                  <span v-for="word in activeMaterial.emotion_words" :key="word" class="rounded bg-rose-50 px-2 py-1 text-xs text-rose-700 dark:bg-rose-950/30 dark:text-rose-200">{{ word }}</span>
                </div>
              </div>
            </div>

            <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
              <h3 class="font-bold text-gray-800 dark:text-white">程度刻度</h3>
              <div class="mt-3 grid grid-cols-1 gap-2 md:grid-cols-5">
                <div v-for="degree in activeMaterial.degree_scale" :key="degree.level" class="rounded bg-gray-50 p-3 dark:bg-gray-800">
                  <p class="text-sm font-bold text-gray-800 dark:text-white">D{{ degree.level }} · {{ degree.label }}</p>
                  <p class="mt-1 text-xs leading-5 text-gray-500 dark:text-gray-400">{{ degree.cue }}</p>
                </div>
              </div>
            </div>

            <div v-if="activeMaterial.technique_cards?.length" class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
              <div class="mb-4">
                <h3 class="font-bold text-gray-800 dark:text-white">关键技术手册</h3>
                <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">把深度连接拆成可观察词、可执行步骤、程度刻度和可直接练习的句式。</p>
              </div>
              <div class="space-y-4">
                <article
                  v-for="card in activeMaterial.technique_cards"
                  :key="card.id"
                  class="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-900"
                >
                  <div class="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
                    <div>
                      <h4 class="font-bold text-gray-800 dark:text-white">{{ card.name }}</h4>
                      <p class="mt-1 text-sm leading-6 text-gray-600 dark:text-gray-300">{{ card.goal }}</p>
                    </div>
                    <span class="rounded bg-cyan-50 px-2 py-1 text-xs font-semibold text-cyan-700 dark:bg-cyan-950/30 dark:text-cyan-200">{{ card.id }}</span>
                  </div>

                  <div class="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
                    <div>
                      <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">术语</p>
                      <div class="mt-2 flex flex-wrap gap-2">
                        <span v-for="term in card.terms" :key="term" class="rounded bg-gray-100 px-2 py-1 text-xs text-gray-600 dark:bg-gray-800 dark:text-gray-300">{{ term }}</span>
                      </div>
                    </div>
                    <div>
                      <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">关键词</p>
                      <div class="mt-2 flex flex-wrap gap-2">
                        <span v-for="keyword in card.keywords" :key="keyword" class="rounded bg-amber-50 px-2 py-1 text-xs text-amber-700 dark:bg-amber-950/30 dark:text-amber-200">{{ keyword }}</span>
                      </div>
                    </div>
                  </div>

                  <div class="mt-4 grid grid-cols-1 gap-3 xl:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
                    <div class="rounded bg-gray-50 p-3 dark:bg-gray-800">
                      <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">具体步骤</p>
                      <ol class="mt-2 space-y-2 text-sm leading-6 text-gray-700 dark:text-gray-300">
                        <li v-for="(step, index) in card.steps" :key="step" class="flex gap-2">
                          <span class="font-semibold text-cyan-600 dark:text-cyan-300">{{ index + 1 }}.</span>
                          <span>{{ step }}</span>
                        </li>
                      </ol>
                    </div>
                    <div class="rounded bg-gray-50 p-3 dark:bg-gray-800">
                      <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">程度与刹车线</p>
                      <div class="mt-2 grid grid-cols-1 gap-2 md:grid-cols-5 xl:grid-cols-1">
                        <div v-for="degree in card.degree_scale" :key="degree.level" class="rounded bg-white p-2 dark:bg-gray-900">
                          <p class="text-xs font-bold text-gray-800 dark:text-white">D{{ degree.level }} · {{ degree.label }}</p>
                          <p class="mt-1 text-xs leading-5 text-gray-500 dark:text-gray-400">{{ degree.cue }}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div class="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
                    <div class="rounded border border-emerald-100 bg-emerald-50 p-3 dark:border-emerald-900/40 dark:bg-emerald-950/20">
                      <p class="text-xs font-semibold text-emerald-700 dark:text-emerald-300">可用句式</p>
                      <ul class="mt-2 space-y-2 text-sm leading-6 text-gray-700 dark:text-gray-300">
                        <li v-for="pattern in card.sentence_patterns" :key="pattern">· {{ pattern }}</li>
                      </ul>
                    </div>
                    <div class="rounded border border-red-100 bg-red-50 p-3 dark:border-red-900/40 dark:bg-red-950/20">
                      <p class="text-xs font-semibold text-red-600 dark:text-red-300">禁区</p>
                      <ul class="mt-2 space-y-2 text-sm leading-6 text-gray-700 dark:text-gray-300">
                        <li v-for="pattern in card.bad_patterns" :key="pattern">· {{ pattern }}</li>
                      </ul>
                    </div>
                  </div>

                  <div v-if="card.comparisons?.length" class="mt-4 rounded-lg border border-blue-100 bg-blue-50 p-3 dark:border-blue-900/40 dark:bg-blue-950/20">
                    <p class="text-xs font-semibold text-blue-700 dark:text-blue-300">开放式 / 封闭式对比</p>
                    <div class="mt-3 space-y-3">
                      <div v-for="comparison in card.comparisons" :key="comparison.axis" class="rounded bg-white p-3 dark:bg-gray-900">
                        <p class="text-sm font-bold text-gray-800 dark:text-white">{{ comparison.axis }}</p>
                        <div class="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-3">
                          <div>
                            <p class="text-xs font-semibold text-emerald-700 dark:text-emerald-300">开放式</p>
                            <p class="mt-1 text-xs leading-5 text-gray-600 dark:text-gray-300">{{ comparison.open_question }}</p>
                          </div>
                          <div>
                            <p class="text-xs font-semibold text-amber-700 dark:text-amber-300">封闭式</p>
                            <p class="mt-1 text-xs leading-5 text-gray-600 dark:text-gray-300">{{ comparison.closed_question }}</p>
                          </div>
                          <div>
                            <p class="text-xs font-semibold text-blue-700 dark:text-blue-300">使用规则</p>
                            <p class="mt-1 text-xs leading-5 text-gray-600 dark:text-gray-300">{{ comparison.use_rule }}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div v-if="card.feeling_spectrum?.length" class="mt-4 rounded-lg border border-rose-100 bg-rose-50 p-3 dark:border-rose-900/40 dark:bg-rose-950/20">
                    <p class="text-xs font-semibold text-rose-700 dark:text-rose-300">感受词谱与身体线索</p>
                    <div class="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
                      <div v-for="group in card.feeling_spectrum" :key="group.family" class="rounded bg-white p-3 dark:bg-gray-900">
                        <p class="text-sm font-bold text-gray-800 dark:text-white">{{ group.family }}</p>
                        <div class="mt-2 flex flex-wrap gap-2">
                          <span v-for="word in group.words" :key="word" class="rounded bg-rose-100 px-2 py-1 text-xs text-rose-700 dark:bg-rose-900/40 dark:text-rose-200">{{ word }}</span>
                        </div>
                        <p class="mt-3 text-xs font-semibold text-gray-500 dark:text-gray-400">身体线索</p>
                        <p class="mt-1 text-xs leading-5 text-gray-600 dark:text-gray-300">{{ group.body_cues.join(' / ') }}</p>
                        <p class="mt-3 text-xs font-semibold text-gray-500 dark:text-gray-400">需要信号</p>
                        <p class="mt-1 text-xs leading-5 text-gray-600 dark:text-gray-300">{{ group.need_signal }}</p>
                      </div>
                    </div>
                  </div>
                </article>
              </div>
            </div>
          </div>

          <div class="space-y-4">
            <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
              <h3 class="font-bold text-gray-800 dark:text-white">场景与对比回应</h3>
              <p class="mt-2 text-sm leading-7 text-gray-600 dark:text-gray-300">{{ activeMaterial.scene_example.context }}</p>
              <div class="mt-3 grid grid-cols-1 gap-3">
                <div class="rounded border border-red-100 bg-red-50 p-3 dark:border-red-900/40 dark:bg-red-950/20">
                  <p class="text-xs font-semibold text-red-600 dark:text-red-300">低质量回应</p>
                  <p class="mt-1 text-sm text-gray-700 dark:text-gray-300">{{ activeMaterial.scene_example.poor_response }}</p>
                </div>
                <div class="rounded border border-emerald-100 bg-emerald-50 p-3 dark:border-emerald-900/40 dark:bg-emerald-950/20">
                  <p class="text-xs font-semibold text-emerald-700 dark:text-emerald-300">更好回应</p>
                  <p class="mt-1 text-sm leading-6 text-gray-700 dark:text-gray-300">{{ activeMaterial.scene_example.better_response }}</p>
                </div>
              </div>
              <p class="mt-3 text-xs leading-5 text-gray-500 dark:text-gray-400">{{ activeMaterial.scene_example.why }}</p>
            </div>

            <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
              <h3 class="font-bold text-gray-800 dark:text-white">完整对话骨架</h3>
              <div class="mt-3 space-y-2">
                <div v-for="turn in activeMaterial.dialogue_template" :key="`${turn.speaker}-${turn.line}`" class="rounded bg-gray-50 p-3 text-sm dark:bg-gray-800">
                  <span class="font-semibold text-gray-800 dark:text-white">{{ turn.speaker }}：</span>
                  <span class="text-gray-600 dark:text-gray-300">{{ turn.line }}</span>
                </div>
              </div>
            </div>

            <div class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
              <h3 class="font-bold text-gray-800 dark:text-white">反模式与练习</h3>
              <div class="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2">
                <div>
                  <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">不要这样</p>
                  <ul class="mt-2 space-y-1 text-sm text-gray-600 dark:text-gray-300">
                    <li v-for="pattern in activeMaterial.anti_patterns" :key="pattern">· {{ pattern }}</li>
                  </ul>
                </div>
                <div>
                  <p class="text-xs font-semibold text-gray-500 dark:text-gray-400">练习任务</p>
                  <ul class="mt-2 space-y-1 text-sm text-gray-600 dark:text-gray-300">
                    <li v-for="drill in activeMaterial.practice_drills" :key="drill">· {{ drill }}</li>
                  </ul>
                </div>
              </div>
              <p class="mt-3 rounded bg-gray-50 p-3 text-xs leading-5 text-gray-500 dark:bg-gray-800 dark:text-gray-400">{{ activeMaterial.quality_contract }}</p>
            </div>
          </div>
        </div>
      </section>

      <section class="grid grid-cols-1 gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div class="card">
          <h2 class="mb-4 text-xl font-bold text-gray-800 dark:text-white">功能模块模板</h2>
          <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <div v-for="template in framework.module_templates" :key="template.module" class="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
              <h3 class="font-bold text-gray-800 dark:text-white">{{ template.module }}</h3>
              <p class="mt-2 text-sm leading-6 text-gray-500 dark:text-gray-400">{{ template.design_rule }}</p>
              <div class="mt-3 flex flex-wrap gap-2">
                <span v-for="tab in template.tabs" :key="tab" class="rounded bg-cyan-50 px-2 py-1 text-xs text-cyan-700 dark:bg-cyan-950/30 dark:text-cyan-200">{{ tab }}</span>
              </div>
              <div class="mt-3 flex flex-wrap gap-2">
                <span v-for="field in template.required_fields" :key="field" class="rounded bg-gray-100 px-2 py-1 text-[11px] text-gray-500 dark:bg-gray-800 dark:text-gray-400">{{ field }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <h2 class="mb-4 text-xl font-bold text-gray-800 dark:text-white">质量门禁</h2>
          <div class="space-y-3">
            <div v-for="gate in framework.quality_gates" :key="gate.gate" class="rounded-lg border border-gray-200 p-3 dark:border-gray-700">
              <p class="font-semibold text-gray-800 dark:text-white">{{ gate.gate }}</p>
              <p class="mt-1 text-sm leading-6 text-gray-500 dark:text-gray-400">{{ gate.rule }}</p>
            </div>
          </div>
        </div>
      </section>

      <section class="card">
        <div class="flex items-center justify-between gap-4 mb-5">
          <div>
            <h2 class="text-xl font-bold text-gray-800 dark:text-white">底层粒度阶梯</h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">每一阶都同时给出问题、单位和图形直觉。</p>
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-5 gap-3">
          <div
            v-for="node in framework.primitive_ladder"
            :key="node.level"
            class="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 p-4 min-h-[150px]"
          >
            <div class="flex items-center justify-between mb-3">
              <span class="w-8 h-8 rounded-md bg-cyan-500 text-white flex items-center justify-center font-bold">{{ node.level }}</span>
              <span class="text-xs text-gray-400">{{ node.unit }}</span>
            </div>
            <h3 class="font-bold text-gray-800 dark:text-white">{{ node.name }}</h3>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">{{ node.question }}</p>
            <p class="text-xs text-cyan-600 dark:text-cyan-300 mt-3">{{ node.visual }}</p>
          </div>
        </div>
      </section>

      <section class="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div class="card xl:col-span-2">
          <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4">分类治学地图</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div
              v-for="branch in framework.classification_tree"
              :key="branch.id"
              class="rounded-lg bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-4"
            >
              <div class="flex items-center justify-between gap-3 mb-3">
                <h3 class="font-bold text-gray-800 dark:text-white">{{ branch.name }}</h3>
                <span class="text-xs text-gray-400">{{ branch.axis.join(' / ') }}</span>
              </div>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="child in branch.children"
                  :key="child"
                  class="px-2 py-1 rounded-md bg-gray-100 dark:bg-gray-700 text-xs text-gray-600 dark:text-gray-300"
                >
                  {{ child }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <div class="card">
          <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4">5W2H 元问题</h2>
          <div class="space-y-3">
            <div v-for="item in framework.five_w_two_h" :key="item.key" class="border-l-4 border-cyan-500 pl-3">
              <p class="font-semibold text-gray-800 dark:text-white">{{ item.label }}</p>
              <p class="text-sm text-gray-500 dark:text-gray-400">{{ item.question }}</p>
            </div>
          </div>
        </div>
      </section>

      <section class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <div class="card">
          <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4">数图结合组件</h2>
          <div class="space-y-4">
            <div v-for="component in framework.visual_components" :key="component.id" class="rounded-lg bg-gray-50 dark:bg-gray-800 p-4">
              <div class="flex items-center justify-between gap-4">
                <h3 class="font-bold text-gray-800 dark:text-white">{{ component.name }}</h3>
                <span class="text-xs text-cyan-600 dark:text-cyan-300">{{ component.visual }}</span>
              </div>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">{{ component.training_use }}</p>
              <div class="flex flex-wrap gap-2 mt-3">
                <span v-for="metric in component.numeric" :key="metric" class="px-2 py-1 rounded bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300 text-xs">{{ metric }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div class="card">
            <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4">三性三管理</h2>
            <div class="space-y-4">
              <div v-for="item in framework.three_natures_management" :key="item.nature" class="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
                <p class="font-bold text-gray-800 dark:text-white">人性{{ item.nature }} · {{ item.management }}</p>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-2">{{ item.relationship_use }}</p>
              </div>
            </div>
          </div>

          <div class="card">
            <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4">熟能生巧路径</h2>
            <div class="space-y-3">
              <div v-for="stage in framework.mastery_stages" :key="stage.level" class="flex gap-3">
                <span class="w-7 h-7 rounded bg-gray-900 text-white text-xs flex items-center justify-center shrink-0">{{ stage.level }}</span>
                <div>
                  <p class="font-semibold text-gray-800 dark:text-white">{{ stage.name }}：{{ stage.definition }}</p>
                  <p class="text-sm text-gray-500 dark:text-gray-400">{{ stage.test }}</p>
                </div>
              </div>
            </div>
          </div>

          <div class="card">
            <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4">安全问答模板</h2>
            <div class="space-y-3">
              <div v-for="q in framework.question_templates" :key="q.scene" class="rounded-lg bg-gray-50 dark:bg-gray-800 p-3">
                <p class="text-sm font-semibold text-gray-700 dark:text-gray-200">{{ q.scene }}</p>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ q.template }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { learningApi } from '@/utils/api'
import type { LearningFramework } from '@/utils/api'

const framework = ref<LearningFramework | null>(null)
const loading = ref(false)
const loadError = ref('')
const activeMaterialId = ref('')

const activeMaterial = computed(() => {
  const library = framework.value?.material_library || []
  return library.find((item) => item.id === activeMaterialId.value) || library[0]
})

watch(
  () => framework.value?.material_library,
  (library) => {
    if (!activeMaterialId.value && library?.length) {
      activeMaterialId.value = library[0].id
    }
  },
)

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    framework.value = await learningApi.framework()
  } catch (error) {
    framework.value = null
    loadError.value = error instanceof Error ? error.message : '无法读取元基础框架，请稍后重试。'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>
