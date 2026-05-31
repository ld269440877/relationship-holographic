export function finiteNumber(value: unknown, fallback = 0): number {
  const parsed = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

export function rounded(value: unknown, fallback = 0): number {
  return Math.round(finiteNumber(value, fallback))
}

export function oneDecimal(value: unknown, fallback = 0): number {
  return Math.round(finiteNumber(value, fallback) * 10) / 10
}

export function percent(value: unknown, fallback = 0): string {
  return `${rounded(value, fallback)}%`
}

export function ratioPercent(value: unknown, fallback = 0): string {
  return `${rounded(finiteNumber(value, fallback) * 100)}%`
}

export function clampedPercent(value: unknown, fallback = 0): number {
  return Math.max(0, Math.min(100, rounded(value, fallback)))
}

export function safeBarWidth(value: unknown, fallback = 0, minimum = 0): string {
  const width = Math.max(minimum, clampedPercent(value, fallback))
  return `${width}%`
}

export function safeRatioBarWidth(value: unknown, fallback = 0, minimum = 0): string {
  const width = Math.max(minimum, clampedPercent(finiteNumber(value, fallback) * 100))
  return `${width}%`
}

export function displayValue(value: unknown, fallback = '-'): string {
  if (value === null || value === undefined || value === '') return fallback
  if (typeof value === 'number') return Number.isFinite(value) ? String(value) : fallback
  return String(value)
}
