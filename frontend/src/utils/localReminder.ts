export interface ReminderPreferences {
  dailyReminder: boolean
  reminderTime: string
}

export interface ReminderScheduleResult {
  supported: boolean
  enabled: boolean
  permission: NotificationPermission | 'unsupported'
  nextAt?: string
  message: string
}

let reminderTimer: number | undefined

export function loadReminderPreferences(): ReminderPreferences {
  try {
    const raw = localStorage.getItem('preferences')
    const parsed = raw ? JSON.parse(raw) : {}
    return {
      dailyReminder: parsed.dailyReminder ?? true,
      reminderTime: parsed.reminderTime || '20:00',
    }
  } catch {
    return { dailyReminder: true, reminderTime: '20:00' }
  }
}

export function scheduleDailyTrainingReminder(preferences: ReminderPreferences): ReminderScheduleResult {
  clearDailyTrainingReminder()
  if (!preferences.dailyReminder) {
    return {
      supported: supportsNotification(),
      enabled: false,
      permission: notificationPermission(),
      message: '每日提醒已关闭。',
    }
  }
  if (!supportsNotification()) {
    return {
      supported: false,
      enabled: false,
      permission: 'unsupported',
      message: '当前浏览器不支持系统通知，只会保存提醒时间。',
    }
  }
  if (Notification.permission !== 'granted') {
    return {
      supported: true,
      enabled: false,
      permission: Notification.permission,
      message: Notification.permission === 'denied'
        ? '浏览器通知权限已被拒绝，请在浏览器设置中允许通知。'
        : '尚未授权浏览器通知，保存偏好时会请求授权。',
    }
  }
  const next = nextReminderTime(preferences.reminderTime)
  reminderTimer = window.setTimeout(() => {
    showTrainingReminder()
    scheduleDailyTrainingReminder(preferences)
  }, Math.max(0, next.getTime() - Date.now()))
  return {
    supported: true,
    enabled: true,
    permission: 'granted',
    nextAt: next.toISOString(),
    message: `下一次提醒：${formatReminderTime(next)}。页面或浏览器关闭后，本地提醒不会继续运行。`,
  }
}

export async function requestAndScheduleDailyTrainingReminder(
  preferences: ReminderPreferences
): Promise<ReminderScheduleResult> {
  if (!preferences.dailyReminder) return scheduleDailyTrainingReminder(preferences)
  if (!supportsNotification()) return scheduleDailyTrainingReminder(preferences)
  if (Notification.permission === 'default') {
    await Notification.requestPermission()
  }
  return scheduleDailyTrainingReminder(preferences)
}

export async function sendTestTrainingReminder(): Promise<ReminderScheduleResult> {
  if (!supportsNotification()) {
    return {
      supported: false,
      enabled: false,
      permission: 'unsupported',
      message: '当前浏览器不支持系统通知。',
    }
  }
  if (Notification.permission === 'default') {
    await Notification.requestPermission()
  }
  if (Notification.permission !== 'granted') {
    return {
      supported: true,
      enabled: false,
      permission: Notification.permission,
      message: '没有通知权限，无法发送测试提醒。',
    }
  }
  showTrainingReminder('测试提醒：关系动力学训练', '这是一条测试通知。真正提醒会按你保存的时间触发。')
  return {
    supported: true,
    enabled: true,
    permission: 'granted',
    message: '测试提醒已发送。',
  }
}

export function clearDailyTrainingReminder() {
  if (reminderTimer !== undefined) {
    window.clearTimeout(reminderTimer)
    reminderTimer = undefined
  }
}

export function formatReminderTime(value: string | Date) {
  const date = typeof value === 'string' ? new Date(value) : value
  return date.toLocaleString(undefined, {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function supportsNotification() {
  return typeof window !== 'undefined' && 'Notification' in window
}

function notificationPermission(): NotificationPermission | 'unsupported' {
  return supportsNotification() ? Notification.permission : 'unsupported'
}

function nextReminderTime(timeValue: string) {
  const [hourText, minuteText] = timeValue.split(':')
  const hour = Number(hourText)
  const minute = Number(minuteText)
  const next = new Date()
  next.setHours(Number.isFinite(hour) ? hour : 20, Number.isFinite(minute) ? minute : 0, 0, 0)
  if (next.getTime() <= Date.now()) {
    next.setDate(next.getDate() + 1)
  }
  return next
}

function showTrainingReminder(title = '关系动力学训练提醒', body = '到了今天的训练时间，花几分钟练一轮微关系感知吧。') {
  const notification = new Notification(title, {
    body,
    tag: 'relationship-training-daily-reminder',
  })
  notification.onclick = () => {
    window.focus()
    window.location.href = '/daily'
    notification.close()
  }
}
