<template>
  <div class="main-container" :class="classInfo?.name.toLowerCase() || 'default'" :style="containerStyles">
    <div class="hero-section">
      <button @click="goHome" class="home-button">
        ← Back to Classes
      </button>
      
      <div class="hero-content">
        <h1 class="class-title" :style="titleStyles">{{ className }} Spells</h1>
        <p class="class-subtitle">Norrath Compendium</p>
      </div>
      
      <!-- Cart Button -->
      <div class="cart-container">
        <button @click="openCart" class="cart-button" title="View Cart">
          <span class="cart-icon">🛒</span>
          <span v-if="cartStore.itemCount > 0" class="cart-counter">{{ cartStore.itemCount }}</span>
        </button>
      </div>
    </div>

    <!-- Cache Status Display -->
    <div v-if="!loading && spells.length > 0" class="cache-status-section">
      <div class="cache-info-container">
        <button 
          @click="toggleDataStatus" 
          class="data-status-toggle"
          :class="{ 'expanded': isDataStatusExpanded, 'collapsed': !isDataStatusExpanded }"
          :style="!isDataStatusExpanded ? { padding: '8px 1px', gap: '1px', width: 'auto', maxWidth: 'max-content' } : {}"
          :aria-expanded="isDataStatusExpanded"
          aria-controls="data-status-content"
          :aria-label="isDataStatusExpanded ? 'Collapse Data Status' : 'Expand Data Status'"
        >
          <template v-if="!isDataStatusExpanded">
            <span class="data-status-text">Spell Data</span>
          </template>
          <template v-else>
            <span class="data-status-icon">📊</span>
            <span class="data-status-text">Data Status</span>
            <span class="expand-icon rotated">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                <path d="M8 10.5L3.5 6L4.91 4.59L8 7.67L11.09 4.59L12.5 6L8 10.5Z"/>
              </svg>
            </span>
          </template>
        </button>
        <div 
          id="data-status-content"
          class="cache-grid-container" 
          :class="{ 'expanded': isDataStatusExpanded }"
          role="region"
          :aria-hidden="!isDataStatusExpanded"
        >
          <div class="cache-grid">
          <!-- Spell Data Status -->
          <div class="cache-card" :class="{ 'expired': isSpellDataExpired }">
            <div class="cache-card-header">
              <span class="cache-icon">🪄</span>
              <span class="cache-title">Spell Data</span>
            </div>
            <div class="cache-details">
              <div class="cache-count">{{ spells.length }} spells</div>
              <div class="cache-timestamp">{{ formatTimestamp(spellMetadata?.last_updated) }}</div>
              <div class="cache-status" :class="isSpellDataExpired ? 'expired' : 'fresh'">
                {{ isSpellDataExpired ? '⚠️ Expired' : '✅ Fresh' }}
                ({{ getTimeDescription(spellMetadata?.last_updated, 24, isSpellDataExpired) }})
              </div>
            </div>
            <div v-if="isSpellDataExpired" class="cache-actions">
              <button @click="refreshSpellData" :disabled="refreshingSpells" class="refresh-btn">
                <span v-if="refreshingSpells">🔄</span>
                <span v-else>🔄</span>
                {{ refreshingSpells ? 'Refreshing...' : 'Refresh Spells' }}
              </button>
            </div>
          </div>

          <!-- Pricing Data Status -->
          <div class="cache-card" :class="{ 'expired': isPricingDataExpired }">
            <div class="cache-card-header">
              <span class="cache-icon">💰</span>
              <span class="cache-title">Pricing Data</span>
            </div>
            <div class="cache-details">
              <div class="cache-count">
                {{ realTimePricingStats.cached }} of {{ realTimePricingStats.total }} spell pricing detected
                <span v-if="realTimePricingStats.loading > 0" class="loading-indicator">
                  ({{ realTimePricingStats.loading }} loading...)
                </span>
                <div v-if="realTimePricingStats.failed > 0 || realTimePricingStats.unfetched > 0" class="pricing-breakdown">
                  <span v-if="realTimePricingStats.unfetched > 0" class="stat-unfetched">{{ realTimePricingStats.unfetched }} unfetched</span>
                  <span v-if="realTimePricingStats.failed > 0" class="stat-failed">{{ realTimePricingStats.failed }} unavailable</span>
                </div>
              </div>
              <div class="cache-timestamp">
                <span v-if="pricingMetadata?.pricing?.most_recent_timestamp">
                  {{ formatTimestamp(pricingMetadata.pricing.most_recent_timestamp) }}
                </span>
                <span v-else-if="pricingMetadata?.pricing?.cached_count > 0">
                  Pricing cached (no timestamp available)
                </span>
                <span v-else>
                  Last updated: {{ formatTimestamp(spellMetadata?.last_updated) }}
                </span>
              </div>
              <div class="cache-status" :class="isPricingDataExpired ? 'expired' : 'fresh'">
                <span v-if="pricingMetadata?.pricing?.cached_count > 0">
                  {{ isPricingDataExpired ? '⚠️ Some expired' : '✅ Fresh' }}
                  <span v-if="pricingMetadata?.pricing?.most_recent_timestamp">
                    ({{ getTimeDescription(pricingMetadata.pricing.most_recent_timestamp, 168, isPricingDataExpired) }})
                  </span>
                  <span v-else>
                    ({{ getTimeDescription(pricingMetadata.spells.timestamp, 168, isPricingDataExpired) }})
                  </span>
                </span>
                <span v-else>
                  ✅ Fresh (Can refresh in 7 days)
                </span>
              </div>
            </div>
            <div v-if="shouldShowPricingRefresh" class="cache-actions">
              <button @click="refreshPricingData" :disabled="refreshingPricing" class="refresh-btn">
                <span v-if="refreshingPricing">🔄</span>
                <span v-else>🔄</span>
                <span v-if="refreshingPricing">
                  Refreshing...
                </span>
                <span v-else>
                  Refresh Pricing
                </span>
              </button>
            </div>
          </div>
        </div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-container" :class="{ 'transitioning': isTransitioning }">
      <div class="loading-spinner"></div>
      <p>{{ isTransitioning ? 'Switching classes...' : 'Loading spells...' }}</p>
      <div class="loading-progress"></div>
    </div>

    <div v-else-if="error" class="error-container">
      <p>{{ error }}</p>
      <button @click="retryLoad" class="retry-button">Retry</button>
    </div>

    <div v-else-if="spells.length === 0" class="no-spells">
      <p>No spells found for {{ className }}.</p>
      <button @click="scrapeClass" class="scrape-button">Scrape Data</button>
    </div>

    <div v-else class="spells-container">
      <!-- Spell Search -->
      <div class="spell-search-container">
        <div class="search-input-wrapper">
          <input
            ref="searchInput"
            v-model="searchQuery"
            @input="handleSearchInput"
            @focus="showDropdown = true"
            @keydown="handleKeyDown"
            type="text"
            placeholder="Search spells..."
            class="spell-search-input"
            autocomplete="off"
          />
          <div class="search-icon">🔍</div>
          <button 
            v-if="searchQuery" 
            @click="clearSearch" 
            class="clear-search-btn"
          >
            ×
          </button>
        </div>
        
        <!-- Search Results Dropdown -->
        <div v-if="showDropdown && filteredSpells.length > 0" class="search-dropdown">
          <div class="search-results-header">
            <span>{{ filteredSpells.length }} result{{ filteredSpells.length === 1 ? '' : 's' }}</span>
          </div>
          <div class="search-results-list">
            <div 
              v-for="(spell, index) in filteredSpells.slice(0, 10)" 
              :key="spell.name"
              :class="['search-result-item', { 'highlighted': index === selectedIndex }]"
              @click="selectSpell(spell)"
              @mouseenter="selectedIndex = index"
            >
              <div class="search-result-info">
                <img 
                  v-if="spell.icon" 
                  :src="spell.icon" 
                  :alt="`${spell.name} icon`"
                  class="search-result-icon"
                  @error="handleIconError"
                  @load="handleIconLoad"
                />
                <div class="search-result-text">
                  <div class="search-result-name" v-html="highlightMatch(spell.name)"></div>
                  <div class="search-result-details">
                    Level {{ spell.level }}
                    <span v-if="spell.mana"> • {{ spell.mana }} MP</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-if="filteredSpells.length > 10" class="search-results-footer">
            Showing first 10 of {{ filteredSpells.length }} results
          </div>
        </div>
        
        <!-- Empty State -->
        <div v-if="showDropdown && searchQuery && filteredSpells.length === 0" class="search-empty">
          No spells found matching "{{ searchQuery }}"
        </div>
      </div>

      <!-- Level Matrix Navigation -->
      <div class="level-navigator-container">
        <nav class="level-navigator" aria-label="Level navigation">
        <h2 class="level-nav-title">Quick Level Navigation</h2>
        <div class="level-matrix" role="grid" aria-label="Level selection grid">
          <button
            v-for="level in 60"
            :key="level"
            :class="['level-cell', { 
              'available': hasSpellsAtLevel(level),
              'disabled': !hasSpellsAtLevel(level),
              'current': currentLevel === level
            }]"
            :disabled="!hasSpellsAtLevel(level)"
            :aria-label="hasSpellsAtLevel(level) ? `Jump to level ${level} spells` : `No spells available at level ${level}`"
            :title="hasSpellsAtLevel(level) ? `Click to view level ${level} spells` : `No spells at level ${level}`"
            @click="scrollToLevel(level)"
          >
            {{ level }}
          </button>
        </div>
        </nav>
      </div>

      <div 
        v-for="(levelGroup, level) in groupedSpells" 
        :key="level"
        class="level-section"
        :id="`level-${level}`"
      >
        <div class="level-header">
          <h2 class="level-title">Level {{ level }}</h2>
          <div class="level-header-right">
            <span class="level-count">{{ levelGroup.length }} {{ levelGroup.length === 1 ? 'Spell' : 'Spells' }}</span>
            <button 
              class="buy-all-btn" 
              @click="buyAllSpellsAtLevel(levelGroup)" 
              :disabled="!canBuyAllSpellsAtLevel(levelGroup)"
              :title="getBuyAllButtonTitle(levelGroup)"
            >
              <span>🛒</span>
              <span>Buy All</span>
            </button>
            <button class="go-to-top-btn" @click="scrollToTop" title="Go to top of page">
              <span>Top</span>
              <span class="top-arrow">↑</span>
            </button>
          </div>
        </div>
        <div class="spells-grid">
          <div 
            v-for="spell in levelGroup" 
            :key="spell.name"
            :id="`spell-${spell.spell_id}`"
            :data-spell-name="spell.name"
            class="spell-card"
            @click="openSpellModal(spell)"
          >
            <div class="spell-header">
              <div class="spell-title-section">
                <img 
                  v-if="spell.icon" 
                  :src="spell.icon" 
                  :alt="`${spell.name} icon`"
                  class="spell-icon"
                  @error="handleIconError"
                  @load="handleIconLoad"
                />
                <div class="spell-title-text">
                  <h3 class="spell-name">{{ spell.name }}</h3>
                  <span v-if="spell.mana" class="spell-mana">{{ spell.mana }} MP</span>
                </div>
              </div>
            </div>
            <div class="spell-details">
              <div class="spell-attributes">
                <div v-if="spell.spell_id" class="spell-attribute">
                  <span class="attribute-label">Spell ID:</span>
                  <div class="spell-id-container">
                    <span class="attribute-value">{{ spell.spell_id }}</span>
                    <button 
                      class="copy-btn" 
                      @click.stop="copySpellId(spell.spell_id)" 
                      title="Copy Spell ID to clipboard"
                    >
                      📋
                    </button>
                  </div>
                </div>
                
                <div v-if="spell.skill" class="spell-attribute">
                  <span class="attribute-label">School:</span>
                  <span class="attribute-value">{{ spell.skill }}</span>
                </div>
                
                <div v-if="spell.target_type" class="spell-attribute" :class="getTargetTypeClass(spell.target_type)">
                  <span class="attribute-label">Target:</span>
                  <span class="attribute-value">{{ spell.target_type }}</span>
                </div>
                
                <div v-if="spell.mana" class="spell-attribute">
                  <span class="attribute-label">Mana Cost:</span>
                  <span class="attribute-value">{{ spell.mana }}</span>
                </div>
              </div>
            </div>
            
            <!-- Pricing and Cart Section -->
            <div class="spell-footer">
              <div v-if="spell.pricing && hasAnyPrice(spell.pricing) && !spell.pricing.unknown" class="spell-pricing">
                <div class="coin-display">
                  <div v-if="spell.pricing.platinum > 0" class="coin-item">
                    <img src="/icons/coins/platinum.svg" alt="Platinum" class="coin-icon" />
                    <span class="coin-value">{{ spell.pricing.platinum }}</span>
                  </div>
                  <div v-if="spell.pricing.gold > 0" class="coin-item">
                    <img src="/icons/coins/gold.svg" alt="Gold" class="coin-icon" />
                    <span class="coin-value">{{ spell.pricing.gold }}</span>
                  </div>
                  <div v-if="spell.pricing.silver > 0" class="coin-item">
                    <img src="/icons/coins/silver.svg" alt="Silver" class="coin-icon" />
                    <span class="coin-value">{{ spell.pricing.silver }}</span>
                  </div>
                  <div v-if="spell.pricing.bronze > 0" class="coin-item">
                    <img src="/icons/coins/bronze.svg" alt="Bronze" class="coin-icon" />
                    <span class="coin-value">{{ spell.pricing.bronze }}</span>
                  </div>
                </div>
              </div>
              <div v-else-if="spell.pricing && (spell.pricing.unknown || !hasAnyPrice(spell.pricing))" class="spell-pricing-failed">
                <span class="pricing-status failed">❌ No Price Available</span>
              </div>
              <div v-else-if="!spell.pricing && getPricingProgress(spell.spell_id) > 0 && getPricingProgress(spell.spell_id) < 100" class="pricing-progress-container">
                <div class="pricing-progress-bar">
                  <div 
                    class="pricing-progress-fill" 
                    :style="{ width: getPricingProgress(spell.spell_id) + '%' }"
                  ></div>
                  <span class="pricing-loading-text">Loading Price</span>
                </div>
                <span class="pricing-progress-text">{{ getPricingProgress(spell.spell_id) }}%</span>
              </div>
              <div v-else class="spell-pricing-not-fetched">
                <span class="pricing-status not-fetched">⏳ Fetching...</span>
              </div>
              
              <button 
                @click.stop="addToCart(spell)" 
                :class="['add-to-cart-btn', { 'in-cart': isInCart(spell.spell_id), 'disabled': !hasValidPricing(spell), 'loading': !spell.pricing || getPricingProgress(spell.spell_id) < 100 }]"
                :disabled="!hasValidPricing(spell)"
                :title="getCartButtonTitle(spell)"
              >
                <span v-if="isInCart(spell.spell_id)">✓</span>
                <span v-else-if="!spell.pricing || getPricingProgress(spell.spell_id) < 100">⏳</span>
                <span v-else-if="spell.pricing && spell.pricing.unknown">❌</span>
                <span v-else>🛒</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Scroll Animation Overlay -->
    <div v-if="isScrolling" class="scroll-overlay">
      <div class="scroll-animation-container">
        <div class="scroll-class-icon">
          <img 
            :src="`/icons/${classInfo?.name.toLowerCase()}.gif`" 
            :alt="classInfo?.name"
            @error="handleScrollIconError"
          >
        </div>
        <div class="scroll-level-text">
          {{ currentSpellName ? `Scrolling to ${currentSpellName}` : currentLevel ? `Scrolling to Level ${currentLevel}` : 'Scrolling to Top' }}
        </div>
      </div>
    </div>
    
    <!-- Spell Detail Modal -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-container" @click.stop>
        <div class="modal-header">
          <div class="modal-title-section">
            <img 
              v-if="selectedSpell?.icon" 
              :src="selectedSpell.icon" 
              :alt="`${selectedSpell.name} icon`"
              class="modal-spell-icon"
              @error="handleIconError"
              @load="handleIconLoad"
            />
            <div>
              <h2 class="modal-spell-name">{{ selectedSpell?.name }}</h2>
              <p class="modal-spell-level">Level {{ selectedSpell?.level }}</p>
            </div>
          </div>
          <button @click="closeModal" class="modal-close-btn">
            <span>×</span>
          </button>
        </div>
        
        <div class="modal-content">
          <div v-if="loadingSpellDetails" class="modal-loading">
            <div class="modal-spinner"></div>
            <p>Loading spell details...</p>
          </div>
          
          <div v-else-if="spellDetailsError" class="modal-error">
            <p>{{ spellDetailsError }}</p>
            <button @click="fetchSpellDetails(selectedSpell.spell_id)" class="retry-btn">
              Retry
            </button>
          </div>
          
          <div v-else-if="spellDetails" class="modal-spell-details">
            <!-- Basic Info Grid -->
            <div class="modal-info-grid">
              <div class="modal-info-card">
                <span class="modal-info-label">
                  <span class="modal-info-icon">🆔</span>
                  Spell ID
                </span>
                <span class="modal-info-value">{{ selectedSpell.spell_id }}</span>
              </div>
              <div class="modal-info-card" v-if="selectedSpell.mana">
                <span class="modal-info-label">
                  <span class="modal-info-icon">💙</span>
                  Mana Cost
                </span>
                <span class="modal-info-value">{{ selectedSpell.mana }}</span>
              </div>
              <div class="modal-info-card" v-if="selectedSpell.skill">
                <span class="modal-info-label">
                  <span class="modal-info-icon">📚</span>
                  School
                </span>
                <span class="modal-info-value">{{ selectedSpell.skill }}</span>
              </div>
              <div class="modal-info-card" v-if="selectedSpell.target_type">
                <span class="modal-info-label">
                  <span class="modal-info-icon">🎯</span>
                  Target
                </span>
                <span class="modal-info-value">{{ selectedSpell.target_type }}</span>
              </div>
              <div class="modal-info-card" v-if="spellDetails.cast_time">
                <span class="modal-info-label">
                  <span class="modal-info-icon">⏱️</span>
                  Cast Time
                </span>
                <span class="modal-info-value">{{ spellDetails.cast_time }}</span>
              </div>
              <div class="modal-info-card" v-if="spellDetails.duration">
                <span class="modal-info-label">
                  <span class="modal-info-icon">⏳</span>
                  Duration
                </span>
                <span class="modal-info-value">{{ spellDetails.duration }}</span>
              </div>
              <div class="modal-info-card" v-if="spellDetails.range">
                <span class="modal-info-label">
                  <span class="modal-info-icon">📏</span>
                  Range
                </span>
                <span class="modal-info-value">{{ spellDetails.range }}</span>
              </div>
              <div class="modal-info-card" v-if="spellDetails.resist">
                <span class="modal-info-label">
                  <span class="modal-info-icon">🛡️</span>
                  Resist
                </span>
                <span class="modal-info-value">{{ spellDetails.resist }}</span>
              </div>
            </div>
            
            <!-- Description -->
            <div v-if="spellDetails.description" class="modal-description">
              <h3>
                <span class="section-icon">📖</span>
                Description
              </h3>
              <p>{{ spellDetails.description }}</p>
            </div>
            
            <!-- Effects -->
            <div v-if="spellDetails.effects && spellDetails.effects.length" class="modal-effects">
              <h3>
                <span class="section-icon">✨</span>
                Effects
              </h3>
              <ul>
                <li v-for="(effect, index) in spellDetails.effects" :key="index">
                  {{ effect }}
                </li>
              </ul>
            </div>
            
            <!-- Reagents -->
            <div v-if="hasValidReagents" class="reagents-section">
              <h3 class="reagents-header">
                <span class="section-icon">🧪</span>
                Reagents
              </h3>
              <div class="reagents-container">
                <div v-for="reagent in validReagents" :key="reagent.name" class="reagent-box">
                  <a :href="reagent.url" target="_blank" class="reagent-link">
                    <img 
                      v-if="reagent.icon" 
                      :src="reagent.icon" 
                      :alt="reagent.name"
                      class="reagent-icon"
                      @error="handleReagentIconError"
                    />
                    <span class="reagent-text">{{ reagent.name }} ↗ × ({{ reagent.quantity }})</span>
                  </a>
                </div>
              </div>
            </div>
            
            <!-- Items with Spell -->
            <div v-if="hasValidItemsWithSpell" class="items-with-spell-section">
              <h3 class="items-header">
                <span class="section-icon">⚔️</span>
                Items with Spell
              </h3>
              <div class="items-container">
                <div v-for="item in validItemsWithSpell" :key="item.item_id || item.name" class="item-box">
                  <a :href="item.url" target="_blank" class="item-link">
                    <img 
                      v-if="item.icon" 
                      :src="item.icon" 
                      :alt="item.name"
                      class="item-icon"
                      @error="handleItemIconError"
                    />
                    <span class="item-text">{{ item.name }} ↗</span>
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <div class="modal-footer-buttons">
            <button 
              @click="shareSpell" 
              class="share-spell-btn"
              title="Copy shareable link to this spell"
            >
              <span class="share-icon">🔗</span>
              Share Spell
            </button>
            <a 
              :href="`https://alla.clumsysworld.com/?a=spell&id=${selectedSpell?.spell_id}`" 
              target="_blank" 
              class="view-original-btn"
            >
              View on Alla Website
              <span class="external-icon">↗</span>
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- Cart Modal -->
    <div v-if="cartStore.isOpen" class="cart-modal-overlay" @click="cartStore.closeCart()">
      <div class="cart-modal" @click.stop>
        <div class="cart-modal-header">
          <h3>Shopping Cart</h3>
          <button @click="cartStore.closeCart()" class="modal-close-btn">×</button>
        </div>
        
        <div class="cart-modal-content">
          <!-- Empty Cart State -->
          <div v-if="cartStore.itemCount === 0" class="cart-empty">
            <div class="cart-empty-icon">🛒</div>
            <h4>Your cart is empty</h4>
            <p>Browse spells and add them to your cart to see them here.</p>
            <button @click="cartStore.closeCart()" class="continue-shopping-btn">
              Continue Shopping
            </button>
          </div>
          
          <!-- Cart Items -->
          <div v-else>
            <div class="cart-items">
              <div 
                v-for="item in cartStore.items" 
                :key="item.spell_id"
                class="cart-item"
              >
                <div class="cart-item-info">
                  <img 
                    v-if="item.icon" 
                    :src="item.icon" 
                    :alt="item.name"
                    class="cart-item-icon"
                    @error="handleIconError"
                  />
                  <div class="cart-item-details">
                    <h4 class="cart-item-name">{{ item.name }}</h4>
                    <div class="cart-item-meta">
                      Level {{ item.level }}
                      <span v-if="item.class_names && item.class_names.length">
                        • {{ item.class_names.join(', ') }}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div class="cart-item-pricing">
                  <div v-if="item.pricing && hasAnyPrice(item.pricing)" class="cart-coin-display">
                    <div v-if="item.pricing.platinum > 0" class="cart-coin-item">
                      <img src="/icons/coins/platinum.svg" alt="Platinum" class="cart-coin-icon" />
                      <span class="cart-coin-value">{{ item.pricing.platinum }}</span>
                    </div>
                    <div v-if="item.pricing.gold > 0" class="cart-coin-item">
                      <img src="/icons/coins/gold.svg" alt="Gold" class="cart-coin-icon" />
                      <span class="cart-coin-value">{{ item.pricing.gold }}</span>
                    </div>
                    <div v-if="item.pricing.silver > 0" class="cart-coin-item">
                      <img src="/icons/coins/silver.svg" alt="Silver" class="cart-coin-icon" />
                      <span class="cart-coin-value">{{ item.pricing.silver }}</span>
                    </div>
                    <div v-if="item.pricing.bronze > 0" class="cart-coin-item">
                      <img src="/icons/coins/bronze.svg" alt="Bronze" class="cart-coin-icon" />
                      <span class="cart-coin-value">{{ item.pricing.bronze }}</span>
                    </div>
                  </div>
                  <div v-else class="cart-pricing-free">Free</div>
                </div>
                
                <button 
                  @click="removeFromCart(item.spell_id)" 
                  class="remove-item-btn"
                  title="Remove from cart"
                >
                  🗑️
                </button>
              </div>
            </div>
            
            <!-- Cart Total -->
            <div class="cart-total">
              <div class="cart-total-header">
                <h4>Total Cost</h4>
                <div class="cart-total-coins">
                  <div v-if="cartStore.optimizedTotal.platinum > 0" class="cart-coin-item">
                    <img src="/icons/coins/platinum.svg" alt="Platinum" class="cart-coin-icon" />
                    <span class="cart-coin-value">{{ cartStore.optimizedTotal.platinum }}</span>
                  </div>
                  <div v-if="cartStore.optimizedTotal.gold > 0" class="cart-coin-item">
                    <img src="/icons/coins/gold.svg" alt="Gold" class="cart-coin-icon" />
                    <span class="cart-coin-value">{{ cartStore.optimizedTotal.gold }}</span>
                  </div>
                  <div v-if="cartStore.optimizedTotal.silver > 0" class="cart-coin-item">
                    <img src="/icons/coins/silver.svg" alt="Silver" class="cart-coin-icon" />
                    <span class="cart-coin-value">{{ cartStore.optimizedTotal.silver }}</span>
                  </div>
                  <div v-if="cartStore.optimizedTotal.bronze > 0" class="cart-coin-item">
                    <img src="/icons/coins/bronze.svg" alt="Bronze" class="cart-coin-icon" />
                    <span class="cart-coin-value">{{ cartStore.optimizedTotal.bronze }}</span>
                  </div>
                  <div v-if="cartStore.totalInBronze === 0" class="cart-total-free">No cost</div>
                </div>
              </div>
            </div>
            
            <!-- Cart Actions -->
            <div class="cart-actions">
              <button @click="clearCart()" class="clear-cart-btn">
                Clear Cart
              </button>
              <button @click="cartStore.closeCart()" class="continue-shopping-btn">
                Continue Shopping
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Share Toast Notification -->
    <div v-if="shareToastVisible" class="share-toast">
      <span class="toast-icon">✓</span>
      Spell link copied to clipboard!
    </div>
    
    <!-- Full-screen Progress Modal -->
    <div v-if="showProgressModal" class="progress-modal-overlay">
      <div class="progress-modal">
        <div class="progress-modal-content">
          <div class="progress-header">
            <div class="progress-title">Refreshing {{ props.className }} Spells</div>
            <div class="progress-subtitle">{{ refreshProgress.message }}</div>
          </div>
          
          <div class="progress-visual">
            <div class="progress-bar-container">
              <div class="progress-bar-background">
                <div 
                  class="progress-bar-fill"
                  :style="{ width: `${refreshProgress.progress_percentage}%` }"
                  :class="refreshProgress.stage"
                ></div>
              </div>
              <div class="progress-percentage">{{ refreshProgress.progress_percentage }}%</div>
            </div>
            
            <div class="progress-stages">
              <div 
                v-for="stage in ['initializing', 'scraping', 'processing', 'updating_cache', 'loading_memory', 'complete']"
                :key="stage"
                class="progress-stage"
                :class="{ 
                  'active': refreshProgress.stage === stage,
                  'completed': getStageOrder(refreshProgress.stage) > getStageOrder(stage),
                  'error': refreshProgress.stage === 'error'
                }"
              >
                <div class="stage-indicator">
                  <div class="stage-dot"></div>
                </div>
                <div class="stage-label">{{ getStageLabel(stage) }}</div>
              </div>
            </div>
          </div>
          
          <div class="progress-info">
            <div v-if="refreshProgress.estimated_time_remaining" class="time-remaining">
              <span class="time-label">Est. time remaining:</span>
              <span class="time-value">{{ refreshProgress.estimated_time_remaining }}s</span>
            </div>
            <div v-if="refreshProgress.stage === 'error'" class="error-actions">
              <button @click="retryRefresh" class="retry-btn">
                🔄 Retry
              </button>
              <button @click="cancelRefresh" class="cancel-btn">
                ❌ Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useSpellsStore } from '../stores/spells'
