<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Header from '@/components/AppHeader.vue'
import { useLeaguesStore } from '@/stores/leagues'
import { useFriendsStore } from '@/stores/friends'

const route = useRoute()
const router = useRouter()
const store = useLeaguesStore()
const friendsStore = useFriendsStore()
const leagueId = Number(route.params.id)

const showInviteModal = ref(false)
const showLeaveModal = ref(false)
const inviteSearchQuery = ref('')
const inviteErrorMessage = ref('')
const leaveErrorMessage = ref('')
const selectedFriendIds = ref<number[]>([])

onMounted(async () => {
    try {
        await store.fetchLeagueDetail(leagueId)
        await friendsStore.fetchFriends()
    } catch {
        // silent fail or redirect?
    }
})

const league = computed(() => store.currentLeague)

const sortedMembers = computed(() => {
  if (!league.value) return []
  // Sort by missionsCompleted descending
  return [...league.value.members].sort((a, b) => (b.missions_completed || 0) - (a.missions_completed || 0))
})

const timeRemaining = computed(() => {
    if (!league.value || league.value.is_archived) return null

    const start = new Date(league.value.start_date).getTime()
    const end = new Date(league.value.end_date).getTime()
    const now = new Date().getTime()

    // Not started yet
    if (now < start) {
        const diff = start - now
        const days = Math.floor(diff / (1000 * 60 * 60 * 24))
        if (days > 0) return `Commence dans ${days} jours`
        return "Commence bientôt"
    }

    const diff = end - now

    if (diff <= 0) return "Terminée"

    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    if (days > 0) return `${days} jours`

    const hours = Math.floor(diff / (1000 * 60 * 60))
    return `${hours} heures`
})

const filteredFriends = computed(() => {
    const q = inviteSearchQuery.value.toLowerCase()
    // Exclude members already in league
    const currentMemberIds = new Set(league.value?.members.map(m => m.user_id) || [])

    return friendsStore.friends
        .filter(f => !currentMemberIds.has(f.id)) // Filter out existing members
        .filter(f => f.username.toLowerCase().includes(q))
})

function goBack() {
  router.back()
}

function openInviteModal() {
    showInviteModal.value = true
    inviteErrorMessage.value = ''
    selectedFriendIds.value = []
}

function closeInviteModal() {
    showInviteModal.value = false
    inviteSearchQuery.value = ''
    inviteErrorMessage.value = ''
    selectedFriendIds.value = []
}

function openLeaveModal() {
    showLeaveModal.value = true
    leaveErrorMessage.value = ''
}

function closeLeaveModal() {
    showLeaveModal.value = false
    leaveErrorMessage.value = ''
}

async function confirmLeaveLeague() {
    leaveErrorMessage.value = ''
    try {
        await store.leaveLeague(leagueId)
        router.push({ name: 'CommunityLeagues' })
    } catch {
        leaveErrorMessage.value = "Impossible de quitter la ligue."
    }
}

function toggleSelection(friendId: number) {
    if (selectedFriendIds.value.includes(friendId)) {
        selectedFriendIds.value = selectedFriendIds.value.filter(id => id !== friendId)
    } else {
        selectedFriendIds.value.push(friendId)
    }
}

async function sendInvitations() {
    if (selectedFriendIds.value.length === 0) return

    inviteErrorMessage.value = ''
    let successCount = 0
    let failCount = 0
    const successfulIds: number[] = []

    // Send invites in parallel
    await Promise.all(selectedFriendIds.value.map(async (id) => {
        try {
            await store.inviteUser(leagueId, id)
            successCount++
            successfulIds.push(id)
        } catch {
            failCount++
        }
    }))

    // Remove successful invites from selection
    selectedFriendIds.value = selectedFriendIds.value.filter(id => !successfulIds.includes(id))

    if (failCount > 0) {
         inviteErrorMessage.value = `${successCount} invitation(s) envoyée(s). ${failCount} échec(s) (déjà membre ?).`
    } else {
        closeInviteModal()
    }
}

</script>

