<template>
  <div v-if="selectedItemDetail && !loadingItemModal" class="modal-overlay" @click="closeItemModal">
    <div class="modal-content item-modal" @click.stop>
      <div class="modal-header">
        <div class="modal-header-content">
          <div class="item-icon-modal-container">
            <img 
              v-if="selectedItemDetail.icon" 
              :src="`/icons/items/${selectedItemDetail.icon}.gif`" 
              :alt="`${selectedItemDetail.name || selectedItemDetail.Name || 'Unknown Item'} icon`"
              class="item-icon-modal"
              @error="handleIconError"
            />
            <div v-else class="item-icon-placeholder-modal">
              <i class="fas fa-cube"></i>
            </div>
          </div>
          <div class="item-header-info">
            <div class="item-title-row">
              <h3>{{ selectedItemDetail.name || selectedItemDetail.Name || 'Unknown Item' }}</h3>
              <button 
                v-if="selectedItemDetail.id"
                @click="openItemInNewTab(selectedItemDetail.id)"
                class="open-item-button"
                title="Open in Items page"
              >
                <i class="fas fa-external-link-alt"></i>
              </button>
            </div>
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
              <div v-if="getStatValue(selectedItemDetail, 'str')" class="attribute-item">
                <span class="attr-label">STR</span>
                <span class="attr-value">+{{ getStatValue(selectedItemDetail, 'str') }}</span>
              </div>
              <div v-if="getStatValue(selectedItemDetail, 'sta')" class="attribute-item">
                <span class="attr-label">STA</span>
                <span class="attr-value">+{{ getStatValue(selectedItemDetail, 'sta') }}</span>
              </div>
              <div v-if="getStatValue(selectedItemDetail, 'agi')" class="attribute-item">
                <span class="attr-label">AGI</span>
                <span class="attr-value">+{{ getStatValue(selectedItemDetail, 'agi') }}</span>
              </div>
              <div v-if="getStatValue(selectedItemDetail, 'dex')" class="attribute-item">
                <span class="attr-label">DEX</span>
                <span class="attr-value">+{{ getStatValue(selectedItemDetail, 'dex') }}</span>
              </div>
              <div v-if="getStatValue(selectedItemDetail, 'wis')" class="attribute-item">
                <span class="attr-label">WIS</span>
                <span class="attr-value">+{{ getStatValue(selectedItemDetail, 'wis') }}</span>
              </div>
              <div v-if="getStatValue(selectedItemDetail, 'int')" class="attribute-item">
                <span class="attr-label">INT</span>
                <span class="attr-value">+{{ getStatValue(selectedItemDetail, 'int') }}</span>
              </div>
              <div v-if="getStatValue(selectedItemDetail, 'cha')" class="attribute-item">
                <span class="attr-label">CHA</span>
                <span class="attr-value">+{{ getStatValue(selectedItemDetail, 'cha') }}</span>
              </div>
            </div>
          </div>
          
          <!-- Resistances -->
          <div v-if="hasResistValues(selectedItemDetail)" class="detail-section">
            <h4>Resistances</h4>
            <div class="resistances-grid">
              <div v-if="getResistanceValue(selectedItemDetail, 'fire')" class="resist-item fire">
                <span class="resist-label">Fire</span>
                <span class="resist-value">+{{ getResistanceValue(selectedItemDetail, 'fire') }}</span>
              </div>
              <div v-if="getResistanceValue(selectedItemDetail, 'cold')" class="resist-item cold">
                <span class="resist-label">Cold</span>
                <span class="resist-value">+{{ getResistanceValue(selectedItemDetail, 'cold') }}</span>
              </div>
              <div v-if="getResistanceValue(selectedItemDetail, 'magic')" class="resist-item magic">
                <span class="resist-label">Magic</span>
                <span class="resist-value">+{{ getResistanceValue(selectedItemDetail, 'magic') }}</span>
              </div>
              <div v-if="getResistanceValue(selectedItemDetail, 'disease')" class="resist-item disease">
                <span class="resist-label">Disease</span>
                <span class="resist-value">+{{ getResistanceValue(selectedItemDetail, 'disease') }}</span>
              </div>
              <div v-if="getResistanceValue(selectedItemDetail, 'poison')" class="resist-item poison">
                <span class="resist-label">Poison</span>
                <span class="resist-value">+{{ getResistanceValue(selectedItemDetail, 'poison') }}</span>
              </div>
              <div v-if="getResistanceValue(selectedItemDetail, 'corruption')" class="resist-item corruption">
                <span class="resist-label">Corruption</span>
                <span class="resist-value">+{{ getResistanceValue(selectedItemDetail, 'corruption') }}</span>
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
                <span class="req-value">{{ selectedItemDetail.weight }}</span>
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
            
            <!-- Loading state -->
            <div v-if="loadingDropSources" class="loading-sources">
              <i class="fas fa-spinner fa-spin"></i>
              <span>Loading drop sources...</span>
            </div>
            
            <!-- Drop Sources Results -->
            <div v-else-if="dropSources && dropSourcesRequested" class="drop-sources-results">
              <div v-if="dropSources.length === 0" class="no-drop-sources">
                <i class="fas fa-exclamation-circle"></i>
                <span>No drop sources found for this item</span>
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
                      @click="openNPCInNewTab(npc.npc_id, npc.npc_name)"
                    >
                      <span class="npc-name">
                        {{ npc.npc_name }}
                        <i class="fas fa-external-link-alt npc-link-icon"></i>
                      </span>
                      <span class="drop-chance">{{ (npc.drop_chance || npc.chance || 0) }}%</span>
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
            
            <!-- Loading state -->
            <div v-if="loadingMerchantSources" class="loading-sources">
              <i class="fas fa-spinner fa-spin"></i>
              <span>Loading merchant sources...</span>
            </div>
            
            <!-- Merchant Sources Results -->
            <div v-else-if="merchantSources && merchantSourcesRequested" class="merchant-sources-results">
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
                    <div 
                      v-for="merchant in zone.merchants" 
                      :key="merchant.npc_id" 
                      class="merchant-item"
                    >
                      <span class="merchant-name">{{ merchant.npc_name }}</span>
                      <span class="merchant-price">{{ formatMerchantPrice(merchant) }}</span>
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
</template>

