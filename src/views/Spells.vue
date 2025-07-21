<template>
  <div class="spells-page">
    <div class="page-header">
      <h1>Spell Database</h1>
      <p class="subtitle">Search and explore spells from the database</p>
    </div>

    <!-- Search Section -->
    <div class="search-section">
      <div class="search-container">
        <div class="search-input-group">
          <input
            v-model="searchQuery"
            @keyup.enter="performSearch()"
            type="text"
            placeholder="Search spells by name..."
            class="search-input"
          />
          <button @click="performSearch()" class="search-button" :disabled="searching">
            <i :class="searching ? 'fas fa-spinner fa-spin' : 'fas fa-search'"></i>
            <span class="search-button-text">{{ searching ? 'Searching...' : 'Search' }}</span>
          </button>
        </div>
        
        <!-- Basic Filters -->
        <div class="filters-container">
          <div class="filter-group">
            <label for="class-filter">Class:</label>
            <select id="class-filter" v-model="selectedClass" class="filter-select">
              <option value="">All Classes</option>
              <option value="warrior">Warrior</option>
              <option value="cleric">Cleric</option>
              <option value="paladin">Paladin</option>
              <option value="ranger">Ranger</option>
              <option value="shadowknight">Shadow Knight</option>
              <option value="druid">Druid</option>
              <option value="monk">Monk</option>
              <option value="bard">Bard</option>
              <option value="rogue">Rogue</option>
              <option value="shaman">Shaman</option>
              <option value="necromancer">Necromancer</option>
              <option value="wizard">Wizard</option>
              <option value="magician">Magician</option>
              <option value="enchanter">Enchanter</option>
              <option value="beastlord">Beastlord</option>
              <option value="berserker">Berserker</option>
            </select>
          </div>
          
          <div class="filter-group">
            <label for="level-min">Min Level:</label>
            <input 
              id="level-min"
              v-model="minLevel" 
              type="number" 
              class="filter-input"
              placeholder="1"
              min="1"
              max="255"
            />
          </div>
          
          <div class="filter-group">
            <label for="level-max">Max Level:</label>
            <input 
              id="level-max"
              v-model="maxLevel" 
              type="number" 
              class="filter-input"
              placeholder="60"
              min="1"
              max="255"
            />
          </div>
          
          <div class="filter-group">
            <label for="skill-filter">Skill:</label>
            <select id="skill-filter" v-model="selectedSkill" class="filter-select">
              <option value="">All Skills</option>
              <option value="0">Conjuration</option>
              <option value="1">Divination</option>
              <option value="2">Abjuration</option>
              <option value="3">Alteration</option>
              <option value="4">Evocation</option>
              <option value="5">Singing</option>
              <option value="6">Percussion</option>
              <option value="7">Stringed</option>
              <option value="8">Brass</option>
              <option value="9">Wind</option>
            </select>
          </div>
          
          <button @click="clearFilters" class="clear-filters-button">
            <i class="fas fa-times"></i>
            Clear Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Spell Matrix Section -->
    <div v-if="!searching" class="spell-matrix-section">
      <div class="matrix-header">
        <h3>Spell Matrix</h3>
        <p class="matrix-subtitle">
          <span v-if="matrixMode === 'classes'">Select a class to view spells by level</span>
          <span v-else>Click and drag across a level range or click a single level.</span>
        </p>
        <button 
          v-if="matrixMode === 'levels'" 
          @click="resetMatrix" 
          class="matrix-reset-button"
          title="Back to class selection"
        >
          <i class="fas fa-arrow-left"></i>
          Back to Classes
        </button>
      </div>
      
      <!-- Class Selection Grid -->
      <div v-if="matrixMode === 'classes'" class="matrix-classes-grid">
        <div 
          v-for="className in availableClasses" 
          :key="className"
          @click="selectMatrixClass(className)"
          class="matrix-class-item"
          :title="`View ${getClassFullName(className)} spells by level`"
        >
          <img 
            :src="`/icons/${className}.gif`" 
            :alt="`${className} icon`"
            class="matrix-class-icon"
            @error="handleIconError"
          />
          <span class="matrix-class-name">{{ getClassAbbreviation(className) }}</span>
        </div>
      </div>
      
      <!-- Level Selection Grid -->
      <div v-if="matrixMode === 'levels'" class="matrix-levels-grid">
        <div class="matrix-selected-class">
          <img 
            :src="`/icons/${selectedMatrixClass}.gif`" 
            :alt="`${selectedMatrixClass} icon`"
            class="matrix-selected-class-icon"
            @error="handleIconError"
          />
          <span class="matrix-selected-class-name">{{ getClassFullName(selectedMatrixClass) }} Spells</span>
        </div>
        
        <div class="matrix-levels-container">
          <div 
            v-for="level in matrixLevels" 
            :key="level"
            @mousedown="startLevelDrag(level)"
            @mouseenter="handleLevelHover(level)"
            @mouseup="endLevelDrag(level)"
            @click="handleLevelClick(level)"
            :class="[
              'matrix-level-item',
              { 
                'selected': selectedLevel === level,
                'in-range': isLevelInSelectedRange(level),
                'drag-start': dragStartLevel === level,
                'drag-current': dragCurrentLevel === level
              }
            ]"
            :title="getLevelTooltip(level)"
          >
            {{ level }}
          </div>
        </div>
      </div>
    </div>

    <!-- Decorative Image Section -->
    <div v-if="!searching && !searchPerformed" class="decorative-image-container">
      <div class="image-wrapper">
        <img 
          src="@/assets/images/goblin-scholar.png" 
          alt="Goblin scholar studying ancient tomes"
          class="decorative-image"
        />
        <div class="image-overlay">
          <h2 class="overlay-title">Spell Search</h2>
          <p class="overlay-subtitle">Discover powerful magic and ancient incantations</p>
        </div>
      </div>
    </div>

    <!-- Loading Modals (outside conditional section for initial search) -->
    <LoadingModal 
      :visible="searching && !paginating"
      text="Searching"
      :timeoutMs="45000"
      @timeout="onSearchTimeout"
    />
    <!-- Pagination Loading Modal -->
    <LoadingModal 
      :visible="paginating"
      text="Loading"
      :timeoutMs="30000"
      @timeout="onPaginationTimeout"
    />

    <!-- Search Results Section -->
    <div v-if="searching || searchPerformed" class="results-section">
      <!-- Results Header -->
      <div class="results-header">
        <div class="results-title-section">
          <h2>Search Results</h2>
          <div class="results-info">
            <span v-if="searchResults.length > 0">
              {{ totalCount }} spells found
            </span>
            <span v-if="searchQuery">(searching for "{{ searchQuery }}")</span>
            <span v-else-if="!searching && searchPerformed && searchResults.length === 0">
              No spells found
            </span>
          </div>
        </div>
        
        <!-- View Toggle -->
        <div class="view-toggle-container">
          <span class="view-toggle-label">View:</span>
          <div class="view-toggle">
            <button 
              @click="viewMode = 'list'" 
              :class="['view-button', { active: viewMode === 'list' }]"
              title="List View"
            >
              <i class="fas fa-list"></i>
              <span class="view-button-text">List</span>
            </button>
            <button 
              @click="viewMode = 'grid'" 
              :class="['view-button', { active: viewMode === 'grid' }]"
              title="Grid View"
            >
              <i class="fas fa-th"></i>
              <span class="view-button-text">Grid</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Top Pagination -->
      <div v-if="totalPages > 1 && !searching && searchResults.length > 0" class="pagination pagination-top">
        <button 
          @click="changePage(currentPage - 1)"
          :disabled="currentPage <= 1"
          class="page-button"
        >
          <i class="fas fa-chevron-left"></i>
          Previous
        </button>
        
        <div class="page-info">
          Page {{ currentPage }} of {{ totalPages }}
        </div>
        
        <button 
          @click="changePage(currentPage + 1)"
          :disabled="currentPage >= totalPages"
          class="page-button"
        >
          Next
          <i class="fas fa-chevron-right"></i>
        </button>
      </div>

      <!-- Spell Results -->
      <div v-if="searchResults.length > 0">
        <!-- Matrix Search Results - Grouped by Level -->
        <div v-if="isMatrixSearch && spellsByLevel.length > 0" class="matrix-spell-results">
          <div v-for="levelGroup in spellsByLevel" :key="levelGroup.level" class="level-group">
            <!-- Level Separator -->
            <div class="level-separator">
              <div class="level-separator-line"></div>
              <div class="level-separator-content">
                <div class="level-separator-info">
                  <span class="level-separator-text">Level {{ levelGroup.level }}</span>
                  <span class="level-separator-count">({{ levelGroup.spells.length }} spell{{ levelGroup.spells.length !== 1 ? 's' : '' }})</span>
                </div>
                <button @click="scrollToTopOfResults" class="level-separator-to-top" title="Scroll to top of search results">
                  <i class="fas fa-arrow-up"></i>
                  <span class="to-top-text">To Top</span>
                </button>
              </div>
              <div class="level-separator-line"></div>
            </div>
            
            <!-- Spells for this level -->
            <div :class="['spell-results', viewMode]">
              <div v-for="spell in levelGroup.spells" :key="spell.spell_id" class="spell-card" @click="openSpellModal(spell)">
                <div class="spell-main-content">
                  <div class="spell-header">
                    <div class="spell-icon-container">
                      <img 
                        v-if="hasSpellIcon(spell)"
                        :src="getSpellIconUrl(spell)"
                        :alt="`${spell.name} icon`"
                        class="spell-icon"
                        @error="handleSpellIconError"
                      />
                      <div v-else class="spell-icon-placeholder">
                        <i class="fas fa-magic"></i>
                      </div>
                    </div>
                    <div class="spell-header-text">
                      <h3 class="spell-name">{{ spell.name }}</h3>
                    </div>
                  </div>
                  
                  <div class="spell-details">
                    <div class="spell-detail-row">
                      <span class="detail-label">Mana:</span>
                      <span class="detail-value">{{ spell.mana || 'N/A' }}</span>
                    </div>
                    
                    <div class="spell-detail-row">
                      <span class="detail-label">Skill:</span>
                      <span class="detail-value">{{ getSkillName(spell.skill) }}</span>
                    </div>
                    
                    <div class="spell-detail-row">
                      <span class="detail-label">Target:</span>
                      <span class="detail-value">{{ getTargetType(spell.targettype) }}</span>
                    </div>
                  </div>
                </div>
                
                <!-- Class Level Requirements -->
                <div class="spell-class-levels">
                  <div class="class-levels-container">
                    <button 
                      v-if="getValidClasses(spell).length > 3"
                      @click.stop="scrollClassCards(spell.spell_id, 'left')"
                      class="class-scroll-arrow class-scroll-left"
                      :style="{ opacity: canScrollLeft(spell.spell_id) ? 1 : 0.3 }"
                    >
                      <i class="fas fa-chevron-left"></i>
                    </button>
                    
                    <div 
                      class="class-levels-grid" 
                      :ref="`classGrid${spell.spell_id}`" 
                      @scroll="updateScrollState(spell.spell_id)"
                      @wheel="handleWheelScroll($event, spell.spell_id)"
                    >
                      <template v-for="(level, className) in getOrderedClassLevels(spell)" :key="className">
                        <div 
                          v-if="level && level !== 255"
                          :class="[
                            'class-level', 
                            'available',
                            { 'selected-class': className === (selectedClass || selectedMatrixClass) }
                          ]"
                          :style="getClassCardWidthStyle(spell)"
                          :title="`${getClassAbbreviation(className)}: Level ${level}`"
                        >
                          <img 
                            :src="`/icons/${className}.gif`" 
                            :alt="`${className} icon`"
                            class="class-icon"
                            @error="handleIconError"
                          />
                          <span class="class-abbrev">{{ getClassAbbreviation(className) }}</span>
                          <span class="class-level-value">lvl {{ level }}</span>
                        </div>
                      </template>
                    </div>
                    
                    <button 
                      v-if="getValidClasses(spell).length > 3"
                      @click.stop="scrollClassCards(spell.spell_id, 'right')"
                      class="class-scroll-arrow class-scroll-right"
                      :style="{ opacity: canScrollRight(spell.spell_id) ? 1 : 0.3 }"
                    >
                      <i class="fas fa-chevron-right"></i>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Regular Search Results - Normal Display -->
        <div v-else :class="['spell-results', viewMode]">
          <div v-for="spell in searchResults" :key="spell.spell_id" class="spell-card" @click="openSpellModal(spell)">
            <div class="spell-main-content">
              <div class="spell-header">
                <div class="spell-icon-container">
                  <img 
                    v-if="hasSpellIcon(spell)"
                    :src="getSpellIconUrl(spell)"
                    :alt="`${spell.name} icon`"
                    class="spell-icon"
                    @error="handleSpellIconError"
                  />
                  <div v-else class="spell-icon-placeholder">
                    <i class="fas fa-magic"></i>
                  </div>
                </div>
                <div class="spell-header-text">
                  <h3 class="spell-name">{{ spell.name }}</h3>
                </div>
              </div>
              
              <div class="spell-details">
                <div class="spell-detail-row">
                  <span class="detail-label">Mana:</span>
                  <span class="detail-value">{{ spell.mana || 'N/A' }}</span>
                </div>
                
                <div class="spell-detail-row">
                  <span class="detail-label">Skill:</span>
                  <span class="detail-value">{{ getSkillName(spell.skill) }}</span>
                </div>
                
                <div class="spell-detail-row">
                  <span class="detail-label">Target:</span>
                  <span class="detail-value">{{ getTargetType(spell.targettype) }}</span>
                </div>
              </div>
            </div>
            
            <!-- Class Level Requirements -->
            <div class="spell-class-levels">
              <div class="class-levels-container">
                <button 
                  v-if="getValidClasses(spell).length > 3"
                  @click.stop="scrollClassCards(spell.spell_id, 'left')"
                  class="class-scroll-arrow class-scroll-left"
                  :style="{ opacity: canScrollLeft(spell.spell_id) ? 1 : 0.3 }"
                >
                  <i class="fas fa-chevron-left"></i>
                </button>
                
                <div 
                  class="class-levels-grid" 
                  :ref="`classGrid${spell.spell_id}`" 
                  @scroll="updateScrollState(spell.spell_id)"
                  @wheel="handleWheelScroll($event, spell.spell_id)"
                >
                  <template v-for="(level, className) in getOrderedClassLevels(spell)" :key="className">
                    <div 
                      v-if="level && level !== 255"
                      :class="[
                        'class-level', 
                        'available',
                        { 'selected-class': className === (selectedClass || selectedMatrixClass) }
                      ]"
                      :style="getClassCardWidthStyle(spell)"
                      :title="`${getClassAbbreviation(className)}: Level ${level}`"
                    >
                      <img 
                        :src="`/icons/${className}.gif`" 
                        :alt="`${className} icon`"
                        class="class-icon"
                        @error="handleIconError"
                      />
                      <span class="class-abbrev">{{ getClassAbbreviation(className) }}</span>
                      <span class="class-level-value">lvl {{ level }}</span>
                    </div>
                  </template>
                </div>
                
                <button 
                  v-if="getValidClasses(spell).length > 3"
                  @click.stop="scrollClassCards(spell.spell_id, 'right')"
                  class="class-scroll-arrow class-scroll-right"
                  :style="{ opacity: canScrollRight(spell.spell_id) ? 1 : 0.3 }"
                >
                  <i class="fas fa-chevron-right"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="searchPerformed && totalPages > 1 && !searching" class="pagination">
        <button 
          @click="changePage(currentPage - 1)"
          :disabled="currentPage <= 1"
          class="page-button"
        >
          <i class="fas fa-chevron-left"></i>
          Previous
        </button>
        
        <div class="page-info">
          Page {{ currentPage }} of {{ totalPages }}
        </div>
        
        <button 
          @click="changePage(currentPage + 1)"
          :disabled="currentPage >= totalPages"
          class="page-button"
        >
          Next
          <i class="fas fa-chevron-right"></i>
        </button>
      </div>
    </div>

    <!-- Spell Details Modal -->
    <div v-if="selectedSpellDetail" class="modal-overlay" @click="closeSpellModal">
      <div class="modal-content spell-modal" @click.stop>
        <div class="modal-header">
          <div class="modal-header-content">
            <div class="spell-icon-modal-container">
              <img 
                v-if="hasSpellIcon(selectedSpellDetail)"
                :src="getSpellIconUrl(selectedSpellDetail)"
                :alt="`${selectedSpellDetail.name} icon`"
                class="spell-icon-modal"
                @error="handleSpellIconError"
              />
              <div v-else class="spell-icon-placeholder-modal">
                <i class="fas fa-magic"></i>
              </div>
            </div>
            <div class="spell-header-info">
              <h3>{{ selectedSpellDetail.name }}</h3>
              <div class="spell-header-meta">
                <span class="spell-id-badge">ID: {{ selectedSpellDetail.spell_id }}</span>
                <span v-if="selectedSpellDetail.skill !== undefined" class="skill-badge">{{ getSkillName(selectedSpellDetail.skill) }}</span>
              </div>
            </div>
          </div>
          <button @click="closeSpellModal" class="modal-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <div class="spell-details">
            <!-- Primary Stats -->
            <div class="detail-section primary-stats">
              <h4>Casting Information</h4>
              <div class="primary-stats-grid">
                <div v-if="selectedSpellDetail.mana" class="primary-stat-item">
                  <div class="stat-icon"><i class="fas fa-star"></i></div>
                  <div class="stat-info">
                    <span class="stat-value">{{ selectedSpellDetail.mana }}</span>
                    <span class="stat-label">Mana Cost</span>
                  </div>
                </div>
                <div v-if="selectedSpellDetail.cast_time !== undefined" class="primary-stat-item">
                  <div class="stat-icon"><i class="fas fa-clock"></i></div>
                  <div class="stat-info">
                    <span class="stat-value">{{ formatCastTime(selectedSpellDetail.cast_time) }}</span>
                    <span class="stat-label">Cast Time</span>
                  </div>
                </div>
                <div v-if="selectedSpellDetail.range" class="primary-stat-item">
                  <div class="stat-icon"><i class="fas fa-crosshairs"></i></div>
                  <div class="stat-info">
                    <span class="stat-value">{{ selectedSpellDetail.range }}</span>
                    <span class="stat-label">Range</span>
                  </div>
                </div>
                <div v-if="selectedSpellDetail.buffduration !== undefined" class="primary-stat-item">
                  <div class="stat-icon"><i class="fas fa-hourglass-half"></i></div>
                  <div class="stat-info">
                    <span class="stat-value">{{ formatDuration(selectedSpellDetail.buffduration) }}</span>
                    <span class="stat-label">Duration</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Class Levels -->
            <div class="detail-section">
              <h4>Class Requirements</h4>
              <div class="class-requirements-grid">
                <template v-for="(level, className) in selectedSpellDetail.class_levels" :key="className">
                  <div 
                    v-if="level && level !== 255"
                    class="class-requirement-item"
                    :title="`${getClassAbbreviation(className)}: Level ${level}`"
                  >
                    <img 
                      :src="`/icons/${className}.gif`" 
                      :alt="`${className} icon`"
                      class="class-icon-detail"
                      @error="handleIconError"
                    />
                    <div class="class-req-text">
                      {{ getClassAbbreviation(className) }} ({{ level }})
                    </div>
                  </div>
                </template>
              </div>
            </div>

            <!-- Spell Effects (if available) -->
            <div v-if="hasSpellEffects(selectedSpellDetail)" class="detail-section">
              <h4>Effects</h4>
              <div class="effects-list">
                <div v-for="(effect, index) in selectedSpellDetail.effects" :key="index" 
                     v-if="effect && effect !== 0" class="effect-item">
                  <span class="effect-label">Effect {{ index + 1 }}:</span>
                  <span class="effect-value">{{ effect }}</span>
                </div>
              </div>
            </div>

            <!-- Components (if available) -->
            <div v-if="hasSpellComponents(selectedSpellDetail)" class="detail-section">
              <h4>Components</h4>
              <div class="components-list">
                <div v-for="(component, index) in selectedSpellDetail.components" :key="index" 
                     v-if="component && component !== 0" class="component-item">
                  <span class="component-label">Component {{ index + 1 }}:</span>
                  <span class="component-value">{{ component }}</span>
                </div>
              </div>
            </div>

            <!-- Additional Information -->
            <div class="detail-section">
              <h4>Additional Information</h4>
              <div class="additional-info-grid">
                <div v-if="selectedSpellDetail.targettype !== undefined" class="info-item">
                  <span class="info-label">Target Type:</span>
                  <span class="info-value">{{ getTargetType(selectedSpellDetail.targettype) }}</span>
                </div>
                <div v-if="selectedSpellDetail.resisttype !== undefined" class="info-item">
                  <span class="info-label">Resist Type:</span>
                  <span class="info-value">{{ getResistType(selectedSpellDetail.resisttype) }}</span>
                </div>
                <div v-if="selectedSpellDetail.spell_category !== undefined" class="info-item">
                  <span class="info-label">Category:</span>
                  <span class="info-value">{{ selectedSpellDetail.spell_category }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Toast Notifications -->
    <div class="toast-container">
      <transition-group name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast"
          :class="toast.type"
        >
          <i class="fas" :class="getToastIcon(toast.type)"></i>
          <div class="toast-content">
            <div class="toast-title">{{ toast.title }}</div>
            <div v-if="toast.message" class="toast-message">{{ toast.message }}</div>
          </div>
          <button @click="removeToast(toast.id)" class="toast-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
      </transition-group>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { API_BASE_URL } from '../config/api'
import LoadingModal from '../components/LoadingModal.vue'
import { toastService } from '../services/toastService'

export default {
  name: 'Spells',
  components: {
    LoadingModal
  },
  data() {
    return {
      searchQuery: '',
      searchResults: [],
      totalCount: 0,
      searching: false,
      searchPerformed: false,
      viewMode: 'list',
      
      // Pagination
      currentPage: 1,
      limit: 20,
      paginating: false, // Loading state for pagination
      searchStartTime: null, // Track when search started
      
      // Basic filters
      selectedClass: '',
      minLevel: '',
      maxLevel: '60',
      selectedSkill: '',
      
      // Spell details modal
      selectedSpellDetail: null,
      
      // Class cards scrolling state
      classScrollPositions: {},
      
      // Spell Matrix state
      matrixMode: 'classes', // 'classes' or 'levels'
      selectedMatrixClass: null,
      matrixLevels: [],
      selectedLevel: null,
      selectedLevelRange: null,
      isMatrixSearch: false, // Flag to track if search came from matrix selector
      
      // Drag selection state
      isDragging: false,
      dragStartLevel: null,
      dragCurrentLevel: null,
      
      // Toast notifications
      toasts: [],
      
      // API configuration will be imported
    }
  },
  
  computed: {
    totalPages() {
      return Math.ceil(this.totalCount / this.limit)
    },
    
    availableClasses() {
      return [
        'warrior', 'cleric', 'paladin', 'ranger', 'shadowknight', 
        'druid', 'monk', 'bard', 'rogue', 'shaman', 
        'necromancer', 'wizard', 'magician', 'enchanter', 
        'beastlord', 'berserker'
      ]
    },
    
    // Group spells by level for matrix search display
    spellsByLevel() {
      if (!this.isMatrixSearch || !this.selectedMatrixClass || !this.searchResults.length) {
        return []
      }
      
      const groups = new Map()
      
      this.searchResults.forEach(spell => {
        // Find the level for the selected matrix class
        const classLevel = this.getSpellLevelForClass(spell, this.selectedMatrixClass)
        if (classLevel !== null) {
          if (!groups.has(classLevel)) {
            groups.set(classLevel, [])
          }
          groups.get(classLevel).push(spell)
        }
      })
      
      // Convert to sorted array of level groups
      return Array.from(groups.entries())
        .sort(([a], [b]) => a - b)
        .map(([level, spells]) => ({ level, spells }))
    }
  },
  
  methods: {
    async performSearch(page = 1) {
      if (!this.searchQuery.trim() && !this.hasActiveFilters()) {
        this.showToast('Search Required', 'Please enter a search term or apply filters', 'warning')
        return
      }
      
      // Clear matrix search flag only if this is NOT a matrix search
      // (isMatrixSearch will already be set to true by searchByClassLevel before calling performSearch)
      if (page === 1 && !this.isMatrixSearch) {
        // Only reset flag for regular searches, not matrix searches
        this.isMatrixSearch = false
      }
      
      this.searching = true
      this.searchPerformed = true
      this.currentPage = page
      this.searchStartTime = Date.now() // Record when search started
      
      try {
        // Build query parameters
        const params = new URLSearchParams()
        
        if (this.searchQuery.trim()) {
          params.append('q', this.searchQuery.trim())
        }
        
        params.append('limit', this.limit.toString())
        params.append('offset', ((page - 1) * this.limit).toString())
        
        // Add basic filters
        const filters = this.buildFilters()
        if (filters.length > 0) {
          params.append('filters', JSON.stringify(filters))
        }
        
        console.log('Searching with params:', params.toString())
        
        const response = await axios.get(`${API_BASE_URL}/api/spells/search?${params.toString()}`)
        
        // Check if API returned HTML instead of JSON (proxy routing issue)
        if (typeof response.data === 'string' && response.data.includes('<!DOCTYPE html>')) {
          throw new Error('API returned HTML instead of JSON - possible proxy routing issue')
        }
        
        // Backend handles all filtering now - no frontend filtering needed
        this.searchResults = response.data.spells || []
        this.totalCount = response.data.total_count || 0
        
        console.log(`Found ${this.searchResults.length} spells total`)
        
        // Ensure loading modal shows for minimum 1 second
        const elapsedTime = Date.now() - this.searchStartTime
        const minDisplayTime = 1000 // 1 second
        const remainingTime = Math.max(0, minDisplayTime - elapsedTime)
        
        if (remainingTime > 0) {
          await new Promise(resolve => setTimeout(resolve, remainingTime))
        }
        
      } catch (error) {
        console.error('Search error:', error)
        this.showToast('Search Failed', error.response?.data?.error || error.message, 'error')
        this.searchResults = []
        this.totalCount = 0
        
        // Ensure loading modal shows for minimum 1 second even on error
        const elapsedTime = Date.now() - this.searchStartTime
        const minDisplayTime = 1000
        const remainingTime = Math.max(0, minDisplayTime - elapsedTime)
        
        if (remainingTime > 0) {
          await new Promise(resolve => setTimeout(resolve, remainingTime))
        }
      } finally {
        this.searching = false
        this.paginating = false
      }
    },
    
    buildFilters() {
      const filters = []
      
      // Class filter
      if (this.selectedClass) {
        filters.push({
          field: `${this.selectedClass}_level`,
          operator: 'class_can_use',
          value: true
        })
      }
      
      // Level filters - backend now supports all level filtering
      if (this.selectedClass && this.minLevel && this.maxLevel && this.minLevel === this.maxLevel) {
        // Exact level search
        filters.push({
          field: `${this.selectedClass}_level`,
          operator: 'equals',
          value: parseInt(this.minLevel)
        })
      } else if (this.selectedClass && this.minLevel && this.maxLevel) {
        // Level range search
        filters.push({
          field: `${this.selectedClass}_level`,
          operator: 'between',
          value: [parseInt(this.minLevel), parseInt(this.maxLevel)]
        })
      } else if (this.selectedClass && this.minLevel) {
        // Minimum level only
        filters.push({
          field: `${this.selectedClass}_level`,
          operator: 'greater than or equal',
          value: parseInt(this.minLevel)
        })
      } else if (this.selectedClass && this.maxLevel) {
        // Maximum level only
        filters.push({
          field: `${this.selectedClass}_level`,
          operator: 'less than or equal',
          value: parseInt(this.maxLevel)
        })
      }
      
      // Skill filter
      if (this.selectedSkill) {
        filters.push({
          field: 'skill',
          operator: 'equals',
          value: parseInt(this.selectedSkill)
        })
      }
      
      return filters
    },
    
    hasActiveFilters() {
      return this.selectedClass || this.minLevel || this.maxLevel || this.selectedSkill
    },
    
    clearFilters() {
      this.selectedClass = ''
      this.minLevel = ''
      this.maxLevel = ''
      this.selectedSkill = ''
      this.currentPage = 1
      this.isMatrixSearch = false
      
      // Reset spell matrix to class selection
      this.resetMatrix()
      
      // Perform search again if we had results
      if (this.searchQuery.trim()) {
        this.performSearch()
      }
    },
    
    changePage(page) {
      if (page >= 1 && page <= this.totalPages) {
        // Clear current results to show loading state
        this.searchResults = []
        
        // Set paginating state
        this.paginating = true
        this.searchStartTime = Date.now() // Track pagination start time too
        
        // Perform the search
        this.performSearch(page)
      }
    },
    
    formatCastTime(castTime) {
      if (!castTime || castTime === 0) return 'Instant'
      return `${(castTime / 1000).toFixed(1)}s`
    },
    
    formatDuration(duration) {
      if (!duration || duration === 0) return 'Instant'
      if (duration === 65535) return 'Permanent'
      
      const minutes = Math.floor(duration / 60)
      const seconds = duration % 60
      
      if (minutes > 0) {
        return seconds > 0 ? `${minutes}m ${seconds}s` : `${minutes}m`
      } else {
        return `${seconds}s`
      }
    },
    
    getClassAbbreviation(className) {
      const abbreviations = {
        'warrior': 'WAR',
        'cleric': 'CLR',
        'paladin': 'PAL',
        'ranger': 'RNG',
        'shadowknight': 'SHD',
        'druid': 'DRU',
        'monk': 'MNK',
        'bard': 'BRD',
        'rogue': 'ROG',
        'shaman': 'SHM',
        'necromancer': 'NEC',
        'wizard': 'WIZ',
        'magician': 'MAG',
        'enchanter': 'ENC',
        'beastlord': 'BST',
        'berserker': 'BER'
      }
      return abbreviations[className.toLowerCase()] || className.substring(0, 3).toUpperCase()
    },
    
    handleIconError(event) {
      // Hide the image if it fails to load
      event.target.style.display = 'none'
    },

    // Spell details modal methods
    async openSpellModal(spell) {
      try {
        // First, show the modal with basic spell data
        this.selectedSpellDetail = { ...spell }
        
        // Then fetch detailed spell information
        const response = await axios.get(`${API_BASE_URL}/api/spells/${spell.spell_id}/details`)
        
        // Check if API returned HTML instead of JSON
        if (typeof response.data === 'string' && response.data.includes('<!DOCTYPE html>')) {
          throw new Error('API returned HTML instead of JSON - possible proxy routing issue')
        }
        
        // Update with detailed information
        this.selectedSpellDetail = { ...this.selectedSpellDetail, ...response.data }
        
      } catch (error) {
        console.error('Error fetching spell details:', error)
        // Keep the modal open with basic data even if detailed fetch fails
        if (!this.selectedSpellDetail) {
          this.selectedSpellDetail = { ...spell }
        }
      }
    },

    closeSpellModal() {
      this.selectedSpellDetail = null
    },

    getSpellIconUrl(spell) {
      // Prefer new_icon over icon, fallback to icon if new_icon is 0 or missing
      const iconId = (spell.new_icon && spell.new_icon !== 0) ? spell.new_icon : spell.icon
      if (iconId && iconId !== 0) {
        // Use the numbered icon files from /icons/items/
        return `/icons/items/${iconId}.gif`
      }
      // Fallback for spells without icons (icon 0 = blank scroll)
      return '/icons/items/0.gif'
    },

    // Helper method to check if spell has a valid icon
    hasSpellIcon(spell) {
      const iconId = (spell.new_icon && spell.new_icon !== 0) ? spell.new_icon : spell.icon
      return iconId && iconId !== 0
    },

    handleSpellIconError(event) {
      const currentSrc = event.target.src
      // If currently trying .gif, try .png
      if (currentSrc.includes('.gif')) {
        event.target.src = currentSrc.replace('.gif', '.png')
      } else {
        // Final fallback to icon 0
        event.target.src = '/icons/items/0.gif'
      }
    },

    getSkillName(skillId) {
      const skills = {
        0: '1H Blunt',
        1: '1H Slashing',
        2: '2H Blunt',
        3: '2H Slashing',
        4: 'Abjuration',
        5: 'Alteration',
        6: 'Apply Poison',
        7: 'Archery',
        8: 'Backstab',
        9: 'Bind Wound',
        10: 'Bash',
        11: 'Block',
        12: 'Brass Instruments',
        13: 'Channeling',
        14: 'Conjuration',
        15: 'Defense',
        16: 'Disarm',
        17: 'Disarm Traps',
        18: 'Divination',
        19: 'Dodge',
        20: 'Double Attack',
        21: 'Dragon Punch',
        22: 'Dual Wield',
        23: 'Eagle Strike',
        24: 'Evocation',
        25: 'Feign Death',
        26: 'Flying Kick',
        27: 'Forage',
        28: 'Hand to Hand',
        29: 'Hide',
        30: 'Kick',
        31: 'Meditate',
        32: 'Mend',
        33: 'Offense',
        34: 'Parry',
        35: 'Pick Lock',
        36: '1H Piercing',
        37: 'Riposte',
        38: 'Round Kick',
        39: 'Safe Fall',
        40: 'Sense Heading',
        41: 'Singing',
        42: 'Sneak',
        43: 'Specialize Abjure',
        44: 'Specialize Alteration',
        45: 'Specialize Conjuration',
        46: 'Specialize Divination',
        47: 'Specialize Evocation',
        48: 'Pick Pockets',
        49: 'Stringed Instruments',
        50: 'Swimming',
        51: 'Throwing',
        52: 'Tiger Claw',
        53: 'Tracking',
        54: 'Wind Instruments',
        55: 'Fishing',
        56: 'Make Poison',
        57: 'Tinkering',
        58: 'Research',
        59: 'Alchemy',
        60: 'Baking',
        61: 'Tailoring',
        62: 'Sense Traps',
        63: 'Blacksmithing',
        64: 'Fletching',
        65: 'Brewing',
        66: 'Alcohol Tolerance',
        67: 'Begging',
        68: 'Jewelry Making',
        69: 'Pottery',
        70: 'Percussion Instruments',
        71: 'Intimidation',
        72: 'Berserking',
        73: 'Taunt',
        74: 'Frenzy',
        75: 'Remove Trap'
      }
      return skills[skillId] || `Skill ${skillId}`
    },

    getClassFullName(className) {
      const fullNames = {
        'warrior': 'Warrior',
        'cleric': 'Cleric',
        'paladin': 'Paladin',
        'ranger': 'Ranger',
        'shadowknight': 'Shadow Knight',
        'druid': 'Druid',
        'monk': 'Monk',
        'bard': 'Bard',
        'rogue': 'Rogue',
        'shaman': 'Shaman',
        'necromancer': 'Necromancer',
        'wizard': 'Wizard',
        'magician': 'Magician',
        'enchanter': 'Enchanter',
        'beastlord': 'Beastlord',
        'berserker': 'Berserker'
      }
      return fullNames[className.toLowerCase()] || className
    },
    
    getSpellLevelForClass(spell, className) {
      // Find the level for a specific class in the spell's class levels
      const classKey = `${className}_level`
      
      // Also check the class_levels object if it exists
      if (spell.class_levels && spell.class_levels[className]) {
        const level = spell.class_levels[className]
        if (level > 0 && level <= 255) {
          return level
        }
      }
      
      // Fallback to the direct property approach
      if (spell[classKey] && spell[classKey] > 0 && spell[classKey] <= 255) {
        return spell[classKey]
      }
      
      return null
    },

    getTargetType(targetType) {
      const types = {
        0: "Rag'Zhezum Special",
        1: 'Line of Sight',
        3: 'Group V1',
        4: 'Point Blank Area of Effect',
        5: 'Single',
        6: 'Self',
        8: 'Targeted Area of Effect',
        9: 'Animal',
        10: 'Undead',
        11: 'Summoned',
        13: 'Life Tap',
        14: 'Pet',
        15: 'Corpse',
        16: 'Plant',
        17: 'Uber Giants',
        18: 'Uber Dragons',
        20: 'Targeted Area of Effect Life Tap',
        24: 'Area of Effect Undead',
        25: 'Area of Effect Summoned',
        32: 'Area of Effect Caster',
        33: 'NPC Hate List',
        34: 'Dungeon Object',
        35: 'Muramite',
        36: 'Area - PC Only',
        37: 'Area - NPC Only',
        38: 'Summoned Pet',
        39: 'Group No Pets',
        40: 'Area of Effect PC V2',
        41: 'Group V2',
        42: 'Self (Directional)',
        43: 'Group With Pets',
        44: 'Beam'
      }
      return types[targetType] || `Type ${targetType}`
    },

    getResistType(resistType) {
      const types = {
        0: 'None',
        1: 'Magic',
        2: 'Fire',
        3: 'Cold',
        4: 'Poison',
        5: 'Disease',
        6: 'Chromatic',
        7: 'Prismatic',
        8: 'Physical',
        9: 'Corruption'
      }
      return types[resistType] || `Resist ${resistType}`
    },

    hasSpellEffects(spell) {
      return spell.effects && spell.effects.some(effect => effect && effect !== 0)
    },

    hasSpellComponents(spell) {
      return spell.components && spell.components.some(component => component && component !== 0)
    },

    // Class scrolling methods
    getValidClasses(spell) {
      if (!spell || !spell.class_levels) return []
      const validClasses = []
      Object.entries(spell.class_levels).forEach(([className, level]) => {
        if (level && level !== 255) {
          validClasses.push({ className, level })
        }
      })
      return validClasses
    },

    getOrderedClassLevels(spell) {
      if (!spell || !spell.class_levels) return {}
      
      const classLevels = { ...spell.class_levels }
      const selectedClass = this.selectedClass || this.selectedMatrixClass
      
      if (!selectedClass) {
        // No selected class, return original order
        return classLevels
      }
      
      // Create ordered object with selected class first
      const orderedLevels = {}
      
      // Add selected class first if it exists and has a valid level
      if (classLevels[selectedClass] && classLevels[selectedClass] !== 255) {
        orderedLevels[selectedClass] = classLevels[selectedClass]
      }
      
      // Add all other classes in their original order
      Object.entries(classLevels).forEach(([className, level]) => {
        if (className !== selectedClass && level && level !== 255) {
          orderedLevels[className] = level
        }
      })
      
      return orderedLevels
    },

    getClassCardWidthStyle(spell) {
      // Return consistent sizing for all class cards - no dynamic resizing
      // This maintains the proportions seen in "Minor Healing" spell
      return {
        minWidth: '110px',
        width: '110px',
        maxWidth: '110px',
        flex: '0 0 110px'
      }
    },

    scrollClassCards(spellId, direction) {
      console.log('scrollClassCards called:', spellId, direction)
      
      // For Vue 2, refs with dynamic names might be in an array
      let gridRef = this.$refs[`classGrid${spellId}`]
      if (Array.isArray(gridRef)) {
        gridRef = gridRef[0]
      }
      
      if (!gridRef) {
        console.log('Grid ref not found for spell', spellId)
        console.log('Available refs:', Object.keys(this.$refs))
        return
      }

      console.log('Grid ref found:', gridRef)
      console.log('Current scrollLeft:', gridRef.scrollLeft)
      console.log('ScrollWidth:', gridRef.scrollWidth)
      console.log('ClientWidth:', gridRef.clientWidth)

      const cardWidth = 126 // 110px min-width + 16px gap
      const scrollAmount = cardWidth * 3 // Scroll 3 cards at a time for snappier feel

      const oldScrollLeft = gridRef.scrollLeft
      if (direction === 'left') {
        gridRef.scrollLeft -= scrollAmount
      } else {
        gridRef.scrollLeft += scrollAmount
      }
      
      console.log('Scroll amount:', scrollAmount)
      console.log('Old scrollLeft:', oldScrollLeft)
      console.log('New scrollLeft:', gridRef.scrollLeft)

      // Update scroll state
      this.$nextTick(() => {
        this.updateScrollState(spellId)
      })
    },

    handleWheelScroll(event, spellId) {
      // Only handle wheel scrolling if there are more than 3 classes (arrows are visible)
      const spell = this.searchResults.find(s => s.spell_id === spellId)
      if (!spell || this.getValidClasses(spell).length <= 3) {
        // Let normal page scrolling happen
        return
      }
      
      // For Vue 2, refs with dynamic names might be in an array
      let gridRef = this.$refs[`classGrid${spellId}`]
      if (Array.isArray(gridRef)) {
        gridRef = gridRef[0]
      }
      
      if (!gridRef) return

      // Check if there's actually scrollable content
      const maxScroll = gridRef.scrollWidth - gridRef.clientWidth
      if (maxScroll <= 0) {
        // No scrollable content, let normal page scrolling happen
        return
      }

      // Prevent default to enable horizontal scrolling
      event.preventDefault()

      const scrollAmount = 150 // Faster scroll amount for wheel
      
      if (event.deltaY > 0) {
        // Scroll down = scroll right
        gridRef.scrollLeft += scrollAmount
      } else {
        // Scroll up = scroll left
        gridRef.scrollLeft -= scrollAmount
      }

      // Update scroll state
      this.$nextTick(() => {
        this.updateScrollState(spellId)
      })
    },

    canScrollLeft(spellId) {
      let gridRef = this.$refs[`classGrid${spellId}`]
      if (Array.isArray(gridRef)) {
        gridRef = gridRef[0]
      }
      if (!gridRef) return false
      return gridRef.scrollLeft > 5 // Small threshold for smoother UX
    },

    canScrollRight(spellId) {
      let gridRef = this.$refs[`classGrid${spellId}`]
      if (Array.isArray(gridRef)) {
        gridRef = gridRef[0]
      }
      if (!gridRef) return false
      const maxScroll = gridRef.scrollWidth - gridRef.clientWidth
      return gridRef.scrollLeft < (maxScroll - 5) // Small threshold
    },

    updateScrollState(spellId) {
      // Trigger reactivity by updating scroll positions
      if (!this.classScrollPositions[spellId]) {
        this.$set(this.classScrollPositions, spellId, {})
      }
      let gridRef = this.$refs[`classGrid${spellId}`]
      if (Array.isArray(gridRef)) {
        gridRef = gridRef[0]
      }
      if (gridRef) {
        this.$set(this.classScrollPositions[spellId], 'left', gridRef.scrollLeft)
      }
    },

    initializeClassScrolling() {
      this.$nextTick(() => {
        this.searchResults.forEach(spell => {
          this.updateScrollState(spell.spell_id)
        })
      })
    },

    // Spell Matrix Methods
    selectMatrixClass(className) {
      this.selectedMatrixClass = className
      this.matrixMode = 'levels'
      this.generateLevelMatrix()
    },

    resetMatrix() {
      this.matrixMode = 'classes'
      this.selectedMatrixClass = null
      this.matrixLevels = []
      this.selectedLevel = null
      this.selectedLevelRange = null
      this.isDragging = false
      this.dragStartLevel = null
      this.dragCurrentLevel = null
      this.isMatrixSearch = false
    },

    generateLevelMatrix() {
      // Generate levels 1-60 in a 10x6 grid
      const levels = []
      for (let i = 1; i <= 60; i++) {
        levels.push(i)
      }
      this.matrixLevels = levels
    },

    scrollToTopOfResults() {
      // Scroll to the top of the search results section
      const resultsSection = document.querySelector('.results-section')
      if (resultsSection) {
        resultsSection.scrollIntoView({ 
          behavior: 'smooth',
          block: 'start'
        })
      }
    },

    async searchByClassLevel(className, minLevel, maxLevel = null) {
      // Set up the search parameters to populate the form
      this.searchQuery = ''
      this.selectedClass = className
      this.minLevel = minLevel.toString()
      this.maxLevel = (maxLevel || minLevel).toString()
      this.selectedSkill = ''
      
      // Update matrix selection state
      if (maxLevel && maxLevel !== minLevel) {
        this.selectedLevelRange = [Math.min(minLevel, maxLevel), Math.max(minLevel, maxLevel)]
        this.selectedLevel = null
      } else {
        this.selectedLevel = minLevel
        this.selectedLevelRange = null
      }
      
      // Mark this as a matrix search
      this.isMatrixSearch = true
      
      // Use the regular search method
      await this.performSearch(1)
      
      // Scroll to results section after search completes
      this.$nextTick(() => {
        const resultsSection = document.querySelector('.results-section')
        if (resultsSection) {
          resultsSection.scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
          })
        }
      })
    },

    // Matrix level drag selection methods
    startLevelDrag(level) {
      this.isDragging = true
      this.dragStartLevel = level
      this.dragCurrentLevel = level
      
      // Prevent text selection during drag
      document.addEventListener('selectstart', this.preventSelect)
      document.addEventListener('mouseup', this.handleDocumentMouseUp)
    },

    handleLevelHover(level) {
      if (this.isDragging) {
        this.dragCurrentLevel = level
      }
    },

    endLevelDrag(level) {
      if (this.isDragging) {
        this.isDragging = false
        const startLevel = this.dragStartLevel
        const endLevel = level
        
        if (startLevel === endLevel) {
          // Single level selection
          this.searchByClassLevel(this.selectedMatrixClass, startLevel)
        } else {
          // Range selection
          const minLevel = Math.min(startLevel, endLevel)
          const maxLevel = Math.max(startLevel, endLevel)
          this.searchByClassLevel(this.selectedMatrixClass, minLevel, maxLevel)
        }
        
        this.cleanup()
      }
    },

    handleLevelClick(level) {
      if (!this.isDragging) {
        // Direct click without drag
        this.searchByClassLevel(this.selectedMatrixClass, level)
      }
    },

    handleDocumentMouseUp() {
      if (this.isDragging) {
        this.isDragging = false
        this.cleanup()
      }
    },

    cleanup() {
      this.dragStartLevel = null
      this.dragCurrentLevel = null
      document.removeEventListener('selectstart', this.preventSelect)
      document.removeEventListener('mouseup', this.handleDocumentMouseUp)
    },

    preventSelect(e) {
      e.preventDefault()
    },

    // Helper methods for highlighting
    isLevelInSelectedRange(level) {
      if (this.isDragging && this.dragStartLevel && this.dragCurrentLevel) {
        const min = Math.min(this.dragStartLevel, this.dragCurrentLevel)
        const max = Math.max(this.dragStartLevel, this.dragCurrentLevel)
        return level >= min && level <= max
      }
      
      if (this.selectedLevelRange) {
        return level >= this.selectedLevelRange[0] && level <= this.selectedLevelRange[1]
      }
      
      return false
    },

    getLevelTooltip(level) {
      if (this.isDragging && this.dragStartLevel && this.dragCurrentLevel) {
        const min = Math.min(this.dragStartLevel, this.dragCurrentLevel)
        const max = Math.max(this.dragStartLevel, this.dragCurrentLevel)
        if (min === max) {
          return `View ${this.getClassFullName(this.selectedMatrixClass)} spells at level ${level}`
        } else {
          return `View ${this.getClassFullName(this.selectedMatrixClass)} spells from level ${min} to ${max}`
        }
      }
      return `View ${this.getClassFullName(this.selectedMatrixClass)} spells at level ${level}`
    },

    // Toast notification methods
    showToast(title, message = '', type = 'info') {
      const id = Date.now() + Math.random()
      this.toasts.push({ id, title, message, type })
      
      // Auto-remove after 5 seconds
      setTimeout(() => {
        this.removeToast(id)
      }, 5000)
    },

    removeToast(id) {
      const index = this.toasts.findIndex(t => t.id === id)
      if (index > -1) {
        this.toasts.splice(index, 1)
      }
    },

    getToastIcon(type) {
      switch (type) {
        case 'success': return 'fa-check-circle'
        case 'error': return 'fa-exclamation-circle'
        case 'warning': return 'fa-exclamation-triangle'
        case 'info': return 'fa-info-circle'
        default: return 'fa-info-circle'
      }
    },

    // Timeout handlers for loading modals
    onSearchTimeout() {
      console.warn('Spell search request timed out')
      this.searching = false
      this.searchPerformed = true
      this.searchResults = []
      toastService.warning('Search request timed out. Please try again with different criteria.')
    },

    onPaginationTimeout() {
      console.warn('Spell pagination request timed out')
      this.paginating = false
      toastService.warning('Pagination request timed out. Please try again.')
    }
  },

  mounted() {
    this.initializeClassScrolling()
  },

  updated() {
    this.initializeClassScrolling()
  }
}
</script>

