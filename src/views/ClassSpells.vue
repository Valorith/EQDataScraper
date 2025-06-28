<template>
  <div class="main-container" :class="classInfo?.name.toLowerCase() || 'default'" :style="containerStyles">
    <div class="hero-section">
      <button @click="goHome" class="home-button">
        ← Back to Classes
      </button>
      
      <h1 class="class-title" :style="titleStyles">{{ className }} Spells</h1>
      <p class="class-subtitle">Norrath Compendium</p>
    </div>

    <div v-if="loading" class="loading-container" :class="{ 'transitioning': isTransitioning }">
      <div class="loading-spinner"></div>
      <p>{{ isTransitioning ? 'Switching classes...' : 'Loading spells...' }}</p>
      <div class="loading-progress"></div>
    </div>

    <div v-else-if="error" class="error-container">
      <p>{{ error }}</p>
      <button @click="retryLoad" class="retry-button">Retry</button>
    </div>

    <div v-else-if="spells.length === 0" class="no-spells">
      <p>No spells found for {{ className }}.</p>
      <button @click="scrapeClass" class="scrape-button">Scrape Data</button>
    </div>

    <div v-else class="spells-container">
      <!-- Level Matrix Navigation -->
      <nav class="level-navigator" aria-label="Level navigation">
        <h2 class="level-nav-title">Quick Level Navigation</h2>
        <div class="level-matrix" role="grid" aria-label="Level selection grid">
          <button
            v-for="level in 60"
            :key="level"
            :class="['level-cell', { 
              'available': hasSpellsAtLevel(level),
              'disabled': !hasSpellsAtLevel(level),
              'current': currentLevel === level
            }]"
            :disabled="!hasSpellsAtLevel(level)"
            :aria-label="hasSpellsAtLevel(level) ? `Jump to level ${level} spells` : `No spells available at level ${level}`"
            :title="hasSpellsAtLevel(level) ? `Click to view level ${level} spells` : `No spells at level ${level}`"
            @click="scrollToLevel(level)"
          >
            {{ level }}
          </button>
        </div>
      </nav>

      <div 
        v-for="(levelGroup, level) in groupedSpells" 
        :key="level"
        class="level-section"
        :id="`level-${level}`"
      >
        <div class="level-header">
          <h2 class="level-title">Level {{ level }}</h2>
          <div class="level-header-right">
            <span class="level-count">{{ levelGroup.length }} {{ levelGroup.length === 1 ? 'Spell' : 'Spells' }}</span>
            <button class="go-to-top-btn" @click="scrollToTop" title="Go to top of page">
              <span>Top</span>
              <span class="top-arrow">↑</span>
            </button>
          </div>
        </div>
        <div class="spells-grid">
          <div 
            v-for="spell in levelGroup" 
            :key="spell.name"
            class="spell-card"
          >
            <div class="spell-header">
              <div class="spell-title-section">
                <img 
                  v-if="spell.icon" 
                  :src="spell.icon" 
                  :alt="`${spell.name} icon`"
                  class="spell-icon"
                  @error="handleIconError"
                />
                <div class="spell-title-text">
                  <h3 class="spell-name">{{ spell.name }}</h3>
                  <span v-if="spell.mana" class="spell-mana">{{ spell.mana }} MP</span>
                </div>
              </div>
            </div>
            <div class="spell-details">
              <div class="spell-attributes">
                <div v-if="spell.spell_id" class="spell-attribute">
                  <span class="attribute-label">Spell ID:</span>
                  <div class="spell-id-container">
                    <span class="attribute-value">{{ spell.spell_id }}</span>
                    <button 
                      class="copy-btn" 
                      @click="copySpellId(spell.spell_id)" 
                      title="Copy Spell ID to clipboard"
                    >
                      📋
                    </button>
                  </div>
                </div>
                
                <div v-if="spell.skill" class="spell-attribute">
                  <span class="attribute-label">School:</span>
                  <span class="attribute-value">{{ spell.skill }}</span>
                </div>
                
                <div v-if="spell.target_type" class="spell-attribute" :class="getTargetTypeClass(spell.target_type)">
                  <span class="attribute-label">Target:</span>
                  <span class="attribute-value">{{ spell.target_type }}</span>
                </div>
                
                <div v-if="spell.mana" class="spell-attribute">
                  <span class="attribute-label">Mana Cost:</span>
                  <span class="attribute-value">{{ spell.mana }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useSpellsStore } from '../stores/spells'

