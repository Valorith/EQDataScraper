#!/usr/bin/env node

/**
 * Focused Zone Navigation Testing: Classic through Luclin
 * Tests only the core EverQuest zones from Classic, Kunark, Velious, and Luclin
 * to achieve near-perfect navigation for foundational content
 */

const fs = require('fs');
const path = require('path');

// Color codes for terminal output
const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m',
  bold: '\x1b[1m'
};

// Load comprehensive zone database from EQResource
const { COMPREHENSIVE_ZONE_DATABASE } = require('./eqresource-zones.js');

// Focus on Classic through Luclin zones only
const CLASSIC_THROUGH_LUCLIN_ZONES = [
  // Classic zones
  ...COMPREHENSIVE_ZONE_DATABASE.filter(zone => 
    ['qeynos', 'qeynos2', 'qrg', 'qeytoqrg', 'highkeep', 'freportn', 'freportw', 'freporte',
     'runnyeye', 'qey2hh1', 'northkarana', 'southkarana', 'eastkarana', 'beholder', 'blackburrow',
     'paw', 'rivervale', 'kithicor', 'commons', 'ecommons', 'erudnint', 'erudnext', 'nektulos',
     'lavastorm', 'halas', 'everfrost', 'soldunga', 'soldungb', 'misty', 'northro', 'southro',
     'befallen', 'oasis', 'tox', 'toxxulia', 'hole', 'neriaka', 'neriakb', 'neriakc', 'neriakd',
     'najena', 'qcat', 'innothule', 'feerrott', 'cazicthule', 'oggok', 'rathemtn', 'lakerathe',
     'grobb', 'aviak', 'gukbottom', 'guktop', 'guk', 'perm', 'butcher', 'oot', 'cauldron',
     'unrest', 'kedge', 'gfaydark', 'akanon', 'steamfont', 'lfaydark', 'crushbone', 'mistmoore',
     'kaladima', 'kaladimb', 'felwithea', 'felwitheb', 'kelethin', 'highpass', 'paineel'].includes(zone.shortName)
  ),
  
  // Kunark zones
  ...COMPREHENSIVE_ZONE_DATABASE.filter(zone =>
    ['fieldofbone', 'warslikswood', 'droga', 'cabwest', 'cabeast', 'swampofnohope', 'firiona',
     'lakeofillomen', 'dreadlands', 'burningwood', 'kaesora', 'sebilis', 'citymist', 'skyfire',
     'frontiermtns', 'overthere', 'emeraldjungle', 'trakanon', 'timorous', 'kurn', 'chardok',
     'nurga', 'veeshan', 'howlingstones', 'chardokb', 'karnor'].includes(zone.shortName)
  ),
  
  // Velious zones
  ...COMPREHENSIVE_ZONE_DATABASE.filter(zone =>
    ['cobaltscar', 'greatdivide', 'eastwastes', 'iceclad', 'frozenshadow', 'westwastes',
     'wakening', 'velketor', 'kael', 'skyshrine', 'thurgadina', 'thurgadinb', 'crystal',
     'necropolis', 'templeveeshan', 'sirens', 'sleeper'].includes(zone.shortName)
  ),
  
  // Luclin zones
  ...COMPREHENSIVE_ZONE_DATABASE.filter(zone =>
    ['bazaar', 'shadowhaven', 'nexus', 'sharvahl', 'paludal', 'fungusgrove', 'twilight',
     'grimling', 'tenebrous', 'maiden', 'dawnshroud', 'scarlet', 'umbral', 'acrylia',
     'ssratemple', 'griegsend', 'thedeep', 'netherbian', 'sseru', 'mseru', 'mons',
     'vexthal', 'katta'].includes(zone.shortName)
  ),
  
  // Add common planes from Classic
  { shortName: 'airplane', longName: 'Plane of Sky' },
  { shortName: 'fearplane', longName: 'Plane of Fear' },
  { shortName: 'hateplane', longName: 'Plane of Hate' },
  { shortName: 'hateplaneb', longName: 'Plane of Hate B' }
];

