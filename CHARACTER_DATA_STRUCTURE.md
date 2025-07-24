# Character Data Structure for EQDataScraper

This document outlines the complete character data structure needed to populate the inventory UI with real EQEmu database data.

## Complete Character Object Structure

Based on the actual EQEmu character_data table schema:

```javascript
const character = {
  // Basic Character Information
  id: number,                    // character_data.id
  accountId: number,             // character_data.account_id
  name: string,                  // character_data.name
  lastName: string,              // character_data.last_name
  level: number,                 // character_data.level
  class: string,                 // Mapped from character_data.class (see class mapping)
  race: string,                  // Mapped from character_data.race (see race mapping)
  gender: number,                // character_data.gender (0=male, 1=female)
  deity: number,                 // character_data.deity
  
  // Physical Appearance
  appearance: {
    face: number,                // character_data.face
    hairColor: number,           // character_data.hair_color
    hairStyle: number,           // character_data.hair_style
    beard: number,               // character_data.beard
    beardColor: number,          // character_data.beard_color
    eyeColor1: number,           // character_data.eye_color_1
    eyeColor2: number            // character_data.eye_color_2
  },
  
  // Location Information
  location: {
    zoneId: number,              // character_data.zone_id
    zoneInstance: number,        // character_data.zone_instance
    x: number,                   // character_data.x
    y: number,                   // character_data.y
    z: number,                   // character_data.z
    heading: number              // character_data.heading
  },
  
  // Combat Statistics
  maxHp: number,                 // character_data.cur_hp (current HP, max needs calculation)
  maxMp: number,                 // character_data.mana (current mana)
  endurance: number,             // character_data.endurance
  ac: number,                    // Calculated from base + equipment
  atk: number,                   // Calculated from base + equipment
  
  // Primary Attributes (base stats from character creation + level bonuses)
  stats: {
    str: number,                 // character_data.str
    sta: number,                 // character_data.sta  
    agi: number,                 // character_data.agi
    dex: number,                 // character_data.dex
    wis: number,                 // character_data.wis
    int: number,                 // character_data.int
    cha: number                  // character_data.cha
  },
  
  // Note: Resistances are typically calculated from race base + equipment
  // The character_data table doesn't store resistance values directly
  resistances: {
    poison: number,              // Calculated from race base + equipment
    magic: number,               // Calculated from race base + equipment
    disease: number,             // Calculated from race base + equipment
    fire: number,                // Calculated from race base + equipment
    cold: number,                // Calculated from race base + equipment
    corrupt: number              // Calculated from race base + equipment
  },
  
  // Experience and Character Progression
  experience: {
    exp: number,                 // character_data.exp
    aaExp: number,               // character_data.aa_exp
    aaPoints: number             // character_data.aa_points
  },
  
  // Character Metadata
  metadata: {
    birthday: number,            // character_data.birthday (UNIX timestamp)
    lastLogin: number,           // character_data.last_login (UNIX timestamp)
    timePlayed: number,          // character_data.time_played (seconds)
    pvpStatus: number            // character_data.pvp_status
  },
  
  // Physical Attributes
  weight: number,                // Calculated from equipped items + inventory
  
  // Note: Currency is NOT stored in character_data table in modern EQEmu
  // Currency is typically handled through separate systems or alternative storage
  currency: {
    platinum: number,            // May need to query separate currency system
    gold: number,                // May need to query separate currency system
    silver: number,              // May need to query separate currency system
    copper: number               // May need to query separate currency system
  },
  
  // Equipment Slots (from inventory table where slotid matches equipment slots)
  equipment: {
    // Armor slots
    head: EquippedItem | null,        // slotid 2
    chest: EquippedItem | null,       // slotid 17
    arms: EquippedItem | null,        // slotid 8
    wrist1: EquippedItem | null,      // slotid 9
    wrist2: EquippedItem | null,      // slotid 10
    hands: EquippedItem | null,       // slotid 11
    legs: EquippedItem | null,        // slotid 18
    feet: EquippedItem | null,        // slotid 19
    
    // Weapon/Shield slots
    primary: EquippedItem | null,     // slotid 13
    secondary: EquippedItem | null,   // slotid 14
    range: EquippedItem | null,       // slotid 15
    ammo: EquippedItem | null,        // slotid 16
    
    // Jewelry slots
    neck: EquippedItem | null,        // slotid 3
    ear1: EquippedItem | null,        // slotid 0
    ear2: EquippedItem | null,        // slotid 1
    ring1: EquippedItem | null,       // slotid 20
    ring2: EquippedItem | null,       // slotid 21
    
    // Misc slots
    face: EquippedItem | null,        // slotid 6
    back: EquippedItem | null,        // slotid 7
    waist: EquippedItem | null,       // slotid 12
    shoulder: EquippedItem | null,    // slotid 4
    charm: EquippedItem | null        // slotid 5
  },
  
  // General Inventory (from inventory table where slotid 22-31 = general inventory)
  inventory: [
    {
      slot: number,              // slotid (22-31 for general inventory)
      item: InventoryItem | null
    }
  ]
}
```

