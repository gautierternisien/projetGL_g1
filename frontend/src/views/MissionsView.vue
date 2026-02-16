<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import Card from '@/components/AppCard.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import { RouterLink, useRouter } from 'vue-router'
import { computed, ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import {
  derivePreferencesFromAnswers,
  PREFERENCE_LABELS,
  type DerivedPreferences,
} from '@/utils/profileMapping'
import { loadAnswers } from '@/lib/ngc/answersStorage.ts'

const API_URL = 'http://localhost:8000'
const authStore = useAuthStore()
const router = useRouter()

const isConnected = computed(() => authStore.isConnected)
const user = computed(() => authStore.user)

// --- GESTION DES PREFERENCES / ONBOARDING ---
const showOnboardingModal = ref(false)
const userPreferences = ref<Partial<DerivedPreferences>>({})
const isSubmittingPrefs = ref(false)

async function fetchPreferences() {
  if (!isConnected.value || !user.value) return

  try {
    const res = await fetch(`${API_URL}/users/me/preferences`, {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })

    if (res.ok) {
      const prefsData = await res.json()
      if (prefsData.data && Object.keys(prefsData.data).length > 0) {
        userPreferences.value = prefsData.data
      } else {
        const defaults = derivePreferencesFromAnswers(loadAnswers() || {})
        userPreferences.value = defaults
      }
      // On charge les missions une fois qu'on a les prefs
      loadCategoryCounts()
    }
  } catch (e) {
    console.error('Erreur fetch preferences', e)
  }
}

// Sauvegarde les préférences validées par l'utilisateur
async function savePreferences() {
  isSubmittingPrefs.value = true
  try {
    const payload = {
      data: userPreferences.value,
      has_completed_onboarding: true,
    }

    const res = await fetch(`${API_URL}/users/me/preferences`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify(payload),
    })

    if (res.ok) {
      showOnboardingModal.value = false
      // On charge les missions maintenant qu'on a le profil
      loadCategoryCounts()
    }
  } catch (e) {
    console.error('Erreur sauvegarde prefs', e)
  } finally {
    isSubmittingPrefs.value = false
  }
}

async function openSettings() {
    await fetchPreferences()
    showOnboardingModal.value = true
}

async function resetToQuestionnaire() {
  if (!isConnected.value) return

  try {
    // 1. On récupère les réponses brutes sauvegardées en BDD
    const res = await fetch(`${API_URL}/ngc/answers/me`, {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })

    if (res.ok) {
      const json = await res.json()
      // L'API renvoie { data: { ... }, updated_at: ... }
      const dbAnswers = json.data || {}

      // 2. On recalcule les préférences avec ces données
      const suggestions = derivePreferencesFromAnswers(dbAnswers)

      // 3. On met à jour la modale
      userPreferences.value = suggestions
    }
  } catch (e) {
    console.error('Erreur lors de la récupération du questionnaire', e)
  }
}

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
    fetchPreferences()
  }
})

// Watch user changes (e.g. after login or refreshing page when user is fetched)
import { watch } from 'vue'
watch(user, (newUser) => {
  if (newUser) {
    fetchPreferences()
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

      <div v-if="isConnected" class="settings-container">
        <button class="settings-btn-static" @click="openSettings">⚙️ Gérer mes préférences</button>
      </div>
    </div>

    <div v-if="showOnboardingModal" class="blur-overlay">
      <div class="onboarding-card">
        <h2>🎯 Personnalisons vos missions</h2>
        <p class="intro-text">Activez ou désactivez les thématiques selon votre profil :</p>

        <button class="reset-link" @click="resetToQuestionnaire">
          🔄 Réinitialiser selon mon questionnaire
        </button>

        <div class="prefs-scroll">
          <div v-for="(label, key) in PREFERENCE_LABELS" :key="key" class="pref-item">
            <label class="switch-container">
              <span>{{ label }}</span>
              <input type="checkbox" v-model="userPreferences[key]" />
              <span class="checkmark"></span>
            </label>
          </div>
        </div>

        <button class="save-btn" @click="savePreferences" :disabled="isSubmittingPrefs">
          {{ isSubmittingPrefs ? '...' : 'Enregistrer' }}
        </button>
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

/* --- STYLE MODALE ONBOARDING --- */
.blur-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(5px);
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
}

.onboarding-card {
  background: white;
  width: 90%;
  max-width: 400px;
  max-height: 85vh;
  border-radius: 20px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
  padding: 24px;
  display: flex;
  flex-direction: column;
  animation: popIn 0.3s ease-out;
}

@keyframes popIn {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.onboarding-card h2 {
  font-size: 1.3rem;
  color: #2c3e50;
  margin-bottom: 10px;
  text-align: center;
}

.intro-text {
  font-size: 0.9rem;
  color: #666;
  text-align: center;
  margin-bottom: 20px;
}

.prefs-scroll {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 20px;
  border-top: 1px solid #eee;
  border-bottom: 1px solid #eee;
  padding: 10px 0;
}

.pref-item {
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f5;
}

/* Switch Custom Style */
.switch-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  font-size: 0.95rem;
  color: #333;
}

.switch-container input {
  display: none;
}

.checkmark {
  width: 44px;
  height: 24px;
  background-color: #ddd;
  border-radius: 24px;
  position: relative;
  transition: 0.2s;
}

.checkmark::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 20px;
  height: 20px;
  background-color: white;
  border-radius: 50%;
  transition: 0.2s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.switch-container input:checked + .checkmark {
  background-color: #679436;
}

.switch-container input:checked + .checkmark::after {
  transform: translateX(20px);
}

.save-btn {
  background-color: #679436;
  color: white;
  border: none;
  padding: 14px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.save-btn:disabled {
  background-color: #ccc;
}

.settings-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding-bottom: 30px; /* Un peu d'espace en bas pour ne pas coller au bord */
}

.settings-btn-static {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 10px 20px;
  background-color: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 20px; /* Forme de pilule */
  color: #555;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: background 0.2s;
}

.settings-btn-static:active {
  background-color: #e0e0e0;
  transform: scale(0.98);
}

.reset-link {
  background: none;
  border: none;
  color: #679436;
  text-decoration: underline;
  cursor: pointer;
  font-size: 0.85rem;
  margin-bottom: 15px;
  align-self: center; /* Pour centrer le lien */
}

.reset-link:hover {
  color: #4e7a25;
}
</style>
