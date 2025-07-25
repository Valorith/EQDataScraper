<template>
  <div class="items-page">
    <div class="page-header">
      <h1>Item Database</h1>
      <p class="subtitle">Search and explore items from the database</p>
    </div>

    <!-- Search Section -->
    <div class="search-section">
      <div class="search-container">
        <div class="search-input-group">
          <input
            v-model="searchQuery"
            @keyup.enter="performSearch()"
            type="text"
            placeholder="Search items by name..."
            class="search-input"
          />
          <button @click="performSearch()" class="search-button" :disabled="searching">
            <i :class="searching ? 'fas fa-spinner fa-spin' : 'fas fa-search'"></i>
            <span class="search-button-text">{{ searching ? 'Searching...' : 'Search' }}</span>
          </button>
        </div>
        
        <!-- Filters -->
        <div class="filters-container">
          <div class="filter-group">
            <label for="class-filter">Class:</label>
            <select id="class-filter" v-model="selectedClass" class="filter-select">
              <option value="">All Classes</option>
              <option value="1">Warrior</option>
              <option value="2">Cleric</option>
              <option value="4">Paladin</option>
              <option value="8">Ranger</option>
              <option value="16">Shadow Knight</option>
              <option value="32">Druid</option>
              <option value="64">Monk</option>
              <option value="128">Bard</option>
              <option value="256">Rogue</option>
              <option value="512">Shaman</option>
              <option value="1024">Necromancer</option>
              <option value="2048">Wizard</option>
              <option value="4096">Magician</option>
              <option value="8192">Enchanter</option>
              <option value="16384">Beastlord</option>
              <option value="32768">Berserker</option>
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
              placeholder="255"
              min="1"
              max="255"
            />
          </div>
          
          <button @click="clearFilters" class="clear-filters-button">
            <i class="fas fa-times"></i>
            Clear Filters
          </button>
          
          <!-- Advanced Filter Button -->
          <div class="advanced-filter-container">
            <button @click="toggleFilterDropdown" class="advanced-filter-button">
              <i class="fas fa-filter"></i>
              Advanced Filters
            </button>
            
            <!-- Filter Field Dropdown -->
            <div v-if="showFilterDropdown && !showFilterConfig" class="filter-dropdown">
              <div class="filter-search-wrapper">
                <input
                  v-model="filterSearchQuery"
                  @keydown.escape="showFilterDropdown = false"
                  type="text"
                  placeholder="Search filter fields..."
                  class="filter-search-input"
                  ref="filterSearchInput"
                />
                <i class="fas fa-search filter-search-icon"></i>
              </div>
              
              <div class="filter-fields-list">
                <div
                  v-for="field in filteredFields"
                  :key="field.name"
                  @click="selectFilterField(field)"
                  class="filter-field-item"
                >
                  <span class="filter-field-label">{{ field.label }}</span>
                  <span class="filter-field-type">{{ field.type }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Filter Configuration Modal -->
          <div v-if="showFilterConfig && currentFilterConfig && currentFilterConfig.field" class="filter-config-modal">
            <div class="filter-config-header">
              <h4>Configure Filter: {{ currentFilterConfig.field?.label }}</h4>
              <button @click="cancelFilterConfig" class="filter-config-close">
                <i class="fas fa-times"></i>
              </button>
            </div>
            
            <div class="filter-config-body">
              <!-- Operator Selection -->
              <div class="filter-config-group">
                <label>Operator:</label>
                <select v-model="currentFilterConfig.operator" class="filter-config-select">
                  <option v-for="op in (currentFilterConfig.field?.operators || [])" :key="op" :value="op">
                    {{ formatOperatorVerbose(op) }}
                  </option>
                </select>
              </div>
              
              <!-- Value Input(s) -->
              <div v-if="currentFilterConfig.field?.type === 'boolean'" class="filter-config-group">
                <label>Value:</label>
                <select v-model="currentFilterConfig.value" class="filter-config-select">
                  <option :value="true">Yes</option>
                  <option :value="false">No</option>
                </select>
              </div>
              
              <div v-else-if="currentFilterConfig.operator === 'exists'" class="filter-config-group">
                <p class="filter-config-info">This will find items where {{ currentFilterConfig.field?.label }} has any value.</p>
              </div>
              
              <div v-else-if="currentFilterConfig.operator === 'between'" class="filter-config-group">
                <label>Min Value:</label>
                <input 
                  v-model="currentFilterConfig.value" 
                  :type="currentFilterConfig.field?.type === 'number' ? 'number' : 'text'"
                  class="filter-config-input"
                  :placeholder="`Minimum ${currentFilterConfig.field?.label}`"
                />
                <label>Max Value:</label>
                <input 
                  v-model="currentFilterConfig.value2" 
                  :type="currentFilterConfig.field?.type === 'number' ? 'number' : 'text'"
                  class="filter-config-input"
                  :placeholder="`Maximum ${currentFilterConfig.field?.label}`"
                />
              </div>
              
              <div v-else class="filter-config-group">
                <label>Value:</label>
                <input 
                  v-model="currentFilterConfig.value" 
                  :type="currentFilterConfig.field?.type === 'number' ? 'number' : 'text'"
                  class="filter-config-input"
                  :placeholder="`Enter ${currentFilterConfig.field?.label}`"
                  @keyup.enter="applyFilterConfig"
                />
              </div>
            </div>
            
            <div class="filter-config-footer">
              <button @click="cancelFilterConfig" class="filter-config-cancel">Cancel</button>
              <button @click="applyFilterConfig" class="filter-config-apply" :disabled="!isFilterConfigValid">
                Apply Filter
              </button>
            </div>
          </div>
        </div>
        
        <!-- Active Filter Pills -->
        <div v-if="activeFilters.length > 0" class="filter-pills-container">
          <div
            v-for="(filter, index) in activeFilters"
            :key="index"
            class="filter-pill"
            :title="`${filter.field?.label} ${formatOperatorVerbose(filter.operator)} ${formatFilterValue(filter)}`"
          >
            <span class="filter-pill-field">{{ filter.field?.label }}</span>
            <span class="filter-pill-operator">{{ formatOperator(filter.operator) }}</span>
            <span class="filter-pill-value">{{ formatFilterValue(filter) }}</span>
            <button @click="removeFilter(index)" class="filter-pill-remove" title="Remove filter">
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Database Status -->
    <div v-if="!databaseAvailable" class="database-status">
      <div class="status-card error">
        <i class="fas fa-exclamation-triangle"></i>
        <div>
          <h3>Database Not Available</h3>
          <p>Please configure a database connection in the admin panel to search items.</p>
        </div>
      </div>
    </div>

    <!-- Decorative Image (shown when no search is active) -->
    <div v-if="!searching && !searchPerformed" class="decorative-image-container">
      <div class="image-wrapper">
        <img 
          src="@/assets/images/goblin-scholar.png" 
          alt="Goblin scholar studying ancient tomes"
          class="decorative-image"
        />
        <div class="image-overlay">
          <h2 class="overlay-title">Item Search</h2>
          <p class="overlay-subtitle">Discover legendary artifacts and treasures</p>
        </div>
      </div>
    </div>

    <!-- Loading Modals (outside conditional section for initial search) -->
    <LoadingModal 
      :visible="searching && !paginating"
      text="Searching"
      :timeoutMs="15000"
      @timeout="onSearchTimeout"
    />
    <!-- Pagination Loading Modal -->
    <LoadingModal 
      :visible="paginating"
      text="Loading"
      :timeoutMs="10000"
      @timeout="onPaginationTimeout"
    />
    <!-- Drop Sources Loading Modal -->
    <LoadingModal 
      :visible="loadingDropSources"
      text="Loading drop sources..."
      :randomClassIcon="true"
      :fullScreen="true"
      :timeoutMs="10000"
      @timeout="onDropSourcesTimeout"
    />
    <!-- Merchant Sources Loading Modal -->
    <LoadingModal 
      :visible="loadingMerchantSources"
      text="Loading merchant sources..."
      :randomClassIcon="true"
      :fullScreen="true"
      :timeoutMs="10000"
      @timeout="onMerchantSourcesTimeout"
    />
    
    <LoadingModal 
      :visible="loadingGroundSpawns"
      text="Loading ground spawns..."
      :randomClassIcon="true"
      :fullScreen="true"
      :timeoutMs="10000"
      @timeout="onGroundSpawnsTimeout"
    />
    
    <LoadingModal 
      :visible="loadingForageSources"
      text="Loading forage sources..."
      :randomClassIcon="true"
      :fullScreen="true"
      :timeoutMs="10000"
      @timeout="onForageSourcesTimeout"
    />
    
    <LoadingModal 
      :visible="loadingTradeskillRecipes"
      text="Loading tradeskill recipes..."
      :randomClassIcon="true"
      :fullScreen="true"
      :timeoutMs="10000"
      @timeout="onTradeskillRecipesTimeout"
    />

    <!-- Created By Recipes Loading Modal -->
    <LoadingModal 
      :visible="loadingCreatedByRecipes"
      text="Loading creation recipes..."
      :randomClassIcon="true"
      :fullScreen="true"
      :timeoutMs="10000"
      @timeout="onCreatedByRecipesTimeout"
    />

    <!-- Recipe Details Loading Modal -->
    <LoadingModal 
      :visible="loadingRecipeDetails"
      text="Loading recipe details..."
      :randomClassIcon="true"
      :fullScreen="true"
      :timeoutMs="10000"
      @timeout="onRecipeDetailsTimeout"
    />

    <!-- Item Modal Loading Modal -->
    <LoadingModal 
      :visible="loadingItemModal"
      text="Loading item details..."
      :randomClassIcon="true"
      :fullScreen="true"
      :timeoutMs="10000"
      @timeout="onItemModalTimeout"
    />

    <!-- Search Results Section -->
    <div v-if="searching || searchPerformed" class="results-section">
      
      <div v-if="!searching && items.length > 0" class="results-header">
        <div class="results-title-section">
          <h2>Search Results</h2>
          <div class="results-info">
            <span>{{ totalCount }} items found</span>
            <span v-if="searchQuery">(searching for "{{ searchQuery }}")</span>
          </div>
        </div>
        <div class="view-toggle-container">
          <span class="view-toggle-label">View:</span>
          <div class="view-toggle">
            <button 
              @click="viewMode = 'grid'" 
              :class="['view-button', { active: viewMode === 'grid' }]"
              title="Grid View"
            >
              <i class="fas fa-th"></i>
              <span class="view-button-text">Grid</span>
            </button>
            <button 
              @click="viewMode = 'list'" 
              :class="['view-button', { active: viewMode === 'list' }]"
              title="List View"
            >
              <i class="fas fa-list"></i>
              <span class="view-button-text">List</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Top Pagination -->
      <div v-if="totalPages > 1 && !searching && items.length > 0" class="pagination pagination-top">
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

      <!-- Grid View -->
      <div v-if="viewMode === 'grid' && items.length > 0 && !searching" class="items-grid">
        <div 
          v-for="item in items" 
          :key="item.item_id"
          class="item-card"
          @click="selectItem(item)"
        >
          <!-- Card Header with Icon and Name -->
          <div class="card-header">
            <div class="card-icon-section">
              <img 
                v-if="item.icon" 
                :src="`/icons/items/${item.icon}.png`" 
                :alt="`${item.name} icon`"
                class="item-icon-grid"
                @error="handleIconError"
              />
              <div v-else class="item-icon-placeholder-grid">
                <i class="fas fa-cube"></i>
              </div>
            </div>
            <div class="card-title-section">
              <h3 class="item-name">{{ item.name }}</h3>
              <span class="item-type">{{ getItemTypeDisplay(item.itemtype) || item.type || 'Unknown' }}</span>
            </div>
          </div>
          
          <!-- Item Properties -->
          <div v-if="item.magic || item.lore_flag || item.nodrop || item.norent" class="card-properties">
            <span v-if="item.magic" class="property magic">Magic</span>
            <span v-if="item.lore_flag" class="property lore">Lore</span>
            <span v-if="item.nodrop" class="property nodrop">No Drop</span>
            <span v-if="item.norent" class="property norent">No Rent</span>
          </div>
          
          <!-- Primary Stats Section -->
          <div class="card-stats">
            <!-- Weapon Stats -->
            <div v-if="item.damage && item.delay" class="stat-group weapon-stats">
              <div class="stat-row">
                <span class="stat-label">Damage</span>
                <span class="stat-value">{{ item.damage }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">Delay</span>
                <span class="stat-value">{{ item.delay }}</span>
              </div>
              <div class="stat-row ratio">
                <span class="stat-label">Ratio</span>
                <span class="stat-value">{{ getWeaponRatio(item.damage, item.delay) }}</span>
              </div>
            </div>
            
            <!-- Defensive Stats -->
            <div v-if="item.ac || item.hp || item.mana" class="stat-group defensive-stats">
              <div v-if="item.ac" class="stat-row">
                <span class="stat-label">AC</span>
                <span class="stat-value">{{ item.ac }}</span>
              </div>
              <div v-if="item.hp" class="stat-row">
                <span class="stat-label">HP</span>
                <span class="stat-value">+{{ item.hp }}</span>
              </div>
              <div v-if="item.mana" class="stat-row">
                <span class="stat-label">Mana</span>
                <span class="stat-value">+{{ item.mana }}</span>
              </div>
            </div>
            
            <!-- Attributes -->
            <div v-if="hasAnyStats(item)" class="stat-group attributes">
              <div v-if="item.str" class="stat-row">
                <span class="stat-label">STR</span>
                <span class="stat-value">+{{ item.str }}</span>
              </div>
              <div v-if="item.sta" class="stat-row">
                <span class="stat-label">STA</span>
                <span class="stat-value">+{{ item.sta }}</span>
              </div>
              <div v-if="item.agi" class="stat-row">
                <span class="stat-label">AGI</span>
                <span class="stat-value">+{{ item.agi }}</span>
              </div>
              <div v-if="item.dex" class="stat-row">
                <span class="stat-label">DEX</span>
                <span class="stat-value">+{{ item.dex }}</span>
              </div>
              <div v-if="item.wis" class="stat-row">
                <span class="stat-label">WIS</span>
                <span class="stat-value">+{{ item.wis }}</span>
              </div>
              <div v-if="item.int" class="stat-row">
                <span class="stat-label">INT</span>
                <span class="stat-value">+{{ item.int }}</span>
              </div>
              <div v-if="item.cha" class="stat-row">
                <span class="stat-label">CHA</span>
                <span class="stat-value">+{{ item.cha }}</span>
              </div>
            </div>
          </div>
          
          <!-- Card Footer -->
          <div class="card-footer">
            <div v-if="getSlotDisplay(item.slots)" class="footer-item">
              <i class="fas fa-shield-alt"></i>
              <span>{{ getSlotDisplay(item.slots) }}</span>
            </div>
            <div v-if="item.reqlevel" class="footer-item level">
              <i class="fas fa-signal"></i>
              <span>Level {{ item.reqlevel }}</span>
            </div>
            <div v-if="item.classes" class="footer-item classes">
              <i class="fas fa-users"></i>
              <span>{{ getClassDisplay(item.classes) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- List View -->
      <div v-if="viewMode === 'list' && items.length > 0 && !searching" class="items-list">
        <div 
          v-for="item in items" 
          :key="item.item_id"
          class="item-row"
          @click="selectItem(item)"
        >
          <div class="item-icon-container">
            <img 
              v-if="item.icon" 
              :src="`/icons/items/${item.icon}.png`" 
              :alt="`${item.name} icon`"
              class="item-icon"
              @error="handleIconError"
            />
            <div v-else class="item-icon-placeholder">
              <i class="fas fa-cube"></i>
            </div>
          </div>
          <div class="item-main-info">
            <h3 class="item-name">{{ item.name }}</h3>
            <div class="item-meta">
              <span class="item-type">{{ getItemTypeDisplay(item.itemtype) || item.type || 'Unknown' }}</span>
              <span v-if="item.magic" class="property magic">Magic</span>
              <span v-if="item.lore_flag" class="property lore">Lore</span>
              <span v-if="item.nodrop" class="property nodrop">No Drop</span>
              <span v-if="item.norent" class="property norent">No Rent</span>
              <span v-if="item.artifact" class="property artifact">Artifact</span>
            </div>
          </div>
          
          <div class="item-center-content">
            <!-- Primary Stats Row -->
            <div class="item-stats-primary">
              <div v-if="item.damage && item.delay" class="stat-inline weapon-stats">
                <span class="stat-label">DMG:</span>
                <span class="stat-value">{{ item.damage }}</span>
                <span class="stat-label">DLY:</span>
                <span class="stat-value">{{ item.delay }}</span>
                <span class="weapon-ratio">{{ getWeaponRatio(item.damage, item.delay) }}</span>
              </div>
              <div v-if="item.ac" class="stat-inline">
                <span class="stat-label">AC:</span>
                <span class="stat-value">{{ item.ac }}</span>
              </div>
              <div v-if="item.hp" class="stat-inline">
                <span class="stat-label">HP:</span>
                <span class="stat-value">{{ item.hp }}</span>
              </div>
              <div v-if="item.mana" class="stat-inline">
                <span class="stat-label">Mana:</span>
                <span class="stat-value">{{ item.mana }}</span>
              </div>
              
              <!-- Show only top 3 stats -->
              <template v-if="hasAnyStats(item)">
                <div v-for="stat in getTopStatsDisplay(item)" :key="stat.name" class="stat-inline attr">
                  <span class="stat-label">{{ stat.name }}:</span>
                  <span class="stat-value">+{{ stat.value }}</span>
                </div>
              </template>
            </div>
            
            <!-- Bottom Row with Slot/Class/Level -->
            <div class="item-info-row">
              <div v-if="getSlotDisplay(item.slots)" class="info-item">
                <span class="info-label">Slot:</span>
                <span class="info-value">{{ getSlotDisplay(item.slots) }}</span>
              </div>
              <div v-if="item.classes" class="info-item">
                <span class="info-label">Class:</span>
                <span class="info-value">{{ getClassDisplay(item.classes) }}</span>
              </div>
              <div v-if="item.races" class="info-item">
                <span class="info-label">Race:</span>
                <span class="info-value">{{ getRaceDisplay(item.races) }}</span>
              </div>
              <div v-if="item.reqlevel" class="info-item">
                <span class="info-label">Req:</span>
                <span class="info-value">{{ item.reqlevel }}</span>
              </div>
            </div>
          </div>
          
          <div class="item-action">
            <i class="fas fa-chevron-right"></i>
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

    <!-- No Results -->
    <div v-if="searchPerformed && items.length === 0 && !searching" class="no-results">
      <div class="no-results-icon">
        <i class="fas fa-search"></i>
      </div>
      <h3>No items found</h3>
      <p v-if="searchQuery">No items match your search for "{{ searchQuery }}"</p>
      <p v-else>Try searching with different criteria</p>
    </div>

    <!-- Item Details Modal -->
    <div v-if="selectedItemDetail && !loadingItemModal" class="modal-overlay" @click="closeItemModal">
      <div class="modal-content item-modal" @click.stop>
        <div class="modal-header">
          <div class="modal-header-content">
            <div class="item-icon-modal-container">
              <img 
                v-if="selectedItemDetail.icon" 
                :src="`/icons/items/${selectedItemDetail.icon}.png`" 
                :alt="`${selectedItemDetail.name} icon`"
                class="item-icon-modal"
                @error="handleIconError"
              />
              <div v-else class="item-icon-placeholder-modal">
                <i class="fas fa-cube"></i>
              </div>
            </div>
            <div class="item-header-info">
              <h3>{{ selectedItemDetail.name }}</h3>
              <div class="item-header-meta">
                <span class="item-type-badge">{{ getItemTypeDisplay(selectedItemDetail.itemtype) }}</span>
                <span v-if="selectedItemDetail.magic" class="property-badge magic">Magic</span>
                <span v-if="selectedItemDetail.lore" class="property-badge lore">Lore</span>
                <span v-if="selectedItemDetail.nodrop" class="property-badge nodrop">No Drop</span>
                <span v-if="selectedItemDetail.norent" class="property-badge norent">No Rent</span>
              </div>
            </div>
          </div>
          <button @click="closeItemModal" class="modal-close">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <div class="item-details">
            <!-- Primary Stats -->
            <div v-if="selectedItemDetail.damage || selectedItemDetail.ac || selectedItemDetail.hp || selectedItemDetail.mana" class="detail-section primary-stats">
              <h4>Primary Stats</h4>
              <div class="primary-stats-grid">
                <div v-if="selectedItemDetail.damage && selectedItemDetail.delay" class="primary-stat-item weapon">
                  <div class="stat-icon"><i class="fas fa-sword"></i></div>
                  <div class="stat-info">
                    <span class="stat-value">{{ selectedItemDetail.damage }} / {{ selectedItemDetail.delay }}</span>
                    <span class="stat-label">Damage / Delay</span>
                    <span class="stat-extra">Ratio: {{ getWeaponRatio(selectedItemDetail.damage, selectedItemDetail.delay) }}</span>
                  </div>
                </div>
                <div v-if="selectedItemDetail.ac" class="primary-stat-item">
                  <div class="stat-icon"><i class="fas fa-shield-alt"></i></div>
                  <div class="stat-info">
                    <span class="stat-value">{{ selectedItemDetail.ac }}</span>
                    <span class="stat-label">Armor Class</span>
                  </div>
                </div>
                <div v-if="selectedItemDetail.hp" class="primary-stat-item">
                  <div class="stat-icon"><i class="fas fa-heart"></i></div>
                  <div class="stat-info">
                    <span class="stat-value">+{{ selectedItemDetail.hp }}</span>
                    <span class="stat-label">Hit Points</span>
                  </div>
                </div>
                <div v-if="selectedItemDetail.mana" class="primary-stat-item">
                  <div class="stat-icon"><i class="fas fa-star"></i></div>
                  <div class="stat-info">
                    <span class="stat-value">+{{ selectedItemDetail.mana }}</span>
                    <span class="stat-label">Mana</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Attributes -->
            <div v-if="hasAnyStats(selectedItemDetail)" class="detail-section">
              <h4>Attributes</h4>
              <div class="attributes-grid">
                <div v-if="selectedItemDetail.str" class="attribute-item">
                  <span class="attr-label">STR</span>
                  <span class="attr-value">+{{ selectedItemDetail.str }}</span>
                </div>
                <div v-if="selectedItemDetail.sta" class="attribute-item">
                  <span class="attr-label">STA</span>
                  <span class="attr-value">+{{ selectedItemDetail.sta }}</span>
                </div>
                <div v-if="selectedItemDetail.agi" class="attribute-item">
                  <span class="attr-label">AGI</span>
                  <span class="attr-value">+{{ selectedItemDetail.agi }}</span>
                </div>
                <div v-if="selectedItemDetail.dex" class="attribute-item">
                  <span class="attr-label">DEX</span>
                  <span class="attr-value">+{{ selectedItemDetail.dex }}</span>
                </div>
                <div v-if="selectedItemDetail.wis" class="attribute-item">
                  <span class="attr-label">WIS</span>
                  <span class="attr-value">+{{ selectedItemDetail.wis }}</span>
                </div>
                <div v-if="selectedItemDetail.int" class="attribute-item">
                  <span class="attr-label">INT</span>
                  <span class="attr-value">+{{ selectedItemDetail.int }}</span>
                </div>
                <div v-if="selectedItemDetail.cha" class="attribute-item">
                  <span class="attr-label">CHA</span>
                  <span class="attr-value">+{{ selectedItemDetail.cha }}</span>
                </div>
              </div>
            </div>
            
            <!-- Resistances -->
            <div v-if="hasResistValues(selectedItemDetail)" class="detail-section">
              <h4>Resistances</h4>
              <div class="resistances-grid">
                <div v-if="(selectedItemDetail.resistances?.fire || selectedItemDetail.fr) && (selectedItemDetail.resistances?.fire || selectedItemDetail.fr) !== 0" class="resist-item fire">
                  <span class="resist-label">Fire</span>
                  <span class="resist-value">+{{ selectedItemDetail.resistances?.fire || selectedItemDetail.fr }}</span>
                </div>
                <div v-if="(selectedItemDetail.resistances?.cold || selectedItemDetail.cr) && (selectedItemDetail.resistances?.cold || selectedItemDetail.cr) !== 0" class="resist-item cold">
                  <span class="resist-label">Cold</span>
                  <span class="resist-value">+{{ selectedItemDetail.resistances?.cold || selectedItemDetail.cr }}</span>
                </div>
                <div v-if="(selectedItemDetail.resistances?.magic || selectedItemDetail.mr) && (selectedItemDetail.resistances?.magic || selectedItemDetail.mr) !== 0" class="resist-item magic">
                  <span class="resist-label">Magic</span>
                  <span class="resist-value">+{{ selectedItemDetail.resistances?.magic || selectedItemDetail.mr }}</span>
                </div>
                <div v-if="(selectedItemDetail.resistances?.disease || selectedItemDetail.dr) && (selectedItemDetail.resistances?.disease || selectedItemDetail.dr) !== 0" class="resist-item disease">
                  <span class="resist-label">Disease</span>
                  <span class="resist-value">+{{ selectedItemDetail.resistances?.disease || selectedItemDetail.dr }}</span>
                </div>
                <div v-if="(selectedItemDetail.resistances?.poison || selectedItemDetail.pr) && (selectedItemDetail.resistances?.poison || selectedItemDetail.pr) !== 0" class="resist-item poison">
                  <span class="resist-label">Poison</span>
                  <span class="resist-value">+{{ selectedItemDetail.resistances?.poison || selectedItemDetail.pr }}</span>
                </div>
              </div>
            </div>
            
            <!-- Requirements & Restrictions -->
            <div class="detail-section">
              <h4>Requirements & Restrictions</h4>
              <div class="requirements-grid">
                <div v-if="selectedItemDetail.classes" class="requirement-item">
                  <span class="req-label">Classes:</span>
                  <span class="req-value">{{ getClassDisplay(selectedItemDetail.classes) }}</span>
                </div>
                <div v-if="selectedItemDetail.races" class="requirement-item">
                  <span class="req-label">Races:</span>
                  <span class="req-value">{{ getRaceDisplay(selectedItemDetail.races) }}</span>
                </div>
                <div v-if="selectedItemDetail.slots" class="requirement-item">
                  <span class="req-label">Slot:</span>
                  <span class="req-value">{{ getSlotDisplay(selectedItemDetail.slots) }}</span>
                </div>
                <div v-if="selectedItemDetail.reqlevel" class="requirement-item">
                  <span class="req-label">Required Level:</span>
                  <span class="req-value">{{ selectedItemDetail.reqlevel }}</span>
                </div>
                <div v-if="selectedItemDetail.weight" class="requirement-item">
                  <span class="req-label">Weight:</span>
                  <span class="req-value">{{ (selectedItemDetail.weight / 10).toFixed(1) }}</span>
                </div>
              </div>
            </div>
            
            <!-- Effects -->
            <div v-if="hasEffects(selectedItemDetail)" class="detail-section">
              <h4>Effects</h4>
              <div class="effects-list">
                <div v-if="selectedItemDetail.effects?.click && selectedItemDetail.effects.click !== -1" class="effect-item">
                  <span class="effect-type">Click:</span>
                  <span class="effect-value">Effect #{{ selectedItemDetail.effects.click }}</span>
                </div>
                <div v-if="selectedItemDetail.effects?.proc && selectedItemDetail.effects.proc !== -1" class="effect-item">
                  <span class="effect-type">Proc:</span>
                  <span class="effect-value">Effect #{{ selectedItemDetail.effects.proc }}</span>
                </div>
                <div v-if="selectedItemDetail.effects?.worn && selectedItemDetail.effects.worn !== -1" class="effect-item">
                  <span class="effect-type">Worn:</span>
                  <span class="effect-value">Effect #{{ selectedItemDetail.effects.worn }}</span>
                </div>
                <div v-if="selectedItemDetail.effects?.focus && selectedItemDetail.effects.focus !== -1" class="effect-item">
                  <span class="effect-type">Focus:</span>
                  <span class="effect-value">Effect #{{ selectedItemDetail.effects.focus }}</span>
                </div>
              </div>
            </div>
            
            <!-- Drop Sources Section -->
            <div v-if="shouldShowDropSources" class="detail-section drop-sources-section">
              <div class="drop-sources-header">
                <h4>Where does this drop?</h4>
                <button 
                  v-if="!dropSourcesRequested"
                  @click="loadDropSources" 
                  class="drop-sources-button"
                >
                  <i class="fas fa-map-marked-alt"></i>
                  <span>Show Drop Sources</span>
                </button>
              </div>
              
              <!-- Drop Sources Results -->
              <div v-if="dropSources && !loadingDropSources" class="drop-sources-results">
                <div v-if="dropSources.length === 0" class="no-drop-sources">
                  <i class="fas fa-exclamation-circle"></i>
                  <div class="no-sources-content">
                    <span v-if="itemDataAvailability && itemDataAvailability.drop_sources > 0">
                      Drop sources may be temporarily unavailable. Please try again later.
                    </span>
                    <span v-else>
                      No drop sources found for this item
                    </span>
                    <button 
                      v-if="itemDataAvailability && itemDataAvailability.drop_sources > 0"
                      @click="retryDropSources"
                      class="retry-button"
                      title="Try loading drop sources again"
                    >
                      <i class="fas fa-redo"></i>
                      Retry
                    </button>
                  </div>
                </div>
                
                <div v-else class="zones-list">
                  <div v-for="zone in dropSources" :key="zone.zone_short" class="zone-section">
                    <div class="zone-header">
                      <i class="fas fa-map-marker-alt"></i>
                      <span class="zone-name">{{ zone.zone_name }}</span>
                      <span class="npc-count">({{ zone.npcs.length }} NPCs)</span>
                    </div>
                    
                    <div class="npcs-list">
                      <div 
                        v-for="npc in zone.npcs" 
                        :key="npc.npc_id" 
                        class="npc-item clickable"
                        @click="openNPCModal(npc.npc_id, npc.npc_name)"
                      >
                        <span class="npc-name">{{ npc.npc_name }}</span>
                        <span class="drop-chance">{{ npc.drop_chance }}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Merchant Sources Section -->
            <div v-if="shouldShowMerchantSources" class="detail-section merchant-sources-section">
              <div class="merchant-sources-header">
                <h4>Where can this be bought?</h4>
                <button 
                  v-if="!merchantSourcesRequested"
                  @click="loadMerchantSources" 
                  class="merchant-sources-button"
                >
                  <i class="fas fa-coins"></i>
                  <span>Show Merchant Sources</span>
                </button>
              </div>
              
              <!-- Merchant Sources Results -->
              <div v-if="merchantSources && !loadingMerchantSources" class="merchant-sources-results">
                <div v-if="merchantSources.length === 0" class="no-merchant-sources">
                  <i class="fas fa-exclamation-circle"></i>
                  <span>No merchant sources found for this item</span>
                </div>
                
                <div v-else class="zones-list">
                  <div v-for="zone in merchantSources" :key="zone.zone_short" class="zone-section">
                    <div class="zone-header">
                      <i class="fas fa-map-marker-alt"></i>
                      <span class="zone-name">{{ zone.zone_name }}</span>
                      <span class="merchant-count">({{ zone.merchants.length }} merchants)</span>
                    </div>
                    
                    <div class="merchants-list">
                      <div v-for="merchant in zone.merchants" :key="merchant.npc_id" class="merchant-item">
                        <span class="merchant-name">{{ merchant.npc_name }}</span>
                        <div class="merchant-pricing">
                          <span v-if="merchant.merchant_type === 'ldon_merchant'" class="adventure-points">
                            {{ merchant.pricing_info }}
                          </span>
                          <div v-else-if="merchant.price_coins" class="coin-display">
                            <span v-if="merchant.price_coins.platinum > 0" class="coin platinum">
                              <img src="/icons/coins/platinum.svg" alt="Platinum" class="coin-icon">
                              {{ merchant.price_coins.platinum }}
                            </span>
                            <span v-if="merchant.price_coins.gold > 0" class="coin gold">
                              <img src="/icons/coins/gold.svg" alt="Gold" class="coin-icon">
                              {{ merchant.price_coins.gold }}
                            </span>
                            <span v-if="merchant.price_coins.silver > 0" class="coin silver">
                              <img src="/icons/coins/silver.svg" alt="Silver" class="coin-icon">
                              {{ merchant.price_coins.silver }}
                            </span>
                            <span v-if="merchant.price_coins.bronze > 0" class="coin bronze">
                              <img src="/icons/coins/bronze.svg" alt="Bronze" class="coin-icon">
                              {{ merchant.price_coins.bronze }}
                            </span>
                            <span v-if="merchant.price_copper === 0" class="free-item">Free</span>
                          </div>
                          <span v-else class="merchant-type">{{ merchant.merchant_type }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Ground Spawns Section -->
            <div v-if="shouldShowGroundSpawns" class="detail-section ground-spawns-section">
              <div class="ground-spawns-header">
                <h4>
                  <i class="fas fa-map-marker-alt"></i>
                  Ground Spawns
                </h4>
                <button 
                  v-if="!groundSpawns && !loadingGroundSpawns"
                  @click="loadGroundSpawns" 
                  class="ground-spawns-button"
                  :disabled="loadingGroundSpawns"
                >
                  <i class="fas fa-search"></i>
                  Show ground spawns
                </button>
              </div>
              
              <!-- Ground Spawns Results -->
              <div v-if="groundSpawns && !loadingGroundSpawns" class="ground-spawns-results">
                <div v-if="groundSpawns.length === 0" class="no-ground-spawns">
                  <i class="fas fa-exclamation-circle"></i>
                  <span>No ground spawns found for this item</span>
                </div>
                
                <div v-else class="zones-list">
                  <div v-for="zone in groundSpawns" :key="zone.zone_short" class="zone-section">
                    <div class="zone-header">
                      <i class="fas fa-map-marker-alt"></i>
                      <span class="zone-name">{{ zone.zone_name }}</span>
                      <span class="spawn-count">({{ zone.spawn_points.length }} locations)</span>
                    </div>
                    
                    <div class="spawn-points-list">
                      <div v-for="spawn in zone.spawn_points" :key="spawn.spawn_id" class="spawn-point-item">
                        <span class="spawn-location">Ground spawn location</span>
                        <span v-if="spawn.respawn_timer" class="respawn-timer">{{ spawn.respawn_timer }}s respawn</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Forage Sources Section -->
            <div v-if="shouldShowForageSources" class="detail-section forage-sources-section">
              <div class="forage-sources-header">
                <h4>
                  <i class="fas fa-leaf"></i>
                  Forage Sources
                </h4>
                <button 
                  v-if="!forageSources && !loadingForageSources"
                  @click="loadForageSources" 
                  class="forage-sources-button"
                  :disabled="loadingForageSources"
                >
                  <i class="fas fa-search"></i>
                  Show forage sources
                </button>
              </div>
              
              <!-- Forage Sources Results -->
              <div v-if="forageSources && !loadingForageSources" class="forage-sources-results">
                <div v-if="forageSources.length === 0" class="no-forage-sources">
                  <i class="fas fa-exclamation-circle"></i>
                  <span>No forage sources found for this item</span>
                </div>
                
                <div v-else class="zones-list">
                  <div v-for="zone in forageSources" :key="zone.zone_short" class="zone-section">
                    <div class="zone-header">
                      <i class="fas fa-map-marker-alt"></i>
                      <span class="zone-name">{{ zone.zone_name }}</span>
                      <span class="forage-count">({{ zone.forage_info.length }} locations)</span>
                    </div>
                    
                    <div class="forage-info-list">
                      <div v-for="(info, index) in zone.forage_info" :key="index" class="forage-info-item">
                        <span class="forage-chance">{{ info.chance }}% chance</span>
                        <span v-if="info.level" class="forage-level">Level {{ info.level }}+</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Tradeskill Recipes Section -->
            <div v-if="shouldShowTradeskillRecipes" class="detail-section tradeskill-recipes-section">
              <div class="tradeskill-recipes-header">
                <h4>
                  <i class="fas fa-hammer"></i>
                  Tradeskill Recipes
                </h4>
                <button 
                  v-if="!tradeskillRecipes && !loadingTradeskillRecipes"
                  @click="loadTradeskillRecipes" 
                  class="tradeskill-recipes-button"
                  :disabled="loadingTradeskillRecipes"
                >
                  <i class="fas fa-search"></i>
                  Show tradeskill recipes
                </button>
              </div>
              
              <!-- Tradeskill Recipes Results -->
              <div v-if="tradeskillRecipes && !loadingTradeskillRecipes" class="tradeskill-recipes-results">
                <div v-if="tradeskillRecipes.length === 0" class="no-tradeskill-recipes">
                  <i class="fas fa-exclamation-circle"></i>
                  <span>No tradeskill recipes found for this item</span>
                </div>
                
                <div v-else class="skills-list">
                  <div v-for="skill in tradeskillRecipes" :key="skill.tradeskill_id" class="skill-section">
                    <div class="skill-header">
                      <i class="fas fa-tools"></i>
                      <span class="skill-name">{{ skill.tradeskill_name }}</span>
                      <span class="recipe-count">({{ skill.recipes.length }} recipes)</span>
                    </div>
                    
                    <div class="recipes-list">
                      <div v-for="recipe in skill.recipes" :key="recipe.recipe_id" class="recipe-list-item">
                        <div class="recipe-item-icon">
                          <img 
                            v-if="recipe.result_item_icon" 
                            :src="`/icons/items/${recipe.result_item_icon}.png`" 
                            :alt="recipe.result_item_name || recipe.recipe_name"
                            @error="handleIconError"
                            class="item-icon-img"
                          />
                          <i v-else class="fas fa-hammer"></i>
                        </div>
                        <div class="recipe-item-info">
                          <span class="recipe-name clickable" @click="loadRecipeDetails(recipe.recipe_id)">{{ recipe.recipe_name }}</span>
                          <div class="recipe-item-badges">
                            <span v-if="recipe.component_count > 1" class="component-count">{{ recipe.component_count }} needed</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Created by Recipes Section -->
            <div v-if="shouldShowCreatedByRecipes" class="detail-section created-by-recipes-section">
              <div class="created-by-recipes-header">
                <h4>
                  <i class="fas fa-cog"></i>
                  Created by Recipes
                </h4>
                <button 
                  v-if="!createdByRecipes && !loadingCreatedByRecipes"
                  @click="loadCreatedByRecipes" 
                  class="created-by-recipes-button"
                  :disabled="loadingCreatedByRecipes"
                >
                  <i class="fas fa-search"></i>
                  Show creation recipes
                </button>
              </div>
              
              <!-- Created by Recipes Results -->
              <div v-if="createdByRecipes && !loadingCreatedByRecipes" class="created-by-recipes-results">
                <div v-if="createdByRecipes.length === 0" class="no-created-by-recipes">
                  <i class="fas fa-exclamation-circle"></i>
                  <span>This item is not created by any tradeskill recipes</span>
                </div>
                
                <div v-else class="creation-recipes-list">
                  <div v-for="recipe in createdByRecipes" :key="recipe.recipe_id" class="creation-recipe-item">
                    <div class="recipe-item-icon">
                      <img 
                        v-if="recipe.result_item_icon" 
                        :src="`/icons/items/${recipe.result_item_icon}.png`" 
                        :alt="recipe.result_item_name || recipe.recipe_name"
                        @error="handleIconError"
                        class="item-icon-img"
                      />
                      <i v-else class="fas fa-cog"></i>
                    </div>
                    <div class="recipe-item-info">
                      <span class="recipe-name clickable" @click="loadRecipeDetails(recipe.recipe_id)">
                        {{ recipe.recipe_name }}
                      </span>
                      <div class="recipe-item-badges">
                        <span class="tradeskill-badge">{{ recipe.tradeskill_name }}</span>
                        <span class="trivial-level">Trivial: {{ recipe.trivial_level }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Lore Text -->
            <div v-if="selectedItemDetail.lore" class="detail-section lore-section">
              <h4>Lore</h4>
              <div class="lore-text">{{ selectedItemDetail.lore }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Recipe Details Modal -->
  <div v-if="selectedRecipe" class="modal-overlay" @click="closeRecipeDetails">
    <div class="modal-content recipe-modal" @click.stop>
      <div class="modal-header">
        <h3>Recipe Details</h3>
        <button @click="closeRecipeDetails" class="close-button">
          <i class="fas fa-times"></i>
        </button>
      </div>
      
      <div class="modal-body">
        <div v-if="selectedRecipe" class="recipe-details">
          <!-- Recipe Header -->
          <div class="recipe-header">
            <h4>{{ selectedRecipe.recipe.recipe_name }}</h4>
            <div class="recipe-info">
              <span class="tradeskill-badge">{{ selectedRecipe.recipe.tradeskill_name }}</span>
              <span class="trivial-level">Trivial: {{ selectedRecipe.recipe.trivial_level }}</span>
            </div>
          </div>
          
          <!-- What it Creates -->
          <div v-if="selectedRecipe.creates && selectedRecipe.creates.length > 0" class="recipe-section creates-section">
            <h5><i class="fas fa-magic"></i> Creates</h5>
            <div class="items-grid">
              <div 
                v-for="item in selectedRecipe.creates" 
                :key="item.item_id" 
                :class="['recipe-item', { 'clickable': item.is_discovered, 'undiscovered': !item.is_discovered }]"
                @click="item.is_discovered ? selectItem({ item_id: item.item_id, Name: item.item_name }) && closeRecipeDetails() : null"
              >
                <div class="recipe-item-icon">
                  <img 
                    v-if="item.item_icon" 
                    :src="`/icons/items/${item.item_icon}.png`" 
                    :alt="item.item_name"
                    @error="handleIconError"
                    class="item-icon-img"
                  />
                  <i v-else class="fas fa-cube"></i>
                </div>
                <div class="recipe-item-info">
                  <span class="item-name">{{ item.item_name }}</span>
                  <div class="recipe-item-badges">
                    <span v-if="!item.is_discovered" class="undiscovered-badge">Not Discovered</span>
                    <span v-if="item.success_count > 1" class="item-count">x{{ item.success_count }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- What it Requires -->
          <div v-if="selectedRecipe.requires && selectedRecipe.requires.length > 0" class="recipe-section requires-section">
            <h5><i class="fas fa-list"></i> Required Components</h5>
            <div class="items-grid">
              <div 
                v-for="item in selectedRecipe.requires" 
                :key="item.item_id" 
                :class="['recipe-item', { 'clickable': item.is_discovered, 'undiscovered': !item.is_discovered }]"
                @click="item.is_discovered ? selectItem({ item_id: item.item_id, Name: item.item_name }) && closeRecipeDetails() : null"
              >
                <div class="recipe-item-icon">
                  <img 
                    v-if="item.item_icon" 
                    :src="`/icons/items/${item.item_icon}.png`" 
                    :alt="item.item_name"
                    @error="handleIconError"
                    class="item-icon-img"
                  />
                  <i v-else class="fas fa-cube"></i>
                </div>
                <div class="recipe-item-info">
                  <span class="item-name">{{ item.item_name }}</span>
                  <div class="recipe-item-badges">
                    <span v-if="!item.is_discovered" class="undiscovered-badge">Not Discovered</span>
                    <span v-if="item.component_count > 1" class="item-count">x{{ item.component_count }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Container Items -->
          <div v-if="selectedRecipe.containers && selectedRecipe.containers.length > 0" class="recipe-section containers-section">
            <h5><i class="fas fa-box"></i> Container Required</h5>
            <div class="items-grid">
              <div 
                v-for="item in selectedRecipe.containers" 
                :key="item.item_id" 
                :class="['recipe-item', { 'clickable': item.is_discovered, 'undiscovered': !item.is_discovered }]"
                @click="item.is_discovered ? selectItem({ item_id: item.item_id, Name: item.item_name }) && closeRecipeDetails() : null"
              >
                <div class="recipe-item-icon">
                  <img 
                    v-if="item.item_icon" 
                    :src="`/icons/items/${item.item_icon}.png`" 
                    :alt="item.item_name"
                    @error="handleIconError"
                    class="item-icon-img"
                  />
                  <i v-else class="fas fa-box"></i>
                </div>
                <div class="recipe-item-info">
                  <span class="item-name">{{ item.item_name }}</span>
                  <div class="recipe-item-badges">
                    <span v-if="!item.is_discovered" class="undiscovered-badge">Not Discovered</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Recipe Notes -->
          <div v-if="selectedRecipe.recipe.notes" class="recipe-section notes-section">
            <h5><i class="fas fa-sticky-note"></i> Notes</h5>
            <div class="recipe-notes">{{ selectedRecipe.recipe.notes }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getApiBaseUrl } from '../config/api'
import LoadingModal from '../components/LoadingModal.vue'
import { toastService } from '../services/toastService'
import axios from 'axios'

// State
const searchQuery = ref('')
// Type filter removed - not needed
const selectedClass = ref('')
const minLevel = ref('')
const maxLevel = ref('')
const items = ref([])
// Item types removed - not needed
const totalCount = ref(0)
const currentPage = ref(1)
const itemsPerPage = ref(20)
const searching = ref(false)
const searchPerformed = ref(false)
const databaseAvailable = ref(true)
const selectedItemDetail = ref(null)
const viewMode = ref('list') // Default to list view
const paginating = ref(false) // Loading state for pagination
const searchStartTime = ref(null) // Track when search started

// Drop sources state
const dropSources = ref(null)
const loadingDropSources = ref(false)
const dropSourcesRequested = ref(false)

// Merchant sources state
const merchantSources = ref(null)
const loadingMerchantSources = ref(false)
const merchantSourcesRequested = ref(false)

// Ground spawns state
const groundSpawns = ref(null)
const loadingGroundSpawns = ref(false)
const groundSpawnsRequested = ref(false)

// Forage sources state
const forageSources = ref(null)
const loadingForageSources = ref(false)
const forageSourcesRequested = ref(false)

// Tradeskill recipes state
const tradeskillRecipes = ref(null)
const loadingTradeskillRecipes = ref(false)
const tradeskillRecipesRequested = ref(false)

// Created by recipes state
const createdByRecipes = ref(null)
const loadingCreatedByRecipes = ref(false)
const createdByRecipesRequested = ref(false)

// Recipe details state
const selectedRecipe = ref(null)
const loadingRecipeDetails = ref(false)

// Data availability state
const itemDataAvailability = ref(null)
const loadingAvailability = ref(false)

// Item modal loading state - encompasses both item details and availability loading
const loadingItemModal = ref(false)

// Computed properties for section visibility - Only show when data exists
const shouldShowDropSources = computed(() => {
  // Show while loading
  if (loadingAvailability.value) return false
  
  // Show all if availability check failed (fallback)
  if (itemDataAvailability.value === 'failed') return true
  
  // Show if no availability data yet (initial state)
  if (!itemDataAvailability.value) return false
  
  // Only show if data exists
  return itemDataAvailability.value.drop_sources > 0
})

const shouldShowMerchantSources = computed(() => {
  if (loadingAvailability.value) return false
  if (itemDataAvailability.value === 'failed') return true
  if (!itemDataAvailability.value) return false
  return itemDataAvailability.value.merchant_sources > 0
})

const shouldShowGroundSpawns = computed(() => {
  if (loadingAvailability.value) return false
  if (itemDataAvailability.value === 'failed') return true
  if (!itemDataAvailability.value) return false
  return itemDataAvailability.value.ground_spawns > 0
})

const shouldShowForageSources = computed(() => {
  if (loadingAvailability.value) return false
  if (itemDataAvailability.value === 'failed') return true
  if (!itemDataAvailability.value) return false
  return itemDataAvailability.value.forage_sources > 0
})

const shouldShowTradeskillRecipes = computed(() => {
  if (loadingAvailability.value) return false
  if (itemDataAvailability.value === 'failed') return true
  if (!itemDataAvailability.value) return false
  return itemDataAvailability.value.tradeskill_recipes > 0
})

const shouldShowCreatedByRecipes = computed(() => {
  if (loadingAvailability.value) return false
  if (itemDataAvailability.value === 'failed') return true
  if (!itemDataAvailability.value) return false
  return itemDataAvailability.value.created_by_recipes > 0
})

// Advanced filtering state
const showFilterDropdown = ref(false)
const filterSearchQuery = ref('')
const activeFilters = ref([])
const filterFieldInput = ref('')
const filterSearchInput = ref(null)
const showFilterConfig = ref(false)
const currentFilterConfig = ref(null)

// Available filter fields based on item schema
const filterFields = [
  // Basic fields
  { name: 'lore', label: 'Lore Text', type: 'text', operators: ['contains', 'equals'] },
  { name: 'price', label: 'Price', type: 'number', operators: ['equals', 'not equals', 'greater than', 'less than', 'between'] },
  { name: 'weight', label: 'Weight', type: 'number', operators: ['equals', 'not equals', 'greater than', 'less than', 'between'] },
  { name: 'size', label: 'Size', type: 'number', operators: ['equals', 'not equals', 'greater than', 'less than'] },
  
  // Combat stats
  { name: 'damage', label: 'Damage', type: 'number', operators: ['equals', 'greater than', 'less than', 'between'] },
  { name: 'delay', label: 'Delay', type: 'number', operators: ['equals', 'greater than', 'less than', 'between'] },
  { name: 'ac', label: 'Armor Class', type: 'number', operators: ['equals', 'greater than', 'less than', 'between'] },
  { name: 'hp', label: 'Hit Points', type: 'number', operators: ['equals', 'greater than', 'less than', 'between'] },
  { name: 'mana', label: 'Mana', type: 'number', operators: ['equals', 'greater than', 'less than', 'between'] },
  
  // Attributes
  { name: 'str', label: 'Strength', type: 'number', operators: ['equals', 'greater than', 'less than', 'between'] },
  { name: 'sta', label: 'Stamina', type: 'number', operators: ['equals', 'greater than', 'less than', 'between'] },
  { name: 'agi', label: 'Agility', type: 'number', operators: ['equals', 'greater than', 'less than', 'between'] },
  { name: 'dex', label: 'Dexterity', type: 'number', operators: ['equals', 'greater than', 'less than', 'between'] },
  { name: 'wis', label: 'Wisdom', type: 'number', operators: ['equals', 'greater than', 'less than', 'between'] },
  { name: 'int', label: 'Intelligence', type: 'number', operators: ['equals', 'greater than', 'less than', 'between'] },
  { name: 'cha', label: 'Charisma', type: 'number', operators: ['equals', 'greater than', 'less than', 'between'] },
  
  // Resistances
  { name: 'mr', label: 'Magic Resist', type: 'number', operators: ['equals', 'greater than', 'less than'] },
  { name: 'fr', label: 'Fire Resist', type: 'number', operators: ['equals', 'greater than', 'less than'] },
  { name: 'cr', label: 'Cold Resist', type: 'number', operators: ['equals', 'greater than', 'less than'] },
  { name: 'dr', label: 'Disease Resist', type: 'number', operators: ['equals', 'greater than', 'less than'] },
  { name: 'pr', label: 'Poison Resist', type: 'number', operators: ['equals', 'greater than', 'less than'] },
  
  // Flags
  { name: 'magic', label: 'Magic Item', type: 'boolean', operators: ['is'] },
  { name: 'lore_flag', label: 'Lore Item', type: 'boolean', operators: ['is'] },
  { name: 'nodrop', label: 'No Drop', type: 'boolean', operators: ['is'] },
  { name: 'norent', label: 'No Rent', type: 'boolean', operators: ['is'] },
  { name: 'artifact', label: 'Artifact', type: 'boolean', operators: ['is'] },
  
  // Requirements
  { name: 'reqlevel', label: 'Required Level', type: 'number', operators: ['equals', 'greater than', 'less than', 'between'] },
  { name: 'reclevel', label: 'Recommended Level', type: 'number', operators: ['equals', 'greater than', 'less than', 'between'] },
  
  // Slots
  { name: 'slots', label: 'Equipment Slot', type: 'slot', operators: ['includes'] },
  
  // Effects
  { name: 'clickeffect', label: 'Click Effect', type: 'text', operators: ['exists', 'contains'] },
  { name: 'proceffect', label: 'Proc Effect', type: 'text', operators: ['exists', 'contains'] },
  { name: 'worneffect', label: 'Worn Effect', type: 'text', operators: ['exists', 'contains'] },
  { name: 'focuseffect', label: 'Focus Effect', type: 'text', operators: ['exists', 'contains'] }
]

// Computed
const totalPages = computed(() => Math.ceil(totalCount.value / itemsPerPage.value))

const filteredFields = computed(() => {
  if (!filterSearchQuery.value) return filterFields
  
  const query = filterSearchQuery.value.toLowerCase()
  return filterFields.filter(field => 
    field.label.toLowerCase().includes(query) || 
    field.name.toLowerCase().includes(query)
  )
})

const isFilterConfigValid = computed(() => {
  if (!currentFilterConfig.value || !currentFilterConfig.value.field) return false
  
  const config = currentFilterConfig.value
  
  // For 'exists' operator, no value needed
  if (config.operator === 'exists') return true
  
  // For 'between' operator, both values needed
  if (config.operator === 'between') {
    return config.value !== '' && config.value !== null && 
           config.value2 !== '' && config.value2 !== null
  }
  
  // For all other operators, just need value
  return config.value !== '' && config.value !== null
})

// Methods

const performSearch = async (page = 1) => {
  if (!searchQuery.value && !selectedClass.value && !minLevel.value && !maxLevel.value && activeFilters.value.length === 0) {
    toastService.warning('Please enter a search term or select a filter')
    return
  }

  // If paginating is already true, we're doing a page change
  // Otherwise, show the normal searching state
  if (!paginating.value) {
    searching.value = true
  }
  searchPerformed.value = true
  currentPage.value = page
  searchStartTime.value = Date.now() // Record when search started

  try {
    const params = new URLSearchParams()
    if (searchQuery.value) params.append('q', searchQuery.value)
    // Type filter removed
    if (selectedClass.value) params.append('class', selectedClass.value)
    
    // Validate numeric inputs before sending
    if (minLevel.value !== '' && minLevel.value !== null) {
      const minLevelNum = parseInt(minLevel.value)
      if (!isNaN(minLevelNum) && minLevelNum > 0) {
        params.append('min_level', minLevelNum.toString())
      }
    }
    
    if (maxLevel.value !== '' && maxLevel.value !== null) {
      const maxLevelNum = parseInt(maxLevel.value)
      if (!isNaN(maxLevelNum) && maxLevelNum > 0) {
        params.append('max_level', maxLevelNum.toString())
      }
    }
    
    params.append('limit', itemsPerPage.value.toString())
    params.append('offset', ((page - 1) * itemsPerPage.value).toString())
    
    // Add advanced filters
    if (activeFilters.value.length > 0) {
      const filters = activeFilters.value.map(filter => ({
        field: filter.field.name,
        operator: filter.operator,
        value: filter.value,
        value2: filter.value2
      }))
      params.append('filters', JSON.stringify(filters))
    }
    
    // Debug log
    console.log('Search params:', params.toString())

    // Add timeout to prevent hanging on slow queries
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 28000) // 28s timeout (under Railway's 30s)
    
    const response = await fetch(`${getApiBaseUrl()}/api/items/search?${params}`, {
      signal: controller.signal
    })
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      if (response.status === 503) {
        databaseAvailable.value = false
        throw new Error('Database not available')
      }
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    // Handle both array response (current API) and object response (future API)
    if (Array.isArray(data)) {
      items.value = data
      totalCount.value = data.length
    } else {
      items.value = data.items || []
      totalCount.value = data.total_count || 0
    }
    databaseAvailable.value = true
    
    // Ensure loading modal shows for minimum 1 second
    const elapsedTime = Date.now() - searchStartTime.value
    const minDisplayTime = 1000 // 1 second
    const remainingTime = Math.max(0, minDisplayTime - elapsedTime)
    
    if (remainingTime > 0) {
      await new Promise(resolve => setTimeout(resolve, remainingTime))
    }
    
  } catch (error) {
    console.error('Error searching items:', error)
    if (error.name === 'AbortError') {
      toastService.warning('Search timed out. The query is taking too long. Try using more specific search terms.')
    } else {
      toastService.error('Error searching items: ' + error.message)
    }
    items.value = []
    totalCount.value = 0
    
    // Ensure loading modal shows for minimum 1 second even on error
    const elapsedTime = Date.now() - searchStartTime.value
    const minDisplayTime = 1000
    const remainingTime = Math.max(0, minDisplayTime - elapsedTime)
    
    if (remainingTime > 0) {
      await new Promise(resolve => setTimeout(resolve, remainingTime))
    }
  } finally {
    searching.value = false
    paginating.value = false
  }
}

const changePage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    // Clear current items to show loading state
    items.value = []
    
    // Set paginating state
    paginating.value = true
    searchStartTime.value = Date.now() // Track pagination start time too
    
    // Perform the search
    performSearch(page)
  }
}

const clearFilters = () => {
  searchQuery.value = ''
  // Type filter removed
  selectedClass.value = ''
  minLevel.value = ''
  maxLevel.value = ''
  items.value = []
  totalCount.value = 0
  searchPerformed.value = false
  currentPage.value = 1
  activeFilters.value = []
}

// Advanced filter methods
const toggleFilterDropdown = async () => {
  showFilterDropdown.value = !showFilterDropdown.value
  if (showFilterDropdown.value) {
    filterSearchQuery.value = ''
    // Wait for next DOM update cycle
    await nextTick()
    // Focus the search input
    if (filterSearchInput.value) {
      filterSearchInput.value.focus()
    }
  }
}


const selectFilterField = (field) => {
  if (!field) {
    console.error('No field provided to selectFilterField')
    return
  }
  
  // Set up the filter configuration
  currentFilterConfig.value = {
    field: field,
    operator: field.operators && field.operators[0] ? field.operators[0] : 'equals',
    value: '',
    value2: '' // For 'between' operator
  }
  
  // Hide dropdown and show configuration modal
  showFilterDropdown.value = false
  showFilterConfig.value = true
}

const removeFilter = (index) => {
  activeFilters.value.splice(index, 1)
}

const formatFilterValue = (filter) => {
  if (!filter || !filter.field) return 'Not set'
  
  if (filter.field.type === 'boolean') {
    return filter.value ? 'Yes' : 'No'
  }
  if (filter.operator === 'between' && filter.value2) {
    return `${filter.value} - ${filter.value2}`
  }
  if (filter.operator === 'exists') {
    return 'Any'
  }
  return filter.value || 'Not set'
}

const formatOperator = (operator) => {
  const operatorMap = {
    'equals': '=',
    'not equals': '≠',
    'contains': 'contains',
    'starts with': 'starts with',
    'ends with': 'ends with',
    'greater than': '>',
    'less than': '<',
    'between': 'between',
    'exists': 'has value'
  }
  return operatorMap[operator] || operator
}

const formatOperatorVerbose = (operator) => {
  const operatorMap = {
    'equals': 'Equals',
    'not equals': 'Not Equals',
    'contains': 'Contains',
    'starts with': 'Starts With',
    'ends with': 'Ends With',
    'greater than': 'Greater Than',
    'less than': 'Less Than',
    'between': 'Between',
    'exists': 'Has Value'
  }
  return operatorMap[operator] || operator
}

const applyFilterConfig = () => {
  if (isFilterConfigValid.value && currentFilterConfig.value && currentFilterConfig.value.field) {
    activeFilters.value.push({
      field: currentFilterConfig.value.field,
      operator: currentFilterConfig.value.operator,
      value: currentFilterConfig.value.value,
      value2: currentFilterConfig.value.value2
    })
    
    // Reset and close
    currentFilterConfig.value = null
    showFilterConfig.value = false
  }
}

const cancelFilterConfig = () => {
  currentFilterConfig.value = null
  showFilterConfig.value = false
}

const selectItem = async (item) => {
  // Start loading modal
  loadingItemModal.value = true
  
  // Clear all source states when selecting a new item
  dropSources.value = null
  loadingDropSources.value = false
  dropSourcesRequested.value = false
  merchantSources.value = null
  loadingMerchantSources.value = false
  merchantSourcesRequested.value = false
  groundSpawns.value = null
  loadingGroundSpawns.value = false
  groundSpawnsRequested.value = false
  forageSources.value = null
  loadingForageSources.value = false
  forageSourcesRequested.value = false
  tradeskillRecipes.value = null
  loadingTradeskillRecipes.value = false
  tradeskillRecipesRequested.value = false
  createdByRecipes.value = null
  loadingCreatedByRecipes.value = false
  createdByRecipesRequested.value = false
  itemDataAvailability.value = null
  loadingAvailability.value = false
  
  try {
    const response = await fetch(`${getApiBaseUrl()}/api/items/${item.item_id}`)
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    selectedItemDetail.value = data.item
    
    // Load data availability after item details are loaded
    await loadItemDataAvailability(item.item_id)
  } catch (error) {
    console.error('Error loading item details:', error)
    toastService.error('Error loading item details: ' + error.message)
  } finally {
    // Stop loading modal only after both item details and availability are loaded
    loadingItemModal.value = false
  }
}

const loadItemDataAvailability = async (itemId) => {
  if (!itemId) return
  
  loadingAvailability.value = true
  
  try {
    const response = await fetch(`${getApiBaseUrl()}/api/items/${itemId}/availability`)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    itemDataAvailability.value = data
    
  } catch (error) {
    console.error('Error loading item data availability:', error)
    // Fallback: Set to 'failed' state so we can show all buttons
    itemDataAvailability.value = 'failed'
  } finally {
    loadingAvailability.value = false
  }
}

const closeItemModal = () => {
  selectedItemDetail.value = null
  // Clear drop sources when closing modal
  dropSources.value = null
  loadingDropSources.value = false
  dropSourcesRequested.value = false
  // Clear merchant sources when closing modal
  merchantSources.value = null
  loadingMerchantSources.value = false
  merchantSourcesRequested.value = false
  // Clear ground spawns when closing modal
  groundSpawns.value = null
  loadingGroundSpawns.value = false
  groundSpawnsRequested.value = false
  // Clear forage sources when closing modal
  forageSources.value = null
  loadingForageSources.value = false
  forageSourcesRequested.value = false
  // Clear tradeskill recipes when closing modal
  tradeskillRecipes.value = null
  loadingTradeskillRecipes.value = false
  tradeskillRecipesRequested.value = false
  // Clear created by recipes when closing modal
  createdByRecipes.value = null
  loadingCreatedByRecipes.value = false
  createdByRecipesRequested.value = false
  // Clear availability data when closing modal
  itemDataAvailability.value = null
  loadingAvailability.value = false
  // Clear item modal loading state
  loadingItemModal.value = false
}

const loadDropSources = async () => {
  if (!selectedItemDetail.value?.item_id) return
  
  // Set flags immediately to hide button and show loading
  dropSourcesRequested.value = true
  loadingDropSources.value = true
  
  // Track start time for minimum display duration
  const startTime = Date.now()
  
  try {
    const response = await axios.get(`${getApiBaseUrl()}/api/items/${selectedItemDetail.value.item_id}/drop-sources`, {
      timeout: 25000 // 25 second timeout for drop sources
    })
    
    dropSources.value = response.data.zones || []
    
  } catch (error) {
    console.error('Error loading drop sources:', error)
    let errorMessage = 'Error loading drop sources: '
    
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      errorMessage += 'Request timed out. The item may have many drop sources. Please try again.'
    } else if (error.response?.status >= 500) {
      errorMessage += 'Server error occurred. Please try again in a moment.'
    } else if (!error.response) {
      errorMessage += 'Network error occurred. Please check your connection and try again.'
    } else {
      errorMessage += error.message
    }
    
    toastService.error(errorMessage)
    dropSources.value = []
    dropSourcesRequested.value = false // Reset to allow retry
  } finally {
    // Ensure loading modal shows for minimum 1 second
    const elapsedTime = Date.now() - startTime
    const minDisplayTime = 1000 // 1 second
    const remainingTime = Math.max(0, minDisplayTime - elapsedTime)
    
    if (remainingTime > 0) {
      await new Promise(resolve => setTimeout(resolve, remainingTime))
    }
    
    loadingDropSources.value = false
  }
}

const retryDropSources = async () => {
  // Reset the state and try again
  dropSources.value = null
  dropSourcesRequested.value = false
  await loadDropSources()
}

const loadMerchantSources = async () => {
  if (!selectedItemDetail.value?.item_id) return
  
  // Set flags immediately to hide button and show loading
  merchantSourcesRequested.value = true
  loadingMerchantSources.value = true
  
  // Track start time for minimum display duration
  const startTime = Date.now()
  
  try {
    const response = await axios.get(`${getApiBaseUrl()}/api/items/${selectedItemDetail.value.item_id}/merchant-sources`, {
      timeout: 20000 // 20 second timeout for merchant sources
    })
    
    merchantSources.value = response.data.zones || []
    
  } catch (error) {
    console.error('Error loading merchant sources:', error)
    let errorMessage = 'Error loading merchant sources: '
    
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      errorMessage += 'Request timed out. The item may have many merchant sources. Please try again.'
    } else if (error.response?.status >= 500) {
      errorMessage += 'Server error occurred. Please try again in a moment.'
    } else if (!error.response) {
      errorMessage += 'Network error occurred. Please check your connection and try again.'
    } else {
      errorMessage += error.message
    }
    
    toastService.error(errorMessage)
    merchantSources.value = []
    merchantSourcesRequested.value = false // Reset to allow retry
  } finally {
    // Ensure loading modal shows for minimum 1 second
    const elapsedTime = Date.now() - startTime
    const minDisplayTime = 1000 // 1 second
    const remainingTime = Math.max(0, minDisplayTime - elapsedTime)
    
    if (remainingTime > 0) {
      await new Promise(resolve => setTimeout(resolve, remainingTime))
    }
    
    loadingMerchantSources.value = false
  }
}

const loadGroundSpawns = async () => {
  if (!selectedItemDetail.value?.item_id) return
  
  // Set flags immediately to hide button and show loading
  groundSpawnsRequested.value = true
  loadingGroundSpawns.value = true
  
  // Track start time for minimum display duration
  const startTime = Date.now()
  
  try {
    const response = await fetch(`${getApiBaseUrl()}/api/items/${selectedItemDetail.value.item_id}/ground-spawns`)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    groundSpawns.value = data.zones || []
    
  } catch (error) {
    console.error('Error loading ground spawns:', error)
    toastService.error('Error loading ground spawns: ' + error.message)
    groundSpawns.value = null // Reset to null to allow retry (uses !groundSpawns condition)
  } finally {
    // Ensure loading modal shows for minimum 1 second
    const elapsedTime = Date.now() - startTime
    const minDisplayTime = 1000 // 1 second
    const remainingTime = Math.max(0, minDisplayTime - elapsedTime)
    
    if (remainingTime > 0) {
      await new Promise(resolve => setTimeout(resolve, remainingTime))
    }
    
    loadingGroundSpawns.value = false
  }
}

const loadForageSources = async () => {
  if (!selectedItemDetail.value?.item_id) return
  
  // Set flags immediately to hide button and show loading
  forageSourcesRequested.value = true
  loadingForageSources.value = true
  
  // Track start time for minimum display duration
  const startTime = Date.now()
  
  try {
    const response = await fetch(`${getApiBaseUrl()}/api/items/${selectedItemDetail.value.item_id}/forage-sources`)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    forageSources.value = data.zones || []
    
  } catch (error) {
    console.error('Error loading forage sources:', error)
    toastService.error('Error loading forage sources: ' + error.message)
    forageSources.value = null // Reset to null to allow retry (uses !forageSources condition)
  } finally {
    // Ensure loading modal shows for minimum 1 second
    const elapsedTime = Date.now() - startTime
    const minDisplayTime = 1000 // 1 second
    const remainingTime = Math.max(0, minDisplayTime - elapsedTime)
    
    if (remainingTime > 0) {
      await new Promise(resolve => setTimeout(resolve, remainingTime))
    }
    
    loadingForageSources.value = false
  }
}

const loadTradeskillRecipes = async () => {
  if (!selectedItemDetail.value?.item_id) return
  
  // Set flags immediately to hide button and show loading
  tradeskillRecipesRequested.value = true
  loadingTradeskillRecipes.value = true
  
  // Track start time for minimum display duration
  const startTime = Date.now()
  
  try {
    const response = await fetch(`${getApiBaseUrl()}/api/items/${selectedItemDetail.value.item_id}/tradeskill-recipes`)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    tradeskillRecipes.value = data.skills || []
    
  } catch (error) {
    console.error('Error loading tradeskill recipes:', error)
    toastService.error('Error loading tradeskill recipes: ' + error.message)
    tradeskillRecipes.value = null // Reset to null to allow retry (uses !tradeskillRecipes condition)
  } finally {
    // Ensure loading modal shows for minimum 1 second
    const elapsedTime = Date.now() - startTime
    const minDisplayTime = 1000 // 1 second
    const remainingTime = Math.max(0, minDisplayTime - elapsedTime)
    
    if (remainingTime > 0) {
      await new Promise(resolve => setTimeout(resolve, remainingTime))
    }
    
    loadingTradeskillRecipes.value = false
  }
}

const loadCreatedByRecipes = async () => {
  if (!selectedItemDetail.value?.item_id) return
  
  // Set flags immediately to hide button and show loading
  createdByRecipesRequested.value = true
  loadingCreatedByRecipes.value = true
  
  // Track start time for minimum display duration
  const startTime = Date.now()
  
  try {
    const response = await fetch(`${getApiBaseUrl()}/api/items/${selectedItemDetail.value.item_id}/created-by-recipes`)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    createdByRecipes.value = data.recipes || []
    
  } catch (error) {
    console.error('Error loading created by recipes:', error)
    toastService.error('Error loading created by recipes: ' + error.message)
    createdByRecipes.value = null // Reset to null to allow retry
  } finally {
    // Ensure loading modal shows for minimum 1 second
    const elapsedTime = Date.now() - startTime
    const minDisplayTime = 1000 // 1 second
    const remainingTime = Math.max(0, minDisplayTime - elapsedTime)
    
    if (remainingTime > 0) {
      await new Promise(resolve => setTimeout(resolve, remainingTime))
    }
    
    loadingCreatedByRecipes.value = false
  }
}

// Timeout handlers for loading modals
const onDropSourcesTimeout = () => {
  console.warn('Drop sources loading timed out')
  loadingDropSources.value = false
  dropSources.value = []
  dropSourcesRequested.value = false // Reset to show button again
  toastService.warning('Request timed out while loading drop sources. Please try again.')
}

const onMerchantSourcesTimeout = () => {
  console.warn('Merchant sources loading timed out')
  loadingMerchantSources.value = false
  merchantSources.value = []
  merchantSourcesRequested.value = false // Reset to show button again
  toastService.warning('Request timed out while loading merchant sources. Please try again.')
}

const onGroundSpawnsTimeout = () => {
  console.warn('Ground spawns loading timed out')
  loadingGroundSpawns.value = false
  groundSpawns.value = null // Reset to null to show button again (uses !groundSpawns condition)
  toastService.warning('Request timed out while loading ground spawns. Please try again.')
}

const onForageSourcesTimeout = () => {
  console.warn('Forage sources loading timed out')
  loadingForageSources.value = false
  forageSources.value = null // Reset to null to show button again (uses !forageSources condition)
  toastService.warning('Request timed out while loading forage sources. Please try again.')
}

const onTradeskillRecipesTimeout = () => {
  console.warn('Tradeskill recipes loading timed out')
  loadingTradeskillRecipes.value = false
  tradeskillRecipes.value = null // Reset to null to show button again (uses !tradeskillRecipes condition)
  toastService.warning('Request timed out while loading tradeskill recipes. Please try again.')
}

const onCreatedByRecipesTimeout = () => {
  console.warn('Created by recipes loading timed out')
  loadingCreatedByRecipes.value = false
  createdByRecipes.value = null // Reset to null to show button again (uses !createdByRecipes condition)
  toastService.warning('Request timed out while loading creation recipes. Please try again.')
}

const onRecipeDetailsTimeout = () => {
  console.warn('Recipe details loading timed out')
  loadingRecipeDetails.value = false
  selectedRecipe.value = null
  toastService.warning('Request timed out while loading recipe details. Please try again.')
}

const onItemModalTimeout = () => {
  console.warn('Item modal loading timed out')
  loadingItemModal.value = false
  selectedItemDetail.value = null
  toastService.warning('Request timed out while loading item details. Please try again.')
}

const loadRecipeDetails = async (recipeId) => {
  if (!recipeId) return
  
  loadingRecipeDetails.value = true
  
  // Track start time for minimum display duration
  const startTime = Date.now()
  
  try {
    const response = await fetch(`${getApiBaseUrl()}/api/recipes/${recipeId}`)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    selectedRecipe.value = data
    
  } catch (error) {
    console.error('Error loading recipe details:', error)
    toastService.error('Error loading recipe details: ' + error.message)
  } finally {
    // Ensure loading modal shows for minimum 1 second
    const elapsedTime = Date.now() - startTime
    const minDisplayTime = 1000 // 1 second
    const remainingTime = Math.max(0, minDisplayTime - elapsedTime)
    
    if (remainingTime > 0) {
      await new Promise(resolve => setTimeout(resolve, remainingTime))
    }
    
    loadingRecipeDetails.value = false
  }
}

const closeRecipeDetails = () => {
  selectedRecipe.value = null
  loadingRecipeDetails.value = false
}

const onSearchTimeout = () => {
  console.warn('Search request timed out')
  searching.value = false
  searchPerformed.value = true
  items.value = []
  toastService.warning('Search request timed out. Please try again with different criteria.')
}

const onPaginationTimeout = () => {
  console.warn('Pagination request timed out')
  paginating.value = false
  toastService.warning('Pagination request timed out. Please try again.')
}

const hasStats = (item) => {
  return item.ac || item.hp || item.mana || item.str || item.sta || item.agi || 
         item.dex || item.wis || item.int || item.cha
}

const handleIconError = (event) => {
  // Try fallback to icon 0 (blank/default icon)
  if (!event.target.dataset.fallbackAttempted) {
    event.target.dataset.fallbackAttempted = 'true'
    event.target.src = '/icons/items/0.png'
  } else {
    // If fallback also fails, hide the image and show placeholder
    event.target.style.display = 'none'
    // Show the placeholder by finding the sibling element
    const placeholder = event.target.nextElementSibling || event.target.parentElement.querySelector('.item-icon-placeholder, .item-icon-placeholder-grid, .item-icon-placeholder-modal')
    if (placeholder) {
      placeholder.style.display = 'flex'
    }
  }
}

// Utility functions for item display
const getItemTypeDisplay = (itemtype) => {
  const typeMap = {
    0: '1H Slashing',
    1: '2H Slashing',
    2: '1H Piercing',
    3: '1H Blunt',
    4: '2H Blunt',
    5: 'Archery',
    7: 'Throwing',
    8: 'Shield',
    10: 'Armor',
    11: 'Tradeskill Item',
    12: 'Lockpicking',
    14: 'Food',
    15: 'Drink',
    16: 'Light Source',
    17: 'Common Inventory Item',
    18: 'Bind Wound',
    19: 'Thrown Casting Item',
    20: 'Spells / Song Sheets',
    21: 'Potions',
    22: 'Fletched Arrows',
    23: 'Wind Instrument',
    24: 'Stringed Instrument',
    25: 'Brass Instrument',
    26: 'Percussion Instrument',
    27: 'Ammo',
    29: 'Jewelry',
    31: 'Readable Note/Scroll',
    32: 'Readable Book',
    33: 'Key',
    34: 'Odd Item',
    35: '2H Piercing',
    36: 'Fishing Pole',
    37: 'Fishing Bait',
    38: 'Alcoholic Beverage',
    39: 'More Keys',
    40: 'Compass',
    42: 'Poison',
    45: 'Hand to Hand',
    52: 'Charm',
    53: 'Dye',
    54: 'Augment',
    55: 'Augment Solvent',
    56: 'Augment Distiller',
    58: 'Fellowship Banner Material',
    60: 'Cultural Armor Manual',
    63: 'New Currency',
  }
  return typeMap[itemtype] || `Type ${itemtype}`
}

const getSlotDisplay = (slots) => {
  if (!slots) return null
  const slotMap = {
    1: 'Charm', 2: 'Ear', 4: 'Head', 8: 'Face',
    16: 'Ear', 32: 'Neck', 64: 'Shoulders', 128: 'Arms',
    256: 'Back', 512: 'Wrist', 1024: 'Wrist', 2048: 'Range',
    4096: 'Hands', 8192: 'Primary', 16384: 'Secondary',
    32768: 'Fingers', 65536: 'Chest', 131072: 'Legs',
    262144: 'Feet', 524288: 'Waist', 1048576: 'Power Source',
    2097152: 'Ammo'
  }
  
  const slotNames = []
  for (let [bit, name] of Object.entries(slotMap)) {
    if (slots & parseInt(bit)) {
      slotNames.push(name)
    }
  }
  
  // Remove duplicates using Set
  const uniqueSlots = [...new Set(slotNames)]
  
  return uniqueSlots.length > 0 ? uniqueSlots.join(', ') : null
}

const getClassDisplay = (classes) => {
  if (!classes || classes === 0) return 'None'
  
  // Check for all classes - 65535 is the bitmask for all 16 classes
  if (classes === 65535) return 'ALL'
  
  const classMap = {
    1: 'WAR', 2: 'CLR', 4: 'PAL', 8: 'RNG',
    16: 'SHD', 32: 'DRU', 64: 'MNK', 128: 'BRD',
    256: 'ROG', 512: 'SHM', 1024: 'NEC', 2048: 'WIZ',
    4096: 'MAG', 8192: 'ENC', 16384: 'BST', 32768: 'BER'
  }
  
  const classNames = []
  for (let [bit, name] of Object.entries(classMap)) {
    if (classes & parseInt(bit)) {
      classNames.push(name)
    }
  }
  
  // If all classes are included, return ALL
  if (classNames.length === Object.keys(classMap).length) {
    return 'ALL'
  }
  
  return classNames.length > 0 ? classNames.join(' ') : 'None'
}

const getRaceDisplay = (races) => {
  if (!races || races === 0) return 'None'
  
  // Check for all races - 65535 is the bitmask for all 16 races
  // Also check for other common "all races" values
  if (races === 65535 || races === 131071 || races === 32767) return 'ALL'
  
  const raceMap = {
    1: 'HUM', 2: 'BAR', 4: 'ERU', 8: 'ELF',
    16: 'HIE', 32: 'DEF', 64: 'HEF', 128: 'DWF',
    256: 'TRL', 512: 'OGR', 1024: 'HFL', 2048: 'GNM',
    4096: 'IKS', 8192: 'VAH', 16384: 'FRG', 32768: 'DRK'
  }
  
  const includedRaces = []
  const excludedRaces = []
  
  for (let [bit, name] of Object.entries(raceMap)) {
    if (races & parseInt(bit)) {
      includedRaces.push(name)
    } else {
      excludedRaces.push(name)
    }
  }
  
  // If all races are included, return ALL
  if (includedRaces.length === Object.keys(raceMap).length) {
    return 'ALL'
  }
  
  // If more than half the races can use it, show "All but X Y Z"
  if (includedRaces.length > Object.keys(raceMap).length / 2) {
    return `All but ${excludedRaces.join(' ')}`
  }
  
  return includedRaces.length > 0 ? includedRaces.join(' ') : 'None'
}

const hasAnyStats = (item) => {
  return item.str || item.sta || item.agi || item.dex || 
         item.wis || item.int || item.cha ||
         (item.stats && (item.stats.str || item.stats.sta || item.stats.agi || 
          item.stats.dex || item.stats.wis || item.stats.int || item.stats.cha))
}

const hasResists = (item) => {
  return item.mr || item.fr || item.cr || item.dr || item.pr || item.svcorruption
}

const hasResistValues = (item) => {
  return (item.mr && item.mr !== 0) || 
         (item.fr && item.fr !== 0) || 
         (item.cr && item.cr !== 0) || 
         (item.dr && item.dr !== 0) || 
         (item.pr && item.pr !== 0) ||
         (item.resistances && (
           (item.resistances.fire && item.resistances.fire !== 0) ||
           (item.resistances.cold && item.resistances.cold !== 0) ||
           (item.resistances.magic && item.resistances.magic !== 0) ||
           (item.resistances.disease && item.resistances.disease !== 0) ||
           (item.resistances.poison && item.resistances.poison !== 0)
         ))
}

const hasEffects = (item) => {
  return item.effects && (
    (item.effects.click && item.effects.click !== -1) ||
    (item.effects.proc && item.effects.proc !== -1) ||
    (item.effects.worn && item.effects.worn !== -1) ||
    (item.effects.focus && item.effects.focus !== -1)
  )
}

const getWeaponRatio = (damage, delay) => {
  if (!damage || !delay) return null
  return (damage / delay).toFixed(2)
}

const getTopStatsDisplay = (item) => {
  const stats = []
  const statValues = {
    str: item.str || item.stats?.str,
    sta: item.sta || item.stats?.sta,
    agi: item.agi || item.stats?.agi,
    dex: item.dex || item.stats?.dex,
    wis: item.wis || item.stats?.wis,
    int: item.int || item.stats?.int,
    cha: item.cha || item.stats?.cha
  }
  
  // Get all stats that have values
  Object.entries(statValues).forEach(([stat, value]) => {
    if (value) {
      stats.push({ name: stat.toUpperCase(), value })
    }
  })
  
  // Sort by value and take top 3
  stats.sort((a, b) => b.value - a.value)
  const topStats = stats.slice(0, 3)
  
  // Return as array instead of string for template rendering
  return topStats
}

// Navigation to NPC modal
const openNPCModal = (npcId, npcName) => {
  // Navigate to the NPCs page with the NPC modal opened
  // We'll pass the NPC ID as a query parameter for the NPC modal to open
  router.push({
    name: 'NPCs',
    query: { npc: npcId }
  })
}

// Get route and router for navigation
const route = useRoute()
const router = useRouter()

// Lifecycle
onMounted(() => {
  // Click outside handler for filter dropdown
  document.addEventListener('click', handleClickOutside)
  
  // Check if there's an item query parameter to open automatically
  if (route.query.item) {
    const itemId = parseInt(route.query.item)
    if (!isNaN(itemId)) {
      // Create a mock item object with the ID to open the modal
      selectItem({ item_id: itemId, id: itemId })
    }
  }
})

// Cleanup on unmount
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

// Click outside handler
const handleClickOutside = (event) => {
  const dropdown = document.querySelector('.filter-dropdown')
  const button = document.querySelector('.advanced-filter-button')
  
  if (dropdown && !dropdown.contains(event.target) && !button.contains(event.target)) {
    showFilterDropdown.value = false
  }
}
</script>

<style scoped>
@import '../style-constants.css';

.items-page {
  padding: 20px;
  padding-top: var(--header-height);
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 40px;
  margin-top: 20px;
}

.page-header h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: #666;
  font-size: 1.1rem;
}

.search-section {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.9) 0%, rgba(45, 55, 72, 0.9) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 30px;
  margin-bottom: 30px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  z-index: 1;
}

.search-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.search-input-group {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  flex: 1;
  padding: 15px 20px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: #f7fafc;
  font-size: 1.1rem;
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
  background: rgba(0, 0, 0, 0.4);
}

.search-input::placeholder {
  color: #9ca3af;
}

.search-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 15px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  font-size: 1.1rem;
  font-weight: 600;
  transition: all 0.3s ease;
  min-width: 120px;
  justify-content: center;
}

.search-button i {
  font-size: 1rem;
}

.search-button-text {
  font-weight: 600;
}

.search-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
}

