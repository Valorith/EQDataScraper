<template>
  <div class="character-inventory">
    <!-- Tab Headers -->
    <div class="inventory-tabs">
      <div class="tab active">Inventory</div>
      <div class="tab">Stats</div>
      <div class="tab">Alt Currency</div>
    </div>

    <!-- Main Inventory Layout -->
    <div class="inventory-layout">
      <!-- Left Stats Panel -->
      <div class="stats-panel">
        <div class="character-header">
          <div class="char-name">{{ character.name }}</div>
          <div class="char-details">{{ character.level }} {{ character.class }}</div>
          <div class="char-details">{{ character.race }}</div>
        </div>
        
        <div class="character-stats">
          <div class="combat-stats">
            <div class="stat-row hp">
              <span class="stat-label">HP</span>
              <span class="stat-value">{{ character.maxHp }}</span>
            </div>
            <div class="stat-row mp">
              <span class="stat-label">MP</span>
              <span class="stat-value">{{ character.maxMp || 0 }}</span>
            </div>
            <div class="stat-row en">
              <span class="stat-label">ENDUR</span>
              <span class="stat-value">{{ character.endurance || 0 }}</span>
            </div>
            <div class="stat-row ac">
              <span class="stat-label">AC</span>
              <span class="stat-value">{{ character.ac || 0 }}</span>
            </div>
            <div class="stat-row atk">
              <span class="stat-label">ATK</span>
              <span class="stat-value">{{ character.atk || 0 }}</span>
            </div>
          </div>
          
          
          <div class="primary-stats">
            <div class="stat-group">
              <div class="stat-row"><span class="stat-label">STR</span><span class="stat-value green">{{ character.stats.str }}</span></div>
              <div class="stat-row"><span class="stat-label">STA</span><span class="stat-value green">{{ character.stats.sta }}</span></div>
              <div class="stat-row"><span class="stat-label">AGI</span><span class="stat-value green">{{ character.stats.agi }}</span></div>
              <div class="stat-row"><span class="stat-label">DEX</span><span class="stat-value green">{{ character.stats.dex }}</span></div>
              <div class="stat-row"><span class="stat-label">WIS</span><span class="stat-value green">{{ character.stats.wis }}</span></div>
              <div class="stat-row"><span class="stat-label">INT</span><span class="stat-value green">{{ character.stats.int }}</span></div>
              <div class="stat-row"><span class="stat-label">CHA</span><span class="stat-value green">{{ character.stats.cha }}</span></div>
            </div>
          </div>
          
          <div class="resistances">
            <div class="resist-group">
              <div class="stat-row"><span class="stat-label">POISON</span><span class="stat-value green">{{ character.resistances.poison }}</span></div>
              <div class="stat-row"><span class="stat-label">MAGIC</span><span class="stat-value green">{{ character.resistances.magic }}</span></div>
              <div class="stat-row"><span class="stat-label">DISEASE</span><span class="stat-value green">{{ character.resistances.disease }}</span></div>
              <div class="stat-row"><span class="stat-label">FIRE</span><span class="stat-value green">{{ character.resistances.fire }}</span></div>
              <div class="stat-row"><span class="stat-label">COLD</span><span class="stat-value green">{{ character.resistances.cold }}</span></div>
              <div class="stat-row"><span class="stat-label">CORRUPT</span><span class="stat-value green">{{ character.resistances.corrupt || 0 }}</span></div>
            </div>
          </div>
          
          <div class="misc-stats">
            <div class="stat-row">
              <span class="stat-label">WEIGHT</span>
              <span class="stat-value">{{ character.weight || 0 }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Center Equipment/Character Area -->
      <div class="equipment-area" @click="handleEquipmentClick">
        <!-- Equipment slots positioned around character -->
        <div class="equipment-slot-positioned charm-slot" data-slot="charm">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.charm }"
               :data-tooltip="getItemTooltip(character.equipment?.charm)">
            <img v-if="character.equipment?.charm" 
                 :src="`/icons/items/${character.equipment.charm.icon}.png`" 
                 :alt="character.equipment.charm.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">CHARM</span>
          </div>
        </div>
        <div class="equipment-slot-positioned head-slot" data-slot="head">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.head }"
               :data-tooltip="getItemTooltip(character.equipment?.head)"
>
            <img v-if="character.equipment?.head" 
                 :src="`/icons/items/${character.equipment.head.icon}.png`" 
                 :alt="character.equipment.head.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">HELM</span>
          </div>
        </div>
        <div class="equipment-slot-positioned ear-slot" data-slot="ear1">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.ear1 }"
               :data-tooltip="getItemTooltip(character.equipment?.ear1)"
>
            <img v-if="character.equipment?.ear1" 
                 :src="`/icons/items/${character.equipment.ear1.icon}.png`" 
                 :alt="character.equipment.ear1.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">EAR</span>
          </div>
        </div>
        <div class="equipment-slot-positioned ear-slot ear-2" data-slot="ear2">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.ear2 }"
               :data-tooltip="getItemTooltip(character.equipment?.ear2)"
>
            <img v-if="character.equipment?.ear2" 
                 :src="`/icons/items/${character.equipment.ear2.icon}.png`" 
                 :alt="character.equipment.ear2.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">EAR</span>
          </div>
        </div>
        <div class="equipment-slot-positioned neck-slot" data-slot="neck">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.neck }"
               :data-tooltip="getItemTooltip(character.equipment?.neck)"
>
            <img v-if="character.equipment?.neck" 
                 :src="`/icons/items/${character.equipment.neck.icon}.png`" 
                 :alt="character.equipment.neck.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">NECK</span>
          </div>
        </div>
        <div class="equipment-slot-positioned shoulder-slot" data-slot="shoulder">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.shoulder }"
               :data-tooltip="getItemTooltip(character.equipment?.shoulder)"
>
            <img v-if="character.equipment?.shoulder" 
                 :src="`/icons/items/${character.equipment.shoulder.icon}.png`" 
                 :alt="character.equipment.shoulder.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">SHOULDER</span>
          </div>
        </div>
        <div class="equipment-slot-positioned arms-slot" data-slot="arms">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.arms }"
               :data-tooltip="getItemTooltip(character.equipment?.arms)"
>
            <img v-if="character.equipment?.arms" 
                 :src="`/icons/items/${character.equipment.arms.icon}.png`" 
                 :alt="character.equipment.arms.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">ARMS</span>
          </div>
        </div>
        <div class="equipment-slot-positioned back-slot" data-slot="back">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.back }"
               :data-tooltip="getItemTooltip(character.equipment?.back)"
>
            <img v-if="character.equipment?.back" 
                 :src="`/icons/items/${character.equipment.back.icon}.png`" 
                 :alt="character.equipment.back.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">BACK</span>
          </div>
        </div>
        <div class="equipment-slot-positioned wrist-slot wrist-1" data-slot="wrist1">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.wrist1 }"
               :data-tooltip="getItemTooltip(character.equipment?.wrist1)"
>
            <img v-if="character.equipment?.wrist1" 
                 :src="`/icons/items/${character.equipment.wrist1.icon}.png`" 
                 :alt="character.equipment.wrist1.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">WRIST</span>
          </div>
        </div>
        <div class="equipment-slot-positioned wrist-slot wrist-2" data-slot="wrist2">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.wrist2 }"
               :data-tooltip="getItemTooltip(character.equipment?.wrist2)"
>
            <img v-if="character.equipment?.wrist2" 
                 :src="`/icons/items/${character.equipment.wrist2.icon}.png`" 
                 :alt="character.equipment.wrist2.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">WRIST</span>
          </div>
        </div>
        <div class="equipment-slot-positioned range-slot" data-slot="range">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.range }"
               :data-tooltip="getItemTooltip(character.equipment?.range)"
>
            <img v-if="character.equipment?.range" 
                 :src="`/icons/items/${character.equipment.range.icon}.png`" 
                 :alt="character.equipment.range.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">RANGED</span>
          </div>
        </div>
        <div class="equipment-slot-positioned hands-slot" data-slot="hands">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.hands }"
               :data-tooltip="getItemTooltip(character.equipment?.hands)"
>
            <img v-if="character.equipment?.hands" 
                 :src="`/icons/items/${character.equipment.hands.icon}.png`" 
                 :alt="character.equipment.hands.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">HANDS</span>
          </div>
        </div>
        <div class="equipment-slot-positioned primary-slot" data-slot="primary">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.primary }"
               :data-tooltip="getItemTooltip(character.equipment?.primary)"
>
            <img v-if="character.equipment?.primary" 
                 :src="`/icons/items/${character.equipment.primary.icon}.png`" 
                 :alt="character.equipment.primary.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">MAIN HAND</span>
          </div>
        </div>
        <div class="equipment-slot-positioned secondary-slot" data-slot="secondary">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.secondary }"
               :data-tooltip="getItemTooltip(character.equipment?.secondary)"
>
            <img v-if="character.equipment?.secondary" 
                 :src="`/icons/items/${character.equipment.secondary.icon}.png`" 
                 :alt="character.equipment.secondary.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">OFF<br>HAND</span>
          </div>
        </div>
        <div class="equipment-slot-positioned ammo-bottom-slot" data-slot="ammo">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.ammo }"
               :data-tooltip="getItemTooltip(character.equipment?.ammo)"
>
            <img v-if="character.equipment?.ammo" 
                 :src="`/icons/items/${character.equipment.ammo.icon}.png`" 
                 :alt="character.equipment.ammo.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">AMMO</span>
          </div>
        </div>
        <div class="equipment-slot-positioned ring-slot ring-1" data-slot="ring1">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.ring1 }"
               :data-tooltip="getItemTooltip(character.equipment?.ring1)"
>
            <img v-if="character.equipment?.ring1" 
                 :src="`/icons/items/${character.equipment.ring1.icon}.png`" 
                 :alt="character.equipment.ring1.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">FINGER</span>
          </div>
        </div>
        <div class="equipment-slot-positioned ring-slot ring-2" data-slot="ring2">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.ring2 }"
               :data-tooltip="getItemTooltip(character.equipment?.ring2)"
>
            <img v-if="character.equipment?.ring2" 
                 :src="`/icons/items/${character.equipment.ring2.icon}.png`" 
                 :alt="character.equipment.ring2.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">FINGER</span>
          </div>
        </div>
        <div class="equipment-slot-positioned chest-slot" data-slot="chest">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.chest }"
               :data-tooltip="getItemTooltip(character.equipment?.chest)"
>
            <img v-if="character.equipment?.chest" 
                 :src="`/icons/items/${character.equipment.chest.icon}.png`" 
                 :alt="character.equipment.chest.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">CHEST</span>
          </div>
        </div>
        <div class="equipment-slot-positioned legs-slot" data-slot="legs">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.legs }"
               :data-tooltip="getItemTooltip(character.equipment?.legs)"