<script setup>
import { ref, computed } from 'vue'
import { getApiBaseUrl } from '../config/api'

const props = defineProps({
  selectedItemDetail: {
    type: Object,
    default: () => null
  },
  loadingItemModal: {
    type: Boolean,
    default: false
  },
  dropSources: {
    type: [Array, Object],
    default: () => null
  },
  loadingDropSources: {
    type: Boolean,
    default: false
  },
  dropSourcesRequested: {
    type: Boolean,
    default: false
  },
  merchantSources: {
    type: [Array, Object],
    default: () => null
  },
  loadingMerchantSources: {
    type: Boolean,
    default: false
  },
  merchantSourcesRequested: {
    type: Boolean,
    default: false
  },
  openNPCModal: {
    type: Function,
    default: () => null
  },
  // Availability data for conditional section display
  itemDataAvailability: {
    type: [Object, String],
    default: () => null
  },
  loadingAvailability: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'loadDropSources', 'loadMerchantSources'])

const shouldShowDropSources = computed(() => {
  // Show while loading availability check
  if (props.loadingAvailability) return false
  
  // Show all if availability check failed (fallback)
  if (props.itemDataAvailability === 'failed') return true
  
  // Show if no availability data yet (initial state)
  if (!props.itemDataAvailability) return false
  
  // Only show if data exists
  return props.itemDataAvailability.drop_sources > 0
})

const shouldShowMerchantSources = computed(() => {
  // Show while loading availability check
  if (props.loadingAvailability) return false
  
  // Show all if availability check failed (fallback)
  if (props.itemDataAvailability === 'failed') return true
  
  // Show if no availability data yet (initial state)
  if (!props.itemDataAvailability) return false
  
  // Only show if data exists
  return props.itemDataAvailability.merchant_sources > 0
})

const closeItemModal = () => {
  emit('close')
}

const loadDropSources = () => {
  emit('loadDropSources')
}

const loadMerchantSources = () => {
  emit('loadMerchantSources')
}

const handleIconError = (event) => {
  const currentSrc = event.target.src
  if (currentSrc.endsWith('.png')) {
    event.target.src = currentSrc.replace('.png', '.gif')
  } else if (currentSrc.endsWith('.gif')) {
    // If gif also fails, try the default icon
    event.target.src = '/icons/items/500.png'
  } else {
    // Last resort - use a generic placeholder
    event.target.style.display = 'none'
    event.target.parentElement.innerHTML = '<div class="item-icon-placeholder-modal"><i class="fas fa-cube"></i></div>'
  }
}

