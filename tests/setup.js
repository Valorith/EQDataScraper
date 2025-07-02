/**
 * Test setup file for Vitest
 * Configures global test environment and mocks
 */

// Mock fetch globally for API tests
global.fetch = vi.fn()

// Mock window.matchMedia for responsive tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock console.log in tests to reduce noise
global.console = {
  ...console,
  log: vi.fn(),
  debug: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
}

// Common test utilities
export const mockAxiosResponse = (data, status = 200) => ({
  data,
  status,
  statusText: 'OK',
  headers: {},
  config: {}
})

export const mockSpellData = [
  {
    name: 'Courage',
    level: 1,
    mana: '10',
    skill: 'ABJURATION',
    target_type: 'Single target',
    spell_id: '202',
    effects: 'Increase AC by 10.5 to 15',
    icon: 'https://alla.clumsysworld.com/images/icons/spell_202.png',
    pricing: {
      platinum: 0,
      gold: 0,
      silver: 4,
      bronze: 0,
      unknown: false
    }
  },
  {
    name: 'Flash of Light',
    level: 1,
    mana: '10', 
    skill: 'EVOCATION',
    target_type: 'Single target',
    spell_id: '203',
    effects: 'Decrease Hitpoints by 5 to 8',
    icon: 'https://alla.clumsysworld.com/images/icons/spell_203.png',
    pricing: {
      platinum: 0,
      gold: 0,
      silver: 0,
      bronze: 0,
      unknown: true
    }
  }
]

export const mockCacheStatus = {
  cleric: {
    cached: true,
    spell_count: 219,
    last_updated: '2025-07-02T12:58:55.856237'
  },
  pricing: {
    cached_count: 154,
    expired_count: 0,
    most_recent_timestamp: '2025-07-02T10:36:21.029163',
    total_spells: 219
  }
}