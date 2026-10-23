<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { ApiError, eventUrl, researchApi, safeSourceUrl, type AgentEvent, type DecisionContext, type DecisionVerdict, type ResearchTask, type TaskStatus } from './api'

const eventTypes = ['task_queued', 'task_started', 'task_requeued', 'subgoals_initialized', 'step_evaluated', 'cancel_requested', 'task_finished']
const terminalStatuses = new Set<TaskStatus>(['completed', 'partial', 'failed', 'cancelled'])
const statusLabels: Record<TaskStatus, string> = {
  queued: '排队中', running: '研究中', completed: '已完成', partial: '部分完成',
  failed: '失败', cancelled: '已取消',
}

const goal = ref('')
const decisionMode = ref(false)
const useCase = ref('')
const mustHave = ref('')
const preferences = ref('')
const candidateProjects = ref('')
const tasks = ref<ResearchTask[]>([])
const selected = ref<ResearchTask | null>(null)
const timeline = ref<AgentEvent[]>([])
const error = ref('')
const notice = ref('')
const streamWarning = ref('')
const listBusy = ref(false)
const taskBusy = ref(false)
const startBusy = ref(false)
const cancelBusy = ref(false)
const seenIds = new Set<string>()
let stream: EventSource | null = null
let statusPoll: ReturnType<typeof setInterval> | null = null
let terminalRetry: ReturnType<typeof setInterval> | null = null
let selectionVersion = 0
let listVersion = 0
let disposed = false

const active = computed(() => selected.value && !terminalStatuses.has(selected.value.status))
const pendingCancellation = computed(() => Boolean(active.value && selected.value?.cancellation_requested))
const validGoal = computed(() => goal.value.trim().length > 0 && goal.value.trim().length <= 4000)
const verdictLabels: Record<DecisionVerdict, string> = {
  satisfied: '满足', not_satisfied: '不满足', unknown: '未知', conflicting: '证据冲突',
}

function parseEntries(value: string, label: string, maxCount: number): { entries: string[], error: string } {
  if (!value.trim()) return { entries: [], error: '' }
  const entries = value.trim().split(/\r?\n/).map((item) => item.trim())
  if (entries.length > maxCount) return { entries, error: `${label}最多 ${maxCount} 条。` }
  if (entries.some((item) => item.length < 1 || item.length > 200)) return { entries, error: `${label}每条需为 1–200 字，不能留空行。` }
  if (new Set(entries.map((item) => item.toLocaleLowerCase())).size !== entries.length) {
    return { entries, error: `${label}不能有重复条目。` }
  }
  return { entries, error: '' }
}