// Debounce utility function
function debounce(func, delay) {
  let timeoutId
  return (...args) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func.apply(null, args), delay)
  }
}

export default {
  name: 'ClassSpells',
  props: {
    className: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const router = useRouter()
    const spellsStore = useSpellsStore()
    const loading = ref(false)
    const error = ref(null)
    const isTransitioning = ref(false)
    const currentLevel = ref(null)

    const classInfo = computed(() => {
      return spellsStore.getClassByName(props.className)
    })

    const containerStyles = computed(() => {
      const info = classInfo.value
      if (!info) return {}
      
      return {
        '--class-color': info.color,
        '--class-color-rgb': info.colorRgb
      }
    })

    const titleStyles = computed(() => {
      const info = classInfo.value
      if (!info) return {}
      
      return {
        '--class-color': info.color,
        '--class-color-rgb': info.colorRgb
      }
    })

    const spells = computed(() => {
      return spellsStore.getSpellsForClass(props.className)
    })

    const groupedSpells = computed(() => {
      const grouped = {}
      spells.value.forEach(spell => {
        const level = spell.level || 'Unknown'
        if (!grouped[level]) {
          grouped[level] = []
        }
        grouped[level].push(spell)
      })
      return grouped
    })

    const hasSpellsAtLevel = (level) => {
      return groupedSpells.value[level] && groupedSpells.value[level].length > 0
    }


    const scrollToLevel = (level) => {
      const element = document.getElementById(`level-${level}`)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' })
        currentLevel.value = level
        
        // Add highlight effect after scrolling completes
        setTimeout(() => {
          const levelHeader = element.querySelector('.level-header')
          if (levelHeader) {
            levelHeader.style.transform = 'scale(1.02)'
            levelHeader.style.boxShadow = '0 0 30px rgba(var(--class-color-rgb), 0.6)'
            setTimeout(() => {
              levelHeader.style.transform = ''
              levelHeader.style.boxShadow = ''
            }, 1000)
          }
        }, 500)
      }
    }

    const scrollToTop = () => {
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      })
      currentLevel.value = null
    }

    const goHome = () => {
      router.push('/')
    }

    // Handle natural scroll events
    const handleScroll = () => {
      // No blur effect - just placeholder for future scroll-based features
    }


    const getTargetTypeClass = (targetType) => {
      if (!targetType) return ''
      const type = targetType.toLowerCase()
      if (type.includes('self')) return 'target-self'
      if (type.includes('single')) return 'target-single'
      if (type.includes('area') && type.includes('target')) return 'target-aoe-target'
      if (type.includes('area') && type.includes('caster')) return 'target-aoe-caster'
      if (type.includes('group')) return 'target-group'
      return ''
    }

    const copySpellId = (spellId) => {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(spellId).then(() => {
          showCopyFeedback(spellId)
        }).catch(() => {
          fallbackCopy(spellId)
        })
      } else {
        fallbackCopy(spellId)
      }
    }

    const fallbackCopy = (spellId) => {
      const textArea = document.createElement('textarea')
      textArea.value = spellId
      textArea.style.position = 'absolute'
      textArea.style.left = '-9999px'
      document.body.appendChild(textArea)
      textArea.select()
      
      try {
        document.execCommand('copy')
        showCopyFeedback(spellId)
      } catch (err) {
        console.error('Failed to copy text: ', err)
      } finally {
        document.body.removeChild(textArea)
      }
    }

    const showCopyFeedback = (spellId) => {
      // Simple alert for now - could be enhanced with a toast notification
      alert(`Spell ID ${spellId} copied to clipboard!`)
    }

    const loadSpells = async (showLoading = true) => {
      if (showLoading) {
        loading.value = true
      }
      error.value = null
      
      try {
        await spellsStore.fetchSpellsForClass(props.className)
        
        // Wait for DOM updates before hiding loading
        await nextTick()
        
        // Small delay to prevent loading flash
        if (showLoading) {
          setTimeout(() => {
            loading.value = false
          }, 300)
        }
      } catch (err) {
        error.value = err.message || 'Failed to load spells'
        loading.value = false
      }
    }

    const retryLoad = () => {
      loadSpells()
    }

    const scrapeClass = async () => {
      loading.value = true
      error.value = null
      
      try {
        await spellsStore.scrapeAllClasses()
        // Don't show loading again immediately after scraping
        await loadSpells(false)
      } catch (err) {
        error.value = err.message || 'Failed to scrape spell data'
      } finally {
        loading.value = false
      }
    }

    // Debounced loading function to prevent rapid API calls
    const debouncedLoad = debounce(loadSpells, 300)
    
    onMounted(() => {
      loadSpells()
      window.addEventListener('scroll', handleScroll, { passive: true })
    })
    
    onUnmounted(() => {
      window.removeEventListener('scroll', handleScroll)
    })

    watch(() => props.className, (newClassName, oldClassName) => {
      if (newClassName !== oldClassName) {
        isTransitioning.value = true
        
        // Use debounced loading for route changes
        debouncedLoad()
        
        // Reset transition state after a delay
        setTimeout(() => {
          isTransitioning.value = false
        }, 500)
      }
    })

    const handleIconError = (event) => {
      // Hide the icon if it fails to load
      event.target.style.display = 'none'
    }

    return {
      loading,
      error,
      spells,
      groupedSpells,
      classInfo,
      containerStyles,
      titleStyles,
      isTransitioning,
      currentLevel,
      hasSpellsAtLevel,
      scrollToLevel,
      scrollToTop,
      goHome,
      getTargetTypeClass,
      copySpellId,
      retryLoad,
      scrapeClass,
      handleIconError
    }
  }
}
</script>

