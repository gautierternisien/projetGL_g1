<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import { useLeaguesStore } from '@/stores/leagues'
import type { League } from '@/types/league'
import { useRouter } from 'vue-router'
import { ref, onMounted } from 'vue'

const router = useRouter()
const store = useLeaguesStore()

onMounted(() => {
  store.fetchLeagues()
  store.fetchInvitations()
})

// --- Navigation / State ---
const goBack = () => router.push('/communaute')

const activeTab = ref(0) // 0: Active, 1: Invites, 2: Archived
// Note: User requested order: "Ligues en cours", "Invitations en attente", "Ligues archivées"
const tabs = [
  { id: 0, label: 'Ligues\nen cours' },
  { id: 1, label: 'Invitations\nen attente' },
  { id: 2, label: 'Ligues\narchivées' },
]

function openLeagueDetail(league: League) {
  router.push({ name: 'CommunityLeaguesDetail', params: { id: league.id } })
}

// --- Create League State ---
const isCreateOpen = ref(false)
const createForm = ref({
  name: '',
  startDate: '',
  endDate: '',
})

function openCreate() {
  const today = new Date().toISOString().split('T')[0] || ''
  createForm.value = {
    name: '',
    startDate: today,
    endDate: '', // User must pick
  }
  isCreateOpen.value = true
}

function closeCreate() {
  isCreateOpen.value = false
}

async function confirmCreate() {
  if (!createForm.value.name || !createForm.value.startDate || !createForm.value.endDate) return

  // Basic validation (example: max 1 year)
  const start = new Date(createForm.value.startDate)
  const end = new Date(createForm.value.endDate)
  const oneYear = 365 * 24 * 60 * 60 * 1000

  if (end.getTime() < start.getTime()) {
    alert('La date de fin doit être après la date de début.')
    return
  }
  if (end.getTime() - start.getTime() > oneYear) {
    alert('La durée maximale est de 1 an.')
    return
  }

  await store.createLeague({
    name: createForm.value.name,
    startDate: createForm.value.startDate,
    endDate: createForm.value.endDate
  })
  closeCreate()
  activeTab.value = 0 // Go to active leagues
}

// --- Invitations Actions ---
async function acceptInvite(id: number) {
  await store.joinLeague(id)
  activeTab.value = 0 // Go to active leagues to see it
}

async function rejectInvite(id: number) {
  await store.rejectInvitation(id)
}

// --- Helpers ---
function formatTimeRemaining(endDateStr: string): string {
  if (!endDateStr) return '?'

  const end = new Date(endDateStr)
  if (isNaN(end.getTime())) return 'Date invalide'

  const now = new Date()
  const diff = end.getTime() - now.getTime()

  if (diff <= 0) return 'Terminée'

  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  if (days > 365) {
     return 'Plus d\'un an'
  }
  if (days > 30) {
    const months = Math.floor(days / 30)
    return `${months} mois`
  }
  if (days > 0) return `${days} jours`

  const hours = Math.floor(diff / (1000 * 60 * 60))
  if (hours > 0) return `${hours} heures`

  return 'Moins d\'une heure'
}
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Ligues" :showResumeBtn="true" resumeBtnLabel="Retour" @resumeLater="goBack" />

    <div class="scrollable-area">

      <!-- TABS -->
      <div class="tabs">
        <button
          v-for="t in tabs"
          :key="t.id"
          :class="['tab-btn', { active: activeTab === t.id }]"
          @click="activeTab = t.id"
        >
          {{ t.label }}
          <span v-if="t.id === 1 && store.pendingInvitations.length > 0" class="badge">
            {{ store.pendingInvitations.length }}
          </span>
        </button>
      </div>

      <!-- TAB 0: Active Leagues -->
      <div v-if="activeTab === 0">
        <div class="top-actions">
          <button class="add-btn" @click="openCreate">➕ Créer une ligue</button>
        </div>

        <div v-if="store.activeLeagues.length" class="leagues-list">
          <div
            v-for="league in store.activeLeagues"
            :key="league.id"
            class="league-card"
            @click="openLeagueDetail(league)"
          >
            <div class="league-header">
              <span class="league-icon">🏆</span>
              <span class="league-name">{{ league.name }}</span>
            </div>
            <div class="league-timer">
              Cette ligue se termine dans {{ formatTimeRemaining(league.endDate) }}
            </div>
          </div>
        </div>
        <div v-else class="placeholder-content">
          <span class="emoji">🏆</span>
          <p>Rejoignez ou créez une ligue !</p>
        </div>
      </div>

      <!-- TAB 1: Invitations -->
      <div v-if="activeTab === 1">
        <div v-if="store.pendingInvitations.length" class="requests-list">
          <div v-for="inv in store.pendingInvitations" :key="inv.id" class="request-item incoming">
             <div class="avatar">📩</div>
             <div class="request-info">
               <div class="name">{{ inv.league.name }}</div>
               <div class="status">Invitation à rejoindre</div>
             </div>
             <div class="request-actions">
               <button class="reject-btn" @click="rejectInvite(inv.id)">Refuser</button>
               <button class="accept-btn" @click="acceptInvite(inv.id)">Rejoindre</button>
             </div>
          </div>
        </div>
        <div v-else class="placeholder-content">
          <span class="emoji">📭</span>
          <p>Aucune invitation en attente</p>
        </div>
      </div>

      <!-- TAB 2: Archived Leagues -->
      <div v-if="activeTab === 2">
        <div v-if="store.archivedLeagues.length" class="leagues-list">
          <div
            v-for="league in store.archivedLeagues"
            :key="league.id"
            class="league-card archived"
            @click="openLeagueDetail(league)"
          >
            <div class="league-header">
              <span class="league-icon">📜</span>
              <span class="league-name">{{ league.name }}</span>
            </div>
            <div class="league-timer">Terminée le {{ new Date(league.endDate).toLocaleDateString() }}</div>
          </div>
        </div>
        <div v-else class="placeholder-content">
          <span class="emoji">🕸️</span>
          <p>Aucune ligue archivée</p>
        </div>
      </div>

    </div>

    <!-- MODAL: CREATE LEAGUE -->
    <div v-if="isCreateOpen" class="fullscreen-overlay">
       <div class="modal-content">
         <div class="modal-header">
            <h3>Créer une ligue</h3>
            <button class="close-icon-btn" @click="closeCreate">✕</button>
         </div>

         <div class="form-group">
            <label>Nom de la ligue</label>
            <input v-model="createForm.name" type="text" placeholder="Ex: Challenge Vélo" />
         </div>

         <div class="form-row">
            <div class="form-group">
              <label>Début</label>
              <input v-model="createForm.startDate" type="date" />
            </div>
            <div class="form-group">
              <label>Fin</label>
              <input v-model="createForm.endDate" type="date" />
            </div>
         </div>
         <p class="hint">La durée maximale est de 1 an.</p>

         <button class="action-btn-primary" @click="confirmCreate">Créer</button>
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
  padding: 8px 6px;
  border-radius: 8px;
  border: none;
  background: #f0f0f0;
  cursor: pointer;
  flex: 1;
  height: 60px; /* matched FriendsView */
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  white-space: pre-line;
  font-family: 'Instrument Sans', sans-serif;
  line-height: 1.2;
  position: relative;
  font-size: 0.9rem;
}

