/* eslint-disable @typescript-eslint/no-explicit-any */
import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import type Engine from 'publicodes'
import type { Category, QuestionRecord } from '@/lib/ngc/questionnaire'
import { isQuestionVisible } from '@/lib/ngc/questionnaire'
import { loadAnswers, saveAnswers, loadProgress, saveProgress } from '@/lib/ngc/answersStorage'

function toPublicodesValue(v: any) {
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

function flattenAnswers(answers: Record<string, any>) {
  const flat: Record<string, any> = {}
  for (const [k, v] of Object.entries(answers)) {
    if (v && typeof v === 'object' && !Array.isArray(v)) {
      const keys = Object.keys(v)
      const looksLikeSlugs = keys.some((x) => x.includes(' . '))
      if (looksLikeSlugs) {
        for (const [subK, subV] of Object.entries(v)) flat[subK] = subV
        continue
      }
    }
    flat[k] = v
  }
  return flat
}

export const useNgcQuestionnaireStore = defineStore('ngcQuestionnaire', () => {
  const engine = ref<Engine | null>(null)
  const questions = ref<QuestionRecord[]>([])

  const answers = ref<Record<string, any>>(loadAnswers() ?? {})
  const progress = ref<Partial<Record<Category, string>>>(loadProgress() ?? {})
  const category = ref<Category | null>(null)
  const currentSlug = ref<string | null>(null)

  // persist answers
  watch(
    answers,
    (v) => saveAnswers(v),
    { deep: true }
  )

  // persist currentSlug per category
  watch([category, currentSlug], ([cat, slug]) => {
    if (!cat || !slug) return
    const next = { ...(progress.value ?? {}), [cat]: slug }
    progress.value = next
    saveProgress(next)
  })

  const situation = computed(() => {
    const flat = flattenAnswers(answers.value)
    return Object.fromEntries(
      Object.entries(flat)
        .map(([k, v]) => [k, toPublicodesValue(v)] as const)
        .filter(([, v]) => v !== undefined)
    )
  })

  const total = computed(() => {
    if (!engine.value) return { val: null as number | null, unit: '', err: null as any, raw: null as any }
    try {
      engine.value.setSituation(situation.value)
      const res: any = engine.value.evaluate('bilan')
      const rawVal = typeof res?.nodeValue === 'number' ? res.nodeValue : null
      return {
        val: rawVal === null ? null : Math.round(rawVal),
        unit: res?.unit?.numerators?.join('.') ?? '',
        err: null,
        raw: res,
      }
    } catch (e: any) {
      return { val: null, unit: '', err: e, raw: null }
    }
  })

  const visibleQuestions = computed(() => {
    const base = category.value
      ? questions.value.filter((q) => q.categorie_empreinte === category.value)
      : questions.value

    return base.filter((q) => isQuestionVisible(q, answers.value, engine.value))
  })

  // IMPORTANT: éviter le “maximum update depth exceeded”
  // => on ne fait PAS un useEffect qui dépend de visibleQuestions et currentSlug et qui fait setCurrentSlug en boucle.
  // Ici, on “reconcilie” de manière déterministe via une watch sur [category, visibleQuestions.length].
  watch(
    [category, () => visibleQuestions.value.map((q) => q.slug).join('|')], // signature stable
    ([cat]) => {
      if (!cat) {
        currentSlug.value = null
        return
      }
      const list = visibleQuestions.value
      if (list.length === 0) {
        currentSlug.value = null
        return
      }

      const saved = progress.value?.[cat]
      const keep =
        (saved && list.some((q) => q.slug === saved) && saved) ||
        (currentSlug.value && list.some((q) => q.slug === currentSlug.value) && currentSlug.value) ||
        list[0].slug

      currentSlug.value = keep
    },
    { immediate: true }
  )

  const currentIndex = computed(() => {
    const list = visibleQuestions.value
    if (list.length === 0) return 0
    if (!currentSlug.value) return 0
    const idx = list.findIndex((q) => q.slug === currentSlug.value)
    return idx >= 0 ? idx : 0
  })

  const currentQuestion = computed(() => visibleQuestions.value[currentIndex.value])

  const progressVal = computed(() => (visibleQuestions.value.length ? currentIndex.value + 1 : 0))
  const progressMax = computed(() => (visibleQuestions.value.length ? visibleQuestions.value.length : 1))
  const progressPct = computed(() =>
    visibleQuestions.value.length ? Math.round((progressVal.value / progressMax.value) * 100) : 0
  )

  function setEngine(e: Engine) {
    engine.value = e
  }

  function setQuestions(qs: QuestionRecord[]) {
    questions.value = qs
  }

  function setCategory(cat: Category) {
    category.value = cat
  }

  function setAnswer(slug: string, v: any) {
    answers.value = { ...answers.value, [slug]: v }
  }

  function clearAnswer(slug: string) {
    const copy = { ...answers.value }
    delete copy[slug]
    answers.value = copy
  }

  function goPrev() {
    if (currentIndex.value <= 0) return
    currentSlug.value = visibleQuestions.value[currentIndex.value - 1].slug
  }

  function goNext() {
    if (currentIndex.value >= visibleQuestions.value.length - 1) return
    currentSlug.value = visibleQuestions.value[currentIndex.value + 1].slug
  }

  return {
    engine,
    questions,
    answers,
    progress,
    category,
    currentSlug,

    situation,
    total,

    visibleQuestions,
    currentIndex,
    currentQuestion,

    progressVal,
    progressMax,
    progressPct,

    setEngine,
    setQuestions,
    setCategory,
    setAnswer,
    clearAnswer,
    goPrev,
    goNext,
  }
})
