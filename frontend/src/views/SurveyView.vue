<script setup lang="ts">
import Card from '@/components/Card.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import Header from '@/components/Header.vue'
import { useProgressStore } from '@/stores/progress'

const store = useProgressStore()
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Questionnaires" />

    <div class="scrollable-area">
      <RouterLink to="/questionnaires/transport">
        <Card title="Transport & Mobilité" :has-arrow="true">
          <div class="image-center">
            <span class="emoji-img">🚗</span>
          </div>
          <ProgressBar :value="store.getCategoryScore('transport')"></ProgressBar>
        </Card>
      </RouterLink>

      <RouterLink to="/questionnaires/logement">
        <Card title="Logement & Énergie" :has-arrow="true">
          <div class="image-center">
            <span class="emoji-img">🏠</span>
          </div>
          <ProgressBar :value="store.getCategoryScore('logement')"></ProgressBar>
        </Card>
      </RouterLink>

      <RouterLink to="/questionnaires/alimentation">
        <Card title="Alimentation" :has-arrow="true">
          <div class="image-center">
            <span class="emoji-img">🍽️</span>
          </div>
          <ProgressBar :value="store.getCategoryScore('alimentation')"></ProgressBar>
        </Card>
      </RouterLink>

      <RouterLink to="/questionnaires/consommation">
        <Card title="Consommation" :has-arrow="true">
          <div class="image-center">
            <span class="emoji-img">📦️</span>
          </div>
          <ProgressBar :value="store.getCategoryScore('consommation')"></ProgressBar>
        </Card>
      </RouterLink>

      <RouterLink to="/questionnaires/recyclage">
        <Card title="Déchets & Recyclage" :has-arrow="true">
          <div class="image-center">
            <span class="emoji-img">♻️️</span>
          </div>
          <ProgressBar :value="store.getCategoryScore('recyclage')"></ProgressBar>
        </Card>
      </RouterLink>

      <RouterLink to="/questionnaires/numerique">
        <Card title="Numérique" :has-arrow="true">
          <div class="image-center">
            <span class="emoji-img">💻️</span>
          </div>
          <ProgressBar :value="store.getCategoryScore('numerique')"></ProgressBar>
        </Card>
      </RouterLink>

      <RouterLink to="/questionnaires/loisirs">
        <Card title="Loisirs" :has-arrow="true">
          <div class="image-center">
            <span class="emoji-img">🃏️</span>
          </div>
          <ProgressBar :value="store.getCategoryScore('loisirs')"></ProgressBar>
        </Card>
      </RouterLink>

      <RouterLink to="/questionnaires/quotidien">
        <Card title="Habitudes Quotidiennes" :has-arrow="true">
          <div class="image-center">
            <span class="emoji-img">🗓️️</span>
          </div>
          <ProgressBar :value="store.getCategoryScore('quotidien')"></ProgressBar>
        </Card>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
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
  padding: 100px 20px;
  overflow-y: auto;
  flew: 1;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}

.image-center {
  flex-shrink: 0;
  margin-left: 15px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.emoji-img {
  font-size: 2.5rem;
}

/* --- BARRE DE PROGRESSION --- */
.progress-container {
  display: flex;
  align-items: center;
  gap: 10px;
}
.progress-track {
  flex-grow: 1;
  height: 12px;
  background-color: white;
  border-radius: 10px;
  overflow: hidden;
}
.progress-fill {
  background-color: #ccc;
  height: 100%;
}
</style>
