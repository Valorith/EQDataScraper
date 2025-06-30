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
            @click="openSpellModal(spell)"
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
                      @click.stop="copySpellId(spell.spell_id)" 
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
    
    <!-- Scroll Animation Overlay -->
    <div v-if="isScrolling" class="scroll-overlay">
      <div class="scroll-animation-container">
        <div class="scroll-class-icon">
          <img 
            :src="`/icons/${classInfo?.name.toLowerCase()}.gif`" 
            :alt="classInfo?.name"
            @error="handleScrollIconError"
          >
        </div>
        <div class="scroll-level-text">
          {{ currentLevel ? `Scrolling to Level ${currentLevel}` : 'Scrolling to Top' }}
        </div>
      </div>
    </div>
    
    <!-- Spell Detail Modal -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-container" @click.stop>
        <div class="modal-header">
          <div class="modal-title-section">
            <img 
              v-if="selectedSpell?.icon" 
              :src="selectedSpell.icon" 
              :alt="`${selectedSpell.name} icon`"
              class="modal-spell-icon"
            />
            <div>
              <h2 class="modal-spell-name">{{ selectedSpell?.name }}</h2>
              <p class="modal-spell-level">Level {{ selectedSpell?.level }}</p>
            </div>
          </div>
          <button @click="closeModal" class="modal-close-btn">
            <span>×</span>
          </button>
        </div>
        
        <div class="modal-content">
          <div v-if="loadingSpellDetails" class="modal-loading">
            <div class="modal-spinner"></div>
            <p>Loading spell details...</p>
          </div>
          
          <div v-else-if="spellDetailsError" class="modal-error">
            <p>{{ spellDetailsError }}</p>
            <button @click="fetchSpellDetails(selectedSpell.spell_id)" class="retry-btn">
              Retry
            </button>
          </div>
          
          <div v-else-if="spellDetails" class="modal-spell-details">
            <!-- Basic Info Grid -->
            <div class="modal-info-grid">
              <div class="modal-info-card">
                <span class="modal-info-label">Spell ID</span>
                <span class="modal-info-value">{{ selectedSpell.spell_id }}</span>
              </div>
              <div class="modal-info-card" v-if="selectedSpell.mana">
                <span class="modal-info-label">Mana Cost</span>
                <span class="modal-info-value">{{ selectedSpell.mana }}</span>
              </div>
              <div class="modal-info-card" v-if="selectedSpell.skill">
                <span class="modal-info-label">School</span>
                <span class="modal-info-value">{{ selectedSpell.skill }}</span>
              </div>
              <div class="modal-info-card" v-if="selectedSpell.target_type">
                <span class="modal-info-label">Target</span>
                <span class="modal-info-value">{{ selectedSpell.target_type }}</span>
              </div>
              <div class="modal-info-card" v-if="spellDetails.cast_time">
                <span class="modal-info-label">Cast Time</span>
                <span class="modal-info-value">{{ spellDetails.cast_time }}</span>
              </div>
              <div class="modal-info-card" v-if="spellDetails.duration">
                <span class="modal-info-label">Duration</span>
                <span class="modal-info-value">{{ spellDetails.duration }}</span>
              </div>
              <div class="modal-info-card" v-if="spellDetails.range">
                <span class="modal-info-label">Range</span>
                <span class="modal-info-value">{{ spellDetails.range }}</span>
              </div>
              <div class="modal-info-card" v-if="spellDetails.resist">
                <span class="modal-info-label">Resist</span>
                <span class="modal-info-value">{{ spellDetails.resist }}</span>
              </div>
            </div>
            
            <!-- Description -->
            <div v-if="spellDetails.description" class="modal-description">
              <h3>Description</h3>
              <p>{{ spellDetails.description }}</p>
            </div>
            
            <!-- Effects -->
            <div v-if="spellDetails.effects && spellDetails.effects.length" class="modal-effects">
              <h3>Effects</h3>
              <ul>
                <li v-for="(effect, index) in spellDetails.effects" :key="index">
                  {{ effect }}
                </li>
              </ul>
            </div>
            
            <!-- Reagents -->
            <div v-if="hasValidReagents" class="reagents-section">
              <h3 class="reagents-header">Reagents</h3>
              <div class="reagents-container">
                <div v-for="reagent in validReagents" :key="reagent.name" class="reagent-box">
                  <a :href="reagent.url" target="_blank" class="reagent-link">
                    <img 
                      v-if="reagent.icon" 
                      :src="reagent.icon" 
                      :alt="reagent.name"
                      class="reagent-icon"
                      @error="handleReagentIconError"
                    />
                    <span class="reagent-text">{{ reagent.name }} ↗ × ({{ reagent.quantity }})</span>
                  </a>
                </div>
              </div>
            </div>
            
            <!-- Items with Spell -->
            <div v-if="hasValidItemsWithSpell" class="items-with-spell-section">
              <h3 class="items-header">Items with Spell</h3>
              <div class="items-container">
                <div v-for="item in validItemsWithSpell" :key="item.item_id || item.name" class="item-box">
                  <a :href="item.url" target="_blank" class="item-link">
                    <img 
                      v-if="item.icon" 
                      :src="item.icon" 
                      :alt="item.name"
                      class="item-icon"
                      @error="handleItemIconError"
                    />
                    <span class="item-text">{{ item.name }} ↗</span>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <a 
            :href="`https://alla.clumsysworld.com/?a=spell&id=${selectedSpell?.spell_id}`" 
            target="_blank" 
            class="view-original-btn"
          >
            View on Alla Website
            <span class="external-icon">↗</span>
          </a>
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
    
    // Modal state
    const showModal = ref(false)
    const selectedSpell = ref(null)
    const spellDetails = ref(null)
    const loadingSpellDetails = ref(false)
    const spellDetailsError = ref(null)

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


    const isScrolling = ref(false)

    const scrollToLevel = (level) => {
      const element = document.getElementById(`level-${level}`)
      if (element) {
        // Start blur animation
        isScrolling.value = true
        currentLevel.value = level
        
        // Scroll to element
        element.scrollIntoView({ behavior: 'smooth', block: 'start' })
        
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
          
          // End blur animation after scroll and highlight are complete
          setTimeout(() => {
            isScrolling.value = false
          }, 500)
        }, 800)
      }
    }

    const scrollToTop = () => {
      // Start blur animation
      isScrolling.value = true
      currentLevel.value = null
      
      // Scroll to top
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      })
      
      // End blur animation after scroll completes
      setTimeout(() => {
        isScrolling.value = false
      }, 1000)
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
        const result = await spellsStore.fetchSpellsForClass(props.className)
        
        // Wait for DOM updates before hiding loading
        await nextTick()
        
        // Check if we actually got data
        const currentSpells = spellsStore.getSpellsForClass(props.className)
        
        if (showLoading) {
          // Only add delay if we're showing a loading state and actually have data
          if (currentSpells && currentSpells.length > 0) {
            // Shorter delay for better UX, and ensure loading is hidden
            setTimeout(() => {
              loading.value = false
            }, 150)
          } else {
            // No delay if no data - hide loading immediately
            loading.value = false
          }
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
      window.addEventListener('keydown', handleKeydown)
    })
    
    onUnmounted(() => {
      window.removeEventListener('scroll', handleScroll)
      window.removeEventListener('keydown', handleKeydown)
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

    const handleScrollIconError = (event) => {
      const fallbackUrl = `https://wiki.heroesjourneyemu.com/${event.target.alt.toLowerCase()}.gif`
      event.target.src = fallbackUrl
      event.target.onerror = () => {
        event.target.style.display = 'none'
      }
    }

    // Modal functions
    const openSpellModal = async (spell) => {
      selectedSpell.value = spell
      showModal.value = true
      spellDetails.value = null
      spellDetailsError.value = null
      
      if (spell.spell_id) {
        await fetchSpellDetails(spell.spell_id)
      }
    }

    const closeModal = () => {
      showModal.value = false
      selectedSpell.value = null
      spellDetails.value = null
      spellDetailsError.value = null
    }

    const fetchSpellDetails = async (spellId) => {
      loadingSpellDetails.value = true
      spellDetailsError.value = null

      try {
        const response = await fetch(`/api/spell-details/${spellId}?_t=${Date.now()}`, {
          headers: {
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
          }
        })
        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
        }
        
        const details = await response.json()
        console.log('Raw API response:', details)
        console.log('Components type:', typeof details.components)
        console.log('Components content:', details.components)
        
        // Force clean the components data
        if (details.components && Array.isArray(details.components)) {
          details.components = details.components.filter(c => c && typeof c === 'object' && c.name && c.url)
        }
        
        spellDetails.value = details
        
      } catch (error) {
        console.error('Error fetching spell details:', error)
        spellDetailsError.value = error.message || 'Failed to load spell details. Please try again.'
      } finally {
        loadingSpellDetails.value = false
      }
    }

    const parseSpellDetails = (doc) => {
      const details = {}
      
      // Try to find spell information from the page
      const tables = doc.querySelectorAll('table')
      
      for (const table of tables) {
        const rows = table.querySelectorAll('tr')
        
        for (const row of rows) {
          const cells = row.querySelectorAll('td')
          if (cells.length >= 2) {
            const label = cells[0]?.textContent?.trim()
            const value = cells[1]?.textContent?.trim()
            
            if (label && value) {
              switch (label.toLowerCase()) {
                case 'cast time:':
                case 'casting time:':
                  details.cast_time = value
                  break
                case 'duration:':
                  details.duration = value
                  break
                case 'range:':
                  details.range = value
                  break
                case 'resist:':
                case 'resist type:':
                  details.resist = value
                  break
                case 'description:':
                  details.description = value
                  break
              }
            }
          }
        }
      }
      
      // Try to find effects/components in different sections
      const effectsList = []
      const componentsList = []
      
      // Look for effect information
      const effectElements = doc.querySelectorAll('td, p, div')
      for (const elem of effectElements) {
        const text = elem.textContent?.trim()
        if (text && (text.includes('Effect:') || text.includes('Increases') || text.includes('Decreases'))) {
          effectsList.push(text)
        }
      }
      
      if (effectsList.length > 0) {
        details.effects = effectsList
      }
      
      // Look for component information
      const componentElements = doc.querySelectorAll('td, span')
      for (const elem of componentElements) {
        const text = elem.textContent?.trim()
        if (text && (text.includes('Component:') || text.includes('Reagent:'))) {
          componentsList.push(text.replace(/^(Component:|Reagent:)\s*/, ''))
        }
      }
      
      if (componentsList.length > 0) {
        details.components = componentsList
      }
      
      return details
    }

    // Handle escape key to close modal
    const handleKeydown = (event) => {
      if (event.key === 'Escape' && showModal.value) {
        closeModal()
      }
    }

    // Computed properties for reagents
    const validReagents = computed(() => {
      if (!spellDetails.value?.components || !Array.isArray(spellDetails.value.components)) {
        return []
      }
      return spellDetails.value.components.filter(c => 
        c && typeof c === 'object' && c.name && c.url
      )
    })

    const hasValidReagents = computed(() => {
      return validReagents.value.length > 0
    })

    // Computed properties for items with spell
    const validItemsWithSpell = computed(() => {
      if (!spellDetails.value?.items_with_spell || !Array.isArray(spellDetails.value.items_with_spell)) {
        return []
      }
      return spellDetails.value.items_with_spell.filter(item => 
        item && typeof item === 'object' && item.name && item.url
      )
    })

    const hasValidItemsWithSpell = computed(() => {
      return validItemsWithSpell.value.length > 0
    })

    // Method to handle item icon errors
    const handleItemIconError = (event) => {
      event.target.style.display = 'none'
    }

    // Method to handle reagent icon errors
    const handleReagentIconError = (event) => {
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
      isScrolling,
      hasSpellsAtLevel,
      scrollToLevel,
      scrollToTop,
      goHome,
      getTargetTypeClass,
      copySpellId,
      retryLoad,
      scrapeClass,
      handleIconError,
      handleScrollIconError,
      // Modal properties and methods
      showModal,
      selectedSpell,
      spellDetails,
      loadingSpellDetails,
      spellDetailsError,
      openSpellModal,
      closeModal,
      fetchSpellDetails,
      // Reagents
      validReagents,
      hasValidReagents,
      // Items with Spell
      validItemsWithSpell,
      hasValidItemsWithSpell,
      handleItemIconError,
      handleReagentIconError
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

/* Scroll Animation Overlay */
.scroll-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(12px);
  z-index: 1500;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: scrollOverlayFadeIn 0.3s ease-out;
}

@keyframes scrollOverlayFadeIn {
  from {
    opacity: 0;
    backdrop-filter: blur(0px);
  }
  to {
    opacity: 1;
    backdrop-filter: blur(12px);
  }
}

.scroll-animation-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  text-align: center;
}

