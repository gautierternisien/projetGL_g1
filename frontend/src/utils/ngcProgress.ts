/* eslint-disable @typescript-eslint/no-explicit-any */
import { loadAnswers, type Category } from '@/lib/ngc/answersStorage'
import { dependancies, TARGET_QUESTIONS, type DependencyRule } from '@/lib/ngc/questionnaire'

function isAnswerFilled(value: any): boolean {
  if (value === undefined || value === null || value === '') return false
  if (Array.isArray(value)) return value.some(isAnswerFilled)
  if (typeof value === 'object') {
    const values = Object.values(value)
    if (values.length === 0) return false
    return values.some(isAnswerFilled)
  }
  return true
}

function normalizeDependencyValue(value: any) {
  if (value === undefined || value === null || value === '') return undefined
  if (typeof value === 'boolean') return value ? 'oui' : 'non'
  if (typeof value === 'number') return value
  if (typeof value === 'string') {
    const trimmed = value.trim()
    const unquoted =
      trimmed.length >= 2 && trimmed.startsWith("'") && trimmed.endsWith("'")
        ? trimmed.slice(1, -1)
        : trimmed
    return unquoted
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
  }
  return value
}

function isQuestionRequired(slug: string, answers: Record<string, any>): boolean {
  const deps = dependancies[slug]
  if (!deps || deps.length === 0) return true

  return deps.every((d: DependencyRule) => {
    const actual = normalizeDependencyValue(answers[d.key])
    if (actual === undefined) return false

    if (d.type === 'EQUAL') return actual === normalizeDependencyValue(d.value)
    if (d.type === 'IN') return d.value.map(normalizeDependencyValue).includes(actual)
    return true
  })
}

export function computeCategoryProgressFromAnswers(
  answers: Record<string, any>,
): Record<Category, number> {
  const totals: Record<Category, number> = {
    transport: 0,
    logement: 0,
    alimentation: 0,
    divers: 0,
  }

  const answered: Record<Category, number> = {
    transport: 0,
    logement: 0,
    alimentation: 0,
    divers: 0,
  }

  for (const [slug, , category] of TARGET_QUESTIONS) {
    if (!isQuestionRequired(slug, answers)) continue

    totals[category] += 1
    if (isAnswerFilled(answers[slug])) answered[category] += 1
  }

  return {
    transport: totals.transport === 0 ? 0 : Math.round((answered.transport / totals.transport) * 100),
    logement: totals.logement === 0 ? 0 : Math.round((answered.logement / totals.logement) * 100),
    alimentation: totals.alimentation === 0 ? 0 : Math.round((answered.alimentation / totals.alimentation) * 100),
    divers: totals.divers === 0 ? 0 : Math.round((answered.divers / totals.divers) * 100),
  }
}

export function loadCategoryProgressFromLocalAnswers(): Record<Category, number> {
  const answers = loadAnswers() ?? {}
  return computeCategoryProgressFromAnswers(answers)
}
