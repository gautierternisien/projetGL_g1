/* eslint-disable @typescript-eslint/no-explicit-any */

import type Engine from 'publicodes'

export type Category = 'logement' | 'transport' | 'alimentation' | 'divers'

// ---- mêmes constantes que ton script ----
export const TARGET_QUESTIONS: Array<[slug: string, icon: string, category: Category]> = [
  ['logement . type', '🏠', 'logement'],
  ['logement . surface', '📏', 'logement'],
  ['logement . propriétaire', '🔑', 'logement'],
  ['logement . habitants', '👥', 'logement'],
  ['logement . chauffage', '🔥', 'logement'],
  ['logement . chauffage . précision consommation . ressenti', '🌡️', 'logement'],
  ['transport . voiture . utilisateur', '🚗', 'transport'],
  ['transport . voiture . km', '⛽', 'transport'],
  ['transport . voiture . motorisation', '🔧', 'transport'],
  ['transport . mobilité douce', '🚲', 'transport'],
  ['transport . avion . usager', '✈️', 'transport'],
  ['transport . avion . vols annuels . heures court courrier . saisie', '🕒', 'transport'],
  ['transport . avion . vols annuels . heures moyen et long courrier . saisie', '🕒', 'transport'],
  ['alimentation . plats', '🍽️', 'alimentation'],
  ['alimentation . boisson . eau en bouteille . consommateur', '💧', 'alimentation'],
  ['divers . numérique . appareils', '💻', 'divers'],
  ['divers . textile . volume', '🛍️', 'divers'],
  ['logement . âge', '🎂', 'logement'],
  ['logement . vacances', '🏖️', 'logement'],
  ['alimentation . petit déjeuner . type', '🥐', 'alimentation'],
  ['alimentation . local . consommation', '🌍', 'alimentation'],
  ['alimentation . de saison . consommation', '🍓', 'alimentation'],
  ['alimentation . boisson . chaude', '☕', 'alimentation'],
  ['alimentation . boisson . sucrées . litres', '🥤', 'alimentation'],
  ['alimentation . boisson . alcool . litres', '🍷', 'alimentation'],
  ['alimentation . déchets . quantité jetée', '🗑️', 'alimentation'],
  ['transport . voiture . gabarit', '🚙', 'transport'],
  ['transport . voiture . thermique . carburant', '⛽', 'transport'],
  ['divers . animaux domestiques . empreinte', '🐶', 'divers'],
  ['divers . loisirs . culture', '🎭', 'divers'],
  ['divers . loisirs . sports', '⚽', 'divers'],
  ['divers . numérique . appareils . renouvellement téléphone', '📱', 'divers'],
  ['divers . tabac . consommation par semaine', '🚬', 'divers'],
]

export type DependencyRule =
  | { key: string; value: string; type: 'EQUAL' }
  | { key: string; value: string[]; type: 'IN' }

export const dependancies: Record<string, DependencyRule[]> = {
  'transport . voiture . km': [
    {
      key: 'transport . voiture . utilisateur',
      value: ['propriétaire', 'régulier non propriétaire', 'non régulier'],
      type: 'IN',
    },
  ],

  'transport . voiture . motorisation': [
    {
      key: 'transport . voiture . utilisateur',
      value: ['propriétaire', 'régulier non propriétaire'],
      type: 'IN',
    },
  ],

  'transport . avion . vols annuels . heures court courrier . saisie': [
    { key: 'transport . avion . usager', value: ['fréquemment', 'occasionnellement'], type: 'IN' },
  ],
  'transport . avion . vols annuels . heures moyen et long courrier . saisie': [
    { key: 'transport . avion . usager', value: ['fréquemment', 'occasionnellement'], type: 'IN' },
  ],

  'transport . voiture . thermique . carburant': [
    { key: 'transport . voiture . motorisation', value: 'thermique', type: 'EQUAL' },
    { key: 'transport . voiture . utilisateur', value: 'propriétaire', type: 'EQUAL' },
  ],

  'transport . voiture . gabarit': [
    {
      key: 'transport . voiture . utilisateur',
      value: ['propriétaire', 'régulier non propriétaire'],
      type: 'IN',
    },
  ],
}

export const limites: Record<string, { min: number; max: number }> = {
  'alimentation . plats': { min: 0, max: 14 },
}

