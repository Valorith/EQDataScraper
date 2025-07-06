<template>
  <div class="user-menu-container">
    <div class="user-menu" :class="{ 'menu-open': isMenuOpen }" ref="userMenu">
      <!-- User Avatar/Button -->
      <button 
        @click="toggleMenu"
        class="user-avatar-button"
        :title="`Signed in as ${user.email}`"
      >
        <!-- Class Avatar -->
        <div 
          v-if="userAvatar.type === 'class'" 
          class="user-avatar-class"
        >
          <div class="class-icon-background" :style="{ backgroundColor: getClassColor(userAvatar.class) }"></div>
          <div class="class-icon">
            <img 
              :src="`/icons/${userAvatar.class}.gif`" 
              :alt="getClassDisplayName(userAvatar.class)"
              @error="handleImageError"
              class="class-icon-img"
            />
          </div>
        </div>
        <!-- Google Photo Avatar -->
        <img 
          v-else-if="userAvatar.url" 
          :src="userAvatar.url" 
          :alt="`${displayName} avatar`"
          class="user-avatar"
        >
        <!-- Fallback Avatar -->
        <div v-else class="user-avatar-fallback">
          {{ avatarInitials }}
        </div>
        <svg class="dropdown-arrow" :class="{ 'rotated': isMenuOpen }" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M6 9L12 15L18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>

      <!-- Dropdown Menu -->
      <transition name="menu-fade">
        <div v-if="isMenuOpen" class="user-dropdown">
          <div class="dropdown-content">
            <!-- User Info -->
            <div class="user-info">
              <div class="user-name">{{ displayName }}</div>
              <div class="user-email">{{ user.email }}</div>
              <div v-if="user.role === 'admin'" class="user-badge admin-badge">Admin</div>
            </div>

            <div class="menu-divider"></div>

            <!-- Menu Items -->
            <nav class="menu-items">
              <router-link 
                to="/profile" 
                class="menu-item"
                @click="closeMenu"
              >
                <svg class="menu-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M12 11C14.2091 11 16 9.20914 16 7C16 4.79086 14.2091 3 12 3C9.79086 3 8 4.79086 8 7C8 9.20914 9.79086 11 12 11Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Profile
              </router-link>

              <router-link 
                v-if="user.role === 'admin'" 
                to="/admin" 
                class="menu-item admin-item"
                @click="closeMenu"
              >
                <svg class="menu-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 15C13.6569 15 15 13.6569 15 12C15 10.3431 13.6569 9 12 9C10.3431 9 9 10.3431 9 12C9 13.6569 10.3431 15 12 15Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M19.4 15C19.2669 15.3016 19.2272 15.6362 19.286 15.9606C19.3448 16.285 19.4995 16.5842 19.73 16.82L19.79 16.88C19.976 17.0657 20.1235 17.2863 20.2241 17.5291C20.3248 17.7719 20.3766 18.0322 20.3766 18.295C20.3766 18.5578 20.3248 18.8181 20.2241 19.0609C20.1235 19.3037 19.976 19.5243 19.79 19.71C19.6043 19.896 19.3837 20.0435 19.1409 20.1441C18.8981 20.2448 18.6378 20.2966 18.375 20.2966C18.1122 20.2966 17.8519 20.2448 17.6091 20.1441C17.3663 20.0435 17.1457 19.896 16.96 19.71L16.9 19.65C16.6642 19.4195 16.365 19.2648 16.0406 19.206C15.7162 19.1472 15.3816 19.1869 15.08 19.32C14.7842 19.4468 14.532 19.6572 14.3543 19.9255C14.1766 20.1938 14.0813 20.5082 14.08 20.83V21C14.08 21.5304 13.8693 22.0391 13.4942 22.4142C13.1191 22.7893 12.6104 23 12.08 23C11.5496 23 11.0409 22.7893 10.6658 22.4142C10.2907 22.0391 10.08 21.5304 10.08 21V20.91C10.0723 20.579 9.96512 20.2579 9.77251 19.9887C9.5799 19.7194 9.31074 19.5143 9 19.4C8.69838 19.2669 8.36381 19.2272 8.03941 19.286C7.71502 19.3448 7.41568 19.4995 7.18 19.73L7.12 19.79C6.93425 19.976 6.71368 20.1235 6.47088 20.2241C6.22808 20.3248 5.96783 20.3766 5.705 20.3766C5.44217 20.3766 5.18192 20.3248 4.93912 20.2241C4.69632 20.1235 4.47575 19.976 4.29 19.79C4.10405 19.6043 3.95653 19.3837 3.85588 19.1409C3.75523 18.8981 3.70343 18.6378 3.70343 18.375C3.70343 18.1122 3.75523 17.8519 3.85588 17.6091C3.95653 17.3663 4.10405 17.1457 4.29 16.96L4.35 16.9C4.58054 16.6642 4.73519 16.365 4.794 16.0406C4.85282 15.7162 4.81312 15.3816 4.68 15.08C4.55324 14.7842 4.34276 14.532 4.07447 14.3543C3.80618 14.1766 3.49179 14.0813 3.17 14.08H3C2.46957 14.08 1.96086 13.8693 1.58579 13.4942C1.21071 13.1191 1 12.6104 1 12.08C1 11.5496 1.21071 11.0409 1.58579 10.6658C1.96086 10.2907 2.46957 10.08 3 10.08H3.09C3.42099 10.0723 3.742 9.96512 4.01127 9.77251C4.28055 9.5799 4.48571 9.31074 4.6 9C4.73312 8.69838 4.77282 8.36381 4.714 8.03941C4.65519 7.71502 4.50054 7.41568 4.27 7.18L4.21 7.12C4.02405 6.93425 3.87653 6.71368 3.77588 6.47088C3.67523 6.22808 3.62343 5.96783 3.62343 5.705C3.62343 5.44217 3.67523 5.18192 3.77588 4.93912C3.87653 4.69632 4.02405 4.47575 4.21 4.29C4.39575 4.10405 4.61632 3.95653 4.85912 3.85588C5.10192 3.75523 5.36217 3.70343 5.625 3.70343C5.88783 3.70343 6.14808 3.75523 6.39088 3.85588C6.63368 3.95653 6.85425 4.10405 7.04 4.29L7.1 4.35C7.33568 4.58054 7.63502 4.73519 7.95941 4.794C8.28381 4.85282 8.61838 4.81312 8.92 4.68H9C9.29579 4.55324 9.54799 4.34276 9.72569 4.07447C9.90339 3.80618 9.99872 3.49179 10 3.17V3C10 2.46957 10.2107 1.96086 10.5858 1.58579C10.9609 1.21071 11.4696 1 12 1C12.5304 1 13.0391 1.21071 13.4142 1.58579C13.7893 1.96086 14 2.46957 14 3V3.09C14.0013 3.41179 14.0966 3.72618 14.2743 3.99447C14.452 4.26276 14.7042 4.47324 15 4.6C15.3016 4.73312 15.6362 4.77282 15.9606 4.714C16.285 4.65519 16.5843 4.50054 16.82 4.27L16.88 4.21C17.0657 4.02405 17.2863 3.87653 17.5291 3.77588C17.7719 3.67523 18.0322 3.62343 18.295 3.62343C18.5578 3.62343 18.8181 3.67523 19.0609 3.77588C19.3037 3.87653 19.5243 4.02405 19.71 4.21C19.896 4.39575 20.0435 4.61632 20.1441 4.85912C20.2448 5.10192 20.2966 5.36217 20.2966 5.625C20.2966 5.88783 20.2448 6.14808 20.1441 6.39088C20.0435 6.63368 19.896 6.85425 19.71 7.04L19.65 7.1C19.4195 7.33568 19.2648 7.63502 19.206 7.95941C19.1472 8.28381 19.1869 8.61838 19.32 8.92V9C19.4468 9.29579 19.6572 9.54799 19.9255 9.72569C20.1938 9.90339 20.5082 9.99872 20.83 10H21C21.5304 10 22.0391 10.2107 22.4142 10.5858C22.7893 10.9609 23 11.4696 23 12C23 12.5304 22.7893 13.0391 22.4142 13.4142C22.0391 13.7893 21.5304 14 21 14H20.91C20.5882 14.0013 20.2738 14.0966 20.0055 14.2743C19.7372 14.452 19.5268 14.7042 19.4 15Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Admin Dashboard
              </router-link>
              
            </nav>

            <div class="menu-divider"></div>

            <!-- Logout -->
            <button 
              @click="handleLogout"
              class="menu-item logout-item"
              :disabled="isLoggingOut"
            >
              <svg class="menu-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M16 17L21 12L16 7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M21 12H9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              {{ isLoggingOut ? 'Signing out...' : 'Sign out' }}
            </button>
          </div>
        </div>
      </transition>
    </div>

    <!-- Backdrop -->
    <div v-if="isMenuOpen" class="menu-backdrop" @click="closeMenu"></div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useUserStore } from '@/stores/userStore'
