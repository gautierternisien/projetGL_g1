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

type OptionLabelMap = Record<string, string>

function normalizeOptionKey(value: string): string {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[-–—]/g, ' ')
    .replace(/[’]/g, "'")
    .toLowerCase()
    .trim()
    .replace(/\s+/g, ' ')
}

function sentenceCase(value: string): string {
  const trimmed = value.trim()
  if (!trimmed) return trimmed
  return trimmed.charAt(0).toUpperCase() + trimmed.slice(1)
}

function humanizeOptionLabel(raw: string): string {
  const label = sentenceCase(raw.trim().replace(/\s+/g, ' '))
  const normalized = normalizeOptionKey(label)

  if (normalized === 'pac') return 'Pompe à chaleur (PAC)'
  if (normalized === 'vae') return 'Vélo à assistance électrique (VAE)'
  if (normalized === 'vul') return 'VUL (utilitaire)'
  if (normalized === 'suv') return 'SUV'

  return label
}

const GLOBAL_OPTION_LABEL_OVERRIDES: OptionLabelMap = {
  [normalizeOptionKey('jamais')]: 'Jamais',
  [normalizeOptionKey('parfois')]: 'Parfois',
  [normalizeOptionKey('souvent')]: 'Souvent',
  [normalizeOptionKey('occasionnellement')]: 'Occasionnellement',
  [normalizeOptionKey('fréquemment')]: 'Fréquemment',
  [normalizeOptionKey('oui toujours')]: 'Oui, toujours',
  [normalizeOptionKey('aucun')]: 'Aucun',
  [normalizeOptionKey('non concerné')]: 'Non concerné',
  [normalizeOptionKey('non concerne')]: 'Non concerné',
  [normalizeOptionKey('non-concerné')]: 'Non concerné',
  [normalizeOptionKey('non-concerne')]: 'Non concerné',
}

