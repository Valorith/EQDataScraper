<template>
  <router-link to="/" class="app-logo-link">
    <div class="app-logo">
      <svg class="logo-svg" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <!-- Outer magical circle -->
        <defs>
          <linearGradient id="logoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#9370db;stop-opacity:1" />
            <stop offset="50%" style="stop-color:#c8a8ff;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#6a4c93;stop-opacity:1" />
          </linearGradient>
          <filter id="logoGlow">
            <feGaussianBlur stdDeviation="4" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        
        <!-- Outer circle with mystical pattern -->
        <circle cx="100" cy="100" r="90" fill="none" stroke="url(#logoGradient)" stroke-width="3" opacity="0.8"/>
        <circle cx="100" cy="100" r="85" fill="none" stroke="url(#logoGradient)" stroke-width="1" opacity="0.5"/>
        
        <!-- Inner magical symbols -->
        <g class="logo-runes">
          <!-- Top rune -->
          <path d="M100 25 L95 35 L100 40 L105 35 Z" fill="url(#logoGradient)" opacity="0.7"/>
          <!-- Right rune -->
          <path d="M175 100 L165 95 L160 100 L165 105 Z" fill="url(#logoGradient)" opacity="0.7"/>
          <!-- Bottom rune -->
          <path d="M100 175 L95 165 L100 160 L105 165 Z" fill="url(#logoGradient)" opacity="0.7"/>
          <!-- Left rune -->
          <path d="M25 100 L35 95 L40 100 L35 105 Z" fill="url(#logoGradient)" opacity="0.7"/>
        </g>
        
        <!-- Central spell book icon -->
        <g class="logo-book" filter="url(#logoGlow)">
          <!-- Book base -->
          <path d="M70 70 L70 130 L100 120 L130 130 L130 70 L100 80 Z" 
                fill="#2a2e36" 
                stroke="url(#logoGradient)" 
                stroke-width="2"/>
          <!-- Book pages -->
          <path d="M75 75 L75 115 L100 107 L100 85 Z" fill="#3a3e46" opacity="0.8"/>
          <path d="M125 75 L125 115 L100 107 L100 85 Z" fill="#3a3e46" opacity="0.8"/>
          <!-- Mystical symbol on book -->
          <circle cx="100" cy="95" r="8" fill="none" stroke="#c8a8ff" stroke-width="1.5" opacity="0.9"/>
          <path d="M100 87 L100 103 M92 95 L108 95" stroke="#c8a8ff" stroke-width="1.5" opacity="0.9"/>
        </g>
        
        <!-- Floating magical particles -->
        <g class="logo-particles">
          <circle cx="60" cy="50" r="2" fill="#c8a8ff" opacity="0.6">
            <animate attributeName="opacity" values="0.6;1;0.6" dur="3s" repeatCount="indefinite"/>
          </circle>
          <circle cx="140" cy="60" r="1.5" fill="#9370db" opacity="0.5">
            <animate attributeName="opacity" values="0.5;0.9;0.5" dur="2.5s" repeatCount="indefinite"/>
          </circle>
          <circle cx="150" cy="140" r="2" fill="#c8a8ff" opacity="0.7">
            <animate attributeName="opacity" values="0.7;1;0.7" dur="2s" repeatCount="indefinite"/>
          </circle>
          <circle cx="50" cy="130" r="1.5" fill="#9370db" opacity="0.6">
            <animate attributeName="opacity" values="0.6;0.9;0.6" dur="3.5s" repeatCount="indefinite"/>
          </circle>
        </g>
      </svg>
      
      <div class="logo-text">
        <div class="logo-title">Clumsy's</div>
        <div class="logo-subtitle">World</div>
      </div>
    </div>
  </router-link>
</template>

<script>
export default {
  name: 'AppLogo'
}
</script>

<style scoped>
.app-logo-link {
  text-decoration: none;
  display: inline-block;
  position: fixed;
  top: 20px;
  left: 20px;
  z-index: 1000;
  transition: transform 0.3s ease;
}

.app-logo-link:hover {
  transform: scale(1.05);
}

.app-logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  background: linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03));
  backdrop-filter: blur(20px);
  border: 1px solid rgba(147, 112, 219, 0.3);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.app-logo:hover {
  background: linear-gradient(145deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06));
  border-color: rgba(147, 112, 219, 0.5);
  box-shadow: 0 6px 30px rgba(147, 112, 219, 0.3);
}

.logo-svg {
  width: 48px;
  height: 48px;
  filter: drop-shadow(0 2px 8px rgba(147, 112, 219, 0.4));
}

.logo-runes {
  animation: rotate-slow 20s linear infinite;
  transform-origin: center;
}

.logo-book {
  animation: float 4s ease-in-out infinite;
  transform-origin: center;
}

.logo-particles {
  animation: rotate-reverse 15s linear infinite;
  transform-origin: center;
}

@keyframes rotate-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes rotate-reverse {
  from { transform: rotate(360deg); }
  to { transform: rotate(0deg); }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-3px); }
}

.logo-text {
  display: flex;
  flex-direction: column;
  line-height: 1;
}

.logo-title {
  font-family: 'Cinzel', serif;
  font-size: 1.4rem;
  font-weight: 700;
  background: linear-gradient(135deg, #c8a8ff 0%, #9370db 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 20px rgba(147, 112, 219, 0.5);
  letter-spacing: 0.5px;
}

.logo-subtitle {
  font-family: 'Cinzel', serif;
  font-size: 1.1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-top: 2px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .app-logo-link {
    top: 10px;
    left: 10px;
  }
  
  .app-logo {
    padding: 6px 12px;
    gap: 8px;
  }
  
  .logo-svg {
    width: 40px;
    height: 40px;
  }
  
  .logo-title {
    font-size: 1.2rem;
  }
  
  .logo-subtitle {
    font-size: 0.9rem;
  }
}

@media (max-width: 480px) {
  .logo-text {
    display: none;
  }
  
  .app-logo {
    padding: 8px;
  }
  
  .logo-svg {
    width: 36px;
    height: 36px;
  }
}
</style>