<style scoped>
/* Fallback for missing class colors */
.main-container {
  --class-color: var(--primary-color, #9370db);
  --class-color-rgb: var(--primary-rgb, 147, 112, 219);
}

.hero-section {
  text-align: center;
  margin-bottom: 60px;
  position: relative;
  background: transparent;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: -50%;
  left: 50%;
  transform: translateX(-50%);
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(var(--class-color-rgb), 0.4) 0%, transparent 70%);
  border-radius: 50%;
  filter: blur(60px);
  z-index: -1;
}

.home-button {
  position: absolute;
  top: 0;
  left: 0;
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  color: white;
  border: none;
  border-radius: 12px;
  padding: 12px 20px;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  box-shadow: 0 4px 12px rgba(var(--class-color-rgb), 0.3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: 'Inter', sans-serif;
  z-index: 1000;
}

.home-button::before {
  content: '';
  width: 0;
  height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-right: 8px solid white;
  transition: all 0.3s ease;
}

.home-button:hover {
  background: linear-gradient(135deg, rgba(var(--class-color-rgb), 0.95), var(--class-color));
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 8px 20px rgba(var(--class-color-rgb), 0.4);
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.6);
}

.class-title {
  font-family: 'Cinzel', serif;
  font-size: 4em;
  font-weight: 700;
  background: linear-gradient(135deg, var(--class-color) 0%, rgba(255,255,255,0.9) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 20px;
  text-shadow: 0 0 40px rgba(var(--class-color-rgb), 0.6);
  letter-spacing: 2px;
}

.class-subtitle {
  font-size: 1.4em;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 400;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.loading-container,
.error-container,
.no-spells {
  text-align: center;
  padding: 60px 20px;
  position: relative;
}

.loading-container {
  background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  margin: 2rem 0;
  transition: all 0.3s ease;
}

.loading-container.transitioning {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.1), rgba(var(--class-color-rgb), 0.05));
  border-color: rgba(var(--class-color-rgb), 0.2);
}

.loading-spinner {
  width: 60px;
  height: 60px;
  border: 4px solid rgba(var(--class-color-rgb), 0.2);
  border-top: 4px solid var(--class-color);
  border-radius: 50%;
  animation: spin 1.2s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
  margin: 0 auto 20px;
  position: relative;
}