.search-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.filters-container {
  display: flex;
  gap: 20px;
  align-items: end;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-group label {
  color: #f7fafc;
  font-weight: 600;
  font-size: 0.95rem;
}

.filter-select, .filter-input {
  padding: 10px 15px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  color: #f7fafc;
  min-width: 150px;
  transition: all 0.3s ease;
}

.filter-input {
  min-width: 100px;
}

.filter-select:focus, .filter-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

.filter-input::placeholder {
  color: #9ca3af;
}

.clear-filters-button {
  padding: 10px 16px;
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.clear-filters-button:hover {
  background: rgba(239, 68, 68, 0.3);
  border-color: rgba(239, 68, 68, 0.5);
}

/* Advanced Filters */
.advanced-filter-container {
  position: relative;
  z-index: 10000;
}

.advanced-filter-button {
  padding: 10px 16px;
  background: rgba(102, 126, 234, 0.2);
  color: #a78bfa;
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.advanced-filter-button:hover {
  background: rgba(102, 126, 234, 0.3);
  border-color: rgba(102, 126, 234, 0.5);
}

.filter-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  width: 320px;
  max-width: calc(100vw - 40px);
  max-height: 400px;
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.95) 0%, rgba(45, 55, 72, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
  z-index: 999999;
  display: flex;
  flex-direction: column;
}

.filter-search-wrapper {
  position: relative;
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.filter-search-input {
  width: 100%;
  padding: 10px 36px 10px 12px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: #f7fafc;
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

.filter-search-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

.filter-search-icon {
  position: absolute;
  right: 24px;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  pointer-events: none;
}

.filter-fields-list {
  overflow-y: auto;
  max-height: 340px;
}

.filter-field-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.filter-field-item:hover {
  background: rgba(102, 126, 234, 0.2);
}

.filter-field-label {
  color: #f7fafc;
  font-weight: 500;
}

.filter-field-type {
  font-size: 0.85rem;
  color: #9ca3af;
  background: rgba(0, 0, 0, 0.3);
  padding: 2px 8px;
  border-radius: 4px;
}

/* Filter Pills */
.filter-pills-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.filter-pill {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(147, 112, 219, 0.2) 100%);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 20px;
  font-size: 0.9rem;
}

.filter-pill-field {
  color: #a78bfa;
  font-weight: 600;
}

.filter-pill-operator {
  color: #60a5fa;
  font-weight: 500;
  font-size: 0.85rem;
  margin: 0 4px;
  font-style: italic;
}

.filter-pill-value {
  color: #f7fafc;
  font-weight: 500;
}

.filter-pill-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 50%;
  color: #f87171;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-left: 4px;
}

.filter-pill-remove:hover {
  background: rgba(239, 68, 68, 0.3);
  transform: scale(1.1);
}

.filter-pill-remove i {
  font-size: 0.7rem;
}

/* Filter Configuration Modal */
.filter-config-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 450px;
  max-width: calc(100vw - 40px);
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.98) 0%, rgba(45, 55, 72, 0.98) 100%);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  border: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 9999999;
}