export type WidgetType = 'CHOIX_UNIQUE' | 'CHOIX_MULTIPLE' | 'COMPTEUR' | 'NOMBRE' | 'BOOLEEN'

export type MosaicOption = {
  titre?: string
  title?: string
  label?: string
  icone?: string
  valeur?: string
  dottedName?: string
  name?: string
}

export type QuestionConfig = {
  options?: any[]
  min?: number
  max?: number
  defaultValue?: any
  unit?: string
  description?: string
  note?: string
  suggestions?: any
  dependances?: DependencyRule[]
  noneOptionLabel?: string
  // true for native Publicodes booleans (no explicit ['oui','non'] possibilities)
  booleanNative?: boolean
  // true when multi-selection options are boolean ".present" flags
  multiValuesAsBoolean?: boolean
  mosaique?: {
    options?: MosaicOption[]
    suggestions?: any
  }
}

export type QuestionRecord = {
  slug: string
  categorie_empreinte: Category
  question: string
  icone: string | null
  type_widget: WidgetType
  config_json: QuestionConfig
  ordre_affichage: number
}

/** Déduit le type de widget à afficher à partir de la règle Publicodes parsée. */
export function determineWidgetType(rule: any): WidgetType {
  const raw = rule?.rawNode ?? {}

  if (raw.mosaique) return raw.mosaique.type === 'selection' ? 'CHOIX_MULTIPLE' : 'COMPTEUR'

  if (Array.isArray(raw['une possibilité'])) {
    const options = raw['une possibilité'] as any[]
    if (options.includes('oui') && options.includes('non')) return 'BOOLEEN'
    return 'CHOIX_UNIQUE'
  }

  if (raw.plancher !== undefined || raw.plafond !== undefined || raw.unité !== undefined) return 'NOMBRE'
  return 'BOOLEEN'
}

/** Construit la config UI (options/contraintes/suggestions/dépendances) à partir de la règle. */
export function buildConfigJson(slug: string, rule: any, widgetType: WidgetType): QuestionConfig {
  const raw = rule?.rawNode ?? {}
  const config: QuestionConfig = {}
  const hasExplicitPossibilities = Array.isArray(raw['une possibilité'])

  if (Array.isArray(rule?.possibilities) && rule.possibilities.length > 0) {
    const normalized = rule.possibilities
      .map((p: any) => {
        if (typeof p === 'string') return { label: p, value: p }

        const label =
          p.title ??
          p.label ??
          p.name ??
          p.acronym ??
          (typeof p.dottedName === 'string' ? p.dottedName.split(' . ').slice(-1)[0] : undefined) ??
          String(p.dottedName ?? p)

        const value = p.dottedName ?? p.name ?? p.value ?? label
        return { label: String(label), value: String(value) }
      })
      .filter(Boolean)

    if (normalized.length > 0) config.options = normalized
  }

  if (raw.mosaique) {
    config.mosaique = {
      options: raw.mosaique.options,
      suggestions: raw.mosaique.suggestions,
    }

    if (widgetType === 'CHOIX_MULTIPLE') {
      const noneLabel = raw.mosaique['option aucun']
      if (typeof noneLabel === 'string' && noneLabel.trim().length > 0) config.noneOptionLabel = noneLabel.trim()
      else config.noneOptionLabel = 'Aucun'
    }

    if (widgetType === 'CHOIX_MULTIPLE' && Array.isArray(raw.mosaique.options)) {
      config.options = raw.mosaique.options.map((opt: any) => {
        if (typeof opt === 'string') {
          const fullSlug = resolveMosaicOptionSlug(slug, opt)
          return { label: prettifyPresentLabel(opt), slug: fullSlug }
        }

        const candidate = opt?.dottedName ?? opt?.valeur ?? opt?.name
        const rawStr = typeof candidate === 'string' ? candidate : String(opt)
        const fullSlug = resolveMosaicOptionSlug(slug, rawStr)

        const rawLabel = String(opt?.titre ?? opt?.title ?? opt?.label ?? rawStr)
        return { label: prettifyPresentLabel(rawLabel), slug: fullSlug }
      })
    }
  }

  if (!config.options && Array.isArray(raw['une possibilité'])) config.options = raw['une possibilité']
  if (widgetType === 'BOOLEEN' && !config.options) config.options = ['oui', 'non']
  if (widgetType === 'BOOLEEN') config.booleanNative = !hasExplicitPossibilities

  if (widgetType === 'CHOIX_MULTIPLE' && Array.isArray(config.options)) {
    const slugs = config.options.map((opt: any) => String(opt?.slug ?? opt?.value ?? '')).filter(Boolean)
    config.multiValuesAsBoolean =
      slugs.length > 0 &&
      slugs.every((s: string) =>
        s
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '')
          .toLowerCase()
          .endsWith('. present'),
      )
  }

  if (raw.plancher !== undefined) config.min = raw.plancher
  if (raw.plafond !== undefined) config.max = raw.plafond
  if (raw['par défaut'] !== undefined) config.defaultValue = raw['par défaut']
  if (raw.unité) config.unit = raw.unité

  if (limites[slug]) {
    config.min = limites[slug].min
    config.max = limites[slug].max
  }

  if (raw.description) config.description = raw.description
  if (raw.note) config.note = raw.note

  if (dependancies[slug]) config.dependances = dependancies[slug]

  if (raw.mosaique?.suggestions) config.suggestions = raw.mosaique.suggestions
  else if (raw.suggestions) config.suggestions = raw.suggestions

  return config
}

