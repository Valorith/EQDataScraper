<template>
  <div class="npcs-page">
    <div class="page-header">
      <h1>NPC Database</h1>
      <p class="subtitle">Search and explore NPCs from the database</p>
    </div>

    <!-- Search Section -->
    <div class="search-section">
      <div class="search-container">
        <div class="search-input-group">
          <input
            v-model="searchQuery"
            @keyup.enter="performSearch()"
            type="text"
            placeholder="Search NPCs by name..."
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
          
          <div class="filter-group">
            <label for="zone-filter">Zone:</label>
            <select id="zone-filter" v-model="selectedZone" class="filter-select">
              <option value="">All Zones</option>
              <!-- Zone options will be populated dynamically -->
            </select>
          </div>
          
          <button @click="clearFilters" class="clear-filters-button">
            <i class="fas fa-times"></i>
            Clear Filters
          </button>
        </div>
      </div>
    </div>

    <!-- Loading Modal for Search -->
    <LoadingModal 
      :visible="searching" 
      text="Searching NPCs..." 
    />

    <!-- Loading Modal for Pagination -->
    <LoadingModal 
      :visible="paginating" 
      text="Loading more results..." 
    />

    <!-- Results Section -->
    <div v-if="searchPerformed" class="results-section">
      <div class="results-header">
        <div class="results-info-container">
          <h2>Search Results</h2>
          <div class="results-info">
            <span>{{ totalCount.toLocaleString() }} NPC{{ totalCount !== 1 ? 's' : '' }} found</span>
            <span v-if="searchQuery">(searching for "{{ searchQuery }}")</span>
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
      <div v-if="searchPerformed && totalPages > 1 && !searching && searchResults.length > 0" class="pagination pagination-top">
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

      <!-- Results Display -->
      <div v-if="searchResults.length > 0" :class="['npc-results', viewMode]">
        <!-- List View -->
        <div v-if="viewMode === 'list'" class="npc-list">
          <div 
            v-for="npc in searchResults" 
            :key="npc.id"
            @click="openNPCModal(npc)"
            class="npc-row"
          >
            <div class="npc-main-info">
              <div class="npc-name-and-details">
                <h3 class="npc-name">{{ cleanNPCName(npc.name) }}</h3>
                <div class="npc-details">
                  <span class="npc-level">Level {{ npc.level }}</span>
                  <span class="npc-separator">•</span>
                  <span class="npc-race">{{ getRaceName(npc.race) }}</span>
                  <span class="npc-separator">•</span>
                  <div class="npc-class-with-icon">
                    <img 
                      v-if="getClassIcon(npc.class)" 
                      :src="getClassIcon(npc.class)" 
                      :alt="getClassName(npc.class)"
                      class="npc-class-icon"
                      @error="handleIconError"
                    />
                    <span class="npc-class">{{ getClassName(npc.class) }}</span>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="npc.zone_short_name" class="npc-zone-display">
              <span class="zone-name">{{ getFormattedZoneName(npc) }}</span>
            </div>
          </div>
        </div>

        <!-- Grid View -->
        <div v-if="viewMode === 'grid'" class="npc-grid">
          <div 
            v-for="npc in searchResults" 
            :key="npc.id"
            @click="openNPCModal(npc)"
            class="npc-card"
          >
            <div class="npc-card-content">
              <div class="npc-card-main">
                <h3 class="npc-card-name">{{ cleanNPCName(npc.name) }}</h3>
                <div class="npc-card-details">
                  <span class="npc-card-level">Level {{ npc.level }}</span>
                  <span class="npc-card-separator">•</span>
                  <span class="npc-card-race">{{ getRaceName(npc.race) }}</span>
                  <span class="npc-card-separator">•</span>
                  <div class="npc-card-class-with-icon">
                    <img 
                      v-if="getClassIcon(npc.class)" 
                      :src="getClassIcon(npc.class)" 
                      :alt="getClassName(npc.class)"
                      class="npc-card-class-icon"
                      @error="handleIconError"
                    />
                    <span class="npc-card-class">{{ getClassName(npc.class) }}</span>
                  </div>
                </div>
              </div>
              <div v-if="npc.zone_short_name" class="npc-card-zone-display">
                <span class="npc-card-zone-name">{{ getFormattedZoneName(npc) }}</span>
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

      <!-- No Results -->
      <div v-else class="no-results">
        <div class="no-results-content">
          <i class="fas fa-search"></i>
          <h3>No NPCs Found</h3>
          <p>Try adjusting your search criteria or filters.</p>
        </div>
      </div>
    </div>

    <!-- NPC Details Loading Modal -->
    <LoadingModal 
      :visible="loadingNPCDetails" 
      text="Loading NPC details..." 
      :full-screen="true" 
    />

    <!-- NPC Details Modal -->
    <div v-if="selectedNPCDetail && !loadingNPCDetails" class="modal-overlay" @click="closeNPCModal">
      <div class="modal-content npc-modal" @click.stop>
        <div class="modal-header">
          <div class="npc-header-main">
            <div class="npc-title-section">
              <div class="npc-icon-container">
                <img 
                  v-if="getClassIcon(selectedNPCDetail.class)" 
                  :src="getClassIcon(selectedNPCDetail.class)" 
                  :alt="getClassName(selectedNPCDetail.class)"
                  class="npc-modal-class-icon"
                  @error="handleIconError"
                />
                <i v-else class="fas fa-user-circle npc-modal-class-fallback"></i>
              </div>
              <div class="npc-title-info">
                <h2 class="npc-modal-title">{{ cleanNPCName(selectedNPCDetail.name) }}</h2>
                <div class="npc-subtitle">{{ getRaceName(selectedNPCDetail.race) }} {{ getClassName(selectedNPCDetail.class) }}</div>
              </div>
            </div>
            <div class="npc-header-badges">
              <div class="badge-group">
                <div class="level-and-combat-row">
                  <span class="level-badge">
                    <i class="fas fa-star"></i> Level {{ selectedNPCDetail.level }}
                  </span>
                  <span class="health-badge">
                    <i class="fas fa-heart"></i> {{ selectedNPCDetail.hp?.toLocaleString() }} HP
                  </span>
                  <span v-if="selectedNPCDetail.mana" class="mana-badge">
                    <i class="fas fa-magic"></i> {{ selectedNPCDetail.mana?.toLocaleString() }} MP
                  </span>
                  <span v-if="selectedNPCDetail.mindmg || selectedNPCDetail.maxdmg" class="damage-badge">
                    <i class="fas fa-sword"></i> {{ selectedNPCDetail.mindmg }}-{{ selectedNPCDetail.maxdmg }} DMG
                  </span>
                </div>
              </div>
            </div>
          </div>
          <button @click="closeNPCModal" class="modal-close">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="modal-body">
          <!-- Enhanced Stats Grid -->
          <div class="stats-overview">
            <div class="stat-card">
              <div class="stat-icon">
                <i class="fas fa-info-circle"></i>
              </div>
              <div class="stat-content">
                <h4>Basic Information</h4>
                <div class="stat-details">
                  <div class="stat-row">
                    <span class="stat-label">Full Name</span>
                    <span class="stat-value">{{ cleanNPCName(selectedNPCDetail.name) }}</span>
                  </div>
                  <div v-if="selectedNPCDetail.lastname" class="stat-row">
                    <span class="stat-label">Last Name</span>
                    <span class="stat-value">{{ selectedNPCDetail.lastname }}</span>
                  </div>
                  <div class="stat-row">
                    <span class="stat-label">Race</span>
                    <span class="stat-value">{{ getRaceName(selectedNPCDetail.race) }}</span>
                  </div>
                  <div class="stat-row">
                    <span class="stat-label">Class</span>
                    <span class="stat-value">{{ getClassName(selectedNPCDetail.class) }}</span>
                  </div>
                  <div v-if="selectedNPCDetail.npc_faction_id" class="stat-row">
                    <span class="stat-label">Main Faction</span>
                    <span class="stat-value">{{ getFactionName(selectedNPCDetail.npc_faction_id) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div v-if="selectedNPCDetail.special_attacks && selectedNPCDetail.special_attacks.length > 0" class="stat-card">
              <div class="stat-icon">
                <i class="fas fa-bolt"></i>
              </div>
              <div class="stat-content">
                <h4>Special Attacks</h4>
                <div class="special-attacks-list">
                  <div v-for="attack in selectedNPCDetail.special_attacks" :key="attack" class="special-attack-item">
                    <i class="fas fa-angle-right special-attack-icon"></i>
                    <span class="special-attack-name">{{ attack }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Spawn Locations -->
          <div v-if="uniqueSpawnZones.length > 0" class="content-section">
            <div class="section-header">
              <i class="fas fa-map-marker-alt section-icon"></i>
              <h3>This NPC spawns in</h3>
            </div>
            <div class="zone-list">
              <div v-for="zone in uniqueSpawnZones" :key="zone" class="zone-item">
                <i class="fas fa-globe zone-icon"></i>
                <span class="zone-name">{{ zone }}</span>
              </div>
            </div>
          </div>

          <!-- NPC Spells -->
          <div v-if="selectedNPCDetail.spells && selectedNPCDetail.spells.length > 0" class="content-section">
            <div class="section-header">
              <i class="fas fa-magic section-icon"></i>
              <h3>Spells cast by this NPC</h3>
            </div>
            <div class="npc-spells-grid">
              <div 
                v-for="spell in selectedNPCDetail.spells" 
                :key="spell.spell_id" 
                @click="openSpellModal(spell.spell_id, spell.spell_name)"
                class="npc-spell-card"
              >
                <div class="npc-spell-icon-container">
                  <img 
                    v-if="spell.icon && spell.icon !== 0" 
                    :src="`/icons/items/${spell.icon}.png`" 
                    :alt="spell.spell_name"
                    @error="handleIconError"
                    class="npc-spell-icon"
                  />
                  <i v-else class="fas fa-magic npc-spell-icon-placeholder"></i>
                </div>
                <div class="npc-spell-info">
                  <span class="npc-spell-name">{{ spell.spell_name }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Merchant Items -->
          <div v-if="selectedNPCDetail.merchant_items && selectedNPCDetail.merchant_items.length > 0" class="detail-section">
            <h4>Items sold by this merchant</h4>
            <div class="merchant-items">
              <div v-for="item in selectedNPCDetail.merchant_items" :key="item.item_id" class="merchant-item">
                <div class="merchant-item-info">
                  <img 
                    v-if="item.icon" 
                    :src="`/icons/items/${item.icon}.png`" 
                    :alt="item.item_name"
                    @error="handleIconError"
                    class="merchant-item-icon"
                  />
                  <i v-else class="fas fa-cube merchant-item-icon-placeholder"></i>
                  <div class="merchant-details">
                    <span class="merchant-item-name">{{ item.item_name }}</span>
                    <span v-if="item.price" class="merchant-price">{{ item.price?.toLocaleString() }} copper</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Loot Drops (if any) -->
          <div v-if="selectedNPCDetail.loot_drops && selectedNPCDetail.loot_drops.length > 0" class="content-section">
            <div class="section-header">
              <div class="section-header-left">
                <i class="fas fa-treasure-chest section-icon"></i>
                <h3>When killed, this NPC drops</h3>
              </div>
              <button 
                @click="toggleAllLootDrops" 
                class="toggle-all-button"
                :title="allLootDropsExpanded ? 'Collapse all loot drops' : 'Expand all loot drops'"
              >
                <i :class="['fas', allLootDropsExpanded ? 'fa-compress-alt' : 'fa-expand-alt']"></i>
                <span>{{ allLootDropsExpanded ? 'Hide All' : 'Show All' }}</span>
              </button>
            </div>
            <div class="loot-tables">
              <div v-for="lootTable in selectedNPCDetail.loot_drops" :key="lootTable.loot_drop_id" class="loot-table">
                <div 
                  class="loot-table-header clickable" 
                  @click="toggleLootDrop(lootTable.loot_drop_id)"
                >
                  <div class="loot-table-info">
                    <div class="loot-table-primary">
                      <span class="loot-table-label">With a probability of {{ lootTable.table_probability }}%</span>
                      <span class="item-count-badge">{{ lootTable.items.length }} {{ lootTable.items.length === 1 ? 'item' : 'items' }}</span>
                      <i :class="['fas', 'expansion-icon', isLootDropExpanded(lootTable.loot_drop_id) ? 'fa-chevron-down' : 'fa-chevron-right']"></i>
                    </div>
                    <div class="loot-table-mechanics">
                      <span v-if="lootTable.multiplier > 1" class="multiplier-info">({{ lootTable.multiplier }} {{ lootTable.multiplier === 1 ? 'roll' : 'rolls' }})</span>
                      <span v-else class="multiplier-info">(1 roll)</span>
                      <span v-if="lootTable.droplimit > 0" class="droplimit-info">• Max {{ lootTable.droplimit }} {{ lootTable.droplimit === 1 ? 'item' : 'items' }}</span>
                      <span v-else class="droplimit-info">• No limit</span>
                      <span v-if="lootTable.mindrop > 0" class="mindrop-info">• Min {{ lootTable.mindrop }} guaranteed</span>
                    </div>
                  </div>
                </div>
                <div 
                  v-if="isLootDropExpanded(lootTable.loot_drop_id)" 
                  class="loot-items"
                >
                  <div 
                    v-for="item in lootTable.items" 
                    :key="item.item_id" 
                    @click="openItemModal(item.item_id)"
                    class="loot-item clickable"
                  >
                    <div class="loot-item-icon-container">
                      <img 
                        v-if="item.icon" 
                        :src="`/icons/items/${item.icon}.png`" 
                        :alt="item.item_name"
                        @error="handleIconError"
                        class="loot-item-icon"
                      />
                      <i v-else class="fas fa-cube loot-item-icon-placeholder"></i>
                    </div>
                    <div class="loot-item-info">
                      <div class="loot-item-name">{{ item.item_name }}</div>
                      <div class="loot-item-chances">
                        <span class="individual-chance">{{ item.item_chance }}%</span>
                        <span class="chance-separator">•</span>
                        <span class="overall-chance" :class="{'rare-drop': item.overall_probability < 5, 'common-drop': item.overall_probability >= 20}">
                          {{ item.overall_probability }}% Overall
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Toast Notifications -->
    <div class="toast-container">
      <div v-for="toast in toasts" :key="toast.id" class="toast" :class="toast.type">
        <i :class="getToastIcon(toast.type)"></i>
        <div class="toast-content">
          <div class="toast-title">{{ toast.title }}</div>
          <div v-if="toast.message" class="toast-message">{{ toast.message }}</div>
        </div>
        <button @click="removeToast(toast.id)" class="toast-close">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import LoadingModal from '../components/LoadingModal.vue'

// API configuration
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 
  (import.meta.env.PROD ? 'https://eqdatascraper-backend-production.up.railway.app' : '')

export default {
  name: 'NPCs',
  components: {
    LoadingModal
  },
  
  data() {
    return {
      // Search state
      searchQuery: '',
      searching: false,
      searchPerformed: false,
      searchResults: [],
      totalCount: 0,
      
      // View mode
      viewMode: 'list', // Default to list view like Items and Spells
      
      // Pagination
      currentPage: 1,
      limit: 20,
      paginating: false,
      
      // Filters
      minLevel: '',
      maxLevel: '',
      selectedZone: '',
      
      // NPC details modal
      selectedNPCDetail: null,
      loadingNPCDetails: false,
      
      // Loot drop expansion state
      expandedLootDrops: new Set(),
      
      // Toast notifications
      toasts: [],
      
      // Accurate EverQuest race mappings from EQEmu documentation
      raceNames: {
        1: 'Human', 2: 'Barbarian', 3: 'Erudite', 4: 'Wood Elf', 5: 'High Elf', 6: 'Dark Elf',
        7: 'Half Elf', 8: 'Dwarf', 9: 'Troll', 10: 'Ogre', 11: 'Halfling', 12: 'Gnome',
        13: 'Aviak', 14: 'Werewolf', 15: 'Brownie', 16: 'Centaur', 17: 'Golem', 18: 'Giant',
        19: 'Trakanon', 20: 'Venril Sathir', 21: 'Evil Eye', 22: 'Beetle', 23: 'Kerran',
        24: 'Fish', 25: 'Fairy', 26: 'Froglok', 27: 'Froglok', 28: 'Fungusman', 29: 'Gargoyle',
        30: 'Gasbag', 31: 'Gelatinous Cube', 32: 'Ghost', 33: 'Ghoul', 34: 'Bat',
        35: 'Eel', 36: 'Rat', 37: 'Snake', 38: 'Spider', 39: 'Gnoll', 40: 'Goblin',
        41: 'Gorilla', 42: 'Wolf', 43: 'Bear', 44: 'Guard', 45: 'Demi Lich', 46: 'Imp',
        47: 'Griffin', 48: 'Kobold', 49: 'Dragon', 50: 'Lion',
        51: 'Lion', 52: 'Lizard Man', 53: 'Mimic', 54: 'Minotaur', 55: 'Orc',
        56: 'Beggar', 57: 'Pixie', 58: 'Drachnid', 59: 'Solusek Ro', 60: 'Goblin',
        61: 'Skeleton', 62: 'Shark', 63: 'Tunare', 64: 'Tiger', 65: 'Treant',
        66: 'Vampire', 67: 'Rallos Zek', 68: 'Human', 69: 'Tentacle Terror', 70: 'Will-O-Wisp',
        71: 'Zombie', 72: 'Human', 73: 'Ship', 74: 'Launch', 75: 'Piranha',
        76: 'Elemental', 77: 'Puma', 78: 'Dark Elf', 79: 'Erudite', 80: 'Bixie',
        81: 'Reanimated Hand', 82: 'Halfling', 83: 'Scarecrow', 84: 'Skunk', 85: 'Snake Elemental',
        86: 'Spectre', 87: 'Sphinx', 88: 'Armadillo', 89: 'Clockwork Gnome', 90: 'Drake',
        91: 'Barbarian', 92: 'Alligator', 93: 'Troll', 94: 'Ogre', 95: 'Dwarf',
        96: 'Cazic Thule', 97: 'Cockatrice', 98: 'Daisy Man', 99: 'Vampire', 100: 'Dervish',
        101: 'Efreeti', 102: 'Tadpole', 103: 'Kedge', 104: 'Leech', 105: 'Swordfish',
        106: 'Guard', 107: 'Mammoth', 108: 'Eye', 109: 'Wasp', 110: 'Mermaid',
        111: 'Harpy', 112: 'Guard', 113: 'Drixie', 114: 'Ghost Ship', 115: 'Clam',
        116: 'Seahorse', 117: 'Ghost', 118: 'Ghost', 119: 'Sabertooth', 120: 'Wolf',
        121: 'Boat', 122: 'Minor Illusion', 123: 'Tree', 124: 'Burynai', 125: 'Goo',
        126: 'Spectral Sarnak', 127: 'Spectral Iksar', 128: 'Kunark Fish', 129: 'Iksar Scorpion',
        130: 'Erollisi', 131: 'Tribunal', 132: 'Bertoxxulous', 133: 'Bristlebane',
        134: 'Fay Drake', 135: 'Undead Sarnak', 136: 'Ratman', 137: 'Wyvern',
        138: 'Necromancer', 139: 'Shadowman', 140: 'Khati Sha', 141: 'Skeletal Horse',
        142: 'Chimera', 143: 'Kly', 144: 'Sludge', 145: 'Combination', 146: 'Bixie',
        147: 'Centaur', 148: 'Drakkin', 149: 'Giant', 150: 'Werewolf', 151: 'Barbarian',
        152: 'Vah Shir', 153: 'Alaran', 154: 'Sarnak', 155: 'Vampire', 156: 'Ayonae Ro',
        157: 'Sullon Zek', 158: 'Banner', 159: 'Flag', 160: 'Rowboat', 161: 'Bear Trap',
        162: 'Clockwork Rat', 163: 'Clockwork Spider', 164: 'Clockwork Gnome',
        165: 'Wisp', 166: 'Ground Spawn', 167: 'Weaponrack', 168: 'Coffin', 169: 'Bones',
        170: 'Jokester', 171: 'Nihil', 172: 'Troll', 173: 'Sarnak Spirit',
        174: 'Iksar Spirit', 175: 'Fish', 176: 'Scorpion', 177: 'Erollisi Marr',
        178: 'Tunare', 179: 'Bertoxxulous', 180: 'Tribunal', 181: 'Bristlebane',
        182: 'Undead Froglok', 183: 'Knight of Pestilence', 184: 'Leech',
        185: 'Swordfish', 186: 'Felguard', 187: 'Mammoth', 188: 'Eye', 189: 'Wasp',
        190: 'Mermaid', 191: 'Harpie', 192: 'Fayguard', 193: 'Drixie', 194: 'Ghost Ship',
        195: 'Clam', 196: 'Seahorse', 197: 'Dwarf Ghost', 198: 'Erudite Ghost',
        199: 'Sabertooth Cat Spirit', 200: 'Wolf Elemental', 201: 'Gorgon',
        202: 'Dragon Skeleton', 203: 'Innoruuk', 204: 'Unicorn', 205: 'Pegasus',
        206: 'Djinn', 207: 'Invisible Man', 208: 'Iksar', 209: 'Scorpion',
        210: 'Vah Shir', 211: 'Sarnak', 212: 'Draglock', 213: 'Drolvarg', 214: 'Mosquito',
        215: 'Rhinoceros', 216: 'Xalgoz', 217: 'Kunark Goblin', 218: 'Yak Man',
        219: 'Faun', 220: 'Coldain', 221: 'Velious Dragon', 222: 'Hag', 223: 'Hippogriff',
        224: 'Siren', 225: 'Frost Giant', 226: 'Storm Giant', 227: 'Ottermen',
        228: 'Walrus', 229: 'Geonid', 230: 'Yakman', 231: 'Scythe Cat', 232: 'Shadel',
        233: 'Shik Nar', 234: 'Rockhopper', 235: 'Underbulk', 236: 'Grimling',
        237: 'Wyvern', 238: 'Wurm', 239: 'Devourer', 240: 'Iksar Citizen',
        241: 'Forest Giant', 242: 'Boat', 243: 'Minor Illusion', 244: 'Tree',
        245: 'Burynai', 246: 'Goo', 247: 'Spectral Sarnak', 248: 'Spectral Iksar',
        249: 'Kunark Fish', 250: 'Iksar Scorpion', 330: 'Froglok', 331: 'Troll', 332: 'Troll',
        333: 'Troll', 334: 'Ghost', 335: 'Pirate', 336: 'Pirate', 337: 'Pirate',
        338: 'Pirate', 339: 'Pirate', 340: 'Pirate', 367: 'Selyrah',
        421: 'Powder Pet', 446: 'Bixie', 460: 'Corathus', 461: 'Coral', 462: 'Drachnid', 463: 'Drachnid Cocoon',
        464: 'Fungus Patch', 465: 'Gargoyle', 466: 'Witheran', 467: 'Dark Lord', 468: 'Snake',
        469: 'Evil Eye', 470: 'Minotaur', 471: 'Zombie', 472: 'Clockwork Boar', 473: 'Fairy',
        474: 'Witheran', 475: 'Air Elemental', 476: 'Earth Elemental', 477: 'Fire Elemental',
        478: 'Water Elemental', 479: 'Alligator', 480: 'Alligator', 481: 'Bear', 482: 'Scaled Wolf',
        483: 'Wolf', 484: 'Spirit Wolf', 485: 'Skeleton', 486: 'Spectre', 487: 'Bolvirk',
        488: 'Banshee', 489: 'Banshee', 490: 'Elddar', 491: 'Forest Giant', 492: 'Bone Golem',
        493: 'Horse', 494: 'Pegasus', 495: 'Shambling Mound', 496: 'Scrykin', 497: 'Treant',
        498: 'Vampire', 499: 'Ayonae Ro', 500: 'Sullon Zek', 501: 'Banner', 502: 'Flag',
        503: 'Rowboat', 504: 'Bear Trap', 505: 'Clockwork Bomb', 506: 'Dynamite Keg',
        507: 'Pressure Plate', 508: 'Puffer Spore', 509: 'Stone Ring', 510: 'Root Tentacle',
        511: 'Runic Symbol', 512: 'Saltpetter Bomb', 513: 'Floating Skull', 514: 'Spike Trap',
        515: 'Totem', 516: 'Web', 517: 'Wicker Basket', 518: 'Nightmare/Unicorn', 519: 'Horse',
        520: 'Bixie', 521: 'Centaur', 522: 'Drakkin', 523: 'Giant', 524: 'Gnoll',
        525: 'Griffin', 526: 'Giant Shade', 527: 'Harpy', 528: 'Mammoth', 529: 'Satyr',
        530: 'Dragon', 531: 'Dragon', 532: 'Dyn\'Leth', 533: 'Boat', 534: 'Weapon Rack',
        535: 'Armor Rack', 536: 'Honey Pot', 537: 'Jum Jum Bucket', 538: 'Toolbox',
        539: 'Stone Jug', 540: 'Small Plant', 567: 'Campfire', 568: 'Brownie', 569: 'Dragon',
        570: 'Exoskeleton', 571: 'Ghoul', 572: 'Clockwork Guardian', 573: 'Mantrap',
        574: 'Minotaur', 575: 'Scarecrow', 576: 'Shade', 577: 'Rotocopter',
        578: 'Tentacle Terror', 579: 'Wereorc', 580: 'Worg', 581: 'Wyvern',
        582: 'Prismatic Dragon', 583: 'Shiknar', 584: 'Rockhopper', 585: 'Underbulk',
        586: 'Grimling', 587: 'Vacuum Cleaner', 588: 'Evan Test', 589: 'Kahli Shah',
        590: 'Owlbear', 591: 'Rhino Beetle', 592: 'Vampyre', 593: 'Earth Elemental',
        594: 'Air Elemental', 595: 'Water Elemental', 596: 'Fire Elemental',
        597: 'Wetfang Minnow', 598: 'Thought Horror', 599: 'Tegi', 600: 'Horse',
        601: 'Pegasus', 602: 'Nightmare', 603: 'Unicorn', 604: 'Selyrah Mount',
        605: 'Drakkin Mount', 606: 'Giant', 607: 'Chimera', 608: 'Kirin',
        609: 'Puma', 610: 'Boulder', 611: 'Banner', 612: 'Elven Boat',
        613: 'Gingerbread Man', 614: 'Gnomework', 615: 'Burynai',
        616: 'Amygdalan', 617: 'Dervish Cutthroat', 618: 'Sphinx',
        619: 'Tentacle Terror', 620: 'Wereorc', 621: 'Kobold', 622: 'Worg',
        623: 'Rhino', 624: 'Raven', 625: 'Prismatic Dragon', 626: 'Diaku Corsair',
        629: 'Phurzikon', 630: 'Dervish', 638: 'Banshee', 652: 'Ship', 653: 'Launch',
        654: 'Prefab Ship', 657: 'Warship', 658: 'Invisible Man', 660: 'Air Elemental',
        661: 'Earth Elemental', 662: 'Fire Elemental', 663: 'Water Elemental',
        664: 'Alaran Sentry Stone', 665: 'Alaran Portal', 666: 'Cliknar Sentinel',
        667: 'Cliknar Drone', 668: 'Cliknar Centurion', 669: 'Cliknar Assassin',
        670: 'Cliknar Adept', 671: 'Cliknar Discordling', 672: 'Banshee', 673: 'Dervish',
        674: 'Worg', 675: 'Catman', 676: 'Cactus', 677: 'Witheran', 678: 'Dark Elf',
        680: 'Fairy', 681: 'Witheran', 682: 'Air Mephit', 683: 'Earth Mephit',
        684: 'Fire Mephit', 685: 'Water Mephit', 686: 'Dream Mephit', 687: 'Nightmare Mephit',
        688: 'Zebuxoruk', 689: 'Muramite Armor', 690: 'Muramite Weapon', 691: 'Apexus',
        692: 'Aneuk', 693: 'Ukun', 694: 'Ixt', 695: 'Kyv', 696: 'Noc', 697: 'Ra`tuk',
        698: 'Taneth', 699: 'Huvul', 700: 'Mutant Humanoid', 701: 'Mastruq', 702: 'Taelosian',
        703: 'Discord Ship', 704: 'Stone Worker', 705: 'Hynid', 706: 'Turepta', 707: 'Alaran',
        708: 'Sarnak', 709: 'Dragorn', 710: 'Murkglider', 711: 'Rat', 712: 'Bat',
        713: 'Gelidran', 714: 'Discordling', 715: 'Girplan', 716: 'Minotaur',
        717: 'Dragorn Box', 718: 'Runed Orb', 719: 'Dragon Bones', 720: 'Muramite Armor',
        721: 'Crystal Spider', 722: 'Zek', 723: 'Luggald', 724: 'Luggald', 725: 'Trite',
        726: 'Yareth', 727: 'Netherbian', 728: 'Akhevan', 729: 'Spire Spirit',
        730: 'Sonic Wolf', 731: 'Ground Shaker', 732: 'Vah Shir Skeleton'
      },
      
      classNames: {
        1: 'Warrior', 2: 'Cleric', 3: 'Paladin', 4: 'Ranger', 5: 'Shadow Knight', 6: 'Druid',
        7: 'Monk', 8: 'Bard', 9: 'Rogue', 10: 'Shaman', 11: 'Necromancer', 12: 'Wizard',
        13: 'Magician', 14: 'Enchanter', 15: 'Beastlord', 16: 'Berserker'
      }
    }
  },
  
  computed: {
    totalPages() {
      return Math.ceil(this.totalCount / this.limit)
    },
    
    
    uniqueSpawnZones() {
      if (!this.selectedNPCDetail || !this.selectedNPCDetail.spawn_locations) return []
      
      // Create a set to store unique zone names
      const uniqueZones = new Set()
      
      this.selectedNPCDetail.spawn_locations.forEach(location => {
        const zoneName = location.zone_long_name || location.zone_short_name
        if (zoneName && zoneName.trim()) {
          uniqueZones.add(zoneName.trim())
        }
      })
      
      // Convert set to sorted array
      return Array.from(uniqueZones).sort()
    },

    allLootDropsExpanded() {
      // Check if we have loot drops and if all are expanded
      if (!this.selectedNPCDetail || !this.selectedNPCDetail.loot_drops || this.selectedNPCDetail.loot_drops.length === 0) {
        return false
      }
      
      // Return true if all loot drops are in the expanded set
      return this.selectedNPCDetail.loot_drops.every(lootDrop => 
        this.expandedLootDrops.has(lootDrop.loot_drop_id)
      )
    }
  },
  
  methods: {
    async performSearch() {
      if (!this.searchQuery.trim() && !this.minLevel && !this.maxLevel && !this.selectedZone) {
        this.showToast('Search Required', 'Please enter a search term or select filters.', 'warning')
        return
      }

      this.searching = true
      this.currentPage = 1
      
      try {
        const params = {
          q: this.searchQuery.trim(),
          limit: this.limit,
          offset: 0
        }
        
        // Add filters
        if (this.minLevel) params.min_level = this.minLevel
        if (this.maxLevel) params.max_level = this.maxLevel
        if (this.selectedZone) params.zone = this.selectedZone
        
        const response = await axios.get(`${API_BASE_URL}/api/npcs/search`, { params })
        
        this.searchResults = response.data.npcs || []
        this.totalCount = response.data.total_count || 0
        this.searchPerformed = true
        
      } catch (error) {
        console.error('Error searching NPCs:', error)
        this.showToast('Search Error', 'Failed to search NPCs. Please try again.', 'error')
        this.searchResults = []
        this.totalCount = 0
        this.searchPerformed = true
      } finally {
        this.searching = false
      }
    },

    changePage(page) {
      if (page < 1 || page > this.totalPages || page === this.currentPage) return
      
      // Clear current results to show loading state
      this.searchResults = []
      
      // Set paginating state
      this.paginating = true
      
      // Update current page
      this.currentPage = page
      
      // Perform the search for the new page
      this.performSearchWithPage(page)
    },

    async performSearchWithPage(page) {
      try {
        const params = {
          q: this.searchQuery.trim(),
          limit: this.limit,
          offset: (page - 1) * this.limit
        }
        
        // Add filters
        if (this.minLevel) params.min_level = this.minLevel
        if (this.maxLevel) params.max_level = this.maxLevel
        if (this.selectedZone) params.zone = this.selectedZone
        
        const response = await axios.get(`${API_BASE_URL}/api/npcs/search`, { params })
        this.searchResults = response.data.npcs || []
        
      } catch (error) {
        console.error('Error loading page:', error)
        this.showToast('Loading Error', 'Failed to load page. Please try again.', 'error')
      } finally {
        this.paginating = false
      }
    },

    clearFilters() {
      this.minLevel = ''
      this.maxLevel = ''
      this.selectedZone = ''
    },

    async openNPCModal(npc) {
      try {
        // Disable body scrolling
        document.body.style.overflow = 'hidden'
        
        // Reset expanded loot drops for new NPC
        this.expandedLootDrops.clear()
        
        // Start loading state
        this.loadingNPCDetails = true
        
        // Fetch detailed NPC information
        const response = await axios.get(`${API_BASE_URL}/api/npcs/${npc.id}/details`)
        
        // Combine basic NPC data with detailed information
        this.selectedNPCDetail = { ...npc, ...response.data }
        
        // Stop loading state
        this.loadingNPCDetails = false
        
      } catch (error) {
        console.error('Error fetching NPC details:', error)
        this.selectedNPCDetail = { ...npc }
        this.loadingNPCDetails = false
        this.showToast('Loading Error', 'Failed to load NPC details.', 'error')
      }
    },

    closeNPCModal() {
      this.selectedNPCDetail = null
      this.loadingNPCDetails = false
      // Re-enable body scrolling
      document.body.style.overflow = ''
    },

    getRaceName(raceId) {
      return this.raceNames[raceId] || `Race ${raceId}`
    },

    getClassName(classId) {
      return this.classNames[classId] || `Class ${classId}`
    },

    getFactionName(factionId) {
      // For now, return a placeholder - this could be expanded with faction data later
      if (!factionId || factionId === 0) return 'No Faction'
      return `Faction ${factionId}`
    },

    cleanNPCName(name) {
      // Remove leading # from NPC names and clean up underscores
      if (!name) return 'Unknown NPC'
      return name.replace(/^#+/, '').replace(/_/g, ' ').trim()
    },

    getClassIcon(classId) {
      // Map class IDs to their icon file names (same as in spell pages)
      const classIconMap = {
        1: 'warrior',      // Warrior
        2: 'cleric',       // Cleric
        3: 'paladin',      // Paladin
        4: 'ranger',       // Ranger
        5: 'shadowknight', // Shadow Knight
        6: 'druid',        // Druid
        7: 'monk',         // Monk
        8: 'bard',         // Bard
        9: 'rogue',        // Rogue
        10: 'shaman',      // Shaman
        11: 'necromancer', // Necromancer
        12: 'wizard',      // Wizard
        13: 'magician',    // Magician
        14: 'enchanter',   // Enchanter
        15: 'beastlord',   // Beastlord
        16: 'berserker'    // Berserker
      }
      
      const iconName = classIconMap[classId]
      return iconName ? `/icons/${iconName}.gif` : null
    },

    getFormattedZoneName(npc) {
      // Use long name if available, otherwise format short name
      if (npc.zone_long_name && npc.zone_long_name.trim()) {
        return npc.zone_long_name
      }
      
      // Format short name: remove underscores, capitalize words
      if (npc.zone_short_name) {
        return npc.zone_short_name
          .replace(/_/g, ' ')
          .split(' ')
          .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
          .join(' ')
      }
      
      return 'Unknown Zone'
    },

    handleIconError(event) {
      event.target.style.display = 'none'
    },

    toggleLootDrop(lootDropId) {
      if (this.expandedLootDrops.has(lootDropId)) {
        this.expandedLootDrops.delete(lootDropId)
      } else {
        this.expandedLootDrops.add(lootDropId)
      }
    },

    isLootDropExpanded(lootDropId) {
      return this.expandedLootDrops.has(lootDropId)
    },

    toggleAllLootDrops() {
      if (this.allLootDropsExpanded) {
        // Collapse all - clear the Set
        this.expandedLootDrops.clear()
      } else {
        // Expand all - add all loot drop IDs to the Set
        if (this.selectedNPCDetail && this.selectedNPCDetail.loot_drops) {
          this.selectedNPCDetail.loot_drops.forEach(lootDrop => {
            this.expandedLootDrops.add(lootDrop.loot_drop_id)
          })
        }
      }
    },

    openItemModal(itemId) {
      // Navigate to the Items page with the item modal opened
      // We'll pass the item ID as a query parameter (matching what Items.vue expects: 'item')
      this.$router.push({
        name: 'Items',
        query: { item: itemId }
      })
    },

    openSpellModal(spellId, spellName) {
      // Navigate to the Spells page with the spell modal opened
      // We'll pass the spell ID as a query parameter for the spell modal to open
      this.$router.push({
        name: 'Spells',
        query: { spell: spellId }
      })
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
    }
  },

  async mounted() {
    // Check if there's an NPC query parameter to open automatically
    if (this.$route.query.npc) {
      const npcId = parseInt(this.$route.query.npc)
      if (!isNaN(npcId)) {
        try {
          // Create a minimal NPC object with the ID to open the modal
          const npc = { id: npcId, name: 'Loading...' }
          await this.openNPCModal(npc)
        } catch (error) {
          console.error('Error auto-opening NPC modal:', error)
          this.showToast('Error', 'Failed to load NPC details', 'error')
        }
      }
    }
  },

  unmounted() {
    // Ensure body scrolling is restored if component is destroyed while modal is open
    document.body.style.overflow = ''
  }
}
</script>

<style scoped>
/* Use the same styling patterns as Items.vue and Spells.vue */
.npcs-page {
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
  background-clip: text;
}

.subtitle {
  font-size: 1.2rem;
  color: #888;
  margin: 0;
}

/* Search Section */
.search-section {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 15px;
  padding: 30px;
  margin-bottom: 30px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.search-container {
  max-width: 800px;
  margin: 0 auto;
}

.search-input-group {
  display: flex;
  gap: 15px;
  margin-bottom: 25px;
}

.search-input {
  flex: 1;
  padding: 15px 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 1rem;
  backdrop-filter: blur(5px);
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.7);
}

.search-button {
  padding: 15px 25px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  transition: all 0.3s ease;
}

.search-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
}

.search-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
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
  color: white;
  font-weight: 500;
  font-size: 0.9rem;
}

.filter-input, .filter-select {
  padding: 10px 15px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  backdrop-filter: blur(5px);
  min-width: 120px;
}

.filter-select option {
  background: #2a2a2a;
  color: white;
}

.clear-filters-button {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.clear-filters-button:hover {
  background: rgba(255, 255, 255, 0.3);
}

/* Results Section */
.results-section {
  margin-top: 30px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 25px;
  gap: 20px;
}

.results-info-container h2 {
  color: white;
  margin: 0 0 10px 0;
  font-size: 1.8rem;
}

.results-info {
  color: #9ca3af;
  font-size: 0.95rem;
}

.results-info span:not(:last-child) {
  margin-right: 8px;
}

/* View Toggle */
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
  padding: 8px 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #9ca3af;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.view-button:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.view-button.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.view-button-text {
  font-weight: 500;
}

/* NPC List View */
.npc-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 30px;
}

.npc-row {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.12) 0%, 
    rgba(255, 255, 255, 0.08) 100%);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 16px;
  padding: 8px 40px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 40px;
  position: relative;
  overflow: hidden;
  min-height: auto;
}