.scroll-class-icon {
  width: 150px;
  height: 150px;
  border-radius: 24px;
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4px solid rgba(255, 255, 255, 0.6);
  box-shadow: 
    0 0 40px rgba(var(--class-color-rgb), 0.8),
    0 0 80px rgba(var(--class-color-rgb), 0.4);
  animation: scrollIconFloat 2s ease-in-out infinite;
  position: relative;
  overflow: hidden;
}

.scroll-class-icon::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255,255,255,0.3), transparent);
  transform: rotate(45deg);
  animation: scrollIconShimmer 2s ease-in-out infinite;
}

.scroll-class-icon img {
  width: 85%;
  height: 85%;
  object-fit: cover;
  border-radius: 16px;
  z-index: 1;
  position: relative;
  animation: scrollIconPulse 1.5s ease-in-out infinite;
}

.scroll-level-text {
  font-family: 'Cinzel', serif;
  font-size: 2rem;
  font-weight: 700;
  color: var(--class-color);
  text-shadow: 
    0 0 20px rgba(var(--class-color-rgb), 0.8),
    0 0 40px rgba(var(--class-color-rgb), 0.4);
  animation: scrollTextGlow 2s ease-in-out infinite alternate;
  letter-spacing: 1px;
}

@keyframes scrollIconFloat {
  0%, 100% { 
    transform: translateY(0px) scale(1);
  }
  50% { 
    transform: translateY(-20px) scale(1.05);
  }
}