<style scoped>
.spells-page {
  padding: 20px;
  padding-top: 100px; /* Prevent logo overlap */
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h1 {
  font-size: 3rem;
  margin: 0 0 15px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 700;
}

.subtitle {
  color: rgba(255, 255, 255, 0.8);
  font-size: 1.2rem;
  margin: 0;
  font-weight: 400;
}

.search-section {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.85) 0%, rgba(45, 55, 72, 0.85) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 30px;
  margin-bottom: 30px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.search-input-group {
  display: flex;
  gap: 15px;
  margin-bottom: 25px;
}

.search-input {
  flex: 1;
  padding: 15px 20px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  font-size: 16px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3);
  background: rgba(255, 255, 255, 0.15);
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.search-button {
  padding: 15px 25px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.search-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
}

.search-button:disabled {
  background: rgba(255, 255, 255, 0.2);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.search-button-text {
  display: none;
}

@media (min-width: 768px) {
  .search-button-text {
    display: inline;
  }
}

.filters-container {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
  align-items: end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 140px;
}

.filter-group label {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.filter-select,
.filter-input {
  padding: 12px 15px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 14px;
  transition: all 0.3s ease;
}

.filter-select:focus,
.filter-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.3);
  background: rgba(255, 255, 255, 0.15);
}

.filter-select option {
  background: #2d3748;
  color: white;
}

.filter-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.clear-filters-button {
  padding: 12px 18px;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
}

.clear-filters-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
}