.npc-row::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(102, 126, 234, 0.05) 0%, 
    rgba(118, 75, 162, 0.05) 100%);
  opacity: 0;
  transition: opacity 0.4s ease;
}

.npc-row:hover {
  transform: translateY(-1px) scale(1.005);
  box-shadow: 
    0 8px 16px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(102, 126, 234, 0.2);
  border-color: rgba(102, 126, 234, 0.4);
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.15) 0%, 
    rgba(255, 255, 255, 0.10) 100%);
}

.npc-row:hover::before {
  opacity: 1;
}

.npc-main-info {
  flex: 1;
  min-width: 0;
  z-index: 1;
}

.npc-name-and-details {
  display: flex;
  align-items: center;
  gap: 24px;
  flex: 1;
  min-width: 0;
  flex-wrap: wrap;
}

.npc-row .npc-name {
  color: #f8fafc;
  margin: 0;
  font-size: 1.6rem;
  font-weight: 700;
  line-height: 1.2;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.4px;
  flex-shrink: 0;
}

.npc-details {
  display: flex;
  align-items: center;
  gap: 18px;
  font-size: 1.1rem;
  flex-wrap: wrap;
}

.npc-level {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 8px 20px;
  border-radius: 18px;
  font-size: 1rem;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  box-shadow: 0 3px 8px rgba(102, 126, 234, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.npc-separator {
  color: #64748b;
  font-weight: 600;
  font-size: 0.9rem;
  margin: 0 2px;
}

.npc-race {
  color: #94a3b8;
  font-weight: 600;
  font-size: 1.1rem;
}

.npc-class-with-icon {
  display: flex;
  align-items: center;
  gap: 12px;
}

.npc-class-icon {
  width: 65px;
  height: 84.5px;
  image-rendering: pixelated;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.4));
}

