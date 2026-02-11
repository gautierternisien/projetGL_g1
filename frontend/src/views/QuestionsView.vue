<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Engine from 'publicodes'
import { VCheckbox, VRadio, VRadioGroup, VTextField } from 'vuetify/components'

import Header from '@/components/AppHeader.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import { API_URL } from '@/config'
import { useProgressStore } from '@/stores/progress'
import { useAuthStore } from '@/stores/auth'
import {
  buildQuestionnaire,
  isQuestionVisible,
  type Category,
  type QuestionRecord,
} from '@/lib/ngc/questionnaire'
import { computeCategoryProgressFromAnswers } from '@/utils/ngcProgress'
import { loadAnswers, loadProgress, saveAnswers, saveProgress } from '@/lib/ngc/answersStorage'

const router = useRouter()
const route = useRoute()
const progressStore = useProgressStore()
const authStore = useAuthStore()
const currentCategory = computed(() => route.params.category as Category)

const CATEGORY_DISPLAY_NAMES: Record<string, string> = {
  transport: 'Transport',
  alimentation: 'Alimentation',
  logement: 'Logement',
  divers: 'Divers',
}

const categoryTitle = computed(
  () => CATEGORY_DISPLAY_NAMES[currentCategory.value as string] ?? currentCategory.value,
)

const isLoading = ref(true)
const engine = ref<Engine | null>(null)
const engineError = ref<string | null>(null)
const situationError = ref<unknown>(null)

const allQuestions = ref<QuestionRecord[]>([])
const answers = ref<Record<string, unknown>>(loadAnswers() ?? {})
const currentSlug = ref<string | null>(null)

const ANSWERS_PERSIST_DEBOUNCE_MS = 200
const ENGINE_SET_SITUATION_DEBOUNCE_MS = 260
const BACKEND_STATS_SYNC_DEBOUNCE_MS = 1000

let saveAnswersTimer: ReturnType<typeof setTimeout> | null = null
let setSituationTimer: ReturnType<typeof setTimeout> | null = null
let backendStatsSyncTimer: ReturnType<typeof setTimeout> | null = null

const isError = computed(() => !isLoading.value && !!engineError.value)

let restoreWarn: (() => void) | null = null

async function fetchRules(): Promise<unknown> {
  const controller = new AbortController()
  const timeoutMs = 10000
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const res = await fetch(`${API_URL}/rules`, { cache: 'no-store', signal: controller.signal })
    if (!res.ok) {
      await Promise.reject(new Error(`HTTP ${res.status}`))
    }
    return await res.json()
  } catch (e: unknown) {
    if ((e as Error)?.name === 'AbortError') {
      throw new Error(`Timeout after ${timeoutMs}ms while fetching rules`)
    }
    throw e
  } finally {
    clearTimeout(timer)
  }
}

function silenceNoisyWarnings() {
  const originalWarn = console.warn
  console.warn = (...args: unknown[]) => {
    const msg = args
      .map((a) => {
        if (typeof a === 'string') return a
        try {
          return JSON.stringify(a)
        } catch {
          return String(a)
        }
      })
      .join(' ')

    const normalized = msg
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()

    if (normalized.includes('un cycle a ete detecte')) return
    if (normalized.includes('avertissement')) return
    if (normalized.includes('reference circulaire')) return

    return originalWarn(...args)
  }

  return () => {
    console.warn = originalWarn
  }
}

function toPublicodesValue(v: unknown) {
  if (v === undefined || v === null || v === '') return undefined
  if (typeof v === 'boolean') return v ? 'oui' : 'non'
  if (typeof v === 'number') return v
  if (typeof v === 'string') {
    const normalized = v.trim().toLowerCase()
    if (normalized === 'oui' || normalized === 'non') return normalized
    return `'${v.replace(/'/g, "\\'")}'`
  }
  if (Array.isArray(v))
    return v.map((x) => {
      if (typeof x === 'boolean') return x ? 'oui' : 'non'
      if (typeof x === 'string') {
        const normalized = x.trim().toLowerCase()
        if (normalized === 'oui' || normalized === 'non') return normalized
        return `'${x.replace(/'/g, "\\'")}'`
      }
      return x
    })
  return v
}

