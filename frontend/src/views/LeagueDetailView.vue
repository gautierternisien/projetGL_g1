<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Header from '@/components/AppHeader.vue'

const route = useRoute()
const router = useRouter()
const leagueId = route.params.id

// Interfaces
interface Member {
  id: number
  username: string
  missionsCompleted: number
}

interface League {
  id: string
  name: string
  endDate: string // ISO date string
  startDate: string // ISO date string
  isArchived: boolean
  members: Member[]
}

const league = ref<League | null>(null)

// Mock fetching logic
onMounted(() => {
  // In a real app, fetch from API using leagueId
  // TODO: Fetch league details from API
})

const sortedMembers = computed(() => {
  if (!league.value) return []
  // Sort by missionsCompleted descending
  return [...league.value.members].sort((a, b) => b.missionsCompleted - a.missionsCompleted)
})

const timeRemaining = computed(() => {
    if (!league.value || league.value.isArchived) return null

    // Calculate difference between now and endDate
    const end = new Date(league.value.endDate).getTime()
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

function inviteMember() {
  // TODO: Implement invitation logic via API
  console.log("Invitation feature to be implemented")
}

function leaveLeague() {
  // TODO: Implement leave logic via API
  if(confirm("Êtes-vous sûr de vouloir quitter cette ligue ?")) {
      // Call API then redirect
      // router.push({ name: 'CommunityLeagues' })
  }
}

</script>

<template>
  <div class="dashboard-wrapper">
    <Header
        :title="league?.isArchived ? 'Ligue archivée' : 'Détails de la ligue'"
        :showResumeBtn="true"
        resumeBtnLabel="Retour"
        @resumeLater="goBack"
    />

    <div v-if="league" class="scrollable-area content-container">

        <div class="league-header">
            <h2>{{ league.name }}</h2>
        </div>

        <div v-if="!league.isArchived" class="actions">
            <button class="action-btn invite" @click="inviteMember">Inviter un membre</button>
            <button class="action-btn leave" @click="leaveLeague">Quitter la ligue</button>
        </div>

        <div class="league-infos">
            <p v-if="!league.isArchived && timeRemaining" class="timer">
                Cette ligue se termine dans {{ timeRemaining }}
            </p>
            <p v-else class="timer">Terminée le {{ new Date(league.endDate).toLocaleDateString() }}</p>
        </div>

        <div class="ranking-section">
            <h3>Classement</h3>
            <div class="ranking-list">
                <div v-for="(member, index) in sortedMembers" :key="member.id" class="rank-item">
                    <div class="rank-pos">{{ index + 1 }}</div>
                    <div class="rank-info">
                        <div class="username">{{ member.username }}</div>
                        <div class="missions">{{ member.missionsCompleted }} missions</div>
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
