# Inventory Debugging Guide

## Issue: Inventory slots showing wrong items compared to Magelo

### What was found:
1. Backend correctly queries EQEmu database slots 251-330
2. Valgor has items in slots: 251-260, 296-297, 309-310, 312-315, 320-325, 330
3. Frontend was only displaying first 10 slots (251-260) in a 2x5 grid

### Changes Made:
1. **Characters.vue**: Updated `loadCharacterInventory()` to process slots 251-330 and show first 20 items
2. **CharacterInventory.vue**: Changed CSS grid from 2x5 to 2x10 with scrolling

### Debugging Steps:
1. **Test with current data**: 
   ```bash
   curl -s "http://localhost:5001/api/characters/2653/inventory" | python3 -c "
   import json, sys
   data = json.load(sys.stdin)
   items = [item for item in data['inventory'] if item['itemid']]
   for i, item in enumerate(items[:20]):
       print(f'{i+1}. Slot {item[\"slotid\"]}: {item[\"item_name\"]}')
   "
   ```

2. **Compare with Magelo**: 
   - Check if Magelo shows containers/backpacks that should be in the main inventory
   - Verify if the displayed items match what's actually in slots 251+

3. **Potential Issues**:
   - Magelo might display different slot ranges
   - Database might have different data than Magelo shows
   - Character may have been updated between Magelo capture and database state

### Expected Result:
After the fix, the inventory panel should show up to 20 items from the character's actual inventory (slots 251-330) instead of just the first 10 slots.

### Test Character: Valgor (ID 2653)
- **Before fix**: Showed 10 items (slots 251-260)  
- **After fix**: Should show up to 20 items from all available slots