/* Spell Matrix Styles */
.spell-matrix-section {
  margin: 40px auto;
  max-width: 1200px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 20px;
  padding: 30px;
  backdrop-filter: blur(10px);
}

.matrix-header {
  text-align: center;
  margin-bottom: 30px;
  position: relative;
}

.matrix-header h3 {
  font-size: 1.8rem;
  margin: 0 0 8px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  font-weight: 700;
}

.matrix-subtitle {
  color: rgba(255, 255, 255, 0.7);
  font-size: 1rem;
  margin: 0;
}

.matrix-reset-button {
  position: absolute;
  top: 0;
  right: 0;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.9);
  padding: 8px 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 6px;
}

.matrix-reset-button:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%);
  border-color: rgba(102, 126, 234, 0.4);
  transform: translateY(-1px);
}

.matrix-classes-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 16px;
  max-width: 1000px;
  margin: 0 auto;
}

.matrix-class-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 12px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 120px;
  justify-content: center;
}

.matrix-class-item:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.25) 0%, rgba(118, 75, 162, 0.25) 100%);
  border-color: rgba(102, 126, 234, 0.5);
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
}

.matrix-class-icon {
  width: 48px;
  height: 48px;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
  margin-bottom: 8px;
}

.matrix-class-name {
  font-size: 1rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.matrix-levels-grid {
  max-width: 1000px;
  margin: 0 auto;
}

.matrix-selected-class {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 30px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  border: 1px solid rgba(102, 126, 234, 0.4);
  border-radius: 12px;
}

.matrix-selected-class-icon {
  width: 40px;
  height: 40px;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}

.matrix-selected-class-name {
  font-size: 1.4rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.matrix-levels-container {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 8px;
}

.matrix-level-item {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
  min-height: 50px;
}

.matrix-level-item:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%);
  border-color: rgba(102, 126, 234, 0.5);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  color: white;
}

