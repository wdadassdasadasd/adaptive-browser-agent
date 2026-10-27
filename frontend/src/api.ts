export type TaskStatus = 'queued' | 'running' | 'completed' | 'partial' | 'failed' | 'cancelled'

export interface Finding {
  name: string
  description: string
  attributes: Record<string, string>
  source_urls: string[]
}

export interface DecisionContext {
  use_case: string
  must_have: string[]
  preferences: string[]
  candidate_projects: string[]
}

export type DecisionVerdict = 'satisfied' | 'not_satisfied' | 'unknown' | 'conflicting'

export interface DecisionCandidate {
  candidate_id: string
  label: string
  origin: 'user' | 'agent'
  verified_subject: string | null
}

export interface DecisionMatrixRow {
  candidate_id: string
  condition_type: 'must_have' | 'preference'
  condition: string
  verdict: DecisionVerdict
  supporting_fact_ids: string[]
  contradicting_fact_ids: string[]
  reason: string
}

export interface DecisionRecommendation {
  candidate_id: string
  text: string
  supporting_fact_ids: string[]
  verification_status: 'machine_admitted_human_unverified'
}

export interface DecisionEvidence {
  fact_id: string
  subject: string
  source_url: string
  excerpt: string
  observed_at: string
}

export interface DecisionReport {
  use_case: string
  must_have: string[]
  preferences: string[]
  candidate_projects: string[]
  candidates: DecisionCandidate[]
  matrix: DecisionMatrixRow[]
  evidence_facts?: DecisionEvidence[]
  unknowns: string[]
  conflicts: string[]
  recommendation: DecisionRecommendation | null
  change_conditions: string[]
  no_recommendation_reason: string | null
  verification_status: 'machine_admitted_human_unverified'
}

export interface ResearchReport {
  task_id: string
  goal: string
  title: string
  summary: string
  findings: Finding[]
  comparison: string
  recommendation: string
  sources: string[]
  markdown: string
  generated_at: string
  decision?: DecisionReport | null
}

export interface ResearchTask {
  id: string
  goal: string
  decision_context?: DecisionContext | null
  status: TaskStatus
  cancellation_requested?: boolean
  error_message: string | null
  created_at: string
  updated_at: string
  completion_level: string | null
  stop_reason: string | null
  report: ResearchReport | null
}

export interface AgentEvent {
  event_id: string
  task_id: string
  event_type: string
  step: number
  timestamp: string
  message: string
  payload: Record<string, unknown>
}

export class ApiError extends Error {
  constructor(public readonly status: number, message: string) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api/research${path}`, init)
  } catch {
    throw new ApiError(0, '无法连接本地 API，请检查后端服务和网络连接。')
  }
  if (!response.ok) {
    if (response.status === 503) {
      const body = await response.json().catch(() => null) as { detail?: string } | null
      throw new ApiError(503, body?.detail === 'DeepSeek provider is not configured'
        ? '未配置 DeepSeek 密钥，暂时无法启动研究任务。'
        : '研究服务暂时不可用，请检查本机后端和数据库后重试。')
    }
    if (response.status === 429) throw new ApiError(429, '研究任务已满，请等待任务结束或取消排队任务后重试。')
    if (response.status === 404) throw new ApiError(404, '任务不存在，可能已被删除。')
    if (response.status === 422) throw new ApiError(422, '研究目标或选型条件无效，请检查长度、空条目与重复项。')
    if (response.status >= 500) throw new ApiError(response.status, `本地 API 暂时不可用，请检查后端服务（HTTP ${response.status}）。`)
    throw new ApiError(response.status, `请求失败（HTTP ${response.status}）。`)
  }
  return response.json() as Promise<T>
}

export const researchApi = {
  list: () => request<ResearchTask[]>(''),
  get: (id: string) => request<ResearchTask>(`/${encodeURIComponent(id)}`),
  traces: (id: string) => request<AgentEvent[]>(`/${encodeURIComponent(id)}/traces`),
  create: (goal: string, decisionContext?: DecisionContext) => request<ResearchTask>('', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(decisionContext ? { goal, decision_context: decisionContext } : { goal }),
  }),
  cancel: (id: string) => request<{ task_id: string; cancelled: boolean; cancellation_requested?: boolean }>(`/${encodeURIComponent(id)}/cancel`, { method: 'POST' }),
}

export function eventUrl(id: string): string {
  return `/api/research/${encodeURIComponent(id)}/events`
}

export function safeSourceUrl(value: string): string | undefined {
  try {
    const url = new URL(value)
    return (url.protocol === 'http:' || url.protocol === 'https:') && !url.username && !url.password
      ? url.href
      : undefined
  } catch {
    return undefined
  }
}
