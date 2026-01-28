<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import { useRouter } from 'vue-router'
import { ref, computed, onMounted } from 'vue'
import { useLeaguesStore } from '@/stores/leagues'

const router = useRouter()
const store = useLeaguesStore()
const activeTab = ref(0) // 0: En cours, 2: Invitations, 1: Archives

const tabs = [
  { id: 0, label: "Ligues\nen cours" },
  { id: 2, label: "Invitations\nen attente" },
  { id: 1, label: "Ligues\narchivées" },
]

onMounted(async () => {
    try {
        await store.fetchActiveLeagues()
        await store.fetchInvites()
        await store.fetchArchivedLeagues()
    } catch {
        // silent fail
    }
})

// Sort logic: Most recent creation first
const sortedActiveLeagues = computed(() => {
    return [...store.activeLeagues].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
})

const sortedArchivedLeagues = computed(() => {
    return [...store.archivedLeagues].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
})

function getTimeRemaining(endDateStr: string) {
    const end = new Date(endDateStr).getTime()
    const now = new Date().getTime()
    const diff = end - now
    if (diff <= 0) return "Terminée"
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    if (days > 0) return `${days}j`
    const hours = Math.floor(diff / (1000 * 60 * 60))
    return `${hours}h`
}

function goBack() {
    router.push('/communaute')
}

function goToDetail(id: number) {
    router.push({ name: 'CommunityLeagueDetail', params: { id: id.toString() } })
}

// Invite actions
async function acceptInvite(id: number) {
    await store.acceptInvite(id)
}

async function rejectInvite(id: number) {
    await store.rejectInvite(id)
}


// Modal logic
const showCreateModal = ref(false)
const newLeagueName = ref('')
const newStartDate = ref('')
const newEndDate = ref('')
const isBlurred = ref(false)

// Computed for form validation
const isFormValid = computed(() => {
    if (!newStartDate.value || !newEndDate.value) return false
    const start = new Date(newStartDate.value).getTime()
    const end = new Date(newEndDate.value).getTime()
    const oneYearLater = new Date(start + 365*24*60*60*1000).getTime()
    return end > start && end <= oneYearLater
})

// Date constraints
const today = new Date()
const todayStr = today.toISOString().split('T')[0]
const minEndDate = computed(() => {
    if (!newStartDate.value) return ''
    const minDate = new Date(newStartDate.value)
    minDate.setDate(minDate.getDate() + 1)
    return minDate.toISOString().split('T')[0]
})
const maxEndDate = computed(() => {
    if (!newStartDate.value) return ''
    const maxDate = new Date(newStartDate.value)
    maxDate.setFullYear(maxDate.getFullYear() + 1)
    return maxDate.toISOString().split('T')[0]
})

function openCreateModal() {
    isBlurred.value = true
    showCreateModal.value = true
}

function closeCreateModal() {
    isBlurred.value = false
    showCreateModal.value = false
    // Reset form
    newLeagueName.value = ''
    newStartDate.value = ''
    newEndDate.value = ''
}

async function confirmCreateLeague() {
    if (!isFormValid.value) return
    try {
        await store.createLeague({
            name: newLeagueName.value,
            start_date: newStartDate.value,
            end_date: newEndDate.value
        })
        closeCreateModal()
    } catch (e) {
        console.error(e)
        alert("Erreur lors de la création")
    }
}

</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Ligues" :showResumeBtn="true" resumeBtnLabel="Retour" @resumeLater="goBack" />
    <div class="scrollable-area" :class="{ 'blurred-content': isBlurred }">

      <!-- Tabs -->
      <div class="tabs">
        <button
          v-for="t in tabs"
          :key="t.id"
          :class="['tab-btn', { active: activeTab === t.id }]"
          @click="activeTab = t.id"
        >
          {{ t.label }}
          <span v-if="t.id === 2 && store.invitations.length > 0" class="badge">
            {{ store.invitations.length }}
          </span>
        </button>
      </div>

      <!-- Tab 0: Ligues en cours -->
      <div v-if="activeTab === 0">
        <div class="top-actions">
          <button class="add-btn" @click="openCreateModal">➕ Créer une ligue</button>
        </div>

        <div v-if="sortedActiveLeagues.length" class="leagues-list">
            <div
                v-for="league in sortedActiveLeagues"
                :key="league.id"
                class="league-card"
                @click="goToDetail(league.id)"
            >
                <div class="league-icon">🏆</div>
                <div class="league-info">
                    <div class="league-name">{{ league.name }}</div>
                    <div class="league-meta">
                         <span class="members-count">{{ league.members_count }} membres</span>
                         <span class="separator">•</span>
                         <span class="timer">Se termine dans {{ getTimeRemaining(league.end_date) }}</span>
                    </div>
                </div>
                <div class="arrow">›</div>
            </div>
        </div>
        <div v-else class="placeholder-content">
             <span class="emoji">🏆</span>
             <p>Vous ne participez à aucune ligue pour le moment.</p>
        </div>
      </div>

      <!-- Tab 2: Invitations -->
      <div v-if="activeTab === 2">
          <div v-if="store.invitations.length" class="requests-list">
            <div v-for="invite in store.invitations" :key="invite.id" class="league-invite-card">
                <div class="invite-info">
                    <div class="league-name">{{ invite.league_name }}</div>
                    <div class="inviter">Invité par {{ invite.inviter_name }}</div>
                </div>
                <div class="invite-actions">
                    <button class="reject-btn" @click="rejectInvite(invite.id)">Refuser</button>
                    <button class="accept-btn" @click="acceptInvite(invite.id)">Rejoindre</button>
                </div>
            </div>
          </div>
          <div v-else class="placeholder-content">
             <span class="emoji">📭</span>
             <p>Aucune invitation en attente.</p>
          </div>
      </div>

      <!-- Tab 1: Archives -->
      <div v-if="activeTab === 1">
        <div v-if="sortedArchivedLeagues.length" class="leagues-list">
            <div
                v-for="league in sortedArchivedLeagues"
                :key="league.id"
                class="league-card archived"
                @click="goToDetail(league.id)"
            >
                <div class="league-icon gray">🏆</div>
                <div class="league-info">
                    <div class="league-name">{{ league.name }}</div>
                    <div class="league-meta">
                        Terminée le {{ new Date(league.end_date).toLocaleDateString() }}
                    </div>
                </div>
                <div class="arrow">›</div>
            </div>
        </div>
        <div v-else class="placeholder-content">
            <span class="emoji">📦</span>
            <p>Aucune ligue archivée.</p>
        </div>
      </div>

    </div>

    <!-- Create League Modal -->
    <div v-if="showCreateModal" class="blur-overlay">
      <div class="confirm-box create-modal">
        <h3>Créer une ligue</h3>

        <div class="form-group">
            <label>Nom de la ligue</label>
            <input v-model="newLeagueName" type="text" placeholder="Ex: Ligue d'été" />
        </div>

        <div class="form-row">
            <div class="form-group">
                <label>Début</label>
                <input v-model="newStartDate" type="date" :min="todayStr" />
            </div>
            <div class="form-group">
                <label>Fin</label>
                <input v-model="newEndDate" type="date" :min="minEndDate" :max="maxEndDate" />
            </div>
        </div>

        <p v-if="newStartDate && newEndDate && !isFormValid" class="error-msg">
            La durée est max 1 an et la fin doit être après le début.
        </p>

        <div class="confirm-actions">
          <button @click="closeCreateModal" class="cancel-btn">Annuler</button>
          <button @click="confirmCreateLeague" class="confirm-btn" :disabled="!isFormValid">Créer</button>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>