function flattenAnswers(source: Record<string, unknown>) {
  const flat: Record<string, unknown> = {}

  for (const [k, v] of Object.entries(source)) {
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      const keys = Object.keys(v)
      const looksLikeSlugs = keys.some((x) => x.includes(' . '))
      if (looksLikeSlugs) {
        for (const [subK, subV] of Object.entries(v as Record<string, unknown>)) flat[subK] = subV
        continue
      }
    }
    flat[k] = v
  }

  return flat
}

function isAnswerFilled(value: unknown): boolean {
  if (value === undefined || value === null || value === '') return false
  if (Array.isArray(value)) return value.some(isAnswerFilled)
  if (typeof value === 'object') {
    const values = Object.values(value as Record<string, unknown>)
    if (values.length === 0) return false
    return values.some(isAnswerFilled)
  }
  return true
}

function normalizeBooleanValue(value: unknown): boolean | null {
  if (value === true || value === false) return value
  if (typeof value !== 'string') return null

  const normalized = value.trim().toLowerCase()
  if (normalized === 'oui') return true
  if (normalized === 'non') return false
  return null
}

function prettifyCounterLabel(raw: string): string {
  const cleaned = raw
    .trim()
    .replace(/\s*\.\s*nombre\s*$/i, '')
    .trim()
  return cleaned.split(' . ').slice(-1)[0]!.trim()
}

function getMosaicDisplayLabel(opt: any): string {
  const rawLabel = String(opt?.titre ?? opt?.title ?? opt?.label ?? opt)
  return prettifyCounterLabel(rawLabel)
}

function getMosaicSubSlug(parentSlug: string, opt: any): string {
  const candidate = opt?.dottedName ?? opt?.valeur ?? opt?.name

  if (typeof candidate === 'string' && candidate.includes(' . ')) {
    if (candidate.endsWith(' . nombre')) return candidate
    if (candidate.endsWith(' . nombre . nombre'))
      return candidate.replace(/ \. nombre \. nombre$/, ' . nombre')
    return `${candidate} . nombre`
  }

  const rawLabel = String(opt?.titre ?? opt?.title ?? opt?.label ?? opt)
  const label = prettifyCounterLabel(rawLabel)
  return `${parentSlug} . ${label} . nombre`
}

function syncCategoryProgress(nextAnswers: Record<string, unknown>) {
  const map = computeCategoryProgressFromAnswers(nextAnswers)
  progressStore.setScore('transport', map.transport)
  progressStore.setScore('logement', map.logement)
  progressStore.setScore('alimentation', map.alimentation)
  progressStore.setScore('divers', map.divers)
}

function flushLocalPersistence() {
  if (saveAnswersTimer) {
    clearTimeout(saveAnswersTimer)
    saveAnswersTimer = null
  }
  saveAnswers(answers.value)
  syncCategoryProgress(answers.value)
}

function normalizeToken(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
}

function findRuleNameByNormalizedName(
  rules: Record<string, any>,
  expectedName: string,
): string | null {
  const expected = normalizeToken(expectedName)
  for (const key of Object.keys(rules ?? {})) {
    if (normalizeToken(key) === expected) return key
  }
  return null
}