import { useSpellsStore } from '@/stores/spells'

export default {
  name: 'UserMenu',
  setup() {
    const userStore = useUserStore()
    const spellsStore = useSpellsStore()
    const userMenu = ref(null)
    const isMenuOpen = ref(false)
    const isLoggingOut = ref(false)

    const user = computed(() => userStore.user)
    const fullName = computed(() => userStore.fullName)
    const displayName = computed(() => {
      try {
        return userStore.displayName || userStore.fullName || 'User'
      } catch (error) {
        console.error('Error getting displayName:', error)
        return userStore.fullName || 'User'
      }
    })

    const userAvatar = computed(() => userStore.userAvatar)

    const avatarInitials = computed(() => {
      if (!user.value) return '?'
      
      const firstName = user.value.first_name || ''
      const lastName = user.value.last_name || ''
      const email = user.value.email || ''
      
      if (firstName && lastName) {
        return `${firstName[0]}${lastName[0]}`.toUpperCase()
      } else if (firstName) {
        return firstName[0].toUpperCase()
      } else if (email) {
        return email[0].toUpperCase()
      }
      return '?'
    })

    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value
    }

    const closeMenu = () => {
      isMenuOpen.value = false
    }

    const handleLogout = async () => {
      if (isLoggingOut.value) return
      
      isLoggingOut.value = true
      closeMenu()
      
      try {
        await userStore.logout()
        // Optionally redirect to home page
        // router.push('/')
      } catch (error) {
        console.error('Logout failed:', error)
      } finally {
        isLoggingOut.value = false
      }
    }

    const getClassColor = (className) => {
      if (!className) return '#667eea'
      const classObj = spellsStore.getClassByName(className)
      return classObj?.color || '#667eea'
    }

    const getClassInitial = (className) => {
      if (!className) return '?'
      return className.charAt(0).toUpperCase()
    }

    const getClassDisplayName = (className) => {
      if (!className) return ''
      const classObj = spellsStore.getClassByName(className)
      return classObj?.name || className.charAt(0).toUpperCase() + className.slice(1)
    }

    const handleImageError = (event) => {
      // Fallback to external wiki image if local icon fails
      const img = event.target
      if (img.src.includes('/icons/')) {
        const className = img.alt || img.src.split('/').pop().split('.')[0]
        img.src = `https://wiki.heroesjourneyemu.com/${className}.gif`
      } else {
        // If external also fails, hide the image
        img.style.display = 'none'
      }
    }

    // Close menu when clicking outside
    const handleClickOutside = (event) => {
      if (userMenu.value && !userMenu.value.contains(event.target)) {
        closeMenu()
      }
    }

    // Close menu on escape key
    const handleEscape = (event) => {
      if (event.key === 'Escape') {
        closeMenu()
      }
    }

    onMounted(() => {
      document.addEventListener('click', handleClickOutside)
      document.addEventListener('keydown', handleEscape)
    })

    onUnmounted(() => {
      document.removeEventListener('click', handleClickOutside)
      document.removeEventListener('keydown', handleEscape)
    })

    return {
      userMenu,
      user,
      fullName,
      displayName,
      userAvatar,
      avatarInitials,
      isMenuOpen,
      isLoggingOut,
      toggleMenu,
      closeMenu,
      handleLogout,
      getClassColor,
      getClassInitial,
      getClassDisplayName,
      handleImageError
    }
  }
}
</script>