import { useCartStore } from '../stores/cart'
import axios from 'axios'

// Configure API base URL - use environment variable if explicitly set, otherwise use appropriate defaults
const API_BASE_URL = (() => {
  // In production, only use VITE_BACKEND_URL if it's a valid production URL
  if (import.meta.env.PROD) {
    const envUrl = import.meta.env.VITE_BACKEND_URL
    // Only use env URL if it's a valid production URL (not localhost)
    if (envUrl && !envUrl.includes('localhost') && !envUrl.includes('127.0.0.1')) {
      return envUrl
    }
    // Default production backend URL
    return 'https://eqdatascraper-backend-production.up.railway.app'
  }
  
  // In development, use env variable or default to localhost
  return import.meta.env.VITE_BACKEND_URL || 'http://localhost:5001'
})()

// Debounce utility function
function debounce(func, delay) {
  let timeoutId
  return (...args) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func.apply(null, args), delay)
  }
}

export default {
  name: 'ClassSpells',
  props: {
    className: {
      type: String,
      required: true
    }
  },
  setup(props) {
    const router = useRouter()
    const route = useRoute()
    const spellsStore = useSpellsStore()
    const cartStore = useCartStore()
    const loading = ref(false)
    const error = ref(null)
    const isTransitioning = ref(false)
    const currentLevel = ref(null)
    const currentSpellName = ref(null)
    
    // Search state
    const searchInput = ref(null)
    const searchQuery = ref('')
    const showDropdown = ref(false)
    const selectedIndex = ref(-1)
    const filteredSpells = ref([])
    
    // Modal state
    const showModal = ref(false)
    const selectedSpell = ref(null)
    const spellDetails = ref(null)
    const loadingSpellDetails = ref(false)
    const spellDetailsError = ref(null)
    
    // Data Status collapse state
    const isDataStatusExpanded = ref(false)
    
    const toggleDataStatus = () => {
      isDataStatusExpanded.value = !isDataStatusExpanded.value
    }
    
    // Pricing progress tracking
    const pricingProgress = ref({})
    const totalSpellsForPricing = ref(0)
    const processedSpellsForPricing = ref(0)
    const pricingCache = ref({})
    
    // Spell details cache
    const spellDetailsCache = ref({})
    
    // Circuit breaker for pricing failures
    const pricingFailureCount = ref(0)
    const lastFailureTime = ref(null)
    const FAILURE_THRESHOLD = 5
    const CIRCUIT_BREAKER_TIMEOUT = 30000 // 30 seconds

    // Persistent pricing fetch manager with cleanup
    const activePricingFetches = ref(new Map()) // spellId -> { promise, cancelled, timestamp }
    const pricingFetchQueue = ref(new Set()) // spell IDs waiting to be fetched
    const isPersistentFetchRunning = ref(false)
    
    // Retry queue system
    const retryQueue = ref(new Set())
    const isFetchingPricing = ref(false)
    
    // Add cleanup interval for stale fetches  
    const FETCH_TIMEOUT = 25000 // 25 seconds (reduced for 4 concurrent limit)
    const cleanupStaleActiveFetches = () => {
      const now = Date.now()
      for (const [spellId, fetchData] of activePricingFetches.value.entries()) {
        if (now - fetchData.timestamp > FETCH_TIMEOUT) {
          console.log(`Cleaning up stale fetch for spell ${spellId}`)
          fetchData.controller.cancelled = true
          activePricingFetches.value.delete(spellId)
        }
      }
    }
    
    // Cache status state
    const refreshingSpells = ref(false)
    const refreshingPricing = ref(false)
    const pricingMetadata = ref(null)
    
    // Progress modal state
    const showProgressModal = ref(false)
    const refreshProgress = ref({
      stage: 'initializing',
      progress_percentage: 0,
      message: 'Initializing refresh process...',
      estimated_time_remaining: null
    })

    const classInfo = computed(() => {
      return spellsStore.getClassByName(props.className)
    })

    const spellMetadata = computed(() => {
      return spellsStore.getSpellsMetadata(props.className)
    })

    const isSpellDataExpired = computed(() => {
      if (!spellMetadata.value?.last_updated) return false
      const now = new Date()
      const lastUpdated = new Date(spellMetadata.value.last_updated)
      const hoursSinceUpdate = (now - lastUpdated) / (1000 * 60 * 60)
      return hoursSinceUpdate > 24
    })

    const isPricingDataExpired = computed(() => {
      if (!pricingMetadata.value?.pricing) return false
      
      // Check if we have a most recent timestamp for pricing data
      const lastPricingUpdate = pricingMetadata.value.pricing.most_recent_timestamp
      if (lastPricingUpdate) {
        const now = new Date()
        const lastUpdate = new Date(lastPricingUpdate)
        const daysSinceUpdate = (now - lastUpdate) / (1000 * 60 * 60 * 24)
        
        // Only allow refresh after 7 days
        return daysSinceUpdate >= 7
      }
      
      // If no pricing timestamp, fall back to spell data timestamp
      if (pricingMetadata.value.spells?.timestamp) {
        const now = new Date()
        const lastUpdate = new Date(pricingMetadata.value.spells.timestamp)
        const daysSinceUpdate = (now - lastUpdate) / (1000 * 60 * 60 * 24)
        
        // Only allow refresh after 7 days
        return daysSinceUpdate >= 7
      }
      
      // If no timestamp available, don't show refresh button
      return false
    })

    // Real-time pricing statistics - optimized with caching
    const pricingStatsCache = ref({ cached: 0, loading: 0, failed: 0, unfetched: 0, total: 0 })
    const lastStatsUpdate = ref(0)
    const STATS_CACHE_DURATION = 500 // Reduced to 500ms for more responsive updates
    
    const realTimePricingStats = computed(() => {
      const now = Date.now()
      const spellsLength = spells.value?.length || 0
      
      // Force refresh if total count changed or cache is older than duration
      const shouldRefresh = (now - lastStatsUpdate.value >= STATS_CACHE_DURATION) || 
                            (pricingStatsCache.value.total !== spellsLength)
      
      if (!shouldRefresh) {
        return pricingStatsCache.value
      }
      
      if (!spellsLength) {
        const emptyStats = { cached: 0, loading: 0, failed: 0, unfetched: 0, total: 0 }
        pricingStatsCache.value = emptyStats
        lastStatsUpdate.value = now
        return emptyStats
      }
      
      let cached = 0
      let loading = 0
      let failed = 0
      let unfetched = 0
      
      spells.value.forEach(spell => {
        const progress = getPricingProgress(spell.spell_id)
        
        if (spell.pricing) {
          // Spell has pricing data
          if (spell.pricing.unknown === true) {
            failed++  // Explicitly marked as unknown/failed
          } else if (hasAnyPrice(spell.pricing)) {
            cached++  // Has actual price values
          } else {
            failed++  // Has pricing object but no actual price (all zeros)
          }
        } else if (progress > 0 && progress < 100) {
          loading++  // Currently being fetched
        } else {
          unfetched++  // Not yet attempted or no progress
        }
      })
      
      // Debug log to identify the mismatch
      if (now - lastStatsUpdate.value > STATS_CACHE_DURATION) {
        console.log(`📊 Stats update: cached=${cached}, failed=${failed}, loading=${loading}, unfetched=${unfetched}, total=${spellsLength}`)
        
        // Also log some sample spell states for debugging
        const sampleSpells = spells.value.slice(0, 3)
        sampleSpells.forEach(spell => {
          console.log(`  Sample spell ${spell.spell_id}: pricing=${JSON.stringify(spell.pricing)}, progress=${getPricingProgress(spell.spell_id)}`)
        })
      }
      
      const newStats = { cached, loading, failed, unfetched, total: spellsLength }
      pricingStatsCache.value = newStats
      lastStatsUpdate.value = now
      return newStats
    })

    // Detect spells with frontend pricing that should be synced to backend
    const spellsWithUIPricing = computed(() => {
      if (!spells.value?.length) return []
      
      const pricingData = []
      
      // Check component pricing cache
      if (pricingCache.value) {
        Object.entries(pricingCache.value).forEach(([spellId, pricing]) => {
          if (pricing && spells.value.some(spell => spell.spell_id == spellId)) {
            // Only include spells that have actual pricing (any coin > 0)
            if (pricing.platinum > 0 || pricing.gold > 0 || pricing.silver > 0 || pricing.bronze > 0) {
              pricingData.push({
                spell_id: spellId,
                pricing: pricing
              })
            }
          }
        })
      }
      
      return pricingData
    })

    // Detect inconsistency: UI has pricing but cache doesn't
    const hasPricingInconsistency = computed(() => {
      // No inconsistency possible when database is single source of truth
      return false
    })

    // Auto-merge frontend pricing data into backend cache
    const mergePricingData = async () => {
      if (spellsWithUIPricing.value.length === 0) {
        console.log('No frontend pricing data found to merge')
        return
      }
      
      try {
        const API_BASE_URL = (() => {
          // In production, only use VITE_BACKEND_URL if it's a valid production URL
          if (import.meta.env.PROD) {
            const envUrl = import.meta.env.VITE_BACKEND_URL
            // Only use env URL if it's a valid production URL (not localhost)
            if (envUrl && !envUrl.includes('localhost') && !envUrl.includes('127.0.0.1')) {
              return envUrl
            }
            // Default production backend URL
            return 'https://eqdatascraper-backend-production.up.railway.app'
          }
          
          // In development, use env variable or default to localhost
          return import.meta.env.VITE_BACKEND_URL || 'http://localhost:5001'
        })()
        
        console.log(`Merging ${spellsWithUIPricing.value.length} pricing entries into cache`)
        
        // Send pricing data to backend to merge into cache
        const response = await axios.post(`${API_BASE_URL}/api/merge-pricing-cache`, {
          class_name: props.className,
          pricing_data: spellsWithUIPricing.value
        })
        
        // Force a brief delay to ensure backend cache is updated
        await new Promise(resolve => setTimeout(resolve, 500))
        
        // Reload metadata to reflect the updated cache
        await loadPricingMetadata()
        
        // Force reactivity update by creating a new object
        pricingMetadata.value = { ...pricingMetadata.value }
        
        console.log('Pricing data merged successfully')
        return response.data
      } catch (err) {
        console.error('Failed to merge pricing data:', err)
        throw err
      }
    }

    // Show refresh button if expired OR inconsistent
    const shouldShowPricingRefresh = computed(() => {
      return isPricingDataExpired.value || hasPricingInconsistency.value
    })

    const containerStyles = computed(() => {
      const info = classInfo.value
      if (!info) return {}
      
      return {
        '--class-color': info.color,
        '--class-color-rgb': info.colorRgb
      }
    })

    const titleStyles = computed(() => {
      const info = classInfo.value
      if (!info) return {}
      
      return {
        '--class-color': info.color,
        '--class-color-rgb': info.colorRgb
      }
    })

    const spells = computed(() => {
      return spellsStore.getSpellsForClass(props.className)
    })

    const groupedSpells = computed(() => {
      const grouped = {}
      spells.value.forEach(spell => {
        const level = spell.level || 'Unknown'
        if (!grouped[level]) {
          grouped[level] = []
        }
        grouped[level].push(spell)
      })
      return grouped
    })

    const hasSpellsAtLevel = (level) => {
      return groupedSpells.value[level] && groupedSpells.value[level].length > 0
    }


    const isScrolling = ref(false)

    const scrollToLevel = (level) => {
      const element = document.getElementById(`level-${level}`)
      if (element) {
        // Start blur animation
        isScrolling.value = true
        currentLevel.value = level
        
        // Scroll to element
        element.scrollIntoView({ behavior: 'smooth', block: 'start' })
        
        // Add highlight effect after scrolling completes
        setTimeout(() => {
          const levelHeader = element.querySelector('.level-header')
          if (levelHeader) {
            levelHeader.style.transform = 'scale(1.02)'
            levelHeader.style.boxShadow = '0 0 30px rgba(var(--class-color-rgb), 0.6)'
            setTimeout(() => {
              levelHeader.style.transform = ''
              levelHeader.style.boxShadow = ''
            }, 1000)
          }
          
          // End blur animation after scroll and highlight are complete
          setTimeout(() => {
            isScrolling.value = false
          }, 500)
        }, 800)
      }
    }

    const scrollToTop = () => {
      // Start blur animation
      isScrolling.value = true
      currentLevel.value = null
      
      // Scroll to top
      window.scrollTo({
        top: 0,
        behavior: 'smooth'
      })
      
      // End blur animation after scroll completes
      setTimeout(() => {
        isScrolling.value = false
        // Focus search box after scrolling to top
        if (searchInput.value) {
          searchInput.value.focus()
        }
      }, 1000)
    }

    const goHome = () => {
      router.push('/')
    }

    // Handle natural scroll events
    const handleScroll = () => {
      // No blur effect - just placeholder for future scroll-based features
    }


    const getTargetTypeClass = (targetType) => {
      if (!targetType) return ''
      const type = targetType.toLowerCase()
      if (type.includes('self')) return 'target-self'
      if (type.includes('single')) return 'target-single'
      if (type.includes('area') && type.includes('target')) return 'target-aoe-target'
      if (type.includes('area') && type.includes('caster')) return 'target-aoe-caster'
      if (type.includes('group')) return 'target-group'
      return ''
    }

    const copySpellId = (spellId) => {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(spellId).then(() => {
          showCopyFeedback(spellId)
        }).catch(() => {
          fallbackCopy(spellId)
        })
      } else {
        fallbackCopy(spellId)
      }
    }

    const fallbackCopy = (spellId) => {
      const textArea = document.createElement('textarea')
      textArea.value = spellId
      textArea.style.position = 'absolute'
      textArea.style.left = '-9999px'
      document.body.appendChild(textArea)
      textArea.select()
      
      try {
        document.execCommand('copy')
        showCopyFeedback(spellId)
      } catch (err) {
        console.error('Failed to copy text: ', err)
      } finally {
        document.body.removeChild(textArea)
      }
    }

    const showCopyFeedback = (spellId) => {
      // Simple alert for now - could be enhanced with a toast notification
      alert(`Spell ID ${spellId} copied to clipboard!`)
    }

    const loadPricingMetadata = async () => {
      try {
        const API_BASE_URL = (() => {
          // In production, only use VITE_BACKEND_URL if it's a valid production URL
          if (import.meta.env.PROD) {
            const envUrl = import.meta.env.VITE_BACKEND_URL
            // Only use env URL if it's a valid production URL (not localhost)
            if (envUrl && !envUrl.includes('localhost') && !envUrl.includes('127.0.0.1')) {
              return envUrl
            }
            // Default production backend URL
            return 'https://eqdatascraper-backend-production.up.railway.app'
          }
          
          // In development, use env variable or default to localhost
          return import.meta.env.VITE_BACKEND_URL || 'http://localhost:5001'
        })()
        
        const response = await axios.get(`${API_BASE_URL}/api/cache-expiry-status/${props.className}`)
        pricingMetadata.value = response.data
      } catch (err) {
        console.error('Failed to load pricing metadata:', err)
        pricingMetadata.value = null
      }
    }

    const performIntelligentPricingCheck = async () => {
      try {
        // Reset progress for spells that already have pricing data and identify spells needing pricing in one pass
        const spellsNeedingPricing = []
        let withPricing = 0, failed = 0, noPricing = 0
        
        spells.value.forEach(spell => {
          if (spell.pricing) {
            if (spell.pricing.unknown === true) {
              failed++
            } else {
              withPricing++
              // Clear any lingering progress for spells that already have pricing
              setPricingProgress(spell.spell_id, 100)
            }
          } else {
            noPricing++
            const progress = getPricingProgress(spell.spell_id)
            if (progress >= 100) {
              // If progress is 100% but no pricing, set as failed
              spell.pricing = { platinum: 0, gold: 0, silver: 0, bronze: 0, unknown: true }
              failed++
              noPricing--
            } else {
              spellsNeedingPricing.push(spell)
            }
          }
        })
        
        const totalSpells = spells.value.length
        
        // Only log if there are spells needing pricing or in debug mode
        if (spellsNeedingPricing.length > 0) {
          console.log(`📊 Pricing check: Total=${totalSpells}, WithPricing=${withPricing}, Failed=${failed}, NoPricing=${noPricing}, NeedingFetch=${spellsNeedingPricing.length}`)
          
          // Queue all spells that don't have pricing for fetching
          const spellIds = spellsNeedingPricing.map(spell => spell.spell_id)
          console.log(`🎯 Queueing ${spellIds.length} spells for pricing: ${spellIds.slice(0, 5).join(', ')}${spellIds.length > 5 ? '...' : ''}`)
          addToQueueAndProcess(spellIds)
        }
        
      } catch (error) {
        console.warn('Error in intelligent pricing check:', error)
      }
    }
    
    // Check circuit breaker before making requests
    const isCircuitBreakerOpen = () => {
      if (pricingFailureCount.value >= FAILURE_THRESHOLD) {
        const timeSinceLastFailure = Date.now() - lastFailureTime.value
        if (timeSinceLastFailure < CIRCUIT_BREAKER_TIMEOUT) {
          return true
        } else {
          // Reset circuit breaker after timeout
          pricingFailureCount.value = 0
          lastFailureTime.value = null
        }
      }
      return false
    }

    // Persistent pricing fetch manager that survives state changes
    const startPersistentPricingFetch = async (spellId) => {
      // Validate that this spell belongs to the current class
      const spell = spells.value.find(s => s.spell_id == spellId)
      if (!spell) {
        console.error(`🚫 INVALID SPELL ID: ${spellId} not found in current class ${props.className} - skipping fetch`)
        pricingFetchQueue.value.delete(spellId)
        activePricingFetches.value.delete(spellId)
        return null
      }

      // Check circuit breaker
      if (isCircuitBreakerOpen()) {
        console.log(`Circuit breaker open, skipping fetch for spell ${spellId}`)
        spell.pricing = { platinum: 0, gold: 0, silver: 0, bronze: 0, unknown: true }
        setPricingProgress(spellId, 100)
        return null
      }

      if (activePricingFetches.value.has(spellId)) {
        console.log(`Spell ${spellId} already being fetched`)
        return activePricingFetches.value.get(spellId).promise
      }

      console.log(`Starting persistent fetch for spell ${spellId}`)
      
      const fetchController = { cancelled: false }
      
      const fetchPromise = (async () => {
        try {
          setPricingProgress(spellId, 1)
          
          if (fetchController.cancelled) return null
          
          setPricingProgress(spellId, 25)
          const response = await fetch(`${API_BASE_URL}/api/spell-details/${spellId}`)
          
          if (fetchController.cancelled) return null
          
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`)
          }
          
          setPricingProgress(spellId, 75)
          const details = await response.json()
          
          if (fetchController.cancelled) return null
          
          // Find the spell in current spells and update it
          const spell = spells.value.find(s => s.spell_id == spellId)
          if (spell) {
            if (details.pricing) {
              spell.pricing = details.pricing
              console.log(`✅ Updated spell ${spellId} with pricing:`, details.pricing)
              // Reset failure count on success
              pricingFailureCount.value = 0
            } else {
              spell.pricing = { platinum: 0, gold: 0, silver: 0, bronze: 0, unknown: true }
              console.log(`❓ No pricing found for spell ${spellId}`)
            }
            
            // Force stats refresh by clearing cache
            lastStatsUpdate.value = 0
          }
          
          setPricingProgress(spellId, 100)
          return details
          
        } catch (error) {
          if (fetchController.cancelled) return null
          console.warn(`Failed to fetch pricing for spell ${spellId}:`, error)
          
          // Increment failure count and record time
          pricingFailureCount.value++
          lastFailureTime.value = Date.now()
          
          const spell = spells.value.find(s => s.spell_id == spellId)
          if (spell) {
            spell.pricing = { platinum: 0, gold: 0, silver: 0, bronze: 0, unknown: true }
            // Force stats refresh by clearing cache
            lastStatsUpdate.value = 0
          }
          setPricingProgress(spellId, 100)
          return null
        } finally {
          activePricingFetches.value.delete(spellId)
          pricingFetchQueue.value.delete(spellId)
        }
      })()
      
      activePricingFetches.value.set(spellId, { 
        promise: fetchPromise, 
        controller: fetchController,
        timestamp: Date.now()
      })
      return fetchPromise
    }

    const processPricingQueue = async () => {
      if (isPersistentFetchRunning.value) {
        console.log('Pricing queue processor already running')
        return
      }

      isPersistentFetchRunning.value = true
      console.log(`Processing pricing queue with ${pricingFetchQueue.value.size} items`)

      try {
        // Process up to 4 items concurrently to improve performance
        const CONCURRENT_LIMIT = 4
        const queueArray = Array.from(pricingFetchQueue.value)
        
        for (let i = 0; i < queueArray.length; i += CONCURRENT_LIMIT) {
          const batch = queueArray.slice(i, i + CONCURRENT_LIMIT)
          const batchPromises = batch
            .filter(spellId => pricingFetchQueue.value.has(spellId)) // Only process if still in queue
            .map(spellId => startPersistentPricingFetch(spellId))
          
          await Promise.allSettled(batchPromises)
          
          // Delay between batches to avoid server overload
          if (i + CONCURRENT_LIMIT < queueArray.length) {
            await new Promise(resolve => setTimeout(resolve, 2000))
          }
        }
      } finally {
        isPersistentFetchRunning.value = false
        console.log('Pricing queue processing completed')
        
        // Run cleanup after processing
        cleanupStaleActiveFetches()
      }
    }

    const addToQueueAndProcess = (spellIds) => {
      spellIds.forEach(spellId => {
        pricingFetchQueue.value.add(spellId)
        
        // Remove existing pricing to show loading state
        const spell = spells.value.find(s => s.spell_id == spellId)
        if (spell) {
          delete spell.pricing
        }
      })
      
      console.log(`Added ${spellIds.length} spells to pricing queue`)
      
      // Start processing if not already running
      if (!isPersistentFetchRunning.value) {
        processPricingQueue()
      }
    }

    // Resume interrupted fetches when spells data changes
    const resumeInterruptedFetches = () => {
      // First, clear progress for spells that have pricing but still show progress
      spells.value.forEach(spell => {
        const progress = getPricingProgress(spell.spell_id)
        if (spell.hasOwnProperty('pricing') && progress > 0 && progress < 100) {
          console.log(`Clearing stuck progress for spell ${spell.spell_id} (has pricing but shows ${progress}% progress)`)
          setPricingProgress(spell.spell_id, 100)
        }
      })
      
      // Then, resume interrupted fetches for spells without pricing
      const interruptedSpells = spells.value.filter(spell => {
        const progress = getPricingProgress(spell.spell_id)
        return progress > 0 && progress < 100 && !spell.pricing && !activePricingFetches.value.has(spell.spell_id)
      })
      
      if (interruptedSpells.length > 0) {
        console.log(`Resuming ${interruptedSpells.length} interrupted pricing fetches`)
        addToQueueAndProcess(interruptedSpells.map(s => s.spell_id))
      }
    }

    const fetchSamplePricingData = async (sampleSpells) => {
      try {
        console.log('Starting persistent pricing fetch for sample spells...')
        
        const spellIds = sampleSpells.map(spell => spell.spell_id)
        addToQueueAndProcess(spellIds)
        
        console.log(`Queued ${sampleSpells.length} sample spells for persistent pricing fetch`)
        
      } catch (error) {
        console.warn('Error starting sample pricing fetch:', error)
      }
    }

    const loadSpells = async (showLoading = true) => {
      if (showLoading) {
        loading.value = true
      }
      error.value = null
      
      // Clear any stale pricing queue data from previous classes/sessions
      pricingFetchQueue.value.clear()
      activePricingFetches.value.clear()
      
      try {
        console.log(`🔄 Loading spells for ${props.className}...`)
        const result = await spellsStore.fetchSpellsForClass(props.className)
        
        // Quick debug: Check pricing data from backend
        if (result && result.length > 0) {
          const withPricing = result.filter(s => s.pricing && !s.pricing.unknown).length
          const noPricing = result.filter(s => !s.pricing).length
          if (noPricing > 0) {
            console.log(`📦 Backend: ${result.length} spells, ${withPricing} with pricing, ${noPricing} without`)
          }
        }
        
        // Check if this was loaded from pre-hydrated memory
        const isFromMemory = spellsStore.isClassHydrated(props.className)
        
        if (isFromMemory) {
          // For pre-hydrated classes: Show spells immediately, load pricing in background
          console.log(`⚡ Instant load from memory for ${props.className}`)
          
          // Start pricing operations in background (non-blocking)
          Promise.all([
            loadPricingMetadata(),
            performIntelligentPricingCheck()
          ]).then(() => {
            resumeInterruptedFetches()
          }).catch(error => {
            console.warn('Background pricing operations failed:', error)
          })
        } else {
          // For non-hydrated classes: Wait for all operations to complete
          console.log(`🐌 Full load required for ${props.className}`)
          await Promise.all([
            loadPricingMetadata(),
            performIntelligentPricingCheck()
          ])
          
          // Resume any interrupted pricing fetches
          resumeInterruptedFetches()
        }
        
        // Check if we actually got data
        const currentSpells = spellsStore.getSpellsForClass(props.className)
        
        if (showLoading) {
          // Only add delay if we're showing a loading state and actually have data
          if (currentSpells && currentSpells.length > 0) {
            // Shorter delay for better UX, and ensure loading is hidden
            setTimeout(() => {
              loading.value = false
            }, 150)
          } else {
            // No delay if no data - hide loading immediately
            loading.value = false
          }
        }
      } catch (err) {
        error.value = err.message || 'Failed to load spells'
        loading.value = false
      }
    }

    const retryLoad = () => {
      loadSpells()
    }

    const scrapeClass = async () => {
      loading.value = true
      error.value = null
      
      try {
        await spellsStore.scrapeSpecificClass(props.className)
        // Don't show loading again immediately after scraping
        await loadSpells(false)
      } catch (err) {
        error.value = err.message || 'Failed to scrape spell data'
      } finally {
        loading.value = false
      }
    }

    // Debounced loading function to prevent rapid API calls
    const debouncedLoad = debounce(loadSpells, 100)

    // Utility functions
    const formatTimestamp = (timestamp) => {
      if (!timestamp) return 'Unknown'
      const date = new Date(timestamp)
      return date.toLocaleString()
    }

    const getTimeDescription = (timestamp, expiryHours, isExpired) => {
      if (!timestamp) return 'Unknown'
      const now = new Date()
      const cacheTime = new Date(timestamp)
      const expiredTime = new Date(cacheTime.getTime() + (expiryHours * 60 * 60 * 1000))
      
      const formatTime = (totalHours, totalMinutes) => {
        if (totalHours >= 24) {
          const days = Math.floor(totalHours / 24)
          const remainingHours = totalHours % 24
          if (remainingHours > 0) {
            return `${days}d ${remainingHours}h`
          } else {
            return `${days}d`
          }
        } else if (totalHours > 0) {
          return `${totalHours}h ${totalMinutes}m`
        } else {
          return `${totalMinutes}m`
        }
      }
      
      if (isExpired) {
        const timeSinceExpired = now - expiredTime
        const hours = Math.floor(timeSinceExpired / (1000 * 60 * 60))
        const minutes = Math.floor((timeSinceExpired % (1000 * 60 * 60)) / (1000 * 60))
        
        return `expired ${formatTime(hours, minutes)} ago`
      } else {
        const timeUntilExpiry = expiredTime - now
        const hours = Math.floor(timeUntilExpiry / (1000 * 60 * 60))
        const minutes = Math.floor((timeUntilExpiry % (1000 * 60 * 60)) / (1000 * 60))
        
        return `Can refresh in ${formatTime(hours, minutes)}`
      }
    }

    // Progress polling function
    const pollRefreshProgress = async (className) => {
      const normalizedClassName = className.toLowerCase()
      
      const poll = async () => {
        try {
          const response = await axios.get(`${API_BASE_URL}/api/refresh-progress/${normalizedClassName}`)
          refreshProgress.value = response.data
          
          // Continue polling if not complete or error
          if (refreshProgress.value.stage !== 'complete' && refreshProgress.value.stage !== 'error') {
            setTimeout(poll, 500) // Poll every 500ms
          } else {
            // Refresh complete, reload data and close modal
            if (refreshProgress.value.stage === 'complete') {
              await loadSpells(false)
              setTimeout(() => {
                showProgressModal.value = false
                refreshingSpells.value = false
              }, 1000) // Show success for 1 second
            } else {
              // Error occurred, show error state
              setTimeout(() => {
                showProgressModal.value = false
                refreshingSpells.value = false
              }, 3000) // Show error for 3 seconds
            }
          }
        } catch (err) {
          console.error('Error polling refresh progress:', err)
          // If polling fails, close modal and reset state
          showProgressModal.value = false
          refreshingSpells.value = false
        }
      }
      
      poll()
    }

    // Modal helper functions
    const getStageOrder = (stage) => {
      const stageOrder = {
        'initializing': 0,
        'scraping': 1,
        'processing': 2,
        'updating_cache': 3,
        'loading_memory': 4,
        'complete': 5,
        'error': -1
      }
      return stageOrder[stage] || 0
    }

    const getStageLabel = (stage) => {
      const stageLabels = {
        'initializing': 'Initializing',
        'scraping': 'Scraping',
        'processing': 'Processing',
        'updating_cache': 'Updating Cache',
        'loading_memory': 'Loading Memory',
        'complete': 'Complete'
      }
      return stageLabels[stage] || stage
    }

    const retryRefresh = () => {
      // Reset progress and retry
      refreshProgress.value = {
        stage: 'initializing',
        progress_percentage: 0,
        message: 'Retrying refresh...',
        estimated_time_remaining: null
      }
      refreshSpellData()
    }

    const cancelRefresh = () => {
      showProgressModal.value = false
      refreshingSpells.value = false
    }

    // Refresh functions
    const refreshSpellData = async () => {
      refreshingSpells.value = true
      showProgressModal.value = true
      
      try {
        const normalizedClassName = props.className.toLowerCase()
        
        // Call backend refresh endpoint
        await axios.post(`${API_BASE_URL}/api/refresh-spell-cache/${normalizedClassName}`)
        
        // Start polling for progress
        pollRefreshProgress(normalizedClassName)
        
      } catch (err) {
        console.error('Failed to start refresh:', err)
        refreshProgress.value = {
          stage: 'error',
          progress_percentage: 0,
          message: `❌ Failed to start refresh: ${err.message}`,
          estimated_time_remaining: null
        }
        setTimeout(() => {
          showProgressModal.value = false
          refreshingSpells.value = false
        }, 3000)
      }
    }

    const refreshPricingData = async () => {
      refreshingPricing.value = true
      try {
        console.log('Refreshing pricing data - clearing cache and re-fetching all')
        
        // Clear cache and re-fetch all pricing data
        await performRegularRefresh()
        
      } catch (err) {
        console.error('Failed to refresh pricing data:', err)
        alert('Failed to refresh pricing data. Please try again.')
      } finally {
        refreshingPricing.value = false
      }
    }

    const performRegularRefresh = async () => {
      const API_BASE_URL = (() => {
        // In production, only use VITE_BACKEND_URL if it's a valid production URL
        if (import.meta.env.PROD) {
          const envUrl = import.meta.env.VITE_BACKEND_URL
          // Only use env URL if it's a valid production URL (not localhost)
          if (envUrl && !envUrl.includes('localhost') && !envUrl.includes('127.0.0.1')) {
            return envUrl
          }
          // Default production backend URL
          return 'https://eqdatascraper-backend-production.up.railway.app'
        }
        
        // In development, use env variable or default to localhost
        return import.meta.env.VITE_BACKEND_URL || 'http://localhost:5001'
      })()
      
      console.log('Clearing backend cache and frontend pricing data...')
      
      // Clear backend cache
      await axios.post(`${API_BASE_URL}/api/refresh-pricing-cache/${props.className}`)
      
      // Clear frontend pricing data to force re-fetch
      spells.value.forEach(spell => {
        if (spell.hasOwnProperty('pricing')) {
          delete spell.pricing
        }
      })
      
      // Force a brief delay to ensure backend cache is updated
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // Reload spells data from backend (without cached pricing)
      await spellsStore.fetchSpellsForClass(props.className, true)
      spells.value = spellsStore.getSpellsForClass(props.className) || []
      
      // Reload pricing metadata
      await loadPricingMetadata()
      
      // Trigger intelligent pricing check to start fetching all pricing again
      await performIntelligentPricingCheck()
      
      console.log('Cache cleared and re-fetch started')
    }

    // Auto-resolve cache inconsistencies
    const performSmartCacheSync = async () => {
      try {
        if (hasPricingInconsistency.value && spellsWithUIPricing.value.length > 0) {
          console.log('Auto-sync: merging frontend pricing to backend cache')
          await mergePricingData()
        }
      } catch (err) {
        console.warn('Auto-sync failed (non-critical):', err)
      }
    }

    
    onMounted(async () => {
      // Wait for route to be fully resolved
      await nextTick()
      
      // Validate className prop is available
      if (!props.className) {
        console.warn('className prop not available, waiting for route resolution')
        await new Promise(resolve => {
          const unwatch = watch(() => props.className, (newValue) => {
            if (newValue) {
              unwatch()
              resolve()
            }
          }, { immediate: true })
        })
      }
      
      await loadSpells()
      window.addEventListener('scroll', handleScroll, { passive: true })
      window.addEventListener('keydown', handleKeydown)
      document.addEventListener('click', handleClickOutside, { passive: true })
      
      // Set up cleanup interval for performance maintenance
      const cleanupInterval = setInterval(() => {
        cleanupStaleActiveFetches()
        
        // Clear old progress entries for non-existent spells
        const currentSpellIds = new Set(spells.value?.map(s => s.spell_id) || [])
        Object.keys(pricingProgress.value).forEach(spellId => {
          if (!currentSpellIds.has(spellId)) {
            delete pricingProgress.value[spellId]
          }
        })
      }, 60000) // Run every minute
      
      // Store interval for cleanup
      window.cleanupInterval = cleanupInterval
      
      // Wait for DOM to be fully rendered before checking for shared spell
      await nextTick()
      setTimeout(async () => {
        await checkForSharedSpell()
        
        // Check for hash navigation (from global search)
        if (route.hash) {
          const spellId = route.hash.replace('#spell-', '')
          if (spellId) {
            // Check if we should also open the modal
            const shouldOpenModal = route.query.openModal === 'true'
            
            setTimeout(() => {
              const spellElement = document.getElementById(`spell-${spellId}`)
              if (spellElement) {
                spellElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
                spellElement.classList.add('spell-search-highlight')
                
                // If modal should be opened, find the spell and open it
                if (shouldOpenModal) {
                  const spell = spells.value.find(s => s.spell_id === spellId)
                  if (spell) {
                    setTimeout(() => {
                      openSpellModal(spell)
                    }, 1000) // Wait for scroll to complete
                  }
                }
                
                setTimeout(() => {
                  spellElement.classList.remove('spell-search-highlight')
                }, 3000)
              }
            }, 500)
          }
        }
      }, 100)
      
      // Focus search input after spells are loaded and DOM is updated
      await nextTick()
      // Add a small delay to ensure the search container is fully rendered
      setTimeout(() => {
        if (searchInput.value && spells.value.length > 0) {
          searchInput.value.focus()
        }
      }, 500)
    })
    
    onUnmounted(() => {
      window.removeEventListener('scroll', handleScroll)
      window.removeEventListener('keydown', handleKeydown)
      document.removeEventListener('click', handleClickOutside)
      
      // Clear cleanup interval
      if (window.cleanupInterval) {
        clearInterval(window.cleanupInterval)
        delete window.cleanupInterval
      }
      
      // Cancel all active pricing fetches to prevent memory leaks
      activePricingFetches.value.forEach((fetchData, spellId) => {
        console.log(`Cancelling active fetch for spell ${spellId}`)
        fetchData.controller.cancelled = true
      })
      activePricingFetches.value.clear()
      
      // Clear pricing queue and progress tracking
      pricingFetchQueue.value.clear()
      pricingProgress.value = {}
      
      // Clear caches to free memory
      pricingCache.value = {}
      spellDetailsCache.value = {}
      
      // Reset fetch state
      isPersistentFetchRunning.value = false
      isFetchingPricing.value = false
      
      // Clear stats cache
      pricingStatsCache.value = { cached: 0, loading: 0, failed: 0, unfetched: 0, total: 0 }
      
      // Clear any pending timeouts to prevent callbacks after component destruction
      if (activeFetchTimeout) {
        clearTimeout(activeFetchTimeout)
        activeFetchTimeout = null
      }
      if (pricingFetchTimeout) {
        clearTimeout(pricingFetchTimeout)
        pricingFetchTimeout = null
      }
    })

    watch(() => props.className, (newClassName, oldClassName) => {
      if (newClassName !== oldClassName && newClassName) {
        isTransitioning.value = true
        
        // Only use debounced loading if not the initial mount
        if (oldClassName) {
          // Check if new class is pre-hydrated for instant loading
          const isHydrated = spellsStore.isClassHydrated(newClassName)
          
          if (isHydrated) {
            // Instant load for hydrated classes - no debounce delay
            console.log(`⚡ Instant route change to hydrated class: ${newClassName}`)
            loadSpells()
          } else {
            // Use debounced loading for non-hydrated classes
            console.log(`🐌 Debounced route change to non-hydrated class: ${newClassName}`)
            debouncedLoad()
          }
        }
        
        // Reset transition state after a delay
        setTimeout(() => {
          isTransitioning.value = false
        }, 500)
      }
    })

    const handleIconError = (event) => {
      // Hide the icon if it fails to load
      event.target.style.display = 'none'
    }

    const handleIconLoad = (event) => {
      // Check if the loaded image is a placeholder (0.gif or very small dimensions)
      const img = event.target
      if (img.naturalWidth <= 1 || img.naturalHeight <= 1 || img.src.includes('0.gif')) {
        img.style.display = 'none'
      }
    }

    const handleScrollIconError = (event) => {
      const fallbackUrl = `https://wiki.heroesjourneyemu.com/${event.target.alt.toLowerCase()}.gif`
      event.target.src = fallbackUrl
      event.target.onerror = () => {
        event.target.style.display = 'none'
      }
    }

    // Modal functions
    const openSpellModal = async (spell) => {
      selectedSpell.value = spell
      showModal.value = true
      spellDetails.value = null
      spellDetailsError.value = null
      
      if (spell.spell_id) {
        await fetchSpellDetails(spell.spell_id)
      }
    }

    const closeModal = () => {
      showModal.value = false
      selectedSpell.value = null
      spellDetails.value = null
      spellDetailsError.value = null
    }

    const fetchSpellDetails = async (spellId) => {
      // Check cache first
      if (spellDetailsCache.value[spellId]) {
        console.log(`📦 Using cached spell details for ${spellId}`)
        spellDetails.value = spellDetailsCache.value[spellId]
        return
      }
      
      loadingSpellDetails.value = true
      spellDetailsError.value = null

      try {
        console.log(`🌐 Fetching fresh spell details for ${spellId}`)
        const response = await fetch(`${API_BASE_URL}/api/spell-details/${spellId}`, {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
          }
        })
        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
        }
        
        const details = await response.json()
        console.log('Raw API response:', details)
        console.log('Components type:', typeof details.components)
        console.log('Components content:', details.components)
        
        // Force clean the components data
        if (details.components && Array.isArray(details.components)) {
          details.components = details.components.filter(c => c && typeof c === 'object' && c.name && c.url)
        }
        
        // Cache the details
        spellDetailsCache.value[spellId] = details
        // Spell details cached in database via backend
        console.log(`✅ Cached spell details for ${spellId}`)
        
        spellDetails.value = details
        
      } catch (error) {
        console.error('Error fetching spell details:', error)
        spellDetailsError.value = error.message || 'Failed to load spell details. Please try again.'
      } finally {
        loadingSpellDetails.value = false
      }
    }

    const parseSpellDetails = (doc) => {
      const details = {}
      
      // Try to find spell information from the page
      const tables = doc.querySelectorAll('table')
      
      for (const table of tables) {
        const rows = table.querySelectorAll('tr')
        
        for (const row of rows) {
          const cells = row.querySelectorAll('td')
          if (cells.length >= 2) {
            const label = cells[0]?.textContent?.trim()
            const value = cells[1]?.textContent?.trim()
            
            if (label && value) {
              switch (label.toLowerCase()) {
                case 'cast time:':
                case 'casting time:':
                  details.cast_time = value
                  break
                case 'duration:':
                  details.duration = value
                  break
                case 'range:':
                  details.range = value
                  break
                case 'resist:':
                case 'resist type:':
                  details.resist = value
                  break
                case 'description:':
                  details.description = value
                  break
              }
            }
          }
        }
      }
      
      // Try to find effects/components in different sections
      const effectsList = []
      const componentsList = []
      
      // Look for effect information
      const effectElements = doc.querySelectorAll('td, p, div')
      for (const elem of effectElements) {
        const text = elem.textContent?.trim()
        if (text && (text.includes('Effect:') || text.includes('Increases') || text.includes('Decreases'))) {
          effectsList.push(text)
        }
      }
      
      if (effectsList.length > 0) {
        details.effects = effectsList
      }
      
      // Look for component information
      const componentElements = doc.querySelectorAll('td, span')
      for (const elem of componentElements) {
        const text = elem.textContent?.trim()
        if (text && (text.includes('Component:') || text.includes('Reagent:'))) {
          componentsList.push(text.replace(/^(Component:|Reagent:)\s*/, ''))
        }
      }
      
      if (componentsList.length > 0) {
        details.components = componentsList
      }
      
      return details
    }

    // Handle escape key to close modal
    const handleKeydown = (event) => {
      if (event.key === 'Escape' && showModal.value) {
        closeModal()
      }
    }

    // Computed properties for reagents
    const validReagents = computed(() => {
      if (!spellDetails.value?.components || !Array.isArray(spellDetails.value.components)) {
        return []
      }
      return spellDetails.value.components.filter(c => 
        c && typeof c === 'object' && c.name && c.url
      )
    })

    const hasValidReagents = computed(() => {
      return validReagents.value.length > 0
    })

    // Computed properties for items with spell
    const validItemsWithSpell = computed(() => {
      if (!spellDetails.value?.items_with_spell || !Array.isArray(spellDetails.value.items_with_spell)) {
        return []
      }
      return spellDetails.value.items_with_spell.filter(item => 
        item && typeof item === 'object' && item.name && item.url
      )
    })

    const hasValidItemsWithSpell = computed(() => {
      return validItemsWithSpell.value.length > 0
    })

    // Method to handle item icon errors
    const handleItemIconError = (event) => {
      event.target.style.display = 'none'
    }

    // Method to handle reagent icon errors
    const handleReagentIconError = (event) => {
      event.target.style.display = 'none'
    }

    // Search methods
    const handleSearchInput = () => {
      if (searchQuery.value.trim() === '') {
        filteredSpells.value = []
        showDropdown.value = false
        selectedIndex.value = -1
        return
      }
      
      const query = searchQuery.value.toLowerCase().trim()
      filteredSpells.value = spells.value.filter(spell => 
        spell.name.toLowerCase().includes(query)
      ).sort((a, b) => {
        // Prioritize exact matches at the beginning
        const aStartsWith = a.name.toLowerCase().startsWith(query)
        const bStartsWith = b.name.toLowerCase().startsWith(query)
        
        if (aStartsWith && !bStartsWith) return -1
        if (!aStartsWith && bStartsWith) return 1
        
        // Then sort by level
        return a.level - b.level
      })
      
      selectedIndex.value = filteredSpells.value.length > 0 ? 0 : -1
      showDropdown.value = true
    }

    const clearSearch = () => {
      searchQuery.value = ''
      filteredSpells.value = []
      showDropdown.value = false
      selectedIndex.value = -1
    }

    const selectSpell = (spell) => {
      // Find the spell card element and scroll to it
      const spellElement = document.querySelector(`[data-spell-name="${spell.name}"]`)
      if (spellElement) {
        // Start blur animation with spell name
        isScrolling.value = true
        currentLevel.value = null
        currentSpellName.value = spell.name
        
        // Scroll to element
        spellElement.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center' 
        })
        
        // Add highlight effect after scrolling completes
        setTimeout(() => {
          // Add golden glow border effect
          spellElement.classList.add('spell-search-highlight')
          spellElement.style.transform = 'scale(1.02)'
          
          // Open the modal after a brief delay
          setTimeout(() => {
            openSpellModal(spell)
          }, 1000) // Wait for scroll and highlight to be visible
          
          // Remove highlight after 5 seconds
          setTimeout(() => {
            spellElement.classList.remove('spell-search-highlight')
            spellElement.style.transform = ''
          }, 5000)
          
          // End blur animation after scroll is complete
          setTimeout(() => {
            isScrolling.value = false
            currentSpellName.value = null
          }, 500)
        }, 800)
      }
      
      // Clear search
      clearSearch()
    }

    const handleKeyDown = (event) => {
      if (!showDropdown.value || filteredSpells.value.length === 0) return
      
      switch (event.key) {
        case 'ArrowDown':
          event.preventDefault()
          selectedIndex.value = Math.min(selectedIndex.value + 1, Math.min(filteredSpells.value.length - 1, 9))
          break
        case 'ArrowUp':
          event.preventDefault()
          selectedIndex.value = Math.max(selectedIndex.value - 1, 0)
          break
        case 'Tab':
          event.preventDefault()
          // Tab cycles through results (forward only, Shift+Tab would be backward but we'll keep it simple)
          const maxIndex = Math.min(filteredSpells.value.length - 1, 9)
          selectedIndex.value = selectedIndex.value >= maxIndex ? 0 : selectedIndex.value + 1
          break
        case 'Enter':
          event.preventDefault()
          if (selectedIndex.value >= 0 && selectedIndex.value < filteredSpells.value.length) {
            selectSpell(filteredSpells.value[selectedIndex.value])
          }
          break
        case 'Escape':
          event.preventDefault()
          clearSearch()
          break
      }
    }

    const highlightMatch = (text) => {
      if (!searchQuery.value) return text
      
      const query = searchQuery.value.trim()
      const regex = new RegExp(`(${query})`, 'gi')
      return text.replace(regex, '<mark>$1</mark>')
    }

    // Close dropdown when clicking outside
    const handleClickOutside = (event) => {
      const searchContainer = document.querySelector('.spell-search-container')
      if (searchContainer && !searchContainer.contains(event.target)) {
        showDropdown.value = false
      }
    }

    // Share spell functionality
    const shareSpell = async () => {
      if (!selectedSpell.value) return
      
      const currentUrl = window.location.origin + window.location.pathname
      const shareUrl = `${currentUrl}?spell=${selectedSpell.value.spell_id}`
      
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(shareUrl)
          showShareFeedback()
        } else {
          fallbackCopyUrl(shareUrl)
        }
      } catch (err) {
        fallbackCopyUrl(shareUrl)
      }
    }

    const fallbackCopyUrl = (url) => {
      const textArea = document.createElement('textarea')
      textArea.value = url
      textArea.style.position = 'absolute'
      textArea.style.left = '-9999px'
      document.body.appendChild(textArea)
      textArea.select()
      
      try {
        document.execCommand('copy')
        showShareFeedback()
      } catch (err) {
        console.error('Failed to copy URL: ', err)
        alert('Could not copy link. Please copy manually: ' + url)
      } finally {
        document.body.removeChild(textArea)
      }
    }

    const shareToastVisible = ref(false)
    
    const showShareFeedback = () => {
      shareToastVisible.value = true
      setTimeout(() => {
        shareToastVisible.value = false
      }, 3000)
    }

    // Check for shared spell on page load
    const checkForSharedSpell = async () => {
      const spellId = route.query.spell
      if (spellId) {
        // Wait for spells to be loaded
        if (spells.value.length === 0) {
          // Spells not loaded yet, wait a bit and try again
          setTimeout(checkForSharedSpell, 500)
          return
        }
        
        // Find the spell by ID
        const spell = spells.value.find(s => s.spell_id === spellId)
        if (spell) {
          // Wait a bit more to ensure DOM is fully rendered
          await nextTick()
          setTimeout(() => {
            const spellElement = document.querySelector(`[data-spell-name="${spell.name}"]`)
            console.log('Looking for spell element:', spell.name, 'Found:', spellElement)
            
            if (spellElement) {
              // Start blur animation with spell name
              isScrolling.value = true
              currentLevel.value = null
              currentSpellName.value = spell.name
              
              // Scroll to element
              spellElement.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
              })
              
              // Add highlight effect after scrolling completes
              setTimeout(() => {
                console.log('Adding highlight class to:', spellElement)
                // Add golden glow border effect
                spellElement.classList.add('spell-search-highlight')
                spellElement.style.transform = 'scale(1.02)'
                // Force the highlight styles as inline styles too
                spellElement.style.border = '3px solid #ffd700'
                spellElement.style.boxShadow = '0 0 20px rgba(255, 215, 0, 0.6), 0 0 40px rgba(255, 215, 0, 0.3), 0 15px 40px rgba(var(--class-color-rgb), 0.2)'
                spellElement.style.zIndex = '10'
                spellElement.style.position = 'relative'
                console.log('Highlight class added, classes:', spellElement.classList.toString())
                
                // End blur animation after a delay
                setTimeout(() => {
                  isScrolling.value = false
                  currentSpellName.value = null
                }, 1000)
                
                // Open the modal after user has seen the highlight for a moment
                setTimeout(() => {
                  openSpellModal(spell)
                }, 2000)
                
                // Remove highlight after 5 seconds
                setTimeout(() => {
                  console.log('Removing highlight class')
                  spellElement.classList.remove('spell-search-highlight')
                  spellElement.style.transform = ''
                  spellElement.style.border = ''
                  spellElement.style.boxShadow = ''
                  spellElement.style.zIndex = ''
                  spellElement.style.position = ''
                }, 5000)
              }, 1200)
            } else {
              console.log('Spell element not found for:', spell.name)
              // If element not found, just open the modal
              openSpellModal(spell)
            }
          }, 1000)
          
          // Remove the query parameter from URL without triggering navigation
          const newUrl = window.location.pathname
          window.history.replaceState({}, document.title, newUrl)
        }
      }
    }

    // Cart functionality
    const addToCart = (spell) => {
      // Prevent adding spells with unknown pricing
      if (!hasValidPricing(spell)) {
        console.log(`Cannot add ${spell.name} to cart - unknown pricing`)
        return
      }
      
      // Check if item is already in cart
      if (isInCart(spell.spell_id)) {
        // Remove from cart if already in cart
        cartStore.removeItem(spell.spell_id)
        console.log(`Removed ${spell.name} from cart`)
      } else {
        // Add to cart if not in cart
        const success = cartStore.addItem(spell)
        if (success) {
          console.log(`Added ${spell.name} to cart`)
        } else {
          console.log(`Failed to add ${spell.name} to cart`)
        }
      }
    }

    const isInCart = (spellId) => {
      return cartStore.items.some(item => item.spell_id === spellId)
    }

    const hasAnyPrice = (pricing) => {
      if (!pricing) return false
      return pricing.platinum > 0 || pricing.gold > 0 || pricing.silver > 0 || pricing.bronze > 0
    }
    
    const hasValidPricing = (spell) => {
      // A spell has valid pricing if:
      // 1. It has pricing data and pricing is not null
      // 2. Pricing has finished loading (progress = 100%)
      // 3. Pricing is not marked as unknown (failed fetch)
      // 4. At least one currency value is greater than 0 (has actual price)
      return spell.pricing && 
             (spell.pricing !== null) && 
             getPricingProgress(spell.spell_id) === 100 && 
             !spell.pricing.unknown &&
             hasAnyPrice(spell.pricing)
    }
    
    const getCartButtonTitle = (spell) => {
      if (!spell.pricing) {
        return 'Loading price - please wait'
      }
      if (getPricingProgress(spell.spell_id) < 100) {
        return `Loading price (${getPricingProgress(spell.spell_id)}%) - please wait`
      }
      if (spell.pricing.unknown) {
        return 'Price unknown - cannot add to cart'
      }
      if (spell.pricing && !hasAnyPrice(spell.pricing)) {
        return 'No price available - cannot add to cart'
      }
      return isInCart(spell.spell_id) ? 'Remove from cart' : 'Add to cart'
    }
    
    const getRetryButtonTitle = (spellId) => {
      if (retryQueue.value.has(spellId)) {
        if (isFetchingPricing.value) {
          return 'Retry queued - click again if stuck after 10 seconds'
        }
        return 'Retry queued - will fetch shortly'
      }
      return 'Retry fetching price'
    }
    
    const forceProcessRetryQueue = () => {
      if (retryQueue.value.size > 0) {
        console.log(`🔥 Force processing retry queue with ${retryQueue.value.size} items`)
        isFetchingPricing.value = false // Reset the flag
        // Pricing included with spell data
      }
    }

    const openCart = () => {
      cartStore.openCart()
    }

    const removeFromCart = (spellId) => {
      cartStore.removeItem(spellId)
    }

    const clearCart = () => {
      if (confirm('Are you sure you want to clear your cart?')) {
        cartStore.clearCart()
      }
    }
    
    // Buy All functionality for level groups
    const canBuyAllSpellsAtLevel = (levelGroup) => {
      // Can buy all if at least one spell has valid pricing
      return levelGroup.some(spell => hasValidPricing(spell))
    }
    
    const getBuyAllButtonTitle = (levelGroup) => {
      const validSpells = levelGroup.filter(spell => hasValidPricing(spell))
      const invalidSpells = levelGroup.filter(spell => !hasValidPricing(spell))
      
      if (validSpells.length === 0) {
        return 'No spells available for purchase at this level'
      }
      
      if (invalidSpells.length === 0) {
        return `Add all ${validSpells.length} spells to cart`
      }
      
      return `Add ${validSpells.length} of ${levelGroup.length} spells to cart (${invalidSpells.length} unavailable)`
    }
    
    const buyAllSpellsAtLevel = (levelGroup) => {
      const validSpells = levelGroup.filter(spell => hasValidPricing(spell))
      
      if (validSpells.length === 0) {
        console.log('No valid spells to add at this level')
        return
      }
      
      let addedCount = 0
      let skippedCount = 0
      
      validSpells.forEach(spell => {
        if (!isInCart(spell.spell_id)) {
          const success = cartStore.addItem(spell)
          if (success) {
            addedCount++
          } else {
            skippedCount++
          }
        } else {
          skippedCount++ // Already in cart
        }
      })
      
      console.log(`Buy All: Added ${addedCount} spells, skipped ${skippedCount} spells`)
      
      // Optional: Show user feedback
      if (addedCount > 0) {
        console.log(`✅ Added ${addedCount} spells to cart!`)
      }
      if (skippedCount > 0) {
        console.log(`ℹ️ Skipped ${skippedCount} spells (already in cart or invalid pricing)`)
      }
    }
    
    const retryPricingFetch = async (spellId) => {
      // If this spell is already queued and user clicks again, force process the queue
      if (retryQueue.value.has(spellId)) {
        console.log(`🔥 Force processing retry queue for spell ${spellId} (user clicked again)`)
        forceProcessRetryQueue()
        return
      }
      
      console.log(`🔄 Queueing retry for spell ${spellId}`)
      
      // Find the spell object
      const spell = spells.value.find(s => s.spell_id === spellId)
      if (!spell) {
        console.error(`Spell with ID ${spellId} not found`)
        return
      }
      
      // Clear existing pricing and cache to force re-fetch
      spell.pricing = null
      delete pricingCache.value[spellId]
      delete pricingProgress.value[spellId]
      
      // Add to retry queue
      retryQueue.value.add(spellId)
      console.log(`📋 Added spell ${spellId} to retry queue (queue size: ${retryQueue.value.size})`)
      
      // If no pricing fetch is currently running, trigger one immediately
      if (!isFetchingPricing.value) {
        console.log('🚀 Starting pricing fetch for retry queue')
        // Pricing included with spell data
      } else {
        console.log('⏳ Pricing fetch in progress - will try to process retry in 5 seconds')
        // Set a timeout to try again if the current fetch seems stuck
        setTimeout(() => {
          if (retryQueue.value.has(spellId) && !isFetchingPricing.value) {
            console.log(`⏰ Timeout triggered - processing queued retry for spell ${spellId}`)
            // Pricing included with spell data
          } else if (retryQueue.value.has(spellId)) {
            console.log(`⚠️ Retry still queued for spell ${spellId} after timeout - forcing new fetch`)
            // Force a new fetch even if one seems to be running
            isFetchingPricing.value = false
            // Pricing included with spell data
          }
        }, 5000)
      }
    }

    // Get pricing progress for a specific spell
    const getPricingProgress = (spellId) => {
      // If we have cached pricing, don't show progress
      if (pricingCache.value[spellId]) {
        return 100
      }
      
      if (pricingProgress.value[spellId] !== undefined) {
        return pricingProgress.value[spellId]
      }
      
      // If we have no individual progress, calculate based on overall progress
      if (totalSpellsForPricing.value > 0) {
        const overallProgress = Math.floor((processedSpellsForPricing.value / totalSpellsForPricing.value) * 100)
        return Math.min(overallProgress, 95) // Cap at 95% until individual spell completes
      }
      
      return 0
    }
    
    // Set progress for a specific spell
    const setPricingProgress = (spellId, progress) => {
      pricingProgress.value[spellId] = Math.min(100, Math.max(0, progress))
    }
    
    // Database is the single source of truth - no localStorage caching needed
    
    // Spell details come from backend API - no localStorage needed
    
    // Record pricing failure
    const recordPricingFailure = () => {
      pricingFailureCount.value++
      lastFailureTime.value = Date.now()
      console.warn(`Pricing failure count: ${pricingFailureCount.value}/${FAILURE_THRESHOLD}`)
    }
    
    // Fetch pricing for spells when component loads
    const fetchPricingForSpells = async () => {
      if (!spells.value || spells.value.length === 0) return
      
      // Check circuit breaker
      if (isCircuitBreakerOpen()) {
        console.warn('Circuit breaker is open - skipping pricing fetch to prevent server overload')
        return
      }
      
      // Prevent concurrent pricing fetches
      if (isFetchingPricing.value) {
        console.log('Pricing fetch already in progress - skipping')
        return
      }
      
      isFetchingPricing.value = true
      
      // Set a timeout to reset the flag if the fetch hangs
      activeFetchTimeout = setTimeout(() => {
        console.warn('⚠️ Pricing fetch timed out after 60 seconds - resetting state')
        isFetchingPricing.value = false
        activeFetchTimeout = null
      }, 60000) // 60 second timeout
      
      // Apply cached pricing to spells that don't have it yet
      spells.value.forEach(spell => {
        if (spell.spell_id && (!spell.pricing || spell.pricing === null) && pricingCache.value[spell.spell_id]) {
          spell.pricing = pricingCache.value[spell.spell_id]
          console.log(`📦 Applied cached pricing for ${spell.name}:`, spell.pricing)
        }
      })
      
      // Get spell IDs that don't have pricing yet (including null pricing) and aren't cached
      let spellsNeedingPricing = spells.value.filter(spell => 
        spell.spell_id && (!spell.pricing || spell.pricing === null) && !pricingCache.value[spell.spell_id]
      )
      
      // Add retry queue items to the list
      const retrySpells = Array.from(retryQueue.value).map(spellId => 
        spells.value.find(spell => spell.spell_id === spellId)
      ).filter(Boolean)
      
      // Combine and deduplicate
      const allSpellIds = new Set([...spellsNeedingPricing.map(s => s.spell_id), ...retrySpells.map(s => s.spell_id)])
      spellsNeedingPricing = spells.value.filter(spell => allSpellIds.has(spell.spell_id))
      
      // Clear retry queue as we're processing it
      if (retryQueue.value.size > 0) {
        console.log(`🔄 Processing ${retryQueue.value.size} retry requests`)
        retryQueue.value.clear()
      }
      
      console.log(`Found ${spellsNeedingPricing.length} spells needing pricing out of ${spells.value.length} total spells`)
      console.log(`${Object.keys(pricingCache.value).length} spells already cached`)
      
      if (spellsNeedingPricing.length === 0) {
        console.log('All spells already have pricing data or are cached')
        return
      }
      
      // Initialize progress tracking
      totalSpellsForPricing.value = spellsNeedingPricing.length
      processedSpellsForPricing.value = 0
      
      // Initialize individual spell progress
      spellsNeedingPricing.forEach(spell => {
        setPricingProgress(spell.spell_id, 0)
      })
      
      try {
        // Use very small batch size for maximum reliability 
        const batchSize = 1
        for (let i = 0; i < spellsNeedingPricing.length; i += batchSize) {
          const batch = spellsNeedingPricing.slice(i, i + batchSize)
          const spellIds = batch.map(spell => spell.spell_id)
          
          const currentBatch = Math.floor(i/batchSize) + 1
          const totalBatches = Math.ceil(spellsNeedingPricing.length/batchSize)
          console.log(`Fetching pricing for batch ${currentBatch}/${totalBatches}:`, spellIds)
          
          // Set progress to 25% for spells being processed
          batch.forEach(spell => {
            setPricingProgress(spell.spell_id, 25)
          })
          
          try {
            const response = await axios.post(`${API_BASE_URL}/api/spell-pricing`, {
              spell_ids: spellIds
            }, {
              timeout: 15000, // Balanced timeout for better reliability
              headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
              }
            })
            
            console.log(`Batch ${currentBatch}/${totalBatches} completed:`, response.data)
            
            // Log cache stats
            console.log(`Cache now contains ${Object.keys(pricingCache.value).length} spells`)
            
            // Set progress to 75% after successful response
            batch.forEach(spell => {
              setPricingProgress(spell.spell_id, 75)
            })
            
            // Update spells with pricing data and cache immediately
            batch.forEach(spell => {
              const pricing = response.data.pricing[spell.spell_id]
              if (pricing) {
                spell.pricing = pricing
                // Cache immediately to prevent re-fetching
                pricingCache.value[spell.spell_id] = pricing
                // Pricing cached in database via backend
                console.log(`✅ Cached pricing for ${spell.name}:`, pricing)
              } else {
                // Set unknown pricing to prevent re-fetching
                const unknownPricing = { platinum: 0, gold: 0, silver: 0, bronze: 0, unknown: true }
                spell.pricing = unknownPricing
                // Cache the unknown pricing too
                pricingCache.value[spell.spell_id] = unknownPricing
                // Pricing cached in database
                console.log(`❓ No pricing data for ${spell.name} - marked as unknown`)
              }
              
              // Set progress to 100% for completed spells
              setPricingProgress(spell.spell_id, 100)
              processedSpellsForPricing.value++
            })
            
          } catch (batchError) {
            console.error(`Batch ${currentBatch}/${totalBatches} failed:`, batchError.message || batchError)
            recordPricingFailure()
            
            // Check if it's a timeout error and potentially retry smaller batches
            if (batchError.message && batchError.message.includes('timeout') && batch.length > 1) {
              console.log(`Timeout detected, trying individual requests for batch ${currentBatch}`)
              
              // Try each spell individually with a delay
              for (const spell of batch) {
                try {
                  await new Promise(resolve => setTimeout(resolve, 1000)) // Longer delay between individual retries
                  
                  const singleResponse = await axios.post(`${API_BASE_URL}/api/spell-pricing`, {
                    spell_ids: [spell.spell_id]
                  }, {
                    timeout: 12000, // Moderate timeout for individual requests
                    headers: {
                      'Accept': 'application/json',
                      'Content-Type': 'application/json'
                    }
                  })
                  
                  const pricing = singleResponse.data.pricing[spell.spell_id]
                  if (pricing) {
                    spell.pricing = pricing
                    pricingCache.value[spell.spell_id] = pricing
                    // Save immediately to localStorage
                    // Pricing cached in database
                    console.log(`✅ Individual retry succeeded for ${spell.name}:`, pricing)
                  } else {
                    const unknownPricing = { platinum: 0, gold: 0, silver: 0, bronze: 0, unknown: true }
                    spell.pricing = unknownPricing
                    pricingCache.value[spell.spell_id] = unknownPricing
                    // Pricing cached in database
                    console.log(`❓ Individual retry failed for ${spell.name} - no pricing data`)
                  }
                } catch (individualError) {
                  console.error(`❌ Individual retry failed for ${spell.name}:`, individualError.message)
                  const unknownPricing = { platinum: 0, gold: 0, silver: 0, bronze: 0, unknown: true }
                  spell.pricing = unknownPricing
                  pricingCache.value[spell.spell_id] = unknownPricing
                  // Pricing cached in database
                }
                
                setPricingProgress(spell.spell_id, 100)
                processedSpellsForPricing.value++
              }
            } else {
              // Handle non-timeout errors or single-spell batches normally
              batch.forEach(spell => {
                const unknownPricing = { platinum: 0, gold: 0, silver: 0, bronze: 0, unknown: true }
                spell.pricing = unknownPricing
                pricingCache.value[spell.spell_id] = unknownPricing
                setPricingProgress(spell.spell_id, 100)
                processedSpellsForPricing.value++
              })
            }
          }
          
          // Longer delay between batches to prevent server overload
          if (i + batchSize < spellsNeedingPricing.length) {
            await new Promise(resolve => setTimeout(resolve, 2500))
          }
        }
        
        // Reset counters after successful completion
        processedSpellsForPricing.value = totalSpellsForPricing.value
      } catch (error) {
        console.error('Critical error in pricing fetch process:', error)
        // Set unknown pricing for any remaining spells to prevent endless loading
        spellsNeedingPricing.forEach(spell => {
          if (!spell.pricing) {
            const unknownPricing = { platinum: 0, gold: 0, silver: 0, bronze: 0, unknown: true }
            spell.pricing = unknownPricing
            // Cache the unknown pricing to prevent re-fetching
            pricingCache.value[spell.spell_id] = unknownPricing
          }
          // Set progress to 100% even for failed spells to stop loading state
          setPricingProgress(spell.spell_id, 100)
        })
        
        // Reset counters
        processedSpellsForPricing.value = totalSpellsForPricing.value
      }
      
      // Clear the timeout and mark fetching as complete
      if (activeFetchTimeout) {
        clearTimeout(activeFetchTimeout)
        activeFetchTimeout = null
      }
      isFetchingPricing.value = false
    }

    // Watch for spell changes and fetch pricing with debouncing
    let pricingFetchTimeout = null
    let activeFetchTimeout = null // Track the main fetch timeout for cleanup
    
    const debouncedFetchPricing = () => {
      if (pricingFetchTimeout) {
        clearTimeout(pricingFetchTimeout)
      }
      pricingFetchTimeout = setTimeout(() => {
        // Pricing included with spell data
      }, 1000) // 1 second debounce to prevent rapid successive calls
    }
    
    // Database is single source of truth - no localStorage needed
    onMounted(() => {
      // Pricing data now comes from the backend with spells
    })
    
    // Watch for spells changes to resume interrupted fetches
    watch(() => spells.value, (newSpells, oldSpells) => {
      // Only resume if spells actually changed (not just reactivity updates)
      if (newSpells && newSpells.length > 0 && (!oldSpells || newSpells !== oldSpells)) {
        // Small delay to allow UI to update first
        nextTick(() => {
          resumeInterruptedFetches()
        })
      }
    }, { deep: false })
    
    // Pricing data now comes from backend - no separate fetching needed

    return {
      loading,
      error,
      spells,
      groupedSpells,
      classInfo,
      containerStyles,
      titleStyles,
      isTransitioning,
      currentLevel,
      currentSpellName,
      isScrolling,
      hasSpellsAtLevel,
      scrollToLevel,
      scrollToTop,
      goHome,
      getTargetTypeClass,
      copySpellId,
      retryLoad,
      scrapeClass,
      handleIconError,
      handleIconLoad,
      handleScrollIconError,
      // Data Status collapse functionality
      isDataStatusExpanded,
      toggleDataStatus,
      // Modal properties and methods
      showModal,
      selectedSpell,
      spellDetails,
      loadingSpellDetails,
      spellDetailsError,
      openSpellModal,
      closeModal,
      fetchSpellDetails,
      // Reagents
      validReagents,
      hasValidReagents,
      // Items with Spell
      validItemsWithSpell,
      hasValidItemsWithSpell,
      handleItemIconError,
      handleReagentIconError,
      // Search functionality
      searchInput,
      searchQuery,
      showDropdown,
      selectedIndex,
      filteredSpells,
      handleSearchInput,
      clearSearch,
      selectSpell,
      handleKeyDown,
      highlightMatch,
      // Share functionality
      shareSpell,
      shareToastVisible,
      // Cart functionality
      cartStore,
      addToCart,
      isInCart,
      hasAnyPrice,
      hasValidPricing,
      getCartButtonTitle,
      openCart,
      removeFromCart,
      clearCart,
      canBuyAllSpellsAtLevel,
      getBuyAllButtonTitle,
      buyAllSpellsAtLevel,
      retryPricingFetch,
      getRetryButtonTitle,
      forceProcessRetryQueue,
      // Pricing progress
      getPricingProgress,
      // Retry queue state
      retryQueue,
      isFetchingPricing,
      // Cache status functionality
      spellMetadata,
      pricingMetadata,
      isSpellDataExpired,
      isPricingDataExpired,
      realTimePricingStats,
      hasPricingInconsistency,
      shouldShowPricingRefresh,
      spellsWithUIPricing,
      refreshingSpells,
      refreshingPricing,
      formatTimestamp,
      getTimeDescription,
      refreshSpellData,
      refreshPricingData,
      mergePricingData,
      performRegularRefresh,
      performSmartCacheSync,
      // Progress modal functionality
      showProgressModal,
      refreshProgress,
      getStageOrder,
      getStageLabel,
      retryRefresh,
      cancelRefresh
    }
  }
}
</script>

