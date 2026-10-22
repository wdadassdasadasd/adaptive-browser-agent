import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App.vue'

type Listener = (event: MessageEvent) => void

class FakeEventSource {
  static instances: FakeEventSource[] = []
  listeners = new Map<string, Listener>()
  onerror: (() => void) | null = null
  closed = false
  constructor(readonly url: string) { FakeEventSource.instances.push(this) }
  addEventListener(type: string, listener: EventListenerOrEventListenerObject) {
    this.listeners.set(type, listener as Listener)
  }
  close() { this.closed = true }
  emit(type: string, data: object) {
    this.listeners.get(type)?.({ data: JSON.stringify(data) } as MessageEvent)
  }
}

const task = (overrides: Record<string, unknown> = {}) => ({
  id: 'task-1', goal: '比较公开项目', status: 'running', error_message: null,
  created_at: '2026-10-12T10:00:00Z', updated_at: '2026-10-12T10:00:00Z',
  completion_level: null, stop_reason: null, report: null, ...overrides,
})
const trace = (id: string, type = 'task_started') => ({
  event_id: id, task_id: 'task-1', event_type: type, step: 0,
  timestamp: '2026-10-12T10:00:00Z', message: `事件 ${id}`, payload: {},
})
const response = (body: unknown, status = 200) => ({ ok: status < 400, status, json: async () => body })

let currentTask: ReturnType<typeof task>
let fetchCalls: string[]
beforeEach(() => {
  currentTask = task()
  fetchCalls = []
  FakeEventSource.instances = []
  vi.stubGlobal('EventSource', FakeEventSource)
  vi.stubGlobal('fetch', vi.fn(async (url: string, options?: RequestInit) => {
    fetchCalls.push(`${options?.method ?? 'GET'} ${url}`)
    if (url.endsWith('/traces')) return response([trace('first')])
    if (url.endsWith('/cancel')) return response({ task_id: 'task-1', cancelled: true })
    if (url.endsWith('/task-1')) return response(currentTask)
    if (options?.method === 'POST') return response(task({ status: 'queued' }), 202)
    return response([currentTask])
  }))
  history.replaceState(null, '', '/')
})
afterEach(() => vi.unstubAllGlobals())