// Get list of map files that correspond to Classic-Luclin zones
const CLASSIC_LUCLIN_MAP_PATTERNS = [
  // Classic zones
  'qeynos', 'qrg', 'qeytoqrg', 'highkeep', 'freeport', 'runnyeye', 'karana', 'blackburrow',
  'paw', 'rivervale', 'kithicor', 'commons', 'erudin', 'nektulos', 'lavastorm', 'halas',
  'everfrost', 'soldunga', 'soldungb', 'misty', 'ro', 'befallen', 'oasis', 'tox',
  'hole', 'neriak', 'najena', 'qcat', 'innothule', 'feerrott', 'cazic', 'oggok',
  'rathe', 'lake', 'grobb', 'aviak', 'guk', 'perm', 'butcher', 'oot', 'cauldron',
  'unrest', 'kedge', 'faydark', 'akanon', 'steamfont', 'crushbone', 'mistmoore',
  'kaladim', 'felwithe', 'kelethin', 'highpass', 'paineel',
  
  // Kunark zones
  'fieldofbone', 'warsliks', 'droga', 'cabilis', 'swamp', 'firiona', 'lakeofill',
  'dreadlands', 'burning', 'kaesora', 'sebilis', 'citymist', 'skyfire', 'frontier',
  'overthere', 'emerald', 'trakanon', 'timorous', 'kurn', 'chardok', 'nurga',
  'veeshan', 'howling', 'karnor',
  
  // Velious zones
  'cobalt', 'great', 'wastes', 'iceclad', 'frozen', 'wakening', 'velketor', 'kael',
  'skyshrine', 'thurg', 'crystal', 'necropolis', 'temple', 'sirens', 'sleeper',
  
  // Luclin zones
  'bazaar', 'shadow', 'nexus', 'shar', 'paludal', 'fungus', 'twilight', 'grimling',
  'tenebrous', 'maiden', 'dawn', 'scarlet', 'umbral', 'acrylia', 'ssra', 'grieg',
  'deep', 'nether', 'sseru', 'mseru', 'mons', 'vex', 'katta'
];

/**
 * Check if a map file corresponds to a Classic-Luclin zone
 */
function isClassicLuclinZone(mapFileName) {
  const baseName = mapFileName.replace('_1.txt', '').replace('_2.txt', '').replace('.txt', '');
  return CLASSIC_LUCLIN_MAP_PATTERNS.some(pattern => baseName.includes(pattern));
}

/**
 * Parse portal data from map file
 */
function parseMapPortals(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n').filter(line => line.trim());
    const portals = [];

    for (const line of lines) {
      if (line.startsWith('P ')) {
        const parts = line.split(', ');
        if (parts.length >= 8) {
          const labelParts = parts.slice(7).join(', ');
          const portalType = parts[6];
          if (portalType === '3') {
            portals.push({
              x: parseFloat(parts[0].substring(2)),
              y: parseFloat(parts[1]),
              z: parseFloat(parts[2]),
              r: parseInt(parts[3]),
              g: parseInt(parts[4]),
              b: parseInt(parts[5]),
              type: parseInt(portalType),
              label: labelParts.trim(),
              sourceFile: path.basename(filePath)
            });
          }
        }
      }
    }
    
    return portals;
  } catch (error) {
    console.error(`Error parsing ${filePath}:`, error.message);
    return [];
  }
}

/**
 * Enhanced zone matching logic focused on Classic-Luclin
 */
