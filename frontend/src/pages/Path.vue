<template>
  <div class="p-4 sm:p-6 lg:p-8 space-y-8">
    <div class="flex flex-col items-start justify-between gap-4 sm:flex-row sm:gap-6">
      <div>
        <p class="text-sm font-semibold text-cyan-500 mb-2">Curriculum Graph / 八阶课程图谱</p>
        <h1 class="text-3xl font-bold text-gray-800 dark:text-white">从默认沉默到被爱的证据路线</h1>
        <p class="text-gray-500 dark:text-gray-400 mt-2 max-w-3xl">
          {{ graph?.axiom || '每一阶都必须有任务、评分、证据和晋级条件。' }}
        </p>
      </div>
      <button class="btn-secondary w-full sm:w-auto" @click="load">刷新</button>
    </div>

    <div v-if="loading" class="card text-center text-gray-500 dark:text-gray-400">加载八阶课程图谱...</div>
    <div v-else-if="loadError" class="card text-center text-red-500 dark:text-red-300">
      <p class="font-semibold">八阶课程图谱加载失败</p>
      <p class="mt-2 text-sm">{{ loadError }}</p>
      <button class="btn-secondary mt-4" @click="load">重试</button>
    </div>

    <template v-else-if="graph">
      <section class="grid grid-cols-1 xl:grid-cols-4 gap-6">
        <div class="card xl:col-span-3">
          <div class="flex items-center justify-between gap-4 mb-6">
            <div>
              <h2 class="text-xl font-bold text-gray-800 dark:text-white">当前关口：{{ graph.current_stage.name }}</h2>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ graph.current_stage.description }}</p>
            </div>
            <div class="text-right">
              <p class="text-4xl font-bold text-cyan-500">{{ graph.overall_progress }}%</p>
              <p class="text-xs text-gray-400">整体进度</p>
            </div>
          </div>

          <div class="relative">
            <div class="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-9 gap-3">
              <div
                v-for="node in graph.nodes"
                :key="node.id"
                class="relative rounded-lg border p-4 min-h-[190px]"
                :class="nodeClass(node)"
              >
                <div class="flex items-center justify-between mb-3">
                  <span class="w-9 h-9 rounded-md flex items-center justify-center font-bold" :class="badgeClass(node)">
                    {{ node.index }}
                  </span>
                  <span class="text-xs text-gray-400">{{ node.difficulty }}</span>
                </div>
                <h3 class="font-bold text-gray-800 dark:text-white leading-snug">{{ node.name }}</h3>
                <p class="text-xs text-cyan-600 dark:text-cyan-300 mt-2">{{ node.primitive }}</p>
                <div class="mt-4 h-2 rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                  <div class="h-full rounded-full bg-cyan-500" :style="{ width: `${node.progress}%` }"></div>
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400 mt-2">{{ node.progress }}% · {{ node.status }}</p>
              </div>
            </div>
          </div>
        </div>

        <aside class="card">
          <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4">下一步最小行动</h2>
          <p class="text-sm text-gray-500 dark:text-gray-400">{{ graph.practice_plan.minimum_action }}</p>
          <div class="mt-5 space-y-2">
            <p class="text-sm font-semibold text-gray-800 dark:text-white">本轮 drills</p>
            <div v-for="drill in graph.practice_plan.drills" :key="drill" class="rounded-lg bg-gray-50 dark:bg-gray-800 p-3 text-sm text-gray-600 dark:text-gray-300">
              {{ drill }}
            </div>
          </div>
        </aside>
      </section>

      <section class="card">
        <div class="mb-5 flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
          <div>
            <h2 class="text-xl font-bold text-gray-800 dark:text-white">这条路线到底在训练什么</h2>
            <p class="mt-1 max-w-3xl text-sm leading-6 text-gray-500 dark:text-gray-400">
              八阶路径不是恋爱技巧清单，而是把“看见信号、承接情绪、尊重边界、形成稳定行动”拆成可练、可评估、可复盘的能力路线。
            </p>
          </div>
          <div class="rounded-lg bg-cyan-50 px-4 py-3 text-sm text-cyan-700 dark:bg-cyan-950/30 dark:text-cyan-200">
            主线：观察 -> 命名 -> 验证 -> 行动 -> 复盘
          </div>
        </div>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          <div v-for="item in routePrinciples" :key="item.title" class="rounded-lg bg-gray-50 p-4 dark:bg-gray-800">
            <p class="font-semibold text-gray-800 dark:text-white">{{ item.title }}</p>
            <p class="mt-2 text-sm leading-6 text-gray-600 dark:text-gray-300">{{ item.body }}</p>
          </div>
        </div>
      </section>

      <section class="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div class="card xl:col-span-2">
          <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4">节点任务、概念与应用方法</h2>
          <div class="space-y-4">
            <div v-for="node in graph.nodes" :key="`${node.id}-detail`" class="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <div class="flex items-start justify-between gap-4">
                <div>
                  <h3 class="font-bold text-gray-800 dark:text-white">{{ node.name }}</h3>
                  <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ node.description }}</p>
                </div>
                <span class="px-2 py-1 rounded-md text-xs" :class="statusPillClass(node)">{{ node.status }}</span>
              </div>

              <div class="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
                <div class="rounded-lg bg-cyan-50 p-3 text-sm text-cyan-800 dark:bg-cyan-950/30 dark:text-cyan-200">
                  <p class="font-semibold">概念定义</p>
                  <p class="mt-1 leading-6">{{ stageGuide(node).definition }}</p>
                </div>
                <div class="rounded-lg bg-gray-50 p-3 text-sm text-gray-700 dark:bg-gray-800 dark:text-gray-200">
                  <p class="font-semibold">核心原则</p>
                  <p class="mt-1 leading-6">{{ stageGuide(node).principle }}</p>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-3 gap-3 mt-3">
                <div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-3">
                  <p class="text-xs text-gray-400 mb-1">工具</p>
                  <p class="text-sm text-gray-700 dark:text-gray-200">{{ node.tools.join(' / ') }}</p>
                </div>
                <div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-3">
                  <p class="text-xs text-gray-400 mb-1">晋级条件</p>
                  <p class="text-sm text-gray-700 dark:text-gray-200">{{ node.promotion_rule }}</p>
                </div>
                <div class="rounded-lg bg-gray-50 dark:bg-gray-800 p-3">
                  <p class="text-xs text-gray-400 mb-1">下一动作</p>
                  <p class="text-sm text-gray-700 dark:text-gray-200">{{ node.next_action }}</p>
                </div>
              </div>

              <div class="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-3">
                <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
                  <p class="mb-2 text-xs font-semibold text-gray-400">实践方法</p>
                  <ol class="space-y-1 text-sm leading-6 text-gray-700 dark:text-gray-200">
                    <li v-for="(step, index) in stageGuide(node).method" :key="`${node.id}-method-${step}`">{{ index + 1 }}. {{ step }}</li>
                  </ol>
                </div>
                <div class="rounded-lg bg-gray-50 p-3 dark:bg-gray-800">
                  <p class="mb-2 text-xs font-semibold text-gray-400">适用场景</p>
                  <div class="flex flex-wrap gap-2">
                    <span v-for="scene in stageGuide(node).scenes" :key="`${node.id}-${scene}`" class="rounded bg-blue-50 px-2 py-1 text-xs text-blue-700 dark:bg-blue-900/20 dark:text-blue-300">{{ scene }}</span>
                  </div>
                </div>
                <div class="rounded-lg bg-amber-50 p-3 text-sm text-amber-800 dark:bg-amber-900/20 dark:text-amber-200">
                  <p class="font-semibold">常见误区</p>
                  <p class="mt-1 leading-6">{{ stageGuide(node).pitfall }}</p>
                </div>
              </div>

              <div class="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
                <div class="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-300">
                  <p class="font-semibold">低质量做法</p>
                  <p class="mt-1 leading-6">{{ stageGuide(node).badExample }}</p>
                </div>
                <div class="rounded-lg bg-emerald-50 p-3 text-sm text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300">
                  <p class="font-semibold">更好做法</p>
                  <p class="mt-1 leading-6">{{ stageGuide(node).goodExample }}</p>
                </div>
              </div>

              <div class="mt-4 grid grid-cols-2 md:grid-cols-6 gap-2">
                <Metric label="训练" :value="node.evidence.attempts_count" />
                <Metric label="均分" :value="node.evidence.average_training_score" />
                <Metric label="错题" :value="node.evidence.open_mistakes" />
                <Metric label="会话" :value="node.evidence.partner_sessions" />
                <Metric label="轮次" :value="node.evidence.partner_turns" />
                <Metric label="阻断" :value="node.evidence.safety_blocks" />
              </div>
              <p class="text-sm text-cyan-600 dark:text-cyan-300 mt-3">{{ node.evidence.evidence_label }}</p>
              <div class="mt-3 rounded-lg bg-indigo-50 p-3 text-sm text-indigo-800 dark:bg-indigo-950/30 dark:text-indigo-200">
                <p class="font-semibold">本阶练习题</p>
                <p class="mt-1 leading-6">{{ stageGuide(node).drill }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div class="card">
            <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4">证据总览</h2>
            <div class="grid grid-cols-2 gap-3">
              <Metric label="训练提交" :value="graph.evidence_summary.training_attempts" />
              <Metric label="开放错题" :value="graph.evidence_summary.open_mistakes" />
              <Metric label="AI 会话" :value="graph.evidence_summary.partner_sessions" />
              <Metric label="对话事件" :value="graph.evidence_summary.partner_events" />
            </div>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-4">{{ graph.evidence_summary.principle }}</p>
          </div>

          <div class="card">
            <h2 class="text-xl font-bold text-gray-800 dark:text-white mb-4">图层说明</h2>
            <div class="space-y-3">
              <div v-for="layer in graph.visual_layers" :key="layer.id" class="rounded-lg bg-gray-50 dark:bg-gray-800 p-3">
                <p class="font-semibold text-gray-800 dark:text-white">{{ layer.name }}</p>
                <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ layer.use }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </template>

    <div v-else class="card text-center text-gray-500 dark:text-gray-400">暂无课程图谱数据</div>
  </div>
