<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import Header from '@/components/AppHeader.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import { VRadio, VRadioGroup } from 'vuetify/components'
import { useProgressStore } from '@/stores/progress.ts'
import { useAuthStore } from '@/stores/auth'
import { API_URL, USER_ID } from '@/config'

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
const route = useRoute()
const progressStore = useProgressStore()
const authStore = useAuthStore()

const userId = computed(() => (authStore.user ? authStore.user.id : USER_ID))

const currentCategory = computed(() => route.params.category as string)

// --- ÉTAT ---
const questions = ref<Question[]>([])
const isLoading = ref(true)
const isError = ref(false)
const isCompletedMode = ref(false) // Nouvel état pour le récapitulatif

// Stockage des réponses
const savedAnswers = ref<Record<number, string>>({})

const currentQuestionIndex = ref(0)
const selectedAnswer = ref<string | null>(null)

// --- APPELS API ---

const fetchQuestions = async () => {
  try {
    // URL DYNAMIQUE : /questions/{category}
    const response = await fetch(`${API_URL}/questions/${currentCategory.value}`)

    if (response.ok) {
      questions.value = await response.json()
    } else {
      isError.value = true
      console.error('Catégorie introuvable ou erreur serveur')
    }
  } catch (error) {
    isError.value = true
    console.error('Erreur lors du chargement des questions:', error)
  }
}

const fetchUserProgress = async () => {
  try {
    // AJOUT DE L'OPTION { cache: 'no-store' }
    const response = await fetch(`${API_URL}/answers/${currentCategory.value}/${userId.value}`, {
      cache: 'no-store',
    })

    if (response.ok) {
      const data = await response.json()
      savedAnswers.value = data.answers || {}
      progressStore.setScore(currentCategory.value, data.progress || 0)
    }
  } catch (error) {
    console.error('Erreur lors du chargement de la progression:', error)
  }
}

const saveAnswerToBackend = async (questionId: number, value: string) => {
  try {
    // URL DYNAMIQUE : /answers/{category}/{user_id}
    const response = await fetch(`${API_URL}/answers/${currentCategory.value}/${userId.value}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question_id: questionId,
        answer_value: value,
      }),
    })

    if (response.ok) {
      const data = await response.json()
      // Mise à jour du store avec la progression calculée par le backend
      progressStore.setScore(currentCategory.value, data.progress)
    }
  } catch (error) {
    console.error('Erreur lors de la sauvegarde:', error)
  }
}

// Fonction pour modifier les réponses (Retour au mode édition)
const modifyAnswers = () => {
  isCompletedMode.value = false
  currentQuestionIndex.value = 0
  // On remet la réponse sélectionnée pour la première question
  if (questions.value.length > 0) {
    const firstQ = questions.value[0]
    if (firstQ) {
      selectedAnswer.value = savedAnswers.value[firstQ.id] || null
    }
  }
}

// --- INITIALISATION (onMounted) ---
onMounted(async () => {
  isLoading.value = true
  // On charge les données en parallèle
  await Promise.all([fetchQuestions(), fetchUserProgress()])

  if (!isError.value && questions.value.length > 0) {
    const totalQuestions = questions.value.length
    const answeredCount = Object.keys(savedAnswers.value).length

    if (answeredCount === totalQuestions && totalQuestions > 0) {
      isCompletedMode.value = true
    } else {
      const firstUnansweredIndex = questions.value.findIndex((q) => !savedAnswers.value[q.id])
      currentQuestionIndex.value =
        firstUnansweredIndex !== -1 ? firstUnansweredIndex : totalQuestions - 1

      const currentQ = questions.value[currentQuestionIndex.value]
      if (currentQ) {
        selectedAnswer.value = savedAnswers.value[currentQ.id] || null
      }
    }
  }
  isLoading.value = false
})

const CATEGORY_DISPLAY_NAMES: Record<string, string> = {
  transport: 'Transport',
  alimentation: 'Alimentation',
  logement: 'Logement ',
  divers: 'Divers',
}

// --- COMPUTED ---
const categoryTitle = computed(() => {
  const slug = currentCategory.value

  // On regarde s'il y a un joli nom, sinon on met une majuscule par défaut
  if (CATEGORY_DISPLAY_NAMES[slug]) {
    return CATEGORY_DISPLAY_NAMES[slug]
  }

  // Fallback (au cas où) : transport -> Transport
  return slug.charAt(0).toUpperCase() + slug.slice(1)
})

const currentQuestion = computed(() => questions.value[currentQuestionIndex.value])

const progressValue = computed(() => {
  if (questions.value.length === 0) return 0
  if (isCompletedMode.value) return 100
  return (currentQuestionIndex.value / questions.value.length) * 100
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
    progressStore.setScore(currentCategory.value, 100)
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
    progressStore.setScore(currentCategory.value, realProgress)
  }
  router.push('/questionnaires')
}
</script>

<template>
  <div class="dashboard-wrapper">
    <Header
      title="Questionnaire"
      :subtitle="categoryTitle"
      :showResumeBtn="!isCompletedMode"
      @resumeLater="saveAndExit"
    />

    <div class="scrollable-area">
      <div v-if="isLoading" class="loading-state">Chargement...</div>

      <div v-else-if="isError" class="error-state">
        <span class="error-emoji">😕</span>
        <h2>Oups !</h2>
        <p>Impossible de charger le questionnaire "{{ categoryTitle }}".</p>
        <button class="nav-btn prev-btn" @click="saveAndExit">Retour au menu</button>
      </div>

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
          <button class="nav-btn reset-btn" @click="modifyAnswers">Modifier mes réponses</button>
          <button class="nav-btn quest-btn" @click="saveAndExit">Retour aux questionnaires</button>
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
            &lt; Question précédente
          </button>
          <div v-else></div>

          <button class="nav-btn next-btn" @click="nextQuestion" :disabled="!canProceed">
            {{ isLastQuestion ? 'Enregistrer et quitter' : 'Question suivante >' }}
          </button>
        </div>

        <div class="progress-section">
          <ProgressBar :value="progressValue" :showLabel="false" />
        </div>

        <div class="message">
          <p>Toute non réponse vaudra la moyenne nationale.</p>
        </div>
      </div>

      <div v-else class="error-state">Erreur de chargement.</div>
    </div>
  </div>
</template>

<style scoped>
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
  /* MODIFICATION : Padding réduit (12px 20px -> 8px 16px) */
  padding: 18px 16px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  /* MODIFICATION : Taille de police réduite (0.9rem -> 0.8rem) */
  font-size: 0.8rem;
  transition: all 0.2s;
  border: none;
}

.prev-btn {
  background-color: #f0f0f0;
  color: #555;
}

.next-btn {
  background-color: #2c3e50;
  color: white;
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

.progress-section {
  margin-top: 20px;
  padding: 0 10px;
}

.quest-btn {
  background-color: #679436;
  color: white;
}

.message {
  margin-top: 30px;
  font-size: 0.9rem;
  font-style: italic;
  color: #888;
  text-align: center;
}
</style>