@keyframes scrollIconShimmer {
  0% { 
    transform: rotate(45deg) translate(-200%, -200%);
  }
  50% { 
    transform: rotate(45deg) translate(0%, 0%);
  }
  100% { 
    transform: rotate(45deg) translate(200%, 200%);
  }
}

@keyframes scrollIconPulse {
  0%, 100% { 
    transform: scale(1);
    opacity: 1;
  }
  50% { 
    transform: scale(1.1);
    opacity: 0.9;
  }
}

@keyframes scrollTextGlow {
  0% { 
    text-shadow: 
      0 0 20px rgba(var(--class-color-rgb), 0.6),
      0 0 40px rgba(var(--class-color-rgb), 0.3);
  }
  100% { 
    text-shadow: 
      0 0 30px rgba(var(--class-color-rgb), 1),
      0 0 60px rgba(var(--class-color-rgb), 0.6),
      0 0 90px rgba(var(--class-color-rgb), 0.3);
  }
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
  animation: modalFadeIn 0.3s ease-out;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    backdrop-filter: blur(0px);
  }
  to {
    opacity: 1;
    backdrop-filter: blur(8px);
  }
}

.modal-container {
  background: linear-gradient(145deg, rgba(20, 25, 40, 0.95), rgba(15, 20, 35, 0.98));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(var(--class-color-rgb), 0.3);
  border-radius: 24px;
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5), 0 0 100px rgba(var(--class-color-rgb), 0.2);
  animation: modalSlideIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-50px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 2rem 2.5rem 1.5rem;
  border-bottom: 1px solid rgba(var(--class-color-rgb), 0.2);
  position: relative;
}