const OPTION_LABEL_OVERRIDES_BY_SLUG: Record<string, OptionLabelMap> = {
  [normalizeOptionKey('transport . voiture . utilisateur')]: {
    [normalizeOptionKey('propriétaire')]: 'Régulièrement avec ma propre voiture',
    [normalizeOptionKey('régulier non propriétaire')]:
      'Régulièrement mais pas avec ma propre voiture',
    [normalizeOptionKey('non régulier')]: 'Pas souvent',
    [normalizeOptionKey('jamais')]: 'Jamais',
  },
  [normalizeOptionKey('transport . avion . usager')]: {
    [normalizeOptionKey('jamais')]: 'Jamais',
    [normalizeOptionKey('occasionnellement')]: 'Entre 1 et 5 fois',
    [normalizeOptionKey('fréquemment')]: 'Plus de 5 fois',
  },
  [normalizeOptionKey('transport . voiture . motorisation')]: {
    [normalizeOptionKey('thermique')]: 'Thermique (essence/diesel)',
    [normalizeOptionKey('électrique')]: 'Électrique',
    [normalizeOptionKey('hybride non rechargeable')]: 'Hybride non rechargeable',
    [normalizeOptionKey('hybride rechargeable')]: 'Hybride rechargeable',
  },
  [normalizeOptionKey('transport . voiture . gabarit')]: {
    [normalizeOptionKey('petite')]: 'Petite citadine',
    [normalizeOptionKey('moyenne')]: 'Voiture moyenne',
    [normalizeOptionKey('berline')]: 'Berline',
    [normalizeOptionKey('suv')]: 'SUV / 4x4',
    [normalizeOptionKey('vul')]: 'Utilitaire (VUL)',
  },
  [normalizeOptionKey('transport . voiture . thermique . carburant')]: {
    [normalizeOptionKey('gazole B7 ou B10')]: 'Diesel (B7/B10)',
    [normalizeOptionKey('essence E5 ou E10')]: 'Essence (E5/E10)',
    [normalizeOptionKey('essence E85')]: 'Superéthanol E85',
    [normalizeOptionKey('GPL')]: 'GPL',
  },
  [normalizeOptionKey('transport . mobilité douce')]: {
    [normalizeOptionKey('vélo')]: 'Vélo classique',
    [normalizeOptionKey('vae')]: 'Vélo à assistance électrique (VAE)',
    [normalizeOptionKey('autres véhicules à moteur')]:
      'Trottinette et autres véhicules électriques',
  },
  [normalizeOptionKey('logement . type')]: {
    [normalizeOptionKey('maison')]: 'Maison',
    [normalizeOptionKey('appartement')]: 'Appartement',
    [normalizeOptionKey('autre')]: 'Autre',
  },
  [normalizeOptionKey('logement . propriétaire')]: {
    [normalizeOptionKey('propriétaire')]: 'Propriétaire',
    [normalizeOptionKey('locataire')]: 'Locataire',
    [normalizeOptionKey('hébergé')]: 'Hébergé·e à titre gratuit',
  },
  [normalizeOptionKey('logement . âge')]: {
    [normalizeOptionKey('très récent')]: 'Très récent (moins de 10 ans)',
    [normalizeOptionKey('récent')]: 'Récent (10 à 50 ans)',
    [normalizeOptionKey('ancien')]: 'Ancien (plus de 50 ans)',
  },
  [normalizeOptionKey('logement . chauffage . précision consommation . ressenti')]: {
    [normalizeOptionKey('passoire thermique')]: "Je chauffe mais j'ai froid",
    [normalizeOptionKey('moyen')]: 'Je chauffe normalement',
    [normalizeOptionKey('confortable')]: 'Je chauffe peu, il fait bon naturellement',
  },
  [normalizeOptionKey('logement . vacances')]: {
    [normalizeOptionKey('hotel')]: 'Hôtel',
    [normalizeOptionKey('camping')]: 'Camping',
    [normalizeOptionKey('auberge de jeunesse')]: 'Auberge de jeunesse',
    [normalizeOptionKey('locations')]: 'Location',
    [normalizeOptionKey('famille ou amis')]: 'Chez la famille ou des amis',
    [normalizeOptionKey('échange')]: 'Échange de maison',
    [normalizeOptionKey('résidence secondaire')]: 'Résidence secondaire',
    [normalizeOptionKey('croisière')]: 'Croisière',
  },
  [normalizeOptionKey('alimentation . petit déjeuner . type')]: {
    [normalizeOptionKey('continental')]: 'Pain ou viennoiserie',
    [normalizeOptionKey('lait céréales')]: 'Produit laitier et céréales',
    [normalizeOptionKey('britannique')]: 'Salé (type britannique)',
    [normalizeOptionKey('végétalien')]: 'Fruits / végétal',
    [normalizeOptionKey('aucun')]: 'Je ne prends pas de petit-déjeuner',
  },
  [normalizeOptionKey('alimentation . local . consommation')]: {
    [normalizeOptionKey('jamais')]: 'Jamais',
    [normalizeOptionKey('parfois')]: 'Parfois',
    [normalizeOptionKey('souvent')]: 'Souvent',
    [normalizeOptionKey('oui toujours')]: 'Toujours',
  },
  [normalizeOptionKey('alimentation . de saison . consommation')]: {
    [normalizeOptionKey('jamais')]: 'Jamais',
    [normalizeOptionKey('parfois')]: 'Parfois',
    [normalizeOptionKey('souvent')]: 'Souvent',
    [normalizeOptionKey('oui toujours')]: 'Toujours',
  },
  [normalizeOptionKey('alimentation . déchets . quantité jetée')]: {
    [normalizeOptionKey('base')]: 'Je jette sans faire attention',
    [normalizeOptionKey('réduction')]: 'Je limite mes déchets',
    [normalizeOptionKey('zéro déchet')]: 'Je suis zéro déchet',
  },
  [normalizeOptionKey('divers . textile . volume')]: {
    [normalizeOptionKey('minimum')]: 'Le strict minimum',
    [normalizeOptionKey('renouvellement occasionnel')]: 'Renouvellement occasionnel',
    [normalizeOptionKey('accro au shopping')]: 'Accro au shopping',
  },
  [normalizeOptionKey('divers . numérique . appareils . renouvellement téléphone')]: {
    [normalizeOptionKey('faible')]: '0 à 1 fois',
    [normalizeOptionKey('moyen')]: '2 à 3 fois',
    [normalizeOptionKey('élevé')]: '4 fois ou plus',
  },
}