.loading-spinner::before {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  right: 2px;
  bottom: 2px;
  border: 2px solid transparent;
  border-top: 2px solid rgba(var(--class-color-rgb), 0.5);
  border-radius: 50%;
  animation: spinReverse 0.8s linear infinite;
}

.loading-progress {
  width: 200px;
  height: 4px;
  background: rgba(var(--class-color-rgb), 0.2);
  border-radius: 2px;
  margin: 20px auto 0;
  overflow: hidden;
  position: relative;
}

.loading-progress::before {
  content: '';
  position: absolute;
  top: 0;
  left: -200px;
  width: 200px;
  height: 100%;
  background: linear-gradient(90deg, transparent, var(--class-color), transparent);
  animation: loadingProgress 2s ease-in-out infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes spinReverse {
  0% { transform: rotate(360deg); }
  100% { transform: rotate(0deg); }
}

@keyframes loadingProgress {
  0% { left: -200px; }
  50% { left: 200px; }
  100% { left: 200px; }
}

/* Level Navigator Styles */
.level-navigator {
  background: linear-gradient(145deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  padding: 2rem;
  margin-bottom: 3rem;
  position: relative;
  overflow: hidden;
}

.level-nav-title {
  font-family: 'Cinzel', serif;
  font-size: 1.8rem;
  font-weight: 600;
  color: var(--class-color);
  text-align: center;
  margin-bottom: 1.5rem;
  text-shadow: 0 0 20px rgba(var(--class-color-rgb), 0.4);
}

.level-matrix {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  grid-template-rows: repeat(6, 1fr);
  gap: 0.5rem;
  max-width: 600px;
  margin: 0 auto;
}

.level-cell {
  aspect-ratio: 1;
  background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  position: relative;
  overflow: hidden;
  color: rgba(255, 255, 255, 0.5);
  min-height: 40px;
  font-family: 'Inter', sans-serif;
  text-align: center;
  user-select: none;
}

.level-cell.available {
  background: linear-gradient(135deg, rgba(var(--class-color-rgb), 0.3), rgba(var(--class-color-rgb), 0.15));
  border-color: rgba(var(--class-color-rgb), 0.5);
  color: var(--text-light);
  font-weight: 700;
  box-shadow: 0 0 15px rgba(var(--class-color-rgb), 0.2);
}

.level-cell.available:hover {
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  color: white;
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 8px 25px rgba(var(--class-color-rgb), 0.6);
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.9);
}

.level-cell.disabled {
  background: linear-gradient(135deg, rgba(100, 100, 100, 0.1), rgba(80, 80, 80, 0.05));
  border-color: rgba(100, 100, 100, 0.15);
  color: rgba(180, 180, 180, 0.3);
  cursor: not-allowed;
  opacity: 0.4;
}

.level-cell.current {
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.9)) !important;
  color: white !important;
  border-color: rgba(255, 255, 255, 0.8) !important;
  box-shadow: 0 0 20px rgba(var(--class-color-rgb), 0.8) !important;
  text-shadow: 0 0 10px rgba(255, 255, 255, 1) !important;
  animation: currentLevel 2s ease-in-out infinite alternate;
}

@keyframes currentLevel {
  0% { box-shadow: 0 0 20px rgba(var(--class-color-rgb), 0.8); }
  100% { box-shadow: 0 0 30px rgba(var(--class-color-rgb), 1), 0 0 40px rgba(var(--class-color-rgb), 0.6); }
}

/* Enhanced Spell Cards */
.spell-attributes {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.spell-attribute {
  display: flex;
  flex-direction: column;
  background: rgba(var(--class-color-rgb), 0.05);
  padding: 0.75rem;
  border-radius: 8px;
  border-left: 3px solid var(--class-color);
  position: relative;
  transition: all 0.3s ease;
}

.spell-attribute:hover {
  background: rgba(var(--class-color-rgb), 0.1);
  transform: translateX(2px);
}

.attribute-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: 'Inter', sans-serif;
}

.attribute-value {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-dark);
  font-family: 'Crimson Text', serif;
}

.spell-id-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.copy-btn {
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.25rem;
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-left: 0.5rem;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.copy-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(var(--class-color-rgb), 0.5);
}