<style scoped>
/* Fallback for missing class colors */
.main-container {
  --class-color: var(--primary-color, #9370db);
  --class-color-rgb: var(--primary-rgb, 147, 112, 219);
}

.hero-section {
  text-align: center;
  margin-bottom: 60px;
  position: relative;
  background: transparent;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: -50%;
  left: 50%;
  transform: translateX(-50%);
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(var(--class-color-rgb), 0.4) 0%, transparent 70%);
  border-radius: 50%;
  filter: blur(60px);
  z-index: -1;
}

/* Cache Status Section */
.cache-status-section {
  margin: 0 auto 30px auto;
  max-width: 1000px;
  padding: 0 20px;
}

.cache-info-container {
  background: rgba(var(--class-color-rgb), 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(var(--class-color-rgb), 0.2);
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s ease;
}

/* When collapsed, make container look like a button */
.cache-info-container:not(:has(.cache-grid-container.expanded)) {
  background: rgba(var(--class-color-rgb), 0.15);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(var(--class-color-rgb), 0.3);
  border-radius: 16px;
  padding: 0;
  box-shadow: 0 4px 20px rgba(var(--class-color-rgb), 0.1);
}

/* Enhanced hover effect for collapsed state */
.cache-info-container:not(:has(.cache-grid-container.expanded)):hover {
  background: rgba(var(--class-color-rgb), 0.2);
  border: 1px solid rgba(var(--class-color-rgb), 0.4);
  box-shadow: 0 6px 25px rgba(var(--class-color-rgb), 0.15);
  transform: translateY(-1px);
}

/* Data Status Toggle Button */
.cache-info-container .data-status-toggle {
  background: none !important;
  border: none !important;
  padding: 8px 2px !important;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px !important;
  color: var(--class-color);
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 auto !important;
  transition: all 0.3s ease;
  border-radius: 16px;
  width: auto !important;
  min-width: fit-content;
  max-width: max-content !important;
}

/* Collapsed state - ultra compact */
.data-status-toggle.collapsed {
  padding: 8px 1px !important;
  gap: 1px !important;
  width: auto !important;
  max-width: max-content !important;
}

/* When expanded, use full width and reduce padding to fit with container */
.data-status-toggle.expanded {
  width: 100% !important;
  padding: 12px 16px !important;
  border-radius: 8px;
  margin: 0 !important;
  max-width: none !important;
  gap: 12px !important;
}

.data-status-toggle:hover {
  background: rgba(var(--class-color-rgb), 0.2);
  transform: translateY(-2px);
}

.data-status-toggle.expanded:hover {
  background: rgba(var(--class-color-rgb), 0.1);
  transform: translateY(-1px);
}

.data-status-toggle:focus {
  outline: 2px solid var(--class-color);
  outline-offset: 2px;
}

.data-status-toggle:focus:not(:focus-visible) {
  outline: none;
}

.data-status-icon {
  font-size: 1.2rem;
}

.data-status-text {
  font-size: 1.1rem;
  font-weight: 600;
}

.expand-icon {
  display: flex;
  align-items: center;
  transition: transform 0.3s ease;
  color: var(--class-color);
  opacity: 0.7;
}

.expand-icon.rotated {
  transform: rotate(180deg);
}

.expand-icon svg {
  width: 16px;
  height: 16px;
}

/* Collapsible Container */
.cache-grid-container {
  max-height: 0;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  opacity: 0;
  margin-top: 0;
}

.cache-grid-container.expanded {
  max-height: 1000px;
  opacity: 1;
  margin-top: 20px;
}

.cache-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.cache-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(var(--class-color-rgb), 0.2);
  border-radius: 10px;
  padding: 16px;
  transition: all 0.3s ease;
}

