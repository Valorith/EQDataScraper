<template>
  <Teleport to="body">
    <div 
      v-if="visible"
      :class="['item-tooltip', { 'pinned': isPinned }]"
      :style="tooltipStyle"
      :data-tooltip-item="itemId"
      @mouseenter="handleTooltipEnter"
      @mouseleave="handleTooltipLeave"
      ref="tooltipEl"
    >
      <div class="tooltip-header">
        <a :href="`/items/${itemData?.id || ''}`" class="item-name" @click.prevent>
          {{ itemData?.name || 'Loading...' }}
        </a>
        <div class="tooltip-controls">
          <button 
            v-if="allowPin" 
            @click="togglePin" 
            :class="{ 'active': isPinned }"
            title="Pin tooltip"
          >
            📌
          </button>
          <button @click="closeTooltip" title="Close">✕</button>
        </div>
      </div>
      
      <div v-if="loading" class="tooltip-loading">
        Loading item data...
      </div>
      
      <div v-else-if="error" class="tooltip-error">
        Failed to load item data
      </div>
      
      <div v-else-if="itemData" class="tooltip-content">
        <div class="item-icon-section">
          <div class="item-icon-large">
            <img 
              :src="getItemIconUrl(itemData.icon)" 
              :alt="itemData.name"
              @error="handleIconError"
            />
            <span v-if="itemData.stacksize > 1" class="stack-count">
              {{ itemData.stacksize }}
            </span>
          </div>
        </div>
        
        <div class="item-details">
          <!-- Item Type and Basic Info -->
          <div v-if="itemData.itemtype" class="item-type">
            {{ getItemTypeName(itemData.itemtype) }}
          </div>
          
          <!-- Damage/Delay for weapons -->
          <div v-if="itemData.damage && itemData.delay" class="weapon-stats">
            <div>Damage: {{ itemData.damage }}</div>
            <div>Delay: {{ itemData.delay }}</div>
            <div>Ratio: {{ calculateRatio(itemData.damage, itemData.delay) }}</div>
          </div>
          
          <!-- AC for armor -->
          <div v-if="itemData.ac > 0" class="armor-stats">
            AC: {{ itemData.ac }}
          </div>
          
          <!-- Stats -->
          <div v-if="hasStats" class="item-stats">
            <div v-if="itemData.hp > 0">HP: +{{ itemData.hp }}</div>
            <div v-if="itemData.mana > 0">Mana: +{{ itemData.mana }}</div>
            <div v-if="itemData.endur > 0">Endur: +{{ itemData.endur }}</div>
            <div v-if="itemData.attack > 0">ATK: +{{ itemData.attack }}</div>
            <div v-if="itemData.astr > 0">STR: +{{ itemData.astr }}</div>
            <div v-if="itemData.asta > 0">STA: +{{ itemData.asta }}</div>
            <div v-if="itemData.aagi > 0">AGI: +{{ itemData.aagi }}</div>
            <div v-if="itemData.adex > 0">DEX: +{{ itemData.adex }}</div>
            <div v-if="itemData.awis > 0">WIS: +{{ itemData.awis }}</div>
            <div v-if="itemData.aint > 0">INT: +{{ itemData.aint }}</div>
            <div v-if="itemData.acha > 0">CHA: +{{ itemData.acha }}</div>
          </div>
          
          <!-- Resistances -->
          <div v-if="hasResistances" class="item-resistances">
            <div v-if="itemData.pr > 0">Poison Resist: +{{ itemData.pr }}</div>
            <div v-if="itemData.mr > 0">Magic Resist: +{{ itemData.mr }}</div>
            <div v-if="itemData.fr > 0">Fire Resist: +{{ itemData.fr }}</div>
            <div v-if="itemData.cr > 0">Cold Resist: +{{ itemData.cr }}</div>
            <div v-if="itemData.dr > 0">Disease Resist: +{{ itemData.dr }}</div>
            <div v-if="itemData.svcorruption > 0">Corruption Resist: +{{ itemData.svcorruption }}</div>
          </div>
          
          <!-- Weight -->
          <div v-if="itemData.weight > 0" class="item-weight">
            Weight: {{ (itemData.weight / 10).toFixed(1) }}
          </div>
          
          <!-- Item Properties -->
          <div class="item-properties">
            <span v-if="itemData.magic" class="property magic">MAGIC</span>
            <span v-if="itemData.lore" class="property lore">LORE</span>
            <span v-if="itemData.nodrop" class="property nodrop">NO DROP</span>
          </div>
          
          <!-- Slot Restrictions -->
          <div v-if="getSlotNames(itemData.slots).length > 0" class="item-slots">
            <strong>Slot:</strong> {{ getSlotNames(itemData.slots).join(', ') }}
          </div>
          
          <!-- Class/Race Restrictions -->
          <div v-if="getClassNames(itemData.classes).length > 0" class="item-classes">
            <strong>Class:</strong> {{ getClassNames(itemData.classes).join(', ') }}
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  itemId: {
    type: Number,
    required: true
  },
  itemData: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: Boolean,
    default: false
  },
  position: {
    type: Object,
    default: () => ({ x: 0, y: 0 })
  },
  allowPin: {
    type: Boolean,
    default: false
  },
  isPinned: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'toggle-pin', 'mouse-enter', 'mouse-leave'])