.matrix-level-item.selected {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.4) 0%, rgba(16, 185, 129, 0.4) 100%);
  border-color: rgba(34, 197, 94, 0.6);
  color: white;
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.3), 0 4px 12px rgba(34, 197, 94, 0.4);
  transform: translateY(-2px);
}

.matrix-level-item.in-range {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.3) 0%, rgba(37, 99, 235, 0.3) 100%);
  border-color: rgba(59, 130, 246, 0.5);
  color: white;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.3);
}

.matrix-level-item.drag-start {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.4) 0%, rgba(245, 158, 11, 0.4) 100%);
  border-color: rgba(251, 191, 36, 0.6);
  color: white;
  box-shadow: 0 0 0 2px rgba(251, 191, 36, 0.4);
  transform: translateY(-2px);
}

.matrix-level-item.drag-current {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.4) 0%, rgba(147, 51, 234, 0.4) 100%);
  border-color: rgba(168, 85, 247, 0.6);
  color: white;
  box-shadow: 0 0 0 2px rgba(168, 85, 247, 0.4);
  transform: translateY(-2px);
}

.matrix-level-item.selected:hover,
.matrix-level-item.in-range:hover,
.matrix-level-item.drag-start:hover,
.matrix-level-item.drag-current:hover {
  transform: translateY(-3px);
}