</template>

<script setup lang="ts">
import { defineComponent, h, onMounted, ref } from 'vue'
import { learningApi } from '@/utils/api'
import type { CurriculumGraph, CurriculumNode } from '@/utils/api'

const graph = ref<CurriculumGraph | null>(null)
const loading = ref(false)
const loadError = ref('')
const routePrinciples = [
  { title: '先证据后判断', body: '任何阶段都先看可观察事实：话语、行为、停顿、频率和边界变化，再提出轻假设。' },
  { title: '先安全后张力', body: '暧昧、幽默和推进都必须建立在可拒绝、可退出、可复盘的安全边界上。' },
  { title: '先小动作后人格结论', body: '训练目标不是给人贴标签，而是找到此刻最小、最温柔、最有效的下一步。' },
  { title: '先复盘后升级', body: '晋级不是靠感觉，而是靠训练提交、错题减少、AI 会话状态和安全记录共同构成证据。' },
]

interface StageGuide {
  definition: string
  principle: string
  method: string[]
  scenes: string[]
  pitfall: string
  badExample: string
  goodExample: string
  drill: string
}

async function load() {
  loading.value = true
  loadError.value = ''
  try {
    graph.value = await learningApi.curriculumGraph()
  } catch (error) {
    graph.value = null
    loadError.value = error instanceof Error ? error.message : '无法读取八阶课程图谱，请稍后重试。'
  } finally {
    loading.value = false
  }
}