const tooltipEl = ref(null)

const tooltipStyle = computed(() => {
  // Simple safe positioning
  const x = Math.min(Math.max(props.position.x + 20, 10), window.innerWidth - 350)
  const y = Math.min(Math.max(props.position.y + 20, 10), window.innerHeight - 200)
  
  return {
    position: 'fixed',
    left: `${x}px`,
    top: `${y}px`,
    zIndex: props.isPinned ? 10000 : 9999
  }
})

const hasStats = computed(() => {
  if (!props.itemData) return false
  return ['hp', 'mana', 'endur', 'attack', 'astr', 'asta', 'aagi', 'adex', 'awis', 'aint', 'acha']
    .some(stat => (props.itemData[stat] || 0) > 0)
})

const hasResistances = computed(() => {
  if (!props.itemData) return false
  return ['pr', 'mr', 'fr', 'cr', 'dr', 'svcorruption']
    .some(resist => (props.itemData[resist] || 0) > 0)
})

const getItemIconUrl = (icon) => {
  if (!icon) return '/icons/items/500.png'
  return `/icons/items/${icon}.png`
}

const handleIconError = (event) => {
  // Try GIF fallback, then default
  if (event.target.src.endsWith('.png')) {
    event.target.src = event.target.src.replace('.png', '.gif')
  } else {
    event.target.src = '/icons/items/500.png'
  }
}