## EquippedItem Structure

```javascript
const EquippedItem = {
  id: number,                    // inventory.itemid
  name: string,                  // items.Name
  icon: string,                  // items.icon (item icon ID)
  charges: number,               // inventory.charges
  color: number,                 // inventory.color
  isNoDrop: boolean,             // !inventory.instnodrop
  
  // Item statistics (from items table)
  ac: number,                    // items.ac
  hp: number,                    // items.hp
  mana: number,                  // items.mana
  endur: number,                 // items.endur
  attack: number,                // items.attack
  
  // Item attributes
  str: number,                   // items.astr
  sta: number,                   // items.asta
  agi: number,                   // items.aagi
  dex: number,                   // items.adex
  wis: number,                   // items.awis
  int: number,                   // items.aint
  cha: number,                   // items.acha
  
  // Resistances
  poisonResist: number,          // items.pr
  magicResist: number,           // items.mr
  fireResist: number,            // items.fr
  coldResist: number,            // items.cr
  diseaseResist: number,         // items.dr
  corruptResist: number,         // items.svcorruption
  
  // Augmentations
  augments: [
    {
      slot: number,              // 1-6
      itemid: number,            // inventory.augslot1-6
      name: string,              // items.Name for augment
      icon: string               // items.icon for augment
    }
  ],
  
  // Ornamentation
  ornament: {
    icon: number,                // inventory.ornamenticon
    idfile: number,              // inventory.ornamentidfile
    heroModel: number            // inventory.ornament_hero_model
  },
  
  customData: string             // inventory.custom_data
}
```

## InventoryItem Structure (for bag slots)

```javascript
const InventoryItem = {
  id: number,                    // inventory.itemid
  name: string,                  // items.Name
  icon: string,                  // items.icon
  stackSize: number,             // inventory.charges (for stackable items)
  isNoDrop: boolean,             // !inventory.instnodrop
  customData: string             // inventory.custom_data
}
```

## EQEmu Database Mappings

### Class ID to Name Mapping
```javascript
const classNames = {
  1: 'Warrior', 2: 'Cleric', 3: 'Paladin', 4: 'Ranger',
  5: 'Shadowknight', 6: 'Druid', 7: 'Monk', 8: 'Bard',
  9: 'Rogue', 10: 'Shaman', 11: 'Necromancer', 12: 'Wizard',
  13: 'Magician', 14: 'Enchanter', 15: 'Beastlord', 16: 'Berserker'
}
```

### Race ID to Name Mapping
```javascript
const raceNames = {
  1: 'Human', 2: 'Barbarian', 3: 'Erudite', 4: 'Wood Elf',
  5: 'High Elf', 6: 'Dark Elf', 7: 'Half Elf', 8: 'Dwarf',
  9: 'Troll', 10: 'Ogre', 11: 'Halfling', 12: 'Gnome',
  128: 'Iksar', 130: 'Vah Shir', 330: 'Froglok', 522: 'Drakkin'
}
```

### Equipment Slot IDs
```javascript
const equipmentSlots = {
  0: 'ear1', 1: 'ear2', 2: 'head', 3: 'neck', 4: 'shoulder',
  5: 'charm', 6: 'face', 7: 'back', 8: 'arms', 9: 'wrist1',
  10: 'wrist2', 11: 'hands', 12: 'waist', 13: 'primary',
  14: 'secondary', 15: 'range', 16: 'ammo', 17: 'chest',
  18: 'legs', 19: 'feet', 20: 'ring1', 21: 'ring2'
}
```

### General Inventory Slot IDs
- Slots 22-31: General inventory "bag" slots (10 slots total)

## API Endpoints Needed

### Character Lookup
```
GET /api/characters/search?name=<characterName>
Returns: Array of matching characters with basic info
```

### Character List (All Characters)
```
GET /api/characters
Returns: Array of all characters with basic info from character_data
```

