<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Header from '@/components/Header.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import { VRadio, VRadioGroup } from 'vuetify/components'
import { useProgressStore } from '@/stores/progress'

const router = useRouter()
const progressStore = useProgressStore()

// --- CONFIGURATION API ---
const API_URL = 'http://localhost:8000'
const USER_ID = 'user123' // ID utilisateur simulé (à remplacer par l'auth réelle plus tard)

// --- ÉTAT ---
// Les questions sont chargées depuis le backend
const questions = ref<any[]>([])
const isLoading = ref(true)

// Stockage des réponses (synchronisé avec le backend)
const savedAnswers = ref<Record<number, string>>({})

// État pour suivre la question actuelle
const currentQuestionIndex = ref(0)
const selectedAnswer = ref<string | null>(null)

// --- APPELS API ---

const fetchQuestions = async () => {
  try {
    const response = await fetch(`${API_URL}/questions/transport`)
    if (response.ok) {
      questions.value = await response.json()
    }
  } catch (error) {
    console.error('Erreur lors du chargement des questions:', error)
  }
}

const fetchUserProgress = async () => {
  try {
    const response = await fetch(`${API_URL}/answers/${USER_ID}`)
    if (response.ok) {
      savedAnswers.value = await response.json()
    }
  } catch (error) {
    console.error('Erreur lors du chargement de la progression:', error)
  }
}