const getItemTypeName = (itemtype) => {
  const types = {
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
  return types[itemtype] || `Type ${itemtype}`
}

const calculateRatio = (damage, delay) => {
  if (!damage || !delay) return '0.0'
  return (damage / (delay / 10)).toFixed(1)
}

const getSlotNames = (slots) => {
  if (!slots) return []
  
  const slotNames = {
    1: 'Charm',
    2: 'Ear', 
    4: 'Head',
    8: 'Face',
    16: 'Ear',
    32: 'Neck',
    64: 'Shoulder',
    128: 'Arms',
    256: 'Back',
    512: 'Wrist',
    1024: 'Wrist',
    2048: 'Range',
    4096: 'Hands',
    8192: 'Primary',
    16384: 'Secondary',
    32768: 'Finger',
    65536: 'Finger',
    131072: 'Chest',
    262144: 'Legs',
    524288: 'Feet',
    1048576: 'Waist',
    2097152: 'Power Source',
    4194304: 'Ammo'
  }
  
  const activeSlots = []
  for (const [bit, name] of Object.entries(slotNames)) {
    if (slots & parseInt(bit)) {
      activeSlots.push(name)
    }
  }
  return activeSlots
}

const getClassNames = (classes) => {
  if (!classes) return []
  
  const classNames = {
    1: 'WAR', 2: 'CLR', 4: 'PAL', 8: 'RNG', 16: 'SHD',
    32: 'DRU', 64: 'MNK', 128: 'BRD', 256: 'ROG', 512: 'SHM',
    1024: 'NEC', 2048: 'WIZ', 4096: 'MAG', 8192: 'ENC',
    16384: 'BST', 32768: 'BER'
  }
  
  const activeClasses = []
  for (const [bit, name] of Object.entries(classNames)) {
    if (classes & parseInt(bit)) {
      activeClasses.push(name)
    }
  }
  return activeClasses
}

const handleTooltipEnter = () => {
  emit('mouse-enter')
}

const handleTooltipLeave = () => {
  emit('mouse-leave')
}

const togglePin = () => {
  emit('toggle-pin')
}

const closeTooltip = () => {
  emit('close')
}
</script>

<style scoped>
.item-tooltip {
  position: fixed;
  z-index: 99999;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.95), rgba(30, 30, 50, 0.95));
  border: 2px solid #4a5568;
  border-radius: 8px;
  backdrop-filter: blur(10px);
  min-width: 300px;
  max-width: 400px;
  font-family: 'Segoe UI', Arial, sans-serif;
  font-size: 12px;
  color: #e2e8f0;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  pointer-events: auto;
  user-select: text;
}

.item-tooltip.pinned {
  box-shadow: 0 0 0 2px #ffd700, 0 10px 25px rgba(0, 0, 0, 0.5);
}

.tooltip-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid #4a5568;
  border-radius: 6px 6px 0 0;
}

.item-name {
  color: #ffd700;
  text-decoration: none;
  font-weight: bold;
  font-size: 13px;
  cursor: pointer;
}

.item-name:hover {
  color: #fff;
}

.tooltip-controls {
  display: flex;
  gap: 4px;
}

.tooltip-controls button {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  color: #e2e8f0;
  font-size: 11px;
  padding: 2px 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tooltip-controls button:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
}

.tooltip-controls button.active {
  background: #ffd700;
  color: #1a1a1a;
}

.tooltip-loading, .tooltip-error {
  padding: 16px;
  text-align: center;
  color: #a0aec0;
  font-style: italic;
}

.tooltip-error {
  color: #fc8181;
}

.tooltip-content {
  padding: 12px;
}

.item-icon-section {
  display: flex;
  justify-content: center;
  margin-bottom: 12px;
}

.item-icon-large {
  position: relative;
  width: 40px;
  height: 40px;
  border: 1px solid #4a5568;
  border-radius: 4px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.3);
}

.item-icon-large img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  image-rendering: pixelated;
}

.stack-count {
  position: absolute;
  bottom: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.8);
  color: #ffd700;
  font-size: 10px;
  padding: 1px 3px;
  border-radius: 2px 0 0 0;
}

.item-details > div {
  margin-bottom: 6px;
}

.item-type {
  color: #a0aec0;
  font-style: italic;
  margin-bottom: 8px;
}

.weapon-stats, .armor-stats {
  color: #90cdf4;
  font-weight: 500;
}

.weapon-stats > div {
  margin-bottom: 2px;
}

.item-stats > div {
  color: #68d391;
  margin-bottom: 2px;
}

.item-resistances > div {
  color: #fbb6ce;
  margin-bottom: 2px;
}

.item-weight {
  color: #a0aec0;
}

.item-properties {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin: 8px 0;
}

.property {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: bold;
}

.property.magic {
  background: #553c9a;
  color: #c6b2ff;
}

.property.lore {
  background: #2d3748;
  color: #e2e8f0;
}

.property.nodrop {
  background: #822727;
  color: #feb2b2;
}

.item-slots, .item-classes {
  color: #a0aec0;
  font-size: 11px;
  line-height: 1.4;
  margin-top: 6px;
}

.item-slots strong, .item-classes strong {
  color: #e2e8f0;
}
</style>