<style scoped>
.user-menu-container {
  position: relative;
}

.user-menu {
  position: relative;
}

.user-avatar-button {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 36px;
  padding: 10px 20px 10px 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(20px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.user-avatar-button:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.user-avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid rgba(255, 255, 255, 0.3);
}

.user-avatar-fallback {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
}

.user-avatar-class {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid rgba(255, 255, 255, 0.3);
  position: relative;
  background: rgba(255, 255, 255, 0.95);
  overflow: hidden;
}

.class-icon-background {
  position: absolute;
  inset: 0;
  opacity: 0.2;
}

.user-avatar-class .class-icon {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.class-icon-img {
  width: 34px;
  height: 34px;
  object-fit: contain;
  filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.3));
}

.dropdown-arrow {
  width: 20px;
  height: 20px;
  color: rgba(255, 255, 255, 0.8);
  transition: transform 0.2s ease;
}

.dropdown-arrow.rotated {
  transform: rotate(180deg);
}

.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  min-width: 260px;
  z-index: 1000;
}

.dropdown-content {
  padding: 12px 0;
}

.user-info {
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.user-name {
  font-weight: 600;
  color: #1a202c;
  font-size: 16px;
  margin-bottom: 4px;
}

.user-email {
  color: #718096;
  font-size: 14px;
  margin-bottom: 8px;
}

.user-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.admin-badge {
  background: #fed7d7;
  color: #c53030;
}

.menu-divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.1);
  margin: 8px 0;
}

