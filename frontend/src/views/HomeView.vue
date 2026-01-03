<script setup lang="ts">
import Card from '@/components/AppCard.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import Header from '@/components/AppHeader.vue'
import { ref, onMounted, computed, onActivated, watch } from 'vue'
import type { Mission } from '@/types/mission'
import { useProgressStore } from '@/stores/progress'
import { useAuthStore } from '@/stores/auth'
import { API_URL, USER_ID } from '@/config'

const store = useProgressStore()
const authStore = useAuthStore()
const isConnected = computed(() => authStore.isConnected)

interface CommunityEvent {
  id: number
  title: string
}

// Dictionnaire pour afficher de jolis noms (au lieu de 'transport', 'alimentation'...)
const CATEGORY_LABELS: Record<string, string> = {
  transport: 'Transport',
  alimentation: 'Alimentation',
  logement: 'Logement',
  consommation: 'Achats & Divers',
  recyclage: 'Déchets',
  numerique: 'Numérique',
  loisirs: 'Loisirs',
  quotidien: 'Quotidien',
}

// Couleurs fixes par catégorie
const CATEGORY_COLORS: Record<string, string> = {
  transport: '#5D4037', // Brown
  alimentation: '#D84315', // Deep Orange
  logement: '#9f8a50', // Yellow
  consommation: '#8E24AA', // Purple
  recyclage: '#388E3C', // Green
  numerique: '#1976D2', // Blue
  loisirs: '#0097A7', // Cyan
  quotidien: '#455A64', // Blue Grey
}

// --- ÉTATS ---
const userScore = ref(0)
const averageScore = ref(0)
const scoreColor = ref('#333') // Couleur par défaut
const scoreEmoji = ref('🥀') // Emoji par défaut
const scoreComment = ref('Chargement...')

const sectors = ref<{ name: string; pct: number; color: string }[]>([])

// Dashboard missions: load actual missions from backend (show title + category)
const displayMissions = ref<{ mission: Mission; category: string }[]>([])

async function loadDashboardMissions() {
  try {
    const keys = Object.keys(CATEGORY_LABELS)
    const userIdParam = authStore.user ? `?user_id=${authStore.user.username}` : ''
    const results = await Promise.all(
      keys.map((k) =>
        fetch(`${API_URL}/missions/${k}${userIdParam}`, { cache: 'no-store' })
          .then((r) => (r.ok ? r.json() : []))
          .catch(() => []),
      ),
    )

    const rows: { mission: Mission; category: string }[] = []
    for (let i = 0; i < keys.length; i++) {
      const k = keys[i]
      const data = results[i]
      if (Array.isArray(data)) {
        for (const d of data) {
          const status = (d.status ?? d.desc ?? 'new').toString().toLowerCase()
          if (
            status.includes('en_cours') ||
            status.includes('encours') ||
            status.includes('in_progress') ||
            status.includes('ongoing')
          ) {
            rows.push({
              mission: {
                id: Number(d.id),
                title: String(d.title || ''),
                description: d.description ?? d.desc ?? '',
                status,
              },
              category: k as string,
            })
          }
          if (rows.length >= 6) break
        }
      }
      if (rows.length >= 6) break
    }

    displayMissions.value = rows
  } catch (e) {
    console.error('Erreur loadDashboardMissions', e)
  }
}

const events = ref<CommunityEvent[]>([])

// --- COMPUTED POUR LE GRAPHIQUE ---
const donutStyle = computed(() => {
  if (sectors.value.length === 0) {
    return { background: '#e0e0e0' }
  }

  let current = 0
  const segments = sectors.value.map((s) => {
    const start = current
    const end = current + s.pct
    current = end
    return `${s.color} ${start}% ${end}%`
  })

  return {
    background: `conic-gradient(${segments.join(', ')})`,
  }
})

// --- LOGIQUE DE CALCUL ---
const calculateStatus = (score: number, avg: number) => {
  // On définit une marge de tolérance de 15% autour de la moyenne
  const lowThreshold = avg * 0.85
  const highThreshold = avg * 1.15

  if (score < lowThreshold) {
    // Cas VERT : Bien en dessous de la moyenne
    scoreColor.value = '#4CAF50' // Vert
    scoreEmoji.value = '🌹'
    scoreComment.value = 'Excellent !'
  } else if (score > highThreshold) {
    // Cas ROUGE : Bien au-dessus de la moyenne
    scoreColor.value = '#D32F2F' // Rouge
    scoreEmoji.value = '🪾' //
    scoreComment.value = 'Attention'
  } else {
    // Cas ORANGE : Dans la moyenne
    scoreColor.value = '#FB8C00' // Orange
    scoreEmoji.value = '🥀️'
    scoreComment.value = 'Dans la moyenne'
  }
}