### Character Details  
```
GET /api/characters/<characterId>
Returns: Basic character object from character_data table
```

### Character Inventory
```
GET /api/characters/<characterId>/inventory
Returns: Character's inventory items with item details
```

### Character Currency
```
GET /api/characters/<characterId>/currency
Returns: Character's currency amounts from appropriate currency system
```

### Character Calculated Stats
```
GET /api/characters/<characterId>/stats
Returns: Calculated stats (max HP/MP, AC, ATK, resistances, weight)
```

### Individual Item Details
```
GET /api/item/<itemId>
Returns: Item details from items table
```

### Character Selection
```
POST /api/user/characters/primary
Body: { characterId: number }
Sets primary main character
```

```
POST /api/user/characters/secondary  
Body: { characterId: number }
Sets secondary main character
```

## Implementation Notes

1. **Class Icon Mapping**: Use `normalizeClassName()` method to map specialty titles to base classes for icon display

2. **Currency Formatting**: Use `formatCurrency()` method to add comma separators for large amounts

3. **Item Icons**: Item icons should be loaded from `/icons/items/<iconId>.gif` or similar path

4. **Augmentation Display**: Consider showing augment slots as small overlay icons on equipped items

5. **Weight Calculation**: Sum up all equipped item weights + inventory item weights

6. **AC/ATK Calculation**: Sum base character stats + all equipped item bonuses

7. **Resistance Totals**: Sum base character resistances + all equipped item resist bonuses

8. **Error Handling**: Provide fallback values (0 or null) for missing data

## Database Queries Required

### Main Character Query
```sql
SELECT 
  id, account_id, name, last_name, level, class, race, gender, deity,
  face, hair_color, hair_style, beard, beard_color, eye_color_1, eye_color_2,
  zone_id, zone_instance, x, y, z, heading,
  cur_hp, mana, endurance,
  str, sta, agi, dex, wis, int, cha,
  exp, aa_exp, aa_points,
  birthday, last_login, time_played, pvp_status
FROM character_data 
WHERE id = ?
```

### Equipment Query
```sql
SELECT inv.*, items.* 
FROM inventory inv
LEFT JOIN items ON inv.itemid = items.id
WHERE inv.charid = ? AND inv.slotid BETWEEN 0 AND 21
```

### Inventory Query  
```sql
SELECT inv.*, items.*
FROM inventory inv  
LEFT JOIN items ON inv.itemid = items.id
WHERE inv.charid = ? AND inv.slotid BETWEEN 22 AND 31
```

### Augmentation Queries
```sql
-- For each augment slot (1-6)
SELECT items.* FROM items WHERE id IN (
  SELECT augslot1 FROM inventory WHERE charid = ? AND augslot1 > 0
  UNION SELECT augslot2 FROM inventory WHERE charid = ? AND augslot2 > 0
  -- ... etc for slots 3-6
)
```

## Important EQEmu-Specific Notes

### 1. Currency Storage
**Important**: The character_data table does NOT contain currency fields (platinum, gold, silver, copper) in modern EQEmu. Currency may be stored in:
- Separate currency tables
- Item-based currency systems  
- Alternative account-based storage
- Server-specific implementations

You'll need to investigate your specific EQEmu server's currency implementation.

### 2. Max HP/Mana Calculation
The `cur_hp` and `mana` fields store current values, not maximum values. Maximum HP/Mana must be calculated using:
- Base racial stats
- Class multipliers
- Level bonuses
- Equipment bonuses
- Spell effects

### 3. AC and Attack Calculation
AC and Attack values are calculated from:
- Base character values
- Equipment AC/Attack values
- Spell effects and buffs
- Class-specific bonuses

### 4. Resistance Calculations
Resistances are calculated from:
- Base racial resistance values
- Equipment resistance bonuses
- Spell effects
- AA (Alternate Advancement) bonuses

### 5. Weight Calculation
Character weight is the sum of:
- All equipped item weights
- All inventory item weights
- Base character weight (if applicable)

### 6. Server-Specific Customizations
Many EQEmu servers have custom:
- Class modifications
- Race modifications  
- Custom items and stats
- Modified experience rates
- Custom currency systems

Always verify your specific server's database schema and customizations.

### 7. Performance Considerations
- Character queries can be expensive with full equipment/inventory joins
- Consider caching frequently accessed character data
- Use indexed queries for character lookups
- Implement pagination for character lists

This structure provides everything needed to populate the inventory UI with real character data from the EQEmu database, but requires server-specific adaptation for currency and calculated statistics.