.cache-card.expired {
  border-color: rgba(255, 165, 0, 0.4);
  background: rgba(255, 165, 0, 0.05);
}

.cache-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(var(--class-color-rgb), 0.15);
}

.cache-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.cache-icon {
  font-size: 1.2rem;
}

.cache-title {
  color: var(--class-color);
  font-weight: 600;
  font-size: 1rem;
}

.cache-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.cache-count {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.85rem;
  font-weight: 500;
}

.loading-indicator {
  color: rgba(255, 215, 0, 0.9);
  font-style: italic;
  font-weight: 400;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}

.pricing-breakdown {
  font-size: 0.75rem;
  margin-top: 4px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stat-unfetched {
  color: rgba(108, 117, 125, 0.9);
}

.stat-failed {
  color: rgba(220, 53, 69, 0.9);
}

.stat-unknown {
  color: rgba(255, 165, 0, 0.9);
}

.cache-timestamp {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.8rem;
  font-family: monospace;
}

.cache-status {
  font-size: 0.85rem;
  font-weight: 500;
}

.cache-status.fresh {
  color: #32cd32;
}

.cache-status.expired {
  color: #ffa500;
}

.cache-actions {
  display: flex;
  justify-content: center;
}

.refresh-btn {
  background: linear-gradient(135deg, rgba(var(--class-color-rgb), 0.2), rgba(var(--class-color-rgb), 0.1));
  border: 1px solid rgba(var(--class-color-rgb), 0.3);
  color: var(--class-color);
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 500;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 4px;
}

.refresh-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(var(--class-color-rgb), 0.3), rgba(var(--class-color-rgb), 0.2));
  border-color: rgba(var(--class-color-rgb), 0.5);
  transform: translateY(-1px);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-btn:disabled span {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .cache-status-section {
    padding: 0 15px;
    margin-bottom: 20px;
  }
  
  .cache-info-container {
    padding: 15px;
  }
  
  .data-status-toggle {
    padding: 14px 14px;
    gap: 6px;
  }
  
  .data-status-toggle.expanded {
    width: 100%;
    padding: 10px 12px;
    margin: 0;
  }
  
  .data-status-icon {
    font-size: 1.1rem;
  }
  
  .data-status-text {
    font-size: 1rem;
  }
  
  .cache-grid-container.expanded {
    margin-top: 15px;
  }
  
  .cache-grid {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .cache-card {
    padding: 14px;
  }
}

.home-button {
  position: absolute;
  top: 0;
  left: 0;
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  color: white;
  border: none;
  border-radius: 12px;
  padding: 12px 20px;
  font-size: 0.9em;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  box-shadow: 0 4px 12px rgba(var(--class-color-rgb), 0.3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: 'Inter', sans-serif;
  z-index: 1000;
}

.home-button::before {
  content: '';
  width: 0;
  height: 0;
  border-top: 5px solid transparent;
  border-bottom: 5px solid transparent;
  border-right: 8px solid white;
  transition: all 0.3s ease;
}

.home-button:hover {
  background: linear-gradient(135deg, rgba(var(--class-color-rgb), 0.95), var(--class-color));
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 8px 20px rgba(var(--class-color-rgb), 0.4);
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.6);
}

.class-title {
  font-family: 'Cinzel', serif;
  font-size: 4em;
  font-weight: 700;
  background: linear-gradient(135deg, var(--class-color) 0%, rgba(255,255,255,0.9) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 20px;
  text-shadow: 0 0 40px rgba(var(--class-color-rgb), 0.6);
  letter-spacing: 2px;
}

.class-subtitle {
  font-size: 1.4em;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 400;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.loading-container,
.error-container,
.no-spells {
  text-align: center;
  padding: 60px 20px;
  position: relative;
}

.loading-container {
  background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  margin: 2rem 0;
  transition: all 0.3s ease;
}

.loading-container.transitioning {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.1), rgba(var(--class-color-rgb), 0.05));
  border-color: rgba(var(--class-color-rgb), 0.2);
}

.loading-spinner {
  width: 60px;
  height: 60px;
  border: 4px solid rgba(var(--class-color-rgb), 0.2);
  border-top: 4px solid var(--class-color);
  border-radius: 50%;
  animation: spin 1.2s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
  margin: 0 auto 20px;
  position: relative;
}

.loading-spinner::before {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  right: 2px;
  bottom: 2px;
  border: 2px solid transparent;
  border-top: 2px solid rgba(var(--class-color-rgb), 0.5);
  border-radius: 50%;
  animation: spinReverse 0.8s linear infinite;
}

.loading-progress {
  width: 200px;
  height: 4px;
  background: rgba(var(--class-color-rgb), 0.2);
  border-radius: 2px;
  margin: 20px auto 0;
  overflow: hidden;
  position: relative;
}

.loading-progress::before {
  content: '';
  position: absolute;
  top: 0;
  left: -200px;
  width: 200px;
  height: 100%;
  background: linear-gradient(90deg, transparent, var(--class-color), transparent);
  animation: loadingProgress 2s ease-in-out infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@keyframes spinReverse {
  0% { transform: rotate(360deg); }
  100% { transform: rotate(0deg); }
}

@keyframes loadingProgress {
  0% { left: -200px; }
  50% { left: 200px; }
  100% { left: 200px; }
}

/* Level Navigator Styles */
.level-navigator-container {
  text-align: center;
  margin-bottom: 3rem;
}

.level-navigator {
  background: linear-gradient(145deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  padding: 1rem 0.75rem;
  margin: 0;
  position: relative;
  overflow: hidden;
  display: inline-block;
}

.level-nav-title {
  font-family: 'Cinzel', serif;
  font-size: 1.8rem;
  font-weight: 600;
  color: var(--class-color);
  text-align: center;
  margin-bottom: 1.5rem;
  text-shadow: 0 0 20px rgba(var(--class-color-rgb), 0.4);
}

.level-matrix {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  grid-template-rows: repeat(6, 1fr);
  gap: 0.75rem;
  width: fit-content;
  margin: 0 auto;
}

.level-cell {
  aspect-ratio: 1;
  background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  position: relative;
  overflow: hidden;
  color: rgba(255, 255, 255, 0.5);
  min-height: 48px;
  min-width: 48px;
  font-family: 'Inter', sans-serif;
  text-align: center;
  user-select: none;
}

.level-cell.available {
  background: linear-gradient(135deg, rgba(var(--class-color-rgb), 0.3), rgba(var(--class-color-rgb), 0.15));
  border-color: rgba(var(--class-color-rgb), 0.5);
  color: var(--text-light);
  font-weight: 700;
  box-shadow: 0 0 15px rgba(var(--class-color-rgb), 0.2);
}

.level-cell.available:hover {
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  color: white;
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 8px 25px rgba(var(--class-color-rgb), 0.6);
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.9);
}

.level-cell.disabled {
  background: linear-gradient(135deg, rgba(100, 100, 100, 0.1), rgba(80, 80, 80, 0.05));
  border-color: rgba(100, 100, 100, 0.15);
  color: rgba(180, 180, 180, 0.3);
  cursor: not-allowed;
  opacity: 0.4;
}

.level-cell.current {
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.9)) !important;
  color: white !important;
  border-color: rgba(255, 255, 255, 0.8) !important;
  box-shadow: 0 0 20px rgba(var(--class-color-rgb), 0.8) !important;
  text-shadow: 0 0 10px rgba(255, 255, 255, 1) !important;
  animation: currentLevel 2s ease-in-out infinite alternate;
}

