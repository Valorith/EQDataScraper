<template>
  <div class="main-container">
    <div class="hero-section">
      <h1 class="main-title">Clumsy's World</h1>
      <p class="main-subtitle">Class Information</p>
    </div>
    
    <div class="classes-grid">
      <router-link 
        v-for="cls in classes" 
        :key="cls.name"
        :to="{ name: 'ClassSpells', params: { className: cls.name.toLowerCase() } }"
        :class="['class-card', cls.name.toLowerCase()]"
      >
        <div class="class-icon">
          <img 
            :src="`/icons/${cls.name.toLowerCase()}.gif`" 
            :alt="cls.name"
            @error="handleImageError"
          >
        </div>
        <div class="class-name">{{ cls.name }}</div>
      </router-link>
    </div>
  </div>
</template>

<script>
import { useSpellsStore } from '../stores/spells'

export default {
  name: 'Home',
  setup() {
    const spellsStore = useSpellsStore()
    
    return {
      classes: spellsStore.classes
    }
  },
  methods: {
    handleImageError(event) {
      const fallbackUrl = `https://wiki.heroesjourneyemu.com/${event.target.alt.toLowerCase()}.gif`
      event.target.src = fallbackUrl
      event.target.onerror = () => {
        event.target.style.display = 'none'
      }
    }
  }
}
</script>

<style scoped>
.hero-section {
  text-align: center;
  margin-bottom: 80px;
  position: relative;
  background: transparent;
}

.hero-section::before {
  content: '';
  position: absolute;
  top: -60%;
  left: 50%;
  transform: translateX(-50%);
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(var(--primary-rgb), 0.2) 0%, rgba(106, 76, 147, 0.15) 30%, transparent 70%);
  border-radius: 50%;
  filter: blur(100px);
  z-index: -1;
}

.main-title {
  font-family: 'Cinzel', serif;
  font-size: 5.5em;
  font-weight: 700;
  background: linear-gradient(135deg, var(--primary-color) 0%, #c8a8ff 50%, rgba(255,255,255,0.9) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 30px;
  text-shadow: 0 0 40px rgba(var(--primary-rgb), 0.6);
  animation: glow 4s ease-in-out infinite alternate;
  letter-spacing: 2px;
}

@keyframes glow {
  from { 
    text-shadow: 0 0 30px rgba(var(--primary-rgb), 0.5);
    transform: scale(1);
  }
  to { 
    text-shadow: 0 0 50px rgba(var(--primary-rgb), 0.8), 0 0 80px rgba(147, 112, 219, 0.4);
    transform: scale(1.01);
  }
}

.main-subtitle {
  font-size: 1.8em;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 400;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 40px;
  position: relative;
}

.main-subtitle::after {
  content: '';
  position: absolute;
  bottom: -15px;
  left: 50%;
  transform: translateX(-50%);
  width: 120px;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--primary-color), transparent);
}

.classes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 35px;
  margin-top: 60px;
  padding: 0 20px;
}

.class-card {
  background: linear-gradient(145deg, rgba(255,255,255,0.12), rgba(255,255,255,0.06));
  backdrop-filter: blur(25px);
  border: 2px solid rgba(255,255,255,0.15);
  border-radius: 24px;
  padding: 50px 20px;
  text-align: center;
  position: relative;
  overflow: hidden;
  transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  cursor: pointer;
  text-decoration: none;
  color: inherit;
  height: 384px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.class-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
  transition: left 0.8s;
}

.class-card::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(var(--class-color), 0.05), transparent);
  opacity: 0;
  transition: opacity 0.5s ease;
  pointer-events: none;
}

.class-card:hover::before {
  left: 100%;
}

.class-card:hover::after {
  opacity: 1;
}

.class-card:hover {
  transform: translateY(-15px) scale(1.03);
  border-color: rgba(var(--class-color-rgb), 0.6);
  box-shadow: 
    0 25px 60px rgba(var(--class-color-rgb), 0.3),
    0 0 40px rgba(var(--class-color-rgb), 0.2);
  background: linear-gradient(145deg, rgba(255,255,255,0.18), rgba(255,255,255,0.08));
}

.class-icon {
  width: 120px;
  height: 120px;
  margin-bottom: 35px;
  border-radius: 16px;
  transition: all 0.4s ease;
  animation: float 4s ease-in-out infinite;
  background: linear-gradient(135deg, var(--class-color), rgba(255,255,255,0.2));
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.2em;
  font-weight: bold;
  color: white;
  text-shadow: 2px 2px 6px rgba(0,0,0,0.6);
  border: 3px solid rgba(255,255,255,0.4);
  box-shadow: 0 8px 24px rgba(var(--class-color-rgb), 0.4);
  position: relative;
  overflow: hidden;
}

.class-icon::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
  transform: rotate(45deg);
  transition: transform 0.6s ease;
}

.class-card:hover .class-icon::before {
  transform: rotate(45deg) translate(50%, 50%);
}

.class-icon img {
  width: 85%;
  height: 85%;
  object-fit: cover;
  border-radius: 12px;
  z-index: 1;
  position: relative;
}

.class-icon.fallback {
  font-family: 'Cinzel', serif;
}

@keyframes float {
  0%, 100% { transform: translateY(0px) rotateY(0deg); }
  25% { transform: translateY(-8px) rotateY(2deg); }
  50% { transform: translateY(-5px) rotateY(0deg); }
  75% { transform: translateY(-12px) rotateY(-2deg); }
}

.class-card:hover .class-icon {
  transform: scale(1.15) translateY(-8px);
  animation-play-state: paused;
  box-shadow: 0 15px 40px rgba(var(--class-color-rgb), 0.6);
}

.class-name {
  font-family: 'Cinzel', serif;
  font-size: 1.9em;
  font-weight: 600;
  color: var(--text-dark);
  transition: all 0.4s ease;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
  letter-spacing: 1px;
}

.class-card:hover .class-name {
  color: var(--class-color);
  text-shadow: 
    0 0 15px rgba(var(--class-color-rgb), 0.6),
    0 2px 4px rgba(0,0,0,0.5);
  transform: translateY(-2px);
}

@media (max-width: 1200px) {
  .classes-grid { grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); }
}

@media (max-width: 768px) {
  .main-title { font-size: 4em; }
  .main-subtitle { font-size: 1.4em; letter-spacing: 2px; }
  .classes-grid { 
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); 
    gap: 25px; 
    padding: 0 10px;
  }
  .class-card { height: 336px; padding: 40px 15px; }
  .class-icon { width: 100px; height: 100px; margin-bottom: 30px; }
  .class-name { font-size: 1.6em; }
}

@media (max-width: 480px) {
  .main-container { padding: 40px 15px; }
  .main-title { font-size: 3.2em; }
  .classes-grid { grid-template-columns: 1fr; }
  .class-card { height: 312px; padding: 35px 15px; }
  .class-icon { width: 90px; height: 90px; margin-bottom: 25px; }
}
</style> 