.menu-items {
  padding: 0 8px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 12px;
  color: #4a5568;
  text-decoration: none;
  border-radius: 8px;
  transition: all 0.2s ease;
  font-size: 14px;
  font-weight: 500;
  border: none;
  background: none;
  width: 100%;
  cursor: pointer;
}

.menu-item:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #2d3748;
}

.menu-item.router-link-active {
  background: rgba(66, 153, 225, 0.1);
  color: #3182ce;
}

.menu-item.admin-item {
  color: #c53030;
}

.menu-item.admin-item:hover {
  background: rgba(197, 48, 48, 0.1);
}

.menu-item.logout-item {
  margin-top: 8px;
  color: #e53e3e;
}

.menu-item.logout-item:hover {
  background: rgba(229, 62, 62, 0.1);
}

.menu-item.dev-item {
  color: #38a169;
  font-weight: 600;
}

.menu-item.dev-item:hover {
  background: rgba(56, 161, 105, 0.1);
}

.menu-item:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.menu-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.menu-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
  background: transparent;
}

/* Transitions */
.menu-fade-enter-active,
.menu-fade-leave-active {
  transition: all 0.2s ease;
}

.menu-fade-enter-from {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}

.menu-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .user-dropdown {
    background: rgba(26, 32, 44, 0.95);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .user-name {
    color: #f7fafc;
  }
  
  .user-email {
    color: #a0aec0;
  }
  
  .menu-divider {
    background: rgba(255, 255, 255, 0.1);
  }
  
  .menu-item {
    color: #e2e8f0;
  }
  
  .menu-item:hover {
    background: rgba(255, 255, 255, 0.05);
    color: #f7fafc;
  }
  
  .user-avatar-class {
    background: rgba(45, 55, 72, 0.95);
  }
}

/* Mobile responsive */
@media (max-width: 768px) {
  .user-dropdown {
    right: -8px;
    min-width: 240px;
  }
  
  .user-avatar,
  .user-avatar-fallback,
  .user-avatar-class {
    width: 44px;
    height: 44px;
  }
  
  .user-avatar-fallback {
    font-size: 18px;
  }
  
  .class-icon-img {
    width: 30px;
    height: 30px;
  }
}
</style>