/* Prevent text selection during drag */
.matrix-levels-container {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

@media (max-width: 768px) {
  .matrix-levels-container {
    grid-template-columns: repeat(5, 1fr);
    gap: 6px;
  }
  
  .matrix-level-item {
    font-size: 0.8rem;
    min-height: 45px;
  }
  
  .matrix-classes-grid {
    grid-template-columns: repeat(4, 1fr);
    grid-template-rows: repeat(4, 1fr);
    gap: 12px;
  }
  
  .matrix-reset-button {
    position: static;
    margin-top: 15px;
    align-self: center;
  }
}

/* Toast Notification Styles */
.toast-container {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 1000;
  max-width: 400px;
  width: 100%;
  pointer-events: none;
}

.toast {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.95) 0%, rgba(45, 55, 72, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 16px;
  margin-bottom: 12px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  pointer-events: auto;
  animation: slideIn 0.3s ease-out;
}

.toast.success {
  border-color: rgba(34, 197, 94, 0.3);
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(16, 185, 129, 0.15) 100%);
}

.toast.error {
  border-color: rgba(239, 68, 68, 0.3);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.15) 100%);
}

.toast.warning {
  border-color: rgba(251, 191, 36, 0.3);
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.15) 0%, rgba(245, 158, 11, 0.15) 100%);
}