async function pushNgcStatsToBackend() {
  if (!authStore.isConnected || !authStore.token) return
  if (!engine.value || situationError.value) return

  try {
    // Use latest local answers snapshot before evaluating.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    engine.value.setSituation(situation.value as any)

    const bilanRes = engine.value.evaluate('bilan')
    const globalScore =
      typeof bilanRes?.nodeValue === 'number' ? Math.round(bilanRes.nodeValue) : 8559

    const detailsByCategory: Record<string, number> = {}
    for (const key of ['transport', 'logement', 'alimentation', 'divers']) {
      const r = engine.value.evaluate(key)
      detailsByCategory[key] = typeof r?.nodeValue === 'number' ? Math.round(r.nodeValue) : 0
    }

    let servicesScore = 0
    const parsedRules = engine.value.getParsedRules() as any
    const servicesRuleName = findRuleNameByNormalizedName(parsedRules, 'services societaux')
    if (servicesRuleName) {
      const r: any = engine.value.evaluate(servicesRuleName)
      servicesScore = typeof r?.nodeValue === 'number' ? Math.round(r.nodeValue) : 0
    }
    detailsByCategory['services societaux'] = servicesScore
    const categoryProgress = computeCategoryProgressFromAnswers(answers.value)

    await fetch(`${API_URL}/ngc/stats/me`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify({
        global_score: globalScore,
        details_by_category: detailsByCategory,
        category_progress: categoryProgress,
      }),
    })
  } catch {
    // Best-effort sync: keep questionnaire fluid even if backend is unreachable.
  }
}

function getResumeSlug(cat: Category, list: QuestionRecord[]): string | null {
  if (list.length === 0) return null

  const firstUnanswered = list.find((q) => !isAnswerFilled(answers.value[q.slug]))?.slug
  if (firstUnanswered) return firstUnanswered

  const progress = loadProgress() ?? {}
  const saved = progress[cat]
  if (saved && list.some((q) => q.slug === saved)) return saved

  return list[list.length - 1]!.slug
}

function getCounterSuggestions(q: QuestionRecord): Record<string, any> {
  const suggestions = q.config_json.mosaique?.suggestions ?? q.config_json.suggestions
  if (!suggestions || typeof suggestions !== 'object') return {}
  return suggestions as Record<string, any>
}

function applyCounterSuggestion(q: QuestionRecord, preset: any) {
  if (!preset || typeof preset !== 'object') return

  const next: Record<string, number> = {}
  for (const [k, v] of Object.entries(preset as Record<string, any>)) {
    const fullSlug = k.startsWith(q.slug) ? k : `${q.slug} . ${k}`
    const n = Number(v)
    next[fullSlug] = Number.isFinite(n) ? n : 0
  }
  setAnswer(q.slug, next)
}

function getNumberSuggestions(q: QuestionRecord): Record<string, any> {
  const suggestions = q.config_json.suggestions
  if (!suggestions || typeof suggestions !== 'object') return {}
  return suggestions as Record<string, any>
}

function applyNumberSuggestion(slug: string, value: any) {
  const n = Number(value)
  if (Number.isFinite(n)) setAnswer(slug, n)
}

function normalizeStoredAnswersByQuestionType(
  source: Record<string, unknown>,
  questions: QuestionRecord[],
): Record<string, unknown> {
  let changed = false
  const next = { ...source }

  for (const q of questions) {
    if (q.type_widget === 'BOOLEEN' && q.config_json.booleanNative) {
      const raw = next[q.slug]
      const normalized = normalizeBooleanValue(raw)
      if (normalized !== null && raw !== normalized) {
        next[q.slug] = normalized
        changed = true
      }
    }

    if (q.type_widget === 'CHOIX_MULTIPLE' && q.config_json.multiValuesAsBoolean) {
      const raw = next[q.slug]
      if (!raw || typeof raw !== 'object' || Array.isArray(raw)) continue

      const normalizedMap: Record<string, boolean> = {}
      for (const [key, value] of Object.entries(raw as Record<string, unknown>)) {
        const normalized = normalizeBooleanValue(value)
        if (normalized !== null) {
          normalizedMap[key] = normalized
          continue
        }

        if (value === true || value === false) {
          normalizedMap[key] = value
        }
      }

      if (JSON.stringify(raw) !== JSON.stringify(normalizedMap)) {
        next[q.slug] = normalizedMap
        changed = true
      }
    }
  }

  return changed ? next : source
}

