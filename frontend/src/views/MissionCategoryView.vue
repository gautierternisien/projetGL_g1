<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import Card from '@/components/AppCard.vue'
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { Mission, MissionStatus } from '@/types/mission'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const category = route.params.category as string

onMounted(() => {
  if (!authStore.isConnected) {
    router.push('/login')
    return
  }
  loadMissions()
})

// ref to the scrolling container so we scroll relative to it
const containerRef = ref<HTMLElement | null>(null)
const HEADER_OFFSET = 100 // matches padding-top used in layout

const CATEGORY_DISPLAY_NAMES: Record<string, string> = {
  transport: 'Transport & Mobilité',
  alimentation: 'Alimentation',
  logement: 'Logement & Énergie',
  numerique: 'Numérique',
  loisirs: 'Loisirs & Voyages',
  quotidien: 'Habitudes Quotidiennes',
  recyclage: 'Déchets & Recyclage',
  consommation: 'Consommation & Achats',
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
const API_URL = 'http://localhost:8000'
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
  try {
    const userIdParam = authStore.user ? `?user_id=${authStore.user.username}` : ''
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

onMounted(() => {
  loadMissions().then(async () => {
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
  })
})

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
          user_id: authStore.user?.username,
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
        <div v-if="missionsForActiveTab.length === 0" class="empty-state">Aucune mission ici.</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-wrapper {
  background: white;
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.scrollable-area {
  padding: 100px 20px;
  overflow-y: auto;
  flex: 1;
}
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
</style>
