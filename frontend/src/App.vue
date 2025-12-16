<template>
  <div class="app-container">
    <RouterView />
  </div>

  <nav class="bottom-nav">
    <RouterLink to="/" class="nav-item">
      <span>📊</span>
    </RouterLink>

    <RouterLink to="/questionnaires" class="nav-item">
      <span>📝</span>
    </RouterLink>

    <RouterLink to="/missions" class="nav-item">
      <span>🎯</span>
    </RouterLink>

    <RouterLink to="/communaute" class="nav-item">
      <span>👥</span>
    </RouterLink>

    <RouterLink to="/conseils" class="nav-item">
      <span>💡</span>
    </RouterLink>
  </nav>
</template>

<script setup lang="ts">
import { RouterView, RouterLink } from 'vue-router'
</script>

<style scoped>
.app-container {
  width: 100%;
  height: 100%;
}

.bottom-nav {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);

  /* Largeur adaptative (max 350px pour ressembler à l'image) */
  width: 90%;
  max-width: 320px;
  height: 65px;

  /* Couleur de fond sombre (gris foncé) */
  background-color: #5e5e5e;

  /* Arrondi prononcé (forme de pilule) */
  border-radius: 35px;

  display: flex;
  justify-content: space-evenly;
  align-items: center;
  z-index: 1000;

  /* Ombre portée pour l'effet flottant */
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
}

.nav-item {
  display: flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  background-color: #77786f;

  /* Taille fixe pour créer des cercles parfaits */
  width: 50px;
  height: 50px;
  border-radius: 50%;

  /* Transition douce pour l'effet au clic */
  transition: background-color 0.3s ease;

  font-size: 1.5rem;
}

/* Style de l'élément actif (cercle plus clair) */
.router-link-active {
  background-color: #9c9e89;
}
</style>