@keyframes currentLevel {
  0% { box-shadow: 0 0 20px rgba(var(--class-color-rgb), 0.8); }
  100% { box-shadow: 0 0 30px rgba(var(--class-color-rgb), 1), 0 0 40px rgba(var(--class-color-rgb), 0.6); }
}

/* Enhanced Spell Cards */
.spell-attributes {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.spell-attribute {
  display: flex;
  flex-direction: column;
  background: rgba(var(--class-color-rgb), 0.05);
  padding: 0.75rem;
  border-radius: 8px;
  border-left: 3px solid var(--class-color);
  position: relative;
  transition: all 0.3s ease;
}

.spell-attribute:hover {
  background: rgba(var(--class-color-rgb), 0.1);
  transform: translateX(2px);
}

.attribute-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: 'Inter', sans-serif;
}

.attribute-value {
  font-size: 0.9rem;
  font-weight: 500;
  color: var(--text-dark);
  font-family: 'Crimson Text', serif;
}

.spell-id-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.copy-btn {
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.25rem;
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-left: 0.5rem;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.copy-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(var(--class-color-rgb), 0.5);
}

/* Target Type Color Coding */
.target-self { 
  background: rgba(255, 215, 0, 0.1) !important; 
  border-left-color: #ffd700 !important; 
}
.target-single { 
  background: rgba(255, 68, 68, 0.1) !important; 
  border-left-color: #ff4444 !important; 
}
.target-aoe-target { 
  background: rgba(34, 197, 94, 0.1) !important; 
  border-left-color: #22c55e !important; 
}
.target-aoe-caster { 
  background: rgba(59, 130, 246, 0.1) !important; 
  border-left-color: #3b82f6 !important; 
}
.target-group { 
  background: rgba(168, 85, 247, 0.1) !important; 
  border-left-color: #a855f7 !important; 
}