.modal-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 2.5rem;
  right: 2.5rem;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--class-color), transparent);
}

.modal-title-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.modal-spell-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  border: 3px solid var(--class-color);
  background: rgba(255, 255, 255, 0.1);
  object-fit: cover;
  box-shadow: 0 8px 20px rgba(var(--class-color-rgb), 0.4);
}

.modal-spell-name {
  font-family: 'Cinzel', serif;
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--class-color);
  margin: 0;
  text-shadow: 0 0 20px rgba(var(--class-color-rgb), 0.6);
}

.modal-spell-level {
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.8);
  margin: 0.5rem 0 0 0;
  font-weight: 500;
}

.modal-close-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.5rem;
  font-weight: bold;
}

.modal-close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
  color: white;
  transform: scale(1.1);
}

.modal-content {
  padding: 2rem 2.5rem;
}

.modal-loading {
  text-align: center;
  padding: 3rem 0;
}

.modal-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(var(--class-color-rgb), 0.2);
  border-top: 4px solid var(--class-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

.modal-error {
  text-align: center;
  padding: 2rem 0;
  color: #ff6b6b;
}

.modal-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.modal-info-card {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.1), rgba(var(--class-color-rgb), 0.05));
  border: 1px solid rgba(var(--class-color-rgb), 0.3);
  border-radius: 12px;
  padding: 1.5rem;
  position: relative;
  transition: all 0.3s ease;
}