.filter-config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.filter-config-header h4 {
  color: #f7fafc;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0;
}

.filter-config-close {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.filter-config-close:hover {
  color: #f7fafc;
  background: rgba(255, 255, 255, 0.1);
}

.filter-config-body {
  padding: 24px;
}

.filter-config-group {
  margin-bottom: 20px;
}

.filter-config-group:last-child {
  margin-bottom: 0;
}

.filter-config-group label {
  display: block;
  color: #e5e7eb;
  font-weight: 500;
  margin-bottom: 8px;
  font-size: 0.95rem;
}

.filter-config-select,
.filter-config-input {
  width: 100%;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: #f7fafc;
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

.filter-config-select:focus,
.filter-config-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

.filter-config-info {
  color: #9ca3af;
  font-size: 0.9rem;
  margin: 0;
}

.filter-config-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.filter-config-cancel,
.filter-config-apply {
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  font-size: 0.95rem;
}

.filter-config-cancel {
  background: rgba(0, 0, 0, 0.3);
  color: #9ca3af;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.filter-config-cancel:hover {
  background: rgba(0, 0, 0, 0.4);
  color: #f7fafc;
}

.filter-config-apply {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.filter-config-apply:hover:not(:disabled) {
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
  transform: translateY(-1px);
}

.filter-config-apply:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.database-status {
  margin-bottom: 30px;
}

.status-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: 12px;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
}

.status-card.error i {
  font-size: 1.5rem;
}

/* Decorative Image Container */
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
  border-radius: 20px;
  width: auto;
  min-width: 300px;
}

.overlay-title {
  font-size: 3rem;
  font-weight: 700;
  margin: 0;
  margin-bottom: 10px;
  background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 50%, #c084fc 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 30px rgba(167, 139, 250, 0.6);
  letter-spacing: 2px;
  filter: drop-shadow(2px 2px 4px rgba(0, 0, 0, 0.8));
}

.overlay-subtitle {
  font-size: 1.1rem;
  color: #e0e7ff;
  margin: 0;
  font-weight: 500;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8),
               0 0 15px rgba(167, 139, 250, 0.4);
  letter-spacing: 1px;
  opacity: 0.95;
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
  margin-bottom: 40px;
  position: relative;
  min-height: 400px;
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.9) 0%, rgba(45, 55, 72, 0.9) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  border: 1px solid rgba(255, 255, 255, 0.1);
}


