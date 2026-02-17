<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import Card from '@/components/AppCard.vue'
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Mission, MissionStatus } from '@/types/mission'
import { useAuthStore } from '@/stores/auth'
import { PREFERENCE_LABELS, type DerivedPreferences } from '@/utils/profileMapping'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const category = route.params.category as string
const user = computed(() => authStore.user)

const CATEGORY_PREFS_MAP: Record<string, string[]> = {
  transport: ['possession_voiture', 'possession_velo', 'prend_avion'],
  logement: ['est_proprietaire', 'vit_en_maison', 'vit_en_appartement', 'passoire_thermique'],
  alimentation: [
    'viande_rouge_importante',
    'eau_bouteille',
    'conso_pas_locaux',
    'conso_pas_saison',
    'boissons_chaudes',
    'soda',
    'alcool',
    'dechets_importants',
  ],
  divers: ['shopping_important', 'fumeur'],
}

// --- LOGIQUE PREFERENCES ---
const showPrefsModal = ref(false)
const userPreferences = ref<Partial<DerivedPreferences>>({})
const isSubmittingPrefs = ref(false)
const API_URL = 'http://localhost:8000'

// Filtre les labels pour n'afficher que ceux de la catégorie en cours
const filteredPreferenceLabels = computed(() => {
  const allowedKeys = CATEGORY_PREFS_MAP[category] || []
  const filtered: Record<string, string> = {}

  // Si la catégorie n'est pas mappée (ex: "quotidien" si ajouté plus tard), on montre tout ou rien.
  // Ici on montre tout par défaut si pas mappé, sinon on filtre.
  if (allowedKeys.length === 0) return PREFERENCE_LABELS

  for (const key of allowedKeys) {
    if (key in PREFERENCE_LABELS) {
      filtered[key] = PREFERENCE_LABELS[key as keyof DerivedPreferences]
    }
  }
  return filtered
})

async function openCategorySettings() {
  if (!authStore.isConnected) return

  try {
    const res = await fetch(`${API_URL}/users/me/preferences`, {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (res.ok) {
      const data = await res.json()
      userPreferences.value = data.data || {}
      showPrefsModal.value = true
    }
  } catch (e) {
    console.error('Erreur chargement prefs', e)
  }
}

async function saveCategoryPreferences() {
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
      showPrefsModal.value = false
      // On recharge les missions car le filtrage a pu changer
      await loadMissions()
    }
  } catch (e) {
    console.error('Erreur save', e)
  } finally {
    isSubmittingPrefs.value = false
  }
}

onMounted(() => {
  if (!authStore.isConnected) {
    router.push('/login')
    return
  }
  // loadMissions() // Retiré, on gère avec le watcher et onMounted combinés plus bas
})

// ref to the scrolling container so we scroll relative to it
const containerRef = ref<HTMLElement | null>(null)
const HEADER_OFFSET = 100 // matches padding-top used in layout

const CATEGORY_DISPLAY_NAMES: Record<string, string> = {
  transport: 'Transport & Mobilité',
  alimentation: 'Alimentation',
  logement: 'Logement & Énergie',
  divers: 'Divers',
}

const title = computed(() => CATEGORY_DISPLAY_NAMES[category] || category)

// Simple tab state: 0 = En cours, 1 = Terminées, 2 = Nouvelles
const activeTab = ref(0)

const tabs = [
  { id: 0, label: 'Missions en cours' },
  { id: 1, label: 'Missions terminées' },
  { id: 2, label: 'Nouvelles missions' },
]

// Placeholder data for each tab (kept as fallback if backend empty)
import { reactive } from 'vue'
// keep empty fallbacks — fake missions are served by the backend now
const sampleMissions = reactive<Record<number, Mission[]>>({ 0: [], 1: [], 2: [] })

// Remote missions (fetched from backend)
const remoteMissions = ref<Mission[]>([])

interface RawMission {
  id: number | string
  title: string
  description?: string
  desc?: string
  status?: string
}