.modal-info-card:hover {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.15), rgba(var(--class-color-rgb), 0.08));
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(var(--class-color-rgb), 0.2);
}

.modal-info-label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: 'Inter', sans-serif;
}

.modal-info-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--class-color);
  font-family: 'Crimson Text', serif;
  text-shadow: 0 0 10px rgba(var(--class-color-rgb), 0.3);
}

.modal-description,
.modal-effects,
.modal-reagents-section {
  margin-bottom: 2rem;
}

.modal-description h3,
.modal-effects h3,
.reagents-title {
  font-family: 'Cinzel', serif;
  font-size: 1.5rem;
  color: var(--class-color);
  margin-bottom: 1rem;
  text-shadow: 0 0 15px rgba(var(--class-color-rgb), 0.4);
}

.modal-description p {
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.6;
  font-size: 1rem;
}

.modal-effects ul {
  list-style: none;
  padding: 0;
}

.modal-effects li {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
  border-left: 3px solid var(--class-color);
  padding: 1rem;
  margin-bottom: 0.5rem;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.9);
  transition: all 0.3s ease;
}

.modal-effects li:hover {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.1), rgba(var(--class-color-rgb), 0.05));
  transform: translateX(5px);
}

.components-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.component-item {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
  border: 1px solid rgba(var(--class-color-rgb), 0.2);
  border-radius: 8px;
  padding: 1rem;
  color: rgba(255, 255, 255, 0.9);
  text-align: center;
  transition: all 0.3s ease;
}

.component-item:hover {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.1), rgba(var(--class-color-rgb), 0.05));
  border-color: rgba(var(--class-color-rgb), 0.4);
  transform: translateY(-2px);
}

.reagents-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.reagent-item {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
  border: 1px solid rgba(var(--class-color-rgb), 0.2);
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.reagent-item:hover {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.1), rgba(var(--class-color-rgb), 0.05));
  border-color: rgba(var(--class-color-rgb), 0.4);
  transform: translateY(-2px);
}

.reagent-name-link {
  color: #ffffff;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
  position: relative;
  text-shadow: 0 0 4px rgba(0, 0, 0, 0.8);
}

.reagent-name-link:hover {
  color: var(--class-color);
  text-shadow: 0 0 8px rgba(var(--class-color-rgb), 0.6);
  transform: translateY(-1px);
}

.reagent-name-link::after {
  content: '↗';
  margin-left: 0.3rem;
  font-size: 0.8rem;
  opacity: 0.7;
  transition: opacity 0.3s ease;
}

.reagent-name-link:hover::after {
  opacity: 1;
}

.reagent-count {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
  font-weight: 500;
}

.reagents-section {
  margin-bottom: 2rem;
}

.reagents-header {
  font-family: 'Cinzel', serif;
  font-size: 1.5rem;
  color: var(--class-color);
  margin-bottom: 1rem;
  text-shadow: 0 0 15px rgba(var(--class-color-rgb), 0.4);
}

.reagents-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.reagent-box {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
  border: 1px solid rgba(var(--class-color-rgb), 0.2);
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
  transition: all 0.3s ease;
}

.reagent-box:hover {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.1), rgba(var(--class-color-rgb), 0.05));
  border-color: rgba(var(--class-color-rgb), 0.4);
  transform: translateY(-2px);
}

