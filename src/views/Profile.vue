<template>
  <div class="profile-container">
    <div class="profile-header">
      <h1>User Profile</h1>
      <p>Manage your account settings and preferences</p>
    </div>

    <div class="profile-content">
      <!-- User Information Section -->
      <div class="profile-section">
        <div class="section-header">
          <h2>Account Information</h2>
        </div>
        <div class="profile-card">
          <div class="user-avatar">
            <!-- Class Avatar -->
            <div 
              v-if="userStore.userAvatar?.type === 'class'" 
              class="avatar-class"
            >
              <div class="class-icon-background" :style="{ backgroundColor: getClassColor(userStore.userAvatar.class) }"></div>
              <div class="class-icon">
                <img 
                  :src="`/icons/${userStore.userAvatar.class}.gif`" 
                  :alt="getClassDisplayName(userStore.userAvatar.class)"
                  @error="handleImageError"
                />
              </div>
            </div>
            <!-- Google Photo Avatar -->
            <img v-else-if="userStore.userAvatar?.url" :src="userStore.userAvatar.url" :alt="user.email" />
            <!-- Fallback Avatar -->
            <div v-else class="avatar-placeholder">
              {{ userInitials }}
            </div>
          </div>
          <div class="user-info">
            <div class="info-row">
              <label>Full Name:</label>
              <span>{{ fullName || 'Not provided' }}</span>
            </div>
            <div class="info-row">
              <label>Email:</label>
              <span>{{ user?.email || 'Not provided' }}</span>
            </div>
            <div class="info-row">
              <label>Account Type:</label>
              <span class="role-badge" :class="user?.role">{{ user?.role || 'user' }}</span>
            </div>
            <div class="info-row">
              <label>Member Since:</label>
              <span>{{ formatDate(user?.created_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Display Settings Section -->
      <div class="profile-section">
        <div class="section-header">
          <h2>Display Settings</h2>
        </div>
        <div class="profile-card">
          <form @submit.prevent="saveProfile" class="profile-form">
            <div class="form-group">
              <label for="display-name">Display Name:</label>
              <input 
                id="display-name" 
                type="text" 
                v-model="localProfile.display_name"
                placeholder="Enter your display name"
                maxlength="50"
              />
              <small class="form-hint">
                This name will be used to represent you throughout the app. If not set, your real name will be used.
              </small>
            </div>

            <div class="form-group">
              <label class="checkbox-label">
                <input 
                  type="checkbox" 
                  v-model="localProfile.anonymous_mode"
                  class="checkbox-input"
                />
                <span class="checkbox-text">Keep myself anonymous</span>
              </label>
              <small class="form-hint">
                When enabled, your real name will never be displayed publicly. Only your display name (if set) or "Anonymous User" will be shown.
              </small>
            </div>

            <div class="form-group avatar-selector-group">
              <label for="avatar-selector">Choose Avatar:</label>
              <div class="avatar-selector-container">
                <!-- Current Selection Display -->
                <div class="current-avatar-display">
                  <div class="current-avatar-preview">
                    <!-- Class Avatar -->
                    <div 
                      v-if="localProfile.avatar_class" 
                      class="current-avatar class-avatar"
                    >
                      <div class="class-icon-background" :style="{ backgroundColor: getClassColor(localProfile.avatar_class) }"></div>
                      <div class="class-icon">
                        <img 
                          :src="`/icons/${localProfile.avatar_class}.gif`" 
                          :alt="getClassDisplayName(localProfile.avatar_class)"
                          @error="handleImageError"
                        />
                      </div>
                    </div>
                    <!-- Google Photo Avatar -->
                    <img v-else-if="user?.picture" :src="user.picture" :alt="user.email" class="current-avatar google-avatar" />
                    <!-- Fallback Avatar -->
                    <div v-else class="current-avatar avatar-placeholder">
                      {{ userInitials }}
                    </div>
                  </div>
                  <div class="current-avatar-info">
                    <span class="current-avatar-title">Current Avatar</span>
                    <span class="current-avatar-name">
                      {{ localProfile.avatar_class ? getClassDisplayName(localProfile.avatar_class) : 'Google Photo' }}
                    </span>
                  </div>
                </div>

                <!-- Avatar Options Grid -->
                <div class="avatar-options-section">
                  <h4 class="section-title">Select New Avatar</h4>
                  
                  <div class="avatar-options-grid">
                    <!-- Google Photo Option -->
                    <div class="avatar-option" 
                         :class="{ 'selected': !localProfile.avatar_class }"
                         @click="localProfile.avatar_class = null"
                         title="Use your Google profile photo">
                      <div class="avatar-preview google-option">
                        <img v-if="user?.picture || user?.avatar_url" :src="user.picture || user.avatar_url" :alt="user.email" />
                        <div v-else class="google-placeholder">
                          {{ userInitials }}
                        </div>
                      </div>
                      <span class="avatar-label">Google Photo</span>
                    </div>
                    
                    <!-- Class Icon Options -->
                    <div v-for="classObj in classList" 
                         :key="classObj.name"
                         class="avatar-option class-option"
                         :class="{ 'selected': localProfile.avatar_class === classObj.name.toLowerCase() }"
                         @click="localProfile.avatar_class = classObj.name.toLowerCase()"
                         :title="`Use ${classObj.name} class icon`">
                      <div class="avatar-preview class-preview">
                        <div class="class-icon-background" :style="{ backgroundColor: classObj.color }"></div>
                        <div class="class-icon">
                          <img 
                            :src="`/icons/${classObj.name.toLowerCase()}.gif`" 
                            :alt="classObj.name"
                            @error="handleImageError"
                            class="class-icon-img"
                          />
                        </div>
                      </div>
                      <span class="avatar-label">{{ classObj.name }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <small class="form-hint">
                Select a class icon to use as your avatar throughout the app, or keep your Google profile photo.
              </small>
            </div>

            <div class="form-actions">
              <button type="submit" class="btn btn-primary" :disabled="!profileChanged || isLoading">
                {{ isLoading ? 'Saving...' : 'Save Profile' }}
              </button>
              <button type="button" @click="resetProfile" class="btn btn-secondary">
                Reset
              </button>
            </div>
          </form>
          
          <!-- Display Settings Messages -->
          <div v-if="profileSuccessMessage" class="alert alert-success profile-alert">
            {{ profileSuccessMessage }}
          </div>
          <div v-if="profileErrorMessage" class="alert alert-error profile-alert">
            {{ profileErrorMessage }}
          </div>
        </div>
      </div>

      <!-- Preferences Section -->
      <div class="profile-section">
        <div class="section-header">
          <h2>App Preferences</h2>
        </div>
        <div class="profile-card">
          <form @submit.prevent="savePreferences" class="preferences-form">
            <div class="form-group">
              <label for="theme">Theme Preference:</label>
              <select id="theme" v-model="localPreferences.theme_preference">
                <option value="auto">Auto (System)</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </div>

            <div class="form-group">
              <label for="results-per-page">Results Per Page:</label>
              <select id="results-per-page" v-model="localPreferences.results_per_page">
                <option :value="10">10</option>
                <option :value="20">20</option>
                <option :value="50">50</option>
                <option :value="100">100</option>
              </select>
            </div>

            <div class="form-actions">
              <button type="submit" class="btn btn-primary" :disabled="!preferencesChanged || isLoading">
                {{ isLoading ? 'Saving...' : 'Save Preferences' }}
              </button>
              <button type="button" @click="resetPreferences" class="btn btn-secondary">
                Reset
              </button>
            </div>
          </form>
        </div>
      </div>

      <!-- Account Actions Section -->
      <div class="profile-section">
        <div class="section-header">
          <h2>Account Actions</h2>
        </div>
        <div class="profile-card">
          <div class="action-buttons">
            <button @click="refreshProfile" class="btn btn-secondary" :disabled="isLoading">
              {{ isLoading ? 'Refreshing...' : 'Refresh Profile' }}
            </button>
            <button @click="logout" class="btn btn-danger">
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Success/Error Messages -->
    <div v-if="successMessage" class="alert alert-success">
      {{ successMessage }}
    </div>
    <div v-if="errorMessage" class="alert alert-error">
      {{ errorMessage }}
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
// DISABLED: Spell system temporarily disabled for redesign
// import { useSpellsStore } from '@/stores/spells'

export default {
  name: 'Profile',
  setup() {
    const router = useRouter()
    const userStore = useUserStore()
    // DISABLED: Spell system temporarily disabled for redesign
    // const spellsStore = useSpellsStore()

    const isLoading = ref(false)
    const successMessage = ref('')
    const errorMessage = ref('')
    const profileSuccessMessage = ref('')
    const profileErrorMessage = ref('')
    const localPreferences = ref({ ...userStore.preferences })
    const localProfile = ref({
      display_name: userStore.user?.display_name || '',
      anonymous_mode: userStore.user?.anonymous_mode || false,
      avatar_class: userStore.user?.avatar_class || null
    })

    // Computed properties
    const user = computed(() => userStore.user)
    const fullName = computed(() => userStore.fullName)
    const displayName = computed(() => userStore.displayName)
    // DISABLED: Spell system temporarily disabled - using fallback class list
    const classList = computed(() => [
      { name: 'Warrior', id: 1, color: '#8e2d2d' },
      { name: 'Cleric', id: 2, color: '#ccccff' },
      { name: 'Paladin', id: 3, color: '#ffd700' },
      { name: 'Ranger', id: 4, color: '#228b22' },
      { name: 'ShadowKnight', id: 5, color: '#551a8b' },
      { name: 'Druid', id: 6, color: '#a0522d' },
      { name: 'Monk', id: 7, color: '#556b2f' },
      { name: 'Bard', id: 8, color: '#ff69b4' },
      { name: 'Rogue', id: 9, color: '#708090' },
      { name: 'Shaman', id: 10, color: '#20b2aa' },
      { name: 'Necromancer', id: 11, color: '#4b0082' },
      { name: 'Wizard', id: 12, color: '#1e90ff' },
      { name: 'Magician', id: 13, color: '#ff8c00' },
      { name: 'Enchanter', id: 14, color: '#9370db' },
      { name: 'Beastlord', id: 15, color: '#a52a2a' },
      { name: 'Berserker', id: 16, color: '#b22222' }
    ])

    const userInitials = computed(() => {
      if (userStore.fullName) {
        return userStore.fullName.split(' ').map(n => n[0]).join('').toUpperCase()
      }
      return userStore.user?.email?.charAt(0).toUpperCase() || 'U'
    })

    const preferencesChanged = computed(() => {
      return JSON.stringify(localPreferences.value) !== JSON.stringify(userStore.preferences)
    })
    
    const profileChanged = computed(() => {
      const currentProfile = {
        display_name: userStore.user?.display_name || '',
        anonymous_mode: userStore.user?.anonymous_mode || false,
        avatar_class: userStore.user?.avatar_class || null
      }
      return JSON.stringify(localProfile.value) !== JSON.stringify(currentProfile)
    })

    // Methods
    const formatDate = (dateString) => {
      if (!dateString) return 'Unknown'
      return new Date(dateString).toLocaleDateString()
    }

    const saveProfile = async () => {
      isLoading.value = true
      profileErrorMessage.value = ''
      profileSuccessMessage.value = ''

      // Client-side validation: anonymous mode requires display name
      if (localProfile.value.anonymous_mode && !localProfile.value.display_name?.trim()) {
        profileErrorMessage.value = 'Cannot enable anonymous mode without setting a display name first'
        isLoading.value = false
        setTimeout(() => {
          profileErrorMessage.value = ''
        }, 5000)
        return
      }

      try {
        await userStore.updateProfile(localProfile.value)
        profileSuccessMessage.value = 'Profile saved successfully!'
        setTimeout(() => {
          profileSuccessMessage.value = ''
        }, 3000)
      } catch (error) {
        profileErrorMessage.value = error.message || 'Failed to save profile'
        setTimeout(() => {
          profileErrorMessage.value = ''
        }, 5000)
      } finally {
        isLoading.value = false
      }
    }

    const savePreferences = async () => {
      isLoading.value = true
      errorMessage.value = ''
      successMessage.value = ''

      try {
        await userStore.updatePreferences(localPreferences.value)
        successMessage.value = 'Preferences saved successfully!'
        setTimeout(() => {
          successMessage.value = ''
        }, 3000)
      } catch (error) {
        errorMessage.value = error.message || 'Failed to save preferences'
        setTimeout(() => {
          errorMessage.value = ''
        }, 5000)
      } finally {
        isLoading.value = false
      }
    }

    const resetProfile = () => {
      localProfile.value = {
        display_name: userStore.user?.display_name || '',
        anonymous_mode: userStore.user?.anonymous_mode || false,
        avatar_class: userStore.user?.avatar_class || null
      }
    }

    const resetPreferences = () => {
      localPreferences.value = { ...userStore.preferences }
    }

    const refreshProfile = async () => {
      isLoading.value = true
      errorMessage.value = ''
      successMessage.value = ''

      try {
        await userStore.fetchUserProfile()
        localPreferences.value = { ...userStore.preferences }
        successMessage.value = 'Profile refreshed successfully!'
        setTimeout(() => {
          successMessage.value = ''
        }, 3000)
      } catch (error) {
        errorMessage.value = error.message || 'Failed to refresh profile'
        setTimeout(() => {
          errorMessage.value = ''
        }, 5000)
      } finally {
        isLoading.value = false
      }
    }

    const logout = async () => {
      await userStore.logout()
      router.push('/')
    }

    // DISABLED: Spell system temporarily disabled - using fallback class data
    const getClassColor = (className) => {
      if (!className) return '#667eea'
      const classObj = classList.value.find(cls => cls.name.toLowerCase() === className.toLowerCase())
      return classObj?.color || '#667eea'
    }

    const getClassInitial = (className) => {
      if (!className) return '?'
      return className.charAt(0).toUpperCase()
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

    // DISABLED: Spell system temporarily disabled - using fallback class data
    const getClassDisplayName = (className) => {
      if (!className) return ''
      const classObj = classList.value.find(cls => cls.name.toLowerCase() === className.toLowerCase())
      return classObj?.name || className.charAt(0).toUpperCase() + className.slice(1)
    }

    // Watch for changes in store data
    watch(() => userStore.preferences, (newPrefs) => {
      localPreferences.value = { ...newPrefs }
    }, { deep: true })
    
    watch(() => userStore.user, (newUser) => {
      if (newUser) {
        localProfile.value = {
          display_name: newUser.display_name || '',
          anonymous_mode: newUser.anonymous_mode || false,
          avatar_class: newUser.avatar_class || null
        }
      }
    }, { deep: true })

    // Initialize
    onMounted(async () => {
      // Redirect if not authenticated
      if (!userStore.isAuthenticated) {
        router.push('/')
        return
      }

      // Classes are statically defined in the store, so they should be available immediately

      // Refresh profile data
      try {
        await userStore.fetchUserProfile()
        localPreferences.value = { ...userStore.preferences }
        localProfile.value = {
          display_name: userStore.user?.display_name || '',
          anonymous_mode: userStore.user?.anonymous_mode || false,
          avatar_class: userStore.user?.avatar_class || null
        }
      } catch (error) {
        console.error('Failed to load profile:', error)
      }
    })

    return {
      user,
      fullName,
      displayName,
      userInitials,
      classList,
      localPreferences,
      localProfile,
      preferencesChanged,
      profileChanged,
      isLoading,
      successMessage,
      errorMessage,
      profileSuccessMessage,
      profileErrorMessage,
      formatDate,
      saveProfile,
      savePreferences,
      resetProfile,
      resetPreferences,
      refreshProfile,
      logout,
      getClassColor,
      getClassInitial,
      getClassDisplayName,
      handleImageError,
      userStore
      // DISABLED: spellsStore removed - spell system temporarily disabled
    }
  }
}
</script>

<style scoped>
.profile-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
}

.profile-header {
  text-align: center;
  margin-bottom: 40px;
}

.profile-header h1 {
  color: #2d3748;
  font-size: 2.5rem;
  font-weight: 600;
  margin-bottom: 8px;
}

.profile-header p {
  color: #4a5568;
  font-size: 1.1rem;
}

.profile-content {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.profile-section {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 0;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  overflow: hidden;
}

.section-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px 24px;
  margin: 0;
}

.section-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.profile-card {
  padding: 24px;
}

.user-avatar {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.user-avatar img {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid #667eea;
}

.avatar-placeholder {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 2rem;
  font-weight: 600;
}

.avatar-class {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3px solid #667eea;
  overflow: hidden;
  position: relative;
  background: rgba(255, 255, 255, 0.95);
}

.avatar-class .class-icon-background {
  position: absolute;
  inset: 0;
  opacity: 0.2;
}

.avatar-class .class-icon {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.avatar-class .class-icon img {
  width: 48px;
  height: 48px;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.avatar-class .class-initial {
  text-transform: uppercase;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
}

.info-row:last-child {
  border-bottom: none;
}

.info-row label {
  font-weight: 600;
  color: #2d3748;
}

.info-row span {
  color: #4a5568;
}

.role-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 500;
  text-transform: capitalize;
}

.role-badge.user {
  background: #e6fffa;
  color: #319795;
}

.role-badge.admin {
  background: #fed7d7;
  color: #c53030;
}

.preferences-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 600;
  color: #2d3748;
}

.form-group select {
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  background: white;
  color: #2d3748;
}

.form-group input {
  padding: 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 1rem;
  background: white;
  color: #2d3748;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-hint {
  color: #718096;
  font-size: 0.875rem;
  margin-top: 4px;
  line-height: 1.4;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  font-weight: 600;
  color: #2d3748;
}

.checkbox-input {
  width: 20px;
  height: 20px;
  border: 2px solid #e2e8f0;
  border-radius: 4px;
  cursor: pointer;
  accent-color: #667eea;
}

.checkbox-text {
  user-select: none;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.btn {
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  border: none;
  font-size: 1rem;
  transition: all 0.2s ease;
  display: inline-block;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5a67d8;
  transform: translateY(-1px);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.8);
  color: #4a5568;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.btn-secondary:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.95);
  transform: translateY(-1px);
}

.btn-danger {
  background: #e53e3e;
  color: white;
}

.btn-danger:hover {
  background: #c53030;
  transform: translateY(-1px);
}

.alert {
  padding: 16px;
  border-radius: 8px;
  margin-top: 20px;
  font-weight: 500;
}

.alert-success {
  background: #c6f6d5;
  color: #276749;
  border: 1px solid #9ae6b4;
}

.alert-error {
  background: #fed7d7;
  color: #c53030;
  border: 1px solid #feb2b2;
}

.profile-alert {
  margin-top: 16px;
  margin-bottom: 0;
}

/* Avatar selector styles */
.avatar-selector-container {
  display: flex;
  flex-direction: column;
  gap: 28px;
  padding: 24px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #f8f9fa;
}

.current-avatar-display {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 12px;
  border: 2px solid rgba(102, 126, 234, 0.1);
}

.current-avatar-preview {
  flex-shrink: 0;
}

.current-avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 3px solid #667eea;
}

.current-avatar.class-avatar {
  position: relative;
  background: rgba(255, 255, 255, 0.95);
}

.current-avatar.class-avatar .class-icon-background {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  opacity: 0.2;
}

.current-avatar.class-avatar .class-icon {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.current-avatar.class-avatar .class-icon img {
  width: 36px;
  height: 36px;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.current-avatar.google-avatar {
  object-fit: cover;
}

.current-avatar-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.current-avatar-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #667eea;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.current-avatar-name {
  font-size: 1.25rem;
  font-weight: 600;
  color: #2d3748;
}

.avatar-options-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
}

/* Scroll indicator at bottom of section */
.avatar-options-section::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  background: linear-gradient(to top, rgba(248, 249, 250, 0.9), transparent);
  pointer-events: none;
  z-index: 2;
  border-bottom-left-radius: 8px;
  border-bottom-right-radius: 8px;
}

.section-title {
  margin: 0;
  font-size: 1.125rem;
  font-weight: 600;
  color: #2d3748;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title::after {
  content: '↓ Scroll for more';
  font-size: 0.75rem;
  font-weight: 400;
  color: #718096;
  opacity: 0.8;
}

.avatar-options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 20px;
  max-height: 400px;
  overflow-y: auto;
  padding: 12px;
  padding-right: 8px;
  padding-bottom: 20px;
  position: relative;
}

/* Custom scrollbar */
.avatar-options-grid::-webkit-scrollbar {
  width: 8px;
}

.avatar-options-grid::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

.avatar-options-grid::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.5);
  border-radius: 4px;
}