.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 30px 30px 0;
}

.results-title-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.results-header h2 {
  color: #f7fafc;
  font-size: 1.8rem;
  font-weight: 700;
}

.results-info {
  color: #9ca3af;
  font-size: 0.95rem;
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
}

.view-button i {
  font-size: 0.9rem;
}

.view-button-text {
  font-weight: 500;
}

.view-button:hover {
  color: #f7fafc;
  background: rgba(255, 255, 255, 0.1);
}

.view-button.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
  padding: 0 30px;
}

.item-card {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(217, 70, 239, 0.1) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 44px;
}

.item-card:hover {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(217, 70, 239, 0.15) 100%);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
}

.card-header {
  display: flex;
  gap: 12px;
  align-items: center;
  flex: 1;
}

.card-icon-section {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(217, 70, 239, 0.2) 100%);
  border-radius: 8px;
}

.card-title-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.card-title-section .item-name {
  color: #ffffff;
  font-size: 0.95rem;
  font-weight: 600;
  margin: 0;
  line-height: 1.3;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.card-title-section .item-type {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.8rem;
  font-weight: 500;
}

.item-type {
  background: rgba(102, 126, 234, 0.2);
  color: #a78bfa;
  padding: 4px 8px;
  border-radius: 5px;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid rgba(102, 126, 234, 0.3);
  height: 22px;
  display: inline-flex;
  align-items: center;
  line-height: 1;
}

.card-properties {
  display: flex;
  gap: 6px;
  padding: 12px 20px;
  background: rgba(102, 126, 234, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  flex-wrap: wrap;
}

.card-stats {
  flex: 1;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-group.weapon-stats {
  background: rgba(102, 126, 234, 0.1);
  padding: 12px;
  border-radius: 8px;
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.9rem;
}

.stat-row.ratio {
  border-top: 1px solid rgba(102, 126, 234, 0.2);
  padding-top: 8px;
  margin-top: 4px;
}

.stat-row .stat-label {
  color: #9ca3af;
  font-weight: 500;
}

.stat-row .stat-value {
  color: #4ade80;
  font-weight: 600;
}

.stat-row.ratio .stat-value {
  color: #fbbf24;
  font-weight: 700;
  padding: 2px 6px;
  border: 1px solid #fbbf24;
  border-radius: 4px;
  background: rgba(251, 191, 36, 0.1);
  display: inline-block;
}





.property {
  padding: 4px 8px;
  border-radius: 5px;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid;
  height: 22px;
  display: inline-flex;
  align-items: center;
  line-height: 1;
}

.property.magic {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border-color: rgba(59, 130, 246, 0.3);
}

.property.lore {
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
  border-color: rgba(245, 158, 11, 0.3);
}

.property.nodrop {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
  border-color: rgba(239, 68, 68, 0.3);
}

.property.norent {
  background: rgba(168, 85, 247, 0.2);
  color: #c084fc;
  border-color: rgba(168, 85, 247, 0.3);
}

.property.artifact {
  background: rgba(236, 72, 153, 0.2);
  color: #f472b6;
  border-color: rgba(236, 72, 153, 0.3);
}


.card-footer {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(0, 0, 0, 0.3);
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 0.85rem;
  flex-wrap: wrap;
  margin-top: auto;
}

.footer-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #9ca3af;
}

.footer-item i {
  font-size: 0.8rem;
  opacity: 0.7;
}

.footer-item span {
  color: #e5e7eb;
  font-weight: 500;
}

.footer-item.level span {
  color: #fbbf24;
}

.footer-item.classes {
  margin-left: auto;
}


/* List View Styles */
.items-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0 30px;
}

.item-row {
  display: grid;
  grid-template-columns: 48px 280px 1fr 48px;
  align-items: center;
  gap: 16px;
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.9) 0%, rgba(45, 55, 72, 0.9) 100%);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
  min-height: 90px;
}