const counterSuggestionEntries = computed(() => {
  const q = currentQuestion.value
  if (!q || q.type_widget !== 'COMPTEUR') return []
  return Object.entries(getCounterSuggestions(q))
})

const numberSuggestionEntries = computed(() => {
  const q = currentQuestion.value
  if (!q || q.type_widget !== 'NOMBRE') return []
  return Object.entries(getNumberSuggestions(q))
})

const situation = computed(() => {
  const flat = flattenAnswers(answers.value)
  return Object.fromEntries(
    Object.entries(flat)
      .map(([k, v]) => [k, toPublicodesValue(v)] as const)
      .filter(([, v]) => v !== undefined),
  )
})

watch(
  [engine, situation],
  ([eng, nextSituation]) => {
    if (setSituationTimer) {
      clearTimeout(setSituationTimer)
      setSituationTimer = null
    }

    if (!eng) {
      situationError.value = null
      return
    }

    setSituationTimer = setTimeout(() => {
      try {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        eng.setSituation(nextSituation as any)
        situationError.value = null
      } catch (e: unknown) {
        console.error('Publicodes setSituation error:', e)
        situationError.value = e
      }
    }, ENGINE_SET_SITUATION_DEBOUNCE_MS)
  },
  { immediate: true, flush: 'post' },
)

const bilan = computed(() => {
  if (!engine.value)
    return { val: null as number | null, unit: '', raw: null as unknown, err: null as unknown }
  if (situationError.value) return { val: null, unit: '', raw: null, err: situationError.value }

  try {
    const res = engine.value.evaluate('bilan')
    const rawVal = typeof res?.nodeValue === 'number' ? res.nodeValue : null
    const val = rawVal === null ? null : Math.round(rawVal)
    const unit = res?.unit?.numerators?.join('.') ?? ''
    return { val, unit, raw: res, err: null }
  } catch (e: unknown) {
    console.error('Publicodes evaluate error:', e)
    return { val: null, unit: '', raw: null, err: e }
  }
})

const visibleQuestions = computed(() => {
  const scoped = allQuestions.value.filter((q) => q.categorie_empreinte === currentCategory.value)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  return scoped.filter((q) => isQuestionVisible(q, answers.value, engine.value as any))
})

const currentIndex = computed(() => {
  if (visibleQuestions.value.length === 0) return 0
  if (!currentSlug.value) return 0
  const idx = visibleQuestions.value.findIndex((q) => q.slug === currentSlug.value)
  return idx >= 0 ? idx : 0
})

const currentQuestion = computed(() => visibleQuestions.value[currentIndex.value] ?? null)
const isFirstQuestion = computed(() => currentIndex.value === 0)

type Option = {
  label?: string
  value?: string
  slug?: string
  icone?: string
  titre?: string
  title?: string
  dottedName?: string
}

const isLastQuestion = computed(() => currentIndex.value >= visibleQuestions.value.length - 1)

const progressPct = computed(() => {
  const total = visibleQuestions.value.length
  if (total === 0) return 0
  return Math.round(((currentIndex.value + 1) / total) * 100)
})

watch(
  () => answers.value,
  (nextAnswers) => {
    if (saveAnswersTimer) {
      clearTimeout(saveAnswersTimer)
      saveAnswersTimer = null
    }
    if (backendStatsSyncTimer) {
      clearTimeout(backendStatsSyncTimer)
      backendStatsSyncTimer = null
    }

    saveAnswersTimer = setTimeout(() => {
      saveAnswers(nextAnswers)
      syncCategoryProgress(nextAnswers)
    }, ANSWERS_PERSIST_DEBOUNCE_MS)

    backendStatsSyncTimer = setTimeout(() => {
      void pushNgcStatsToBackend()
    }, BACKEND_STATS_SYNC_DEBOUNCE_MS)
  },
  { deep: true },
)