function testZoneMatching(portalLabel) {
  let zoneName = portalLabel;
  if (zoneName.startsWith('to_')) {
    zoneName = zoneName.substring(3);
  }
  
  const zoneNameLower = zoneName.replace(/_/g, ' ').toLowerCase();
  
  // Try exact match first
  for (const zone of CLASSIC_THROUGH_LUCLIN_ZONES) {
    if (zone.shortName.toLowerCase() === zoneNameLower || 
        zone.longName.toLowerCase() === zoneNameLower) {
      return zone;
    }
  }
  
  // Enhanced pattern matching for Classic-Luclin zones
  for (const zone of CLASSIC_THROUGH_LUCLIN_ZONES) {
    const shortNameLower = zone.shortName.toLowerCase();
    
    // Classic zone patterns
    if (zoneNameLower.includes('plane of knowledge') || zoneNameLower.includes('the plane of knowledge')) {
      if (shortNameLower === 'poknowledge') return zone;
    }
    
    if (zoneNameLower.includes('plane of sky') || zoneNameLower.includes('sky')) {
      if (shortNameLower === 'airplane') return zone;
    }
    
    if (zoneNameLower.includes('plane of fear') || zoneNameLower.includes('fear')) {
      if (shortNameLower === 'fearplane') return zone;
    }
    
    if (zoneNameLower.includes('plane of hate') || zoneNameLower.includes('hate')) {
      if (shortNameLower === 'hateplane' || shortNameLower === 'hateplaneb') return zone;
    }
    
    // Guk variations
    if ((zoneNameLower.includes('city') && zoneNameLower.includes('guk')) || 
        zoneNameLower.includes('the city of guk')) {
      if (shortNameLower === 'guk') return zone;
    }
    
    if (zoneNameLower.includes('upper') && zoneNameLower.includes('guk')) {
      if (shortNameLower === 'guktop') return zone;
    }
    
    if (zoneNameLower.includes('lower') && zoneNameLower.includes('guk')) {
      if (shortNameLower === 'gukbottom') return zone;
    }
    
    if ((zoneNameLower.includes('ruins') && zoneNameLower.includes('old') && zoneNameLower.includes('guk')) ||
        (zoneNameLower.includes('ruins') && zoneNameLower.includes('guk'))) {
      if (shortNameLower === 'gukbottom') return zone;
    }
    
    // Feerott variations
    if (zoneNameLower.includes('feerott') || zoneNameLower.includes('feerrott')) {
      if (shortNameLower === 'feerrott') return zone;
    }
    
    // Desert of Ro variations
    if (zoneNameLower.includes('south') && zoneNameLower.includes('desert') && zoneNameLower.includes('ro')) {
      if (shortNameLower === 'southro') return zone;
    }
    
    if (zoneNameLower.includes('north') && zoneNameLower.includes('desert') && zoneNameLower.includes('ro')) {
      if (shortNameLower === 'northro') return zone;
    }
    
    // Steamfont variations
    if (zoneNameLower.includes('steamfont') && zoneNameLower.includes('mountains')) {
      if (shortNameLower === 'steamfont') return zone;
    }
    
    // Commonlands variations
    if (zoneNameLower.includes('commonlands') || zoneNameLower.includes('the commonlands')) {
      if (shortNameLower === 'commons' || shortNameLower === 'ecommons') return zone;
    }
    
    // Lake Rathetear variations
    if (zoneNameLower.includes('lake rathetear') || zoneNameLower.includes('lake_rathetear')) {
      if (shortNameLower === 'lakerathe') return zone;
    }
    
    // Kunark zone patterns
    if (zoneNameLower.includes('field of bone') || zoneNameLower.includes('the field of bone')) {
      if (shortNameLower === 'fieldofbone') return zone;
    }
    
    if (zoneNameLower.includes('warsliks woods') || zoneNameLower.includes('warsliks wood')) {
      if (shortNameLower === 'warslikswood') return zone;
    }
    
    if (zoneNameLower.includes('swamp of no hope') || zoneNameLower.includes('the swamp of no hope')) {
      if (shortNameLower === 'swampofnohope') return zone;
    }
    
    if (zoneNameLower.includes('lake of ill omen')) {
      if (shortNameLower === 'lakeofillomen') return zone;
    }
    
    if (zoneNameLower.includes('burning wood')) {
      if (shortNameLower === 'burningwood') return zone;
    }
    
    if (zoneNameLower.includes('skyfire mountains')) {
      if (shortNameLower === 'skyfire') return zone;
    }
    
    if (zoneNameLower.includes('frontier mountains')) {
      if (shortNameLower === 'frontiermtns') return zone;
    }
    
    if (zoneNameLower.includes('the overthere') || zoneNameLower.includes('overthere')) {
      if (shortNameLower === 'overthere') return zone;
    }
    
    if (zoneNameLower.includes('emerald jungle')) {
      if (shortNameLower === 'emeraldjungle') return zone;
    }
    
    if (zoneNameLower.includes('trakanon') && zoneNameLower.includes('teeth')) {
      if (shortNameLower === 'trakanon') return zone;
    }
    
    if (zoneNameLower.includes('timorous deep')) {
      if (shortNameLower === 'timorous') return zone;
    }
    
    if (zoneNameLower.includes('kurn') && zoneNameLower.includes('tower')) {
      if (shortNameLower === 'kurn') return zone;
    }
    
    if (zoneNameLower.includes('old sebilis')) {
      if (shortNameLower === 'sebilis') return zone;
    }
    
    if (zoneNameLower.includes('city of mist')) {
      if (shortNameLower === 'citymist') return zone;
    }
    
    if (zoneNameLower.includes('howling stones')) {
      if (shortNameLower === 'howlingstones') return zone;
    }
    
    if (zoneNameLower.includes('karnor') && zoneNameLower.includes('castle')) {
      if (shortNameLower === 'karnor') return zone;
    }
    
    // Velious zone patterns
    if (zoneNameLower.includes('great divide') || zoneNameLower.includes('the great divide')) {
      if (shortNameLower === 'greatdivide') return zone;
    }
    
    if (zoneNameLower.includes('eastern wastes') || zoneNameLower.includes('the eastern wastes')) {
      if (shortNameLower === 'eastwastes') return zone;
    }
    
    if (zoneNameLower.includes('western wastes') || zoneNameLower.includes('the western wastes')) {
      if (shortNameLower === 'westwastes') return zone;
    }
    
    if (zoneNameLower.includes('iceclad ocean') || zoneNameLower.includes('the iceclad ocean')) {
      if (shortNameLower === 'iceclad') return zone;
    }
    
    if (zoneNameLower.includes('tower of frozen shadow')) {
      if (shortNameLower === 'frozenshadow') return zone;
    }
    
    if (zoneNameLower.includes('wakening land') || zoneNameLower.includes('the wakening land')) {
      if (shortNameLower === 'wakening') return zone;
    }
    
    if (zoneNameLower.includes('kael drakkel')) {
      if (shortNameLower === 'kael') return zone;
    }
    
    if (zoneNameLower.includes('crystal caverns')) {
      if (shortNameLower === 'crystal') return zone;
    }
    
    if (zoneNameLower.includes('dragon necropolis')) {
      if (shortNameLower === 'necropolis') return zone;
    }
    
    if (zoneNameLower.includes('temple of veeshan')) {
      if (shortNameLower === 'templeveeshan') return zone;
    }
    
    if (zoneNameLower.includes('siren') && zoneNameLower.includes('grotto')) {
      if (shortNameLower === 'sirens') return zone;
    }
    
    if (zoneNameLower.includes('sleeper') && zoneNameLower.includes('tomb')) {
      if (shortNameLower === 'sleeper') return zone;
    }
    
    // Luclin zone patterns
    if (zoneNameLower.includes('the bazaar') || zoneNameLower.includes('bazaar')) {
      if (shortNameLower === 'bazaar') return zone;
    }
    
    if (zoneNameLower.includes('shadow haven')) {
      if (shortNameLower === 'shadowhaven') return zone;
    }
    
    if (zoneNameLower.includes('the nexus') || zoneNameLower.includes('nexus')) {
      if (shortNameLower === 'nexus') return zone;
    }
    
    if (zoneNameLower.includes('shar vahl')) {
      if (shortNameLower === 'sharvahl') return zone;
    }
    
    if (zoneNameLower.includes('paludal caverns')) {
      if (shortNameLower === 'paludal') return zone;
    }
    
    if (zoneNameLower.includes('fungus grove')) {
      if (shortNameLower === 'fungusgrove') return zone;
    }
    
    if (zoneNameLower.includes('grimling forest')) {
      if (shortNameLower === 'grimling') return zone;
    }
    
    if (zoneNameLower.includes('maiden') && zoneNameLower.includes('eye')) {
      if (shortNameLower === 'maiden') return zone;
    }
    
    if (zoneNameLower.includes('dawnshroud peaks')) {
      if (shortNameLower === 'dawnshroud') return zone;
    }
    
    if (zoneNameLower.includes('scarlet desert')) {
      if (shortNameLower === 'scarlet') return zone;
    }
    
    if (zoneNameLower.includes('umbral plains')) {
      if (shortNameLower === 'umbral') return zone;
    }
    
    if (zoneNameLower.includes('acrylia caverns')) {
      if (shortNameLower === 'acrylia') return zone;
    }
    
    if (zoneNameLower.includes('ssraeshza temple') || zoneNameLower.includes('ssrae')) {
      if (shortNameLower === 'ssratemple') return zone;
    }
    
    if (zoneNameLower.includes('grieg') && zoneNameLower.includes('end')) {
      if (shortNameLower === 'griegsend') return zone;
    }
    
    if (zoneNameLower.includes('netherbian lair')) {
      if (shortNameLower === 'netherbian') return zone;
    }
    
    if (zoneNameLower.includes('sanctus seru')) {
      if (shortNameLower === 'sseru') return zone;
    }
    
    if (zoneNameLower.includes('marus seru')) {
      if (shortNameLower === 'mseru') return zone;
    }
    
    if (zoneNameLower.includes('mons letalis')) {
      if (shortNameLower === 'mons') return zone;
    }
    
    if (zoneNameLower.includes('vex thal')) {
      if (shortNameLower === 'vexthal') return zone;
    }
    
    if (zoneNameLower.includes('katta castellum')) {
      if (shortNameLower === 'katta') return zone;
    }
    
    // Enhanced "The" prefix handling for Classic-Luclin zones
    if (zoneNameLower.startsWith('the ')) {
      const withoutThe = zoneNameLower.substring(4);
      
      // Try matching without "The" prefix
      if (zone.longName.toLowerCase().includes(withoutThe) || 
          zone.shortName.toLowerCase() === withoutThe.replace(/\s+/g, '')) {
        return zone;
      }
      
      // Specific "The" prefix mappings for Classic-Luclin
      const theZoneMappings = {
        'greater faydark': 'gfaydark',
        'lesser faydark': 'lfaydark', 
        'plane of knowledge': 'poknowledge',
        'ocean of tears': 'oot',
        'estate of unrest': 'unrest',
        'steamfont mountains': 'steamfont',
        'butcherblock mountains': 'butcher',
        'lavastorm mountains': 'lavastorm',
        'commonlands': 'commons',
        'feerrott': 'feerrott',
        'city of guk': 'guk',
        'ruins of old guk': 'gukbottom',
        'field of bone': 'fieldofbone',
        'overthere': 'overthere',
        'swamp of no hope': 'swampofnohope',
        'burning woods': 'burningwood',
        'emerald jungle': 'emeraldjungle',
        'dreadlands': 'dreadlands',
        'great divide': 'greatdivide',
        'eastern wastes': 'eastwastes',
        'western wastes': 'westwastes',
        'iceclad ocean': 'iceclad',
        'wakening land': 'wakening',
        'tower of frozen shadow': 'frozenshadow',
        'temple of veeshan': 'templeveeshan',
        'sleeper tomb': 'sleeper',
        'bazaar': 'bazaar',
        'nexus': 'nexus',
        'maiden eye': 'maiden',
        'scarlet desert': 'scarlet',
        'umbral plains': 'umbral',
        'deep': 'thedeep',
        'grey': 'thegrey'
      };
      
      if (theZoneMappings[withoutThe] && shortNameLower === theZoneMappings[withoutThe]) {
        return zone;
      }
    }
    
    // Handle Nagafen's Lair variations
    if (zoneNameLower.includes('nagafen') && (zoneNameLower.includes('lair') || zoneNameLower.includes('`s'))) {
      if (shortNameLower === 'soldungb') return zone;
    }
    
    // Handle Solusek's Eye variations
    if (zoneNameLower.includes('solusek') && (zoneNameLower.includes('eye') || zoneNameLower.includes('`s'))) {
      if (shortNameLower === 'soldunga') return zone;
    }
    
    // Handle Cabilis variations
    if (zoneNameLower.includes('cabilis')) {
      if (zoneNameLower.includes('east') && shortNameLower === 'cabeast') return zone;
      if (zoneNameLower.includes('west') && shortNameLower === 'cabwest') return zone;
    }
    
    // Handle Freeport variations  
    if (zoneNameLower.includes('freeport')) {
      if (zoneNameLower.includes('east') && shortNameLower === 'freporte') return zone;
      if (zoneNameLower.includes('west') && shortNameLower === 'freportw') return zone;
      if (zoneNameLower.includes('north') && shortNameLower === 'freportn') return zone;
    }
    
    // Handle Neriak variations
    if (zoneNameLower.includes('neriak')) {
      if (zoneNameLower.includes('foreign') && shortNameLower === 'neriaka') return zone;
      if (zoneNameLower.includes('commons') && shortNameLower === 'neriakb') return zone;
      if (zoneNameLower.includes('third') && shortNameLower === 'neriakc') return zone;
      if (zoneNameLower.includes('palace') && shortNameLower === 'neriakd') return zone;
    }
    
    // Handle Echo Caverns variations
    if (zoneNameLower.includes('echo') && zoneNameLower.includes('caverns')) {
      if (shortNameLower === 'echo' || shortNameLower === 'echocaverns') return zone;
    }
    
    // Handle zone numbering (like zones with _1, _2 variations)
    const cleanZoneName = zoneNameLower.replace(/\s*\(\d+\)/, '').replace(/_\d+$/, '');
    if (cleanZoneName !== zoneNameLower) {
      // Try matching the clean name recursively
      const cleanMatch = testZoneMatching(`to_${cleanZoneName.replace(/\s+/g, '_')}`);
      if (cleanMatch) return cleanMatch;
    }
    
    // Enhanced substring matching for Classic-Luclin with better scoring
    const zoneWords = zoneNameLower.split(/\s+/);
    const longNameWords = zone.longName.toLowerCase().split(/\s+/);
    
    // Count matching words
    let matchingWords = 0;
    for (const word of zoneWords) {
      if (longNameWords.some(longWord => longWord.includes(word) || word.includes(longWord))) {
        matchingWords++;
      }
    }
    
    // Require higher match threshold for quality
    if (matchingWords >= Math.min(2, zoneWords.length) && matchingWords >= zoneWords.length * 0.6) {
      return zone;
    }
    
    // Basic substring matching as final fallback
    if (zoneNameLower.includes(shortNameLower) || shortNameLower.includes(zoneNameLower)) {
      return zone;
    }
  }
  
  return null;
}

