<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import Header from '@/components/Header.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import { VRadio, VRadioGroup } from 'vuetify/components'
import { useProgressStore } from '@/stores/progress'

// Définition des types pour éviter les 'any'
interface Option {
  label: string
  value: string
}

interface Question {
  id: number
  text: string
  options: Option[]
}

const router = useRouter()
const progressStore = useProgressStore()

// --- CONFIGURATION API ---
const API_URL = 'http://localhost:8000'
const USER_ID = 'user123'

// --- ÉTAT ---
const questions = ref<Question[]>([])
const isLoading = ref(true)
const isCompletedMode = ref(false) // Nouvel état pour le récapitulatif

// Stockage des réponses
const savedAnswers = ref<Record<number, string>>({})

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
      progressStore.setScore('transport', data.progress)
    }
  } catch (error) {
    console.error('Erreur lors de la sauvegarde:', error)
  }
}

// Fonction pour effacer les réponses (Reset)
const resetAnswers = async () => {
  if (
    confirm(
      'Attention, cela va effacer toutes vos réponses pour ce questionnaire. Voulez-vous continuer ?',
    )
  ) {
    try {
      // Appel DELETE au backend
      const response = await fetch(`${API_URL}/answers/${USER_ID}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        // Si le backend confirme la suppression, on reset le frontend
        savedAnswers.value = {}
        currentQuestionIndex.value = 0
        selectedAnswer.value = null
        isCompletedMode.value = false
        progressStore.setScore('transport', 0)
        console.log('Réponses réinitialisées avec succès.')
      } else {
        alert('Erreur lors de la réinitialisation côté serveur.')
      }
    } catch (error) {
      console.error('Erreur réseau lors du reset:', error)
    }
  }
}

// --- INITIALISATION (onMounted) ---
onMounted(async () => {
  await Promise.all([fetchQuestions(), fetchUserProgress()])

  if (questions.value.length > 0) {
    // 1. Vérifier si tout est répondu
    const totalQuestions = questions.value.length
    const answeredCount = Object.keys(savedAnswers.value).length

    if (answeredCount === totalQuestions && totalQuestions > 0) {
      // Tout est répondu -> Mode Récapitulatif
      isCompletedMode.value = true
      progressStore.setScore('transport', 100)
    } else {
      // 2. Sinon, trouver la première question NON répondue
      const firstUnansweredIndex = questions.value.findIndex((q) => !savedAnswers.value[q.id])

      // Si on trouve une question non répondue, on y va, sinon on va à la fin (cas rare)
      currentQuestionIndex.value =
        firstUnansweredIndex !== -1 ? firstUnansweredIndex : totalQuestions - 1

      // Initialiser la réponse courante
      const currentQ = questions.value[currentQuestionIndex.value]
      if (currentQ) {
        selectedAnswer.value = savedAnswers.value[currentQ.id] || null
      }
    }
  }

  isLoading.value = false
})

// --- COMPUTED ---
const currentQuestion = computed(() => questions.value[currentQuestionIndex.value])

const progressValue = computed(() => {
  if (questions.value.length === 0) return 0
  if (isCompletedMode.value) return 100
  return ((currentQuestionIndex.value + 1) / questions.value.length) * 100
})

const isFirstQuestion = computed(() => currentQuestionIndex.value === 0)
const isLastQuestion = computed(
  () => questions.value.length > 0 && currentQuestionIndex.value === questions.value.length - 1,
)

const canProceed = computed(
  () => selectedAnswer.value !== null && selectedAnswer.value !== undefined,
)

// Helper pour afficher le libellé de la réponse dans le récapitulatif
const getAnswerLabel = (question: Question) => {
  const val = savedAnswers.value[question.id]
  const option = question.options.find((opt) => opt.value === val)
  return option ? option.label : 'Non répondu'
}

// --- WATCHERS ---
watch(currentQuestionIndex, (newIndex) => {
  if (questions.value[newIndex]) {
    const questionId = questions.value[newIndex].id
    selectedAnswer.value = savedAnswers.value[questionId] || null
  }
})

watch(selectedAnswer, async (newVal) => {
  if (newVal && currentQuestion.value) {
    const questionId = currentQuestion.value.id
    savedAnswers.value[questionId] = newVal
    await saveAnswerToBackend(questionId, newVal)
  }
})

// --- ACTIONS DE NAVIGATION ---
const nextQuestion = () => {
  if (!canProceed.value) return

  if (!isLastQuestion.value) {
    currentQuestionIndex.value++
  } else {
    // Fin du questionnaire -> On passe en mode récapitulatif
    isCompletedMode.value = true
    progressStore.setScore('transport', 100)
  }
}

const prevQuestion = () => {
  if (!isFirstQuestion.value) {
    currentQuestionIndex.value--
  }
}

const saveAndExit = () => {
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
      :showResumeBtn="!isCompletedMode"
      @resumeLater="saveAndExit"
    />

    <div class="scrollable-area">
      <div v-if="isLoading" class="loading-state">Chargement...</div>

      <!-- VUE RÉCAPITULATIF (Si terminé) -->
      <div v-else-if="isCompletedMode" class="recap-container">
        <div class="success-icon">🎉</div>
        <h2 class="recap-title">Questionnaire terminé !</h2>
        <p class="recap-subtitle">Voici le récapitulatif de vos réponses :</p>

        <div class="recap-list">
          <div v-for="q in questions" :key="q.id" class="recap-item">
            <div class="recap-question">{{ q.text }}</div>
            <div class="recap-answer">{{ getAnswerLabel(q) }}</div>
          </div>
        </div>

        <div class="recap-actions">
          <button class="nav-btn prev-btn" @click="saveAndExit">Retour au tableau de bord</button>
          <button class="nav-btn reset-btn" @click="resetAnswers">Modifier mes réponses</button>
        </div>
      </div>

      <!-- VUE QUESTIONNAIRE (Si en cours) -->
      <div v-else-if="currentQuestion" class="question-container">
        <h3 class="question-counter">
          Question {{ currentQuestionIndex + 1 }} sur {{ questions.length }}
        </h3>

        <h1 class="question-text">{{ currentQuestion.text }}</h1>

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

        <div class="navigation-buttons">
          <button v-if="!isFirstQuestion" class="nav-btn prev-btn" @click="prevQuestion">
            < Question précédente
          </button>
          <div v-else></div>

          <button class="nav-btn next-btn" @click="nextQuestion" :disabled="!canProceed">
            {{ isLastQuestion ? 'Enregistrer et quitter' : 'Question suivante >' }}
          </button>
        </div>

        <div class="progress-section">
          <ProgressBar :value="progressValue" :showLabel="false" />
        </div>
      </div>

      <div v-else class="error-state">Erreur de chargement.</div>
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

.question-container,
.recap-container {
  width: 100%;
  max-width: 600px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

/* Styles spécifiques au récapitulatif */
.recap-container {
  align-items: center;
}
.success-icon {
  font-size: 3rem;
  margin-bottom: 10px;
}
.recap-title {
  font-size: 1.8rem;
  color: #2c3e50;
  margin-bottom: 10px;
}
.recap-subtitle {
  color: #666;
  margin-bottom: 30px;
}
.recap-list {
  width: 100%;
  background: #f9f9f9;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 30px;
}
.recap-item {
  margin-bottom: 15px;
  border-bottom: 1px solid #eee;
  padding-bottom: 15px;
}
.recap-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}
.recap-question {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 5px;
  font-size: 0.95rem;
}
.recap-answer {
  color: #679436;
  font-weight: 500;
}
.recap-actions {
  display: flex;
  gap: 15px;
  width: 100%;
  justify-content: center;
}

/* Styles existants */
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
.next-btn:disabled {
  background-color: #bdc3c7;
  color: #7f8c8d;
  cursor: not-allowed;
}

.reset-btn {
  background-color: #fff;
  color: #e74c3c;
  border: 1px solid #e74c3c;
}
.reset-btn:hover {
  background-color: #e74c3c;
  color: white;
}

.progress-section {
  margin-top: 20px;
  padding: 0 10px;
}
</style>