describe('research UI', () => {
  it('restores selected task and sourced report on refresh without unsafe links', async () => {
    currentTask = task({ status: 'completed', report: {
      task_id: 'task-1', goal: '比较公开项目', title: '研究结果', summary: '总结',
      findings: [], comparison: '对比', recommendation: '建议',
      sources: ['https://example.org/reference', 'javascript:alert(1)'],
      markdown: 'ignored', generated_at: '2026-10-12T10:00:00Z',
    } })
    history.replaceState(null, '', '/?task=task-1')
    const wrapper = mount(App)
    await flushPromises()
    expect(wrapper.text()).toContain('研究结果')
    expect(wrapper.text()).toContain('事件 first')
    expect(wrapper.findAll('a[href="https://example.org/reference"]').length).toBe(1)
    expect(wrapper.findAll('a[href^="javascript:"]').length).toBe(0)
    expect(FakeEventSource.instances).toHaveLength(0)
    wrapper.unmount()
  })

  it('shows unfinished work from a partial report', async () => {
    currentTask = task({ status: 'partial', report: {
      task_id: 'task-1', goal: '比较公开项目', title: '部分研究结果', summary: '尚未完成',
      findings: [], comparison: '证据不足', recommendation: '继续核实', sources: [],
      markdown: '# 部分研究结果\n\n## Unknown or unfinished\n- 核对第二个项目的许可证\n\n## Sources\n',
      generated_at: '2026-10-12T10:00:00Z',
    } })
    const wrapper = mount(App)
    await flushPromises()
    expect(wrapper.text()).toContain('待核实或未完成')
    expect(wrapper.text()).toContain('核对第二个项目的许可证')
    wrapper.unmount()
  })

  it('labels only evaluated actions as numbered steps', async () => {
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (url.endsWith('/traces')) return response([
        trace('queued', 'task_queued'),
        trace('started', 'task_started'),
        trace('action', 'step_evaluated'),
        { ...trace('finished', 'task_finished'), step: 1 },
      ])
      if (url.endsWith('/task-1')) return response(task({ status: 'completed' }))
      return response([task({ status: 'completed' })])
    }))
    const wrapper = mount(App)
    await flushPromises()
    const timelineText = wrapper.get('.timeline').text()
    expect(timelineText.match(/第 1 步/g)?.length).toBe(1)
    expect(timelineText).not.toContain('第 2 步')
    wrapper.unmount()
  })

  it('deduplicates replayed SSE IDs, shows reconnect feedback, and closes at terminal state', async () => {
    const wrapper = mount(App)
    await flushPromises()
    const stream = FakeEventSource.instances[0]
    expect(stream.url).toBe('/api/research/task-1/events')
    stream.emit('task_started', trace('first'))
    stream.emit('step_evaluated', trace('second', 'step_evaluated'))
    await flushPromises()
    expect(wrapper.text().match(/事件 first/g)?.length).toBe(1)
    stream.onerror?.()
    await flushPromises()
    expect(wrapper.text()).toContain('正在重连')
    currentTask = task({ status: 'completed' })
    stream.emit('task_finished', trace('last', 'task_finished'))
    await flushPromises()
    expect(stream.closed).toBe(true)
    expect(wrapper.text()).toContain('已完成')
    wrapper.unmount()
  })

  it('opens SSE when initial traces fail after task detail loads', async () => {
    let traceRequests = 0
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (url.endsWith('/traces')) {
        traceRequests += 1
        if (traceRequests === 1) throw new TypeError('temporary trace outage')
        return response([trace('first'), trace('finished', 'task_finished')])
      }
      if (url.endsWith('/task-1')) return response(currentTask)
      return response([currentTask])
    }))
    const wrapper = mount(App)
    await flushPromises()
    expect(FakeEventSource.instances).toHaveLength(1)
    const stream = FakeEventSource.instances[0]
    stream.emit('step_evaluated', trace('live', 'step_evaluated'))
    currentTask = task({ status: 'completed' })
    stream.emit('task_finished', trace('finished', 'task_finished'))
    await flushPromises()
    expect(stream.closed).toBe(true)
    expect(wrapper.get('.task-summary').text()).toContain('已完成')
    expect(wrapper.text()).toContain('事件 live')
    expect(wrapper.text().match(/事件 finished/g)?.length).toBe(1)
    wrapper.unmount()
  })

  it('updates the recent-task status when detail is terminal but list refresh lags', async () => {
    let finished = false
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (url.endsWith('/traces')) return response([trace('first')])
      if (url.endsWith('/task-1')) return response(task({ status: finished ? 'completed' : 'running' }))
      return response([task({ status: 'running' })])
    }))
    const wrapper = mount(App)
    await flushPromises()
    finished = true
    FakeEventSource.instances[0].emit('task_finished', trace('last', 'task_finished'))
    await flushPromises()
    expect(wrapper.get('.task-summary').text()).toContain('已完成')
    expect(wrapper.get('.recent').text()).toContain('已完成')
    wrapper.unmount()
  })

  it('updates queued status from a successful nonterminal detail poll', async () => {
    vi.useFakeTimers()
    currentTask = task({ status: 'queued' })
    const wrapper = mount(App)
    try {
      await flushPromises()
      expect(wrapper.get('.task-summary').text()).toContain('排队中')
      currentTask = task({ status: 'running' })
      await vi.advanceTimersByTimeAsync(6000)
      await flushPromises()
      expect(wrapper.get('.task-summary').text()).toContain('研究中')
      expect(wrapper.get('.recent').text()).toContain('研究中')
    } finally {
      vi.useRealTimers()
      wrapper.unmount()
    }
  })

  it('recovers terminal state when a disconnected SSE proxy never fires onerror', async () => {
    vi.useFakeTimers()
    const wrapper = mount(App)
    try {
      await flushPromises()
      const stream = FakeEventSource.instances[0]
      currentTask = task({ status: 'failed', stop_reason: 'server_restart' })
      await vi.advanceTimersByTimeAsync(6000)
      await flushPromises()
      expect(wrapper.text()).toContain('server_restart')
      expect(stream.closed).toBe(true)
    } finally {
      vi.useRealTimers()
      wrapper.unmount()
    }
  })

  it('retries terminal detail after a temporary trace failure without keeping SSE open', async () => {
    vi.useFakeTimers()
    let traceOffline = false
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (url.endsWith('/traces')) {
        if (traceOffline) throw new TypeError('temporary outage')
        return response([trace('first'), trace('last', 'task_finished')])
      }
      if (url.endsWith('/task-1')) return response(currentTask)
      return response([currentTask])
    }))
    const wrapper = mount(App)
    try {
      await flushPromises()
      const stream = FakeEventSource.instances[0]
      traceOffline = true
      currentTask = task({ status: 'completed', report: {
        task_id: 'task-1', goal: '比较公开项目', title: '恢复的报告', summary: '总结',
        findings: [], comparison: '', recommendation: '', sources: [],
        markdown: '', generated_at: '2026-10-12T10:00:00Z',
      } })
      stream.emit('task_finished', trace('last', 'task_finished'))
      await flushPromises()
      expect(stream.closed).toBe(true)
      expect(wrapper.get('.task-summary').text()).toContain('已完成')
      expect(wrapper.text()).toContain('恢复的报告')
      expect(wrapper.find('[data-test="cancel"]').exists()).toBe(false)
      traceOffline = false
      await vi.advanceTimersByTimeAsync(6000)
      await flushPromises()
      expect(wrapper.text()).toContain('恢复的报告')
      expect(vi.getTimerCount()).toBe(0)
    } finally {
      vi.useRealTimers()
      wrapper.unmount()
    }
  })

  it('stops automatic terminal retries and offers refresh after repeated failure', async () => {
    vi.useFakeTimers()
    let tracesOffline = false
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (url.endsWith('/traces')) {
        if (tracesOffline) throw new TypeError('persistent outage')
        return response([trace('first')])
      }
      if (url.endsWith('/task-1')) return response(currentTask)
      return response([currentTask])
    }))
    const wrapper = mount(App)
    try {
      await flushPromises()
      tracesOffline = true
      currentTask = task({ status: 'completed' })
      FakeEventSource.instances[0].emit('task_finished', trace('last', 'task_finished'))
      await flushPromises()
      await vi.advanceTimersByTimeAsync(20000)
      await flushPromises()
      expect(vi.getTimerCount()).toBe(0)
      expect(wrapper.text()).toContain('点击刷新')
    } finally {
      vi.useRealTimers()
      wrapper.unmount()
    }
  })

  it('keeps an SSE event received while a trace reload is in flight', async () => {
    let finishDetail: ((value: ReturnType<typeof response>) => void) | undefined
    let delayDetail = false
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (url.endsWith('/traces')) return response([trace('first')])
      if (url.endsWith('/task-1')) {
        if (delayDetail) return new Promise<ReturnType<typeof response>>((resolve) => { finishDetail = resolve })
        return response(currentTask)
      }
      return response([currentTask])
    }))
    const wrapper = mount(App)
    await flushPromises()
    const stream = FakeEventSource.instances[0]
    delayDetail = true
    await wrapper.get('.task-panel button').trigger('click')
    await flushPromises()
    stream.emit('step_evaluated', trace('during-reload', 'step_evaluated'))
    finishDetail?.(response(currentTask))
    await flushPromises()
    expect(wrapper.text()).toContain('事件 during-reload')
    wrapper.unmount()
  })

  it('reconnects the timeline after refresh recovers an initial detail failure', async () => {
    let detailOffline = true
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (url.endsWith('/traces')) return response([trace('first')])
      if (url.endsWith('/task-1')) {
        if (detailOffline) throw new TypeError('temporary outage')
        return response(currentTask)
      }
      return response([currentTask])
    }))
    const wrapper = mount(App)
    await flushPromises()
    expect(FakeEventSource.instances).toHaveLength(0)
    detailOffline = false
    await wrapper.get('.task-panel button').trigger('click')
    await flushPromises()
    expect(FakeEventSource.instances).toHaveLength(1)
    FakeEventSource.instances[0].emit('step_evaluated', trace('recovered', 'step_evaluated'))
    await flushPromises()
    expect(wrapper.text()).toContain('事件 recovered')
    wrapper.unmount()
  })

  it('submits with the keyboard and gives cancellation feedback', async () => {
    const wrapper = mount(App)
    await flushPromises()
    await wrapper.get('textarea').setValue('分析三个开源项目')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(fetchCalls).toContain('POST /api/research')
    await wrapper.get('[data-test="cancel"]').trigger('click')
    await flushPromises()
    expect(fetchCalls).toContain('POST /api/research/task-1/cancel')
    expect(wrapper.text()).toContain('取消请求已发送')
    wrapper.unmount()
  })

  it('shows a durable running cancellation as pending and restores it on refresh', async () => {
    history.replaceState(null, '', '/?task=task-1')
    vi.stubGlobal('fetch', vi.fn(async (url: string) => {
      if (url.endsWith('/cancel')) {
        currentTask = task({ cancellation_requested: true })
        return response({ task_id: 'task-1', cancelled: false, cancellation_requested: true })
      }
      if (url.endsWith('/traces')) return response([])
      if (url.endsWith('/task-1')) return response(currentTask)
      return response([currentTask])
    }))
    const wrapper = mount(App)
    await flushPromises()
    await wrapper.get('[data-test="cancel"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('取消请求已发送')
    expect(wrapper.get('[data-test="cancel"]').attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('等待取消完成')
    wrapper.unmount()
    const restored = mount(App)
    await flushPromises()
    expect(restored.text()).toContain('取消中')
    expect(restored.get('[data-test="cancel"]').attributes('disabled')).toBeDefined()
    restored.unmount()
  })

  it('shows a created task while the subsequent recent-list request is stalled', async () => {
    let releaseList: ((value: ReturnType<typeof response>) => void) | undefined
    let listCalls = 0
    const created = task({ id: 'created-now', goal: '即时研究', status: 'queued' })
    vi.stubGlobal('fetch', vi.fn(async (url: string, options?: RequestInit) => {
      if (url.endsWith('/traces')) return response([])
      if (url.endsWith('/created-now')) return response(created)
      if (options?.method === 'POST') return response(created, 202)
      if (url === '/api/research') {
        listCalls += 1
        if (listCalls === 1) return response([])
        return new Promise<ReturnType<typeof response>>((resolve) => { releaseList = resolve })
      }
      return response([], 404)
    }))
    const wrapper = mount(App)
    await flushPromises()
    await wrapper.get('textarea').setValue('即时研究')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(listCalls).toBe(2)
    expect(wrapper.get('.task-summary').text()).toContain('即时研究')
    expect(FakeEventSource.instances).toHaveLength(1)
    releaseList?.(response([created]))
    await flushPromises()
    wrapper.unmount()
  })

  it('keeps a newly submitted task selected when the initial list arrives late', async () => {
    let finishInitial: ((value: ReturnType<typeof response>) => void) | undefined
    let listCalls = 0
    let detailCalls = 0
    const created = task({ id: 'new-task', goal: '新研究', status: 'queued' })
    vi.stubGlobal('fetch', vi.fn(async (url: string, options?: RequestInit) => {
      if (url.endsWith('/traces')) return response([])
      if (url.endsWith('/new-task')) { detailCalls += 1; return response(created) }
      if (options?.method === 'POST') return response(created, 202)
      if (url === '/api/research') {
        listCalls += 1
        if (listCalls === 1) return new Promise<ReturnType<typeof response>>((resolve) => { finishInitial = resolve })
        return response([created])
      }
      return response([], 404)
    }))
    const wrapper = mount(App)
    await flushPromises()
    expect(listCalls).toBe(1)
    await wrapper.get('textarea').setValue('新研究')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(listCalls).toBe(2)
    expect(wrapper.get('.task-summary').text()).toContain('新研究')
    expect(finishInitial).toBeDefined()
    finishInitial!(response([task({ id: 'old-task', goal: '旧研究' })]))
    await flushPromises()
    expect(wrapper.get('.task-summary').text()).toContain('新研究')
    expect(window.location.search).toContain('new-task')
    expect(wrapper.get('.recent').text()).toContain('新研究')
    expect(wrapper.get('.recent').text()).not.toContain('旧研究')
    expect(detailCalls).toBe(1)
    wrapper.unmount()
  })

  it('explains missing provider configuration without exposing credentials', async () => {
    vi.stubGlobal('fetch', vi.fn(async (_url: string, options?: RequestInit) =>
      options?.method === 'POST' ? response({ detail: 'DeepSeek provider is not configured' }, 503) : response([])))
    const wrapper = mount(App)
    await flushPromises()
    await wrapper.get('textarea').setValue('研究目标')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain('未配置 DeepSeek 密钥')
    expect(wrapper.text()).not.toContain('sk-')
    wrapper.unmount()
  })

  it.each([
    [503, '研究服务暂时不可用'],
    [429, '研究任务已满'],
  ])('explains unavailable capacity or database (HTTP %s)', async (status, message) => {
    vi.stubGlobal('fetch', vi.fn(async (_url: string, options?: RequestInit) =>
      options?.method === 'POST' ? response({}, status) : response([])))
    const wrapper = mount(App)
    await flushPromises()
    await wrapper.get('textarea').setValue('研究目标')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(wrapper.text()).toContain(message)
    expect(wrapper.text()).not.toContain('未配置 DeepSeek 密钥')
    wrapper.unmount()
  })

  it('shows a bookmarked task 404 and does not open a stale event stream', async () => {
    history.replaceState(null, '', '/?task=missing')
    vi.stubGlobal('fetch', vi.fn(async (url: string) =>
      url.endsWith('/missing') ? response({}, 404) : response([task()])))
    const wrapper = mount(App)
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('任务不存在')
    expect(FakeEventSource.instances).toHaveLength(0)
    wrapper.unmount()
  })

  it('shows an empty state when the API has no recent tasks', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => response([])))
    const wrapper = mount(App)
    await flushPromises()
    expect(wrapper.text()).toContain('还没有任务')
    expect(wrapper.text()).toContain('尚无历史任务')
    expect(FakeEventSource.instances).toHaveLength(0)
    wrapper.unmount()
  })

  it('explains an API network failure', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => { throw new TypeError('network down') }))
    const wrapper = mount(App)
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('无法连接本地 API')
    wrapper.unmount()
  })

  it('explains a development proxy failure when the API is offline', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => response('proxy connection refused', 500)))
    const wrapper = mount(App)
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('本地 API 暂时不可用')
    wrapper.unmount()
  })
})
