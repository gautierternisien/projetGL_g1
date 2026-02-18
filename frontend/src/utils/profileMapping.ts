// src/utils/profileMapping.ts

export interface DerivedPreferences {
  possession_voiture: boolean
  possession_velo: boolean
  prend_avion: boolean
  est_proprietaire: boolean
  vit_en_maison: boolean
  vit_en_appartement: boolean
  passoire_thermique: boolean
  viande_rouge_importante: boolean
  eau_bouteille: boolean
  conso_pas_locaux: boolean
  conso_pas_saison: boolean
  boissons_chaudes: boolean
  soda: boolean
  alcool: boolean
  dechets_importants: boolean
  shopping_important: boolean
  fumeur: boolean
}

/**
 * Aplatit les réponses imbriquées (gestion des Mosaïques Publicodes)
 */
function flattenAnswers(answers: Record<string, any>): Record<string, any> {
  const flat: Record<string, any> = {}
  for (const [key, value] of Object.entries(answers)) {
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      for (const [subKey, subValue] of Object.entries(value)) {
        flat[subKey] = subValue
      }
    } else {
      flat[key] = value
    }
  }
  return flat
}

/**
 * Analyse les réponses.
 * LOGIQUE : "Opt-out". Par défaut (si pas de réponse), on renvoie TRUE.
 * On ne renvoie FALSE que si la réponse explicite indique que ce n'est pas le cas.
 */
export function derivePreferencesFromAnswers(rawAnswers: Record<string, any>): DerivedPreferences {
  const answers = flattenAnswers(rawAnswers)

  // Récupère la valeur brute, undefined si absente
  const val = (key: string) => {
    const v = answers[key]
    if (typeof v === 'string') return v.replace(/['"]+/g, '').trim()
    return v
  }

  const num = (key: string) => {
    const v = val(key)
    if (v === undefined || v === null || v === '') return undefined
    return Number(v)
  }

  // Si "non" ou false -> on désactive. Sinon (oui, undefined, autre) -> on active.
  const isExplicitlyNo = (key: string) => {
    const v = val(key)
    if (v === undefined || v === null) return false

    // On compare en minuscule pour être sûr
    const s = String(v).toLowerCase()
    return s === 'non' || s === 'false' || s === 'aucun' || s === 'jamais' || v === false
  }

  const isExplicitlyZero = (key: string) => {
    const n = num(key)
    return n !== undefined && n === 0
  }

  // Pour les sélecteurs type "local", "saison", "déchets"
  // Si on répond "oui toujours" ou "zéro déchet", on désactive la mission d'amélioration.
  // Sinon (pas répondu ou autre réponse), on active.
  const isExplicitlyPerfect = (key: string, perfectValue: string) => {
    const v = val(key)
    return v === perfectValue
  }

  return {
    // --- TRANSPORT ---
    // Activé sauf si on dit explicitement qu'on n'a pas de voiture
    possession_voiture: !isExplicitlyNo('transport . voiture . utilisateur'),

    // Pour le vélo, c'est l'inverse : on veut savoir s'il en a un pour proposer le vélotaf.
    // Mais en logique opt-out, on suppose qu'il peut en faire, sauf s'il dit "non".
    // Disons : Activé par défaut (pour encourager), désactivé si 'non'.
    possession_velo: !isExplicitlyNo('transport . mobilité douce . vélo . présent'),

    prend_avion: val('transport . avion . usager') !== 'jamais',

    // --- LOGEMENT ---
    est_proprietaire:
      val('logement . propriétaire') !== 'locataire' &&
      val('logement . propriétaire') !== 'hébergé',

    vit_en_maison: val('logement . type') !== 'appartement',
    vit_en_appartement: val('logement . type') !== 'maison',

    // Isolation :
    // On désactive SI le DPE est bon (A/B/C) OU si le ressenti est bon.
    // Sinon (pas de réponse ou mauvais), on laisse activé.
    passoire_thermique: !(
      ['A', 'B', 'C'].includes(val('logement . DPE')) ||
      ['confortable', 'chaud'].includes(
        val('logement . chauffage . précision consommation . ressenti'),
      )
    ),

    // --- ALIMENTATION ---
    // Activé par défaut. Désactivé si on répond 0 ou 1 repas.
    viande_rouge_importante: !(
      num('alimentation . plats . viande rouge . nombre') !== undefined &&
      num('alimentation . plats . viande rouge . nombre')! <= 1
    ),

    eau_bouteille: !isExplicitlyNo('alimentation . boisson . eau en bouteille . consommateur'),

    conso_pas_locaux: !isExplicitlyPerfect('alimentation . local . consommation', 'oui toujours'),
    conso_pas_saison: !isExplicitlyPerfect(
      'alimentation . de saison . consommation',
      'oui toujours',
    ),

    // --- BOISSONS ---
    // Désactivé si la somme est explicitement 0
    boissons_chaudes: !(
      isExplicitlyZero('alimentation . boisson . chaude . café . nombre') &&
      isExplicitlyZero('alimentation . boisson . chaude . thé . nombre') &&
      isExplicitlyZero('alimentation . boisson . chaude . chocolat chaud . nombre')
    ),

    soda: !isExplicitlyZero('alimentation . boisson . sucrées . litres'),
    alcool: !isExplicitlyZero('alimentation . boisson . alcool . litres'),

    // --- DIVERS ---
    dechets_importants: !isExplicitlyPerfect(
      'alimentation . déchets . quantité jetée',
      'zéro déchet',
    ),

    shopping_important: val('divers . textile . volume') !== 'minimum',

    fumeur: !isExplicitlyZero('divers . tabac . consommation par semaine'),
  }
}

export const PREFERENCE_LABELS: Record<keyof DerivedPreferences, string> = {
  possession_voiture: "J'utilise une voiture",
  possession_velo: "J'ai un vélo",
  prend_avion: "Je prends l'avion",
  est_proprietaire: 'Je suis propriétaire',
  vit_en_maison: 'Je vis en maison',
  vit_en_appartement: 'Je vis en appartement',
  passoire_thermique: 'Mon logement est mal isolé',
  viande_rouge_importante: 'Je mange de la viande rouge',
  eau_bouteille: "Je bois de l'eau en bouteille",
  conso_pas_locaux: 'Je veux consommer plus local',
  conso_pas_saison: 'Je veux manger plus de saison',
  boissons_chaudes: 'Je consomme café/thé',
  soda: 'Je bois des sodas',
  alcool: "Je bois de l'alcool",
  dechets_importants: 'Je veux réduire mes déchets',
  shopping_important: "J'achète des vêtements neufs",
  fumeur: 'Je fume',
}