.item-row:hover {
  transform: translateX(4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4),
              0 0 0 1px rgba(255, 255, 255, 0.15) inset;
  border-color: rgba(255, 255, 255, 0.2);
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.95) 0%, rgba(45, 55, 72, 0.95) 100%);
}

.item-main-info {
  min-width: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 6px;
}

.item-row .item-name {
  color: #f7fafc;
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

.item-meta {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  flex-wrap: wrap;
}

.item-row .item-type {
  background: rgba(102, 126, 234, 0.2);
  color: #a78bfa;
  padding: 4px 8px;
  border-radius: 5px;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid rgba(102, 126, 234, 0.3);
  height: 22px;
  display: inline-flex;
  align-items: center;
  line-height: 1;
}


.item-center-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
  overflow: hidden;
}

.item-stats-primary {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: nowrap;
  overflow: hidden;
}

.item-info-row {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.85rem;
  color: #9ca3af;
  overflow: hidden;
}

.stat-inline {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  font-size: 0.85rem;
  white-space: nowrap;
}

.stat-inline.weapon-stats {
  background: rgba(102, 126, 234, 0.15);
  border: 1px solid rgba(102, 126, 234, 0.2);
}

.stat-inline.attr {
  background: rgba(34, 197, 94, 0.15);
  border: 1px solid rgba(34, 197, 94, 0.2);
}