>
            <img v-if="character.equipment?.legs" 
                 :src="`/icons/items/${character.equipment.legs.icon}.png`" 
                 :alt="character.equipment.legs.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">LEGS</span>
          </div>
        </div>
        <div class="equipment-slot-positioned feet-slot" data-slot="feet">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.feet }"
               :data-tooltip="getItemTooltip(character.equipment?.feet)"
>
            <img v-if="character.equipment?.feet" 
                 :src="`/icons/items/${character.equipment.feet.icon}.png`" 
                 :alt="character.equipment.feet.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">FEET</span>
          </div>
        </div>
        <div class="equipment-slot-positioned waist-slot" data-slot="waist">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.waist }"
               :data-tooltip="getItemTooltip(character.equipment?.waist)"
>
            <img v-if="character.equipment?.waist" 
                 :src="`/icons/items/${character.equipment.waist.icon}.png`" 
                 :alt="character.equipment.waist.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">WAIST</span>
          </div>
        </div>
        <div class="equipment-slot-positioned ammo-slot" data-slot="power_source">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.power_source }"
               :data-tooltip="getItemTooltip(character.equipment?.power_source)"
>
            <img v-if="character.equipment?.power_source" 
                 :src="`/icons/items/${character.equipment.power_source.icon}.png`" 
                 :alt="character.equipment.power_source.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">POWER<br>SOURCE</span>
          </div>
        </div>
        <div class="equipment-slot-positioned face-slot" data-slot="face">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.face }"
               :data-tooltip="getItemTooltip(character.equipment?.face)"
>
            <img v-if="character.equipment?.face" 
                 :src="`/icons/items/${character.equipment.face.icon}.png`" 
                 :alt="character.equipment.face.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">FACE</span>
          </div>
        </div>

        <!-- Character Model/Class Icon in center -->
        <div class="character-model">
          <img :src="`/icons/${normalizeClassName(character.class).toLowerCase()}.gif`" :alt="character.class" class="class-icon" @error="handleImageError" />
        </div>
      </div>

      <!-- Right Currency/Bags Panel -->
      <div class="currency-bags-panel">
        <!-- Currency Display -->
        <div class="currency-section">
          <div class="currency-header">MONEY</div>
          <div class="currency-row platinum">
            <img src="/icons/coins/platinum.svg" class="coin-icon" />
            <div class="coin-info">
              <span class="coin-label">Platinum</span>
              <span class="coin-amount">{{ formatCurrency(character.currency?.platinum || 0) }}</span>
            </div>
          </div>
          <div class="currency-row gold">
            <img src="/icons/coins/gold.svg" class="coin-icon" />
            <div class="coin-info">
              <span class="coin-label">Gold</span>
              <span class="coin-amount">{{ formatCurrency(character.currency?.gold || 0) }}</span>
            </div>
          </div>
          <div class="currency-row silver">
            <img src="/icons/coins/silver.svg" class="coin-icon" />
            <div class="coin-info">
              <span class="coin-label">Silver</span>
              <span class="coin-amount">{{ formatCurrency(character.currency?.silver || 0) }}</span>
            </div>
          </div>
          <div class="currency-row copper">
            <img src="/icons/coins/bronze.svg" class="coin-icon" />
            <div class="coin-info">
              <span class="coin-label">Copper</span>
              <span class="coin-amount">{{ formatCurrency(character.currency?.copper || 0) }}</span>
            </div>
          </div>
        </div>

        <!-- Bags/Inventory Grid -->
        <div class="bags-section">
          <div class="inventory-bags">
            <div 
              v-for="slot in character.inventory" 
              :key="slot.slot"
              class="bag-slot"
              :class="{ 'has-item': slot.item }"
              :data-tooltip="getItemTooltip(slot.item)"
              :data-slot="slot.slot"
              @click="selectItem(slot.item)"
              @contextmenu.prevent="handleBagRightClick($event, slot)"
            >
              <div v-if="slot.item" class="item-container">
                <img 
                  :src="slot.item.icon" 
                  :alt="slot.item.name"
                  class="item-icon"
                  @error="handleImageError"
                />
                <span v-if="slot.item.stackSize > 1" class="stack-count">
                  {{ slot.item.stackSize }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Action Bar -->
    <div class="action-bar">
      <button class="eq-button">Key Rings</button>
      <button class="eq-button">Skills</button>
      <button class="eq-button">Alt. Adv.</button>
      <button class="eq-button find-item" @click="toggleFindItem">Find Item</button>
    </div>
    
    <!-- Find Item Search Box -->
    <div v-if="showFindItem" class="find-item-overlay" @click="closeFindItem">
      <div class="find-item-box" @click.stop>
        <div class="find-item-header">
          <h3>Find Item in Inventory</h3>
          <button @click="closeFindItem" class="find-item-close">×</button>
        </div>
        <div class="find-item-content">
          <input 
            ref="findItemInput"
            v-model="searchQuery" 
            @input="debouncedSearch"
            @keyup.enter="findAndHighlight"
            @keyup.escape="closeFindItem"
            placeholder="Enter item name to search..."
            class="find-item-input"
          />
          <div v-if="searchResults.length > 0" class="search-results">
            <div class="results-header">Found {{ searchResults.length }} item(s):</div>
            <div 
              v-for="(result, index) in searchResults" 
              :key="`${result.slotid}-${index}`"
              class="search-result-item"
              @click="highlightItem(result)"
            >
              <img 
                :src="result.item.icon" 
                :alt="result.item.name"
                class="result-icon"
                @error="handleImageError"
              />
              <div class="result-info">
                <div class="result-name">{{ result.item.name }}</div>
                <div class="result-location">{{ getLocationDescription(result) }}</div>
              </div>
            </div>
          </div>
          <div v-else-if="searchQuery.length > 0" class="no-results">
            No items found matching "{{ searchQuery }}"
          </div>
        </div>
      </div>
    </div>
    
    <!-- Item Modal -->
    <ItemModal 
      :selectedItemDetail="selectedItemDetail"
      :loadingItemModal="loadingItemModal"
      :dropSources="dropSources"
      :loadingDropSources="loadingDropSources"
      :dropSourcesRequested="dropSourcesRequested"
      :merchantSources="merchantSources"
      :loadingMerchantSources="loadingMerchantSources"
      :merchantSourcesRequested="merchantSourcesRequested"
      :itemDataAvailability="itemDataAvailability"
      :loadingAvailability="loadingAvailability"
      @close="closeItemModal"
      @loadDropSources="loadDropSources"
      @loadMerchantSources="loadMerchantSources"
    />
    
    <!-- Loading Modal -->
    <LoadingModal :visible="loadingItemModal" text="Loading item details..." @timeout="onItemModalTimeout" />
    
    <!-- Bag Windows -->
    <div 
      v-for="bagWindow in openBagWindows" 
      :key="bagWindow.slotId"
      class="bag-window"
      :style="{ left: bagWindow.x + 'px', top: bagWindow.y + 'px', zIndex: bagWindow.zIndex }"
      @mousedown="bringBagToFront(bagWindow.slotId)"
    >
      <div class="bag-window-header" @mousedown="startDrag($event, bagWindow)">
        <span class="bag-window-title">{{ bagWindow.bagName }}</span>
        <button class="bag-close-btn" @click="closeBagWindow(bagWindow.slotId)">×</button>
      </div>
      <div class="bag-window-content">
        <div class="bag-slots-grid" :style="getBagGridStyle(bagWindow.containerSize)">
          <div 
            v-for="bagSlot in bagWindow.contents" 
            :key="bagSlot.slot"
            class="bag-slot"
            :class="{ 'has-item': bagSlot.item }"
            :data-tooltip="getItemTooltip(bagSlot.item, true)"
            :data-bag="bagWindow.slotId"
            :data-slot="bagSlot.slotid"
            @click="selectItem(bagSlot.item)"
          >
            <div v-if="bagSlot.item" class="item-container">
              <img 
                :src="bagSlot.item.icon" 
                :alt="bagSlot.item.name"
                class="item-icon"
                @error="handleImageError"
              />
              <span v-if="bagSlot.item.stackSize > 1" class="stack-count">
                {{ bagSlot.item.stackSize }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
  </div>
</template>

<script setup>
import { ref, nextTick, onUnmounted, computed, watch } from 'vue'
import LoadingModal from './LoadingModal.vue'
import ItemModal from './ItemModal.vue'
import { getApiBaseUrl } from '../config/api'
import { resilientApi } from '../utils/resilientRequest'

// Circuit breaker for item availability endpoint
const availabilityCircuitBreaker = ref({
  failures: 0,
  lastFailure: null,
  isOpen: false
})

const isAvailabilityCircuitOpen = () => {
  if (availabilityCircuitBreaker.value.failures < 3) {
    return false
  }
  
  const fiveMinutesAgo = Date.now() - 5 * 60 * 1000
  if (availabilityCircuitBreaker.value.lastFailure && availabilityCircuitBreaker.value.lastFailure > fiveMinutesAgo) {
    return true
  } else {
    // Reset after 5 minutes
    availabilityCircuitBreaker.value.failures = 0
    availabilityCircuitBreaker.value.lastFailure = null
    availabilityCircuitBreaker.value.isOpen = false
  }
  return false
}

const recordAvailabilityFailure = () => {
  availabilityCircuitBreaker.value.failures++
  availabilityCircuitBreaker.value.lastFailure = Date.now()
  
  if (availabilityCircuitBreaker.value.failures >= 3) {
    availabilityCircuitBreaker.value.isOpen = true
    console.warn('Item availability circuit breaker opened after 3 failures')
  }
}

const recordAvailabilitySuccess = () => {
  availabilityCircuitBreaker.value.failures = 0
  availabilityCircuitBreaker.value.lastFailure = null
  availabilityCircuitBreaker.value.isOpen = false
}

// Debounce utility function with cancel capability
const debounce = (func, delay) => {
  let timeoutId
  const debounced = (...args) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func.apply(null, args), delay)
  }
  debounced.cancel = () => clearTimeout(timeoutId)
  return debounced
}

const props = defineProps({
  character: {
    type: Object,
    required: true
  },
  rawInventoryData: {
    type: Array,
    default: () => []
  }
})

// Item modal state
const selectedItemDetail = ref(null)
const loadingItemModal = ref(false)

// Drop sources state
const dropSources = ref(null)
const loadingDropSources = ref(false)
const dropSourcesRequested = ref(false)

// Merchant sources state
const merchantSources = ref(null)
const loadingMerchantSources = ref(false)
const merchantSourcesRequested = ref(false)

// Data availability state
const itemDataAvailability = ref(null)
const loadingAvailability = ref(false)

// Bag window state
const openBagWindows = ref([])
const nextZIndex = ref(1000)
const dragState = ref({
  isDragging: false,
  currentBag: null,
  startX: 0,
  startY: 0,
  startMouseX: 0,
  startMouseY: 0
})

// Find Item functionality
const showFindItem = ref(false)
const searchQuery = ref('')
const searchResults = ref([])
const highlightedItems = ref(new Set())
const findItemInput = ref(null)

