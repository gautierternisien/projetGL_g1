// src/stores/progress.ts
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { API_URL } from '@/config' // On importe l'URL de l'API
import { loadCategoryProgressFromLocalAnswers } from '@/utils/ngcProgress'

export const useProgressStore = defineStore('progress', () => {
  // --- 1. STATE (Les données) ---
  // On initialise tout à 0 par défaut
  const progressValueTransport = ref(0)
  const progressValueLogement = ref(0)
  const progressValueAlimentation = ref(0)
  const progressValueDivers = ref(0)

  // --- 2. ACTIONS (Pour modifier les données) ---
  // Ces fonctions seront appelées par ta page Questionnaire
  function setScore(category: string, value: number) {
    if (category === 'transport') progressValueTransport.value = value
    if (category === 'logement') progressValueLogement.value = value
    if (category === 'alimentation') progressValueAlimentation.value = value
    if (category === 'divers') progressValueDivers.value = value
  }

  function syncFromLocalAnswers() {
    const local = loadCategoryProgressFromLocalAnswers()
    setScore('transport', local.transport)
    setScore('logement', local.logement)
    setScore('alimentation', local.alimentation)
    setScore('divers', local.divers)
  }

  // NOUVELLE ACTION : Charge tout depuis le backend
  async function fetchAllProgress(userId: number) {
    const categories = ['transport', 'logement', 'alimentation', 'divers']

    await Promise.all(
      categories.map(async (category) => {
        try {
          const response = await fetch(`${API_URL}/answers/${category}/${userId}`, {
            cache: 'no-store',
          })
          if (response.ok) {
            const data = await response.json()
            setScore(category, data.progress || 0)
          }
        } catch (error) {
          console.error(`Erreur chargement progression ${category}:`, error)
        }
      }),
    )
  }

  // --- 3. GETTERS (Calculs automatiques) ---
  // Calcule la moyenne globale automatiquement pour le Dashboard
  const globalAverage = computed(() => {
    // On additionne tout et on divise par le nombre de catégories (4 ici)
    const total =
      progressValueTransport.value +
      progressValueLogement.value +
      progressValueAlimentation.value +
      progressValueDivers.value
    return Math.round(total / 4)
  })

  function getCategoryScore(category: string): number {
    if (category === 'transport') return progressValueTransport.value
    if (category === 'alimentation') return progressValueAlimentation.value
    if (category === 'logement') return progressValueLogement.value
    if (category === 'divers') return progressValueDivers.value

    return 0 // Valeur par défaut si catégorie inconnue
  }

  // On retourne tout pour pouvoir l'utiliser ailleurs
  return {
    getCategoryScore,
    setScore,
    syncFromLocalAnswers,
    fetchAllProgress, // On exporte la nouvelle action
    globalAverage,
  }
})
