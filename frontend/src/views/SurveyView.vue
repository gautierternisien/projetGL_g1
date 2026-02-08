<script setup lang="ts">
import Card from '@/components/AppCard.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import Header from '@/components/AppHeader.vue'
import { useProgressStore } from '@/stores/progress'
import { useAuthStore } from '@/stores/auth'
import { onMounted, onUnmounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'

const store = useProgressStore()
const authStore = useAuthStore()
const router = useRouter()
const isConnected = computed(() => authStore.isConnected)

function syncProgressFromLocalStorage() {
  store.syncFromLocalAnswers()
}

onMounted(async () => {
  // ton comportement actuel
  if (isConnected.value) {
    if (!authStore.user) await authStore.fetchUser()
    if (authStore.user) await store.fetchAllProgress(authStore.user.id)
  }

  // + sync local progress NGC (si tu passes par localStorage)
  syncProgressFromLocalStorage()
  window.addEventListener('focus', syncProgressFromLocalStorage)
})

onUnmounted(() => {
  window.removeEventListener('focus', syncProgressFromLocalStorage)
})

watch(
  () => authStore.user,
  async (newUser) => {
    if (newUser) await store.fetchAllProgress(newUser.id)
    syncProgressFromLocalStorage()
  },
)

function handleCardClick(e: Event) {
  if (!isConnected.value) e.preventDefault()
}
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Questionnaires" />

    <div class="scrollable-area" :style="!isConnected ? { overflow: 'hidden' } : {}">
      <div v-if="!isConnected" class="blur-overlay">
        <div class="lock-message">
          <span class="lock-icon">🔒</span>
          <p>Connectez-vous pour accéder aux questionnaires</p>
          <button @click="router.push('/login')" class="login-btn">Se connecter</button>
        </div>
      </div>

      <div :class="{ 'blurred-content': !isConnected }">
        <RouterLink to="/questionnaires/transport" @click="handleCardClick">
          <Card title="Transport" :has-arrow="isConnected">
            <div class="image-center"><span class="emoji-img">🚗</span></div>
            <ProgressBar v-if="isConnected" :value="store.getCategoryScore('transport')" />
            <div v-else class="lock-placeholder">🔒</div>
          </Card>
        </RouterLink>

        <RouterLink to="/questionnaires/logement" @click="handleCardClick">
          <Card title="Logement" :has-arrow="isConnected">
            <div class="image-center"><span class="emoji-img">🏠</span></div>
            <ProgressBar v-if="isConnected" :value="store.getCategoryScore('logement')" />
            <div v-else class="lock-placeholder">🔒</div>
          </Card>
        </RouterLink>

        <RouterLink to="/questionnaires/alimentation" @click="handleCardClick">
          <Card title="Alimentation" :has-arrow="isConnected">
            <div class="image-center"><span class="emoji-img">🍽️</span></div>
            <ProgressBar v-if="isConnected" :value="store.getCategoryScore('alimentation')" />
            <div v-else class="lock-placeholder">🔒</div>
          </Card>
        </RouterLink>

        <RouterLink to="/questionnaires/divers" @click="handleCardClick">
          <Card title="Divers" :has-arrow="isConnected">
            <div class="image-center"><span class="emoji-img">📦️</span></div>
            <ProgressBar v-if="isConnected" :value="store.getCategoryScore('divers')" />
            <div v-else class="lock-placeholder">🔒</div>
          </Card>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* tes styles inchangés */
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
.lock-placeholder {
  text-align: center;
  font-size: 1.5rem;
  color: #999;
}
.image-center {
  flex-shrink: 0;
  margin-left: 15px;
  display: flex;
  justify-content: center;
  align-items: center;
}
.emoji-img {
  font-size: 2.5rem;
}
</style>