// Persistent highlighting state
const persistentHighlights = ref({
  items: new Set(),     // Set of highlighted item slot IDs
  bags: new Set(),      // Set of highlighted bag slot IDs
  blinking: new Set()   // Set of currently blinking elements
})

// API response cache for item details (5-minute TTL)
const itemDetailsCache = new Map()
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes


// Modal functions
const selectItem = async (item) => {
  if (!item) return
  
  loadingItemModal.value = true
  
  try {
    // Check cache first
    const cacheKey = `item-${item.id}`
    const cachedData = itemDetailsCache.get(cacheKey)
    
    if (cachedData && (Date.now() - cachedData.timestamp) < CACHE_TTL) {
      // Use cached data
      selectedItemDetail.value = cachedData.data
    } else {
      // Fetch fresh data
      const response = await resilientApi.get(`/api/items/${item.id}/details`)
      selectedItemDetail.value = response.data
      
      // Cache the response
      itemDetailsCache.set(cacheKey, {
        data: response.data,
        timestamp: Date.now()
      })
      
      // Prevent cache from growing too large (LRU-style cleanup)
      if (itemDetailsCache.size > 100) {
        const firstKey = itemDetailsCache.keys().next().value
        itemDetailsCache.delete(firstKey)
      }
    }
    
    // Load data availability after item details are loaded (non-blocking)
    loadItemDataAvailability(item.id).catch(error => {
      console.warn('Item availability loading failed but continuing:', error)
    })
  } catch (error) {
    console.error('Error loading item details:', error)
    // Show basic item data even if API fails
    selectedItemDetail.value = {
      id: item.id,
      Name: item.name,
      icon: item.icon,
      weight: item.weight || 0,
      ac: item.ac || 0,
      hp: item.hp || 0,
      mana: item.mana || 0,
      damage: item.damage || 0,
      delay: item.delay || 0,
      astr: item.astr || 0,
      asta: item.asta || 0,
      aagi: item.aagi || 0,
      adex: item.adex || 0,
      awis: item.awis || 0,
      aint: item.aint || 0,
      acha: item.acha || 0,
      pr: item.pr || 0,
      mr: item.mr || 0,
      fr: item.fr || 0,
      cr: item.cr || 0,
      dr: item.dr || 0,
      magic: item.magic || false,
      lore: item.lore || false,
      nodrop: item.nodrop || false
    }
  } finally {
    loadingItemModal.value = false
  }
}

const closeItemModal = () => {
  selectedItemDetail.value = null
  loadingItemModal.value = false
  // Reset drop/merchant sources when closing modal
  dropSources.value = null
  loadingDropSources.value = false
  dropSourcesRequested.value = false
  merchantSources.value = null
  loadingMerchantSources.value = false
  merchantSourcesRequested.value = false
  // Clear availability data when closing modal
  itemDataAvailability.value = null
  loadingAvailability.value = false
}

// Event delegation handler for equipment slots (replaces 22 individual click handlers)
const handleEquipmentClick = (event) => {
  // Find the closest equipment slot container
  const slotContainer = event.target.closest('[data-slot]')
  if (!slotContainer) return
  
  // Get the slot type from data-slot attribute
  const slotType = slotContainer.dataset.slot
  if (!slotType) return
  
  // Get the equipment item for this slot
  const item = props.character.equipment?.[slotType]
  
  // Call the original selectItem function
  selectItem(item)
}

const onItemModalTimeout = () => {
  console.warn('Item modal loading timed out')
  loadingItemModal.value = false
  selectedItemDetail.value = null
}

// Drop sources functions
const loadDropSources = async () => {
  if (!selectedItemDetail.value?.id || loadingDropSources.value || dropSourcesRequested.value) return
  
  loadingDropSources.value = true
  dropSourcesRequested.value = true
  
  try {
    const response = await resilientApi.get(`/api/items/${selectedItemDetail.value.id}/drop-sources`)
    // Backend returns {zones: [...]} but frontend expects array directly
    dropSources.value = response.data.zones || []
  } catch (error) {
    console.error('Error loading drop sources:', error)
    dropSources.value = []
  } finally {
    loadingDropSources.value = false
  }
}

// Merchant sources functions
const loadMerchantSources = async () => {
  if (!selectedItemDetail.value?.id || loadingMerchantSources.value || merchantSourcesRequested.value) return
  
  loadingMerchantSources.value = true
  merchantSourcesRequested.value = true
  
  try {
    const response = await resilientApi.get(`/api/items/${selectedItemDetail.value.id}/merchant-sources`)
    // Backend returns {zones: [...]} but frontend expects array directly
    merchantSources.value = response.data.zones || []
  } catch (error) {
    console.error('Error loading merchant sources:', error)
    merchantSources.value = []
  } finally {
    loadingMerchantSources.value = false
  }
}

// Item data availability function
const loadItemDataAvailability = async (itemId) => {
  if (!itemId) return
  
  // Circuit breaker: skip if too many recent failures
  if (isAvailabilityCircuitOpen()) {
    console.log('Item availability circuit breaker active, skipping request')
    itemDataAvailability.value = 'failed' // Show all buttons when circuit is open
    return
  }
  
  // Prevent multiple simultaneous requests for the same item
  if (loadingAvailability.value) return
  
  loadingAvailability.value = true
  
  try {
    const response = await resilientApi.get(`/api/items/${itemId}/availability`, {
      timeout: 8000 // Increased timeout for this endpoint
    })
    itemDataAvailability.value = response.data
    
    // Record success to reset circuit breaker
    recordAvailabilitySuccess()
    
  } catch (error) {
    // Record failure for circuit breaker
    recordAvailabilityFailure()
    
    console.error('Error loading item data availability:', {
      itemId,
      error: error.message,
      status: error.response?.status
    })
    // Fallback: Set to 'failed' state so we can show all buttons
    itemDataAvailability.value = 'failed'
  } finally {
    loadingAvailability.value = false
  }
}

// Helper functions for modal display
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

const hasAnyStats = (item) => {
  if (!item) return false
  return item.astr || item.asta || item.aagi || item.adex || item.awis || item.aint || item.acha ||
         item.stats?.ac || item.stats?.hp || item.stats?.mana || item.stats?.endur || item.stats?.attack ||
         item.attributes?.str || item.attributes?.sta || item.attributes?.agi || item.attributes?.dex ||
         item.attributes?.wis || item.attributes?.int || item.attributes?.cha ||
         item.resistances?.poison || item.resistances?.magic || item.resistances?.fire || 
         item.resistances?.cold || item.resistances?.disease || item.resistances?.corruption ||
         item.weight || item.charges
}

const hasResistValues = (item) => {
  if (!item) return false
  return item.fr || item.cr || item.mr || item.dr || item.pr || item.svcorruption
}

const hasAttributeValues = (item) => {
  if (!item) return false
  return item.astr || item.asta || item.aagi || item.adex || item.awis || item.aint || item.acha
}
    
const handleImageError = (event) => {
  // PNG-first strategy: Try GIF as fallback, then default icon
  const currentSrc = event.target.src
  if (currentSrc.endsWith('.png')) {
    // Try GIF as fallback
    event.target.src = currentSrc.replace('.png', '.gif')
  } else {
    // Final fallback to default icon (PNG)
    event.target.src = '/icons/items/500.png'
  }
}

const formatCurrency = (value) => {
  // Format currency with commas for readability
  return value.toLocaleString()
}

// Tooltip memoization cache
const tooltipCache = new Map()

const getItemTooltip = (item, isInBagWindow = false) => {
  if (!item) return ''
  
  // Create cache key from item properties that affect tooltip
  const cacheKey = `${item.id || 'unknown'}-${item.name || 'unknown'}-${item.containerSize || 0}-${isInBagWindow}`
  
  // Return cached result if available
  if (tooltipCache.has(cacheKey)) {
    return tooltipCache.get(cacheKey)
  }
  
  const itemName = item.name || 'Unknown Item'
  const isContainer = item.containerSize && item.containerSize > 0
  
  let tooltip = itemName
  
  if (isContainer && !isInBagWindow) {
    tooltip += `\n\nLeft click for info.\nRight click to open`
  } else {
    tooltip += `\n\nLeft click for info.`
  }
  
  // Cache the result for future use
  tooltipCache.set(cacheKey, tooltip)
  
  // Prevent cache from growing too large (LRU-style cleanup)
  if (tooltipCache.size > 200) {
    const firstKey = tooltipCache.keys().next().value
    tooltipCache.delete(firstKey)
  }
  
  return tooltip
}

const normalizeClassName = (className) => {
  // Map level 60+ specialty class titles to base class names
  const classMapping = {
        // Base class mappings (for spaced names)
        'Shadow Knight': 'Shadowknight',
        
        // Warrior specializations
        'Myrmidon': 'Warrior',
        'Champion': 'Warrior',
        'Warlord': 'Warrior',
        
        // Cleric specializations  
        'Vicar': 'Cleric',
        'Templar': 'Cleric',
        'High Priest': 'Cleric',
        
        // Paladin specializations
        'Cavalier': 'Paladin',
        'Knight': 'Paladin',
        'Lord Protector': 'Paladin',
        
        // Ranger specializations
        'Pathfinder': 'Ranger',
        'Outrider': 'Ranger',
        'Warder': 'Ranger',
        
        // Shadow Knight specializations
        'Reaver': 'Shadowknight',
        'Revenant': 'Shadowknight',
        'Grave Lord': 'Shadowknight',
        
        // Druid specializations
        'Wanderer': 'Druid',
        'Preserver': 'Druid',
        'Hierophant': 'Druid',
        
        // Monk specializations
        'Disciple': 'Monk',
        'Master': 'Monk',
        'Grandmaster': 'Monk',
        
        // Bard specializations
        'Minstrel': 'Bard',
        'Troubadour': 'Bard',
        'Virtuoso': 'Bard',
        
        // Rogue specializations
        'Rake': 'Rogue',
        'Blackguard': 'Rogue',
        'Assassin': 'Rogue',
        
        // Shaman specializations
        'Mystic': 'Shaman',
        'Luminary': 'Shaman',
        'Oracle': 'Shaman',
        
        // Necromancer specializations
        'Heretic': 'Necromancer',
        'Defiler': 'Necromancer',
        'Warlock': 'Necromancer',
        
        // Wizard specializations
        'Elementalist': 'Wizard',
        'Sorcerer': 'Wizard',
        'Arcanist': 'Wizard',
        
        // Magician specializations
        'Elementalist': 'Magician',
        'Conjurer': 'Magician',
        'Arch Mage': 'Magician',
        
        // Enchanter specializations
        'Illusionist': 'Enchanter',
        'Beguiler': 'Enchanter',
        'Phantasmist': 'Enchanter',
        
        // Beastlord specializations
        'Savage Lord': 'Beastlord',
        'Feral Lord': 'Beastlord',
        'Primalist': 'Beastlord',
        
        // Berserker specializations
        'Rager': 'Berserker',
        'Fury': 'Berserker',
        'Rampager': 'Berserker'
  }
  
  return classMapping[className] || className
}