.toast.info {
  border-color: rgba(59, 130, 246, 0.3);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(37, 99, 235, 0.15) 100%);
}

.toast i {
  font-size: 1.3rem;
  margin-top: 2px;
}

.toast.success i {
  color: #34d399;
}

.toast.error i {
  color: #f87171;
}

.toast.warning i {
  color: #fbbf24;
}

.toast.info i {
  color: #60a5fa;
}

.toast-content {
  flex: 1;
}

.toast-title {
  font-weight: 600;
  color: #f7fafc;
  margin-bottom: 2px;
}

.toast-message {
  font-size: 0.9rem;
  color: #9ca3af;
  line-height: 1.4;
}

.toast-close {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  font-size: 0.9rem;
  transition: color 0.2s;
}

.toast-close:hover {
  color: #f7fafc;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast-enter-active {
  animation: slideIn 0.3s ease-out;
}

.toast-leave-active {
  animation: slideOut 0.3s ease-in;
}

@keyframes slideOut {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}

.decorative-image-container {
  margin: 40px auto;
  max-width: 800px;
  display: flex;
  justify-content: center;
  align-items: center;
  animation: fadeIn 0.5s ease-in-out;
}

.image-wrapper {
  position: relative;
  width: 100%;
  overflow: hidden;
  border-radius: 20px;
}