// 2. Traitement des secteurs pour le graphique
const processSectors = (details: Record<string, number>, total: number) => {
  // A. On transforme l'objet { transport: 2000, ... } en tableau
  const rawSectors = Object.entries(details).map(([key, value]) => {
    return {
      key: key, // On garde la clé pour la couleur
      name: CATEGORY_LABELS[key] || key, // On met le joli nom ou la clé par défaut
      rawScore: value,
      pct: total > 0 ? Math.round((value / total) * 100) : 0,
    }
  })

  // B. On filtre les catégories à 0% pour ne pas polluer l'affichage (optionnel)
  const activeSectors = rawSectors.filter((s) => s.pct > 0)

  // C. On TRIE du plus grand au plus petit pourcentage
  activeSectors.sort((a, b) => b.pct - a.pct)

  // D. On applique la couleur selon la catégorie
  sectors.value = activeSectors.map((sector) => {
    const color = CATEGORY_COLORS[sector.key] || '#333'

    return {
      name: sector.name,
      pct: sector.pct,
      color: String(color),
    }
  })
}

// --- CHARGEMENT DES DONNÉES ---
onMounted(async () => {
  // Ensure user is loaded if connected
  if (isConnected.value && !authStore.user) {
    await authStore.fetchUser()
  }

  // 1. On lance le chargement des progressions en arrière-plan
  if (isConnected.value && authStore.user) {
    store.fetchAllProgress(authStore.user.username)
  }

  try {
    let url = `${API_URL}/global-stats`
    if (isConnected.value) {
      const userId = authStore.user ? authStore.user.username : USER_ID
      url = `${API_URL}/carbon-score/${userId}`
    }

    const response = await fetch(url)

    if (response.ok) {
      const data = await response.json()

      // Mise à jour des scores globaux
      userScore.value = data.global_score
      // Si connecté, on compare à la moyenne nationale (déjà dans data)
      // Si pas connecté, on affiche la moyenne globale comme score principal
      averageScore.value = data.average_national_score || 0
      calculateStatus(userScore.value, averageScore.value)

      // Mise à jour dynamique du graphique
      processSectors(data.details_by_category, data.global_score)
    }
  } catch (error) {
    console.error('Erreur chargement:', error)
    scoreComment.value = 'Erreur'
  }

  // load dashboard missions (real ones) only if connected
  if (isConnected.value) {
    await loadDashboardMissions()
  }
})

// Refresh missions when navigating back to this view (if cached)
onActivated(async () => {
  if (isConnected.value) {
    await loadDashboardMissions()
    if (authStore.user) {
      store.fetchAllProgress(authStore.user.username)
    }
  }
})

// Also refresh when the window regains focus
window.addEventListener('focus', async () => {
  if (isConnected.value) {
    await loadDashboardMissions()
    if (authStore.user) {
      store.fetchAllProgress(authStore.user.username)
    }
  }
})

// Watch for user changes to reload data (e.g. after login or page refresh)
watch(
  () => authStore.user,
  async (newUser) => {
    if (newUser) {
      store.fetchAllProgress(newUser.username)
      await loadDashboardMissions()
    }
  },
)
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Tableau de bord" />

    <div class="scrollable-area">
      <Card :title="isConnected ? 'Mon empreinte carbone' : 'Empreinte moyenne des utilisateurs'">
        <div class="split-content">
          <div class="info-side">
            <span class="big-number" :style="{ color: scoreColor }">{{
              (userScore / 1000).toFixed(2)
            }}</span>
            <span class="unit-text">Tonnes CO₂</span>
          </div>
          <div class="image-side">
            <span class="emoji-img">{{ scoreEmoji }}</span>
          </div>
        </div>
      </Card>

      <Card :title="isConnected ? 'Mes émissions par secteur' : 'Émissions moyennes par secteur'">
        <div class="split-content">
          <div class="info-side">
            <ul class="legend-list">
              <li v-for="sector in sectors" :key="sector.name">
                <span class="dot" :style="{ backgroundColor: sector.color }"></span>
                <span :style="{ color: sector.color }">
                  {{ sector.name }} ({{ sector.pct }}%)
                </span>
              </li>
            </ul>
          </div>
          <div class="image-side">
            <!-- Remplacement de l'emoji par le graphique Donut CSS -->
            <div class="donut-chart" :style="donutStyle"></div>
          </div>
        </div>
      </Card>

      <RouterLink to="/questionnaires" class="unstyled-link">
        <Card title="Questionnaires" :hasArrow="true">
          <ProgressBar v-if="isConnected" :value="store.globalAverage"></ProgressBar>
          <div v-else class="lock-placeholder">🔒</div>
        </Card>
      </RouterLink>

      <RouterLink to="/missions" class="unstyled-link">
        <Card title="Missions en cours" :hasArrow="true">
          <div v-if="isConnected" class="carousel-container">
            <div v-for="item in displayMissions" :key="item.mission.id" class="mission-card">
              <RouterLink
                :to="`/missions/${item.category}?missionId=${item.mission.id}`"
                class="unstyled-link inner-mission-link"
              >
                <div class="card-content">
                  <span class="card-icon">🎯</span>
                  <div class="card-texts">
                    <span class="card-title">{{ item.mission.title }}</span>
                    <span class="card-subtitle">{{ CATEGORY_LABELS[item.category] }}</span>
                  </div>
                </div>
              </RouterLink>
            </div>
            <div v-if="displayMissions.length === 0" class="mission-card empty">
              Aucune mission en cours
            </div>
          </div>
          <div v-else class="lock-placeholder">🔒</div>
        </Card>
      </RouterLink>

      <RouterLink to="/communaute" class="unstyled-link">
        <Card title="Évènements communautaires " :hasArrow="true">
          <div v-if="isConnected" class="carousel-container">
            <div v-for="event in events" :key="event.id" class="mission-card">
              <RouterLink :to="'/communaute/' + event.id">
                <div class="card-content">
                  <span class="card-icon">👥</span>
                  <span class="card-title">{{ event.title }}</span>
                </div>
              </RouterLink>
            </div>
            <div v-if="events.length === 0" class="mission-card empty">Aucun évènement récent</div>
          </div>
          <div v-else class="lock-placeholder">🔒</div>
        </Card>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
