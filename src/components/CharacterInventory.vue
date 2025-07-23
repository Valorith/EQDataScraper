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
      <div class="equipment-area">
        <!-- Equipment slots positioned around character -->
        <div class="equipment-slot-positioned charm-slot" data-slot="charm">
          <div class="equipment-slot" 
               :class="{ 'has-item': character.equipment?.charm }"
               :title="getItemTooltip(character.equipment?.charm)"
               @click="selectItem(character.equipment?.charm)">
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
               :title="getItemTooltip(character.equipment?.head)"
               @click="selectItem(character.equipment?.head)">
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
               :title="getItemTooltip(character.equipment?.ear1)"
               @click="selectItem(character.equipment?.ear1)">
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
               :title="getItemTooltip(character.equipment?.ear2)"
               @click="selectItem(character.equipment?.ear2)">
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
               :title="getItemTooltip(character.equipment?.neck)"
               @click="selectItem(character.equipment?.neck)">
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
               :title="getItemTooltip(character.equipment?.shoulder)"
               @click="selectItem(character.equipment?.shoulder)">
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
               :title="getItemTooltip(character.equipment?.arms)"
               @click="selectItem(character.equipment?.arms)">
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
               :title="getItemTooltip(character.equipment?.back)"
               @click="selectItem(character.equipment?.back)">
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
               :title="getItemTooltip(character.equipment?.wrist1)"
               @click="selectItem(character.equipment?.wrist1)">
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
               :title="getItemTooltip(character.equipment?.wrist2)"
               @click="selectItem(character.equipment?.wrist2)">
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
               :title="getItemTooltip(character.equipment?.range)"
               @click="selectItem(character.equipment?.range)">
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
               :title="getItemTooltip(character.equipment?.hands)"
               @click="selectItem(character.equipment?.hands)">
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
               :title="getItemTooltip(character.equipment?.primary)"
               @click="selectItem(character.equipment?.primary)">
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
               :title="getItemTooltip(character.equipment?.secondary)"
               @click="selectItem(character.equipment?.secondary)">
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
               :title="getItemTooltip(character.equipment?.ammo)"
               @click="selectItem(character.equipment?.ammo)">
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
               :title="getItemTooltip(character.equipment?.ring1)"
               @click="selectItem(character.equipment?.ring1)">
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
               :title="getItemTooltip(character.equipment?.ring2)"
               @click="selectItem(character.equipment?.ring2)">
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
               :title="getItemTooltip(character.equipment?.chest)"
               @click="selectItem(character.equipment?.chest)">
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
               :title="getItemTooltip(character.equipment?.legs)"
               @click="selectItem(character.equipment?.legs)">
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
               :title="getItemTooltip(character.equipment?.feet)"
               @click="selectItem(character.equipment?.feet)">
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
               :title="getItemTooltip(character.equipment?.waist)"
               @click="selectItem(character.equipment?.waist)">
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
               :title="getItemTooltip(character.equipment?.power_source)"
               @click="selectItem(character.equipment?.power_source)">
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
               :title="getItemTooltip(character.equipment?.face)"
               @click="selectItem(character.equipment?.face)">
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
              :title="getItemTooltip(slot.item)"
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
      <button class="eq-button find-item">Find Item</button>
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
            :title="getItemTooltip(bagSlot.item, true)"
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
import { ref } from 'vue'
import LoadingModal from './LoadingModal.vue'
import ItemModal from './ItemModal.vue'
import { getApiBaseUrl } from '../config/api'

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

// Debug: Watch for prop changes
import { watch } from 'vue'
watch(() => props.rawInventoryData, (newData, oldData) => {
  console.log('rawInventoryData prop changed from', oldData?.length || 0, 'to', newData?.length || 0, 'items')
  if (newData?.length > 0) {
    console.log('Sample items:', newData.slice(0, 3).map(item => ({ slotid: item?.slotid, name: item?.item_name })))
  }
}, { immediate: true })


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

// Modal functions
const selectItem = async (item) => {
  if (!item) return
  
  loadingItemModal.value = true
  
  try {
    const response = await fetch(`${getApiBaseUrl()}/api/items/${item.id}/details`)
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    selectedItemDetail.value = data
    
    // Load data availability after item details are loaded
    await loadItemDataAvailability(item.id)
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
    const response = await fetch(`${getApiBaseUrl()}/api/items/${selectedItemDetail.value.id}/drop-sources`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    const data = await response.json()
    // Backend returns {zones: [...]} but frontend expects array directly
    dropSources.value = data.zones || []
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
    const response = await fetch(`${getApiBaseUrl()}/api/items/${selectedItemDetail.value.id}/merchant-sources`)
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`)
    const data = await response.json()
    // Backend returns {zones: [...]} but frontend expects array directly
    merchantSources.value = data.zones || []
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

const getItemTooltip = (item, isInBagWindow = false) => {
  if (!item) return ''
  
  const isContainer = item.containerSize && item.containerSize > 0
  
  if (isContainer && !isInBagWindow) {
    return `Left click for info.\nRight click to open`
  } else {
    return `Left click for info.`
  }
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
  
  // Check if this bag is already open
  const existingWindow = openBagWindows.value.find(w => w.slotId === slot.slotid)
  if (existingWindow) {
    bringBagToFront(slot.slotid)
    return
  }
  
  // Calculate position next to the clicked bag
  const rect = event.target.closest('.bag-slot').getBoundingClientRect()
  const x = rect.right + 10
  const y = rect.top
  
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
  
  // Map bag slot IDs to their content slot ranges - EQEmu allocates 10 slots per bag regardless of actual size
  const slotRanges = {
    23: [262, 271], 24: [272, 281], 25: [282, 291], 26: [292, 301], 27: [302, 311],
    28: [312, 321], 29: [322, 331], 30: [332, 341], 31: [342, 351], 32: [352, 361]
  }
  
  const range = slotRanges[bagSlotId]
  if (!range) {
    return []
  }
  
  const [startSlot, endSlot] = range
  
  // Find all items that exist in this bag's slot range, regardless of gaps
  const bagItems = props.rawInventoryData.filter(item => 
    item && item.slotid >= startSlot && item.slotid <= endSlot
  ).sort((a, b) => a.slotid - b.slotid) // Sort by slot ID
  
  const contents = []
  
  // Create slots for the container, mapping actual items to UI slots
  for (let i = 0; i < containerSize; i++) {
    const inventoryItem = bagItems[i] // Use the i-th item found, not a specific slot
    
    contents.push({
      slot: i,
      slotid: inventoryItem ? inventoryItem.slotid : (startSlot + i), // Use actual slot if item exists
      item: inventoryItem ? {
        id: inventoryItem.itemid || inventoryItem.id,
        name: inventoryItem.item_name || inventoryItem.name,
        icon: `/icons/items/${inventoryItem.item_icon || inventoryItem.icon || 500}.png`,
        charges: inventoryItem.charges || 0,
        stackSize: inventoryItem.stackable ? (inventoryItem.charges || 1) : 1,
        stackable: inventoryItem.stackable,
        color: inventoryItem.color || 0
      } : null
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
  event.preventDefault()
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

.equipment-slot[title]:hover::after,
.bag-slot[title]:hover::after {
  content: attr(title);
  position: absolute;
  top: -8px;
  left: 50%;
  transform: translateX(-50%) translateY(-100%);
  background: rgba(0, 0, 0, 0.9);
  color: white;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 11px;
  white-space: pre;
  z-index: 1000;
  pointer-events: none;
  animation: tooltipFadeIn 0.15s ease-out;
  text-align: center;
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(5px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
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
</style>