import { defineStore } from 'pinia'

export const useCartStore = defineStore('cart', {
  state: () => ({
    items: [], // Array of spell objects with pricing information
    isOpen: false // Whether cart modal is open
  }),

  getters: {
    itemCount: (state) => state.items.length,
    
    totalPlatinum: (state) => {
      return state.items.reduce((total, item) => {
        return total + (item.pricing?.platinum || 0)
      }, 0)
    },
    
    totalGold: (state) => {
      return state.items.reduce((total, item) => {
        return total + (item.pricing?.gold || 0)
      }, 0)
    },
    
    totalSilver: (state) => {
      return state.items.reduce((total, item) => {
        return total + (item.pricing?.silver || 0)
      }, 0)
    },
    
    totalBronze: (state) => {
      return state.items.reduce((total, item) => {
        return total + (item.pricing?.bronze || 0)
      }, 0)
    },
    
    // Convert all currency to total bronze for easier calculations
    totalInBronze: (state) => {
      return state.items.reduce((total, item) => {
        const pricing = item.pricing || {}
        return total + 
          (pricing.platinum || 0) * 1000 + 
          (pricing.gold || 0) * 100 + 
          (pricing.silver || 0) * 10 + 
          (pricing.bronze || 0)
      }, 0)
    },
    
    // Get optimized currency breakdown (convert bronze to higher denominations)
    optimizedTotal: (state) => {
      const totalBronze = state.totalInBronze
      const platinum = Math.floor(totalBronze / 1000)
      const gold = Math.floor((totalBronze % 1000) / 100)
      const silver = Math.floor((totalBronze % 100) / 10)
      const bronze = totalBronze % 10
      
      return { platinum, gold, silver, bronze }
    }
  },

  actions: {
    addItem(spell) {
      // Check if item already exists in cart
      const existingItem = this.items.find(item => item.spell_id === spell.spell_id)
      
      if (existingItem) {
        // Item already in cart - could show a message or increment quantity
        console.log(`${spell.name} is already in cart`)
        return false
      }
      
      this.items.push({
        spell_id: spell.spell_id,
        name: spell.name,
        level: spell.level,
        class_names: spell.class_names || [],
        icon: spell.icon,
        pricing: spell.pricing || { platinum: 0, gold: 0, silver: 0, bronze: 0 }
      })
      
      this.saveToLocalStorage()
      return true
    },
    
    removeItem(spellId) {
      const index = this.items.findIndex(item => item.spell_id === spellId)
      if (index > -1) {
        this.items.splice(index, 1)
        this.saveToLocalStorage()
        return true
      }
      return false
    },
    
    clearCart() {
      this.items = []
      this.saveToLocalStorage()
    },
    
    openCart() {
      this.isOpen = true
    },
    
    closeCart() {
      this.isOpen = false
    },
    
    saveToLocalStorage() {
      try {
        localStorage.setItem('eq-spell-cart', JSON.stringify(this.items))
      } catch (error) {
        console.error('Failed to save cart to localStorage:', error)
      }
    },
    
    loadFromLocalStorage() {
      try {
        const saved = localStorage.getItem('eq-spell-cart')
        if (saved) {
          this.items = JSON.parse(saved)
        }
      } catch (error) {
        console.error('Failed to load cart from localStorage:', error)
        this.items = []
      }
    }
  }
})