.decorative-image {
  width: 100%;
  height: auto;
  max-height: 500px;
  object-fit: cover;
  display: block;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.image-overlay {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
  z-index: 10;
  padding: 30px 50px;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(8px);
  border-radius: 15px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.overlay-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  margin: 0 0 10px 0;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.overlay-subtitle {
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  font-weight: 400;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.results-section {
  margin-top: 30px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 30px 30px 0;
  margin-bottom: 30px;
}

.results-title-section h2 {
  font-size: 2rem;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 8px 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
}

.results-info {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.95);
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
}

.results-info span:not(:last-child) {
  margin-right: 8px;
}

.view-toggle-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.view-toggle-label {
  color: #9ca3af;
  font-weight: 500;
  font-size: 0.95rem;
}

.view-toggle {
  display: flex;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
  padding: 4px;
  gap: 4px;
}

.view-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: transparent;
  color: #9ca3af;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.95rem;
  font-weight: 500;
}

.view-button i {
  font-size: 0.9rem;
}

.view-button.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.view-button:hover {
  color: #f7fafc;
  background: rgba(255, 255, 255, 0.1);
}

.view-button-text {
  font-weight: 500;
}

@media (max-width: 768px) {
  .view-toggle-container {
    align-self: stretch;
    justify-content: center;
  }

  .view-button-text {
    display: inline;  /* Text remains visible on mobile */
  }
}

.spell-results.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
  gap: 20px;
}

.spell-results.list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.spell-results.list .spell-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 15px 20px;
}

.spell-results.list .spell-main-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 20px;
}

.spell-results.list .spell-header {
  flex-shrink: 0;
  margin-bottom: 0;
  min-width: 200px;
  align-items: center;
  justify-content: flex-start;
}

.spell-results.list .spell-details {
  flex: 1;
  display: flex;
  gap: 20px;
  margin-bottom: 0;
}

.spell-results.list .spell-detail-row {
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 8px 12px;
  min-width: 80px;
}

.spell-results.list .spell-class-levels {
  flex-shrink: 0;
  border-top: none;
  padding-top: 0;
}

.spell-card {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.95) 0%, rgba(45, 55, 72, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: all 0.3s ease;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4),
              0 0 0 1px rgba(255, 255, 255, 0.08) inset;
  position: relative;
  overflow: hidden;
}

.spell-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #667eea 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.spell-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5),
              0 0 0 1px rgba(102, 126, 234, 0.2) inset;
  border-color: rgba(102, 126, 234, 0.4);
}

.spell-card:hover::before {
  opacity: 1;
}

.spell-main-content {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 20px;
}

.spell-header {
  display: flex;
  align-items: center;
  margin-bottom: 0;
  position: relative;
  gap: 16px;
  justify-content: flex-start;
  flex-shrink: 0;
  min-width: 300px;
}

.spell-icon-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}

.spell-icon {
  width: 40px;
  height: 40px;
  object-fit: contain;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}

.spell-icon-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 22px;
}

.spell-header-text {
  flex: 1;
  display: flex;
  align-items: center;
}

.spell-name {
  font-size: 1.5em;
  color: #ffffff;
  margin: 0;
  font-weight: 700;
  line-height: 1.2;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.6);
  background: linear-gradient(135deg, #ffffff 0%, rgba(255, 255, 255, 0.9) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-align: left;
}

.spell-meta {
  text-align: right;
  font-size: 0.85em;
  color: #ffffff;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  border: 1px solid rgba(102, 126, 234, 0.3);
  padding: 6px 12px;
  border-radius: 8px;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(10px);
}

.spell-details {
  display: flex;
  gap: 20px;
  margin-bottom: 0;
  flex: 1;
}

.spell-detail-row {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 8px 12px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.04) 100%);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
  min-width: 80px;
}

.spell-detail-row::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
  opacity: 0;
  transition: opacity 0.2s ease;
}

.spell-detail-row:hover::before {
  opacity: 1;
}

.spell-detail-row:hover {
  border-color: rgba(102, 126, 234, 0.3);
  transform: translateY(-1px);
}

.detail-label {
  font-weight: 700;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.85em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  position: relative;
  z-index: 1;
}

.detail-value {
  color: #ffffff;
  font-weight: 700;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.6);
  font-size: 1em;
  position: relative;
  z-index: 1;
}

.spell-class-levels {
  border-left: 1px solid rgba(102, 126, 234, 0.2);
  padding-left: 20px;
  position: relative;
  flex: 1;
  min-width: 400px;
  max-width: 600px;
  overflow: hidden;
}

.class-levels-container {
  position: relative;
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
}

.spell-class-levels::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  transform: translateY(-50%);
  width: 1px;
  height: 60px;
  background: linear-gradient(180deg, transparent 0%, #667eea 50%, transparent 100%);
}

.class-levels-grid {
  display: flex;
  flex-wrap: nowrap;
  gap: 16px;
  align-items: center;
  overflow-x: auto;
  overflow-y: hidden;
  scroll-behavior: auto;
  scrollbar-width: none;
  -ms-overflow-style: none;
  flex: 1;
  padding: 4px 0;
  min-width: 320px;
}

.class-levels-grid::-webkit-scrollbar {
  display: none;
}

.class-scroll-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.4) 0%, rgba(118, 75, 162, 0.4) 100%);
  border: 1px solid rgba(102, 126, 234, 0.5);
  border-radius: 50%;
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 10;
  flex-shrink: 0;
}

.class-scroll-arrow:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.5) 0%, rgba(118, 75, 162, 0.5) 100%);
  border-color: rgba(102, 126, 234, 0.6);
  color: rgba(255, 255, 255, 1);
  transform: scale(1.05);
}

.class-scroll-arrow:active {
  transform: scale(0.95);
}

.class-scroll-arrow i {
  font-size: 12px;
}

.class-scroll-left {
  margin-right: 4px;
}

.class-scroll-right {
  margin-left: 4px;
}

.class-level {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 16px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
  border: 1px solid rgba(102, 126, 234, 0.3);
  font-size: 1em;
  transition: all 0.3s ease;
  min-height: 120px;
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(10px);
  justify-content: center;
  /* Dynamic sizing will be controlled via inline styles */
}

.class-level.available {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.25) 0%, rgba(118, 75, 162, 0.25) 100%);
  border-color: rgba(102, 126, 234, 0.4);
  color: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

.class-level.available::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.class-level:hover.available {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.35) 0%, rgba(118, 75, 162, 0.35) 100%);
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  border-color: rgba(102, 126, 234, 0.6);
}

.class-level:hover.available::before {
  opacity: 1;
}

/* Selected class highlighting */
.class-level.selected-class {
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.25) 0%, rgba(255, 165, 0, 0.25) 100%) !important;
  border: 2px solid rgba(255, 215, 0, 0.6) !important;
  box-shadow: 0 4px 16px rgba(255, 215, 0, 0.4), 
              0 0 0 1px rgba(255, 215, 0, 0.2) inset !important;
  transform: scale(1.05);
  z-index: 10;
  position: relative;
}

.class-level.selected-class::before {
  content: '';
  position: absolute;
  top: -2px;
  left: -2px;
  right: -2px;
  bottom: -2px;
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.3) 0%, rgba(255, 165, 0, 0.3) 100%);
  border-radius: 18px;
  z-index: -1;
  animation: selectedClassGlow 2s ease-in-out infinite alternate;
}

.class-level.selected-class .class-abbrev,
.class-level.selected-class .class-level-value {
  color: #fff !important;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
  font-weight: 700;
}

.class-level.selected-class:hover {
  transform: scale(1.08) translateY(-2px) !important;
  box-shadow: 0 8px 24px rgba(255, 215, 0, 0.5), 
              0 0 0 1px rgba(255, 215, 0, 0.3) inset !important;
}

@keyframes selectedClassGlow {
  0% {
    opacity: 0.6;
    box-shadow: 0 0 20px rgba(255, 215, 0, 0.4);
  }
  100% {
    opacity: 0.8;
    box-shadow: 0 0 30px rgba(255, 215, 0, 0.6);
  }
}

.class-icon {
  width: 48px;
  height: 48px;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
  margin-bottom: 10px;
  animation: classIconPulse 2.5s infinite ease-in-out;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.7));
  position: relative;
  z-index: 2;
}

@keyframes classIconPulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.5));
  }
  50% {
    opacity: 0.9;
    transform: scale(1.08);
    filter: drop-shadow(0 3px 6px rgba(102, 126, 234, 0.3));
  }
}