/* Target Type Color Coding */
.target-self { 
  background: rgba(255, 215, 0, 0.1) !important; 
  border-left-color: #ffd700 !important; 
}
.target-single { 
  background: rgba(255, 68, 68, 0.1) !important; 
  border-left-color: #ff4444 !important; 
}
.target-aoe-target { 
  background: rgba(34, 197, 94, 0.1) !important; 
  border-left-color: #22c55e !important; 
}
.target-aoe-caster { 
  background: rgba(59, 130, 246, 0.1) !important; 
  border-left-color: #3b82f6 !important; 
}
.target-group { 
  background: rgba(168, 85, 247, 0.1) !important; 
  border-left-color: #a855f7 !important; 
}

.retry-button,
.scrape-button {
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 1em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 20px;
}

.retry-button:hover,
.scrape-button:hover {
  background: linear-gradient(135deg, rgba(var(--class-color-rgb), 0.95), var(--class-color));
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(var(--class-color-rgb), 0.4);
}

.level-section {
  margin-bottom: 60px;
}

.level-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;
  padding: 1rem 2rem;
  background: linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.04));
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px;
  transition: all 0.3s ease;
  position: relative;
}

.level-title {
  font-family: 'Cinzel', serif;
  font-size: 2.2em;
  font-weight: 600;
  color: var(--class-color);
  text-shadow: 0 0 20px rgba(var(--class-color-rgb), 0.4);
  margin: 0;
}

.level-header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.level-count {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 500;
  background: rgba(var(--class-color-rgb), 0.1);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  border: 1px solid rgba(var(--class-color-rgb), 0.2);
}

.go-to-top-btn {
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  color: white;
  border: none;
  border-radius: 12px;
  padding: 0.75rem 1.25rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 12px rgba(var(--class-color-rgb), 0.3);
  font-family: 'Inter', sans-serif;
}

.go-to-top-btn:hover {
  background: linear-gradient(135deg, rgba(var(--class-color-rgb), 0.95), var(--class-color));
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 8px 20px rgba(var(--class-color-rgb), 0.5);
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.6);
}

.top-arrow {
  font-size: 1.1em;
  font-weight: bold;
  transition: transform 0.3s ease;
}

.go-to-top-btn:hover .top-arrow {
  transform: translateY(-2px);
}

.level-header::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 100px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--class-color), transparent);
}

.spells-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 25px;
}

.spell-card {
  background: linear-gradient(145deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(255,255,255,0.15);
  border-radius: 16px;
  padding: 25px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.spell-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--class-color), rgba(var(--class-color-rgb), 0.6));
}

.spell-card:hover {
  transform: translateY(-5px);
  border-color: rgba(var(--class-color-rgb), 0.4);
  box-shadow: 0 15px 40px rgba(var(--class-color-rgb), 0.2);
}

.spell-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.spell-title-section {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.spell-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 2px solid rgba(var(--class-color-rgb), 0.3);
  background: rgba(255, 255, 255, 0.1);
  object-fit: cover;
  transition: all 0.3s ease;
}

.spell-icon:hover {
  transform: scale(1.1);
  border-color: var(--class-color);
  box-shadow: 0 4px 12px rgba(var(--class-color-rgb), 0.4);
}

.spell-title-text {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex: 1;
}

.spell-name {
  font-family: 'Cinzel', serif;
  font-size: 1.4em;
  font-weight: 600;
  color: var(--text-dark);
  margin: 0;
}

.spell-mana {
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.9em;
  font-weight: 600;
  min-width: 60px;
  text-align: center;
}

.spell-details {
  color: var(--text-light);
  font-size: 0.95em;
  line-height: 1.6;
}

.spell-details p {
  margin: 8px 0;
}

.spell-cast-time,
.spell-duration,
.spell-range {
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}

.spell-description {
  color: var(--text-light);
  font-style: italic;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

/* Blur effect CSS removed */

@media (max-width: 768px) {
  .class-title { font-size: 3em; }
  .spells-grid { grid-template-columns: 1fr; }
  .spell-card { padding: 20px; }
  .home-button { position: relative; margin-bottom: 30px; }
}
</style> 