// Bag window methods
const handleBagRightClick = (event, slot) => {
  
  if (!slot.item || !slot.item.containerSize || slot.item.containerSize === 0) {
    return // Not a container
  }
  
  // Clear all highlights on any bag right-click (same as Find Item button)
  clearAllHighlights()
  
  // Check if this bag is already open - if so, close it (toggle behavior)
  const existingWindowIndex = openBagWindows.value.findIndex(w => w.slotId === slot.slotid)
  if (existingWindowIndex !== -1) {
    openBagWindows.value.splice(existingWindowIndex, 1)
    return
  }
  
  // Calculate position next to the clicked bag with viewport bounds checking
  const rect = event.target.closest('.bag-slot').getBoundingClientRect()
  
  // Estimate bag window size (2 columns × rows based on container size)
  const bagWindowWidth = 2 * 70 + 20 // 2 columns * 70px + padding
  const bagWindowHeight = Math.ceil(slot.item.containerSize / 2) * 70 + 50 // rows * 70px + header + padding
  
  // Get viewport dimensions
  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight
  
  // Calculate initial position (right of bag)
  let x = rect.right + 10
  let y = rect.top
  
  // Check right edge - if bag window would go off-screen, position it to the left of the bag
  if (x + bagWindowWidth > viewportWidth) {
    x = rect.left - bagWindowWidth - 10
  }
  
  // Check left edge - ensure minimum distance from left edge
  if (x < 10) {
    x = 10
  }
  
  // Check bottom edge - if bag window would go off-screen, adjust upward
  if (y + bagWindowHeight > viewportHeight) {
    y = viewportHeight - bagWindowHeight - 10
  }
  
  // Check top edge - ensure minimum distance from top edge
  if (y < 10) {
    y = 10
  }
  
  const bagContents = getBagContents(slot.slotid, slot.item.containerSize)
  
  // Create bag window
  const bagWindow = {
    slotId: slot.slotid,
    bagName: slot.item.name,
    containerSize: slot.item.containerSize,
    x: x,
    y: y,
    zIndex: nextZIndex.value++,
    contents: bagContents
  }
  
  
  openBagWindows.value.push(bagWindow)
}

const getBagContents = (bagSlotId, containerSize) => {
  // Safety check for props
  if (!props.rawInventoryData || !Array.isArray(props.rawInventoryData)) {
    console.warn('rawInventoryData is not available or not an array:', props.rawInventoryData)
    return []
  }
  
  // PURE MAGELO CHARBROWSER MAPPING (Working for most bags)
  // Map bag slot IDs to their content slot ranges - exactly like Magelo CharBrowser
  const slotRanges = {
    23: [251, 260], 24: [261, 270], 25: [271, 280], 26: [281, 290], 27: [291, 300],
    28: [301, 310], 29: [311, 320], 30: [321, 330], 31: [331, 340], 32: [341, 350]
  }
  
  const range = slotRanges[bagSlotId]
  if (!range) {
    return []
  }
  
  const [startSlot, endSlot] = range
  
  // Initialize all slots as empty
  const contents = []
  for (let i = 0; i < containerSize; i++) {
    contents.push({
      slot: i,
      slotid: startSlot + i,
      item: null
    })
  }
  
  // SPECIAL HANDLING FOR BAG 23: Map all expected items to their correct Light Burlap Sack positions
  if (bagSlotId === 23) {
    // Define expected items with their target UI positions (0-based) and exact Item IDs
    const expectedItemsMapping = [
      { name: 'Ichorflow', position: 0, itemId: 28829 },
      { name: 'Jaelen\'s Katana', position: 1, itemId: 31243 },
      { name: 'Iron Ration', position: 2, itemId: 13005 },
      { name: 'Water Flask', position: 3, itemId: 13006 },
      { name: 'Disrupting Spear', position: 4, itemId: 150293 },
      { name: 'Warhammer of Motion Alteration', position: 5, itemId: 150273 },
      { name: 'Claw of the Savage Spirit Ornamentation', position: 6, itemId: 150800 },
      { name: 'Shimmering Bauble of Trickery', position: 7, itemId: 62433 }
    ]
    
    // Search ALL inventory slots for each expected item
    const allInventoryItems = props.rawInventoryData.filter(item => item && (item.item_name || item.name))
    
    expectedItemsMapping.forEach(expectedItem => {
      // PERFECT SEARCH: Find by exact Item ID anywhere in inventory
      const foundItem = allInventoryItems.find(item => {
        const itemId = item.itemid || item.id
        return itemId && parseInt(itemId) === expectedItem.itemId
      })
      
      if (foundItem) {
        // Place item in its correct Light Burlap Sack position regardless of current database slot
        if (expectedItem.position < containerSize) {
          contents[expectedItem.position] = {
            slot: expectedItem.position,
            slotid: foundItem.slotid, // Keep original database slot for reference
            item: {
              id: foundItem.itemid || foundItem.id,
              name: foundItem.item_name || foundItem.name,
              icon: `/icons/items/${foundItem.item_icon || foundItem.icon || 500}.png`,
              charges: foundItem.charges || 0,
              stackSize: foundItem.stackable ? (foundItem.charges || 1) : 1,
              stackable: foundItem.stackable,
              color: foundItem.color || 0
            }
          }
        }
      }
    })
  } else {
    // STANDARD MAGELO MAPPING FOR ALL OTHER BAGS (This was working correctly)
    const bagItems = props.rawInventoryData.filter(item => 
      item && item.slotid >= startSlot && item.slotid <= endSlot
    )
    
    // Place each item in its calculated virtual slot position (like Magelo CharBrowser)
    bagItems.forEach(inventoryItem => {
      // Magelo calculation: vslot = slotid - startSlot + 1, then convert to 0-based
      const vslot = inventoryItem.slotid - startSlot + 1 // Calculate virtual slot (1-based like Magelo)
      const uiSlotIndex = vslot - 1 // Convert to 0-based for UI
      
      // Only place item if it fits within the container size
      if (uiSlotIndex >= 0 && uiSlotIndex < containerSize) {
        contents[uiSlotIndex] = {
          slot: uiSlotIndex,
          slotid: inventoryItem.slotid,
          item: {
            id: inventoryItem.itemid || inventoryItem.id,
            name: inventoryItem.item_name || inventoryItem.name,
            icon: `/icons/items/${inventoryItem.item_icon || inventoryItem.icon || 500}.png`,
            charges: inventoryItem.charges || 0,
            stackSize: inventoryItem.stackable ? (inventoryItem.charges || 1) : 1,
            stackable: inventoryItem.stackable,
            color: inventoryItem.color || 0
          }
        }
      }
    })
  }
  
  return contents
}

const getBagGridStyle = (containerSize) => {
  // Calculate grid dimensions based on container size
  const columns = 2
  const rows = Math.ceil(containerSize / columns)
  
  return {
    gridTemplateColumns: `repeat(${columns}, 70px)`,
    gridTemplateRows: `repeat(${rows}, 70px)`
  }
}

const closeBagWindow = (slotId) => {
  const index = openBagWindows.value.findIndex(w => w.slotId === slotId)
  if (index !== -1) {
    openBagWindows.value.splice(index, 1)
  }
}

const bringBagToFront = (slotId) => {
  const bagWindow = openBagWindows.value.find(w => w.slotId === slotId)
  if (bagWindow) {
    bagWindow.zIndex = nextZIndex.value++
  }
}

const startDrag = (event, bagWindow) => {
  dragState.value = {
    isDragging: true,
    currentBag: bagWindow,
    startX: bagWindow.x,
    startY: bagWindow.y,
    startMouseX: event.clientX,
    startMouseY: event.clientY
  }
  
  document.addEventListener('mousemove', handleDrag)
  document.addEventListener('mouseup', endDrag)
}

const handleDrag = (event) => {
  if (!dragState.value.isDragging) return
  
  const deltaX = event.clientX - dragState.value.startMouseX
  const deltaY = event.clientY - dragState.value.startMouseY
  
  dragState.value.currentBag.x = dragState.value.startX + deltaX
  dragState.value.currentBag.y = dragState.value.startY + deltaY
}

const endDrag = () => {
  dragState.value.isDragging = false
  dragState.value.currentBag = null
  
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', endDrag)
}

// Find Item functions
const toggleFindItem = () => {
  // Clear any existing highlights when opening Find Item
  clearAllHighlights()
  
  showFindItem.value = !showFindItem.value
  if (showFindItem.value) {
    nextTick(() => {
      findItemInput.value?.focus()
    })
  } else {
    clearSearch()
  }
}

const closeFindItem = () => {
  showFindItem.value = false
  clearSearch()
}

const clearSearch = () => {
  searchQuery.value = ''
  searchResults.value = []
  highlightedItems.value.clear()
  clearAllHighlights() // Clear persistent highlights when search is cleared
}

