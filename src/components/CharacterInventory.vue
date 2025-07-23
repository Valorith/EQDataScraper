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
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.charm }">
            <img v-if="character.equipment?.charm" 
                 :src="`/icons/items/${character.equipment.charm.icon}.gif`" 
                 :alt="character.equipment.charm.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">CHARM</span>
          </div>
        </div>
        <div class="equipment-slot-positioned head-slot" data-slot="head">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.head }">
            <img v-if="character.equipment?.head" 
                 :src="`/icons/items/${character.equipment.head.icon}.gif`" 
                 :alt="character.equipment.head.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">HELM</span>
          </div>
        </div>
        <div class="equipment-slot-positioned ear-slot" data-slot="ear1">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.ear1 }">
            <img v-if="character.equipment?.ear1" 
                 :src="`/icons/items/${character.equipment.ear1.icon}.gif`" 
                 :alt="character.equipment.ear1.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">EAR</span>
          </div>
        </div>
        <div class="equipment-slot-positioned ear-slot ear-2" data-slot="ear2">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.ear2 }">
            <img v-if="character.equipment?.ear2" 
                 :src="`/icons/items/${character.equipment.ear2.icon}.gif`" 
                 :alt="character.equipment.ear2.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">EAR</span>
          </div>
        </div>
        <div class="equipment-slot-positioned neck-slot" data-slot="neck">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.neck }">
            <img v-if="character.equipment?.neck" 
                 :src="`/icons/items/${character.equipment.neck.icon}.gif`" 
                 :alt="character.equipment.neck.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">NECK</span>
          </div>
        </div>
        <div class="equipment-slot-positioned shoulder-slot" data-slot="shoulder">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.shoulder }">
            <img v-if="character.equipment?.shoulder" 
                 :src="`/icons/items/${character.equipment.shoulder.icon}.gif`" 
                 :alt="character.equipment.shoulder.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">SHOULDER</span>
          </div>
        </div>
        <div class="equipment-slot-positioned arms-slot" data-slot="arms">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.arms }">
            <img v-if="character.equipment?.arms" 
                 :src="`/icons/items/${character.equipment.arms.icon}.gif`" 
                 :alt="character.equipment.arms.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">ARMS</span>
          </div>
        </div>
        <div class="equipment-slot-positioned back-slot" data-slot="back">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.back }">
            <img v-if="character.equipment?.back" 
                 :src="`/icons/items/${character.equipment.back.icon}.gif`" 
                 :alt="character.equipment.back.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">BACK</span>
          </div>
        </div>
        <div class="equipment-slot-positioned wrist-slot wrist-1" data-slot="wrist1">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.wrist1 }">
            <img v-if="character.equipment?.wrist1" 
                 :src="`/icons/items/${character.equipment.wrist1.icon}.gif`" 
                 :alt="character.equipment.wrist1.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">WRIST</span>
          </div>
        </div>
        <div class="equipment-slot-positioned wrist-slot wrist-2" data-slot="wrist2">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.wrist2 }">
            <img v-if="character.equipment?.wrist2" 
                 :src="`/icons/items/${character.equipment.wrist2.icon}.gif`" 
                 :alt="character.equipment.wrist2.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">WRIST</span>
          </div>
        </div>
        <div class="equipment-slot-positioned range-slot" data-slot="range">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.range }">
            <img v-if="character.equipment?.range" 
                 :src="`/icons/items/${character.equipment.range.icon}.gif`" 
                 :alt="character.equipment.range.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">RANGED</span>
          </div>
        </div>
        <div class="equipment-slot-positioned hands-slot" data-slot="hands">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.hands }">
            <img v-if="character.equipment?.hands" 
                 :src="`/icons/items/${character.equipment.hands.icon}.gif`" 
                 :alt="character.equipment.hands.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">HANDS</span>
          </div>
        </div>
        <div class="equipment-slot-positioned primary-slot" data-slot="primary">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.primary }">
            <img v-if="character.equipment?.primary" 
                 :src="`/icons/items/${character.equipment.primary.icon}.gif`" 
                 :alt="character.equipment.primary.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">MAIN HAND</span>
          </div>
        </div>
        <div class="equipment-slot-positioned secondary-slot" data-slot="secondary">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.secondary }">
            <img v-if="character.equipment?.secondary" 
                 :src="`/icons/items/${character.equipment.secondary.icon}.gif`" 
                 :alt="character.equipment.secondary.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">OFF<br>HAND</span>
          </div>
        </div>
        <div class="equipment-slot-positioned ammo-bottom-slot" data-slot="ammo">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.ammo }">
            <img v-if="character.equipment?.ammo" 
                 :src="`/icons/items/${character.equipment.ammo.icon}.gif`" 
                 :alt="character.equipment.ammo.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">AMMO</span>
          </div>
        </div>
        <div class="equipment-slot-positioned ring-slot ring-1" data-slot="ring1">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.ring1 }">
            <img v-if="character.equipment?.ring1" 
                 :src="`/icons/items/${character.equipment.ring1.icon}.gif`" 
                 :alt="character.equipment.ring1.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">FINGER</span>
          </div>
        </div>
        <div class="equipment-slot-positioned ring-slot ring-2" data-slot="ring2">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.ring2 }">
            <img v-if="character.equipment?.ring2" 
                 :src="`/icons/items/${character.equipment.ring2.icon}.gif`" 
                 :alt="character.equipment.ring2.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">FINGER</span>
          </div>
        </div>
        <div class="equipment-slot-positioned chest-slot" data-slot="chest">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.chest }">
            <img v-if="character.equipment?.chest" 
                 :src="`/icons/items/${character.equipment.chest.icon}.gif`" 
                 :alt="character.equipment.chest.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">CHEST</span>
          </div>
        </div>
        <div class="equipment-slot-positioned legs-slot" data-slot="legs">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.legs }">
            <img v-if="character.equipment?.legs" 
                 :src="`/icons/items/${character.equipment.legs.icon}.gif`" 
                 :alt="character.equipment.legs.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">LEGS</span>
          </div>
        </div>
        <div class="equipment-slot-positioned feet-slot" data-slot="feet">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.feet }">
            <img v-if="character.equipment?.feet" 
                 :src="`/icons/items/${character.equipment.feet.icon}.gif`" 
                 :alt="character.equipment.feet.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">FEET</span>
          </div>
        </div>
        <div class="equipment-slot-positioned waist-slot" data-slot="waist">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.waist }">
            <img v-if="character.equipment?.waist" 
                 :src="`/icons/items/${character.equipment.waist.icon}.gif`" 
                 :alt="character.equipment.waist.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">WAIST</span>
          </div>
        </div>
        <div class="equipment-slot-positioned ammo-slot" data-slot="power_source">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.power_source }">
            <img v-if="character.equipment?.power_source" 
                 :src="`/icons/items/${character.equipment.power_source.icon}.gif`" 
                 :alt="character.equipment.power_source.name"
                 class="item-icon" 
                 @error="handleImageError" />
            <span v-else class="slot-label">POWER<br>SOURCE</span>
          </div>
        </div>
        <div class="equipment-slot-positioned face-slot" data-slot="face">
          <div class="equipment-slot" :class="{ 'has-item': character.equipment?.face }">
            <img v-if="character.equipment?.face" 
                 :src="`/icons/items/${character.equipment.face.icon}.gif`" 
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
              v-for="slot in character.inventory.slice(0, 10)" 
              :key="slot.slot"
              class="bag-slot"
              :class="{ 'has-item': slot.item }"
              @click="handleSlotClick(slot)"
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
  </div>