/**
 * Main testing function for Classic-Luclin zones
 */
async function runClassicLuclinTests() {
  const mapsDir = path.join(__dirname, 'Maps');
  
  if (!fs.existsSync(mapsDir)) {
    console.error(`${colors.red}Maps directory not found at: ${mapsDir}${colors.reset}`);
    process.exit(1);
  }
  
  console.log(`${colors.bold}${colors.blue}🗺️  Classic through Luclin Zone Navigation Testing${colors.reset}\n`);
  
  // Get all _1.txt files that correspond to Classic-Luclin zones
  const allLabelFiles = fs.readdirSync(mapsDir).filter(file => file.endsWith('_1.txt'));
  const classicLuclinFiles = allLabelFiles.filter(file => isClassicLuclinZone(file)).sort();
  
  console.log(`${colors.yellow}Focusing on ${classicLuclinFiles.length} Classic-Luclin zones out of ${allLabelFiles.length} total zones${colors.reset}\n`);
  
  let totalPortals = 0;
  let successfulMatches = 0;
  let failedMatches = [];
  let zoneNavigations = {};
  
  // Process each Classic-Luclin zone's label file
  for (const labelFile of classicLuclinFiles) {
    const filePath = path.join(mapsDir, labelFile);
    const zoneName = labelFile.replace('_1.txt', '');
    const portals = parseMapPortals(filePath);
    
    if (portals.length > 0) {
      console.log(`${colors.yellow}📂 ${zoneName}${colors.reset} (${portals.length} portals)`);
      
      for (const portal of portals) {
        totalPortals++;
        const match = testZoneMatching(portal.label);
        
        if (match) {
          successfulMatches++;
          console.log(`  ${colors.green}✓${colors.reset} ${portal.label} → ${match.shortName} (${match.longName})`);
          
          // Track navigation relationships
          if (!zoneNavigations[zoneName]) {
            zoneNavigations[zoneName] = [];
          }
          zoneNavigations[zoneName].push({
            destination: match.shortName,
            label: portal.label
          });
        } else {
          failedMatches.push({
            sourceZone: zoneName,
            portalLabel: portal.label,
            sourceFile: labelFile
          });
          console.log(`  ${colors.red}✗${colors.reset} ${portal.label} → NO MATCH FOUND`);
        }
      }
      console.log();
    }
  }
  
  // Summary
  console.log(`${colors.bold}${colors.blue}📊 Classic-Luclin Testing Summary${colors.reset}`);
  console.log(`Total Classic-Luclin portals tested: ${totalPortals}`);
  console.log(`${colors.green}Successful matches: ${successfulMatches}${colors.reset}`);
  console.log(`${colors.red}Failed matches: ${failedMatches.length}${colors.reset}`);
  console.log(`Success rate: ${((successfulMatches / totalPortals) * 100).toFixed(1)}%\n`);
  
  // Detailed failure analysis for Classic-Luclin zones
  if (failedMatches.length > 0) {
    console.log(`${colors.bold}${colors.red}❌ Classic-Luclin Navigation Failures:${colors.reset}`);
    for (const failure of failedMatches) {
      console.log(`  ${failure.sourceZone} → "${failure.portalLabel}" (from ${failure.sourceFile})`);
    }
    console.log();
    
    // Analyze failure patterns
    console.log(`${colors.bold}${colors.yellow}🔍 Failure Analysis:${colors.reset}`);
    const failurePatterns = {};
    for (const failure of failedMatches) {
      const pattern = failure.portalLabel.replace(/to_/, '').replace(/_.*/, '');
      failurePatterns[pattern] = (failurePatterns[pattern] || 0) + 1;
    }
    
    const sortedPatterns = Object.entries(failurePatterns)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 10);
    
    for (const [pattern, count] of sortedPatterns) {
      console.log(`  ${count}x "${pattern}"`);
    }
  }
  
  const targetSuccessRate = 95.0; // Target for Classic-Luclin zones
  const currentSuccessRate = (successfulMatches / totalPortals) * 100;
  
  console.log(`\n${colors.bold}🎯 Classic-Luclin Target: ${targetSuccessRate}% success rate${colors.reset}`);
  if (currentSuccessRate >= targetSuccessRate) {
    console.log(`${colors.green}✅ TARGET ACHIEVED! ${currentSuccessRate.toFixed(1)}% success rate${colors.reset}`);
  } else {
    console.log(`${colors.yellow}⚠️  Need ${(targetSuccessRate - currentSuccessRate).toFixed(1)}% more to reach target${colors.reset}`);
  }
  
  console.log(`\n${colors.bold}🎉 Classic-Luclin testing complete!${colors.reset}`);
  
  // Exit with error code if below target
  if (currentSuccessRate < targetSuccessRate) {
    process.exit(1);
  }
}

// Run the focused tests
if (require.main === module) {
  runClassicLuclinTests().catch(error => {
    console.error(`${colors.red}Testing failed:${colors.reset}`, error);
    process.exit(1);
  });
}

module.exports = { runClassicLuclinTests, testZoneMatching };