watch(
  [() => currentCategory.value, () => visibleQuestions.value.map((q) => q.slug).join('|')],
  ([cat]) => {
    if (!cat) {
      currentSlug.value = null
      return
    }

    const list = visibleQuestions.value
    if (list.length === 0) {
      if (currentSlug.value !== null) currentSlug.value = null
      return
    }

    const stillExists = list.some((q) => q.slug === currentSlug.value)
    if (!stillExists) {
      currentSlug.value = getResumeSlug(cat, list)
    }
  },
  { immediate: true },
)

watch(
  () => [currentCategory.value, currentSlug.value] as const,
  ([cat, slug]) => {
    if (!slug) return
    const progress = loadProgress() ?? {}
    if (progress[cat] === slug) return
    saveProgress({ ...progress, [cat]: slug })
  },
  { immediate: true },
)

function saveAndExit() {
  flushLocalPersistence()
  router.push('/questionnaires')
}

function goPrev() {
  if (isFirstQuestion.value) return
  const prevQ = visibleQuestions.value[currentIndex.value - 1]
  if (prevQ) currentSlug.value = prevQ.slug
}

function goNext() {
  if (isLastQuestion.value) return
  const nextQ = visibleQuestions.value[currentIndex.value + 1]
  if (nextQ) currentSlug.value = nextQ.slug
}

function setAnswer(slug: string, v: any) {
  answers.value = { ...answers.value, [slug]: v }
}

function clearAnswer(slug: string) {
  const copy = { ...answers.value }
  delete copy[slug]
  answers.value = copy
}

function getBooleanAnswerValue(q: QuestionRecord): boolean | string | null {
  const raw = answers.value[q.slug]
  if (q.config_json.booleanNative) return normalizeBooleanValue(raw)
  return (raw as string | null) ?? null
}

function setBooleanAnswer(q: QuestionRecord, value: unknown) {
  if (q.config_json.booleanNative) {
    const normalized = normalizeBooleanValue(value)
    if (normalized === null) {
      clearAnswer(q.slug)
      return
    }
    setAnswer(q.slug, normalized)
    return
  }

  setAnswer(q.slug, value)
}

function isMultiSelected(q: QuestionRecord, subSlug: string): boolean {
  const value = (answers.value[q.slug] as Record<string, unknown>)?.[subSlug]
  if (q.config_json.multiValuesAsBoolean) {
    const normalized = normalizeBooleanValue(value)
    return normalized === true
  }
  const normalized = normalizeBooleanValue(value)
  if (normalized !== null) return normalized
  return !!value
}

function getMultiOptionSlugs(q: QuestionRecord): string[] {
  if (!Array.isArray(q.config_json.options)) return []
  return q.config_json.options.map((opt: unknown) => {
    if (typeof opt === 'string') return opt
    const typedOpt = opt as { slug?: string; value?: string }
    return String(typedOpt?.slug ?? typedOpt?.value ?? String(typedOpt))
  })
}

function isMultiNoneSelected(q: QuestionRecord): boolean {
  const selected =
    answers.value[q.slug] &&
    typeof answers.value[q.slug] === 'object' &&
    !Array.isArray(answers.value[q.slug])
      ? (answers.value[q.slug] as Record<string, unknown>)
      : null
  if (!selected) return false

  const optionSlugs = getMultiOptionSlugs(q)
  if (optionSlugs.length === 0) return false

  const hasAnyKey = Object.keys(selected).length > 0
  if (!hasAnyKey) return false

  return optionSlugs.every((slug) => !isMultiSelected(q, slug))
}

function setMultiNone(q: QuestionRecord, enabled: boolean) {
  if (!enabled) {
    clearAnswer(q.slug)
    return
  }

  const optionSlugs = getMultiOptionSlugs(q)
  if (optionSlugs.length === 0) return

  const next: Record<string, unknown> = {}
  for (const optionSlug of optionSlugs) {
    next[optionSlug] = q.config_json.multiValuesAsBoolean ? false : 'non'
  }
  setAnswer(q.slug, next)
}