.npc-class {
  color: #cbd5e1;
  font-weight: 600;
  font-size: 1.1rem;
}

.npc-zone-display {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-width: 180px;
  z-index: 1;
}

.zone-name {
  color: #e2e8f0;
  font-size: 1.05rem;
  font-weight: 600;
  text-align: right;
  line-height: 1.4;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  padding: 10px 18px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 3px 10px rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(10px);
  white-space: nowrap;
}

/* NPC Grid View */
.npc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 14px;
  margin-bottom: 30px;
}

.npc-card {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.12) 0%, 
    rgba(255, 255, 255, 0.08) 100%);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: 16px;
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  min-height: auto;
}

.npc-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(102, 126, 234, 0.05) 0%, 
    rgba(118, 75, 162, 0.05) 100%);
  opacity: 0;
  transition: opacity 0.4s ease;
}

.npc-card:hover {
  transform: translateY(-1px) scale(1.005);
  box-shadow: 
    0 8px 16px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(102, 126, 234, 0.2);
  border-color: rgba(102, 126, 234, 0.4);
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.15) 0%, 
    rgba(255, 255, 255, 0.10) 100%);
}

.npc-card:hover::before {
  opacity: 1;
}

.npc-card-content {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
  gap: 16px;
  z-index: 1;
  position: relative;
}

