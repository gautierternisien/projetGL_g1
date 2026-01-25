<script setup lang="ts">
import Card from '@/components/AppCard.vue'
import Header from '@/components/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { useFriendsStore } from '@/stores/friends'
import { useRouter } from 'vue-router'
import { computed, watchEffect, onUnmounted, onMounted } from 'vue'

const authStore = useAuthStore()
const friendsStore = useFriendsStore()
const router = useRouter()
const isConnected = computed(() => authStore.isConnected)

onMounted(async () => {
  if (isConnected.value) {
    try {
      await friendsStore.fetchIncomingRequests()
    } catch {
      // ignore
    }
  }
})

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
              <p class="dashboard-text">Retrouvez vos amis</p>
              <p v-if="friendsStore.incomingRequests.length > 0" class="pending-text">
                Vous avez {{ friendsStore.incomingRequests.length }} demande{{
                  friendsStore.incomingRequests.length > 1 ? 's' : ''
                }}
                en attente
              </p>
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
          <Card title="Activité des Amis" :hasArrow="isConnected">
            <div class="dashboard-card-content">
              <span class="dashboard-emoji">🍾</span>
              <p class="dashboard-text">
                Dernières missions réalisées par les amis (bientôt par les gens des ligues)
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

.pending-text {
  color: #ffa500;
  font-size: 0.85rem;
  font-weight: 600;
  margin-top: 4px;
}

.unstyled-link {
  text-decoration: none;
  color: inherit;
  display: block;
}
</style>
