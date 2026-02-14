<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import Card from '@/components/AppCard.vue'
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { type Trophy } from '@/stores/trophies'

const router = useRouter()
const authStore = useAuthStore()
const API_URL = 'http://localhost:8000'

function goBack() {
  router.back()
}

// Gestion des onglets : 0 = En cours, 1 = Obtenus, 2 = À commencer
const activeTab = ref(0)

const tabs = [
  { id: 0, label: 'En cours' },
  { id: 1, label: 'Obtenus' },
  { id: 2, label: 'À commencer' },
]

interface MedalsSummary {
  'Bronze': number;
  'Argent': number;
  'Or': number;
  'Trophée': number;
}

const inProgressTrophies = ref<Trophy[]>([])
const obtainedTrophies = ref<Trophy[]>([])
const notStartedTrophies = ref<Trophy[]>([])
const medalsSummary = ref<MedalsSummary>({ 'Bronze': 0, 'Argent': 0, 'Or': 0, 'Trophée': 0 })
const loading = ref(true)

async function loadTrophies() {
  if (!authStore.isConnected || !authStore.token) {
    loading.value = false
    return
  }

  try {
    const headers = {
      'Authorization': `Bearer ${authStore.token}`
    }

    // Charger les trophées en cours et à commencer
    const inProgressRes = await fetch(`${API_URL}/trophies/in-progress`, { headers })
    if (inProgressRes.ok) {
      const allInProgress = await inProgressRes.json()
      // Séparer les trophées avec progression (en cours) et sans progression (à commencer)
      inProgressTrophies.value = allInProgress.filter((t: Trophy) => (t.progress || 0) > 0)
      notStartedTrophies.value = allInProgress.filter((t: Trophy) => (t.progress || 0) === 0)
    }

    // Charger les trophées obtenus
    const obtainedRes = await fetch(`${API_URL}/trophies/obtained`, { headers })
    if (obtainedRes.ok) {
      const data = await obtainedRes.json()
      console.log('Données reçues de /trophies/obtained:', data)
      obtainedTrophies.value = data.trophies || []
      medalsSummary.value = data.summary || { 'Bronze': 0, 'Argent': 0, 'Or': 0, 'Trophée': 0 }
      console.log('Trophées obtenus:', obtainedTrophies.value)
      console.log('Résumé médailles:', medalsSummary.value)
    } else {
      console.error('Erreur lors du chargement des trophées obtenus:', obtainedRes.status)
    }
  } catch (error) {
    console.error('Erreur lors du chargement des trophées:', error)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  if (!authStore.isConnected) {
    router.push('/login')
    return
  }
  // Charger les trophées pour l'affichage
  await loadTrophies()
})

function getTrophyLevel(trophy: Trophy): number {
  const progress = trophy.progress || 0
  const finalValue = trophy.requirement_value || 5
  const milestones = trophy.milestones || []
  
  // Si le trophée final est obtenu
  if (progress >= finalValue) {
    return 1 // Trophée (priorité la plus haute)
  }
  
  // Sinon, trouver la médaille la plus haute obtenue
  const sortedMilestones = [...milestones].sort((a, b) => b.value - a.value)
  for (const milestone of sortedMilestones) {
    if (progress >= milestone.value) {
      if (milestone.label === 'Or') return 2
      if (milestone.label === 'Argent') return 3
      if (milestone.label === 'Bronze') return 4
    }
  }
  
  // Aucun niveau atteint
  return 5
}

const trophiesForActiveTab = computed(() => {
  let trophies = []
  if (activeTab.value === 0) {
    trophies = [...inProgressTrophies.value]
  } else if (activeTab.value === 1) {
    trophies = [...obtainedTrophies.value]
  } else {
    trophies = [...notStartedTrophies.value]
  }
  
  // Trier par niveau : Trophée (1) → Or (2) → Argent (3) → Bronze (4)
  // Pour "À commencer", on garde l'ordre par défaut (level 5)
  return trophies.sort((a, b) => getTrophyLevel(a) - getTrophyLevel(b))
})

function formatDate(isoDate: string | undefined): string {
  if (!isoDate) return ''
  const date = new Date(isoDate)
  return date.toLocaleDateString('fr-FR', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  })
}

function getNextMilestone(progress: number, milestones: { value: number; label: string; icon: string }[], finalValue: number): { value: number; label: string } | null {
  // Chercher le prochain palier non atteint
  for (const milestone of milestones) {
    if (progress < milestone.value) {
      return { value: milestone.value, label: milestone.label }
    }
  }
  // Si tous les paliers sont atteints, le prochain est le trophée final
  if (progress < finalValue) {
    return { value: finalValue, label: 'Trophée' }
  }
  return null
}

