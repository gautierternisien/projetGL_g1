<script setup lang="ts">
import { computed } from 'vue'

// On définit les propriétés que le parent doit envoyer
const props = defineProps({
  value: {
    type: Number,
    required: true,
    default: 0,
  },
  showLabel: {
    type: Boolean,
    default: true,
  },
})

// Logique de couleur dynamique
const statusColor = computed(() => {
  if (props.value < 30) {
    return '#EC8879' // Rouge (si peu avancé)
  } else if (props.value < 70) {
    return '#FFA162' // Jaune/Orange (si moyen)
  } else {
    return '#00B2B5' // Vert du thème (si bien avancé)
  }
})
</script>

<template>
  <div class="progress-wrapper">
    <div v-if="showLabel" class="progress-text" :style="{ color: statusColor }">{{ value }}%</div>

    <div class="progress-track">
      <div
        class="progress-fill"
        :style="{
          width: value + '%',
          backgroundColor: statusColor,
        }"
      ></div>
    </div>
  </div>
</template>

<style scoped>
.progress-wrapper {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-text {
  font-weight: 700;
  font-size: 0.9rem;
  min-width: 35px;
  text-align: right;
  transition: color 0.5s ease; /* Transition fluide de la couleur */
  flex-shrink: 0;
}

.progress-track {
  flex-grow: 1;
  width: 100%;
  height: 12px; /* Épaisseur de la barre */
  background-color: #eeeeee; /* Gris très clair pour le fond */
  border-radius: 10px;
  overflow: hidden; /* Important pour que le remplissage ne dépasse pas des bords ronds */
  box-shadow: inset 0 2px 5px rgba(0, 0, 0, 0.1);
}

.progress-fill {
  height: 100%;
  border-radius: 10px;
  /* Animation fluide quand la largeur ou la couleur change */
  transition:
    width 0.6s cubic-bezier(0.4, 0, 0.2, 1),
    background-color 0.5s ease;
  box-shadow: 2px 0 5px rgba(0, 0, 0, 0.15);
}
</style>