function nodeClass(node: CurriculumNode) {
  if (node.is_current) return 'border-cyan-500 bg-cyan-50 dark:bg-cyan-900/20'
  if (node.is_completed) return 'border-green-300 bg-green-50 dark:bg-green-900/10'
  return 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900'
}

function badgeClass(node: CurriculumNode) {
  if (node.is_current) return 'bg-cyan-500 text-white'
  if (node.is_completed) return 'bg-green-500 text-white'
  return 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
}

function statusPillClass(node: CurriculumNode) {
  if (node.is_current) return 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300'
  if (node.is_completed) return 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300'
  return 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-300'
}

function stageGuide(node: CurriculumNode): StageGuide {
  const guides: Record<number, StageGuide> = {
    0: {
      definition: '默认沉默指注意力缩回自己脑内，只剩紧张和空白；本阶训练把注意力放回外部世界。',
      principle: '不急着有趣，先准确看见。能说出事实，就是从沉默里迈出的第一步。',
      method: ['扫一眼环境，记录 3 个事实', '把事实和脑补解释分开', '选一个低风险事实开口'],
      scenes: ['没话题', '初次见面', '紧张冷场'],
      pitfall: '把沉默解释成“我不行”，或为了破冰强行表演。',
      badExample: '“我脑子空白，我是不是很无聊？”',
      goodExample: '“刚才这首歌挺安静的，好像让这里没那么赶。”',
      drill: '今天任选一个场景，写下 3 个外部事实，再把其中 1 个改成一句自然开场。',
    },
    1: {
      definition: '信息阶训练事实交换：让彼此知道一点真实生活，但不把聊天变成审问。',
      principle: '事实问题要轻，自我暴露要小，问完要接住回答。',
      method: ['先问一个事实问题', '接一句自己的小事实', '从对方回答里延伸一个轻问题'],
      scenes: ['初识', '破冰', '日常聊天'],
      pitfall: '连续追问、查户口、急着证明自己懂。',
      badExample: '“你多大？哪里人？做什么？为什么单身？”',
      goodExample: '“你说最近很忙，是工作节奏变快了吗？我这周也有点被日程追着跑。”',
      drill: '把一个查户口式问题改成“事实 + 自我小暴露 + 轻延伸”。',
    },
    2: {
      definition: '情绪阶训练识别主情绪、强度和混合情绪，让回应先落到人的感受上。',
      principle: '情绪标注要用“可能/听起来”，给对方纠正空间。',
      method: ['找情绪词', '估计 1-10 强度', '用轻问句校准'],
      scenes: ['委屈', '失望', '压力支持'],
      pitfall: '直接下诊断，或把情绪当成对方的全部人格。',
      badExample: '“你就是太敏感了。”',
      goodExample: '“听起来你有点委屈，也可能是累了；我理解对了吗？”',
      drill: '从今天的一句对话中标出 1 个情绪词、1 个强度和 1 个校准问题。',
    },
    3: {
      definition: '感受阶训练主体体验：让对方感觉你站在一起，而不是站在对面评价。',
      principle: '先承接，再行动；不要用解决方案跳过对方的体验。',
      method: ['复述对方处境', '命名可能感受', '问需要陪伴还是建议'],
      scenes: ['倾诉', '压力', '亲密支持'],
      pitfall: '急着给建议，或者把共情说成套话。',
      badExample: '“这有什么，按我说的做就好了。”',
      goodExample: '“这事卡了这么久，难怪你会烦。你现在更想我听你说，还是一起想办法？”',
      drill: '把一句建议型回应改成“处境 + 感受 + 选择权”。',
    },
    4: {
      definition: '看见阶训练未明说线索：从停顿、回避、重复、边界试探里读出假设，但不把假设当事实。',
      principle: '看见不是猜透，真正的能力是轻验证。',
      method: ['列出信号', '提出 2 个以上假设', '用一句不施压的问题确认'],
      scenes: ['暧昧变化', '回复变慢', '冲突前兆'],
      pitfall: '把脑补当证据，或用试探逼对方表态。',
      badExample: '“你这样就是不在乎我了吧？”',
      goodExample: '“我感觉你这两天回复慢了些，是需要休息，还是我哪里理解错了？”',
      drill: '选一个微关系信号，写出 3 个可能解释，再写 1 个轻验证问题。',
    },
    5: {
      definition: '欣赏阶训练具体照亮：把喜欢落到行为、过程和特质，而不是空泛夸奖。',
      principle: '欣赏要具体、真实、不过度索取回应。',
      method: ['说具体行为', '说它对你的影响', '停在感谢，不追讨回报'],
      scenes: ['热恋', '长期关系', '修复后连接'],
      pitfall: '夸得太大、太油，或把欣赏变成索取。',
      badExample: '“你是世界上最好的人，所以你也要对我好。”',
      goodExample: '“你刚才没有打断我，我会觉得自己被认真听见了。”',
      drill: '写三句欣赏：行为欣赏、过程欣赏、特质欣赏，各不超过 25 字。',
    },
    6: {
      definition: '理解阶训练内在模型：从单次事件看到重复回路、触发点和未来需求。',
      principle: '理解不是替对方解释人生，而是为下一次互动减少伤害。',
      method: ['用 5W2H 复盘', '找重复触发点', '预测下一次需要什么支持'],
      scenes: ['反复争执', '长期磨合', '关系复盘'],
      pitfall: '用框架压人，或把一次事件升格成人格审判。',
      badExample: '“你一直这样，是因为你原生家庭有问题。”',
      goodExample: '“我们好像一忙就容易误会，下次可以先约定一个报平安方式。”',
      drill: '把一次小冲突按 Who/What/When/Why/How 写成 5W2H 复盘。',
    },
    7: {
      definition: '爱阶训练稳定行动：把理解变成持续、尊重边界、不忽冷忽热的行动。',
      principle: '爱不是强烈情绪，而是稳定、可预期、可协商的行动。',
      method: ['明确自己的底线', '选择一个稳定行动', '在压力中不控制对方'],
      scenes: ['承诺', '压力期', '长期连接'],
      pitfall: '用爱之名控制，或用牺牲制造亏欠。',
      badExample: '“我都是为你好，所以你必须听我的。”',
      goodExample: '“我在乎你，所以我会稳定出现；但你的选择我也尊重。”',
      drill: '列出一个你能稳定做到的行动，以及一个你不能越过的边界。',
    },
    8: {
      definition: '被爱阶训练接收与回馈：能看见别人对你的好，不把它立刻变成压力、亏欠或控制。',
      principle: '接收爱意不是还债，而是允许连接自然流动。',
      method: ['记录被爱的证据', '说出接收感受', '做一个自然回馈'],
      scenes: ['被关心', '收到支持', '稳定亲密'],
      pitfall: '麻木、怀疑、立刻还债，或把被爱当成失控。',
      badExample: '“你对我这么好，我压力好大。”',
      goodExample: '“谢谢你记得这件事，我有被放在心上的感觉。”',
      drill: '今天记录一条被爱的证据，用一句话表达接收，不急着补偿。',
    },
  }
  return guides[node.index] || guides[0]
}

const Metric = defineComponent({
  props: {
    label: { type: String, required: true },
    value: { type: [String, Number], required: true },
  },
  setup(props) {
    return () =>
      h('div', { class: 'rounded-lg bg-gray-50 dark:bg-gray-800 p-3' }, [
        h('p', { class: 'text-xs text-gray-400 mb-1' }, props.label),
        h('p', { class: 'text-lg font-bold text-gray-800 dark:text-white' }, String(props.value)),
      ])
  },
})

onMounted(load)
</script>
