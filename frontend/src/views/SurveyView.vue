<script setup lang="ts">
import Card from '@/components/AppCard.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import Header from '@/components/AppHeader.vue'
import { useProgressStore } from '@/stores/progress'
import { useAuthStore } from '@/stores/auth'
import { onMounted, onUnmounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { fetchRemoteAnswers } from '@/lib/ngc/answersStorage'
import { computeCategoryProgressFromAnswers } from '@/utils/ngcProgress'

const store = useProgressStore()
const authStore = useAuthStore()
const router = useRouter()
const isConnected = computed(() => authStore.isConnected)

async function syncProgress() {
  if (!isConnected.value || !authStore.token) {
    // Si invité, on nettoie ou on laisse à 0
    // Mais comme on a désactivé le local storage, c'est 0.
    return
  }

  try {
    const remote = await fetchRemoteAnswers(authStore.token)
    if (remote) {
      const progress = computeCategoryProgressFromAnswers(remote)
      store.setScore('transport', progress.transport)
      store.setScore('logement', progress.logement)
      store.setScore('alimentation', progress.alimentation)
      store.setScore('divers', progress.divers)
    }
  } catch (e) {
    console.error('Erreur syncProgress', e)
  }
}

onMounted(async () => {
  // ton comportement actuel
  if (isConnected.value) {
    if (!authStore.user) await authStore.fetchUser()
  }

  await syncProgress()
  window.addEventListener('focus', syncProgress)
})

onUnmounted(() => {
  window.removeEventListener('focus', syncProgress)
})

watch(
  () => authStore.user,
  async () => {
    await syncProgress()
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
