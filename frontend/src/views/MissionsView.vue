<script setup lang="ts">
import Header from '@/components/Header.vue'
import Card from '@/components/Card.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import { RouterLink } from 'vue-router'
import { computed, ref, onMounted } from 'vue'
import { useProgressStore } from '@/stores/progress'

const store = useProgressStore()
const API_URL = 'http://localhost:8000'

const countsByCategory = ref<Record<string, { completed: number; total: number; inProgress: number }>>({})

// tableau statique des catégories
const CATEGORY_DATA = [
  { key: 'transport', title: 'Transport & Mobilité', emoji: '🚗' },
  { key: 'logement', title: 'Logement & Énergie', emoji: '🏠' },
  { key: 'alimentation', title: 'Alimentation', emoji: '🍽️' },
  { key: 'consommation', title: 'Consommation', emoji: '📦️' },
  { key: 'recyclage', title: 'Déchets & Recyclage', emoji: '♻️️' },
  { key: 'numerique', title: 'Numérique', emoji: '💻️' },
  { key: 'loisirs', title: 'Loisirs', emoji: '🃏️' },
  { key: 'quotidien', title: 'Habitudes Quotidiennes', emoji: '🗓️️' },
]

const categoriesKeys = ref(CATEGORY_DATA.map(c => c.key))

async function loadCategoryCounts() {
  try {
    const results = await Promise.all(
      categoriesKeys.value.map(k =>
        fetch(`${API_URL}/missions/${k}`, { cache: 'no-store' })
          .then(r => (r.ok ? r.json() : []))
          .catch(() => [])
      )
    )

    results.forEach((data, i) => {
      const key = categoriesKeys.value[i]
      if (Array.isArray(data)) {
        const total = data.length
        const completed = data.filter(d => /termine|terminee|done|completed/i.test(d.status ?? '')).length
        const inProgress = data.filter(d => /en_cours|encours|in_progress|ongoing|open/i.test(d.status ?? '')).length
        countsByCategory.value[key] = { completed, total, inProgress }
      } else {
        countsByCategory.value[key] = { completed: 0, total: 0, inProgress: 0 }
      }
    })
  } catch (e) {
    console.warn('loadCategoryCounts failed', e)
  }
}

onMounted(loadCategoryCounts)

// Computed categories avec progression
const categoriesWithProgress = computed(() => {
  return CATEGORY_DATA.map(c => {
    const backend = countsByCategory.value[c.key]
    const pct = store.getCategoryScore(c.key)
    const totalConfigured = backend ? backend.total : 0
    const completed = backend ? backend.completed : Math.round((pct / 100) * totalConfigured)
    const inProgress = backend ? backend.inProgress : Math.max(0, totalConfigured - completed)
    return { ...c, pct, completed, inProgress }
  })
})
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Missions" />

    <div class="scrollable-area">
      <div class="categories-list">
        <RouterLink
          v-for="cat in categoriesWithProgress"
          :key="cat.key"
          :to="`/missions/${cat.key}`"
          class="unstyled-link category-item"
        >
          <Card :title="cat.title" :hasArrow="true">
            <div class="mission-row">
              <div class="emoji-side">
                <span class="emoji-img">{{ cat.emoji }}</span>
              </div>
              <div class="mission-info">
                <div class="mission-count">En cours: {{ cat.inProgress }} • Terminées: {{ cat.completed }}</div>
                <ProgressBar :value="cat.pct" :showLabel="false" />
              </div>
            </div>
          </Card>
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-wrapper {
  background-color: white;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: 'Instrument Sans', sans-serif;
  position: relative;
}

.scrollable-area {
  padding: 100px 20px;
  overflow-y: auto;
  flex: 1;
  -webkit-overflow-scrolling: touch;
}

.categories-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.mission-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.emoji-side {
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.emoji-img {
  font-size: 2.5rem;
}

.mission-info {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.mission-count {
  font-weight: 700;
  color: #333;
  font-size: 0.95rem;
}

.unstyled-link {
  text-decoration: none;
  color: inherit;
}
</style>