function prettifyOptionLabel(slug: string, rawLabel: string, rawValue?: string): string {
  const slugKey = normalizeOptionKey(slug)
  const valueKey = normalizeOptionKey(rawValue ?? rawLabel)

  const bySlug = OPTION_LABEL_OVERRIDES_BY_SLUG[slugKey]
  if (bySlug && bySlug[valueKey]) return bySlug[valueKey]

  const globalOverride = GLOBAL_OPTION_LABEL_OVERRIDES[valueKey]
  if (globalOverride) return globalOverride

  return humanizeOptionLabel(rawLabel)
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

  if (raw.plancher !== undefined || raw.plafond !== undefined || raw['unité'] !== undefined)
    return 'NOMBRE'
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
        if (typeof p === 'string')
          return { label: prettifyOptionLabel(slug, String(p), String(p)), value: p }

        const label =
          p.title ??
          p.label ??
          p.name ??
          p.acronym ??
          (typeof p.dottedName === 'string' ? p.dottedName.split(' . ').slice(-1)[0] : undefined) ??
          String(p.dottedName ?? p)

        const value = p.dottedName ?? p.name ?? p.value ?? label
        const valueStr = String(value)
        return {
          label: prettifyOptionLabel(slug, String(label), valueStr),
          value: valueStr,
        }
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
      if (typeof noneLabel === 'string' && noneLabel.trim().length > 0)
        config.noneOptionLabel = prettifyOptionLabel(slug, noneLabel.trim(), noneLabel.trim())
      else config.noneOptionLabel = 'Aucun'
    }

    if (widgetType === 'CHOIX_MULTIPLE' && Array.isArray(raw.mosaique.options)) {
      config.options = raw.mosaique.options.map((opt: any) => {
        if (typeof opt === 'string') {
          const fullSlug = resolveMosaicOptionSlug(slug, opt)
          const rawLabel = prettifyPresentLabel(opt)
          return { label: prettifyOptionLabel(slug, rawLabel, rawLabel), slug: fullSlug }
        }

        const candidate = opt?.dottedName ?? opt?.valeur ?? opt?.name
        const rawStr = typeof candidate === 'string' ? candidate : String(opt)
        const fullSlug = resolveMosaicOptionSlug(slug, rawStr)

        const rawLabel = String(opt?.titre ?? opt?.title ?? opt?.label ?? rawStr)
        const cleanLabel = prettifyPresentLabel(rawLabel)
        return {
          label: prettifyOptionLabel(slug, cleanLabel, cleanLabel),
          slug: fullSlug,
        }
      })
    }
  }

  if (!config.options && Array.isArray(raw['une possibilité'])) {
    config.options = raw['une possibilité'].map((opt: any) => {
      const value = String(opt)
      return { label: prettifyOptionLabel(slug, value, value), value }
    })
  }
  if (widgetType === 'BOOLEEN' && !config.options) config.options = ['oui', 'non']
  if (widgetType === 'BOOLEEN') config.booleanNative = !hasExplicitPossibilities

  if (widgetType === 'CHOIX_MULTIPLE' && Array.isArray(config.options)) {
    const slugs = config.options
      .map((opt: any) => String(opt?.slug ?? opt?.value ?? ''))
      .filter(Boolean)
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
  if (raw['unité']) config.unit = raw['unité']

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
export function isQuestionVisible(
  q: QuestionRecord,
  answers: Record<string, any>,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _engine?: Engine | null,
): boolean {
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

/** Transforme un libellé NGC (ex: "électricité . présent") en libellé UI plus propre. */
function prettifyPresentLabel(s: string): string {
  const withoutPresent = s.replace(/\s*\.\s*présent\s*$/i, '').trim()
  if (withoutPresent.includes('photovoltaique')) return 'électricité photovoltaïque'
  return withoutPresent.split(' . ').slice(-1)[0]!
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