/* Modal styles */
.blurred-content {
  filter: blur(4px);
  pointer-events: none;
  user-select: none;
}

.blur-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
}

.confirm-box {
  background: white;
  padding: 1.5rem;
  border-radius: 16px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 85%;
  max-width: 320px;
  animation: popIn 0.2s ease-out;
  font-family: 'Instrument Sans', sans-serif;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.confirm-box h3 {
    margin: 0;
    font-size: 1.2rem;
}

.form-group {
    display: flex;
    flex-direction: column;
    text-align: left;
    gap: 6px;
}

.form-group label {
    font-size: 0.9rem;
    font-weight: 600;
    color: #333;
}

.form-group input {
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 1rem;
    font-family: inherit;
}

.form-row {
    display: flex;
    gap: 12px;
}
.form-row .form-group {
    flex: 1;
}

.error-msg {
    color: #d32f2f;
    font-size: 0.8rem;
    margin: 0;
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

.confirm-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 8px;
}

.cancel-btn {
  background-color: #f0f0f0;
  color: #333;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  flex: 1;
  font-size: 1rem;
}

.confirm-btn {
  background-color: #679436; /* Using the green theme */
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  flex: 1;
  font-size: 1rem;
}

.confirm-btn:disabled {
    background-color: #ccc;
    cursor: not-allowed;
}

/* Reusing Friend View styles logic */
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
  width: 100%;
  height: 60px;
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
    background-color: #679436;
    color: #fff;
}

.badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background-color: #ff4d4d;
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  border: 2px solid white;
}

.top-actions {
    display: flex;
    justify-content: flex-end; /* Match FriendsView right alignment */
    margin-bottom: 20px;
}

.add-btn {
    background: #e0f5e9;
    border: 1px solid #bfe8cd;
    color: #1f7a3a;
    padding: 8px 12px;
    border-radius: 10px;
    font-weight: 600;
    cursor: pointer;
    font-size: 1rem;
    display: flex;
    align-items: center;
    gap: 8px;
}

.leagues-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.league-card {
    display: flex;
    align-items: center;
    background: #f7f9f5;
    color: #1f2a2c;
    padding: 16px;
    border-radius: 12px;
    border: 1px solid #dbe5d3;
    cursor: pointer;
    transition: background 0.2s;
}

.league-card:active {
    background: #e3eddd;
}

.league-icon {
    font-size: 1.5rem;
    margin-right: 16px;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: #e3eddd;
    display: flex;
    align-items: center;
    justify-content: center;
}

.league-icon.gray {
    filter: grayscale(100%);
    opacity: 0.6;
    background: #eee;
}

.league-info {
    flex: 1;
}

.league-name {
    font-weight: 600;
    font-size: 1.05rem;
    margin-bottom: 4px;
}

.league-meta {
    font-size: 0.85rem;
    color: #666;
    display: flex;
    align-items: center;
    gap: 6px;
}

.timer {
    color: #d32f2f; /* Red-ish for urgency */
    font-weight: 500;
}

.arrow {
    font-size: 1.5rem;
    color: #999;
    margin-left: 8px;
}

.requests-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.league-invite-card {
    background: #f5f5f5;
    border: none;
    border-left: 4px solid #679436; /* Incoming green type */
    padding: 16px;
    border-radius: 12px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.inviter {
    color: #666;
    font-size: 0.9rem;
}

.invite-actions {
    display: flex;
    gap: 8px;
}

.reject-btn, .accept-btn {
    flex: 1;
    padding: 8px 12px;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    cursor: pointer;
}

.reject-btn {
    background: #f44336;
    color: #fff;
}

.accept-btn {
    background: #679436;
    color: #fff;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
  color: #666;
  gap: 20px;
}

.emoji {
  font-size: 4rem;
}
</style>
