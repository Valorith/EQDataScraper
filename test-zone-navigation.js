#!/usr/bin/env node

/**
 * Automated Zone Navigation Testing System
 * Tests all portal navigations by extracting portal data from map files
 * and checking if zone matching logic works correctly
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

// Zone database from authoritative EQResource.com  
const availableZones = [
  // Add planes that might be missing from EQResource
  { shortName: 'airplane', longName: 'Plane of Sky' },
  { shortName: 'fearplane', longName: 'Plane of Fear' },
  { shortName: 'hateplane', longName: 'Plane of Hate' },
  { shortName: 'hateplaneb', longName: 'Plane of Hate B' },
  { shortName: 'growthplane', longName: 'Plane of Growth' },
  { shortName: 'mischiefplane', longName: 'Plane of Mischief' },
  
  // Load comprehensive authoritative database
  ...COMPREHENSIVE_ZONE_DATABASE
];

/**
 * Parse portal data from map file
 * @param {string} filePath Path to map file
 * @returns {Array} Array of portal objects
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
          // Extract zone name from portal label
          const labelParts = parts.slice(7).join(', ');
          
          // Only test zone portals (type 3), skip other portal types
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
 * Test zone matching logic (simplified version of the Vue component logic)
 * @param {string} portalLabel The portal label from map file
 * @returns {object|null} Matching zone or null
 */
