<template>
  <div class="app-container">
    <RouterView />
  </div>

  <!-- Popup de notification pour nouveau trophée -->
  <Transition name="trophy-popup">
    <div v-if="showTrophyNotification" class="trophy-popup-overlay" @click="dismissTrophyNotification">
      <div class="trophy-popup" @click.stop>
        <div class="trophy-popup-header">
          <span class="trophy-popup-icon">🎉</span>
          <h3>Nouvelle récompense !</h3>
        </div>
        <div class="trophy-popup-content">
          <div class="trophy-popup-reward-icon">{{ trophiesStore.newTrophyNotification?.milestoneIcon }}</div>
          <p class="trophy-popup-title">{{ trophiesStore.newTrophyNotification?.trophy.title }}</p>
          <p class="trophy-popup-milestone">{{ trophiesStore.newTrophyNotification?.milestone }} obtenue</p>
        </div>
        <div class="trophy-popup-actions">
          <button @click="dismissTrophyNotification" class="trophy-popup-btn trophy-popup-btn-secondary">Plus tard</button>
          <button @click="goToTrophies" class="trophy-popup-btn trophy-popup-btn-primary">Voir</button>
        </div>
      </div>
    </div>
  </Transition>

  <nav class="bottom-nav" :class="{ 'nav-blurred': uiStore.isNavigationBlurred }">
    <RouterLink to="/" class="nav-item">
      <span>📊</span>
    </RouterLink>

    <RouterLink to="/questionnaires" class="nav-item">
      <span>📝</span>
    </RouterLink>

    <RouterLink to="/missions" class="nav-item">
      <span>🎯</span>
    </RouterLink>

    <RouterLink to="/communaute" class="nav-item">
      <div class="icon-wrapper">
        <span>👥</span>
        <span v-if="hasIncomingRequests" class="notification-badge"></span>
      </div>
    </RouterLink>

    <RouterLink to="/conseils" class="nav-item">
      <span>💡</span>
    </RouterLink>
  </nav>
</template>

<script setup lang="ts">
import { RouterView, RouterLink, useRoute, useRouter } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import { useFriendsStore } from '@/stores/friends'
import { useLeaguesStore } from '@/stores/leagues'
import { useAuthStore } from '@/stores/auth'
import { useTrophiesStore } from '@/stores/trophies'
import { computed, watch, onMounted } from 'vue'
import confetti from 'canvas-confetti'

const uiStore = useUiStore()
const friendsStore = useFriendsStore()
const leaguesStore = useLeaguesStore()
const authStore = useAuthStore()
const trophiesStore = useTrophiesStore()
const route = useRoute()
const router = useRouter()

const hasIncomingRequests = computed(() => {
  return friendsStore.incomingRequests.length > 0 || leaguesStore.invitations.length > 0
})

const showTrophyNotification = computed(() => {
  return trophiesStore.newTrophyNotification !== null
})

async function checkRequests() {
  if (authStore.isConnected) {
    try {
      await Promise.all([
        friendsStore.fetchIncomingRequests(),
        leaguesStore.fetchInvites()
      ])
    } catch {
      // ignore
    }
  }
}

async function checkTrophies() {
  if (authStore.isConnected && authStore.token) {
    try {
      await trophiesStore.checkNewTrophies(authStore.token)
    } catch {
      // ignore
    }
  }
}

function dismissTrophyNotification() {
  trophiesStore.dismissNotification()
}

function goToTrophies() {
  trophiesStore.dismissNotification()
  router.push({ name: 'trophees', query: { tab: 'obtained' } })
}

