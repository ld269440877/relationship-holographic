<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast-item"
          :class="`toast-${toast.type}`"
        >
          <span class="toast-icon">{{ icons[toast.type] }}</span>
          <span class="toast-msg">{{ toast.message }}</span>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { useToast } from '@/utils/toast'
const { toasts } = useToast()

const icons: Record<string, string> = {
  success: '✅',
  error: '❌',
  info: '💡',
  warning: '⚠️',
}
</script>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
}
.toast-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
  border-radius: 12px;
  font-size: 14px;
  min-width: 240px;
  max-width: 380px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.15);
  pointer-events: auto;
}
.toast-success { background: #ecfdf5; color: #065f46; border: 1px solid #6ee7b7; }
.toast-error   { background: #fef2f2; color: #991b1b; border: 1px solid #fca5a5; }
.toast-info    { background: #eff6ff; color: #1e40af; border: 1px solid #93c5fd; }
.toast-warning { background: #fffbeb; color: #92400e; border: 1px solid #fcd34d; }
.toast-msg { flex: 1; line-height: 1.4; }

/* 过渡动画 */
.toast-enter-active { animation: slideIn 0.3s ease; }
.toast-leave-active { animation: slideIn 0.3s ease reverse; }
@keyframes slideIn {
  from { opacity: 0; transform: translateX(40px); }
  to   { opacity: 1; transform: translateX(0); }
}
</style>