function testZoneMatching(portalLabel) {
  // Extract zone name from portal label
  let zoneName = portalLabel;
  if (zoneName.startsWith('to_')) {
    zoneName = zoneName.substring(3);
  }
  
  // Remove underscores and convert to lowercase
  const zoneNameLower = zoneName.replace(/_/g, ' ').toLowerCase();
  
  // Try exact match first
  for (const zone of availableZones) {
    if (zone.shortName.toLowerCase() === zoneNameLower || 
        zone.longName.toLowerCase() === zoneNameLower) {
      return zone;
    }
  }
  
  // Test specific pattern matching logic
  for (const zone of availableZones) {
    const shortNameLower = zone.shortName.toLowerCase();
    
    // Feerott variations
    if (zoneNameLower.includes('feerott') || zoneNameLower.includes('feerrott')) {
      if (shortNameLower === 'feerrott') return zone;
    }
    
    // Plane of Knowledge variations (most common failure)
    if (zoneNameLower.includes('plane of knowledge') || zoneNameLower.includes('the plane of knowledge')) {
      if (shortNameLower === 'poknowledge') return zone;
    }
    
    // Plane of Tranquility variations
    if (zoneNameLower.includes('plane of tranquility') || zoneNameLower.includes('the plane of tranquility')) {
      if (shortNameLower === 'potranquility') return zone;
    }
    
    // Eastern/Western Wastes variations
    if (zoneNameLower.includes('eastern wastes') || zoneNameLower.includes('the eastern wastes')) {
      if (shortNameLower === 'eastwastes') return zone;
    }
    if (zoneNameLower.includes('western wastes') || zoneNameLower.includes('the western wastes')) {
      if (shortNameLower === 'westwastes') return zone;
    }
    
    // Field of Scale variations
    if (zoneNameLower.includes('field of scale')) {
      if (shortNameLower === 'fieldofscale') return zone;
    }
    
    // Iceclad Ocean variations
    if (zoneNameLower.includes('iceclad ocean') || zoneNameLower.includes('the iceclad ocean')) {
      if (shortNameLower === 'iceclad') return zone;
    }
    
    // The Overthere variations
    if (zoneNameLower.includes('the overthere') || zoneNameLower.includes('overthere')) {
      if (shortNameLower === 'overthere') return zone;
    }
    
    // Field of Bone variations
    if (zoneNameLower.includes('field of bone') || zoneNameLower.includes('the field of bone')) {
      if (shortNameLower === 'fieldofbone') return zone;
    }
    
    // Frontier Mountains variations
    if (zoneNameLower.includes('frontier mountains')) {
      if (shortNameLower === 'frontier') return zone;
    }
    
    // Great Divide variations
    if (zoneNameLower.includes('great divide') || zoneNameLower.includes('the great divide')) {
      if (shortNameLower === 'greatdivide') return zone;
    }
    
    // Warsliks Woods variations
    if (zoneNameLower.includes('warsliks woods') || zoneNameLower.includes('the warsliks woods')) {
      if (shortNameLower === 'warslikswood') return zone;
    }
    
    // Swamp of No Hope variations
    if (zoneNameLower.includes('swamp of no hope') || zoneNameLower.includes('the swamp of no hope')) {
      if (shortNameLower === 'swampofnohope') return zone;
    }
    
    // Lake Rathetear variations
    if (zoneNameLower.includes('lake rathetear') || zoneNameLower.includes('lake_rathetear')) {
      if (shortNameLower === 'lakerathe' || shortNameLower === 'lakerathetear') return zone;
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
    
    // Desert of Ro variations
    if (zoneNameLower.includes('south') && zoneNameLower.includes('desert') && zoneNameLower.includes('ro')) {
      if (shortNameLower === 'southro') return zone;
    }
    
    if (zoneNameLower.includes('north') && zoneNameLower.includes('desert') && zoneNameLower.includes('ro')) {
      if (shortNameLower === 'northro') return zone;
    }
    
    // Plane variations
    if (zoneNameLower.includes('plane of sky') || zoneNameLower.includes('sky')) {
      if (shortNameLower === 'airplane') return zone;
    }
    
    if (zoneNameLower.includes('plane of fear') || zoneNameLower.includes('fear')) {
      if (shortNameLower === 'fearplane') return zone;
    }
    
    if (zoneNameLower.includes('plane of time') || zoneNameLower.includes('the plane of time')) {
      if (shortNameLower === 'potime') return zone;
    }
    
    // Commonlands variations
    if (zoneNameLower.includes('commonlands') || zoneNameLower.includes('the commonlands')) {
      if (shortNameLower === 'commons' || shortNameLower === 'commonlands' || 
          shortNameLower === 'eastcommons' || shortNameLower === 'westcommons') return zone;
    }
    
    // Steamfont variations
    if (zoneNameLower.includes('steamfont') && zoneNameLower.includes('mountains')) {
      if (shortNameLower === 'steamfont') return zone;
    }
    
    // Toxxulia Forest variations
    if (zoneNameLower.includes('toxxulia') && zoneNameLower.includes('forest')) {
      if (shortNameLower === 'toxxulia' || shortNameLower === 'tox') return zone;
    }
    
    // Bazaar variations
    if (zoneNameLower.includes('bazaar') || zoneNameLower.includes('the bazaar')) {
      if (shortNameLower === 'bazaar') return zone;
    }
    
    // Nexus variations
    if (zoneNameLower.includes('nexus') || zoneNameLower.includes('the nexus')) {
      if (shortNameLower === 'nexus') return zone;
    }
    
    // Shadow Haven variations
    if (zoneNameLower.includes('shadow haven')) {
      if (shortNameLower === 'shadowhaven') return zone;
    }
    
    // Additional zone variations from second wave analysis
    if (zoneNameLower.includes('lake of ill omen') || zoneNameLower.includes('lake_of_ill_omen')) {
      if (shortNameLower === 'lakeofillomen') return zone;
    }
    
    if (zoneNameLower.includes('firiona vie')) {
      if (shortNameLower === 'firiona') return zone;
    }
    
    if (zoneNameLower.includes('cobalt scar')) {
      if (shortNameLower === 'cobaltscar') return zone;
    }
    
    if (zoneNameLower.includes('the dreadlands') || zoneNameLower.includes('dreadlands')) {
      if (shortNameLower === 'dreadlands') return zone;
    }
    
    if (zoneNameLower.includes('cabilis east')) {
      if (shortNameLower === 'cabeast') return zone;
    }
    
    if (zoneNameLower.includes('cabilis west')) {
      if (shortNameLower === 'cabwest') return zone;
    }
    
    if (zoneNameLower.includes('timorous deep')) {
      if (shortNameLower === 'timorous') return zone;
    }
    
    if (zoneNameLower.includes('temple of droga') || zoneNameLower.includes('the temple of droga')) {
      if (shortNameLower === 'droga') return zone;
    }
    
    if (zoneNameLower.includes('echo caverns')) {
      if (shortNameLower === 'echocaverns') return zone;
    }
    
    if (zoneNameLower.includes('grimling forest')) {
      if (shortNameLower === 'grimling') return zone;
    }
    
    if (zoneNameLower.includes('dulak') && zoneNameLower.includes('harbor')) {
      if (shortNameLower === 'dulak') return zone;
    }
    
    if (zoneNameLower.includes('gulf of gunthak') || zoneNameLower.includes('the gulf of gunthak')) {
      if (shortNameLower === 'gunthak') return zone;
    }
    
    if (zoneNameLower.includes('old bloodfields')) {
      if (shortNameLower === 'oldbloodfields' || shortNameLower === 'bloodfields') return zone;
    }
    
    if (zoneNameLower.includes('loping plains')) {
      if (shortNameLower === 'lopingplains') return zone;
    }
    
    if (zoneNameLower.includes('the undershore') || zoneNameLower.includes('undershore')) {
      if (shortNameLower === 'undershore') return zone;
    }
    
    if (zoneNameLower.includes('buried sea') || zoneNameLower.includes('the buried sea')) {
      if (shortNameLower === 'buried' || shortNameLower === 'buriedsea') return zone;
    }
    
    if (zoneNameLower.includes('ruins of illsalin')) {
      if (shortNameLower === 'illsalin') return zone;
    }
    
    if (zoneNameLower.includes('nagafen') && zoneNameLower.includes('lair')) {
      if (shortNameLower === 'soldungb') return zone;
    }
    
    if (zoneNameLower.includes('solusek') && zoneNameLower.includes('eye')) {
      if (shortNameLower === 'soldunga') return zone;
    }
    
    if (zoneNameLower.includes('lesser faydark') || zoneNameLower.includes('the lesser faydark')) {
      if (shortNameLower === 'lfaydark') return zone;
    }
    
    // Basic substring matching
    if (zoneNameLower.includes(shortNameLower) || shortNameLower.includes(zoneNameLower)) {
      return zone;
    }
  }
  
  return null;
}

/**
 * Main testing function
 */
async function runNavigationTests() {
  const mapsDir = path.join(__dirname, 'Maps');
  
  if (!fs.existsSync(mapsDir)) {
    console.error(`${colors.red}Maps directory not found at: ${mapsDir}${colors.reset}`);
    process.exit(1);
  }
  
  console.log(`${colors.bold}${colors.blue}🗺️  EverQuest Zone Navigation Testing${colors.reset}\n`);
  
  // Get all _1.txt files (label files)
  const labelFiles = fs.readdirSync(mapsDir)
    .filter(file => file.endsWith('_1.txt'))
    .sort();
  
  let totalPortals = 0;
  let successfulMatches = 0;
  let failedMatches = [];
  let zoneNavigations = {};
  
  // Process each zone's label file
  for (const labelFile of labelFiles) {
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
  console.log(`${colors.bold}${colors.blue}📊 Testing Summary${colors.reset}`);
  console.log(`Total portals tested: ${totalPortals}`);
  console.log(`${colors.green}Successful matches: ${successfulMatches}${colors.reset}`);
  console.log(`${colors.red}Failed matches: ${failedMatches.length}${colors.reset}`);
  console.log(`Success rate: ${((successfulMatches / totalPortals) * 100).toFixed(1)}%\n`);
  
  // Failed matches details
  if (failedMatches.length > 0) {
    console.log(`${colors.bold}${colors.red}❌ Failed Navigation Tests:${colors.reset}`);
    for (const failure of failedMatches) {
      console.log(`  ${failure.sourceZone} → "${failure.portalLabel}" (from ${failure.sourceFile})`);
    }
    console.log();
  }
  
  // Bidirectional navigation check
  console.log(`${colors.bold}${colors.blue}🔄 Bidirectional Navigation Analysis${colors.reset}`);
  const bidirectionalIssues = [];
  
  for (const [sourceZone, destinations] of Object.entries(zoneNavigations)) {
    for (const dest of destinations) {
      // Check if destination zone has a portal back to source
      if (zoneNavigations[dest.destination]) {
        const hasReturnPortal = zoneNavigations[dest.destination].some(
          returnDest => returnDest.destination === sourceZone
        );
        
        if (!hasReturnPortal) {
          bidirectionalIssues.push({
            from: sourceZone,
            to: dest.destination,
            label: dest.label
          });
        }
      }
    }
  }
  
  if (bidirectionalIssues.length > 0) {
    console.log(`${colors.yellow}⚠️  Missing return portals:${colors.reset}`);
    for (const issue of bidirectionalIssues) {
      console.log(`  ${issue.from} → ${issue.to} (via "${issue.label}") but no return portal found`);
    }
  } else {
    console.log(`${colors.green}✓ All portal pairs appear to have bidirectional navigation${colors.reset}`);
  }
  
  console.log(`\n${colors.bold}🎯 Testing complete!${colors.reset}`);
  
  // Exit with error code if there were failures
  if (failedMatches.length > 0) {
    process.exit(1);
  }
}

// Run the tests
if (require.main === module) {
  runNavigationTests().catch(error => {
    console.error(`${colors.red}Testing failed:${colors.reset}`, error);
    process.exit(1);
  });
}

module.exports = { parseMapPortals, testZoneMatching, runNavigationTests };