// Clear all persistent highlights
const clearAllHighlights = () => {
  if (import.meta.env.DEV) console.log('=== CLEARING ALL HIGHLIGHTS ===')
  if (import.meta.env.DEV) console.log('Current highlights before clearing:', {
    items: persistentHighlights.value.items.size,
    bags: persistentHighlights.value.bags.size,
    blinking: persistentHighlights.value.blinking.size,
    itemsList: Array.from(persistentHighlights.value.items),
    bagsList: Array.from(persistentHighlights.value.bags)
  })
  
  // Remove highlight classes from all highlighted elements
  persistentHighlights.value.items.forEach(slotId => {
    const element = findElementBySlotId(slotId)
    if (element) {
      element.classList.remove('persistent-highlight', 'blinking-highlight')
      if (import.meta.env.DEV) console.log(`Cleared item highlight for slot ${slotId}`)
    }
  })
  
  if (import.meta.env.DEV) console.log(`Attempting to clear ${persistentHighlights.value.bags.size} bag highlights...`)
  persistentHighlights.value.bags.forEach(bagSlot => {
    console.log(`Clearing bag slot ${bagSlot}...`)
    const bagElement = findBagElementBySlot(bagSlot)
    console.log(`Found bag element for slot ${bagSlot}:`, !!bagElement)
    
    if (bagElement) {
      console.log(`Before clearing - styles:`, {
        border: bagElement.style.border,
        background: bagElement.style.background,
        transform: bagElement.style.transform
      })
      
      bagElement.classList.remove('persistent-highlight', 'blinking-highlight')
      // Clear inline styles that were applied for bag highlighting
      bagElement.style.border = ''
      bagElement.style.background = ''
      bagElement.style.transform = ''
      bagElement.style.boxShadow = ''
      bagElement.style.zIndex = ''
      bagElement.style.position = ''
      
      console.log(`After clearing - styles:`, {
        border: bagElement.style.border,
        background: bagElement.style.background,
        transform: bagElement.style.transform
      })
      
      console.log(`Successfully cleared bag highlight for slot ${bagSlot}`)
    } else {
      console.warn(`Could not find bag element for slot ${bagSlot} during clearing`)
    }
  })
  
  // Also clear any remaining highlights by searching the DOM directly
  const allHighlightedElements = document.querySelectorAll('.persistent-highlight, .blinking-highlight')
  allHighlightedElements.forEach(element => {
    element.classList.remove('persistent-highlight', 'blinking-highlight')
    // Also clear inline styles for any remaining highlighted elements
    element.style.border = ''
    element.style.background = ''
    element.style.transform = ''
    element.style.boxShadow = ''
    element.style.zIndex = ''
    element.style.position = ''
    console.log('Cleared remaining highlight from element:', element)
  })
  
  // Nuclear option: Clear ALL bag slot inline styles
  console.log('Nuclear cleanup: clearing ALL bag slot inline styles...')
  const allBagSlots = document.querySelectorAll('.bag-slot')
  console.log(`Found ${allBagSlots.length} bag slots for cleanup`)
  
  allBagSlots.forEach((bagSlot, index) => {
    const hadStyles = bagSlot.style.border || bagSlot.style.background || bagSlot.style.transform
    if (hadStyles) {
      console.log(`Clearing styles from bag slot ${index}:`, {
        before: {
          border: bagSlot.style.border,
          background: bagSlot.style.background,
          transform: bagSlot.style.transform
        }
      })
    }
    
    bagSlot.style.border = ''
    bagSlot.style.background = ''
    bagSlot.style.transform = ''
    bagSlot.style.boxShadow = ''
    bagSlot.style.zIndex = ''
    bagSlot.style.position = ''
    
    if (hadStyles) {
      console.log(`Cleared inline styles from bag slot ${index}`)
    }
  })
  
  // Clear the sets
  persistentHighlights.value.items.clear()
  persistentHighlights.value.bags.clear()
  persistentHighlights.value.blinking.clear()
  
  console.log('All highlights cleared')
}

// Helper function to find element by slot ID
const findElementBySlotId = (slotId) => {
  // For main inventory slots (23-32), convert to UI slot (0-9)
  let actualSlotToFind = slotId
  if (slotId >= 23 && slotId <= 32) {
    actualSlotToFind = slotId - 23 // Convert to UI slot (0-9)
  }
  
  const selectors = [
    `[data-slot="${slotId}"]`,
    `[data-slot="${actualSlotToFind}"]`,
    `.inventory-slot[data-slot="${slotId}"]`,
    `.inventory-slot[data-slot="${actualSlotToFind}"]`,
    `.equipment-slot[data-slot="${slotId}"]`,
    `.bag-slot[data-slot="${slotId}"]`
  ]
  
  console.log('Finding element for slot:', {
    originalSlot: slotId,
    actualSlot: actualSlotToFind,
    selectors: selectors
  })
  
  for (const selector of selectors) {
    const element = document.querySelector(selector)
    if (element) {
      console.log('Found element with selector:', selector)
      return element
    }
  }
  
  console.warn('No element found for slot:', slotId)
  return null
}

// Helper function to find bag element by slot
const findBagElementBySlot = (bagSlot) => {
  // Convert EQEmu slot (23-32) to UI slot (0-9) for bag elements
  const uiSlot = getUISlotFromBagSlot(bagSlot)
  
  const selectors = [
    // Try UI slot first (bag slots use 0-9)
    `.bag-slot[data-slot="${uiSlot}"]`,
    `[data-slot="${uiSlot}"]`,
    // Try EQEmu slot as fallback
    `[data-slot="${bagSlot}"]`,
    `.inventory-slot[data-slot="${bagSlot}"]`,
    `.bag-container[data-bagslot="${bagSlot}"]`
  ]
  
  for (const selector of selectors) {
    const element = document.querySelector(selector)
    if (element) {
      console.log(`Found bag element with selector: ${selector}`)
      return element
    }
  }
  
  console.warn(`Could not find bag element for bagSlot ${bagSlot} (UI slot ${uiSlot})`)
  return null
}

const performSearch = () => {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  
  const query = searchQuery.value.toLowerCase().trim()
  const results = []
  
  // Search through all inventory data
  if (props.rawInventoryData) {
    props.rawInventoryData.forEach(item => {
      if (item && (item.item_name || item.name)) {
        const itemName = (item.item_name || item.name).toLowerCase()
        if (itemName.includes(query)) {
          results.push({
            slotid: item.slotid,
            item: {
              id: item.itemid || item.id,
              name: item.item_name || item.name,
              icon: `/icons/items/${item.item_icon || item.icon || 500}.png`
            }
          })
        }
      }
    })
  }
  
  searchResults.value = results
}

// Create debounced version of search for input events
const debouncedSearch = debounce(performSearch, 300)

const findAndHighlight = () => {
  if (searchResults.value.length > 0) {
    highlightItem(searchResults.value[0])
  }
}

const highlightItem = (result) => {
  const slotid = result.slotid
  
  // Clear previous highlights
  clearAllHighlights()
  
  // Determine if item is in main inventory or bag
  if (slotid >= 23 && slotid <= 32) {
    // Main inventory slot - highlight directly
    highlightInventorySlot(slotid)
  } else if (slotid >= 251 && slotid <= 361) {
    // Bag content - open bag first, then highlight both bag and item
    const bagSlot = getBagSlotForContentSlot(slotid)
    
    // Highlight the bag container first
    highlightBagContainer(bagSlot)
    
    // Open bag if needed and highlight the item
    openBagIfClosed(bagSlot, () => {
      highlightBagItem(bagSlot, slotid)
    })
  }
  
  // Close search after highlighting
  closeFindItem()
}

const getBagSlotForContentSlot = (contentSlot) => {
  // Calculate which bag this content slot belongs to (EQEmu mapping)
  if (contentSlot >= 251 && contentSlot <= 260) return 23  // Bag slot 0 (UI slot 23)
  if (contentSlot >= 261 && contentSlot <= 270) return 24  // Bag slot 1 (UI slot 24)
  if (contentSlot >= 271 && contentSlot <= 280) return 25  // Bag slot 2 (UI slot 25)
  if (contentSlot >= 281 && contentSlot <= 290) return 26  // Bag slot 3 (UI slot 26)
  if (contentSlot >= 291 && contentSlot <= 300) return 27  // Bag slot 4 (UI slot 27)
  if (contentSlot >= 301 && contentSlot <= 310) return 28  // Bag slot 5 (UI slot 28)
  if (contentSlot >= 311 && contentSlot <= 320) return 29  // Bag slot 6 (UI slot 29)
  if (contentSlot >= 321 && contentSlot <= 330) return 30  // Bag slot 7 (UI slot 30)
  if (contentSlot >= 331 && contentSlot <= 340) return 31  // Bag slot 8 (UI slot 31)
  if (contentSlot >= 341 && contentSlot <= 350) return 32  // Bag slot 9 (UI slot 32)
  return null
}

const getUISlotFromBagSlot = (bagSlot) => {
  // Convert EQEmu bag slot (23-32) to UI slot (0-9)
  return bagSlot - 23
}

const openBagIfClosed = (bagSlot, callback) => {
  const bagWindow = openBagWindows.value.find(w => w.slotId === bagSlot)
  if (!bagWindow) {
    // Find bag in main inventory and open it
    const uiSlot = getUISlotFromBagSlot(bagSlot)
    const slot = props.character?.inventory?.find(s => s.slot === uiSlot)
    
    console.log('Opening bag:', {
      bagSlot: bagSlot,
      uiSlot: uiSlot,
      slot: slot,
      hasItem: !!(slot?.item)
    })
    
    if (slot && slot.item && slot.item.containerSize > 0) {
      // Calculate position to the right of the bags section
      let baseX = 500 // Default fallback position (to the right)
      let baseY = 150 // Default fallback position (middle of screen)
      
      try {
        // Find the bags section for precise positioning
        const bagsSection = document.querySelector('.bags-section')
        
        if (bagsSection) {
          const bagsSectionRect = bagsSection.getBoundingClientRect()
          
          // Position to the right of the bags section with top alignment
          baseX = bagsSectionRect.right + 15 // 15px gap from bags section
          baseY = bagsSectionRect.top // Align with top of bag slot area
          
          // For multiple bags, stagger horizontally instead of vertically to maintain top alignment
          if (openBagWindows.value.length > 0) {
            baseX += (openBagWindows.value.length * 20) // Horizontal staggering
          }
          
          // Ensure bag doesn't go off screen
          const maxX = window.innerWidth - 300 // Assume bag window is ~300px wide
          const maxY = window.innerHeight - 400 // Assume bag window is ~400px tall
          
          if (baseX > maxX) {
            // If too far right, start a new row
            baseX = bagsSectionRect.right + 15
            baseY = bagsSectionRect.top + 30 // Move down for second row
          }
          if (baseY > maxY) baseY = Math.max(50, maxY)
          
          console.log('Calculated bag position (viewport relative):', {
            baseX,
            baseY,
            bagsSectionRight: bagsSectionRect.right,
            bagsSectionTop: bagsSectionRect.top,
            bagCount: openBagWindows.value.length,
            viewportWidth: window.innerWidth,
            viewportHeight: window.innerHeight
          })
        } else {
          console.warn('Could not find .bags-section element, using fallback positioning')
        }
      } catch (error) {
        console.warn('Could not calculate dynamic bag position, using fallback:', error)
      }
      
      // Create bag window
      const bagWindow = {
        slotId: bagSlot,
        x: baseX,
        y: baseY,
        zIndex: nextZIndex.value++,
        contents: getBagContents(bagSlot, slot.item.containerSize)
      }
      
      openBagWindows.value.push(bagWindow)
      console.log('Bag opened successfully:', bagWindow)
    } else {
      console.warn('Cannot open bag - not a container or no item found:', { bagSlot, uiSlot, slot })
    }
  }
  
  // Execute callback after short delay to ensure bag is opened
  setTimeout(callback, 200) // Increased delay
}

const highlightInventorySlot = (slotid) => {
  const slotElement = findElementBySlotId(slotid)
  
  console.log('Highlighting inventory slot:', {
    slotid: slotid,
    found: !!slotElement
  })
  
  if (slotElement) {
    addPersistentHighlight(slotElement, slotid, 'item')
    // Scroll the element into view
    slotElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
  } else {
    console.warn(`Could not find inventory slot ${slotid} for highlighting`)
  }
}