.retry-button,
.scrape-button {
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 1em;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 20px;
}

.retry-button:hover,
.scrape-button:hover {
  background: linear-gradient(135deg, rgba(var(--class-color-rgb), 0.95), var(--class-color));
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(var(--class-color-rgb), 0.4);
}

.level-section {
  margin-bottom: 60px;
}

.level-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;
  padding: 1rem 2rem;
  background: linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.04));
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px;
  transition: all 0.3s ease;
  position: relative;
}

.level-title {
  font-family: 'Cinzel', serif;
  font-size: 2.2em;
  font-weight: 600;
  color: var(--class-color);
  text-shadow: 0 0 20px rgba(var(--class-color-rgb), 0.4);
  margin: 0;
}

.level-header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.level-count {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 500;
  background: rgba(var(--class-color-rgb), 0.1);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  border: 1px solid rgba(var(--class-color-rgb), 0.2);
}

.buy-all-btn {
  background: linear-gradient(135deg, #28a745, #20c997);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 0.75rem 1.25rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
  font-family: 'Inter', sans-serif;
}

.buy-all-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #218838, #1ea080);
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 8px 20px rgba(40, 167, 69, 0.5);
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.6);
}

.buy-all-btn:disabled {
  background: linear-gradient(135deg, #6c757d, #5a6268);
  cursor: not-allowed;
  opacity: 0.6;
  box-shadow: 0 2px 6px rgba(108, 117, 125, 0.2);
}

.buy-all-btn:disabled:hover {
  background: linear-gradient(135deg, #6c757d, #5a6268);
  transform: none;
  box-shadow: 0 2px 6px rgba(108, 117, 125, 0.2);
}

.go-to-top-btn {
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  color: white;
  border: none;
  border-radius: 12px;
  padding: 0.75rem 1.25rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  box-shadow: 0 4px 12px rgba(var(--class-color-rgb), 0.3);
  font-family: 'Inter', sans-serif;
}

.go-to-top-btn:hover {
  background: linear-gradient(135deg, rgba(var(--class-color-rgb), 0.95), var(--class-color));
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 8px 20px rgba(var(--class-color-rgb), 0.5);
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.6);
}

.top-arrow {
  font-size: 1.1em;
  font-weight: bold;
  transition: transform 0.3s ease;
}

.go-to-top-btn:hover .top-arrow {
  transform: translateY(-2px);
}

.level-header::after {
  content: '';
  position: absolute;
  bottom: -10px;
  left: 50%;
  transform: translateX(-50%);
  width: 100px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--class-color), transparent);
}

