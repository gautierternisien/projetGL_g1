<script setup lang="ts">
import Card from '@/components/AppCard.vue'
import Header from '@/components/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { computed, watchEffect, onUnmounted } from 'vue'

const authStore = useAuthStore()
const router = useRouter()
const isConnected = computed(() => authStore.isConnected)

// Scroll lock si pas connecté
watchEffect(() => {
  if (!isConnected.value) {
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
})

// Scroll unlock au unmount
onUnmounted(() => {
  document.body.style.overflow = ''
})

function handleCardClick(e: Event) {
  if (!isConnected.value) {
    e.preventDefault()
  }
}
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Espace Communautaire" />
    <div class="scrollable-area">
      <div v-if="!isConnected" class="blur-overlay">
        <div class="lock-message">
          <span class="lock-icon">🔒</span>
          <p>Connectez-vous pour accéder à l'espace communautaire</p>
          <button @click="router.push('/login')" class="login-btn">Se connecter</button>
        </div>
      </div>

      <div :class="{ 'blurred-content': !isConnected }">
        <!-- Liste d'amis -->
        <RouterLink to="/communaute/amis" class="unstyled-link" @click="handleCardClick">
          <Card title="Liste d'amis" :hasArrow="isConnected">
            <div class="dashboard-card-content">
              <span class="dashboard-emoji">👥</span>
              <p class="dashboard-text">Retrouvez et comparez votre impact avec vos amis</p>
            </div>
          </Card>
        </RouterLink>

        <!-- Ligues -->
        <RouterLink to="/communaute/ligues" class="unstyled-link" @click="handleCardClick">
          <Card title="Ligues" :hasArrow="isConnected">
            <div class="dashboard-card-content">
              <span class="dashboard-emoji">🏆</span>
              <p class="dashboard-text">Participez à des ligues et classements communautaires</p>
            </div>
          </Card>
        </RouterLink>

        <!-- Evenements -->
        <RouterLink to="/communaute/evenements" class="unstyled-link" @click="handleCardClick">
          <Card title="Événements" :hasArrow="isConnected">
            <div class="dashboard-card-content">
              <span class="dashboard-emoji">📅</span>
              <p class="dashboard-text">
                Dernières missions réalisées par les amis (bientot les ligues)
              </p>
            </div>
          </Card>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.placeholder-content {
  padding: 20px;
  text-align: center;
  color: #666;
}

.blurred-content {
  filter: blur(5px);
  pointer-events: none;
  user-select: none;
}

.blur-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 10;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 500px;
}

.lock-message {
  background: rgba(255, 255, 255, 0.9);
  padding: 2rem;
  border-radius: 16px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.lock-icon {
  font-size: 3rem;
}

.login-btn {
  background-color: #679436;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  font-size: 1rem;
}

.dashboard-card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 10px 0;
  text-align: center;
}

.dashboard-emoji {
  font-size: 3rem;
}

.dashboard-text {
  font-size: 0.9rem;
  color: #666;
  font-weight: 500;
  max-width: 240px;
}

.unstyled-link {
  text-decoration: none;
  color: inherit;
  display: block;
}
</style>