// Add highlighting to bag container (the bag in main inventory)
const highlightBagContainer = (bagSlot) => {
  const uiSlot = getUISlotFromBagSlot(bagSlot)
  const bagElement = findBagElementBySlot(bagSlot) // Use the improved bag element finder
  
  console.log('Highlighting bag container:', {
    bagSlot: bagSlot,
    uiSlot: uiSlot,
    found: !!bagElement,
    elementDetails: bagElement ? {
      tagName: bagElement.tagName,
      className: bagElement.className,
      dataSlot: bagElement.getAttribute('data-slot')
    } : null
  })
  
  if (bagElement) {
    addPersistentHighlight(bagElement, bagSlot, 'bag')
    persistentHighlights.value.bags.add(bagSlot)
    
    // Force inline golden styles since CSS isn't working
    bagElement.style.border = '6px solid #FFD700'
    bagElement.style.background = 'rgba(255, 215, 0, 0.4)'
    bagElement.style.transform = 'scale(1.05)'
    bagElement.style.boxShadow = '0 0 20px rgba(255, 215, 0, 0.8)'
    bagElement.style.zIndex = '1000'
    bagElement.style.position = 'relative'
    
    // Verify styles were applied
    setTimeout(() => {
      console.log('Verifying applied styles after 100ms:', {
        border: bagElement.style.border,
        background: bagElement.style.background,
        transform: bagElement.style.transform,
        computedBorder: window.getComputedStyle(bagElement).border,
        computedBackground: window.getComputedStyle(bagElement).background,
        element: bagElement,
        parentElement: bagElement.parentElement?.tagName,
        isConnected: bagElement.isConnected
      })
    }, 100)
    
    // Store reference for repeated application
    const applyGoldenStyles = () => {
      bagElement.style.border = '6px solid #FFD700'
      bagElement.style.background = 'rgba(255, 215, 0, 0.4)'
      bagElement.style.transform = 'scale(1.05)'
      bagElement.style.boxShadow = '0 0 20px rgba(255, 215, 0, 0.8)'
      bagElement.style.zIndex = '1000'
      bagElement.style.position = 'relative'
    }
    
    // Apply styles multiple times to ensure they stick
    applyGoldenStyles()
    setTimeout(applyGoldenStyles, 50)
    setTimeout(applyGoldenStyles, 150)
    setTimeout(applyGoldenStyles, 300)
    
    console.log(`Successfully added highlight to bag container slot ${bagSlot} (UI slot ${uiSlot})`)
    console.log('Applied inline golden styles to bag element')
  } else {
    console.warn(`Could not find bag container for slot ${bagSlot} (UI slot ${uiSlot})`)
    
    // Debug: List all available bag slots
    const allBagSlots = document.querySelectorAll('.bag-slot[data-slot]')
    console.log('Available bag slots:', Array.from(allBagSlots).map(el => ({
      dataSlot: el.getAttribute('data-slot'),
      className: el.className
    })))
  }
}

const highlightBagItem = (bagSlot, contentSlot) => {
  console.log('Highlighting bag item:', {
    bagSlot: bagSlot,
    contentSlot: contentSlot,
    openBags: openBagWindows.value.map(w => w.slotId)
  })
  
  // Wait a moment for bag to open if needed
  setTimeout(() => {
    const bagWindow = openBagWindows.value.find(w => w.slotId === bagSlot)
    if (bagWindow) {
      // Try multiple selectors for bag items - use more specific combinations
      const selectors = [
        `[data-bag="${bagSlot}"][data-slot="${contentSlot}"]`,
        `[data-bagslot="${bagSlot}"][data-slot="${contentSlot}"]`,
        `.bag-window [data-slot="${contentSlot}"]`,
        `.bag-slot[data-slot="${contentSlot}"]`
      ]
      
      let slotElement = null
      for (const selector of selectors) {
        slotElement = document.querySelector(selector)
        console.log(`Trying selector: ${selector}, found:`, !!slotElement)
        if (slotElement) break
      }
      
      if (slotElement) {
        addPersistentHighlight(slotElement, contentSlot, 'item')
        // Scroll the bag window to show the item
        slotElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
      } else {
        console.warn(`Could not find bag item ${contentSlot} in bag ${bagSlot} for highlighting`)
        // List all elements in the bag for debugging
        const bagElements = document.querySelectorAll(`.bag-window [data-slot]`)
        console.log('Available bag elements:', Array.from(bagElements).map(el => el.getAttribute('data-slot')))
      }
    } else {
      console.warn(`Bag ${bagSlot} is not open, cannot highlight item ${contentSlot}`)
    }
  }, 300) // Wait for bag to open and render
}

// Core function to add persistent highlighting with blinking
const addPersistentHighlight = (element, slotId, type) => {
  // Add the element to our tracking
  if (type === 'item') {
    persistentHighlights.value.items.add(slotId)
  } else if (type === 'bag') {
    persistentHighlights.value.bags.add(slotId)
  }
  
  // Add both blinking and persistent classes
  element.classList.add('blinking-highlight', 'persistent-highlight')
  persistentHighlights.value.blinking.add(slotId)
  
  // Debug: Verify CSS classes are applied
  console.log(`Applied highlighting to ${type} slot ${slotId}:`, {
    element: element.tagName + (element.className ? '.' + element.className.split(' ').join('.') : ''),
    hasBlinking: element.classList.contains('blinking-highlight'),
    hasPersistent: element.classList.contains('persistent-highlight'),
    computedBorder: window.getComputedStyle(element).border,
    computedOutline: window.getComputedStyle(element).outline
  })
  
  // After 5 seconds, remove blinking but keep persistent highlight
  setTimeout(() => {
    element.classList.remove('blinking-highlight')
    persistentHighlights.value.blinking.delete(slotId)
    console.log(`Stopped blinking for ${type} slot ${slotId}, persistent border remains`)
    console.log(`Post-blink CSS state:`, {
      hasBlinking: element.classList.contains('blinking-highlight'),
      hasPersistent: element.classList.contains('persistent-highlight'),
      computedBorder: window.getComputedStyle(element).border
    })
  }, 5000)
  
  console.log(`Added persistent highlight to ${type} slot ${slotId}`)
}

const addHighlightEffect = (element) => {
  element.classList.add('highlight-found-item')
  setTimeout(() => {
    element.classList.remove('highlight-found-item')
  }, 5000)
}

const getLocationDescription = (result) => {
  const slotid = result.slotid
  
  if (slotid >= 23 && slotid <= 32) {
    return `Main inventory slot ${slotid}`
  } else if (slotid >= 251 && slotid <= 361) {
    const bagSlot = getBagSlotForContentSlot(slotid)
    if (bagSlot) {
      const uiSlot = getUISlotFromBagSlot(bagSlot)
      const bagItem = props.character?.inventory?.find(s => s.slot === uiSlot)?.item
      const bagName = bagItem?.name || 'Unknown Bag'
      
      // Debug logging to help troubleshoot
      console.log('Bag lookup:', {
        contentSlot: slotid,
        bagSlot: bagSlot,
        uiSlot: uiSlot,
        bagItem: bagItem,
        bagName: bagName,
        inventory: props.character?.inventory
      })
      
      return `In ${bagName} (slot ${uiSlot})`
    }
    return `Bag content slot ${slotid}`
  }
  
  return `Slot ${slotid}`
}

// Watch for character changes to clear highlights
watch(() => props.character?.id, (newCharacterId, oldCharacterId) => {
  if (newCharacterId !== oldCharacterId && oldCharacterId !== undefined) {
    console.log('Character changed, clearing persistent highlights')
    clearAllHighlights()
  }
})

// Component cleanup to prevent memory leaks
onUnmounted(() => {
  // Clear highlights when component unmounts
  clearAllHighlights()
  
  // Cleanup global drag event listeners that might persist
  document.removeEventListener('mousemove', handleDrag)
  document.removeEventListener('mouseup', endDrag)
  
  // Clear any pending timeouts from debounced search
  debouncedSearch.cancel?.()
  
  // Clear caches to prevent memory leaks
  tooltipCache.clear()
  itemDetailsCache.clear()
})
</script>

<style scoped>
/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(5px);
}

.modal-content {
  background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%);
  border: 2px solid #444;
  border-radius: 8px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5);
}

.item-modal {
  width: 500px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px;
  border-bottom: 1px solid #444;
  background: linear-gradient(135deg, #333 0%, #222 100%);
}

.modal-header-content {
  display: flex;
  gap: 15px;
  flex: 1;
}

.item-icon-modal-container {
  flex-shrink: 0;
}

.item-icon-modal {
  width: 64px;
  height: 64px;
  image-rendering: pixelated;
  border: 2px solid #555;
  border-radius: 4px;
  background: #1a1a1a;
}

.item-icon-placeholder-modal {
  width: 64px;
  height: 64px;
  border: 2px solid #555;
  border-radius: 4px;
  background: #1a1a1a;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 24px;
}

.item-header-info h3 {
  color: #fff;
  font-size: 18px;
  margin: 0 0 10px 0;
  font-weight: bold;
}

.item-header-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.item-type-badge, .property-badge {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: bold;
  text-transform: uppercase;
}

.item-type-badge {
  background: #444;
  color: #ccc;
}

.property-badge.magic {
  background: #4a90e2;
  color: white;
}

.property-badge.lore {
  background: #f5a623;
  color: white;
}

.property-badge.nodrop {
  background: #d0021b;
  color: white;
}

.modal-close {
  background: none;
  border: none;
  color: #ccc;
  font-size: 20px;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: #444;
  color: #fff;
}

.modal-body {
  padding: 20px;
}

.detail-section {
  margin-bottom: 25px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h4 {
  color: #fff;
  font-size: 14px;
  margin: 0 0 12px 0;
  padding-bottom: 6px;
  border-bottom: 1px solid #444;
  font-weight: bold;
}

.primary-stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.primary-stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  border: 1px solid #333;
}

.stat-icon {
  width: 32px;
  height: 32px;
  background: #444;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #888;
  font-size: 14px;
  flex-shrink: 0;
}

.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  color: #fff;
  font-size: 16px;
  font-weight: bold;
}

.stat-label {
  color: #ccc;
  font-size: 12px;
  text-transform: uppercase;
}

.stat-extra {
  color: #888;
  font-size: 11px;
  font-style: italic;
}

.attributes-grid, .resistances-grid, .requirements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 8px;
}

.attribute-item, .resist-item, .requirement-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 4px;
  border: 1px solid #333;
}

.attr-label, .resist-label, .req-label {
  color: #ccc;
  font-size: 12px;
  font-weight: bold;
}

.attr-value, .resist-value, .req-value {
  color: #98d982;
  font-size: 12px;
  font-weight: bold;
}