function launchConfetti() {
  // Effet de confettis multicolore pour célébrer le trophée
  const duration = 3000
  const end = Date.now() + duration

  const colors = ['#FFD700', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DFE6E9', '#A29BFE', '#FD79A8', '#FDCB6E']
  
  const frame = () => {
    confetti({
      particleCount: 4,
      angle: 60,
      spread: 20,
      origin: { x: 0 },
      colors: colors,
      scalar: 1.5,
      gravity: 0.8,
      zIndex: 100000
    })
    confetti({
      particleCount: 4,
      angle: 120,
      spread: 20,
      origin: { x: 1 },
      colors: colors,
      scalar: 1.5,
      gravity: 0.8,
      zIndex: 100000
    })

    if (Date.now() < end) {
      requestAnimationFrame(frame)
    }
  }
  
  frame()
}

onMounted(() => {
  if (authStore.isConnected && !authStore.user) {
    authStore.fetchUser().catch(() => {
      // Token invalid or expired, optional handling here
    })
  }
  checkRequests()
  checkTrophies()
})

watch(() => authStore.isConnected, (connected) => {
  if (connected) {
    checkRequests()
    checkTrophies()
  }
})

// Check for notifications on every route change
watch(() => route.path, () => {
  checkRequests()
  checkTrophies()
})

// Lance les confettis quand une notification de trophée apparaît
watch(() => showTrophyNotification.value, (isVisible) => {
  if (isVisible) {
    launchConfetti()
  }
})
</script>

<style scoped>
.app-container {
  width: 100%;
  height: 100%;
}

.bottom-nav {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);

  /* Largeur adaptative (max 350px pour ressembler à l'image) */
  width: 90%;
  max-width: 320px;
  height: 65px;

  /* Couleur de fond sombre (gris foncé) */
  background-color: #5e5e5e;

  /* Arrondi prononcé (forme de pilule) */
  border-radius: 35px;

  display: flex;
  justify-content: space-evenly;
  align-items: center;
  z-index: 1000;

  /* Ombre portée pour l'effet flottant */
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  transition: filter 0.3s ease;
}

.nav-blurred {
  filter: blur(5px);
  pointer-events: none;
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  background-color: #77786f;

  /* Taille fixe pour créer des cercles parfaits */
  width: 50px;
  height: 50px;
  border-radius: 50%;

  /* Transition douce pour l'effet au clic */
  transition: background-color 0.3s ease;

  font-size: 1.5rem;
}

.router-link-active {
  background-color: #9c9e89;
}

.icon-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.notification-badge {
  position: absolute;
  top: 3px; /* Ajusté pour être "en haut à droite" de l'icône visuellement dans le cercle */
  right: 3px;
  width: 10px;
  height: 10px;
  background-color: #ff0000;
  border-radius: 50%;
  box-shadow: 0 0 0 1px #5e5e5e; /* Petit contour pour séparer */
}

/* Popup de notification pour nouveau trophée */
.trophy-popup-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.6);
}

.trophy-popup {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  border-radius: 20px;
  padding: 24px;
  width: 85%;
  max-width: 320px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  text-align: center;
  font-family: 'Instrument Sans', sans-serif;
}

.trophy-popup-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.trophy-popup-icon {
  font-size: 2.5rem;
  animation: bounce 0.6s ease-in-out;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

.trophy-popup-header h3 {
  margin: 0;
  font-size: 1.5rem;
  color: #333;
  font-weight: 700;
}

.trophy-popup-content {
  margin: 20px 0;
}

.trophy-popup-reward-icon {
  font-size: 4rem;
  margin-bottom: 12px;
  animation: scale-in 0.5s ease-out;
}

@keyframes scale-in {
  0% { transform: scale(0); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

.trophy-popup-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
  margin: 8px 0;
}

.trophy-popup-milestone {
  font-size: 1rem;
  color: #555;
  margin: 4px 0;
  font-weight: 500;
}

.trophy-popup-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.trophy-popup-btn {
  border: none;
  padding: 12px 24px;
  border-radius: 25px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-family: 'Instrument Sans', sans-serif;
  flex: 1;
}

.trophy-popup-btn-secondary {
  background-color: rgba(255, 255, 255, 0.3);
  color: #333;
  border: 2px solid rgba(0, 0, 0, 0.1);
}

.trophy-popup-btn-secondary:hover {
  background-color: rgba(255, 255, 255, 0.5);
}

.trophy-popup-btn-primary {
  background-color: #679436;
  color: white;
}

.trophy-popup-btn-primary:hover {
  background-color: #577a2e;
  transform: scale(1.05);
}

/* Transitions */
.trophy-popup-enter-active {
  animation: popup-in 0.4s ease-out;
}

.trophy-popup-leave-active {
  animation: popup-out 0.3s ease-in;
}

@keyframes popup-in {
  0% {
    opacity: 0;
    transform: scale(0.8);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

@keyframes popup-out {
  0% {
    opacity: 1;
    transform: scale(1);
  }
  100% {
    opacity: 0;
    transform: scale(0.8);
  }
}
</style>