/** Fabrique la liste ordonnée des questions à afficher à partir des règles parsées. */
export function buildQuestionnaire(engine: Engine): QuestionRecord[] {
  const parsedRules = (engine as Engine).getParsedRules()
  const records: QuestionRecord[] = []

  TARGET_QUESTIONS.forEach(([slug, icon, category], index) => {
    const rule = (parsedRules as any)[slug]
    if (!rule) return

    const widgetType = determineWidgetType(rule)
    const raw = rule.rawNode ?? {}

    records.push({
      slug,
      categorie_empreinte: category,
      question: raw.question || raw.titre || slug,
      icone: icon || (typeof raw.icone === 'string' ? raw.icone : null),
      type_widget: widgetType,
      config_json: buildConfigJson(slug, rule, widgetType),
      ordre_affichage: index + 1,
    })
  })

  return records
}

/** Détermine si une question doit être visible (dépendances sur les réponses utilisateur). */
export function isQuestionVisible(q: QuestionRecord, answers: Record<string, any>, _engine?: Engine | null): boolean {
  const deps = q.config_json.dependances
  if (!deps || deps.length === 0) return true

  return deps.every((d) => {
    const actual = normalizeDependencyValue(answers[d.key])
    if (actual === undefined) return false
    if (d.type === 'EQUAL') return actual === normalizeDependencyValue(d.value)
    if (d.type === 'IN') return d.value.map(normalizeDependencyValue).includes(actual)
    return true
  })
}

/** Normalise une valeur (string/quoted/bool) pour la comparaison de dépendances. */
function normalizeDependencyValue(value: any) {
  if (value === undefined || value === null || value === '') return undefined
  if (typeof value === 'boolean') return value ? 'oui' : 'non'
  if (typeof value === 'number') return value
  if (typeof value === 'string') {
    const trimmed = value.trim()
    const unquoted =
      trimmed.length >= 2 && trimmed.startsWith("'") && trimmed.endsWith("'") ? trimmed.slice(1, -1) : trimmed
    return unquoted
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
  }
  return value
}

/** Transforme un libellé NGC (ex: "électricité . présent") en libellé UI plus propre. */
function prettifyPresentLabel(s: string): string {
  const withoutPresent = s.replace(/\s*\.\s*présent\s*$/i, '').trim()
  if (withoutPresent.includes('photovoltaique')) return 'électricité photovoltaïque'
  return withoutPresent.split(' . ').slice(-1)[0]
}

/** Construit le slug Publicodes complet pour une option de mosaïque, relative ou absolue. */
function resolveMosaicOptionSlug(parentSlug: string, opt: string): string {
  const clean = opt.trim()

  const isAbsolute =
    clean.startsWith('logement .') ||
    clean.startsWith('transport .') ||
    clean.startsWith('alimentation .') ||
    clean.startsWith('divers .') ||
    clean.startsWith('ui .')

  if (isAbsolute) return clean
  if (clean.startsWith(parentSlug + ' .') || clean === parentSlug) return clean
  return `${parentSlug} . ${clean}`
}

