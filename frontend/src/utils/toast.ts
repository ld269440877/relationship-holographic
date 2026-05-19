/**
 * Toast 通知系统
 * 用法：const toast = useToast(); toast.success('保存成功')
 */
import { ref } from 'vue'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

export interface Toast {
  id: number
  type: ToastType
  message: string
}

const toasts = ref<Toast[]>([])
let nextId = 1

export function useToast() {
  function show(message: string, type: ToastType = 'info', duration = 3000) {
    const id = nextId++
    toasts.value.push({ id, type, message })
    setTimeout(() => {
      toasts.value = toasts.value.filter((t) => t.id !== id)
    }, duration)
  }

  const success = (msg: string) => show(msg, 'success')
  const error = (msg: string) => show(msg, 'error', 4000)
  const info = (msg: string) => show(msg, 'info')
  const warning = (msg: string) => show(msg, 'warning')

  return { toasts, success, error, info, warning }
}