.tab-btn.active {
  background: #679436;
  color: white;
}

.badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background-color: #ff4d4d;
  color: white;
  min-width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid white;
  font-size: 0.7rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Lists */
.leagues-list, .requests-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.league-card {
  background: #f7f9f5;
  border: 1px solid #dbe5d3;
  padding: 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: transform 0.1s;
}
.league-card:active {
  transform: scale(0.98);
}
.league-card.archived {
  background: #f0f0f0;
  border-color: #ddd;
  opacity: 0.8;
}

.league-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.league-icon {
  font-size: 1.5rem;
}
.league-name {
  font-weight: 600;
  font-size: 1.1rem;
  color: #1f2a2c;
}
.league-timer {
  font-size: 0.85rem;
  color: #666;
  margin-left: 36px; /* align with text */
}

/* Request items (copied from FriendsView slightly adapted) */
.request-item {
  display: flex;
  align-items: center;
  background: #f5f5f5;
  padding: 12px;
  border-radius: 12px;
  border-left: 4px solid #679436;
  gap: 10px;
}
.avatar {
  font-size: 1.5rem;
}
.request-info {
  flex: 1;
}
.request-info .name {
  font-weight: 600;
}
.request-info .status {
  font-size: 0.8rem;
  color: #666;
}
.request-actions {
  display: flex;
  gap: 6px;
}
.accept-btn, .reject-btn {
  border: none;
  padding: 6px 10px;
  border-radius: 6px;
  cursor: pointer;
  color: white;
  font-size: 0.8rem;
}
.accept-btn { background: #679436; }
.reject-btn { background: #f44336; }

/* Placeholder */
.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  color: #666;
  gap: 10px;
}
.emoji { font-size: 3rem; }

/* Top Actions */
.top-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}
.add-btn {
  background: #e0f5e9;
  border: 1px solid #bfe8cd;
  color: #1f7a3a;
  border-radius: 10px;
  padding: 8px 12px;
  cursor: pointer;
  font-weight: 500;
}

/* Modal Styles */
.fullscreen-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 24px;
  width: 90%;
  max-width: 500px;
  position: relative;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.close-icon-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 1rem;
}

.form-row {
  display: flex;
  gap: 12px;
}

.hint {
  font-size: 0.9rem;
  color: #888;
  margin-top: -8px;
  margin-bottom: 16px;
}

.action-btn-primary {
  background: #679436;
  color: white;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  width: 100%;
  transition: background 0.3s;
}
.action-btn-primary:hover {
  background: #5a7e2d;
}
</style>
