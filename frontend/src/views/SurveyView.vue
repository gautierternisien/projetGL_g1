<script setup lang="ts">
import Card from '@/components/AppCard.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import Header from '@/components/AppHeader.vue'
import { useProgressStore } from '@/stores/progress'
import { useAuthStore } from '@/stores/auth'
import { onMounted, computed, watch, onUnmounted, watchEffect } from 'vue'
import { useRouter } from 'vue-router'

const store = useProgressStore()
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

// Au montage de la vue, on utilise l'action centralisée du store
onMounted(async () => {
  if (isConnected.value) {
    if (!authStore.user) {
      await authStore.fetchUser()
    }
    if (authStore.user) {
      store.fetchAllProgress(authStore.user.username)
    }
  }
})

watch(
  () => authStore.user,
  (newUser) => {
    if (newUser) {
      store.fetchAllProgress(newUser.username)
    }
  },
)

function handleCardClick(e: Event) {
  if (!isConnected.value) {
    e.preventDefault()
  }
}
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Questionnaires" />

    <div class="scrollable-area">
      <div v-if="!isConnected" class="blur-overlay">
        <div class="lock-message">
          <span class="lock-icon">🔒</span>
          <p>Connectez-vous pour accéder aux questionnaires</p>
          <button @click="router.push('/login')" class="login-btn">Se connecter</button>
        </div>
      </div>

      <div :class="{ 'blurred-content': !isConnected }">
        <RouterLink to="/questionnaires/transport" @click="handleCardClick">
          <Card title="Transport & Mobilité" :has-arrow="isConnected">
            <div class="image-center">
              <span class="emoji-img">🚗</span>
            </div>
            <ProgressBar
              v-if="isConnected"
              :value="store.getCategoryScore('transport')"
            ></ProgressBar>
            <div v-else class="lock-placeholder">🔒</div>
          </Card>
        </RouterLink>

        <RouterLink to="/questionnaires/logement" @click="handleCardClick">
          <Card title="Logement & Énergie" :has-arrow="isConnected">
            <div class="image-center">
              <span class="emoji-img">🏠</span>
            </div>
            <ProgressBar
              v-if="isConnected"
              :value="store.getCategoryScore('logement')"
            ></ProgressBar>
            <div v-else class="lock-placeholder">🔒</div>
          </Card>
        </RouterLink>

        <RouterLink to="/questionnaires/alimentation" @click="handleCardClick">
          <Card title="Alimentation" :has-arrow="isConnected">
            <div class="image-center">
              <span class="emoji-img">🍽️</span>
            </div>
            <ProgressBar
              v-if="isConnected"
              :value="store.getCategoryScore('alimentation')"
            ></ProgressBar>
            <div v-else class="lock-placeholder">🔒</div>
          </Card>
        </RouterLink>

        <RouterLink to="/questionnaires/consommation" @click="handleCardClick">
          <Card title="Consommation" :has-arrow="isConnected">
            <div class="image-center">
              <span class="emoji-img">📦️</span>
            </div>
            <ProgressBar
              v-if="isConnected"
              :value="store.getCategoryScore('consommation')"
            ></ProgressBar>
            <div v-else class="lock-placeholder">🔒</div>
          </Card>
        </RouterLink>

        <RouterLink to="/questionnaires/recyclage" @click="handleCardClick">
          <Card title="Déchets & Recyclage" :has-arrow="isConnected">
            <div class="image-center">
              <span class="emoji-img">♻️️</span>
            </div>
            <ProgressBar
              v-if="isConnected"
              :value="store.getCategoryScore('recyclage')"
            ></ProgressBar>
            <div v-else class="lock-placeholder">🔒</div>
          </Card>
        </RouterLink>

        <RouterLink to="/questionnaires/numerique" @click="handleCardClick">
          <Card title="Numérique" :has-arrow="isConnected">
            <div class="image-center">
              <span class="emoji-img">💻️</span>
            </div>
            <ProgressBar
              v-if="isConnected"
              :value="store.getCategoryScore('numerique')"
            ></ProgressBar>
            <div v-else class="lock-placeholder">🔒</div>
          </Card>
        </RouterLink>

        <RouterLink to="/questionnaires/loisirs" @click="handleCardClick">
          <Card title="Loisirs" :has-arrow="isConnected">
            <div class="image-center">
              <span class="emoji-img">🃏️</span>
            </div>
            <ProgressBar
              v-if="isConnected"
              :value="store.getCategoryScore('loisirs')"
            ></ProgressBar>
            <div v-else class="lock-placeholder">🔒</div>
          </Card>
        </RouterLink>

        <RouterLink to="/questionnaires/quotidien" @click="handleCardClick">
          <Card title="Habitudes Quotidiennes" :has-arrow="isConnected">
            <div class="image-center">
              <span class="emoji-img">🗓️️</span>
            </div>
            <ProgressBar
              v-if="isConnected"
              :value="store.getCategoryScore('quotidien')"
            ></ProgressBar>
            <div v-else class="lock-placeholder">🔒</div>
          </Card>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
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
  /* Ensure overlay covers the scrollable area properly */
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
