<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import Card from '@/components/AppCard.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import { RouterLink, useRouter } from 'vue-router'
import { computed, ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const API_URL = 'http://localhost:8000'
const authStore = useAuthStore()
const router = useRouter()
const isConnected = computed(() => authStore.isConnected)
const user = computed(() => authStore.user)

const countsByCategory = ref<
  Record<string, { completed: number; total: number; inProgress: number }>
>({})

// tableau statique des catégories
const CATEGORY_DATA = [
  { key: 'transport', title: 'Transport', emoji: '🚗' },
  { key: 'logement', title: 'Logement', emoji: '🏠' },
  { key: 'alimentation', title: 'Alimentation', emoji: '🍽️' },
  { key: 'divers', title: 'Divers', emoji: '📦️' },
]

const categoriesKeys = ref(CATEGORY_DATA.map((c) => c.key))

async function loadCategoryCounts() {
  if (!isConnected.value) return

  // Si l'utilisateur n'est pas encore chargé (ex: F5, token présent main user null), on ne charge pas encore
  // On attendra que le watcher le déclenche
  if (!user.value) return

  try {
    const userIdParam = user.value ? `?user_id=${user.value.id}` : ''
    const results = await Promise.all(
      categoriesKeys.value.map((k) =>
        fetch(`${API_URL}/missions/${k}${userIdParam}`, { cache: 'no-store' })
          .then((r) => (r.ok ? r.json() : []))
          .catch(() => []),
      ),
    )

    results.forEach((data, i) => {
      const key = categoriesKeys.value[i]
      // On s'assure que la clé existe
      if (!key) return

      if (Array.isArray(data)) {
        const total = data.length
        const completed = data.filter((d) =>
          /termine|terminee|done|completed/i.test(d.status ?? ''),
        ).length
        const inProgress = data.filter((d) =>
          /en_cours|encours|in_progress|ongoing|open/i.test(d.status ?? ''),
        ).length
        countsByCategory.value[key] = { completed, total, inProgress }
      } else {
        countsByCategory.value[key] = { completed: 0, total: 0, inProgress: 0 }
      }
    })
  } catch (e) {
    console.warn('loadCategoryCounts failed', e)
  }
}

onMounted(() => {
  if (user.value) {
    loadCategoryCounts()
  }
})

// Watch user changes (e.g. after login or refreshing page when user is fetched)
import { watch } from 'vue'
watch(user, (newUser) => {
  if (newUser) {
    loadCategoryCounts()
  }
})

// Computed categories avec progression
const categoriesWithProgress = computed(() => {
  return CATEGORY_DATA.map((c) => {
    const backend = countsByCategory.value[c.key]
    const totalConfigured = backend ? backend.total : 0
    const completed = backend ? backend.completed : 0
    const inProgress = backend ? backend.inProgress : 0

    // Calcul pondéré : 100% pour terminé, 50% pour en cours
    const weightedScore = completed + inProgress * 0.5
    const pct = totalConfigured > 0 ? Math.round((weightedScore / totalConfigured) * 100) : 0

    return { ...c, pct, completed, inProgress, total: totalConfigured }
  })
})

function handleCardClick(e: Event) {
  if (!isConnected.value) {
    e.preventDefault()
  }
}
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Missions" />

    <div class="scrollable-area" :style="!isConnected ? { overflow: 'hidden' } : {}">
      <div v-if="!isConnected" class="blur-overlay">
        <div class="lock-message">
          <span class="lock-icon">🔒</span>
          <p>Connectez-vous pour accéder aux missions</p>
          <button @click="router.push('/login')" class="login-btn">Se connecter</button>
        </div>
      </div>

      <div class="categories-list" :class="{ 'blurred-content': !isConnected }">
        <RouterLink
          v-for="cat in categoriesWithProgress"
          :key="cat.key"
          :to="`/missions/${cat.key}`"
          class="unstyled-link category-item"
          @click="handleCardClick"
        >
          <Card :title="cat.title" :hasArrow="isConnected">
            <div class="mission-row">
              <div class="emoji-side">
                <span class="emoji-img">{{ cat.emoji }}</span>
              </div>
              <div class="mission-info">
                <div class="mission-count" v-if="isConnected">
                  En cours: {{ cat.inProgress }} • Terminées: {{ cat.completed }} • Total:
                  {{ cat.total }}
                </div>
                <ProgressBar v-if="isConnected" :value="cat.pct" :showLabel="false" />
                <div v-else class="lock-placeholder">🔒</div>
              </div>
            </div>
          </Card>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* .dashboard-wrapper,blur et lock sont dans global.css */
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
  width: 100%;
}

.categories-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mission-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.emoji-side {
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.emoji-img {
  font-size: 2.5rem;
  line-height: 1;
}

.mission-info {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.mission-count {
  color: #666;
  font-size: 0.85rem;
}

.unstyled-link {
  text-decoration: none;
  color: inherit;
}
</style>