</template>

<script>
export default {
  name: 'CharacterInventory',
  props: {
    character: {
      type: Object,
      required: true
    }
  },
  methods: {
    handleSlotClick(slot) {
      if (slot.item) {
        console.log('Clicked item:', slot.item.name)
        // TODO: Show item tooltip or details
      }
    },
    
    handleImageError(event) {
      // Try PNG version first, then fallback to default icon
      const currentSrc = event.target.src
      if (currentSrc.endsWith('.gif')) {
        // Try PNG version
        event.target.src = currentSrc.replace('.gif', '.png')
      } else {
        // Fallback to default icon
        event.target.src = '/icons/items/500.gif'
      }
    },

    formatCurrency(value) {
      // Format currency with commas for readability
      return value.toLocaleString()
    },

    normalizeClassName(className) {
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
  }
}
</script>

<style scoped>
.character-inventory {
  background: linear-gradient(to bottom, #3a3a3a, #2a2a2a);
  border: 3px outset #666;
  color: #f0f0f0;
  font-family: 'Verdana', sans-serif;
  font-size: 14px;
  width: 750px;
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
  font-size: 12px;
  font-weight: bold;
  margin-bottom: 2px;
}

.char-details {
  color: #ccc;
  font-size: 10px;
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
  width: 150px;
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
}

.inventory-bags {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(5, 1fr);
  gap: 1px;
  justify-content: center;
  align-content: center;
  height: 100%;
  padding: 4px;
}

.bag-slot {
  width: 100%;
  height: 100%;
  min-width: 60px;
  min-height: 60px;
  max-width: 80px;
  max-height: 80px;
  background: #222;
  border: 1px inset #555;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  justify-self: center;
  align-self: center;
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
</style>