function getNextMilestoneIcon(progress: number, milestones: { value: number; label: string; icon: string }[], finalIcon: string): string {
  // Chercher la prochaine icône non atteinte
  for (const milestone of milestones) {
    if (progress < milestone.value) {
      return milestone.icon
    }
  }
  // Si tous les paliers sont atteints, retourner l'icône du trophée final
  return finalIcon
}

function getLastObtainedMilestoneIcon(progress: number, milestones: { value: number; label: string; icon: string }[], finalValue: number, finalIcon: string): string | null {
  // Si le trophée final est obtenu, retourner son icône
  if (progress >= finalValue) {
    return finalIcon
  }
  
  // Sinon, trouver la médaille la plus haute obtenue (tri décroissant)
  const sortedMilestones = [...milestones].sort((a, b) => b.value - a.value)
  for (const milestone of sortedMilestones) {
    if (progress >= milestone.value) {
      return milestone.icon
    }
  }
  return null
}

function getLastObtainedMilestone(progress: number, milestones: { value: number; label: string; icon: string }[], finalValue: number): { value: number; label: string; icon: string } | null {
  // Si le trophée final est obtenu
  if (progress >= finalValue) {
    return { value: finalValue, label: 'Trophée', icon: '🏆' }
  }
  
  // Sinon, trouver la médaille la plus haute obtenue (tri décroissant)
  const sortedMilestones = [...milestones].sort((a, b) => b.value - a.value)
  for (const milestone of sortedMilestones) {
    if (progress >= milestone.value) {
      return milestone
    }
  }
  return null
}

function getDescription(progress: number, milestones: { value: number; label: string; icon: string }[], finalValue: number, requirementType: string = 'login_count', isInProgress: boolean = false): string {
  if (isInProgress) {
    // Pour les trophées en cours, afficher le prochain objectif
    const next = getNextMilestone(progress, milestones, finalValue)
    if (next) {
      if (requirementType === 'mission_count') {
        return `Terminez au moins ${next.value} missions`
      } else {
        return `Connectez-vous au moins ${next.value} fois`
      }
    }
    return "Objectif atteint"
  } else {
    // Pour les trophées obtenus, afficher l'objectif atteint
    const obtained = getLastObtainedMilestone(progress, milestones, finalValue)
    if (obtained) {
      if (requirementType === 'mission_count') {
        return `Terminez au moins ${obtained.value} missions`
      } else {
        return `Connectez-vous au moins ${obtained.value} fois`
      }
    }
    return "Trophée obtenu"
  }
}

</script>