.stat-inline.resist {
  background: rgba(234, 179, 8, 0.15);
  border: 1px solid rgba(234, 179, 8, 0.2);
}

.stat-inline .stat-label {
  color: #9ca3af;
  font-weight: 500;
}

.stat-inline .stat-value {
  color: #4ade80;
  font-weight: 600;
}

.stat-inline .stat-value.ratio {
  color: #a78bfa;
}

/* Weapon Ratio Styling */
.weapon-ratio {
  color: #fbbf24;
  font-weight: 700;
  padding: 2px 6px;
  border: 1px solid #fbbf24;
  border-radius: 4px;
  margin-left: 4px;
  background: rgba(251, 191, 36, 0.1);
}

.info-item {
  display: flex;
  gap: 4px;
  white-space: nowrap;
}

.info-label {
  color: #6b7280;
  font-weight: 500;
}

.info-value {
  color: #d1d5db;
  font-weight: 600;
}

.item-classes-row {
  min-width: 200px;
  font-size: 0.9rem;
  color: #e5e7eb;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-action {
  color: #9ca3af;
  font-size: 1.2rem;
  transition: all 0.3s ease;
  width: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.item-row:hover .item-action {
  color: #667eea;
  transform: translateX(4px);
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

.no-results {
  text-align: center;
  padding: 60px 20px;
  color: #9ca3af;
}

.no-results-icon i {
  font-size: 3rem;
  color: #4b5563;
  margin-bottom: 20px;
}

.no-results h3 {
  color: #e5e7eb;
  margin-bottom: 12px;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.95) 0%, rgba(45, 55, 72, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  border: 1px solid rgba(255, 255, 255, 0.1);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
}

.item-modal {
  max-width: 800px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30px 30px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.modal-header h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f7fafc;
  margin: 0;
}

.item-header-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}


.item-type-badge {
  background: rgba(102, 126, 234, 0.2);
  color: #a78bfa;
  padding: 4px 8px;
  border-radius: 5px;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid rgba(102, 126, 234, 0.3);
  height: 22px;
  display: inline-flex;
  align-items: center;
  line-height: 1;
}

.property-badge {
  padding: 4px 8px;
  border-radius: 5px;
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid;
  height: 22px;
  display: inline-flex;
  align-items: center;
  line-height: 1;
}

.property-badge.magic {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border-color: rgba(59, 130, 246, 0.3);
}

.property-badge.lore {
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
  border-color: rgba(245, 158, 11, 0.3);
}

.property-badge.nodrop {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
  border-color: rgba(239, 68, 68, 0.3);
}

.property-badge.norent {
  background: rgba(168, 85, 247, 0.2);
  color: #c084fc;
  border-color: rgba(168, 85, 247, 0.3);
}

.modal-close {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 5px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.modal-close:hover {
  color: #f7fafc;
  background: rgba(255, 255, 255, 0.1);
}

.close-button {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-button:hover {
  color: #f7fafc;
  background: rgba(255, 255, 255, 0.1);
  transform: rotate(90deg);
}

.modal-body {
  padding: 30px;
}

.item-details {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-section h4 {
  color: #f7fafc;
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.stats-grid {
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
}

.detail-item, .stat-detail {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
}

.detail-label, .stat-label {
  color: #9ca3af;
  font-weight: 500;
}

.detail-value, .stat-value {
  color: #f7fafc;
  font-weight: 600;
}

.classes-detail, .races-detail, .slots-detail, .effect-detail, .description-detail {
  color: #e5e7eb;
  line-height: 1.6;
  padding: 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
}

/* Primary Stats Section */
.primary-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.primary-stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.primary-stat-item.weapon {
  grid-column: 1 / -1;
  background: rgba(102, 126, 234, 0.1);
  border-color: rgba(102, 126, 234, 0.2);
}

.stat-icon {
  width: 48px;
  height: 48px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: #a78bfa;
}

.stat-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.primary-stat-item .stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f7fafc;
}

.primary-stat-item .stat-label {
  font-size: 0.9rem;
  color: #9ca3af;
  font-weight: 500;
}

.stat-extra {
  font-size: 0.85rem;
  color: #a78bfa;
  font-weight: 600;
}

/* Attributes Grid */
.attributes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 12px;
}

.attribute-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 8px;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 10px;
}

.attr-label {
  font-size: 0.85rem;
  color: #9ca3af;
  font-weight: 600;
  margin-bottom: 4px;
}

.attr-value {
  font-size: 1.1rem;
  color: #4ade80;
  font-weight: 700;
}

/* Resistances Grid */
.resistances-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 12px;
}

.resist-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid;
}

