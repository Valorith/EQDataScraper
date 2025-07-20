# Legacy Spell System Code to Remove from app.py

## Global Variables (Not explicitly declared but used throughout)
- `spells_cache` - Used to cache spell data by class
- `spell_details_cache` - Used to cache individual spell details  
- `pricing_lookup` - Used for fast pricing lookups
- `pricing_cache_loaded` - Flag indicating if pricing is loaded
- `cache_timestamp` - Timestamps for cache entries
- `last_scrape_time` - Tracking last scrape times
- `pricing_cache_timestamp` - Timestamps for pricing cache

## File Path Constants (Lines 455-457)
```python
SPELLS_CACHE_FILE = os.path.join(CACHE_DIR, 'spells_cache.json')
SPELL_DETAILS_CACHE_FILE = os.path.join(CACHE_DIR, 'spell_details_cache.json')
```

## Functions to Remove

### 1. `load_cache_from_database()` (Lines 1407-1463)
- Loads spell cache data from database tables

### 2. `load_cache_from_files()` (Lines 1464-1511)  
- Loads spell cache data from JSON files

### 3. `rebuild_pricing_lookup()` (Lines 1385-1400)
- Rebuilds pricing lookup index from spell_details_cache

### 4. `get_spells()` (Line 1757)
- Legacy spell retrieval function

### 5. `fetch_single_spell_pricing()` (Line 2477)
- Fetches pricing for individual spells

### 6. `refresh_spell_cache()` (Lines 1811-1813)
- Route to manually refresh spell cache

### 7. `get_expired_spell_cache_classes()` (Line 2652)
- Identifies expired spell cache classes

### 8. `refresh_expired_spell_caches()` (Line 2663)
- Refreshes expired spell caches

## Code References to Remove/Update

### In Various Functions:
- Lines 1369: Reference to `spell_details_cache` in `get_bulk_pricing_from_db()`
- Lines 1392-1398: Loop through `spell_details_cache` in `rebuild_pricing_lookup()`
- Lines 1409, 1420, 1432, 1454: References in `load_cache_from_database()`
- Lines 1466, 1476, 1487: References in `load_cache_from_files()`
- Lines 1580-1601: Saving spell caches in database save functions
- Lines 1644-1650: Saving single class spell cache
- Lines 1680-1693: Saving spell caches to files
- Lines 1752: Reference to `last_scrape_time`
- Lines 2480-2541: Multiple references to `spell_details_cache` in pricing functions
- Lines 2674, 2686: References to `spells_cache` in refresh functions
- Line 3699: Check for 'spell', 'cache', 'classes', 'scrape' in error handling

### Comments to Remove:
- Line 561: "# All spell system configuration and cache variables removed"
- Line 563: "# Spell system completely removed"  
- Line 3675: "# Spell system disabled - skipping spell data preloading"

## Database Table References (Should already be removed)
- `spell_cache` table
- `pricing_cache` table  
- `spell_details_cache` table

## Import Statement to Check
- Line 2469 in routes/admin.py imports these variables from app

## Recommendation
Since these global variables are not explicitly declared at module level but are being used throughout the code, they need to be either:
1. Properly declared at module level with empty initializations, OR
2. All references to them should be removed

The error "Failed to scrape Druid spell" is likely coming from code trying to access these undefined variables.