const getItemTypeDisplay = (itemtype) => {
  const ITEM_TYPES = {
    0: 'Common Item',
    1: '1H Slashing',
    2: '2H Slashing', 
    3: '1H Piercing',
    4: '1H Blunt',
    5: '2H Blunt',
    7: 'Archery',
    8: 'Shield',
    10: 'Armor',
    11: 'Miscellaneous',
    14: 'Food',
    15: 'Drink',
    16: 'Light',
    17: 'Combinable',
    18: 'Bandage',
    19: 'Throwing',
    20: 'Spell',
    21: 'Potion',
    22: 'Wind Instrument',
    23: 'String Instrument',
    24: 'Brass Instrument',
    25: 'Drum',
    26: 'Arrow',
    27: 'Jewelry',
    29: 'Skill Tome',
    35: 'Note'
  }
  return ITEM_TYPES[itemtype] || 'Unknown'
}

const getWeaponRatio = (damage, delay) => {
  if (!damage || !delay) return '0.0'
  return (damage / (delay / 10)).toFixed(1)
}

const getStatValue = (item, stat) => {
  // Handle both character inventory format and items API format
  if (!item) return 0
  
  // Character inventory format (attributes object)
  if (item.attributes && item.attributes[stat]) {
    return item.attributes[stat]
  }
  
  // Character inventory format (astr, asta, etc.)
  const attrMap = {
    str: 'astr',
    sta: 'asta', 
    agi: 'aagi',
    dex: 'adex',
    wis: 'awis',
    int: 'aint',
    cha: 'acha'
  }
  
  if (item[attrMap[stat]]) {
    return item[attrMap[stat]]
  }
  
  // Items API format (direct properties)
  return item[stat] || 0
}

const getResistanceValue = (item, resist) => {
  if (!item) return 0
  
  // Character inventory format (resistances object)
  if (item.resistances && item.resistances[resist]) {
    return item.resistances[resist]
  }
  
  // Character inventory format (fr, cr, etc.)
  const resistMap = {
    fire: 'fr',
    cold: 'cr',
    magic: 'mr',
    disease: 'dr',
    poison: 'pr',
    corruption: 'svcorruption'
  }
  
  if (item[resistMap[resist]]) {
    return item[resistMap[resist]]
  }
  
  return 0
}

const hasAnyStats = (item) => {
  if (!item) return false
  return getStatValue(item, 'str') || getStatValue(item, 'sta') || getStatValue(item, 'agi') ||
         getStatValue(item, 'dex') || getStatValue(item, 'wis') || getStatValue(item, 'int') ||
         getStatValue(item, 'cha')
}

const hasResistValues = (item) => {
  if (!item) return false
  return getResistanceValue(item, 'fire') || getResistanceValue(item, 'cold') ||
         getResistanceValue(item, 'magic') || getResistanceValue(item, 'disease') ||
         getResistanceValue(item, 'poison') || getResistanceValue(item, 'corruption')
}

const getClassDisplay = (classes) => {
  // Implementation depends on your class mapping
  return 'All Classes' // Placeholder
}

const getRaceDisplay = (races) => {
  // Implementation depends on your race mapping
  return 'All Races' // Placeholder
}

const getSlotDisplay = (slots) => {
  // Implementation depends on your slot mapping
  return 'Various' // Placeholder
}

const formatMerchantPrice = (merchant) => {
  if (!merchant) return '0pp'
  
  // Handle different price formats from backend
  if (merchant.price_coins) {
    const coins = merchant.price_coins
    const parts = []
    
    if (coins.platinum && coins.platinum > 0) parts.push(`${coins.platinum}pp`)
    if (coins.gold && coins.gold > 0) parts.push(`${coins.gold}gp`)
    if (coins.silver && coins.silver > 0) parts.push(`${coins.silver}sp`)
    if (coins.bronze && coins.bronze > 0) parts.push(`${coins.bronze}cp`)
    
    return parts.length > 0 ? parts.join(' ') : '0pp'
  }
  
  // Fallback to simple price display
  return merchant.price ? `${merchant.price}pp` : '0pp'
}