.resist-item.fire {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.2);
}

.resist-item.cold {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.2);
}

.resist-item.magic {
  background: rgba(168, 85, 247, 0.1);
  border-color: rgba(168, 85, 247, 0.2);
}

.resist-item.disease {
  background: rgba(245, 158, 11, 0.1);
  border-color: rgba(245, 158, 11, 0.2);
}

.resist-item.poison {
  background: rgba(34, 197, 94, 0.1);
  border-color: rgba(34, 197, 94, 0.2);
}

.resist-label {
  font-size: 0.9rem;
  color: #9ca3af;
  font-weight: 500;
}

.resist-value {
  font-size: 1rem;
  color: #f7fafc;
  font-weight: 700;
}

/* Requirements Grid */
.requirements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.requirement-item {
  display: flex;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
}

.req-label {
  color: #9ca3af;
  font-weight: 500;
  min-width: 100px;
}

.req-value {
  color: #f7fafc;
  font-weight: 600;
  flex: 1;
}

/* Effects List */
.effects-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.effect-item {
  display: flex;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(102, 126, 234, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 8px;
}

.effect-type {
  color: #a78bfa;
  font-weight: 600;
  min-width: 60px;
}

.effect-value {
  color: #e5e7eb;
}

/* Lore Section */
.lore-section {
  background: rgba(0, 0, 0, 0.2);
  padding: 20px;
  border-radius: 12px;
}

.lore-text {
  color: #fbbf24;
  font-style: italic;
  line-height: 1.6;
  font-size: 0.95rem;
}

@media (max-width: 768px) {
  .page-header h1 {
    font-size: 2rem;
  }

  .filters-container {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-group {
    min-width: 100%;
  }

  .filter-select {
    min-width: 100%;
  }

  .items-grid {
    grid-template-columns: 1fr;
  }

  .results-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .view-toggle-container {
    align-self: stretch;
    justify-content: center;
  }

  .view-button-text {
    display: inline;
  }

  .item-row {
    grid-template-columns: 48px 1fr;
    height: auto;
    min-height: 90px;
    gap: 12px;
    padding: 16px;
  }
  
  .item-row .item-icon-container {
    grid-row: 1 / 3;
  }
  
  .item-row .item-main-info {
    grid-column: 2;
  }
  
  .item-row .item-center-content {
    grid-column: 1 / -1;
  }

  .item-stats-row {
    gap: 8px;
  }

  .stat-inline {
    padding: 4px 8px;
    font-size: 0.85rem;
  }

  .item-classes-row {
    min-width: unset;
    white-space: normal;
  }

  .item-action {
    display: none;
  }

  .pagination {
    flex-direction: column;
    gap: 12px;
  }

  .modal-content {
    margin: 10px;
    max-width: none;
  }

  .modal-header, .modal-body {
    padding: 20px;
  }

  .detail-grid {
    grid-template-columns: 1fr;
  }

  .filter-dropdown {
    max-height: 60vh;
  }

  .advanced-filter-container {
    position: static;
  }

  .advanced-filter-button {
    width: 100%;
    justify-content: center;
  }
}

/* Item Icon Styles */

/* List View Icons */
.item-icon-container {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.item-icon {
  width: 48px;
  height: 48px;
  object-fit: contain;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}

.item-icon-placeholder {
  width: 48px;
  height: 48px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  font-size: 1.2rem;
}

/* Grid View Icons */
.item-icon-container-grid {
  width: 48px;
  height: 48px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.item-icon-grid {
  width: 32px;
  height: 32px;
  object-fit: contain;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}

.item-icon-placeholder-grid {
  width: 32px;
  height: 32px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  display: none;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  font-size: 1.5rem;
}


/* Modal Icons */
.item-icon-modal-container {
  width: 56px;
  height: 56px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.item-icon-modal {
  width: 56px;
  height: 56px;
  object-fit: contain;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.item-icon-placeholder-modal {
  width: 56px;
  height: 56px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 10px;
  display: none;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  font-size: 1.8rem;
}

/* Ensure placeholders show when images fail */
.item-icon[style*="display: none"] + .item-icon-placeholder,
.item-icon-grid[style*="display: none"] + .item-icon-placeholder-grid,
.item-icon-modal[style*="display: none"] + .item-icon-placeholder-modal {
  display: flex !important;
}

/* Drop Sources Section */
.drop-sources-section {
  margin-top: 20px;
}

.drop-sources-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.drop-sources-header h4 {
  margin: 0;
  color: #f7fafc;
  font-size: 1.1rem;
  font-weight: 600;
}

.drop-sources-button {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 10px 16px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.drop-sources-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.drop-sources-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.drop-sources-results {
  margin-top: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.no-drop-sources {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #9ca3af;
  font-style: italic;
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.no-sources-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}

.retry-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  align-self: flex-start;
}

.retry-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.retry-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.zones-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.zone-section {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
}

.zone-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(102, 126, 234, 0.2);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  color: #f7fafc;
  font-weight: 600;
}

.zone-name {
  flex: 1;
}

.npc-count {
  font-size: 0.85rem;
  color: #cbd5e0;
  font-weight: normal;
}

.npcs-list {
  padding: 8px;
}

.npc-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  margin: 4px 0;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.npc-item.clickable {
  cursor: pointer;
}

.npc-item.clickable:hover {
  background: rgba(102, 126, 234, 0.15);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

.npc-item:not(.clickable):hover {
  background: rgba(255, 255, 255, 0.1);
}

.npc-name {
  color: #e2e8f0;
  font-size: 0.9rem;
}

.drop-chance {
  color: #81c784;
  font-weight: 600;
  font-size: 0.85rem;
  background: rgba(129, 199, 132, 0.2);
  padding: 2px 8px;
  border-radius: 6px;
}

/* Merchant Sources Section */
.merchant-sources-section {
  margin-top: 20px;
}

.merchant-sources-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.merchant-sources-header h4 {
  margin: 0;
  color: #f7fafc;
  font-size: 1.1rem;
  font-weight: 600;
}

.merchant-sources-button {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 10px 16px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
}

.merchant-sources-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(245, 158, 11, 0.4);
}

.merchant-sources-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.merchant-sources-results {
  margin-top: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.no-merchant-sources {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #9ca3af;
  font-style: italic;
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.merchant-count {
  font-size: 0.85rem;
  color: #cbd5e0;
  font-weight: normal;
}

.merchants-list {
  padding: 8px;
}

.merchant-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  margin: 4px 0;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  transition: background 0.2s ease;
}

.merchant-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.merchant-name {
  color: #e2e8f0;
  font-size: 0.9rem;
}

.merchant-pricing {
  color: #fbbf24;
  font-weight: 600;
  font-size: 0.85rem;
  background: rgba(251, 191, 36, 0.2);
  padding: 2px 8px;
  border-radius: 6px;
}

.merchant-type {
  color: #9ca3af;
  font-size: 0.85rem;
  font-style: italic;
}

/* Coin Display Styles */
.coin-display {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.coin {
  display: flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
  font-size: 0.85rem;
}

.coin-icon {
  width: 16px;
  height: 16px;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
}

.coin.platinum {
  color: #e5e7eb;
}

.coin.gold {
  color: #fbbf24;
}

.coin.silver {
  color: #d1d5db;
}

.coin.bronze {
  color: #cd7c2f;
}

.adventure-points {
  color: #8b5cf6;
  font-weight: 600;
  font-size: 0.85rem;
  background: rgba(139, 92, 246, 0.2);
  padding: 2px 8px;
  border-radius: 6px;
}

.free-item {
  color: #10b981;
  font-weight: 600;
  font-size: 0.85rem;
  background: rgba(16, 185, 129, 0.2);
  padding: 2px 8px;
  border-radius: 6px;
}

/* Ground Spawns Section */
.ground-spawns-section {
  margin-top: 20px;
}

.ground-spawns-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.ground-spawns-header h4 {
  margin: 0;
  color: #f7fafc;
  font-size: 1.1rem;
  font-weight: 600;
}

.ground-spawns-button {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #10b981 0%, #047857 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 10px 16px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.ground-spawns-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.ground-spawns-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.ground-spawns-results {
  margin-top: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.no-ground-spawns {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #9ca3af;
  font-style: italic;
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.spawn-count {
  font-size: 0.85rem;
  color: #cbd5e0;
  font-weight: normal;
}

.spawn-points-list {
  padding: 8px;
}

.spawn-point-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  margin: 4px 0;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  transition: background 0.2s ease;
}

.spawn-point-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.spawn-location {
  color: #e2e8f0;
  font-size: 0.9rem;
  font-style: italic;
}

.respawn-timer {
  color: #10b981;
  font-weight: 600;
  font-size: 0.85rem;
  background: rgba(16, 185, 129, 0.2);
  padding: 2px 8px;
  border-radius: 6px;
}

/* Forage Sources Section */
.forage-sources-section {
  margin-top: 20px;
}

.forage-sources-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.forage-sources-header h4 {
  margin: 0;
  color: #f7fafc;
  font-size: 1.1rem;
  font-weight: 600;
}

.forage-sources-button {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #8b5a2b 0%, #654422 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 10px 16px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(139, 90, 43, 0.3);
}

.forage-sources-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(139, 90, 43, 0.4);
}

.forage-sources-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.forage-sources-results {
  margin-top: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.no-forage-sources {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #9ca3af;
  font-style: italic;
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.forage-count {
  font-size: 0.85rem;
  color: #cbd5e0;
  font-weight: normal;
}

.forage-info-list {
  padding: 8px;
}

.forage-info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  margin: 4px 0;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  transition: background 0.2s ease;
}

.forage-info-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.forage-chance {
  color: #8b5a2b;
  font-weight: 600;
  font-size: 0.9rem;
}

.forage-level {
  color: #94a3b8;
  font-weight: 500;
  font-size: 0.85rem;
  background: rgba(148, 163, 184, 0.2);
  padding: 2px 8px;
  border-radius: 6px;
}

/* Tradeskill Recipes Section */
.tradeskill-recipes-section {
  margin-top: 20px;
}

.tradeskill-recipes-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.tradeskill-recipes-header h4 {
  margin: 0;
  color: #f7fafc;
  font-size: 1.1rem;
  font-weight: 600;
}

.tradeskill-recipes-button {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 10px 16px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
}

.tradeskill-recipes-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4);
}

.tradeskill-recipes-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.tradeskill-recipes-results {
  margin-top: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.no-tradeskill-recipes {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #9ca3af;
  font-style: italic;
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.skills-list {
  padding: 0;
}

.skill-section {
  margin-bottom: 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.skill-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(124, 58, 237, 0.1);
  border-radius: 8px 8px 0 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.skill-name {
  color: #c4b5fd;
  font-weight: 600;
  font-size: 1rem;
}

.recipe-count {
  font-size: 0.85rem;
  color: #cbd5e0;
  font-weight: normal;
}

.recipes-list {
  padding: 8px;
}

.recipe-list-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(217, 70, 239, 0.1) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  transition: all 0.3s ease;
  margin: 4px 0;
  cursor: pointer;
  min-height: 44px;
}

.recipe-list-item:hover {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(217, 70, 239, 0.15) 100%);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
}

.recipe-list-item .recipe-name {
  color: #ffffff;
  font-size: 0.95rem;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.recipe-list-item .recipe-name.clickable {
  cursor: pointer;
  transition: color 0.2s ease;
}

.recipe-list-item .recipe-name.clickable:hover {
  color: #c4b5fd;
  text-decoration: underline;
}

.component-count {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(217, 70, 239, 0.3) 100%);
  color: #ffffff;
  font-weight: 700;
  font-size: 0.75rem;
  padding: 2px 6px;
  border-radius: 4px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* Recipe Modal Styles */
.recipe-modal {
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
}

.recipe-details {
  padding: 0;
}

.recipe-header {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.recipe-header h4 {
  color: #f7fafc;
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 12px 0;
}

.recipe-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.tradeskill-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 4px 12px;
  border-radius: 6px;
  font-size: 0.85rem;
  font-weight: 600;
}

.trivial-level {
  color: #9ca3af;
  font-size: 0.9rem;
}

.recipe-section {
  margin-bottom: 30px;
}

.recipe-section h5 {
  color: #f7fafc;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 16px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.recipe-section h5 i {
  color: #a78bfa;
}

.creates-section h5 i {
  color: #34d399;
}

.requires-section h5 i {
  color: #fbbf24;
}

.containers-section h5 i {
  color: #60a5fa;
}

.recipe-section .items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

.recipe-section .recipe-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(217, 70, 239, 0.1) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  transition: all 0.3s ease;
  min-height: 44px;
}

.recipe-section .recipe-item.clickable {
  cursor: pointer;
}

.recipe-section .recipe-item.clickable:hover {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(217, 70, 239, 0.15) 100%);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
}

.recipe-item-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(217, 70, 239, 0.2) 100%);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.recipe-item-icon .item-icon-img {
  width: 32px;
  height: 32px;
  object-fit: contain;
  image-rendering: pixelated;
  image-rendering: -moz-crisp-edges;
  image-rendering: crisp-edges;
}

.recipe-item-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.recipe-section .item-name {
  color: #ffffff;
  font-size: 0.95rem;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.recipe-item-badges {
  display: flex;
  gap: 6px;
  align-items: center;
}

.recipe-section .item-count {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(217, 70, 239, 0.3) 100%);
  color: #ffffff;
  font-weight: 700;
  font-size: 0.75rem;
  padding: 2px 6px;
  border-radius: 4px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* Undiscovered item styles */
.recipe-section .recipe-item.undiscovered {
  opacity: 0.6;
  border-color: rgba(255, 255, 255, 0.05);
  cursor: not-allowed;
}

.recipe-section .recipe-item.undiscovered .item-name {
  color: #9ca3af;
}

.recipe-section .recipe-item.undiscovered:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.05);
  transform: none;
}

.undiscovered-badge {
  color: #ef4444;
  font-weight: 600;
  font-size: 0.8rem;
  background: rgba(239, 68, 68, 0.2);
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.recipe-notes {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 16px;
  color: #cbd5e0;
  font-size: 0.9rem;
  line-height: 1.5;
}

/* Loading container for recipe modal */
.loading-container {
  position: relative;
  min-height: 200px;
}

/* Created by Recipes Section Styles */
.created-by-recipes-section {
  margin-top: 20px;
}

.created-by-recipes-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.created-by-recipes-button {
  background: linear-gradient(135deg, #7c3aed, #a855f7);
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
  display: flex;
  align-items: center;
  gap: 8px;
}

.created-by-recipes-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4);
}

.created-by-recipes-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.created-by-recipes-results {
  margin-top: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.no-created-by-recipes {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #9ca3af;
  font-style: italic;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border: 1px dashed rgba(255, 255, 255, 0.2);
}

.creation-recipes-list {
  padding: 0;
}

.creation-recipe-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(217, 70, 239, 0.1) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  transition: all 0.3s ease;
  padding: 12px;
  cursor: pointer;
  min-height: 44px;
}

.creation-recipe-item:hover {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(217, 70, 239, 0.15) 100%);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
}

.creation-recipe-item .recipe-name {
  color: #ffffff;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.2s ease;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.creation-recipe-item .recipe-name:hover {
  color: #c4b5fd;
  text-decoration: underline;
}

.creation-recipe-item .tradeskill-badge {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3) 0%, rgba(217, 70, 239, 0.3) 100%);
  color: #ffffff;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.creation-recipe-item .trivial-level {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.8rem;
  font-weight: 500;
}
</style>