.spells-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 25px;
}

.spell-card {
  background: linear-gradient(145deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(255,255,255,0.15);
  border-radius: 16px;
  padding: 25px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.spell-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--class-color), rgba(var(--class-color-rgb), 0.6));
}

.spell-card:hover {
  transform: translateY(-5px);
  border-color: rgba(var(--class-color-rgb), 0.4);
  box-shadow: 0 15px 40px rgba(var(--class-color-rgb), 0.2);
}

.spell-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.spell-title-section {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.spell-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 2px solid rgba(var(--class-color-rgb), 0.3);
  background: rgba(255, 255, 255, 0.1);
  object-fit: cover;
  transition: all 0.3s ease;
}

.spell-icon:hover {
  transform: scale(1.1);
  border-color: var(--class-color);
  box-shadow: 0 4px 12px rgba(var(--class-color-rgb), 0.4);
}

.spell-title-text {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex: 1;
}

.spell-name {
  font-family: 'Cinzel', serif;
  font-size: 1.4em;
  font-weight: 600;
  color: var(--text-dark);
  margin: 0;
}

.spell-mana {
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.9em;
  font-weight: 600;
  min-width: 60px;
  text-align: center;
}

.spell-details {
  color: var(--text-light);
  font-size: 0.95em;
  line-height: 1.6;
}

.spell-details p {
  margin: 8px 0;
}

.spell-cast-time,
.spell-duration,
.spell-range {
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}

.spell-description {
  color: var(--text-light);
  font-style: italic;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

/* Scroll Animation Overlay */
.scroll-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(12px);
  z-index: 1500;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: scrollOverlayFadeIn 0.3s ease-out;
}

@keyframes scrollOverlayFadeIn {
  from {
    opacity: 0;
    backdrop-filter: blur(0px);
  }
  to {
    opacity: 1;
    backdrop-filter: blur(12px);
  }
}

.scroll-animation-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
  text-align: center;
}

.scroll-class-icon {
  width: 150px;
  height: 150px;
  border-radius: 24px;
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  display: flex;
  align-items: center;
  justify-content: center;
  border: 4px solid rgba(255, 255, 255, 0.6);
  box-shadow: 
    0 0 40px rgba(var(--class-color-rgb), 0.8),
    0 0 80px rgba(var(--class-color-rgb), 0.4);
  animation: scrollIconFloat 2s ease-in-out infinite;
  position: relative;
  overflow: hidden;
}

.scroll-class-icon::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255,255,255,0.3), transparent);
  transform: rotate(45deg);
  animation: scrollIconShimmer 2s ease-in-out infinite;
}

.scroll-class-icon img {
  width: 85%;
  height: 85%;
  object-fit: cover;
  border-radius: 16px;
  z-index: 1;
  position: relative;
  animation: scrollIconPulse 1.5s ease-in-out infinite;
}

.scroll-level-text {
  font-family: 'Cinzel', serif;
  font-size: 2rem;
  font-weight: 700;
  color: var(--class-color);
  text-shadow: 
    0 0 20px rgba(var(--class-color-rgb), 0.8),
    0 0 40px rgba(var(--class-color-rgb), 0.4);
  animation: scrollTextGlow 2s ease-in-out infinite alternate;
  letter-spacing: 1px;
}

@keyframes scrollIconFloat {
  0%, 100% { 
    transform: translateY(0px) scale(1);
  }
  50% { 
    transform: translateY(-20px) scale(1.05);
  }
}

@keyframes scrollIconShimmer {
  0% { 
    transform: rotate(45deg) translate(-200%, -200%);
  }
  50% { 
    transform: rotate(45deg) translate(0%, 0%);
  }
  100% { 
    transform: rotate(45deg) translate(200%, 200%);
  }
}

@keyframes scrollIconPulse {
  0%, 100% { 
    transform: scale(1);
    opacity: 1;
  }
  50% { 
    transform: scale(1.1);
    opacity: 0.9;
  }
}

@keyframes scrollTextGlow {
  0% { 
    text-shadow: 
      0 0 20px rgba(var(--class-color-rgb), 0.6),
      0 0 40px rgba(var(--class-color-rgb), 0.3);
  }
  100% { 
    text-shadow: 
      0 0 30px rgba(var(--class-color-rgb), 1),
      0 0 60px rgba(var(--class-color-rgb), 0.6),
      0 0 90px rgba(var(--class-color-rgb), 0.3);
  }
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
  animation: modalFadeIn 0.3s ease-out;
}

@keyframes modalFadeIn {
  from {
    opacity: 0;
    backdrop-filter: blur(0px);
  }
  to {
    opacity: 1;
    backdrop-filter: blur(8px);
  }
}

.modal-container {
  background: linear-gradient(145deg, rgba(20, 25, 40, 0.95), rgba(15, 20, 35, 0.98));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(var(--class-color-rgb), 0.3);
  border-radius: 16px;
  width: 100%;
  max-width: 700px;
  max-height: 85vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5), 0 0 100px rgba(var(--class-color-rgb), 0.2);
  animation: modalSlideIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-50px) scale(0.9);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 2rem 1rem;
  border-bottom: 1px solid rgba(var(--class-color-rgb), 0.2);
  position: relative;
}

.modal-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 2rem;
  right: 2rem;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--class-color), transparent);
}

.modal-title-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.modal-spell-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  border: 2px solid var(--class-color);
  background: rgba(255, 255, 255, 0.1);
  object-fit: cover;
  box-shadow: 0 4px 12px rgba(var(--class-color-rgb), 0.4);
}

.modal-spell-name {
  font-family: 'Cinzel', serif;
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--class-color);
  margin: 0;
  text-shadow: 0 0 20px rgba(var(--class-color-rgb), 0.6);
}

.modal-spell-level {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.8);
  margin: 0.25rem 0 0 0;
  font-weight: 500;
}

.modal-close-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.2rem;
  font-weight: bold;
}

.modal-close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.4);
  color: white;
  transform: scale(1.1);
}

.modal-content {
  padding: 1.5rem 2rem;
}

.modal-loading {
  text-align: center;
  padding: 3rem 0;
}

.modal-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(var(--class-color-rgb), 0.2);
  border-top: 4px solid var(--class-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

.modal-error {
  text-align: center;
  padding: 2rem 0;
  color: #ff6b6b;
}

.modal-info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.modal-info-card {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.1), rgba(var(--class-color-rgb), 0.05));
  border: 1px solid rgba(var(--class-color-rgb), 0.3);
  border-radius: 8px;
  padding: 1rem;
  position: relative;
  transition: all 0.3s ease;
}

.modal-info-card:hover {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.15), rgba(var(--class-color-rgb), 0.08));
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(var(--class-color-rgb), 0.2);
}

.modal-info-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 0.4rem;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  font-family: 'Inter', sans-serif;
}

.modal-info-icon {
  font-size: 0.9rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

.section-icon {
  font-size: 1rem;
  margin-right: 0.4rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.modal-info-value {
  font-size: 1rem;
  font-weight: 600;
  color: var(--class-color);
  font-family: 'Crimson Text', serif;
  text-shadow: 0 0 10px rgba(var(--class-color-rgb), 0.3);
}

.modal-description,
.modal-effects,
.modal-reagents-section {
  margin-bottom: 1.5rem;
}

.modal-description h3,
.modal-effects h3,
.reagents-title {
  font-family: 'Cinzel', serif;
  font-size: 1.3rem;
  color: var(--class-color);
  margin-bottom: 0.75rem;
  text-shadow: 0 0 15px rgba(var(--class-color-rgb), 0.4);
  display: flex;
  align-items: center;
}

.modal-description p {
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.5;
  font-size: 0.95rem;
}

.modal-effects ul {
  list-style: none;
  padding: 0;
}

.modal-effects li {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
  border-left: 3px solid var(--class-color);
  padding: 0.75rem;
  margin-bottom: 0.4rem;
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.9);
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.modal-effects li:hover {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.1), rgba(var(--class-color-rgb), 0.05));
  transform: translateX(5px);
}

.components-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.component-item {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
  border: 1px solid rgba(var(--class-color-rgb), 0.2);
  border-radius: 8px;
  padding: 1rem;
  color: rgba(255, 255, 255, 0.9);
  text-align: center;
  transition: all 0.3s ease;
}

.component-item:hover {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.1), rgba(var(--class-color-rgb), 0.05));
  border-color: rgba(var(--class-color-rgb), 0.4);
  transform: translateY(-2px);
}

.reagents-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.reagent-item {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
  border: 1px solid rgba(var(--class-color-rgb), 0.2);
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.reagent-item:hover {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.1), rgba(var(--class-color-rgb), 0.05));
  border-color: rgba(var(--class-color-rgb), 0.4);
  transform: translateY(-2px);
}

.reagent-name-link {
  color: #ffffff;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
  position: relative;
  text-shadow: 0 0 4px rgba(0, 0, 0, 0.8);
}

.reagent-name-link:hover {
  color: var(--class-color);
  text-shadow: 0 0 8px rgba(var(--class-color-rgb), 0.6);
  transform: translateY(-1px);
}

.reagent-name-link::after {
  content: '↗';
  margin-left: 0.3rem;
  font-size: 0.8rem;
  opacity: 0.7;
  transition: opacity 0.3s ease;
}

.reagent-name-link:hover::after {
  opacity: 1;
}

.reagent-count {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.9rem;
  font-weight: 500;
}

.reagents-section {
  margin-bottom: 2rem;
}

.reagents-header {
  font-family: 'Cinzel', serif;
  font-size: 1.5rem;
  color: var(--class-color);
  margin-bottom: 1rem;
  text-shadow: 0 0 15px rgba(var(--class-color-rgb), 0.4);
  display: flex;
  align-items: center;
}

.reagents-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.reagent-box {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
  border: 1px solid rgba(var(--class-color-rgb), 0.2);
  border-radius: 8px;
  padding: 0.6rem 0.8rem;
  transition: all 0.3s ease;
  overflow: hidden;
  flex: 0 0 auto;
  min-width: 0;
}

.reagent-box:hover {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.1), rgba(var(--class-color-rgb), 0.05));
  border-color: rgba(var(--class-color-rgb), 0.4);
  transform: translateY(-2px);
}

.reagent-link {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: #ffffff;
  text-decoration: none;
  font-weight: 600;
  text-shadow: 0 0 4px rgba(0, 0, 0, 0.8);
  transition: all 0.3s ease;
  width: 100%;
  font-size: 0.9rem;
}

.reagent-link:hover {
  color: var(--class-color);
  text-shadow: 0 0 8px rgba(var(--class-color-rgb), 0.6);
}

.reagent-icon {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.05);
  object-fit: cover;
  transition: all 0.3s ease;
}

.reagent-icon:hover {
  border-color: rgba(var(--class-color-rgb), 0.5);
  transform: scale(1.05);
}

.reagent-text {
  line-height: 1.3;
  white-space: nowrap;
}

/* Items with Spell Section */
.items-with-spell-section {
  margin-top: 1.2rem;
  padding: 1.2rem;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.01));
  border: 1px solid rgba(var(--class-color-rgb), 0.15);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.items-header {
  font-family: 'Cinzel', serif;
  font-size: 1.3rem;
  color: var(--class-color);
  margin-bottom: 0.75rem;
  text-shadow: 0 0 15px rgba(var(--class-color-rgb), 0.4);
  display: flex;
  align-items: center;
}

.items-container {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.item-box {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
  border: 1px solid rgba(var(--class-color-rgb), 0.2);
  border-radius: 8px;
  padding: 0.6rem 0.8rem;
  transition: all 0.3s ease;
  overflow: hidden;
  flex: 0 0 auto;
  min-width: 0;
}

.item-box:hover {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.1), rgba(var(--class-color-rgb), 0.05));
  border-color: rgba(var(--class-color-rgb), 0.4);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(var(--class-color-rgb), 0.2);
}

.item-link {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: #ffffff;
  text-decoration: none;
  font-weight: 600;
  text-shadow: 0 0 4px rgba(0, 0, 0, 0.8);
  transition: all 0.3s ease;
  width: 100%;
  font-size: 0.9rem;
}

.item-link:hover {
  color: var(--class-color);
  text-shadow: 0 0 8px rgba(var(--class-color-rgb), 0.6);
}

.item-icon {
  width: 24px;
  height: 24px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.05);
  object-fit: cover;
  transition: all 0.3s ease;
}

.item-icon:hover {
  border-color: rgba(var(--class-color-rgb), 0.5);
  transform: scale(1.05);
}

.item-text {
  line-height: 1.3;
  white-space: nowrap;
}

.modal-footer {
  padding: 1.2rem 2rem 1.5rem;
  border-top: 1px solid rgba(var(--class-color-rgb), 0.2);
  text-align: center;
  position: relative;
}

.modal-footer-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
  align-items: center;
  flex-wrap: wrap;
}

.modal-footer::before {
  content: '';
  position: absolute;
  top: 0;
  left: 2rem;
  right: 2rem;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--class-color), transparent);
}

.share-spell-btn {
  background: linear-gradient(135deg, #4a90e2, rgba(74, 144, 226, 0.8));
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  text-transform: uppercase;
  letter-spacing: 0.3px;
  box-shadow: 0 4px 15px rgba(74, 144, 226, 0.4);
}

.share-spell-btn:hover {
  background: linear-gradient(135deg, rgba(74, 144, 226, 0.95), #4a90e2);
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 6px 20px rgba(74, 144, 226, 0.6);
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.6);
}

.share-icon {
  font-size: 1rem;
  transition: transform 0.3s ease;
}

.share-spell-btn:hover .share-icon {
  transform: rotate(15deg);
}

.view-original-btn {
  background: linear-gradient(135deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  text-transform: uppercase;
  letter-spacing: 0.3px;
  box-shadow: 0 4px 15px rgba(var(--class-color-rgb), 0.4);
}

.view-original-btn:hover {
  background: linear-gradient(135deg, rgba(var(--class-color-rgb), 0.95), var(--class-color));
  transform: translateY(-3px) scale(1.05);
  box-shadow: 0 8px 25px rgba(var(--class-color-rgb), 0.6);
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
}

.external-icon {
  font-size: 1.2em;
  transition: transform 0.3s ease;
}

.view-original-btn:hover .external-icon {
  transform: translate(2px, -2px);
}

.retry-btn {
  background: linear-gradient(135deg, #ff6b6b, #ee5a24);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 1rem;
}

.retry-btn:hover {
  background: linear-gradient(135deg, #ee5a24, #ff6b6b);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255, 107, 107, 0.4);
}

/* Add cursor pointer to spell cards */
.spell-card {
  cursor: pointer;
}

/* Search Component Styles */
.spell-search-container {
  position: relative;
  margin-bottom: 2rem;
  z-index: 100;
}

.search-input-wrapper {
  position: relative;
  max-width: 500px;
  margin: 0 auto;
}

.spell-search-input {
  width: 100%;
  padding: 1rem 3rem 1rem 3.5rem;
  border: 2px solid rgba(var(--class-color-rgb), 0.3);
  border-radius: 25px;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
  backdrop-filter: blur(15px);
  color: white;
  font-size: 1.1rem;
  font-weight: 500;
  outline: none;
  transition: all 0.3s ease;
  font-family: 'Inter', sans-serif;
}

.spell-search-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.spell-search-input:focus {
  border-color: var(--class-color);
  box-shadow: 0 0 20px rgba(var(--class-color-rgb), 0.4);
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.08));
}

.search-icon {
  position: absolute;
  left: 1.25rem;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.7);
  pointer-events: none;
}

.clear-search-btn {
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(var(--class-color-rgb), 0.2);
  color: white;
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1.2rem;
  font-weight: bold;
  transition: all 0.3s ease;
}

.clear-search-btn:hover {
  background: rgba(var(--class-color-rgb), 0.4);
  transform: translateY(-50%) scale(1.1);
}

.search-dropdown {
  position: absolute;
  top: calc(100% + 0.5rem);
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 500px;
  background: linear-gradient(145deg, rgba(20, 25, 40, 0.95), rgba(15, 20, 35, 0.98));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(var(--class-color-rgb), 0.3);
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3), 0 0 50px rgba(var(--class-color-rgb), 0.2);
  overflow: hidden;
  animation: searchDropdownFadeIn 0.2s ease-out;
  z-index: 1000;
}

