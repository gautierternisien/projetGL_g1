<template>
  <div class="app-container">
    <RouterView />
  </div>

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
import { RouterView, RouterLink } from 'vue-router'
import { useUiStore } from '@/stores/ui'
import { useFriendsStore } from '@/stores/friends'
import { useLeaguesStore } from '@/stores/leagues'
import { useAuthStore } from '@/stores/auth'
import { computed, watch, onMounted } from 'vue'

const uiStore = useUiStore()
const friendsStore = useFriendsStore()
const leaguesStore = useLeaguesStore()
const authStore = useAuthStore()

const hasIncomingRequests = computed(() => {
  return friendsStore.incomingRequests.length > 0 || leaguesStore.invitations.length > 0
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

onMounted(() => {
  if (authStore.isConnected && !authStore.user) {
    authStore.fetchUser().catch(() => {
      // Token invalid or expired, optional handling here
    })
  }
  checkRequests()
})

watch(() => authStore.isConnected, (connected) => {
  if (connected) {
    checkRequests()
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
  top: 3px; /* Ajusté pour être "en haut à droite" de l'icone visuellement dans le cercle */
  right: 3px;
  width: 10px;
  height: 10px;
  background-color: #ff0000;
  border-radius: 50%;
  box-shadow: 0 0 0 1px #5e5e5e; /* Petit contour pour séparer */
}
</style>