.reagent-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #ffffff;
  text-decoration: none;
  font-weight: 600;
  text-shadow: 0 0 4px rgba(0, 0, 0, 0.8);
  transition: all 0.3s ease;
}

.reagent-link:hover {
  color: var(--class-color);
  text-shadow: 0 0 8px rgba(var(--class-color-rgb), 0.6);
}

.reagent-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.05);
  object-fit: cover;
  transition: all 0.3s ease;
}

.reagent-icon:hover {
  border-color: rgba(var(--class-color-rgb), 0.5);
  transform: scale(1.05);
}

.reagent-text {
  flex: 1;
  line-height: 1.3;
}

/* Items with Spell Section */
.items-with-spell-section {
  margin-top: 2rem;
  padding: 1.5rem;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.01));
  border: 1px solid rgba(var(--class-color-rgb), 0.15);
  border-radius: 16px;
  backdrop-filter: blur(10px);
}

.items-header {
  font-family: 'Cinzel', serif;
  font-size: 1.5rem;
  color: var(--class-color);
  margin-bottom: 1rem;
  text-shadow: 0 0 15px rgba(var(--class-color-rgb), 0.4);
}

.items-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.item-box {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
  border: 1px solid rgba(var(--class-color-rgb), 0.2);
  border-radius: 8px;
  padding: 1rem;
  transition: all 0.3s ease;
}

.item-box:hover {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.1), rgba(var(--class-color-rgb), 0.05));
  border-color: rgba(var(--class-color-rgb), 0.4);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(var(--class-color-rgb), 0.2);
}

.item-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #ffffff;
  text-decoration: none;
  font-weight: 600;
  text-shadow: 0 0 4px rgba(0, 0, 0, 0.8);
  transition: all 0.3s ease;
}

.item-link:hover {
  color: var(--class-color);
  text-shadow: 0 0 8px rgba(var(--class-color-rgb), 0.6);
}

.item-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.05);
  object-fit: cover;
  transition: all 0.3s ease;
}

.item-icon:hover {
  border-color: rgba(var(--class-color-rgb), 0.5);
  transform: scale(1.05);
}

.item-text {
  flex: 1;
  line-height: 1.3;
}

.modal-footer {
  padding: 1.5rem 2.5rem 2rem;
  border-top: 1px solid rgba(var(--class-color-rgb), 0.2);
  text-align: center;
  position: relative;
}

.modal-footer::before {
  content: '';
  position: absolute;
  top: 0;
  left: 2.5rem;
  right: 2.5rem;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--class-color), transparent);
}

.view-original-btn {
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  color: white;
  border: none;
  border-radius: 12px;
  padding: 1rem 2rem;
  font-size: 1rem;
  font-weight: 600;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 15px rgba(var(--class-color-rgb), 0.4);
}

.view-original-btn:hover {
  background: linear-gradient(135deg, rgba(var(--class-color-rgb), 0.95), var(--class-color));
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 8px 25px rgba(var(--class-color-rgb), 0.6);
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
}

.external-icon {
  font-size: 1.2em;
  transition: transform 0.3s ease;
}

.view-original-btn:hover .external-icon {
  transform: translate(2px, -2px);
}

.retry-btn {
  background: linear-gradient(135deg, #ff6b6b, #ee5a24);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 1rem;
}

.retry-btn:hover {
  background: linear-gradient(135deg, #ee5a24, #ff6b6b);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
}

/* Add cursor pointer to spell cards */
.spell-card {
  cursor: pointer;
}

@media (max-width: 768px) {
  .class-title { font-size: 3em; }
  .spells-grid { grid-template-columns: 1fr; }
  .spell-card { padding: 20px; }
  .home-button { position: relative; margin-bottom: 30px; }
  
  .modal-container {
    margin: 1rem;
    max-height: 95vh;
  }
  
  .modal-header {
    padding: 1.5rem;
  }
  
  .modal-content {
    padding: 1.5rem;
  }
  
  .modal-footer {
    padding: 1rem 1.5rem;
  }
  
  .modal-spell-name {
    font-size: 2rem;
  }
  
  .modal-info-grid {
    grid-template-columns: 1fr;
  }
  
  .components-grid {
    grid-template-columns: 1fr;
  }
}
</style> 