.avatar-options-grid::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.7);
}

/* Remove the problematic ::after pseudo-element */

.avatar-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
  background: rgba(255, 255, 255, 0.6);
}

.avatar-option:hover {
  background: rgba(255, 255, 255, 0.95);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.avatar-option:hover .class-icon-background {
  opacity: 0.25;
}

.avatar-option.selected {
  border-color: #667eea;
  background: rgba(102, 126, 234, 0.15);
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.avatar-preview {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  overflow: hidden;
  border: 3px solid rgba(0, 0, 0, 0.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.avatar-preview.google-option img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.google-placeholder {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 1.75rem;
}

.avatar-preview.class-preview {
  position: relative;
  background: rgba(255, 255, 255, 0.95);
}

.class-icon-background {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  opacity: 0.15;
}

.avatar-preview.class-preview .class-icon {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.class-icon-img {
  width: 48px;
  height: 48px;
  object-fit: contain;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
}

.class-initial {
  font-size: 1.2rem;
  font-weight: 700;
  text-transform: uppercase;
}

.avatar-label {
  font-size: 0.9rem;
  font-weight: 600;
  text-align: center;
  color: #4a5568;
  line-height: 1.3;
  max-width: 100%;
  word-break: break-word;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .profile-header h1 {
    color: #f7fafc;
  }
  
  .profile-header p {
    color: #e2e8f0;
  }
  
  .profile-section {
    background: rgba(26, 32, 44, 0.95);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .profile-card {
    background: transparent;
  }
  
  .info-row {
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .info-row label {
    color: #f7fafc;
  }
  
  .info-row span {
    color: #e2e8f0;
  }
  
  .form-group label {
    color: #f7fafc;
  }
  
  .form-group input,
  .form-group select {
    background: rgba(45, 55, 72, 0.8);
    color: #f7fafc;
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .form-hint {
    color: #a0aec0;
  }
  
  .checkbox-label {
    color: #f7fafc;
  }
  
  .checkbox-input {
    border-color: rgba(255, 255, 255, 0.2);
  }
  
  .btn-secondary {
    background: rgba(45, 55, 72, 0.8);
    color: #e2e8f0;
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .btn-secondary:hover:not(:disabled) {
    background: rgba(45, 55, 72, 0.95);
  }
  
  .avatar-selector-container {
    background: rgba(45, 55, 72, 0.8);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .current-avatar-display {
    background: rgba(45, 55, 72, 0.6);
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .current-avatar-name {
    color: #f7fafc;
  }
  
  .current-avatar.class-avatar {
    background: rgba(45, 55, 72, 0.95);
  }
  
  .avatar-class {
    background: rgba(45, 55, 72, 0.95);
  }
  
  .section-title {
    color: #f7fafc;
    border-color: rgba(255, 255, 255, 0.1);
  }
  
  .avatar-option {
    background: rgba(45, 55, 72, 0.6);
  }
  
  .avatar-preview.class-preview {
    background: rgba(45, 55, 72, 0.95);
  }
  
  .avatar-options-section::after {
    background: linear-gradient(to top, rgba(26, 32, 44, 0.9), transparent);
  }
  
  .avatar-options-grid::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
  }
  
  .avatar-options-grid::-webkit-scrollbar-thumb {
    background: rgba(102, 126, 234, 0.3);
  }
  
  .avatar-options-grid::-webkit-scrollbar-thumb:hover {
    background: rgba(102, 126, 234, 0.5);
  }
  
  .avatar-option:hover {
    background: rgba(74, 85, 104, 0.8);
  }
  
  .avatar-option.selected {
    background: rgba(102, 126, 234, 0.2);
  }
  
  .avatar-label {
    color: #e2e8f0;
  }
}

/* Mobile responsive */
@media (max-width: 768px) {
  .profile-container {
    padding: 16px;
  }
  
  .profile-header h1 {
    font-size: 2rem;
  }
  
  .section-header {
    padding: 16px 20px;
  }
  
  .profile-card {
    padding: 20px;
  }
  
  .info-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .form-actions,
  .action-buttons {
    flex-direction: column;
  }
  
  .btn {
    width: 100%;
    text-align: center;
  }
}
</style>