function toggleMulti(q: QuestionRecord, subSlug: string) {
  const selected: Record<string, unknown> =
    answers.value[q.slug] &&
    typeof answers.value[q.slug] === 'object' &&
    !Array.isArray(answers.value[q.slug])
      ? (answers.value[q.slug] as Record<string, unknown>)
      : {}

  const next = { ...selected }
  if (isMultiSelected(q, subSlug)) delete next[subSlug]
  else next[subSlug] = q.config_json.multiValuesAsBoolean ? true : 'oui'
  if (Object.keys(next).length === 0) clearAnswer(q.slug)
  else setAnswer(q.slug, next)
}

function getMosaicCount(slug: string, subSlug: string): string | number {
  const value = (answers.value[slug] as Record<string, unknown>)?.[subSlug]
  return value === undefined || value === null ? '' : (value as number)
}

function setMosaicCountFromInput(slug: string, subSlug: string, raw: unknown) {
  const counters: Record<string, number> =
    answers.value[slug] &&
    typeof answers.value[slug] === 'object' &&
    !Array.isArray(answers.value[slug])
      ? (answers.value[slug] as Record<string, number>)
      : {}

  if (raw === '' || raw === null || raw === undefined) {
    const next = { ...counters }
    delete next[subSlug]
    if (Object.keys(next).length === 0) clearAnswer(slug)
    else setAnswer(slug, next)
    return
  }

  const n = Number(raw)
  if (!Number.isFinite(n)) return
  setAnswer(slug, { ...counters, [subSlug]: n })
}

onMounted(async () => {
  isLoading.value = true
  engineError.value = null
  restoreWarn = silenceNoisyWarnings()
  syncCategoryProgress(answers.value)

  try {
    const rules = await fetchRules()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    engine.value = new Engine(rules as any)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    allQuestions.value = buildQuestionnaire(engine.value as any)

    const normalized = normalizeStoredAnswersByQuestionType(answers.value, allQuestions.value)
    if (normalized !== answers.value) answers.value = normalized
    void pushNgcStatsToBackend()
  } catch (e: unknown) {
    console.error(e)
    engineError.value = (e as Error)?.message ?? String(e)
  } finally {
    isLoading.value = false
  }
})

onUnmounted(() => {
  flushLocalPersistence()

  if (setSituationTimer) {
    clearTimeout(setSituationTimer)
    setSituationTimer = null
  }
  if (backendStatsSyncTimer) {
    clearTimeout(backendStatsSyncTimer)
    backendStatsSyncTimer = null
  }

  if (restoreWarn) {
    restoreWarn()
    restoreWarn = null
  }
})
</script>