.class-abbrev {
  font-size: 1.3em;
  color: #ffffff;
  font-weight: 800;
  text-align: center;
  margin-bottom: 6px;
  letter-spacing: 0.8px;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
  position: relative;
  z-index: 2;
}

.class-level-value {
  font-weight: 800;
  color: #ffffff;
  font-size: 1.1em;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8);
  position: relative;
  z-index: 2;
  opacity: 0.95;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 30px;
  margin-bottom: 40px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.9) 0%, rgba(45, 55, 72, 0.9) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.pagination-top {
  margin: 20px 30px;
}

.page-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.page-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.page-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.page-info {
  color: #f7fafc;
  font-weight: 600;
  font-size: 1rem;
  background: rgba(0, 0, 0, 0.3);
  padding: 10px 20px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  min-width: 150px;
  text-align: center;
}

/* Level Separator Styles for Matrix Search */
.matrix-spell-results {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.level-group {
  margin-bottom: 20px;
}

.level-separator {
  display: flex;
  align-items: center;
  margin: 30px 0 20px 0;
  gap: 20px;
}

.level-separator-line {
  flex: 1;
  height: 2px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(102, 126, 234, 0.6) 25%, 
    rgba(102, 126, 234, 0.8) 50%, 
    rgba(102, 126, 234, 0.6) 75%, 
    transparent 100%);
  position: relative;
}

.level-separator-line::after {
  content: '';
  position: absolute;
  top: -1px;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(255, 255, 255, 0.3) 25%, 
    rgba(255, 255, 255, 0.5) 50%, 
    rgba(255, 255, 255, 0.3) 75%, 
    transparent 100%);
}

.level-separator-content {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.95) 0%, rgba(45, 55, 72, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 12px 24px;
  border: 1px solid rgba(102, 126, 234, 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4),
              0 0 0 1px rgba(255, 255, 255, 0.08) inset;
  position: relative;
  min-width: 200px;
  gap: 16px;
}

.level-separator-content::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #667eea 100%);
  border-radius: 16px 16px 0 0;
}

.level-separator-info {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.level-separator-text {
  font-size: 1.1rem;
  font-weight: 700;
  color: #f7fafc;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
  line-height: 1.2;
}

.level-separator-count {
  font-size: 0.85rem;
  color: #a0aec0;
  font-weight: 500;
  margin-top: 2px;
}

.level-separator-to-top {
  display: flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  border: 1px solid rgba(102, 126, 234, 0.4);
  border-radius: 12px;
  padding: 8px 12px;
  color: #f7fafc;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  flex-shrink: 0;
}

.level-separator-to-top:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.35) 0%, rgba(118, 75, 162, 0.35) 100%);
  border-color: rgba(102, 126, 234, 0.6);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.level-separator-to-top:active {
  transform: translateY(0);
}

.level-separator-to-top i {
  font-size: 0.9rem;
}

.to-top-text {
  white-space: nowrap;
}


/* Responsive design */
@media (max-width: 1024px) {
  .spell-results.list .spell-details {
    grid-template-columns: 1fr 1fr;
  }
  
  .spell-class-levels {
    min-width: 350px;
    max-width: 500px;
  }
  
  /* Responsive level separators */
  .level-separator {
    margin: 20px 0 15px 0;
    gap: 15px;
  }
  
  .level-separator-content {
    padding: 10px 20px;
    min-width: 180px;
    flex-direction: column;
    gap: 12px;
  }
  
  .level-separator-text {
    font-size: 1rem;
  }
  
  .level-separator-count {
    font-size: 0.8rem;
  }
  
  .level-separator-to-top {
    padding: 6px 10px;
    font-size: 0.8rem;
  }
  
  .to-top-text {
    display: none;
  }
  
  .level-separator-to-top i {
    font-size: 0.85rem;
  }
}

@media (max-width: 768px) {
  .spells-page {
    padding: 15px;
    padding-top: 120px;
  }
  
  .page-header h1 {
    font-size: 2.5rem;
  }
  
  .search-section {
    padding: 20px;
  }
  
  .decorative-image-container {
    margin: 20px auto;
  }
  
  .overlay-title {
    font-size: 2rem;
  }
  
  .overlay-subtitle {
    font-size: 1rem;
  }
  
  .image-overlay {
    padding: 20px 30px;
  }
  
  .filters-container {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-group {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    min-width: auto;
  }
  
  .spell-results.grid {
    grid-template-columns: 1fr;
  }
  
  .spell-results.list .spell-card {
    flex-direction: column;
    align-items: stretch;
  }
  
  .spell-class-levels {
    min-width: 280px;
    max-width: 100%;
    padding-left: 0;
    border-left: none;
    border-top: 1px solid rgba(102, 126, 234, 0.2);
    padding-top: 20px;
    margin-top: 20px;
  }
  
  .results-header {
    flex-direction: column;
    gap: 15px;
    align-items: stretch;
    padding: 20px 20px 0;
  }
  
  .results-title-section h2 {
    font-size: 1.5rem;
  }
  
  .spell-details {
    grid-template-columns: 1fr;
  }
  
  .spell-results.list .spell-main-content {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }
  
  .spell-results.list .spell-header {
    min-width: auto;
  }
  
  .spell-results.list .spell-details {
    flex-direction: column;
    gap: 8px;
  }
  
  .spell-results.list .spell-detail-row {
    flex-direction: row;
    justify-content: space-between;
    text-align: left;
    min-width: auto;
  }
  
  .class-levels-grid {
    justify-content: center;
  }
  
  .class-level {
    min-width: 55px;
  }
  
  .class-icon {
    width: 20px;
    height: 20px;
  }
  
  .pagination {
    flex-direction: column;
    gap: 12px;
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 2rem;
  }
  
  .search-input-group {
    flex-direction: column;
  }
  
  .search-button {
    justify-content: center;
  }
  
  .spell-card {
    padding: 20px;
  }
  
  .class-levels-grid {
    justify-content: center;
    gap: 6px;
  }
  
  .class-level {
    min-width: 50px;
    padding: 6px 4px;
  }
  
  .class-icon {
    width: 18px;
    height: 18px;
  }
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.modal-content {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.95) 0%, rgba(45, 55, 72, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  max-width: 800px;
  width: 100%;
  max-height: 95vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.spell-modal {
  max-width: 900px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 25px 30px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
}

.modal-header-content {
  display: flex;
  align-items: center;
  gap: 20px;
  flex: 1;
}

.spell-icon-modal-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.spell-icon-modal {
  width: 48px;
  height: 48px;
  object-fit: contain;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}

.spell-icon-placeholder-modal {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 24px;
}

.spell-header-info h3 {
  font-size: 1.8rem;
  font-weight: 700;
  margin: 0 0 8px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.spell-header-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.spell-id-badge, .skill-badge {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%);
  color: #e2e8f0;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.modal-close {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #e2e8f0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 16px;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.05);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 0;
}

.spell-details {
  padding: 30px;
}

.detail-section {
  margin-bottom: 30px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h4 {
  font-size: 1.3rem;
  font-weight: 700;
  margin: 0 0 20px 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow: none;
}

.primary-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.primary-stat-item {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 15px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.3s ease;
}

.primary-stat-item:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.stat-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.3) 0%, rgba(118, 75, 162, 0.3) 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #e2e8f0;
  font-size: 16px;
}

.stat-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 1.2rem;
  font-weight: 700;
  color: #e2e8f0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.stat-label {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 2px;
}

.class-requirements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 16px;
  max-height: 450px; /* Ensure 4 full cards are visible before scrolling */
  overflow-y: auto;
  padding-right: 8px; /* Space for scrollbar */
}

/* Custom scrollbar styling */
.class-requirements-grid::-webkit-scrollbar {
  width: 8px;
}

.class-requirements-grid::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.class-requirements-grid::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.6) 0%, rgba(118, 75, 162, 0.6) 100%);
  border-radius: 4px;
}

.class-requirements-grid::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.8) 0%, rgba(118, 75, 162, 0.8) 100%);
}

.class-requirement-item {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.3s ease;
  min-height: 80px;
}

.class-requirement-item:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
}

.class-icon-detail {
  width: auto;
  height: 100%;
  max-width: 60px;
  object-fit: contain;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}

.class-req-text {
  font-weight: 600;
  color: #e2e8f0;
  font-size: 0.95rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  white-space: nowrap;
}

.effects-list, .components-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 10px;
}

.effect-item, .component-item {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 10px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.effect-label, .component-label {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
}

.effect-value, .component-value {
  font-weight: 700;
  color: #e2e8f0;
}

.additional-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.info-item {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
}

.info-value {
  font-weight: 700;
  color: #e2e8f0;
}

/* Make spell cards clickable */
.spell-card {
  cursor: pointer;
  transition: all 0.3s ease;
}

.spell-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.2) inset;
}

/* Responsive Modal */
@media (max-width: 768px) {
  .modal-overlay {
    padding: 10px;
  }
  
  .modal-header {
    padding: 20px;
  }
  
  .spell-details {
    padding: 20px;
  }
  
  .primary-stats-grid,
  .class-requirements-grid,
  .additional-info-grid {
    grid-template-columns: 1fr;
  }
  
  .effects-list,
  .components-list {
    grid-template-columns: 1fr;
  }
  
  .spell-header-info h3 {
    font-size: 1.5rem;
  }
}
</style>