<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import { useLeaguesStore } from '@/stores/leagues'
import type { League } from '@/types/league'
import { useRoute, useRouter } from 'vue-router'
import { ref, computed, onMounted } from 'vue'

const route = useRoute()
const router = useRouter()
const store = useLeaguesStore()

const league = ref<League | undefined>(undefined)

onMounted(async () => {
  const id = Number(route.params.id)

  // Try to find in store first
  let l = store.getLeagueById(id)
  if (l) {
    league.value = l
  }

  // Also fetch fresh data (or if not invalid store)
  const fetched = await store.fetchLeague(id)
  if (fetched) {
     league.value = fetched
  } else if (!league.value) {
    // If not found in store AND fetch failed or returned nothing
    // router.replace('/communaute/ligues')
  }

})

function goBack() {
  router.push('/communaute/ligues')
}

// --- Actions ---
async function handleLeaveLeague() {
  if (league.value) {
    if (confirm('Voulez-vous vraiment quitter cette ligue ?')) {
      await store.leaveLeague(league.value.id)
      goBack()
    }
  }
}

async function handleInviteMember() {
  const username = prompt("Entrez le pseudo de l'ami à inviter :")
  if (username && league.value) {
    await store.inviteMember(league.value.id, username)
    alert('Invitation envoyée !')
  }
}

// --- Helpers ---
const sortedMembers = computed(() => {
  if (!league.value) return []
  return [...league.value.members].sort((a, b) => b.missionsCount - a.missionsCount)
})

function formatTimeRemaining(endDateStr: string): string {
  if (!endDateStr) return '?'
  const end = new Date(endDateStr)
  if (isNaN(end.getTime())) return 'Date invalide'

  const now = new Date()
  const diff = end.getTime() - now.getTime()

  if (diff <= 0) return 'Terminée'

  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
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
    <!-- Header with Back button -->
    <Header
      :title="league?.name || 'Chargement...'"
      :showResumeBtn="true"
      resumeBtnLabel="Retour"
      @resumeLater="goBack"
    />

    <div v-if="league" class="scrollable-area content-area">
      <!-- Info Card -->
      <div class="info-card" :class="{ archived: league.isArchived }">
        <div class="timer">
           <span class="icon">⏳</span>
           <span v-if="league.isArchived">Terminée le {{ new Date(league.endDate).toLocaleDateString() }}</span>
           <span v-else>Se termine dans {{ formatTimeRemaining(league.endDate) }}</span>
        </div>
        <div class="desc" v-if="league.description">{{ league.description }}</div>
      </div>

      <!-- Actions (Only for active leagues) -->
      <div v-if="!league.isArchived" class="actions-row">
        <button class="action-btn invite" @click="handleInviteMember">
          <span>✉️</span> Inviter un membre
        </button>
        <button class="action-btn leave" @click="handleLeaveLeague">
          <span>🚪</span> Quitter
        </button>
      </div>

      <!-- Leaderboard -->
      <div class="leaderboard-section">
        <h3>Classement</h3>
        <div class="leaderboard-list">
           <div v-for="(member, index) in sortedMembers" :key="member.id" class="leaderboard-item">
              <div class="rank-badge" :class="`rank-${index + 1}`">{{ index + 1 }}</div>
              <div class="member-info">
                 <div class="member-name">{{ member.username }}</div>
                 <div class="member-progress">
                   <div class="progress-bar-bg">
                      <div class="progress-bar-fill" :style="{ width: Math.min((member.missionsCount / 20) * 100, 100) + '%' }"></div>
                   </div>
                 </div>
              </div>
              <div class="member-score">
                 <span class="score-num">{{ member.missionsCount }}</span>
                 <span class="score-label">missions</span>
              </div>
           </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.content-area {
  padding: 20px;
}

.info-card {
  background: white;
  padding: 16px;
  border-radius: 16px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  border: 1px solid #eee;
}
.info-card.archived {
  background: #f0f0f0;
  opacity: 0.8;
}

.timer {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #666;
  margin-bottom: 4px;
}
.desc {
  font-size: 0.9rem;
  color: #444;
}

.actions-row {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}
.action-btn {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  cursor: pointer;
  transition: transform 0.1s;
}
.action-btn:active {
  transform: scale(0.98);
}
.action-btn.invite {
  background: #e0f5e9;
  color: #1f7a3a;
}
.action-btn.leave {
  background: #ffe5e5;
  color: #d32f2f;
}

.leaderboard-section h3 {
  margin-bottom: 12px;
  color: #1f2a2c;
  font-size: 1.1rem;
}

.leaderboard-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.leaderboard-item {
  background: white;
  padding: 12px 16px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.03);
  border: 1px solid #f0f0f0;
}

.rank-badge {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  background: #eee;
  color: #666;
  font-size: 0.9rem;
}
.rank-1 { background: #FFD700; color: #7a6600; } /* Gold */
.rank-2 { background: #C0C0C0; color: #555; }    /* Silver */
.rank-3 { background: #CD7F32; color: #643c16; } /* Bronze */

.member-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.member-name {
  font-weight: 600;
  color: #1f2a2c;
}

.member-score {
  text-align: right;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}
.score-num {
  font-weight: 700;
  font-size: 1.1rem;
  color: #679436;
}
.score-label {
  font-size: 0.7rem;
  color: #888;
}

/* Mini Progress Bar */
.progress-bar-bg {
  height: 4px;
  background: #eee;
  border-radius: 2px;
  overflow: hidden;
  width: 100%;
  max-width: 100px;
}
.progress-bar-fill {
  height: 100%;
  background: #679436;
  border-radius: 2px;
}
</style>