<template>
  <div class="dashboard-wrapper">
    <Header
      title="Questionnaire"
      :subtitle="categoryTitle"
      :showResumeBtn="true"
      @resumeLater="saveAndExit"
    />

    <div class="scrollable-area">
      <div v-if="isLoading" class="loading-state">Chargement...</div>

      <div v-else-if="isError" class="error-state">
        <h2>Oups !</h2>
        <p>Impossible de charger le questionnaire "{{ categoryTitle }}".</p>
        <button class="nav-btn prev-btn" @click="saveAndExit">Retour au menu</button>
        <pre v-if="engineError" style="white-space: pre-wrap; margin-top: 12px">{{
          engineError
        }}</pre>
      </div>

      <div v-else class="question-container">
        <h3 class="question-counter">
          Bilan : {{ bilan.val ?? '—' }} {{ bilan.unit }} • Question
          {{ visibleQuestions.length === 0 ? '—' : currentIndex + 1 }} sur
          {{ visibleQuestions.length }}
        </h3>

        <div class="progress-section">
          <ProgressBar :value="progressPct" :showLabel="false" />
        </div>

        <div v-if="!currentQuestion" class="error-state" style="margin-top: 40px">
          Aucune question a afficher (dependances non satisfaites).
        </div>

        <div v-else>
          <h1 class="question-text">{{ currentQuestion!.question }}</h1>

          <div class="answers-area">
            <div v-if="currentQuestion!.type_widget === 'BOOLEEN'">
              <v-radio-group
                :model-value="getBooleanAnswerValue(currentQuestion!)"
                @update:model-value="(v: unknown) => setBooleanAnswer(currentQuestion!, v)"
              >
                <v-radio
                  label="Oui"
                  :value="currentQuestion!.config_json.booleanNative ? true : 'oui'"
                  color="#679436"
                />
                <v-radio
                  label="Non"
                  :value="currentQuestion!.config_json.booleanNative ? false : 'non'"
                  color="#679436"
                />
              </v-radio-group>
            </div>

            <div v-else-if="currentQuestion!.type_widget === 'CHOIX_UNIQUE'">
              <v-radio-group
                :model-value="answers[currentQuestion!.slug] ?? null"
                @update:model-value="(v: unknown) => setAnswer(currentQuestion!.slug, v)"
              >
                <v-radio
                  v-for="opt in (currentQuestion!.config_json.options as Option[]) ?? []"
                  :key="opt.value ?? String(opt)"
                  :label="opt.label ?? String(opt)"
                  :value="opt.value ?? String(opt)"
                  color="#679436"
                />
              </v-radio-group>
            </div>

            <div v-else-if="currentQuestion!.type_widget === 'CHOIX_MULTIPLE'">
              <div
                v-for="opt in (currentQuestion!.config_json.options as Option[]) ?? []"
                :key="opt.slug ?? opt.value ?? String(opt)"
              >
                <v-checkbox
                  :label="opt.label ?? String(opt)"
                  :model-value="
                    isMultiSelected(currentQuestion!, opt.slug ?? opt.value ?? String(opt))
                  "
                  color="#679436"
                  @update:model-value="
                    () => toggleMulti(currentQuestion!, opt.slug ?? opt.value ?? String(opt))
                  "
                />
              </div>
              <div v-if="currentQuestion!.config_json.noneOptionLabel">
                <v-checkbox
                  :label="currentQuestion!.config_json.noneOptionLabel"
                  :model-value="isMultiNoneSelected(currentQuestion!)"
                  color="#679436"
                  @update:model-value="(v: any) => setMultiNone(currentQuestion!, !!v)"
                />
              </div>
            </div>

            <div v-else-if="currentQuestion!.type_widget === 'NOMBRE'">
              <v-text-field
                type="number"
                placeholder="ex : 0"
                :label="
                  currentQuestion!.config_json.unit ? `(${currentQuestion!.config_json.unit})` : ''
                "
                :model-value="answers[currentQuestion!.slug] ?? ''"
                @update:model-value="
                  (v: any) => setAnswer(currentQuestion!.slug, v === '' ? '' : Number(v))
                "
              />
              <div style="opacity: 0.7; font-size: 0.9rem">
                <span v-if="currentQuestion!.config_json.min !== undefined"
                  >min {{ currentQuestion!.config_json.min }}</span
                >
                <span
                  v-if="
                    currentQuestion!.config_json.min !== undefined &&
                    currentQuestion!.config_json.max !== undefined
                  "
                >
                  ·
                </span>
                <span v-if="currentQuestion!.config_json.max !== undefined"
                  >max {{ currentQuestion!.config_json.max }}</span
                >
              </div>

              <div v-if="numberSuggestionEntries.length > 0" class="suggestions-wrap">
                <div class="suggestions-label">Suggestions :</div>
                <div class="suggestions-row">
                  <button
                    v-for="[label, preset] in numberSuggestionEntries"
                    :key="String(label)"
                    class="suggestion-btn"
                    @click="applyNumberSuggestion(currentQuestion!.slug, preset)"
                  >
                    {{ label }}
                  </button>
                </div>
              </div>
            </div>

            <div v-else-if="currentQuestion!.type_widget === 'COMPTEUR'">
              <div
                v-for="(opt, idx) in currentQuestion!.config_json.mosaique?.options ?? []"
                :key="idx"
                style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px"
              >
                <div style="flex: 1; display: flex; gap: 8px; align-items: center">
                  <span v-if="opt.icone">{{ opt.icone }}</span>
                  <span>{{ getMosaicDisplayLabel(opt) }}</span>
                </div>

                <v-text-field
                  type="number"
                  placeholder="ex : 0"
                  style="max-width: 140px"
                  :model-value="
                    getMosaicCount(
                      currentQuestion!.slug,
                      getMosaicSubSlug(currentQuestion!.slug, opt),
                    )
                  "
                  @update:model-value="
                    (v: unknown) =>
                      setMosaicCountFromInput(
                        currentQuestion!.slug,
                        getMosaicSubSlug(currentQuestion!.slug, opt),
                        v,
                      )
                  "
                />
              </div>

              <div v-if="counterSuggestionEntries.length > 0" class="suggestions-wrap">
                <div class="suggestions-label">Suggestions :</div>
                <div class="suggestions-row">
                  <button
                    v-for="[label, preset] in counterSuggestionEntries"
                    :key="String(label)"
                    class="suggestion-btn"
                    @click="applyCounterSuggestion(currentQuestion!, preset)"
                  >
                    {{ label }}
                  </button>
                </div>
              </div>
            </div>

            <div v-else class="error-state">
              Type de question non gere : {{ currentQuestion!.type_widget }}
            </div>
          </div>

          <div class="navigation-buttons">
            <button v-if="!isFirstQuestion" class="nav-btn prev-btn" @click="goPrev">
              &lt; Question precedente
            </button>
            <div v-else></div>

            <div style="display: flex; gap: 10px; align-items: center">
              <button class="nav-btn reset-btn" @click="clearAnswer(currentQuestion!.slug)">
                Effacer
              </button>
              <button class="nav-btn next-btn" @click="isLastQuestion ? saveAndExit() : goNext()">
                {{ isLastQuestion ? 'Terminer' : 'Question suivante >' }}
              </button>
            </div>
          </div>

          <div class="message">
            <p>Toute non reponse vaudra la moyenne nationale.</p>
          </div>

          <div
            v-if="bilan.err"
            style="margin-top: 16px; padding: 12px; border: 1px solid #f99; border-radius: 10px"
          >
            <strong>Erreur Publicodes</strong>
            <pre style="white-space: pre-wrap; margin: 8px 0 0">{{
              String((bilan.err as Error)?.message ?? bilan.err)
            }}</pre>
          </div>

          <div
            v-if="situationError"
            style="margin-top: 16px; padding: 12px; border: 1px solid #f99; border-radius: 10px"
          >
            <strong>Erreur situation</strong>
            <pre style="white-space: pre-wrap; margin: 8px 0 0"
              >{{ String((situationError as Error)?.message ?? situationError) }}
            </pre>
          </div>
        </div>
      </div>
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
  margin-bottom: 10px;
  font-size: 1.1rem;
}

.question-text {
  text-align: center;
  font-size: 1.8rem;
  margin-bottom: 30px;
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
  padding: 18px 16px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
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
  margin: 10px 0 20px;
  padding: 0 10px;
}

.message {
  margin-top: 30px;
  font-size: 0.9rem;
  font-style: italic;
  color: #888;
  text-align: center;
}

.suggestions-wrap {
  margin-top: 10px;
}

.suggestions-label {
  font-size: 0.85rem;
  color: #666;
  margin-bottom: 6px;
}

.suggestions-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.suggestion-btn {
  border: 1px solid #d8e3cc;
  background: #f7fbf2;
  color: #3e5a27;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 0.8rem;
  cursor: pointer;
}
</style>
