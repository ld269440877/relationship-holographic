import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './styles/main.css'
import { installWindowRuntimeReporting, reportRuntimeEvent } from '@/utils/runtimeEvents'
import { loadReminderPreferences, scheduleDailyTrainingReminder } from '@/utils/localReminder'

const app = createApp(App)

app.config.errorHandler = (error, instance, info) => {
  const component = instance?.$options.name || 'unknown'
  reportRuntimeEvent({
    event_type: 'vue_error',
    severity: 'high',
    route: router.currentRoute.value.path,
    message: error instanceof Error ? error.message : String(error),
    context: {
      component,
      info,
      online: navigator.onLine,
    },
  })
  console.error(error)
}

installWindowRuntimeReporting()
scheduleDailyTrainingReminder(loadReminderPreferences())

app.use(createPinia())
app.use(router)

app.mount('#app')