const decisionInput = computed<{ context: DecisionContext | undefined, error: string }>(() => {
  if (!decisionMode.value) return { context: undefined, error: '' }
  const use_case = useCase.value.trim()
  if (!use_case || use_case.length > 1000) return { context: undefined, error: '选型用途需为 1–1000 字。' }
  const hard = parseEntries(mustHave.value, '必须条件', 12)
  const soft = parseEntries(preferences.value, '偏好', 12)
  const candidates = parseEntries(candidateProjects.value, '候选项目', 8)
  const error = hard.error || soft.error || candidates.error
  if (error) return { context: undefined, error }
  return { context: {
    use_case,
    must_have: hard.entries,
    preferences: soft.entries,
    candidate_projects: candidates.entries,
  }, error: '' }
})
const validSubmission = computed(() => validGoal.value && !decisionInput.value.error)
const decisionReport = computed(() => selected.value?.report?.decision ?? null)
function candidateName(id: string): string {
  return selected.value?.report?.decision?.candidates.find((candidate) => candidate.candidate_id === id)?.label || id
}
const unfinishedItems = computed(() => {
  const lines = selected.value?.report?.markdown.split(/\r?\n/) ?? []
  const start = lines.findIndex((line) => line.trim() === '## Unknown or unfinished')
  if (start < 0) return []
  const rest = lines.slice(start + 1)
  const nextSection = rest.findIndex((line) => /^##\s/.test(line))
  return (nextSection < 0 ? rest : rest.slice(0, nextSection))
    .filter((line) => /^\s*-\s+/.test(line))
    .map((line) => line.replace(/^\s*-\s+/, '').trim())
    .filter((item) => item && item !== 'No remaining subgoal is recorded.')
})

function explainError(cause: unknown): string {
  return cause instanceof ApiError ? cause.message : '发生未知错误，请稍后重试。'
}

function closeStream(keepTerminalRetry = false): void {
  stream?.close()
  stream = null
  if (statusPoll) clearInterval(statusPoll)
  statusPoll = null
  if (!keepTerminalRetry) {
    if (terminalRetry) clearInterval(terminalRetry)
    terminalRetry = null
  }
}

function addEvent(event: AgentEvent): void {
  if (!event.event_id || event.task_id !== selected.value?.id || seenIds.has(event.event_id)) return
  seenIds.add(event.event_id)
  timeline.value.push(event)
}

function setUrlTask(id: string): void {
  const url = new URL(window.location.href)
  url.searchParams.set('task', id)
  history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`)
}

async function refreshList(): Promise<void> {
  const requestVersion = ++listVersion
  listBusy.value = true
  try {
    const latest = await researchApi.list()
    if (requestVersion !== listVersion || disposed) return
    // A terminal detail response can arrive before an in-flight list response.
    // Keep the selected task's terminal state visible in the recent list.
    const terminal = selected.value && terminalStatuses.has(selected.value.status) ? selected.value : null
    tasks.value = latest.map((task) => terminal && task.id === terminal.id ? terminal : task)
  } catch (cause) {
    if (requestVersion === listVersion && !disposed) error.value = explainError(cause)
  } finally {
    if (requestVersion === listVersion) listBusy.value = false
  }
}

async function reloadSelected(version: number, openStream = false): Promise<boolean> {
  const id = selected.value?.id
  if (!id) return false
  try {
    const task = await researchApi.get(id)
    if (version !== selectionVersion || disposed) return false
    selected.value = task
    tasks.value = tasks.value.map((recent) => recent.id === task.id ? task : recent)
    if (terminalStatuses.has(task.status)) closeStream(true)
    else if (openStream && !stream) connect(version)
    const traces = await researchApi.traces(id)
    if (version !== selectionVersion || disposed) return false
    const liveEvents = timeline.value.slice()
    timeline.value = []
    seenIds.clear()
    for (const event of traces) addEvent(event)
    for (const event of liveEvents) addEvent(event)
    return true
  } catch (cause) {
    if (version !== selectionVersion || disposed) return false
    error.value = explainError(cause)
    if (cause instanceof ApiError && cause.status === 404) {
      closeStream()
      selected.value = null
    }
    return false
  }
}

async function loadTerminal(version: number): Promise<void> {
  if (await reloadSelected(version)) {
    if (terminalRetry) clearInterval(terminalRetry)
    terminalRetry = null
    error.value = ''
    streamWarning.value = ''
    await refreshList()
    return
  }
  if (version !== selectionVersion || disposed || !selected.value || terminalRetry) return
  streamWarning.value = '任务已结束，正在重新加载报告与时间线。'
  let retrying = false
  let retries = 0
  terminalRetry = setInterval(() => {
    if (retrying || version !== selectionVersion || disposed || !selected.value) return
    retrying = true
    retries += 1
    void loadTerminal(version).finally(() => {
      retrying = false
      if (retries >= 3 && terminalRetry) {
        clearInterval(terminalRetry)
        terminalRetry = null
        streamWarning.value = '报告与时间线暂不可用，自动重试已结束。请点击刷新重试。'
      }
    })
  }, 5000)
}

function connect(version: number): void {
  const task = selected.value
  if (!task || terminalStatuses.has(task.status) || version !== selectionVersion) return
  closeStream()
  const source = new EventSource(eventUrl(task.id))
  stream = source
  for (const type of eventTypes) {
    source.addEventListener(type, (raw) => {
      if (version !== selectionVersion || source !== stream) return
      let event: AgentEvent
      try { event = JSON.parse((raw as MessageEvent).data) as AgentEvent } catch { return }
      if (event.event_type !== type || event.task_id !== task.id) return
      streamWarning.value = ''
      addEvent(event)
      if (type === 'task_finished') {
        closeStream()
        void loadTerminal(version)
      }
    })
  }
  source.onerror = () => {
    if (version !== selectionVersion || source !== stream) return
    streamWarning.value = '实时连接中断，正在重连；已收到的事件会按 ID 去重。'
    // EventSource resumes with Last-Event-ID. Refresh status to detect a terminal
    // task if the stream closed between persisted replay and subscription.
    void researchApi.get(task.id).then((latest) => {
      if (version !== selectionVersion || source !== stream) return
      selected.value = latest
      if (terminalStatuses.has(latest.status)) {
        closeStream()
        streamWarning.value = ''
        void loadTerminal(version)
      }
    }).catch((cause: unknown) => {
      if (version !== selectionVersion || source !== stream) return
      error.value = explainError(cause)
      if (cause instanceof ApiError && cause.status === 404) closeStream()
    })
  }
  // A development proxy or broken connection can leave EventSource open without
  // delivering an error. Poll the existing detail API to detect terminal state
  // and restore the stream after a temporary API outage.
  let pollFailed = false
  let polling = false
  statusPoll = setInterval(() => {
    if (polling || version !== selectionVersion || source !== stream) return
    polling = true
    void researchApi.get(task.id).then(async (latest) => {
      if (version !== selectionVersion || source !== stream) return
      selected.value = latest
      tasks.value = tasks.value.map((recent) => recent.id === latest.id ? latest : recent)
      if (terminalStatuses.has(latest.status)) {
        closeStream()
        streamWarning.value = ''
        await loadTerminal(version)
      } else if (pollFailed) {
        pollFailed = false
        streamWarning.value = ''
        if (await reloadSelected(version)) connect(version)
      }
    }).catch((cause: unknown) => {
      if (version !== selectionVersion || source !== stream) return
      pollFailed = true
      streamWarning.value = '实时连接中断，正在重连；已收到的事件会按 ID 去重。'
      if (cause instanceof ApiError && cause.status === 404) {
        error.value = explainError(cause)
        closeStream()
      }
    }).finally(() => { polling = false })
  }, 5000)
}

async function chooseTask(task: ResearchTask): Promise<void> {
  closeStream()
  const version = ++selectionVersion
  selected.value = task
  timeline.value = []
  seenIds.clear()
  error.value = ''
  notice.value = ''
  streamWarning.value = ''
  setUrlTask(task.id)
  taskBusy.value = true
  try {
    await reloadSelected(version, true)
  } finally {
    if (version === selectionVersion) taskBusy.value = false
  }
}

async function start(): Promise<void> {
  if (!validSubmission.value || startBusy.value) return
  startBusy.value = true
  error.value = ''
  notice.value = ''
  try {
    const created = await researchApi.create(goal.value.trim(), decisionInput.value.context)
    goal.value = ''
    decisionMode.value = false
    useCase.value = ''
    mustHave.value = ''
    preferences.value = ''
    candidateProjects.value = ''
    await chooseTask(created)
    void refreshList()
  } catch (cause) {
    error.value = explainError(cause)
  } finally {
    startBusy.value = false
  }
}

async function cancel(): Promise<void> {
  const task = selected.value
  if (!task || !active.value || cancelBusy.value) return
  cancelBusy.value = true
  error.value = ''
  try {
    const result = await researchApi.cancel(task.id)
    notice.value = result.cancelled || result.cancellation_requested ? '取消请求已发送，等待任务结束。' : '任务已结束，无法取消。'
    await reloadSelected(selectionVersion)
    await refreshList()
  } catch (cause) {
    error.value = explainError(cause)
  } finally {
    cancelBusy.value = false
  }
}

async function refresh(): Promise<void> {
  error.value = ''
  await refreshList()
  if (selected.value) {
    const version = selectionVersion
    await reloadSelected(version, true)
  }
}

onMounted(async () => {
  const initialVersion = selectionVersion
  await refreshList()
  if (disposed || selected.value || selectionVersion !== initialVersion) return
  const requested = new URLSearchParams(window.location.search).get('task')
  const initial = requested
    ? tasks.value.find((task) => task.id === requested)
    : tasks.value[0]
  if (initial) await chooseTask(initial)
  else if (requested) {
    // Preserve the informative 404 from the task endpoint when a bookmarked ID
    // is no longer in the recent task list.
    await chooseTask({ id: requested, goal: '', status: 'queued', error_message: null,
      created_at: '', updated_at: '', completion_level: null, stop_reason: null, report: null })
  }
})
onUnmounted(() => { disposed = true; ++selectionVersion; closeStream() })
</script>

<template>
  <div class="shell">
    <header class="topbar">
      <div class="brand"><span class="brand-mark">A</span><div><strong>Adaptive Research Agent</strong><small>研究工作台</small></div></div>
      <span class="environment">本地演示 · V1</span>
    </header>

    <main class="layout">
      <section class="workspace" aria-labelledby="page-title">
        <div class="intro"><span class="eyebrow">RESEARCH WORKSPACE</span><h1 id="page-title">提出问题，追踪研究过程。</h1><p>输入一个具体目标，查看代理的执行时间线与有来源的结论。</p></div>

        <form class="composer" @submit.prevent="start">
          <label for="goal">研究目标</label>
          <textarea id="goal" v-model="goal" rows="3" maxlength="4000" placeholder="例如：比较三个开源浏览器自动化项目的功能与适用场景" :disabled="startBusy" />
          <label class="decision-toggle" for="decision-mode"><input id="decision-mode" v-model="decisionMode" type="checkbox" :disabled="startBusy" />加入 Python 开源选型条件</label>
          <div v-if="decisionMode" class="decision-inputs" data-test="decision-inputs">
            <p class="muted">以下内容是您提供的约束。每项一行；候选名称只是待核验标识，不代表官方身份已确认。</p>
            <label for="use-case">使用场景 <span aria-hidden="true">*</span></label>
            <textarea id="use-case" v-model="useCase" rows="2" maxlength="1000" :disabled="startBusy" placeholder="团队要解决什么问题？" />
            <label for="must-have">必须条件（最多 12 条）</label>
            <textarea id="must-have" v-model="mustHave" rows="3" :disabled="startBusy" placeholder="每行一条必须满足的条件" />
            <label for="preferences">偏好（最多 12 条）</label>
            <textarea id="preferences" v-model="preferences" rows="3" :disabled="startBusy" placeholder="每行一条可权衡的偏好" />
            <label for="candidate-projects">已知候选项目（最多 8 个，可留空）</label>
            <textarea id="candidate-projects" v-model="candidateProjects" rows="3" :disabled="startBusy" placeholder="每行一个项目标识；留空可由 Agent 发现候选" />
            <p v-if="decisionInput.error" class="input-error" role="alert">{{ decisionInput.error }}</p>
          </div>
          <div class="composer-actions"><small>{{ goal.trim().length }} / 4000 字</small><button class="primary" type="submit" :disabled="!validSubmission || startBusy">{{ startBusy ? '正在创建…' : '开始研究' }}</button></div>
        </form>

        <div v-if="error" class="alert error" role="alert">{{ error }}</div>
        <div v-if="notice" class="alert notice" role="status">{{ notice }}</div>

        <section class="task-panel" aria-labelledby="current-title">
          <div class="section-head"><div><span class="eyebrow">CURRENT TASK</span><h2 id="current-title">当前任务</h2></div><button class="quiet" type="button" :disabled="listBusy || taskBusy" @click="refresh">{{ listBusy || taskBusy ? '加载中…' : '刷新' }}</button></div>
          <div v-if="taskBusy" class="empty" role="status">正在加载任务与时间线…</div>
          <div v-else-if="!selected" class="empty">还没有任务。输入研究目标后即可开始。</div>
          <template v-else>
            <div class="task-summary"><div><span class="status" :class="selected.status">{{ pendingCancellation ? '取消中' : statusLabels[selected.status] }}</span><h3>{{ selected.goal || selected.id }}</h3><small>创建于 {{ new Date(selected.created_at).toLocaleString('zh-CN') }}</small></div><button v-if="active" class="danger" data-test="cancel" type="button" :disabled="cancelBusy || pendingCancellation" @click="cancel">{{ pendingCancellation ? '等待取消完成' : cancelBusy ? '正在请求取消…' : '取消任务' }}</button></div>
            <p v-if="selected.error_message" class="task-error">{{ selected.error_message }}</p>
            <p v-if="selected.stop_reason" class="muted">结束原因：{{ selected.stop_reason }}</p>
            <p v-if="streamWarning" class="connection" role="status">{{ streamWarning }}</p>
            <div class="two-column">
              <section aria-labelledby="timeline-title"><h3 id="timeline-title">执行时间线 <span class="count">{{ timeline.length }}</span></h3><p v-if="timeline.length === 0" class="empty-small">等待研究事件…</p><ol v-else class="timeline"><li v-for="event in timeline" :key="event.event_id"><span class="timeline-dot"></span><div><small>{{ new Date(event.timestamp).toLocaleTimeString('zh-CN') }} · {{ event.event_type === 'step_evaluated' ? `第 ${event.step + 1} 步` : '任务事件' }}</small><p>{{ event.message || event.event_type }}</p></div></li></ol></section>
              <section aria-labelledby="report-title"><h3 id="report-title">研究报告</h3><div v-if="selected.report" class="report"><h4>{{ selected.report.title }}</h4><p>{{ selected.report.summary }}</p><template v-if="selected.report.findings.length"><h5>发现</h5><article v-for="finding in selected.report.findings" :key="finding.name"><strong>{{ finding.name }}</strong><p>{{ finding.description }}</p><ul v-if="finding.source_urls.length" class="source-list"><li v-for="url in finding.source_urls" :key="url"><a v-if="safeSourceUrl(url)" :href="safeSourceUrl(url)" target="_blank" rel="noopener noreferrer">{{ url }}</a></li></ul></article></template><h5>对比</h5><p>{{ selected.report.comparison }}</p><h5>建议</h5><p>{{ selected.report.recommendation }}</p><template v-if="unfinishedItems.length"><h5>待核实或未完成</h5><ul><li v-for="item in unfinishedItems" :key="item">{{ item }}</li></ul></template><h5>来源</h5><ul class="source-list"><li v-for="url in selected.report.sources" :key="url"><a v-if="safeSourceUrl(url)" :href="safeSourceUrl(url)" target="_blank" rel="noopener noreferrer">{{ url }}</a></li></ul><p v-if="!selected.report.sources.length" class="muted">暂无来源。</p></div><p v-else class="empty-small">{{ active ? '研究进行中，报告完成后显示。' : '此任务没有可显示的报告。' }}</p></section>
            </div>
            <section v-if="decisionReport" class="decision-report" aria-labelledby="decision-title" data-test="decision-report">
              <h3 id="decision-title">选型决策记录</h3>
              <p class="verification-note">机器准入的候选分析，待人工打开官方来源逐条核实；不计作正式评测通过。</p>
              <p><strong>使用场景：</strong>{{ decisionReport.use_case }}</p>
              <div class="decision-constraints">
                <div><h4>必须条件</h4><ul v-if="decisionReport.must_have.length"><li v-for="item in decisionReport.must_have" :key="item">{{ item }}</li></ul><p v-else class="muted">未提供。</p></div>
                <div><h4>偏好</h4><ul v-if="decisionReport.preferences.length"><li v-for="item in decisionReport.preferences" :key="item">{{ item }}</li></ul><p v-else class="muted">未提供。</p></div>
              </div>
              <h4>候选与依据矩阵</h4>
              <ul v-if="decisionReport.candidates.length" class="candidate-list"><li v-for="candidate in decisionReport.candidates" :key="candidate.candidate_id"><strong>{{ candidate.label }}</strong><small>{{ candidate.origin === 'user' ? '用户提供的待核验标识' : 'Agent 发现的候选' }}<span v-if="candidate.verified_subject"> · 记录主体：{{ candidate.verified_subject }}</span></small></li></ul>
              <p v-else class="muted">尚无候选。</p>
              <div v-if="decisionReport.matrix.length" class="matrix-scroll"><table class="decision-matrix"><caption>每项判断均需核对 fact ID 和来源；“满足”仍待人工核源。</caption><thead><tr><th scope="col">候选</th><th scope="col">条件</th><th scope="col">判断</th><th scope="col">理由及事实</th></tr></thead><tbody><tr v-for="(row, index) in decisionReport.matrix" :key="`${row.candidate_id}-${row.condition_type}-${index}`"><th scope="row">{{ candidateName(row.candidate_id) }}</th><td><small>{{ row.condition_type === 'must_have' ? '必须' : '偏好' }}</small><br />{{ row.condition }}</td><td><span class="verdict" :class="row.verdict">{{ verdictLabels[row.verdict] }}</span></td><td>{{ row.reason }}<small v-if="row.supporting_fact_ids.length" class="fact-ids">支持 fact ID：{{ row.supporting_fact_ids.join('、') }}</small><small v-if="row.contradicting_fact_ids.length" class="fact-ids">反证 fact ID：{{ row.contradicting_fact_ids.join('、') }}</small><small v-if="!row.supporting_fact_ids.length && !row.contradicting_fact_ids.length" class="fact-ids">无准入事实</small></td></tr></tbody></table></div>
              <p v-else class="muted">尚无可展示的条件矩阵。</p>
              <div v-if="decisionReport.evidence_facts?.length" class="decision-evidence" data-test="decision-evidence"><h4>引用事实</h4><ul><li v-for="fact in decisionReport.evidence_facts" :key="fact.fact_id"><strong>{{ fact.fact_id }} · {{ fact.subject }}</strong><p>{{ fact.excerpt }}</p><small>抓取时间：{{ new Date(fact.observed_at).toLocaleString('zh-CN') }}</small><a v-if="safeSourceUrl(fact.source_url)" :href="safeSourceUrl(fact.source_url)" target="_blank" rel="noopener noreferrer">{{ fact.source_url }}</a></li></ul></div>
              <div v-if="decisionReport.unknowns.length || decisionReport.conflicts.length" class="decision-gaps"><div v-if="decisionReport.unknowns.length"><h4>未知项</h4><ul><li v-for="item in decisionReport.unknowns" :key="item">{{ item }}</li></ul></div><div v-if="decisionReport.conflicts.length"><h4>冲突</h4><ul><li v-for="item in decisionReport.conflicts" :key="item">{{ item }}</li></ul></div></div>
              <h4>条件化建议</h4>
              <div v-if="decisionReport.recommendation" class="decision-advice"><p><strong>{{ candidateName(decisionReport.recommendation.candidate_id) }}：</strong>{{ decisionReport.recommendation.text }}</p><p class="muted">支持 fact ID：{{ decisionReport.recommendation.supporting_fact_ids.join('、') || '无' }} · 待人工核实</p></div>
              <p v-else>{{ decisionReport.no_recommendation_reason || '当前证据不足，无法推荐。' }}</p>
              <div v-if="decisionReport.change_conditions.length"><h4>哪些条件会改变建议</h4><ul><li v-for="item in decisionReport.change_conditions" :key="item">{{ item }}</li></ul></div>
            </section>
          </template>
        </section>
      </section>
      <aside class="recent" aria-labelledby="recent-title"><div class="section-head"><div><span class="eyebrow">HISTORY</span><h2 id="recent-title">最近任务</h2></div><span class="count">{{ tasks.length }}</span></div><p v-if="listBusy && !tasks.length" class="empty-small">正在加载…</p><p v-else-if="!tasks.length" class="empty-small">尚无历史任务。</p><ul v-else class="recent-list"><li v-for="task in tasks" :key="task.id"><button type="button" :class="{ selected: task.id === selected?.id }" @click="chooseTask(task)"><span>{{ task.goal }}</span><small>{{ statusLabels[task.status] }} · {{ new Date(task.created_at).toLocaleDateString('zh-CN') }}</small></button></li></ul></aside>
    </main>
  </div>
</template>
