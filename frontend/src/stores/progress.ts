// src/stores/progress.ts
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useProgressStore = defineStore('progress', () => {
  // --- 1. STATE (Les données) ---
  // On initialise tout à 0 par défaut
  const progressValueTransport = ref(0)
  const progressValueLogement = ref(0)
  const progressValueAlimentation = ref(0)
  const progressValueConsommation = ref(0)
  const progressValueRecyclage = ref(0)
  const progressValueNumerique = ref(0)
  const progressValueLoisirs = ref(0)
  const progressValueQuotidien = ref(0)

  // --- 2. ACTIONS (Pour modifier les données) ---
  // Ces fonctions seront appelées par ta page Questionnaire
  function setScore(category: string, value: number) {
    if (category === 'transport') progressValueTransport.value = value
    if (category === 'logement') progressValueLogement.value = value
    if (category === 'alimentation') progressValueAlimentation.value = value
    if (category === 'consommation') progressValueConsommation.value = value
    if (category === 'recyclage') progressValueRecyclage.value = value
    if (category === 'numerique') progressValueNumerique.value = value
    if (category === 'loisirs') progressValueLoisirs.value = value
    if (category === 'quotidien') progressValueQuotidien.value = value
  }

  // --- 3. GETTERS (Calculs automatiques) ---
  // Calcule la moyenne globale automatiquement pour le Dashboard
  const globalAverage = computed(() => {
    // On additionne tout et on divise par le nombre de catégories (4 ici)
    const total =
      progressValueTransport.value +
      progressValueLogement.value +
      progressValueAlimentation.value +
      progressValueConsommation.value +
      progressValueRecyclage.value +
      progressValueNumerique.value +
      progressValueLoisirs.value +
      progressValueQuotidien.value
    return Math.round(total / 8)
  })

  function getCategoryScore(category: string): number {
    if (category === 'transport') return progressValueTransport.value
    if (category === 'alimentation') return progressValueAlimentation.value
    if (category === 'logement') return progressValueLogement.value
    if (category === 'consommation') return progressValueConsommation.value
    if (category === 'recyclage') return progressValueRecyclage.value
    if (category === 'numerique') return progressValueNumerique.value
    if (category === 'loisirs') return progressValueLoisirs.value
    if (category === 'quotidien') return progressValueQuotidien.value

    return 0 // Valeur par défaut si catégorie inconnue
  }

  // On retourne tout pour pouvoir l'utiliser ailleurs
  return {
    getCategoryScore,
    setScore,
    globalAverage,
  }
})
