import axios from 'axios'

type RuntimeSeverity = 'low' | 'medium' | 'high' | 'critical'

interface RuntimeEventPayload {
  source?: string
  event_type: string
  severity?: RuntimeSeverity
  route?: string
  method?: string
  endpoint?: string
  http_status?: number
  message: string
  context?: Record<string, unknown>
}

const reporter = axios.create({
  baseURL: '/api',
  timeout: 5000,
  headers: { 'Content-Type': 'application/json' },
})

const recent = new Map<string, number>()
const throttleMs = 30_000

export function reportRuntimeEvent(payload: RuntimeEventPayload) {
  if (typeof window === 'undefined') return
  if (payload.endpoint?.includes('/analytics/runtime-events')) return

  const normalized = normalizePayload(payload)
  const key = `${normalized.event_type}:${normalized.route || ''}:${normalized.endpoint || ''}:${normalized.message.slice(0, 80)}`
  const now = Date.now()
  const last = recent.get(key) || 0
  if (now - last < throttleMs) return
  recent.set(key, now)

  reporter.post('/analytics/runtime-events', normalized).catch(() => {
    // Runtime reporting must never break the user flow.
  })
}

export function installWindowRuntimeReporting() {
  if (typeof window === 'undefined') return

  window.addEventListener('error', (event) => {
    reportRuntimeEvent({
      event_type: 'window_error',
      severity: 'high',
      route: window.location.pathname,
      message: event.message || 'window error',
      context: {
        browser: navigator.userAgent,
        online: navigator.onLine,
      },
    })
  })

  window.addEventListener('unhandledrejection', (event) => {
    reportRuntimeEvent({
      event_type: 'unhandled_rejection',
      severity: 'high',
      route: window.location.pathname,
      message: reasonToMessage(event.reason),
      context: {
        browser: navigator.userAgent,
        online: navigator.onLine,
      },
    })
  })
}

function normalizePayload(payload: RuntimeEventPayload): RuntimeEventPayload {
  return {
    source: payload.source || 'frontend',
    event_type: payload.event_type,
    severity: payload.severity || 'medium',
    route: stripQuery(payload.route || window.location.pathname),
    method: payload.method,
    endpoint: stripQuery(payload.endpoint),
    http_status: payload.http_status,
    message: sanitizeMessage(payload.message),
    context: sanitizeContext(payload.context || {}),
  }
}

function reasonToMessage(reason: unknown): string {
  if (reason instanceof Error) return reason.message
  if (typeof reason === 'string') return reason
  return 'unhandled promise rejection'
}

function stripQuery(value?: string) {
  if (!value) return undefined
  return value.split('?')[0].slice(0, 240)
}

function sanitizeMessage(value: string) {
  return value.replace(/Bearer\\s+\\S+/gi, 'Bearer [redacted]').slice(0, 500)
}

function sanitizeContext(context: Record<string, unknown>) {
  const allowed = ['status_text', 'component', 'info', 'browser', 'online', 'retryable', 'duration_ms']
  return Object.fromEntries(
    Object.entries(context)
      .filter(([key]) => allowed.includes(key))
      .map(([key, value]) => [key, typeof value === 'string' ? value.slice(0, 160) : value])
  )
}