<template>
  <div class="dashboard-wrapper">
    <Header
      title="Trophées"
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
      
      <div v-if="loading" class="loading">Chargement...</div>
      
      <!-- Résumé des médailles pour l'onglet "Récompenses obtenues" - toujours affiché -->
      <div v-if="!loading && activeTab === 1" class="medals-summary">
        <div class="medal-item">
          <span class="medal-icon">🏆</span>
          <span class="medal-label">Trophée</span>
          <span class="medal-count">x{{ medalsSummary['Trophée'] }}</span>
        </div>
        <div class="medal-item">
          <span class="medal-icon">🥇</span>
          <span class="medal-label">Or</span>
          <span class="medal-count">x{{ medalsSummary['Or'] }}</span>
        </div>
        <div class="medal-item">
          <span class="medal-icon">🥈</span>
          <span class="medal-label">Argent</span>
          <span class="medal-count">x{{ medalsSummary['Argent'] }}</span>
        </div>
        <div class="medal-item">
          <span class="medal-icon">🥉</span>
          <span class="medal-label">Bronze</span>
          <span class="medal-count">x{{ medalsSummary['Bronze'] }}</span>
        </div>
      </div>
      
      <template v-if="!loading && trophiesForActiveTab.length > 0">
        <div class="trophies-list">
          <Card
            v-for="trophy in trophiesForActiveTab"
            :key="trophy.id"
            :title="trophy.title"
            class="trophy-card"
          >
            <div class="trophy-content">
              <div class="trophy-icon" :class="{ 'trophy-icon-dimmed': activeTab === 0, 'trophy-icon-locked': activeTab === 2 }">
                {{ activeTab === 1 ? getLastObtainedMilestoneIcon(trophy.progress || 0, trophy.milestones || [], trophy.requirement_value || 5, trophy.icon) : getNextMilestoneIcon(trophy.progress || 0, trophy.milestones || [], trophy.icon) }}
              </div>
              <div class="trophy-info">
                <p class="trophy-description">
                  {{ getDescription(trophy.progress || 0, trophy.milestones || [], trophy.requirement_value || 5, trophy.requirement_type || 'login_count', activeTab !== 0) }}
                </p>
                
                <!-- En cours : afficher la progression -->
                <div v-if="activeTab === 0" class="trophy-progress">
                  <!-- Prochain objectif -->
                  <div v-if="getNextMilestone(trophy.progress || 0, trophy.milestones || [], trophy.requirement_value || 60)" class="next-milestone">
                    <div class="progress-text">
                      Prochain : {{ getNextMilestone(trophy.progress || 0, trophy.milestones || [], trophy.requirement_value || 60)?.label }}
                      ({{ trophy.progress }} / {{ getNextMilestone(trophy.progress || 0, trophy.milestones || [], trophy.requirement_value || 60)?.value }})
                    </div>
                    <div class="progress-bar">
                      <div 
                        class="progress-fill" 
                        :style="{ 
                          width: `${(trophy.progress! / (getNextMilestone(trophy.progress || 0, trophy.milestones || [], trophy.requirement_value || 60)?.value || 1)) * 100}%` 
                        }"
                      ></div>
                    </div>
                  </div>
                </div>
                
                <!-- Obtenus : afficher la date de la dernière médaille obtenue -->
                <div v-else-if="activeTab === 1" class="trophy-obtained">
                  <span class="obtained-date">
                    {{ getLastObtainedMilestone(trophy.progress || 0, trophy.milestones || [], trophy.requirement_value || 5)?.label }} obtenue le {{ formatDate(trophy.last_milestone_date) }}
                  </span>
                </div>
                
                <!-- À commencer : afficher un message d'encouragement -->
                <div v-else-if="activeTab === 2" class="trophy-not-started">
                  <span class="not-started-hint">
                    Commencez dès maintenant !
                  </span>
                </div>
              </div>
            </div>
          </Card>
        </div>
      </template>
      
      <div v-if="!loading && trophiesForActiveTab.length === 0" class="empty-state">
        <p v-if="activeTab === 0">Aucun trophée en cours. Commencez une nouvelle récompense !</p>
        <p v-else-if="activeTab === 1">
          Aucune récompense obtenue pour le moment.<br>
          <small style="color: #999; margin-top: 8px; display: block;">
            Venez régulièrement pour gagner des médailles !
          </small>
        </p>
        <p v-else>Toutes les récompenses ont été commencées ! 🎉</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tabs {
  display: flex;
  gap: 8px;
  margin: 12px 0 18px;
  justify-content: flex-start;
  align-items: center;
}

.tab-btn {
  padding: 8px 12px;
  border-radius: 8px;
  border: none;
  background: #f0f0f0;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.tab-btn.active {
  background: #679436;
  color: white;
}

.tab-btn:hover {
  opacity: 0.8;
}

.loading {
  text-align: center;
  color: #666;
  margin-top: 24px;
}

.trophies-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trophy-card {
  transition: transform 0.2s;
}

.trophy-content {
  display: flex;
  gap: 16px;
  align-items: center;
}

.trophy-icon {
  font-size: 48px;
  flex-shrink: 0;
}

.trophy-icon.trophy-icon-dimmed {
  opacity: 0.5;
}

.trophy-icon.trophy-icon-locked {
  opacity: 0.3;
  filter: grayscale(100%);
}

.trophy-info {
  flex: 1;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

.trophy-description {
  color: #666;
  margin: 0 0 12px 0;
  font-size: 14px;
}

.trophy-progress {
  margin-top: 8px;
}

.next-milestone {
  margin-top: 8px;
}

.progress-text {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #679436;
  transition: width 0.3s;
  border-radius: 4px;
}

.trophy-obtained {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}

.obtained-date {
  color: #679436;
  font-weight: 500;
  font-size: 14px;
}

.trophy-not-started {
  display: flex;
  flex-direction: column;
  margin-top: 8px;
}

.not-started-hint {
  color: #999;
  font-style: italic;
  font-size: 13px;
}

.empty-state {
  color: #666;
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
}

.medals-summary {
  display: flex;
  justify-content: space-around;
  background: #f9f9f9;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  border: 1px solid #e0e0e0;
}

.medal-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.medal-icon {
  font-size: 28px;
}

.medal-label {
  font-size: 12px;
  color: #666;
}

.medal-count {
  font-size: 16px;
  font-weight: bold;
  color: #333;
}
</style>