// Load missions for this category from backend
async function loadMissions() {
  if (!authStore.user) return // Attendre le user

  try {
    const userIdParam = authStore.user ? `?user_id=${authStore.user.id}` : ''
    const res = await fetch(`${API_URL}/missions/${category}${userIdParam}`, { cache: 'no-store' })
    if (res.ok) {
      const data = await res.json()
      // Normalise les clés: backend peut renvoyer `desc` ou `description`.
      if (Array.isArray(data)) {
        remoteMissions.value = data.map((d: RawMission) => ({
          id: Number(d.id),
          title: d.title,
          description: d.description ?? d.desc ?? '',
          status: (d.status as MissionStatus) ?? 'new',
        }))
      }
    } else {
      console.warn('Missions non trouvées pour', category)
    }
  } catch (e) {
    console.error('Erreur loadMissions:', e)
  }
}

// Watch user for changes (F5 load)
import { watch } from 'vue'

onMounted(() => {
  const init = async () => {
    if (user.value) {
      await loadMissions()
      handleScrollQuery()
    }
  }
  init()
})

watch(user, async (newUser) => {
  if (newUser) {
    await loadMissions()
    handleScrollQuery()
  }
})

async function handleScrollQuery() {
  const q = route.query.missionId
  if (q) {
    const id = Number(q)
    const found = remoteMissions.value.find((m) => Number(m.id) === id)
    if (found) {
      const st = (found.status || 'new').toLowerCase()
      if (['en_cours', 'encours', 'in_progress', 'ongoing'].some((x) => st.includes(x)))
        activeTab.value = 0
      else if (['termine', 'terminee', 'done', 'completed'].some((x) => st.includes(x)))
        activeTab.value = 1
      else activeTab.value = 2

      await nextTick()
      scrollToMission(id)
    }
  }
}

function scrollToMission(id: number) {
  const container = containerRef.value || document.querySelector('.scrollable-area')
  const el = container
    ? (container.querySelector(`#mission-${id}`) as HTMLElement | null)
    : document.getElementById(`mission-${id}`)
  if (!el || !container) return

  // compute element position relative to container
  const containerRect = container.getBoundingClientRect()
  const elRect = el.getBoundingClientRect()
  const offsetTop = elRect.top - containerRect.top + container.scrollTop

  const target = Math.max(0, offsetTop - HEADER_OFFSET / 2)
  container.scrollTo({ top: target, behavior: 'smooth' })
}

// --- Actions: move / restore missions ---
function moveToCompleted(mission: Mission) {
  updateMissionStatus(mission, 'termine')
}

function moveToInProgress(mission: Mission) {
  updateMissionStatus(mission, 'en_cours')
}

function moveToNew(mission: Mission) {
  updateMissionStatus(mission, 'new')
}

function restoreToInProgress(mission: Mission) {
  updateMissionStatus(mission, 'en_cours')
}