const saveAnswerToBackend = async (questionId: number, value: string) => {
  try {
    const response = await fetch(`${API_URL}/answers/${USER_ID}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question_id: questionId,
        answer_value: value,
      }),
    })

    if (response.ok) {
      const data = await response.json()
      // On met à jour le store avec la progression calculée par le serveur
      progressStore.setScore('transport', data.progress)
    }
  } catch (error) {
    console.error('Erreur lors de la sauvegarde:', error)
  }
}

// --- INITIALISATION (onMounted) ---
onMounted(async () => {
  // 1. On charge les données en parallèle
  await Promise.all([fetchQuestions(), fetchUserProgress()])

  // 2. Calcul de l'index initial basé sur la progression (si des questions existent)
  if (questions.value.length > 0) {
    const savedScore = progressStore.getCategoryScore('transport')
    let initialIndex = 0

    if (savedScore > 0) {
      initialIndex = Math.round((savedScore * questions.value.length) / 100) - 1
      if (initialIndex < 0) initialIndex = 0
      if (initialIndex >= questions.value.length) initialIndex = questions.value.length - 1
    }

    currentQuestionIndex.value = initialIndex

    // 3. Initialiser la réponse courante pour la question affichée
    const currentQ = questions.value[initialIndex]
    if (currentQ) {
      selectedAnswer.value = savedAnswers.value[currentQ.id] || null
    }
  }

  isLoading.value = false
})

// --- COMPUTED ---
const currentQuestion = computed(() => questions.value[currentQuestionIndex.value])

const progressValue = computed(() => {
  if (questions.value.length === 0) return 0
  return ((currentQuestionIndex.value + 1) / questions.value.length) * 100
})

const isFirstQuestion = computed(() => currentQuestionIndex.value === 0)
const isLastQuestion = computed(
  () => questions.value.length > 0 && currentQuestionIndex.value === questions.value.length - 1,
)

// Vérifie si une réponse est sélectionnée pour activer le bouton suivant
const canProceed = computed(
  () => selectedAnswer.value !== null && selectedAnswer.value !== undefined,
)

// --- WATCHERS ---

// Quand on change de question, on restaure la réponse depuis l'état local (qui vient du back)
watch(currentQuestionIndex, (newIndex) => {
  if (questions.value[newIndex]) {
    const questionId = questions.value[newIndex].id
    selectedAnswer.value = savedAnswers.value[questionId] || null
  }
})

// Quand l'utilisateur sélectionne une réponse, on sauvegarde via l'API
watch(selectedAnswer, async (newVal) => {
  if (newVal && currentQuestion.value) {
    const questionId = currentQuestion.value.id

    // Mise à jour locale immédiate
    savedAnswers.value[questionId] = newVal

    // Envoi asynchrone au backend
    await saveAnswerToBackend(questionId, newVal)
  }
})

// --- ACTIONS DE NAVIGATION ---

const nextQuestion = () => {
  if (!canProceed.value) return

  if (!isLastQuestion.value) {
    currentQuestionIndex.value++
  } else {
    // Fin du questionnaire
    console.log('Questionnaire terminé')
    router.push('/questionnaires')
  }
}

const prevQuestion = () => {
  if (!isFirstQuestion.value) {
    currentQuestionIndex.value--
  }
}

const saveAndExit = () => {
  // La sauvegarde est déjà faite à chaque sélection via le watcher.
  // On met juste à jour le store localement pour l'affichage immédiat dans le dashboard
  const answeredCount = Object.keys(savedAnswers.value).length
  if (questions.value.length > 0) {
    const realProgress = Math.round((answeredCount / questions.value.length) * 100)
    progressStore.setScore('transport', realProgress)
  }

  router.push('/questionnaires')
}
</script>

<template>
  <div class="dashboard-wrapper">
    <Header
      title="Questionnaire"
      subtitle="Transport"
      :showResumeBtn="true"
      @resumeLater="saveAndExit"
    />

    <div class="scrollable-area">
      <!-- Affichage conditionnel : on attend que les questions soient chargées -->
      <div v-if="isLoading" class="loading-state">Chargement du questionnaire...</div>

      <div class="question-container" v-else-if="currentQuestion">
        <!-- Compteur -->
        <h3 class="question-counter">
          Question {{ currentQuestionIndex + 1 }} sur {{ questions.length }}
        </h3>

        <!-- Question posée -->
        <h1 class="question-text">{{ currentQuestion.text }}</h1>

        <!-- Réponses -->
        <div class="answers-area">
          <v-radio-group v-model="selectedAnswer">
            <v-radio
              v-for="option in currentQuestion.options"
              :key="option.value"
              :label="option.label"
              :value="option.value"
              color="#679436"
            ></v-radio>
          </v-radio-group>
        </div>

        <!-- Boutons de navigation -->
        <div class="navigation-buttons">
          <button v-if="!isFirstQuestion" class="nav-btn prev-btn" @click="prevQuestion">
            &lt; Question précédente
          </button>

          <div v-else></div>

          <button class="nav-btn next-btn" @click="nextQuestion" :disabled="!canProceed">
            {{ isLastQuestion ? 'Enregistrer et quitter' : 'Question suivante >' }}
          </button>
        </div>

        <!-- Barre de progression -->
        <div class="progress-section">
          <ProgressBar :value="progressValue" :showLabel="false" />
        </div>
      </div>

      <div v-else class="error-state">
        Impossible de charger les questions. Vérifiez que le backend est lancé.
      </div>
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

.scrollable-area {
  padding: 120px 20px 40px 20px;
  overflow-y: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.loading-state,
.error-state {
  margin-top: 50px;
  font-size: 1.2rem;
  color: #666;
}

.question-container {
  width: 100%;
  max-width: 600px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.question-counter {
  text-align: center;
  color: #666;
  font-weight: 500;
  margin-bottom: 20px;
  font-size: 1.1rem;
}

.question-text {
  text-align: center;
  font-size: 1.8rem;
  margin-bottom: 40px;
  line-height: 1.3;
  color: #2c3e50;
}

.answers-area {
  margin-bottom: 20px;
  padding: 0 10px;
}

.navigation-buttons {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  margin-top: 40px;
}

.nav-btn {
  padding: 12px 20px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
  border: none;
}

.prev-btn {
  background-color: #f0f0f0;
  color: #555;
}

.prev-btn:hover {
  background-color: #e0e0e0;
}

.next-btn {
  background-color: #2c3e50;
  color: white;
}

.next-btn:hover {
  background-color: #1a252f;
}

/* Style pour le bouton désactivé */
.next-btn:disabled {
  background-color: #bdc3c7; /* Gris */
  color: #7f8c8d;
  cursor: not-allowed;
  transform: none;
}

.progress-section {
  margin-top: 20px;
  padding: 0 10px;
}
</style>