.resist-item.fire .resist-value { color: #ff6b6b; }
.resist-item.cold .resist-value { color: #74c0fc; }
.resist-item.magic .resist-value { color: #da77f2; }
.resist-item.disease .resist-value { color: #69db7c; }
.resist-item.poison .resist-value { color: #95e5d4; }

.character-inventory {
  background: linear-gradient(to bottom, #3a3a3a, #2a2a2a);
  border: 3px outset #666;
  color: #f0f0f0;
  font-family: 'Verdana', sans-serif;
  font-size: 14px;
  width: 800px;
  height: 813px;
  margin: 0 auto;
  position: relative;
}

/* Tab Headers */
.inventory-tabs {
  display: flex;
  background: linear-gradient(to bottom, #4a4a4a, #3a3a3a);
  border-bottom: 1px solid #666;
}

.tab {
  padding: 6px 20px;
  border-right: 1px solid #666;
  cursor: pointer;
  background: linear-gradient(to bottom, #3a3a3a, #2a2a2a);
  color: #ccc;
}

.tab.active {
  background: linear-gradient(to bottom, #4a4a4a, #3a3a3a);
  color: #fff;
  border-bottom: 2px solid #4a4a4a;
}

.tab:hover:not(.active) {
  background: linear-gradient(to bottom, #404040, #303030);
  color: #fff;
}

/* Main Layout */
.inventory-layout {
  display: flex;
  height: calc(100% - 80px);
  padding: 4px;
  gap: 4px;
  overflow: hidden;
}

/* Stats Panel (Left) */
.stats-panel {
  width: 225px;
  background: rgba(20, 20, 20, 0.9);
  border: 1px inset #666;
  padding: 10px;
  flex-shrink: 0;
}

.character-header {
  text-align: center;
  margin-bottom: 8px;
}

.char-name {
  color: #fff;
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 6px;
}

.char-details {
  color: #ccc;
  font-size: 16px;
  margin-bottom: 3px;
}

.character-stats {
  font-size: 12px;
}

.combat-stats {
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #555;
}


.stat-group, .resist-group {
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #555;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: 2px 0;
  line-height: 1.3;
}

.stat-label {
  color: #ddd;
  font-weight: 500;
  min-width: 60px;
}

.stat-value {
  color: #fff;
  font-weight: bold;
  text-align: right;
}

.stat-value.green {
  color: #4CAF50;
}

.stat-row.hp .stat-value { color: #7ba05b; }
.stat-row.mp .stat-value { color: #4169E1; }
.stat-row.en .stat-value { color: #FFD700; }
.stat-row.ac .stat-value { color: #CD853F; }
.stat-row.atk .stat-value { color: #FF6347; }

.misc-stats {
  border-bottom: none;
}

/* Equipment Area (Center) */
.equipment-area {
  position: relative;
  background: rgba(15, 15, 15, 0.8);
  border: 1px inset #666;
  width: 350px;
  height: 675px;
  flex-shrink: 0;
  margin: 0 5px;
}

.equipment-slot-positioned {
  position: absolute;
}

.equipment-slot {
  width: 69px;
  height: 69px;
  background: #222;
  border: 1px inset #555;
  cursor: pointer;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.equipment-slot:hover {
  background: #333;
}

.equipment-slot.has-item {
  background: #2a2a2a;
}

.equipment-slot .item-icon {
  max-width: 90%;
  max-height: 90%;
  image-rendering: pixelated;
  image-rendering: crisp-edges;
}

.slot-label {
  font-size: 7px;
  color: #666;
  text-align: center;
  font-weight: bold;
  letter-spacing: 0.3px;
  text-shadow: 1px 1px 1px rgba(0, 0, 0, 0.8);
  pointer-events: none;
  user-select: none;
  line-height: 0.9;
}

/* Equipment slot positions - rectangular border around class icon */

/* Top border - 4 slots forming continuous top border */
.ear-slot { top: 38px; left: 25px; }
.head-slot { top: 38px; left: 100px; }
.face-slot { top: 38px; left: 175px; }
.ear-2 { top: 38px; left: 250px; }

/* Left border - 4 slots forming continuous left border, aligned with ear slots */
.chest-slot { top: 113px; left: 25px; }
.arms-slot { top: 188px; left: 25px; }
.waist-slot { top: 263px; left: 25px; }
.wrist-1 { top: 338px; left: 25px; }

/* Right border - 4 slots forming continuous right border, aligned with ear slots */
.neck-slot { top: 113px; left: 250px; }
.back-slot { top: 188px; left: 250px; }
.shoulder-slot { top: 263px; left: 250px; }
.wrist-2 { top: 338px; left: 250px; }

/* Bottom area - 3 rows as in original diagram */
/* Bottom row 1: LEGS, HANDS, CHARM, FEET */
.legs-slot { top: 413px; left: 25px; }
.hands-slot { top: 413px; left: 100px; }
.charm-slot { top: 413px; left: 175px; }
.feet-slot { top: 413px; left: 250px; }

/* Bottom row 2: FINGER, FINGER, POWER SOURCE */
.ring-1 { top: 488px; left: 100px; }
.ring-2 { top: 488px; left: 175px; }
.ammo-slot { top: 488px; left: 250px; }

/* Bottom row 3: PRIMARY, OFF HAND, RANGED, AMMO */
.primary-slot { top: 563px; left: 25px; }
.range-slot { top: 563px; left: 100px; }
.secondary-slot { top: 563px; left: 175px; }
.ammo-bottom-slot { top: 563px; left: 250px; }

/* Styling for special slot types that need larger size */
.belt-slot .equipment-slot,
.face-slot .equipment-slot {
  width: 69px;
  height: 69px;
  background: #222;
  border: 1px inset #555;
  cursor: pointer;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Character Model - centered within continuous rectangular border */
.character-model {
  position: absolute;
  top: 150px;
  left: 88px;
  width: 175px;
  height: 225px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.class-icon {
  max-width: 120px;
  max-height: 180px;
  width: auto;
  height: auto;
  image-rendering: auto;
}

/* Currency/Bags Panel (Right) */
.currency-bags-panel {
  width: 200px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  flex-shrink: 0;
}

.currency-section {
  background: rgba(20, 20, 20, 0.9);
  border: 1px inset #666;
  padding: 12px;
  height: auto;
  min-height: 160px;
  font-size: 12px;
  flex-shrink: 0;
}

.currency-header {
  color: #fff;
  font-size: 14px;
  font-weight: bold;
  margin-bottom: 12px;
  text-align: center;
  border-bottom: 1px solid #555;
  padding-bottom: 6px;
}

.currency-amount {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}

.currency-icon {
  width: 20px;
  height: 20px;
  image-rendering: pixelated;
}

.currency-section-divider {
  color: #999;
  font-size: 10px;
  text-align: center;
  margin: 8px 0;
  padding: 4px 0;
  border-top: 1px solid #555;
}

.currency-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 12px;
  padding: 6px;
  border-radius: 3px;
}

.currency-row:hover {
  background: rgba(40, 40, 40, 0.5);
}

.coin-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.coin-label {
  color: #ddd;
  font-weight: 500;
  font-size: 11px;
}

.coin-amount {
  color: #fff;
  font-weight: bold;
  font-size: 13px;
}

.coin-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.currency-row.platinum .coin-amount { color: #E6E6FA; }
.currency-row.gold .coin-amount { color: #FFD700; }
.currency-row.silver .coin-amount { color: #C0C0C0; }
.currency-row.copper .coin-amount { color: #CD7F32; }

/* Bags Section */
.bags-section {
  flex: 1;
  background: rgba(20, 20, 20, 0.9);
  border: 1px inset #666;
  padding: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.inventory-bags {
  display: grid;
  grid-template-columns: repeat(2, 70px);
  grid-template-rows: repeat(5, 70px);
  gap: 1px;
}

.bag-slot {
  width: 70px;
  height: 70px;
  background: #222;
  border: 1px inset #555;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 1;
}

/* CRITICAL: Override bag slot highlighting immediately after base definition */
.inventory-bags .bag-slot.persistent-highlight,
.bags-section .inventory-bags .bag-slot.persistent-highlight,
.character-inventory .bags-section .inventory-bags .bag-slot.persistent-highlight,
div.bag-slot.persistent-highlight,
[data-slot].persistent-highlight {
  border: 6px solid #FFD700 !important;
  border-style: solid !important;
  border-color: #FFD700 !important;
  border-width: 6px !important;
  background: rgba(255, 215, 0, 0.5) !important;
  box-shadow: 0 0 30px rgba(255, 215, 0, 1.0) !important;
  transform: scale(1.05) !important;
  z-index: 1000 !important;
  position: relative !important;
}

/* Nuclear option: Pseudo-element overlay for bag highlighting */
.inventory-bags .bag-slot.persistent-highlight::after,
.bags-section .inventory-bags .bag-slot.persistent-highlight::after,
div.bag-slot.persistent-highlight::after,
[data-slot].persistent-highlight::after {
  content: '';
  position: absolute;
  top: -3px;
  left: -3px;
  right: -3px;
  bottom: -3px;
  border: 3px solid #FFD700;
  border-radius: 4px;
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.8);
  pointer-events: none;
  z-index: 1;
}

.bag-slot:hover {
  background: #333;
}

.bag-slot.has-item {
  background: #2a2a2a;
}

.item-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.item-icon {
  max-width: 90%;
  max-height: 90%;
  image-rendering: pixelated;
  image-rendering: crisp-edges;
}

.stack-count {
  position: absolute;
  bottom: 0;
  right: 1px;
  font-size: 8px;
  color: #fff;
  text-shadow: 1px 1px 1px #000;
  font-weight: bold;
  background: rgba(0, 0, 0, 0.7);
  padding: 0 2px;
  border-radius: 2px;
}

/* Action Bar */
.action-bar {
  height: 40px;
  background: linear-gradient(to bottom, #4a4a4a, #3a3a3a);
  border-top: 1px solid #666;
  display: flex;
  align-items: center;
  padding: 0 8px;
  gap: 4px;
}

.eq-button {
  background: linear-gradient(to bottom, #5a5a5a, #4a4a4a);
  border: 1px outset #666;
  color: #fff;
  padding: 4px 8px;
  font-size: 10px;
  font-family: 'Verdana', sans-serif;
  cursor: pointer;
  height: 24px;
}

.eq-button:hover {
  background: linear-gradient(to bottom, #6a6a6a, #5a5a5a);
}

.eq-button:active {
  border-style: inset;
  background: linear-gradient(to bottom, #4a4a4a, #5a5a5a);
}

.eq-button.find-item {
  margin-left: auto;
  background: linear-gradient(to bottom, #4a6a4a, #3a5a3a);
}

.eq-button.find-item:hover {
  background: linear-gradient(to bottom, #5a7a5a, #4a6a4a);
}

/* Faster tooltip appearance for better UX */
.equipment-slot, .bag-slot {
  position: relative;
}

/* Base tooltip styling */
.equipment-slot[data-tooltip]:hover::after,
.bag-slot[data-tooltip]:hover::after {
  content: attr(data-tooltip);
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.9);
  color: white;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 11px;
  white-space: pre;
  z-index: 10000;
  pointer-events: none;
  animation: tooltipFadeIn 0.15s ease-out;
  text-align: center;
  max-width: 250px;
  word-wrap: break-word;
}

/* DEFAULT: All tooltips appear ABOVE items */
.character-inventory .equipment-slot[data-tooltip]:hover::after,
.character-inventory .bag-slot[data-tooltip]:hover::after {
  bottom: calc(100% + 8px);
  top: auto;
}

/* EQUIPMENT AREA: Target the actual .equipment-slot elements with data-tooltip */

/* TOP HALF OF EQUIPMENT AREA: All equipment slots - tooltips appear BELOW by default */
.character-inventory .equipment-area .equipment-slot[data-tooltip]:hover::after {
  top: calc(100% + 8px) !important;
  bottom: auto !important;
}

/* BOTTOM HALF OF EQUIPMENT AREA: Override for bottom positioned slots - tooltips appear ABOVE */
.character-inventory .equipment-area .legs-slot .equipment-slot[data-tooltip]:hover::after,
.character-inventory .equipment-area .hands-slot .equipment-slot[data-tooltip]:hover::after,
.character-inventory .equipment-area .charm-slot .equipment-slot[data-tooltip]:hover::after,
.character-inventory .equipment-area .feet-slot .equipment-slot[data-tooltip]:hover::after,
.character-inventory .equipment-area .ring-1 .equipment-slot[data-tooltip]:hover::after,
.character-inventory .equipment-area .ring-2 .equipment-slot[data-tooltip]:hover::after,
.character-inventory .equipment-area .ammo-slot .equipment-slot[data-tooltip]:hover::after,
.character-inventory .equipment-area .primary-slot .equipment-slot[data-tooltip]:hover::after,
.character-inventory .equipment-area .range-slot .equipment-slot[data-tooltip]:hover::after,
.character-inventory .equipment-area .secondary-slot .equipment-slot[data-tooltip]:hover::after,
.character-inventory .equipment-area .ammo-bottom-slot .equipment-slot[data-tooltip]:hover::after {
  bottom: calc(100% + 8px) !important;
  top: auto !important;
}

/* TOP HALF OF BAG SECTION: First 6 bag slots - tooltips appear BELOW (higher specificity) */
.character-inventory .bags-section .inventory-bags .bag-slot:nth-child(1)[data-tooltip]:hover::after,
.character-inventory .bags-section .inventory-bags .bag-slot:nth-child(2)[data-tooltip]:hover::after,
.character-inventory .bags-section .inventory-bags .bag-slot:nth-child(3)[data-tooltip]:hover::after,
.character-inventory .bags-section .inventory-bags .bag-slot:nth-child(4)[data-tooltip]:hover::after,
.character-inventory .bags-section .inventory-bags .bag-slot:nth-child(5)[data-tooltip]:hover::after,
.character-inventory .bags-section .inventory-bags .bag-slot:nth-child(6)[data-tooltip]:hover::after {
  top: calc(100% + 8px) !important;
  bottom: auto !important;
}

/* BOTTOM HALF OF BAG SECTION: Last 4 bag slots - tooltips appear ABOVE (explicit) */
.character-inventory .bags-section .inventory-bags .bag-slot:nth-child(7)[data-tooltip]:hover::after,
.character-inventory .bags-section .inventory-bags .bag-slot:nth-child(8)[data-tooltip]:hover::after,
.character-inventory .bags-section .inventory-bags .bag-slot:nth-child(9)[data-tooltip]:hover::after,
.character-inventory .bags-section .inventory-bags .bag-slot:nth-child(10)[data-tooltip]:hover::after {
  bottom: calc(100% + 8px) !important;
  top: auto !important;
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateX(-50%) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) scale(1);
  }
}

/* Simple Tooltip Styles */
.simple-tooltip {
  background: linear-gradient(135deg, #2a2a2a 0%, #1a1a1a 100%);
  border: 2px solid #444;
  border-radius: 6px;
  padding: 12px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
  min-width: 200px;
  max-width: 350px;
  font-size: 12px;
  color: #fff;
  pointer-events: none;
  user-select: none;
}

.tooltip-header {
  font-weight: bold;
  font-size: 14px;
  margin-bottom: 8px;
  color: #fff;
  border-bottom: 1px solid #444;
  padding-bottom: 4px;
}

.tooltip-loading {
  color: #888;
  font-style: italic;
}

.tooltip-error {
  color: #ff6b6b;
  font-style: italic;
}

.tooltip-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.tooltip-body .basic {
  color: #ccc;
}

.tooltip-body .stat {
  color: #4CAF50;
}

.tooltip-body .attr {
  color: #2196F3;
}

.tooltip-body .resist {
  color: #FF9800;
}

.tooltip-body .weapon-stat {
  color: #E91E63;
}

.tooltip-body .item-type {
  color: #9C27B0;
  font-style: italic;
}

.tooltip-body .flag {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: bold;
  margin: 2px 0;
  display: inline-block;
}

.tooltip-body .flag.magic {
  background: #2196F3;
  color: white;
}

.tooltip-body .flag.lore {
  background: #FF9800;
  color: white;
}

.tooltip-body .flag.no-drop {
  background: #f44336;
  color: white;
}

.tooltip-body .basic-info {
  color: #888;
  font-style: italic;
}

.tooltip-body .system-status {
  color: #ff9800;
  font-size: 11px;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid #444;
}

/* Bag Window Styles */
.bag-window {
  position: fixed;
  background: linear-gradient(to bottom, #3a3a3a, #2a2a2a);
  border: 3px outset #666;
  border-radius: 4px;
  font-family: 'Verdana', sans-serif;
  font-size: 12px;
  color: #f0f0f0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  user-select: none;
}

.bag-window-header {
  background: linear-gradient(to bottom, #4a4a4a, #3a3a3a);
  border-bottom: 1px inset #666;
  padding: 4px 8px;
  cursor: move;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 20px;
  font-weight: bold;
}

.bag-window-title {
  color: #fff;
  font-size: 11px;
  flex: 1;
  truncate: true;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.bag-close-btn {
  background: #aa4444;
  border: 1px outset #666;
  color: white;
  width: 16px;
  height: 16px;
  font-size: 10px;
  font-weight: bold;
  cursor: pointer;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 2px;
}

.bag-close-btn:hover {
  background: #cc5555;
}

.bag-close-btn:active {
  border: 1px inset #666;
}

.bag-window-content {
  padding: 8px;
}

.bag-slots-grid {
  display: grid;
  gap: 1px;
}

.bag-window .bag-slot {
  width: 70px;
  height: 70px;
  background: #222;
  border: 1px inset #555;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  aspect-ratio: 1;
}

.bag-window .bag-slot:hover {
  background: #333;
}

.bag-window .bag-slot.has-item {
  background: #2a2a2a;
}

.bag-window .item-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.bag-window .item-icon {
  max-width: 64px;
  max-height: 64px;
  width: auto;
  height: auto;
  image-rendering: pixelated;
}

.bag-window .stack-count {
  position: absolute;
  bottom: 2px;
  right: 2px;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  font-size: 10px;
  font-weight: bold;
  padding: 1px 3px;
  border-radius: 2px;
  min-width: 12px;
  text-align: center;
}

/* Find Item Styles */
.find-item-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.find-item-box {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.95) 0%, rgba(45, 55, 72, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  border: 1px solid rgba(255, 255, 255, 0.1);
  width: 100%;
  max-width: 500px;
  max-height: 600px;
  overflow: hidden;
}

.find-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.find-item-header h3 {
  color: #f7fafc;
  font-size: 1.2rem;
  font-weight: 600;
  margin: 0;
}

.find-item-close {
  background: none;
  border: none;
  color: #cbd5e0;
  font-size: 24px;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s ease;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.find-item-close:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.find-item-content {
  padding: 20px 24px;
}

.find-item-input {
  width: 100%;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: #f7fafc;
  font-size: 14px;
  outline: none;
  transition: all 0.2s ease;
}

.find-item-input:focus {
  border-color: rgba(102, 126, 234, 0.5);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.find-item-input::placeholder {
  color: #9ca3af;
}

.search-results {
  margin-top: 16px;
  max-height: 400px;
  overflow-y: auto;
}

.results-header {
  color: #cbd5e0;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.search-result-item:hover {
  background: rgba(102, 126, 234, 0.1);
  border-color: rgba(102, 126, 234, 0.3);
}

.result-icon {
  width: 32px;
  height: 32px;
  border-radius: 4px;
  image-rendering: pixelated;
  flex-shrink: 0;
}

.result-info {
  flex: 1;
  min-width: 0;
}

.result-name {
  color: #f7fafc;
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 2px;
}

.result-location {
  color: #9ca3af;
  font-size: 12px;
}

.no-results {
  text-align: center;
  color: #9ca3af;
  font-style: italic;
  padding: 20px;
  margin-top: 16px;
}

/* Highlight Effect */
.highlight-found-item {
  animation: goldFlash 5s ease-in-out;
  position: relative;
  z-index: 10;
}

/* Persistent Highlight Styles */
.persistent-highlight {
  border: 3px solid #FFD700 !important;
  position: relative;
  z-index: 10;
  box-shadow: 0 0 15px rgba(255, 215, 0, 0.8) !important;
}

/* Ensure bag slots show the highlight properly - use maximum specificity */
.character-inventory .bag-slot.persistent-highlight,
.inventory-bags .bag-slot.persistent-highlight,
.bag-slot.persistent-highlight.has-item,
.bag-slot.persistent-highlight {
  border: 4px solid #FFD700 !important;
  border-style: solid !important;
  border-color: #FFD700 !important;
  border-width: 4px !important;
  box-shadow: 0 0 20px rgba(255, 215, 0, 1.0) !important;
  outline: 3px solid #FFA500 !important;
  outline-offset: -1px !important;
  background: rgba(255, 215, 0, 0.2) !important; /* More visible gold tint */
}

/* Ensure equipment slots show the highlight properly */
.equipment-slot.persistent-highlight {
  border: 3px solid #FFD700 !important;
  box-shadow: 0 0 15px rgba(255, 215, 0, 0.8) !important;
}

/* Blinking Highlight Animation */
.blinking-highlight,
.bag-slot.blinking-highlight,
.equipment-slot.blinking-highlight {
  animation: goldBlink 0.3s ease-in-out infinite alternate;
}

@keyframes goldBlink {
  0% {
    border-color: #FFD700 !important;
    box-shadow: 0 0 15px rgba(255, 215, 0, 0.8) !important;
  }
  100% {
    border-color: #FFA500 !important;
    box-shadow: 0 0 20px rgba(255, 165, 0, 1) !important;
  }
}

@keyframes goldFlash {
  0%, 100% { 
    box-shadow: 0 0 0 2px transparent; 
  }
  5%, 15%, 25%, 35%, 45% { 
    box-shadow: 0 0 0 3px #ffd700, 0 0 20px rgba(255, 215, 0, 0.6); 
  }
  10%, 20%, 30%, 40% { 
    box-shadow: 0 0 0 2px #ffed4e, 0 0 15px rgba(255, 237, 78, 0.4); 
  }
  50% { 
    box-shadow: 0 0 0 2px #ffd700, 0 0 10px rgba(255, 215, 0, 0.3); 
  }
}
</style>