function updateMissionStatus(mission: Mission, newStatus: Mission['status']) {
  if (remoteMissions.value.length > 0) {
    const idx = remoteMissions.value.findIndex((x) => x.id === mission.id)
    if (idx !== -1 && remoteMissions.value[idx]) {
      // optimistically update local list
      remoteMissions.value[idx].status = newStatus
      // send update to backend, then refresh list and re-scroll to the mission if still present
      fetch(`${API_URL}/missions/${mission.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: newStatus,
          user_id: authStore.user?.id,
        }),
      })
        .then(async (r) => {
          if (!r.ok) throw new Error('PUT failed')
          // reload missions to keep in sync with server ordering
          await loadMissions()
          await nextTick()
        })
        .catch((e) => console.warn('PUT /missions/:id failed', e))
    }
  } else {
    // local fallback: remove from source arrays and push to target
    // remove wherever it exists
    ;(Object.values(sampleMissions) as Mission[][]).forEach((arr) => {
      const i = arr.findIndex((m) => m.id === mission.id)
      if (i !== -1) arr.splice(i, 1)
    })
    if (newStatus === 'en_cours') sampleMissions[0]?.unshift({ ...mission, status: newStatus })
    else if (newStatus === 'termine') sampleMissions[1]?.unshift({ ...mission, status: newStatus })
    else sampleMissions[2]?.unshift({ ...mission, status: newStatus })
  }
}

// Normalise et filtre selon l'onglet actif.
const missionsForActiveTab = computed(() => {
  // If backend returned missions, use them (filter by status)
  if (remoteMissions.value.length > 0) {
    const statusMatches = (s?: string, tab = activeTab.value) => {
      if (!s) return false
      const norm = s.toLowerCase()
      if (tab === 0)
        return ['en_cours', 'encours', 'in_progress', 'ongoing', 'open'].some((x) =>
          norm.includes(x),
        )
      if (tab === 1)
        return ['termine', 'terminee', 'done', 'completed'].some((x) => norm.includes(x))
      if (tab === 2) return ['new', 'nouveau', 'nouvelle', 'pending'].some((x) => norm.includes(x))
      return false
    }

    return remoteMissions.value.filter((m) => statusMatches(m.status))
  }

  // Fallback to local samples
  return sampleMissions[activeTab.value] || []
})

const goBack = () => router.push('/missions')
</script>

<template>
  <div class="dashboard-wrapper">
    <Header
      title="Missions"
      :subtitle="title"
      :showResumeBtn="true"
      resumeBtnLabel="Retour"
      @resumeLater="goBack"
    />

    <div class="scrollable-area">
      <div class="tabs">
        <button
          v-for="t in tabs"
          :key="t.id"
          :class="['tab-btn', { active: activeTab === t.id }]"
          @click="activeTab = t.id"
        >
          {{ t.label }}
        </button>
      </div>

      <div class="missions-list">
        <Card
          v-for="m in missionsForActiveTab"
          :key="m.id"
          :title="m.title"
          class="note-card"
          :id="`mission-${m.id}`"
        >
          <p>{{ m.description }}</p>
          <div class="card-actions">
            <button v-if="activeTab === 2" class="action-btn" @click="moveToInProgress(m)">
              Commencer
            </button>
            <button v-if="activeTab === 0" class="action-btn" @click="moveToCompleted(m)">
              Terminer
            </button>
            <button v-if="activeTab === 0" class="action-btn warn" @click="moveToNew(m)">
              Supprimer
            </button>
            <button v-if="activeTab === 1" class="action-btn" @click="restoreToInProgress(m)">
              Remettre en cours
            </button>
          </div>
        </Card>
        <div v-if="missionsForActiveTab.length === 0" class="empty-state">
          <span v-if="activeTab === 2"
            >Toutes les missions sont prises ou filtrées selon vos préférences.</span
          >
          <span v-else>Aucune mission ici.</span>
        </div>
      </div>
    </div>

    <button class="fab-settings" @click="openCategorySettings">⚙️</button>

    <div v-if="showPrefsModal" class="blur-overlay">
      <div class="onboarding-card">
        <h2>Réglages : {{ title }}</h2>
        <p class="intro-text">Ajustez vos préférences pour cette catégorie :</p>

        <div class="prefs-scroll">
          <div v-for="(label, key) in filteredPreferenceLabels" :key="key" class="pref-item">
            <label class="switch-container">
              <span>{{ label }}</span>
              <input type="checkbox" v-model="userPreferences[key as keyof DerivedPreferences]" />
              <span class="checkmark"></span>
            </label>
          </div>
          <div v-if="Object.keys(filteredPreferenceLabels).length === 0" class="empty-state-prefs">
            Aucun réglage spécifique pour cette catégorie.
          </div>
        </div>

        <button class="save-btn" @click="saveCategoryPreferences" :disabled="isSubmittingPrefs">
          {{ isSubmittingPrefs ? '...' : 'Enregistrer' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tabs {
  display: flex;
  gap: 8px;
  margin: 12px 0 18px;
  align-items: center;
}
.tab-btn {
  padding: 8px 12px;
  border-radius: 8px;
  border: none;
  background: #f0f0f0;
  cursor: pointer;
}
.tab-btn.active {
  background: #679436;
  color: white;
}
.missions-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.empty-state {
  color: #666;
  text-align: center;
  margin-top: 12px;
}
.card-actions {
  margin-top: 10px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.action-btn {
  background: #eee;
  border: none;
  padding: 6px 10px;
  border-radius: 8px;
  cursor: pointer;
}
.action-btn.warn {
  background: #ffecec;
  color: #c0392b;
  border: 1px solid #f5c6c6;
}

/* FAB */
.fab-settings {
  position: fixed;
  bottom: 90px;
  right: 20px;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background-color: #f0f0f0;
  border: 1px solid #ddd;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
  font-size: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 90;
  transition: transform 0.2s;
}
.fab-settings:active {
  transform: scale(0.95);
}

/* Modale */
.blur-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  //background: rgba(255, 255, 255, 0.8);
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
  flex-shrink: 0;
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
.empty-state-prefs {
  text-align: center;
  color: #999;
  font-style: italic;
  padding: 20px 0;
}
</style>