.npc-card-main {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.npc-card-name {
  color: #f8fafc;
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  line-height: 1.3;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.3px;
}

.npc-card-details {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.95rem;
  flex-wrap: wrap;
}

.npc-card-level {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 5px 14px;
  border-radius: 14px;
  font-size: 0.85rem;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  box-shadow: 0 2px 6px rgba(102, 126, 234, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.npc-card-separator {
  color: #64748b;
  font-weight: 600;
  font-size: 0.75rem;
}

.npc-card-race {
  color: #94a3b8;
  font-weight: 600;
  font-size: 0.95rem;
}

.npc-card-class-with-icon {
  display: flex;
  align-items: center;
  gap: 6px;
}

.npc-card-class-icon {
  width: 50px;
  height: 65px;
  image-rendering: pixelated;
  filter: drop-shadow(0 1px 3px rgba(0, 0, 0, 0.4));
}

.npc-card-class {
  color: #cbd5e1;
  font-weight: 600;
  font-size: 0.95rem;
}

.npc-card-zone-display {
  display: flex;
  justify-content: center;
  margin-top: auto;
}

.npc-card-zone-name {
  color: #e2e8f0;
  font-size: 0.9rem;
  font-weight: 600;
  text-align: center;
  line-height: 1.4;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  padding: 8px 14px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(8px);
}

/* Enhanced Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
  animation: modalFadeIn 0.3s ease;
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

.npc-modal {
  background: linear-gradient(135deg, 
    rgba(20, 20, 30, 0.98) 0%, 
    rgba(25, 25, 35, 0.95) 100%);
  backdrop-filter: blur(25px);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 24px;
  width: 100%;
  max-width: 1000px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 
    0 30px 60px rgba(0, 0, 0, 0.6),
    0 0 0 1px rgba(102, 126, 234, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  animation: modalSlideIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes modalSlideIn {
  from {
    transform: translateY(-30px) scale(0.95);
    opacity: 0;
  }
  to {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 30px 35px 25px 35px;
  border-bottom: 1px solid rgba(102, 126, 234, 0.2);
  background: linear-gradient(135deg, 
    rgba(102, 126, 234, 0.08) 0%, 
    rgba(118, 75, 162, 0.05) 100%);
  border-radius: 24px 24px 0 0;
}

.npc-header-main {
  display: flex;
  align-items: center;
  gap: 30px;
  flex: 1;
}

.npc-title-section {
  display: flex;
  align-items: center;
  gap: 20px;
}

.npc-icon-container {
  position: relative;
}

.npc-modal-class-icon {
  width: 80px;
  height: 104px;
  image-rendering: pixelated;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.5));
  border-radius: 8px;
}

.npc-modal-class-fallback {
  font-size: 80px;
  color: rgba(102, 126, 234, 0.6);
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.5));
}

.npc-title-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.npc-modal-title {
  color: #f8fafc;
  margin: 0;
  font-size: 2.2rem;
  font-weight: 800;
  text-shadow: 0 3px 6px rgba(0, 0, 0, 0.4);
  letter-spacing: 0.5px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.npc-subtitle {
  color: #94a3b8;
  font-size: 1.1rem;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.npc-header-badges {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

.badge-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: flex-end;
}

.npc-id-badge, .level-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
}

.level-and-combat-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.health-badge, .mana-badge, .damage-badge {
  padding: 6px 12px;
  border-radius: 16px;
  font-size: 0.85rem;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  gap: 6px;
}

.health-badge {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  box-shadow: 0 3px 8px rgba(239, 68, 68, 0.3);
}

.mana-badge {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  box-shadow: 0 3px 8px rgba(59, 130, 246, 0.3);
}

.damage-badge {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  box-shadow: 0 3px 8px rgba(245, 158, 11, 0.3);
}

.modal-close {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #cbd5e1;
  font-size: 1.3rem;
  cursor: pointer;
  padding: 12px;
  border-radius: 12px;
  transition: all 0.3s ease;
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(10px);
}

.modal-close:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.4);
  color: #fecaca;
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
}

.modal-body {
  padding: 0 35px 35px 35px;
}

.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.08) 0%, 
    rgba(255, 255, 255, 0.04) 100%);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 16px;
  padding: 20px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
  border-color: rgba(102, 126, 234, 0.4);
}

.stat-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.stat-icon i {
  color: white;
  font-size: 1.2rem;
}

.stat-content h4 {
  color: #f8fafc;
  margin: 0 0 15px 0;
  font-size: 1.2rem;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.stat-details {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-label {
  color: #cbd5e1;
  font-weight: 500;
  font-size: 0.95rem;
}

.stat-value {
  color: #f8fafc;
  font-weight: 600;
  text-align: right;
  font-size: 0.95rem;
}

.highlight-health {
  color: #10b981;
  text-shadow: 0 1px 2px rgba(16, 185, 129, 0.3);
}

.highlight-mana {
  color: #3b82f6;
  text-shadow: 0 1px 2px rgba(59, 130, 246, 0.3);
}

.highlight-damage {
  color: #ef4444;
  text-shadow: 0 1px 2px rgba(239, 68, 68, 0.3);
}

.special-attacks-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.special-attack-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.special-attack-item:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateX(4px);
}

.special-attack-icon {
  color: #f59e0b;
  font-size: 0.8rem;
  opacity: 0.8;
}

.special-attack-name {
  color: #f8fafc;
  font-weight: 600;
  font-size: 0.9rem;
}

.content-section {
  margin-bottom: 30px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid rgba(102, 126, 234, 0.3);
}

.section-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-icon {
  color: #667eea;
  font-size: 1.3rem;
}

.section-header h3 {
  color: #f8fafc;
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.toggle-all-button {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

.toggle-all-button:hover {
  background: linear-gradient(135deg, #7c8df5 0%, #8b5cb3 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.toggle-all-button i {
  font-size: 0.8rem;
}

.zone-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.zone-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  padding: 12px 18px;
  border-radius: 14px;
  border: 1px solid rgba(102, 126, 234, 0.2);
  transition: all 0.3s ease;
  flex: 0 0 auto;
}

.zone-item:hover {
  transform: translateY(-1px);
  border-color: rgba(102, 126, 234, 0.4);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.zone-icon {
  color: #667eea;
  font-size: 1rem;
  flex-shrink: 0;
}

.zone-name {
  color: #f8fafc;
  font-weight: 600;
  font-size: 1rem;
}

.loot-tables {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.loot-table {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.05) 0%, 
    rgba(255, 255, 255, 0.02) 100%);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.3s ease;
}

.loot-table:hover {
  border-color: rgba(102, 126, 234, 0.4);
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.1);
}

.loot-table-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 12px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.2s ease;
}

.loot-table-header:hover {
  background: linear-gradient(135deg, #7c8df5 0%, #8b5cb3 100%);
}

.loot-table-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.loot-table-primary {
  display: flex;
  align-items: center;
  gap: 12px;
}

.loot-table-label {
  color: white;
  font-weight: 700;
  font-size: 0.95rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.item-count-badge {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 600;
  text-shadow: none;
}

.expansion-icon {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
  margin-left: auto;
  transition: transform 0.2s ease;
}

.loot-table-mechanics {
  display: flex;
  align-items: center;
  gap: 8px;
}

.multiplier-info, .droplimit-info, .mindrop-info {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.85rem;
  font-weight: 500;
}

.mindrop-info {
  color: rgba(34, 197, 94, 0.9); /* Green color to indicate guaranteed drops */
}

.loot-items {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.loot-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.08) 0%, 
    rgba(255, 255, 255, 0.04) 100%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.loot-item.clickable {
  cursor: pointer;
}

.loot-item.clickable:hover {
  transform: translateY(-1px);
  border-color: rgba(102, 126, 234, 0.4);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.15);
  background: linear-gradient(135deg, 
    rgba(102, 126, 234, 0.1) 0%, 
    rgba(118, 75, 162, 0.05) 100%);
}

.loot-item-icon-container {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.loot-item-icon {
  width: 32px;
  height: 32px;
  image-rendering: pixelated;
}

.loot-item-icon-placeholder {
  color: #64748b;
  font-size: 1.2rem;
}

.loot-item-info {
  flex: 1;
  min-width: 0;
}

.loot-item-name {
  color: #f8fafc;
  font-weight: 600;
  font-size: 1rem;
  line-height: 1.3;
  margin-bottom: 6px;
  transition: color 0.3s ease;
}

.loot-item.clickable:hover .loot-item-name {
  color: #e2e8f0;
}

.loot-item-chances {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.individual-chance {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  color: white;
  font-size: 0.8rem;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 8px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.chance-separator {
  color: #94a3b8;
  font-weight: 600;
  font-size: 0.8rem;
}

.overall-chance {
  font-size: 0.8rem;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.overall-chance.rare-drop {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
}

.overall-chance.common-drop {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.overall-chance:not(.rare-drop):not(.common-drop) {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.spawn-locations, .loot-drops {
  display: grid;
  gap: 10px;
}

.spawn-location {
  background: rgba(255, 255, 255, 0.05);
  padding: 12px 15px;
  border-radius: 8px;
  color: #ccc;
}

.loot-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 12px 15px;
}

.loot-item-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.loot-item-icon {
  width: 24px;
  height: 24px;
  image-rendering: pixelated;
}

.loot-item-icon-placeholder {
  width: 24px;
  height: 24px;
  color: #666;
}

.loot-item-name {
  flex: 1;
  color: white;
  font-weight: 500;
}

.loot-probability {
  color: #ccc;
  font-size: 0.9rem;
}

/* NPC Spells */
.npc-spells-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.npc-spell-card {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.08) 0%, 
    rgba(255, 255, 255, 0.04) 100%);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  padding: 16px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.npc-spell-card:hover {
  border-color: rgba(102, 126, 234, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
  background: linear-gradient(135deg, 
    rgba(102, 126, 234, 0.12) 0%, 
    rgba(118, 75, 162, 0.08) 100%);
}

.npc-spell-icon-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 64px;
  height: 64px;
  margin: 0 auto 12px;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.npc-spell-icon {
  width: 48px;
  height: 48px;
  image-rendering: pixelated;
}

.npc-spell-icon-placeholder {
  color: rgba(102, 126, 234, 0.6);
  font-size: 24px;
}

.npc-spell-info {
  text-align: center;
}

.npc-spell-name {
  color: #f8fafc;
  font-size: 0.95rem;
  font-weight: 600;
  line-height: 1.3;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

/* Merchant Items */
.merchant-items {
  display: grid;
  gap: 10px;
}

.merchant-item {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 12px 15px;
}

.merchant-item-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.merchant-item-icon {
  width: 24px;
  height: 24px;
  image-rendering: pixelated;
}

.merchant-item-icon-placeholder {
  width: 24px;
  height: 24px;
  color: #666;
}

.merchant-details {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.merchant-item-name {
  color: white;
  font-weight: 500;
}

.merchant-price {
  color: #ffd700;
  font-weight: 600;
  font-size: 0.9rem;
}

/* Enhanced Pagination */
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
  margin: 20px 0;
  margin-bottom: 30px;
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
  font-weight: 600;
  font-size: 0.9rem;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.page-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.page-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: linear-gradient(135deg, #4a5568 0%, #2d3748 100%);
  transform: none;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.page-info {
  color: #e2e8f0;
  font-weight: 600;
  font-size: 1rem;
  padding: 0 15px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 8px 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
}

/* No Results */
.no-results {
  text-align: center;
  padding: 60px 20px;
  color: #ccc;
}

.no-results-content i {
  font-size: 4rem;
  margin-bottom: 20px;
  opacity: 0.5;
}

.no-results-content h3 {
  margin: 0 0 10px 0;
  color: white;
}

/* Toast Notifications */
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.toast {
  background: rgba(30, 30, 30, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 15px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 300px;
  max-width: 400px;
  color: white;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
  animation: slideInRight 0.3s ease;
}

.toast.success { border-left: 4px solid #10b981; }
.toast.error { border-left: 4px solid #ef4444; }
.toast.warning { border-left: 4px solid #f59e0b; }
.toast.info { border-left: 4px solid #3b82f6; }

.toast-content {
  flex: 1;
}

.toast-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.toast-message {
  font-size: 0.9rem;
  opacity: 0.8;
}

.toast-close {
  background: none;
  border: none;
  color: #ccc;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.toast-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  .npcs-page {
    padding: 15px;
    padding-top: 80px;
  }
  
  .page-header h1 {
    font-size: 2rem;
  }
  
  .search-input-group {
    flex-direction: column;
  }
  
  .filters-container {
    flex-direction: column;
    align-items: stretch;
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
  
  .npc-grid {
    grid-template-columns: 1fr;
  }
  
  .npc-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
    padding: 26px 28px;
    min-height: auto;
  }
  
  .npc-name-and-details {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .npc-row .npc-name {
    font-size: 1.35rem;
  }
  
  .npc-details {
    gap: 14px;
    font-size: 1rem;
  }
  
  .npc-class-icon {
    width: 60px;
    height: 78px;
  }
  
  .npc-level {
    padding: 6px 16px;
    font-size: 0.9rem;
  }
  
  .npc-zone-display {
    align-self: stretch;
    justify-content: flex-start;
    min-width: auto;
  }
  
  .zone-name {
    text-align: left;
    font-size: 0.95rem;
    padding: 8px 14px;
  }
  
  .modal-overlay {
    padding: 10px;
  }
  
  .modal-header, .modal-body {
    padding: 20px;
  }
  
  .npc-header-meta {
    flex-direction: column;
    align-items: start;
  }
  
  .info-row {
    flex-direction: column;
    align-items: start;
    gap: 4px;
  }
  
  .info-value {
    text-align: left;
  }
  
  .pagination {
    flex-direction: column;
    gap: 12px;
  }
}
</style>