<template>
  <div class="dashboard-wrapper">
    <Header
        :title="league?.is_archived ? 'Ligue archivée' : 'Détails de la ligue'"
        :showResumeBtn="true"
        resumeBtnLabel="Retour"
        @resumeLater="goBack"
    />

    <div v-if="league" class="scrollable-area content-container" :class="{ 'blurred-content': showInviteModal || showLeaveModal }">

        <div class="league-header">
            <h2>{{ league.name }}</h2>
        </div>

        <div v-if="!league.is_archived" class="actions">
            <button class="action-btn invite" @click="openInviteModal">Inviter un membre</button>
            <button class="action-btn leave" @click="openLeaveModal">Quitter la ligue</button>
        </div>

        <div class="league-infos">
            <p v-if="!league.is_archived && timeRemaining" class="timer">
                {{ timeRemaining.includes('Commence') ? timeRemaining : 'Se termine dans ' + timeRemaining }}
            </p>
            <p v-else class="timer">Terminée le {{ new Date(league.end_date).toLocaleDateString() }}</p>
        </div>

        <div class="ranking-section">
            <h3>Classement</h3>
            <div class="ranking-list">
                <div v-for="(member, index) in sortedMembers" :key="member.id" class="rank-item">
                    <div class="rank-pos">{{ index + 1 }}</div>
                    <div class="rank-info">
                        <div class="username">{{ member.username }}</div>
                        <div class="missions">{{ member.missions_completed }} mission{{ (member.missions_completed || 0) > 1 ? 's' : '' }}</div>
                    </div>
                </div>
            </div>
        </div>

    </div>
    <div v-else class="loading">
        Chargement...
    </div>

    <!-- Invite Modal -->
    <div v-if="showInviteModal" class="blur-overlay">
      <div class="confirm-box">
        <h3>Inviter un ami</h3>

        <input
            type="text"
            v-model="inviteSearchQuery"
            placeholder="Rechercher un ami..."
            class="search-input"
        />

        <div class="friends-list-modal">
            <div
                v-for="friend in filteredFriends"
                :key="friend.id"
                class="friend-modal-item"
            >
                <div class="friend-name">{{ friend.username }}</div>
                <button
                    class="add-friend-btn"
                    :class="{ 'selected': selectedFriendIds.includes(friend.id) }"
                    @click="toggleSelection(friend.id)"
                >
                    {{ selectedFriendIds.includes(friend.id) ? 'Désélectionner' : 'Sélectionner' }}
                </button>
            </div>

            <div v-if="filteredFriends.length === 0" class="empty-msg">
                Aucun ami trouvé.
            </div>
        </div>

        <div v-if="inviteErrorMessage" class="error-message">
            {{ inviteErrorMessage }}
        </div>

        <div class="confirm-actions">
          <button @click="closeInviteModal" class="cancel-btn">Annuler</button>
          <button @click="sendInvitations" class="confirm-btn">Envoyer les invitations</button>
        </div>
      </div>
    </div>

    <!-- Leave Modal -->
    <div v-if="showLeaveModal" class="blur-overlay">
      <div class="confirm-box leave-confirm">
        <h3>Quitter la ligue</h3>
        <p>Êtes-vous sûr de vouloir quitter cette ligue ?</p>

        <div v-if="leaveErrorMessage" class="error-message">
            {{ leaveErrorMessage }}
        </div>

        <div class="confirm-actions">
          <button @click="closeLeaveModal" class="cancel-btn">Annuler</button>
          <button @click="confirmLeaveLeague" class="confirm-btn">Oui, quitter</button>
        </div>
      </div>
    </div>

  </div>
</template>

<style scoped>


.league-header {
    text-align: center;
}

.league-infos {
    text-align: center;
    margin-top: 12px;
}

.league-header h2 {
    font-size: 1.5rem;
    margin-bottom: 8px;
}

.timer {
    color: #666;
    font-style: italic;
}

.actions {
    display: flex;
    gap: 12px;
    justify-content: center;
}

.action-btn {
    padding: 10px 16px;
    border-radius: 8px;
    border: none;
    font-weight: 500;
    cursor: pointer;
    font-family: inherit;
}

.action-btn.invite {
    background-color: #e0f5e9;
    color: #1f7a3a;
    border: 1px solid #bfe8cd;
}

.action-btn.leave {
    background-color: #f4e5e5;
    color: #b23b3b;
    border: 1px solid #e7caca;
}

.ranking-section h3 {
    margin-bottom: 12px;
    font-size: 1.2rem;
}

.ranking-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.rank-item {
    display: flex;
    align-items: center;
    background: #f7f9f5;
    color: #1f2a2c;
    border: 1px solid #dbe5d3;
    padding: 12px;
    border-radius: 12px;
    gap: 16px;
}

.rank-pos {
    font-size: 1.2rem;
    font-weight: bold;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #e3eddd;
    border-radius: 50%;
    color: #2f3b2f;
}

.rank-info {
    flex: 1;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.username {
    font-weight: 600;
}

.missions {
    color: #666;
    font-size: 0.9em;
}

.loading {
    padding: 40px;
    text-align: center;
    color: #666;
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
  padding: 2rem;
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

.search-input {
    width: 100%;
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 1rem;
    font-family: inherit;
}

.friends-list-modal {
    max-height: 250px;
    overflow-y: auto;
}

.friend-modal-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px;
    border-radius: 8px;
    background: #f9f9f9;
    margin-bottom: 8px;
    border: 1px solid #eee;
}

.friend-name {
    font-weight: 500;
    color: #333;
}

.add-friend-btn {
    padding: 6px 12px;
    border-radius: 8px;
    border: none;
    background: #e0f5e9;
    color: #1f7a3a;
    border: 1px solid #bfe8cd;
    cursor: pointer;
    font-size: 0.9rem;
    font-weight: 600;
}

.add-friend-btn.selected {
    background: #f4e5e5;
    color: #b23b3b;
    border-color: #e7caca;
}

.empty-msg {
    text-align: center;
    color: #999;
    font-size: 0.9rem;
    padding: 10px;
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

.error-message {
    color: #b23b3b;
    background: #f8d7da;
    padding: 10px;
    border-radius: 8px;
    margin-top: 8px;
    font-size: 0.9rem;
    border: 1px solid #f5c6cb;
}

.leave-confirm {
  /* Specific styles for leave confirmation box */
}

.confirm-btn {
  background-color: #679436;
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  flex: 1;
  font-size: 1rem;
}
</style>