/* --- LAYOUT GLOBAL --- */
/* .dashboard-wrapper est dans global.css */

/* --- ZONE DE SCROLL --- */
/* Géré dans global.css (.scrollable-area) */

/* --- MISE EN PAGE CONTENU (GAUCHE / DROITE) --- */
.split-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-side {
  flex: 1;
  display: flex;
  flex-direction: column; /* Pour empiler les infos */
  justify-content: center;
}

.image-side {
  flex-shrink: 0;
  margin-left: 15px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.emoji-img {
  font-size: 3.5rem;
}

/* --- GRAPHIQUE DONUT (Custom CSS car v-pie n'existe pas) --- */
.donut-chart {
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  /* Le background est géré dynamiquement via :style */
}

/* Le trou du donut */
.donut-chart::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60%; /* Épaisseur du donut */
  height: 60%;
  background-color: #f5f5f5; /* Couleur de fond de la carte */
  border-radius: 50%;
}

/* --- STYLE SPÉCIFIQUE EMPREINTE --- */
.big-number {
  font-size: 2.2rem;
  font-weight: 800;
}
.unit-text {
  display: block;
  font-weight: 600;
  color: #333;
}

/* --- STYLE SPÉCIFIQUE LISTE --- */
.legend-list {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 0.8rem;
  font-weight: 600;
}
.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 6px;
}

/* --- CARROUSEL --- */
.carousel-container {
  display: flex;
  gap: 12px;
  overflow-x: auto;

  /* MODIFICATION : On ajoute du padding tout autour pour que l'ombre ne soit pas coupée */
  padding: 10px 10px 20px 10px;
  /* (Haut Droite Bas Gauche) - On met un peu plus en bas pour l'ombre portée */

  /* On compense le padding pour que le scroll commence bien au bord visuel si besoin */
  margin: -10px;

  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  touch-action: pan-x;
  overscroll-behavior-x: contain;
  scroll-behavior: smooth;
  width: 100%;
}

/* Masquer la barre de scroll du carrousel (Optionnel mais joli) */
.carousel-container::-webkit-scrollbar {
  height: 8px;
}
.carousel-container {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.mission-card {
  /* Dimensions réduites pour voir les cartes adjacentes */
  width: 230px;
  height: 110px;

  /* Apparence : Fond blanc + Ombre */
  background-color: white;
  border-radius: 16px;
  border: 1px solid #f0f0f0; /* Bordure très subtile */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); /* L'effet "pop" */

  /* Positionnement */
  position: relative; /* Indispensable pour placer les flèches */
  display: flex;
  align-items: center;
  justify-content: center;

  /* Comportement scroll : centré pour voir avant/après */
  flex-shrink: 0;
  scroll-snap-align: center;
  transition: transform 0.2s ease;
}

/* Effet au clic/toucher (optionnel) */
.mission-card:active {
  transform: scale(0.98);
}

/* Contenu central (Icône + Texte) */
.card-content {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px; /* Espace entre icône et textes */
  justify-content: flex-start;
  padding: 6px 8px;
}

.card-icon {
  font-size: 1.8rem;
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-texts {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.card-title {
  font-size: 0.95rem;
  color: #333;
  font-weight: 600;
  text-align: left;
}

.card-subtitle {
  font-size: 0.8rem;
  color: #679436; /* app green */
  font-weight: 600;
}

.unstyled-link {
  text-decoration: none;
  color: inherit;
  display: block;
  cursor: pointer;
}

.lock-placeholder {
  text-align: center;
  font-size: 1.5rem;
  color: #999;
  padding: 10px;
}
</style>
