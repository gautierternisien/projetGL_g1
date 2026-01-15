<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="view-container">
    <Header title="Introuvable" subtitle="Erreur 404" />

    <div class="content-wrapper">
      <div class="message-card">
        <span class="icon">🤔</span>
        <p class="message-text">La page que vous cherchez n'existe pas</p>

        <RouterLink to="/" class="btn-home"> Retour à l'accueil </RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.view-container {
  min-height: 100vh;
  box-sizing: border-box;
  padding-top: 110px; /* Espace pour le header fixe */
  padding-bottom: 90px; /* Espace pour la navbar fixe */
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
}

.content-wrapper {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 20px;
}

.message-card {
  background-color: #f5f5f5;
  border-radius: 24px;
  padding: 40px 30px;
  width: 100%;
  max-width: 350px;
  text-align: center;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.icon {
  font-size: 3rem;
}

.message-text {
  font-size: 1.2rem;
  color: #333;
  margin: 0;
  font-weight: 500;
  line-height: 1.4;
}

.btn-home {
  margin-top: 10px;
  background-color: #679436; /* Vert du thème */
  color: white;
  text-decoration: none;
  padding: 12px 24px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.95rem;
  transition:
    transform 0.2s,
    background-color 0.2s;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.btn-home:active {
  transform: scale(0.95);
  background-color: #557a2d;
}
</style>
