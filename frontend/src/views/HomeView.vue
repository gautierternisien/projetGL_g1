<script setup lang="ts">
import Card from '@/components/Card.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import Header from '@/components/Header.vue'
import { ref } from 'vue'
import { useProgressStore } from '@/stores/progress'

const store = useProgressStore()

//Valeur fixe temporaire avant lien avec le back
const co2Total = ref(1.2)
const sectors = ref([
  { name: 'Transport', pct: 35, color: '#D32F2F' },
  { name: 'Alimentation', pct: 28, color: '#FBC02D' },
  { name: 'Logement', pct: 20, color: '#7CB342' },
  { name: 'Numérique', pct: 12, color: '#8BC34A' },
  { name: 'Autres', pct: 5, color: '#558B2F' },
])

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
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Tableau de bord" />

    <div class="scrollable-area">
      <Card title="Empreinte ce mois">
        <div class="split-content">
          <div class="info-side">
            <span class="big-number">{{ co2Total }}</span>
            <span class="unit-text">Tonnes CO₂</span>
          </div>
          <div class="image-side">
            <span class="emoji-img">🥀</span>
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
              <div class="card-content">
                <span class="card-icon">🎯</span>
                <span class="card-title">{{ mission.title }}</span>
              </div>
            </div>
          </div>
        </Card>
      </RouterLink>

      <RouterLink to="/evenements" class="unstyled-link">
        <Card title="Évènements communautaires " :hasArrow="true">
          <div class="carousel-container">
            <div v-for="event in events" :key="event.id" class="mission-card">
              <div class="card-content">
                <span class="card-icon">👥</span>
                <span class="card-title">{{ event.title }}</span>
              </div>
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

/* --- HEADER FIXE --- */
/*
.top-header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background-color: #6d8b46;
  z-index: 1000;
  border-bottom-left-radius: 20px;
  border-bottom-right-radius: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  height: 100px;
  padding-top: env(safe-area-inset-top);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  color: white;
  box-sizing: border-box;
  width: 100%;
}

.header-content h1 {
  margin: 0;
  font-size: 1.8rem;
}

.user-avatar {
  font-size: 1.5rem;
  background: rgba(255, 255, 255, 0.2);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(5px);
}
*/

/* --- ZONE DE SCROLL --- */
.scrollable-area {
  padding-top: 100px;
  padding-left: 20px;
  padding-right: 20px;
  overflow-y: auto;
}

/* --- MISE EN PAGE CONTENU (GAUCHE / DROITE) --- */
.split-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-side {
  flex: 1;
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
  color: #d32f2f;
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
