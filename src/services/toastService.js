import { reactive } from 'vue'

class ToastService {
  constructor() {
    this.toasts = reactive({
      current: null
    })
  }

  show(message, type = 'info', duration = 3000) {
    this.toasts.current = {
      message,
      type,
      duration,
      id: Date.now()
    }
  }

  info(message, duration) {
    this.show(message, 'info', duration)
  }

  success(message, duration) {
    this.show(message, 'success', duration)
  }

  warning(message, duration) {
    this.show(message, 'warning', duration)
  }

  error(message, duration) {
    this.show(message, 'error', duration)
  }

  clear() {
    this.toasts.current = null
  }

  getCurrent() {
    return this.toasts.current
  }
}

export const toastService = new ToastService()