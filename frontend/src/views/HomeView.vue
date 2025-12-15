<script setup lang="ts">
import Card from '@/components/Card.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import Header from '@/components/Header.vue'
import { ref, onMounted } from 'vue'
import { useProgressStore } from '@/stores/progress'

const store = useProgressStore()

// --- CONFIGURATION API ---
const API_URL = 'http://localhost:8000'
const USER_ID = 'user123'

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

// Palette de dégradé : Du Rouge (Impact Fort) au Vert (Impact Faible)
const GRADIENT_PALETTE = [
  '#D32F2F', // Rouge foncé (1er)
  '#E64A19',
  '#F57C00', // Orange
  '#FBC02D', // Jaune
  '#AFB42B',
  '#7CB342', // Vert clair
  '#388E3C', // Vert foncé
  '#2E7D32', // Vert très foncé (8ème)
]

// --- ÉTATS ---
const userScore = ref(0)
const averageScore = ref(0)
const scoreColor = ref('#333') // Couleur par défaut
const scoreEmoji = ref('🥀') // Emoji par défaut
const scoreComment = ref('Chargement...')

const sectors = ref<{ name: string; pct: number; color: string }[]>([])

const missions = ref([
  { id: 1, title: 'Mission 1' },
  { id: 2, title: 'Mission 2' },
  { id: 3, title: 'Mission 3' },
  { id: 4, title: 'Mission 4' },
])

const events = ref([
  { id: 1, title: 'Maxine à pris le vélo au lieu de la voiture' },
  { id: 2, title: 'Maxine à pris le vélo au lieu de la voiture' },
  { id: 3, title: 'Maxine à pris le vélo au lieu de la voiture' },
  { id: 4, title: 'Maxine à pris le vélo au lieu de la voiture' },
])

// --- LOGIQUE DE CALCUL ---
const calculateStatus = (score: number, avg: number) => {
  // On définit une marge de tolérance de 50% autour de la moyenne
  const lowThreshold = avg * 0.5
  const highThreshold = avg * 1.5

  if (score < lowThreshold) {
    // Cas VERT : Bien en dessous de la moyenne
    scoreColor.value = '#4CAF50' // Vert
    scoreEmoji.value = '🌹'
    scoreComment.value = 'Excellent !'
  } else if (score > highThreshold) {
    // Cas ROUGE : Bien au-dessus de la moyenne
    scoreColor.value = '#D32F2F' // Rouge
    scoreEmoji.value = '💀' //
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
      name: CATEGORY_LABELS[key] || key, // On met le joli nom ou la clé par défaut
      rawScore: value,
      pct: total > 0 ? Math.round((value / total) * 100) : 0,
    }
  })

  // B. On filtre les catégories à 0% pour ne pas polluer l'affichage (optionnel)
  const activeSectors = rawSectors.filter((s) => s.pct > 0)

  // C. On TRIE du plus grand au plus petit pourcentage
  activeSectors.sort((a, b) => b.pct - a.pct)

  // D. On applique la couleur selon la position (1er = Rouge, Dernier = Vert)
  sectors.value = activeSectors.map((sector, index) => {
    // On prend la couleur dans la liste, ou la dernière si on dépasse
    const color = GRADIENT_PALETTE[index] || GRADIENT_PALETTE[GRADIENT_PALETTE.length - 1]

    return {
      name: sector.name,
      pct: sector.pct,
      color: color,
    }
  })
}

// --- CHARGEMENT DES DONNÉES ---
onMounted(async () => {
  try {
    const response = await fetch(`${API_URL}/carbon-score/${USER_ID}`)

    if (response.ok) {
      const data = await response.json()

      // Mise à jour des scores globaux
      userScore.value = data.global_score
      averageScore.value = data.average_national_score
      calculateStatus(userScore.value, averageScore.value)

      // Mise à jour dynamique du graphique
      processSectors(data.details_by_category, data.global_score)
    }
  } catch (error) {
    console.error('Erreur chargement:', error)
    scoreComment.value = 'Erreur'
  }
})
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Tableau de bord" />

    <div class="scrollable-area">
      <Card title="Empreinte carbone">
        <div class="split-content">
          <div class="info-side">
            <span class="big-number" :style="{ color: scoreColor }">{{ userScore / 1000 }}</span>
            <span class="unit-text">Tonnes CO₂</span>
          </div>
          <div class="image-side">
            <span class="emoji-img">{{ scoreEmoji }}</span>
          </div>
        </div>
      </Card>

      <Card title="Émissions par secteur">
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
            <span class="emoji-img">🍩</span>
          </div>
        </div>
      </Card>

      <RouterLink to="/questionnaires" class="unstyled-link">
        <Card title="Questionnaires" :hasArrow="true">
          <ProgressBar :value="store.globalAverage"></ProgressBar>
        </Card>
      </RouterLink>

      <RouterLink to="/missions" class="unstyled-link">
        <Card title="Missions en cours" :hasArrow="true">
          <div class="carousel-container">
            <div v-for="mission in missions" :key="mission.id" class="mission-card">
              <RouterLink :to="'/missions/' + mission.id">
                <div class="card-content">
                  <span class="card-icon">🎯</span>
                  <span class="card-title">{{ mission.title }}</span>
                </div>
              </RouterLink>
            </div>
          </div>
        </Card>
      </RouterLink>

      <RouterLink to="/communaute" class="unstyled-link">
        <Card title="Évènements communautaires " :hasArrow="true">
          <div class="carousel-container">
            <div v-for="event in events" :key="event.id" class="mission-card">
              <RouterLink :to="'/communaute/' + event.id">
                <div class="card-content">
                  <span class="card-icon">👥</span>
                  <span class="card-title">{{ event.title }}</span>
                </div>
              </RouterLink>
            </div>
          </div>
        </Card>
      </RouterLink>

      <div style="height: 100px"></div>
    </div>
  </div>
</template>

<style scoped>
/* --- LAYOUT GLOBAL --- */
.dashboard-wrapper {
  background-color: white;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: 'Instrument Sans', sans-serif;
  position: relative;
}

/* --- ZONE DE SCROLL --- */
.scrollable-area {
  flex: 1;
  padding-top: 100px;
  padding-left: 20px;
  padding-right: 20px;
  overflow-y: auto;

  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}

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
  padding-bottom: 5px;

  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
}

/* Masquer la barre de scroll du carrousel (Optionnel mais joli) */
.carousel-container::-webkit-scrollbar {
  display: none;
}
.carousel-container {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.mission-card {
  /* Dimensions */
  width: 290px;
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

  /* Comportement scroll */
  flex-shrink: 0;
  scroll-snap-align: start;
  transition: transform 0.2s ease;
}

/* Effet au clic/toucher (optionnel) */
.mission-card:active {
  transform: scale(0.98);
}

/* Contenu central (Icône + Texte) */
.card-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px; /* Espace entre icône et texte */
}

.card-icon {
  font-size: 1.8rem;
}

.card-title {
  font-size: 0.9rem;
  color: #333;
  font-weight: 500;
  text-align: center;
}

.unstyled-link {
  text-decoration: none;
  color: inherit;
  display: block;
  cursor: pointer;
}
</style>
