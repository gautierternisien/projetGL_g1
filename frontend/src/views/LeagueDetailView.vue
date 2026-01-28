<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Header from '@/components/AppHeader.vue'
import { useLeaguesStore } from '@/stores/leagues'

const route = useRoute()
const router = useRouter()
const store = useLeaguesStore()
const leagueId = Number(route.params.id)

onMounted(async () => {
    try {
        await store.fetchLeagueDetail(leagueId)
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

    // Calculate difference between now and endDate
    const end = new Date(league.value.end_date).getTime()
    const now = new Date().getTime()
    const diff = end - now

    if (diff <= 0) return "Terminée"

    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    if (days > 0) return `${days} jours`

    const hours = Math.floor(diff / (1000 * 60 * 60))
    return `${hours} heures`
})

function goBack() {
  router.back()
}

async function inviteMember() {
  // Temporary interaction
  const id = prompt("Entrez l'ID de l'utilisateur à inviter :")
  if (id) {
    try {
        await store.inviteUser(leagueId, parseInt(id))
        alert("Invitation envoyée !")
    } catch {
        alert("Erreur lors de l'invitation")
    }
  }
}

async function leaveLeague() {
  if(confirm("Êtes-vous sûr de vouloir quitter cette ligue ?")) {
      await store.leaveLeague(leagueId)
      router.push({ name: 'CommunityLeagues' })
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

    <div v-if="league" class="scrollable-area content-container">

        <div class="league-header">
            <h2>{{ league.name }}</h2>
        </div>

        <div v-if="!league.is_archived" class="actions">
            <button class="action-btn invite" @click="inviteMember">Inviter un membre</button>
            <button class="action-btn leave" @click="leaveLeague">Quitter la ligue</button>
        </div>

        <div class="league-infos">
            <p v-if="!league.is_archived && timeRemaining" class="timer">
                Cette ligue se termine dans {{ timeRemaining }}
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
                        <div class="missions">{{ member.missions_completed }} missions</div>
                    </div>
                </div>
            </div>
        </div>

    </div>
    <div v-else class="loading">
        Chargement...
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
</style>