// Navigation functions for opening items/NPCs in new tabs
const openNPCInNewTab = (npcId, npcName) => {
  if (!npcId) return
  
  // Build URL for NPCs page with query parameter
  const npcUrl = `${window.location.origin}/npcs?npc=${npcId}`
  
  // Open in new tab
  window.open(npcUrl, '_blank', 'noopener,noreferrer')
}

const openItemInNewTab = (itemId) => {
  if (!itemId) return
  
  // Build URL for Items page with query parameter
  const itemUrl = `${window.location.origin}/items?item=${itemId}`
  
  // Open in new tab
  window.open(itemUrl, '_blank', 'noopener,noreferrer')
}

</script>

<style scoped>
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
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
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

.item-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.item-header-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.item-icon-modal-container {
  flex-shrink: 0;
}

.item-icon-modal {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  image-rendering: pixelated;
}

.item-icon-placeholder-modal {
  width: 64px;
  height: 64px;
  border-radius: 8px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  color: #666;
  font-size: 24px;
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
  background: rgba(156, 163, 175, 0.2);
  color: #9ca3af;
  border-color: rgba(156, 163, 175, 0.3);
}

.modal-close {
  background: none;
  border: none;
  color: #ccc;
  font-size: 20px;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.open-item-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: white;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 28px;
}

.open-item-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.modal-body {
  padding: 30px;
}

.item-details {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-section {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.detail-section h4 {
  color: #f7fafc;
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.primary-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
}

.primary-stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(0, 0, 0, 0.3);
  padding: 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.stat-icon {
  color: #60a5fa;
  font-size: 1.2rem;
  width: 20px;
  text-align: center;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  color: #f7fafc;
  font-weight: 600;
  font-size: 1rem;
}

.stat-label {
  color: #cbd5e0;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-extra {
  color: #9ca3af;
  font-size: 0.75rem;
}

.attributes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
  gap: 12px;
}

.attribute-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(0, 0, 0, 0.3);
  padding: 12px 8px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.attr-label {
  color: #cbd5e0;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.attr-value {
  color: #68d391;
  font-weight: 700;
  font-size: 1rem;
}

.resistances-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 12px;
}

.resist-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(0, 0, 0, 0.3);
  padding: 12px 8px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.resist-label {
  color: #cbd5e0;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.resist-value {
  font-weight: 700;
  font-size: 1rem;
}

.resist-item.fire .resist-value { color: #f56565; }
.resist-item.cold .resist-value { color: #63b3ed; }
.resist-item.magic .resist-value { color: #9f7aea; }
.resist-item.disease .resist-value { color: #68d391; }
.resist-item.poison .resist-value { color: #48bb78; }
.resist-item.corruption .resist-value { color: #ed8936; }

.requirements-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.requirement-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.requirement-item:last-child {
  border-bottom: none;
}

.req-label {
  color: #cbd5e0;
  font-weight: 500;
}

.req-value {
  color: #f7fafc;
  font-weight: 600;
}

.drop-sources-header, .merchant-sources-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.drop-sources-button, .merchant-sources-button {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
}

.drop-sources-button:hover, .merchant-sources-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.loading-sources {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 24px;
  color: #cbd5e0;
}

.no-drop-sources, .no-merchant-sources {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: #9ca3af;
  font-style: italic;
}

.zones-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.zone-section {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.zone-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #f7fafc;
  font-weight: 600;
}

.zone-name {
  color: #60a5fa;
}

.npc-count, .merchant-count {
  color: #9ca3af;
  font-size: 0.875rem;
}

.npcs-list, .merchants-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.npc-item, .merchant-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.npc-item.clickable {
  cursor: pointer;
  transition: all 0.2s ease;
}

.npc-item.clickable:hover {
  background: rgba(0, 0, 0, 0.4);
  border-color: rgba(255, 255, 255, 0.1);
}

.npc-name, .merchant-name {
  color: #f7fafc;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.npc-link-icon {
  font-size: 10px;
  color: #9ca3af;
  opacity: 0.7;
  transition: all 0.2s ease;
}

.npc-item.clickable:hover .npc-link-icon {
  opacity: 1;
  color: #60a5fa;
}

.drop-chance {
  color: #68d391;
  font-weight: 600;
}

.merchant-price {
  color: #fbbf24;
  font-weight: 600;
}
</style>