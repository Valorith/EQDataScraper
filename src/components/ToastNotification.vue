<template>
  <transition name="toast">
    <div v-if="visible" class="toast-notification" :class="type">
      <div class="toast-content">
        <i :class="iconClass"></i>
        <span class="toast-message">{{ message }}</span>
      </div>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'ToastNotification',
  props: {
    message: {
      type: String,
      required: true
    },
    type: {
      type: String,
      default: 'info',
      validator: value => ['info', 'success', 'warning', 'error'].includes(value)
    },
    duration: {
      type: Number,
      default: 3000
    }
  },
  data() {
    return {
      visible: false,
      timer: null
    }
  },
  computed: {
    iconClass() {
      const icons = {
        info: 'fas fa-info-circle',
        success: 'fas fa-check-circle',
        warning: 'fas fa-exclamation-triangle',
        error: 'fas fa-times-circle'
      }
      return icons[this.type]
    }
  },
  methods: {
    show() {
      this.visible = true
      if (this.timer) {
        clearTimeout(this.timer)
      }
      this.timer = setTimeout(() => {
        this.hide()
      }, this.duration)
    },
    hide() {
      this.visible = false
      if (this.timer) {
        clearTimeout(this.timer)
        this.timer = null
      }
    }
  },
  beforeUnmount() {
    if (this.timer) {
      clearTimeout(this.timer)
    }
  }
}
</script>

<style scoped>
.toast-notification {
  position: fixed;
  top: 80px;
  right: 20px;
  min-width: 300px;
  max-width: 500px;
  padding: 16px 24px;
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.95) 0%, rgba(45, 55, 72, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  border: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 10000;
}

.toast-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toast-content i {
  font-size: 1.2rem;
}

.toast-message {
  color: #f7fafc;
  font-size: 1rem;
  font-weight: 500;
  line-height: 1.4;
}

/* Type-specific colors */
.toast-notification.info {
  border-left: 4px solid #3b82f6;
}

.toast-notification.info i {
  color: #60a5fa;
}

.toast-notification.success {
  border-left: 4px solid #10b981;
}

.toast-notification.success i {
  color: #34d399;
}

.toast-notification.warning {
  border-left: 4px solid #f59e0b;
}

.toast-notification.warning i {
  color: #fbbf24;
}

.toast-notification.error {
  border-left: 4px solid #ef4444;
}

.toast-notification.error i {
  color: #f87171;
}

/* Toast animations */
.toast-enter-active {
  animation: slide-in-right 0.3s ease-out;
}

.toast-leave-active {
  animation: slide-out-right 0.3s ease-in;
}

@keyframes slide-in-right {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slide-out-right {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}
</style>