@keyframes searchDropdownFadeIn {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.search-results-header {
  padding: 0.75rem 1rem;
  background: rgba(var(--class-color-rgb), 0.1);
  border-bottom: 1px solid rgba(var(--class-color-rgb), 0.2);
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.search-results-list {
  max-height: 400px;
  overflow-y: auto;
}

.search-result-item {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: all 0.2s ease;
}

.search-result-item:hover,
.search-result-item.highlighted {
  background: linear-gradient(145deg, rgba(var(--class-color-rgb), 0.15), rgba(var(--class-color-rgb), 0.08));
  transform: translateX(4px);
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.search-result-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  border: 2px solid rgba(var(--class-color-rgb), 0.3);
  background: rgba(255, 255, 255, 0.1);
  object-fit: cover;
  flex-shrink: 0;
}

.search-result-text {
  flex: 1;
  min-width: 0;
}

.search-result-name {
  font-family: 'Cinzel', serif;
  font-size: 1rem;
  font-weight: 600;
  color: white;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.search-result-name mark {
  background: var(--class-color);
  color: white;
  padding: 0.1em 0.2em;
  border-radius: 3px;
  font-weight: 700;
}

.search-result-details {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 500;
}

.search-results-footer {
  padding: 0.75rem 1rem;
  background: rgba(var(--class-color-rgb), 0.05);
  border-top: 1px solid rgba(var(--class-color-rgb), 0.2);
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
  font-style: italic;
}

.search-empty {
  position: absolute;
  top: calc(100% + 0.5rem);
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 500px;
  background: linear-gradient(145deg, rgba(20, 25, 40, 0.95), rgba(15, 20, 35, 0.98));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(255, 68, 68, 0.3);
  border-radius: 16px;
  padding: 1.5rem;
  text-align: center;
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.95rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  animation: searchDropdownFadeIn 0.2s ease-out;
  z-index: 1000;
}

/* Share Toast Notification */
.share-toast {
  position: fixed;
  top: 2rem;
  right: 2rem;
  background: linear-gradient(135deg, #10b981, rgba(16, 185, 129, 0.9));
  color: white;
  padding: 1rem 1.5rem;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3), 0 0 20px rgba(16, 185, 129, 0.4);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  font-weight: 600;
  font-size: 0.95rem;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  animation: toastSlideIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  max-width: 300px;
}

.toast-icon {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: bold;
  flex-shrink: 0;
}

@keyframes toastSlideIn {
  from {
    opacity: 0;
    transform: translateX(100px) scale(0.8);
  }
  to {
    opacity: 1;
    transform: translateX(0) scale(1);
  }
}

/* Spell card highlight animation */
.spell-card {
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

/* Golden highlight effect for search results */
.spells-grid .spell-card.spell-search-highlight {
  border: 3px solid #ffd700 !important;
  box-shadow: 
    0 0 20px rgba(255, 215, 0, 0.6) !important,
    0 0 40px rgba(255, 215, 0, 0.3) !important,
    0 15px 40px rgba(var(--class-color-rgb), 0.2) !important;
  animation: goldenPulse 2s ease-in-out infinite alternate !important;
  z-index: 10 !important;
  position: relative !important;
}

@keyframes goldenPulse {
  0% {
    box-shadow: 
      0 0 20px rgba(255, 215, 0, 0.6),
      0 0 40px rgba(255, 215, 0, 0.3),
      0 15px 40px rgba(var(--class-color-rgb), 0.2);
  }
  100% {
    box-shadow: 
      0 0 30px rgba(255, 215, 0, 0.8),
      0 0 60px rgba(255, 215, 0, 0.5),
      0 15px 40px rgba(var(--class-color-rgb), 0.3);
  }
}

/* Darker text for lighter colored class themes */
.main-container.cleric .home-button,
.main-container.cleric .go-to-top-btn,
.main-container.cleric .retry-button,
.main-container.cleric .scrape-button,
.main-container.cleric .view-original-btn {
  color: #2c3e50 !important;
}

/* Lighter text for darker colored class themes - modal info values */
.main-container.necromancer .modal-info-value,
.main-container.shadowknight .modal-info-value,
.main-container.monk .modal-info-value,
.main-container.rogue .modal-info-value {
  color: #ffffff !important;
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.3);
}

.main-container.paladin .home-button,
.main-container.paladin .go-to-top-btn,
.main-container.paladin .retry-button,
.main-container.paladin .scrape-button,
.main-container.paladin .view-original-btn {
  color: #2c3e50 !important;
}

.main-container.bard .home-button,
.main-container.bard .go-to-top-btn,
.main-container.bard .retry-button,
.main-container.bard .scrape-button,
.main-container.bard .view-original-btn {
  color: #2c3e50 !important;
}

.main-container.wizard .home-button,
.main-container.wizard .go-to-top-btn,
.main-container.wizard .retry-button,
.main-container.wizard .scrape-button,
.main-container.wizard .view-original-btn {
  color: #2c3e50 !important;
}

.main-container.magician .home-button,
.main-container.magician .go-to-top-btn,
.main-container.magician .retry-button,
.main-container.magician .scrape-button,
.main-container.magician .view-original-btn {
  color: #2c3e50 !important;
}

.main-container.shaman .home-button,
.main-container.shaman .go-to-top-btn,
.main-container.shaman .retry-button,
.main-container.shaman .scrape-button,
.main-container.shaman .view-original-btn {
  color: #2c3e50 !important;
}

@media (max-width: 768px) {
  .class-title { font-size: 3em; }
  .spells-grid { grid-template-columns: 1fr; }
  .spell-card { padding: 20px; }
  .home-button { position: relative; margin-bottom: 30px; }
  
  .modal-container {
    margin: 1rem;
    max-height: 95vh;
  }
  
  .modal-header {
    padding: 1.2rem;
  }
  
  .modal-content {
    padding: 1.2rem;
  }
  
  .modal-footer {
    padding: 1rem 1.2rem;
  }
  
  .modal-spell-name {
    font-size: 1.5rem;
  }
  
  .modal-info-grid {
    grid-template-columns: 1fr;
  }
  
  .components-grid {
    grid-template-columns: 1fr;
  }
  
  /* Mobile search adjustments */
  .spell-search-input {
    font-size: 1rem;
    padding: 0.875rem 2.5rem 0.875rem 3rem;
  }
  
  .search-dropdown {
    width: calc(100vw - 2rem);
    max-width: none;
  }
  
  /* Mobile modal footer adjustments */
  .modal-footer-buttons {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .share-spell-btn,
  .view-original-btn {
    width: 100%;
    justify-content: center;
  }
  
  /* Mobile toast adjustments */
  .share-toast {
    top: 1rem;
    right: 1rem;
    left: 1rem;
    max-width: none;
    font-size: 0.9rem;
  }
  
  /* Mobile level navigation adjustments */
  .level-navigator {
    padding: 1rem;
    margin-bottom: 2rem;
  }
  
  .level-matrix {
    gap: 0.375rem;
  }
  
  .level-cell {
    min-height: 36px;
    font-size: 0.8rem;
  }
}

/* Spell Footer and Pricing Styles */
.spell-footer {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.spell-pricing {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.coin-display {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.coin-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: rgba(0, 0, 0, 0.3);
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.coin-icon {
  width: 20px;
  height: 20px;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
}

.coin-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.spell-pricing-loading {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.8rem;
  font-style: italic;
}

.pricing-progress-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 100px;
}

.pricing-progress-bar {
  flex: 1;
  height: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pricing-progress-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  background: linear-gradient(90deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  border-radius: 4px;
  transition: width 0.3s ease;
  box-shadow: 0 0 8px rgba(var(--class-color-rgb), 0.4);
  z-index: 1;
}

.pricing-loading-text {
  position: relative;
  z-index: 2;
  font-size: 0.75rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.7);
  pointer-events: none;
}

.pricing-progress-text {
  font-size: 0.7rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  min-width: 30px;
  text-align: right;
}

.spell-pricing-unknown {
  color: rgba(255, 165, 0, 0.8);
  font-size: 0.8rem;
  font-style: italic;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.spell-pricing-failed {
  color: rgba(220, 53, 69, 0.9);
  font-size: 0.8rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.spell-pricing-not-fetched {
  color: rgba(108, 117, 125, 0.8);
  font-size: 0.8rem;
  font-style: italic;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.pricing-status.failed {
  color: rgba(220, 53, 69, 1);
}

.pricing-status.unknown {
  color: rgba(255, 165, 0, 1);
}

.pricing-status.not-fetched {
  color: rgba(108, 117, 125, 1);
}

.retry-pricing-btn {
  background: rgba(255, 165, 0, 0.2);
  border: 2px solid rgba(255, 165, 0, 0.8);
  border-radius: 8px;
  color: rgba(255, 165, 0, 1);
  cursor: pointer;
  padding: 0.25rem;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.retry-pricing-btn:hover:not(.disabled) {
  background: rgba(255, 165, 0, 0.25);
  border-color: rgba(255, 165, 0, 0.8);
  transform: scale(1.05);
  box-shadow: 0 4px 8px rgba(255, 165, 0, 0.3);
}

/* Queued retry button state */
.retry-pricing-btn.queued {
  background: rgba(52, 152, 219, 0.2);
  border-color: rgba(52, 152, 219, 0.8);
  color: rgba(52, 152, 219, 1);
  cursor: wait;
}

.retry-pricing-btn.queued:hover {
  background: rgba(52, 152, 219, 0.25);
  border-color: rgba(52, 152, 219, 0.8);
  transform: none;
  box-shadow: 0 4px 8px rgba(52, 152, 219, 0.3);
}

/* Disabled retry button state */
.retry-pricing-btn.disabled {
  background: rgba(108, 117, 125, 0.1);
  border-color: rgba(108, 117, 125, 0.3);
  color: rgba(108, 117, 125, 0.5);
  cursor: not-allowed;
  opacity: 0.6;
}

.retry-pricing-btn.disabled:hover {
  background: rgba(108, 117, 125, 0.1);
  border-color: rgba(108, 117, 125, 0.3);
  transform: none;
  box-shadow: none;
}

/* Queued pricing status text */
.pricing-status.queued {
  color: rgba(52, 152, 219, 0.9);
  font-weight: 600;
}

/* SVG icon styles */
.retry-icon {
  width: 14px;
  height: 14px;
  transition: transform 0.3s ease;
}

/* Refresh icon animation on hover */
.retry-pricing-btn:hover:not(.disabled):not(.queued) .refresh-icon {
  transform: rotate(180deg);
}

/* Hourglass animation for queued retry button */
.retry-pricing-btn.queued .hourglass-icon {
  animation: hourglass 2s ease-in-out infinite;
}

@keyframes hourglass {
  0%, 100% { 
    transform: scale(1) rotate(0deg); 
    opacity: 1;
  }
  50% { 
    transform: scale(1.1) rotate(180deg); 
    opacity: 0.8;
  }
}

.add-to-cart-btn {
  background: linear-gradient(135deg, #28a745, #20c997);
  color: white;
  border: none;
  border-radius: 50%;
  padding: 0;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  box-shadow: 0 2px 8px rgba(40, 167, 69, 0.3);
  align-self: flex-end;
  flex-shrink: 0;
}

.add-to-cart-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #218838, #1ea080);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.4);
}

.add-to-cart-btn:active:not(:disabled) {
  transform: translateY(0);
}

/* Add to cart button in cart state - different color to show it's in cart */
.add-to-cart-btn.in-cart {
  background: linear-gradient(135deg, #6c757d, #5a6268);
  box-shadow: 0 2px 8px rgba(108, 117, 125, 0.3);
}

.add-to-cart-btn.in-cart:hover {
  background: linear-gradient(135deg, #5a6268, #495057);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(108, 117, 125, 0.4);
}

/* Disabled add to cart button for unknown pricing */
.add-to-cart-btn.disabled {
  background: linear-gradient(135deg, #6c757d, #5a6268);
  cursor: not-allowed;
  opacity: 0.6;
  box-shadow: 0 1px 3px rgba(108, 117, 125, 0.2);
}

.add-to-cart-btn.disabled:hover {
  background: linear-gradient(135deg, #6c757d, #5a6268);
  transform: none;
  box-shadow: 0 1px 3px rgba(108, 117, 125, 0.2);
}

/* Loading state for add to cart button */
.add-to-cart-btn.loading {
  background: linear-gradient(135deg, #ffc107, #e0a800);
  cursor: wait;
  opacity: 0.8;
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.3);
}

.add-to-cart-btn.loading:hover {
  background: linear-gradient(135deg, #e0a800, #d39e00);
  transform: none;
  box-shadow: 0 2px 8px rgba(255, 193, 7, 0.4);
}

/* Animation for loading hourglass */
.add-to-cart-btn.loading span {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Mobile adjustments for spell footer */
@media (max-width: 768px) {
  .spell-footer {
    gap: 0.5rem;
  }
  
  .coin-display {
    gap: 0.375rem;
  }
  
  .coin-item {
    padding: 0.2rem 0.4rem;
  }
  
  .coin-icon {
    width: 18px;
    height: 18px;
  }
  
  .coin-value {
    font-size: 0.8rem;
  }
  
  .add-to-cart-btn {
    font-size: 0.9rem;
    width: 28px;
    height: 28px;
  }
}

/* Cart Header Button Styles */
.hero-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 60px;
  position: relative;
}

.hero-content {
  text-align: center;
  flex: 1;
}

.cart-container {
  position: relative;
}

.cart-button {
  background: linear-gradient(135deg, rgba(147, 112, 219, 0.8), rgba(147, 112, 219, 0.6));
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  width: 60px;
  height: 60px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  backdrop-filter: blur(10px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
}

.cart-button:hover {
  background: linear-gradient(135deg, rgba(147, 112, 219, 1), rgba(147, 112, 219, 0.8));
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(147, 112, 219, 0.4);
  border-color: rgba(255, 255, 255, 0.4);
}

.cart-icon {
  font-size: 1.5rem;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.cart-counter {
  position: absolute;
  top: -8px;
  right: -8px;
  background: linear-gradient(145deg, #ff4757, #ff3742);
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
  border: 2px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

/* Cart Modal Styles */
.cart-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.cart-modal {
  background: linear-gradient(145deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(255,255,255,0.15);
  border-radius: 24px;
  max-width: 600px;
  width: 100%;
  max-height: 80vh;
  overflow: hidden;
  box-shadow: 0 25px 60px rgba(0, 0, 0, 0.3);
}

.cart-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.cart-modal-header h3 {
  font-family: 'Cinzel', serif;
  font-size: 1.8rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.cart-modal-content {
  padding: 1.5rem;
  max-height: 60vh;
  overflow-y: auto;
}

.cart-empty {
  text-align: center;
  padding: 2rem;
}

.cart-empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.6;
}

.cart-empty h4 {
  font-size: 1.5rem;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 1rem 0;
}

.cart-empty p {
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 2rem 0;
}

.cart-items {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 2rem;
}

.cart-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.cart-item-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.cart-item-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  object-fit: cover;
}

.cart-item-details h4 {
  margin: 0 0 0.25rem 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.1rem;
}

.cart-item-meta {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
}

.cart-item-pricing {
  display: flex;
  align-items: center;
  margin-right: 1rem;
}

.cart-coin-display {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.cart-coin-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  background: rgba(0, 0, 0, 0.3);
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.cart-coin-icon {
  width: 22px;
  height: 22px;
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
}

.cart-coin-value {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.cart-pricing-unknown {
  color: rgba(255, 165, 0, 0.8);
  font-style: italic;
}

.remove-item-btn {
  background: linear-gradient(135deg, #dc3545, #c82333);
  border: none;
  border-radius: 8px;
  width: 40px;
  height: 40px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  box-shadow: 0 2px 8px rgba(220, 53, 69, 0.3);
}

.remove-item-btn:hover {
  background: linear-gradient(135deg, #c82333, #a71e2a);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(220, 53, 69, 0.4);
}

.cart-total {
  padding: 1.5rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 1.5rem;
}

.cart-total-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cart-total-header h4 {
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.3rem;
}

.cart-total-coins {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.cart-total-none {
  color: rgba(255, 255, 255, 0.6);
  font-style: italic;
  font-size: 1.1rem;
}

.cart-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
}

.clear-cart-btn {
  background: linear-gradient(135deg, #6c757d, #5a6268);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(108, 117, 125, 0.3);
}

.clear-cart-btn:hover {
  background: linear-gradient(135deg, #5a6268, #495057);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(108, 117, 125, 0.4);
}

.continue-shopping-btn {
  background: linear-gradient(135deg, #007bff, #0056b3);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
}

.continue-shopping-btn:hover {
  background: linear-gradient(135deg, #0056b3, #004085);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.4);
}

/* Mobile cart adjustments */
@media (max-width: 768px) {
  .hero-section {
    flex-direction: column;
    gap: 1rem;
  }
  
  .cart-button {
    width: 50px;
    height: 50px;
  }
  
  .cart-icon {
    font-size: 1.25rem;
  }
  
  .cart-counter {
    width: 20px;
    height: 20px;
    font-size: 0.7rem;
  }
  
  .cart-modal {
    margin: 0.5rem;
    max-height: 90vh;
  }
  
  .cart-modal-header {
    padding: 1rem;
  }
  
  .cart-modal-content {
    padding: 1rem;
  }
  
  .cart-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .cart-item-info {
    width: 100%;
  }
  
  .cart-item-pricing {
    margin-right: 0;
    align-self: flex-end;
  }
  
  .cart-total-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .cart-actions {
    flex-direction: column;
  }
  
  .cart-coin-display {
    gap: 0.375rem;
  }
  
  .cart-total-coins {
    gap: 0.5rem;
  }
}

/* Progress Modal Styles */
.progress-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  animation: fadeIn 0.3s ease-out;
}

.progress-modal {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 2rem;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  animation: slideIn 0.3s ease-out;
}

.progress-modal-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.progress-header {
  text-align: center;
}

.progress-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--class-color);
  margin-bottom: 0.5rem;
}

.progress-subtitle {
  font-size: 1.1rem;
  color: #666;
  font-weight: 500;
}

.progress-visual {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.progress-bar-container {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.progress-bar-background {
  width: 100%;
  height: 12px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--class-color), rgba(var(--class-color-rgb), 0.8));
  border-radius: 6px;
  transition: width 0.5s ease-out;
  position: relative;
}

.progress-bar-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: shimmer 2s infinite;
}

.progress-bar-fill.error {
  background: linear-gradient(90deg, #ff4444, #cc3333);
}

.progress-bar-fill.complete {
  background: linear-gradient(90deg, #4caf50, #45a049);
}

.progress-percentage {
  text-align: center;
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--class-color);
}

.progress-stages {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  margin: 1rem 0;
}

.progress-stages::before {
  content: '';
  position: absolute;
  top: 20px;
  left: 20px;
  right: 20px;
  height: 2px;
  background: rgba(0, 0, 0, 0.1);
  z-index: 1;
}

.progress-stage {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  position: relative;
  z-index: 2;
  flex: 1;
}

.stage-indicator {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.stage-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.progress-stage.completed .stage-indicator {
  background: var(--class-color);
  border-color: var(--class-color);
}

.progress-stage.completed .stage-dot {
  background: white;
}

.progress-stage.active .stage-indicator {
  background: var(--class-color);
  border-color: var(--class-color);
  animation: pulse 1.5s infinite;
}

.progress-stage.active .stage-dot {
  background: white;
}

.progress-stage.error .stage-indicator {
  background: #ff4444;
  border-color: #ff4444;
}

.progress-stage.error .stage-dot {
  background: white;
}

.stage-label {
  font-size: 0.8rem;
  color: #666;
  text-align: center;
  font-weight: 500;
  line-height: 1.2;
}

.progress-stage.active .stage-label {
  color: var(--class-color);
  font-weight: 600;
}

.progress-stage.completed .stage-label {
  color: var(--class-color);
  font-weight: 600;
}

.progress-info {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: center;
}

.time-remaining {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #666;
}

.time-label {
  font-weight: 500;
}

.time-value {
  font-weight: 600;
  color: var(--class-color);
}

.error-actions {
  display: flex;
  gap: 1rem;
}

.retry-btn, .cancel-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.9rem;
}

.retry-btn {
  background: var(--class-color);
  color: white;
}

.retry-btn:hover {
  background: rgba(var(--class-color-rgb), 0.9);
  transform: translateY(-2px);
}

.cancel-btn {
  background: #f5f5f5;
  color: #666;
}

.cancel-btn:hover {
  background: #e0e0e0;
  transform: translateY(-2px);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { 
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to { 
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

/* Responsive modal */
@media (max-width: 768px) {
  .progress-modal {
    margin: 1rem;
    padding: 1.5rem;
  }
  
  .progress-title {
    font-size: 1.3rem;
  }
  
  .progress-subtitle {
    font-size: 1rem;
  }
  
  .progress-stages {
    flex-wrap: wrap;
    gap: 1rem;
  }
  
  .stage-indicator {
    width: 30px;
    height: 30px;
  }
  
  .stage-dot {
    width: 8px;
    height: 8px;
  }
  
  .stage-label {
    font-size: 0.7rem;
  }
}
</style> 