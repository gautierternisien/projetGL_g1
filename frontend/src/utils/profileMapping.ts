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

  // Si "non" ou false -> on désactive. Sinon (oui, undefined, autre) -> on active.
  const isNotNo = (key: string) => {
    const v = val(key)
    return v !== 'non' && v !== false
  }

  // Pour les nombres : Si la valeur existe ET qu'elle est sous le seuil -> on désactive.
  // Si la valeur n'existe pas (undefined), on garde activé (par défaut).
  const numCheck = (key: string, threshold: number) => {
    const v = val(key)
    if (v === undefined || v === null || v === '') return true // Pas répondu -> Activé
    return Number(v) > threshold // Répondu -> Activé seulement si > seuil
  }

  // Pour les sélecteurs type "local", "saison", "déchets"
  // Si on répond "oui toujours" ou "zéro déchet", on désactive la mission d'amélioration.
  // Sinon (pas répondu ou autre réponse), on active.
  const isNotPerfect = (key: string, perfectValue: string) => {
    const v = val(key)
    if (v === undefined || v === null) return true // Pas répondu -> Activé
    return v !== perfectValue
  }

  return {
    // --- TRANSPORT ---
    // Activé sauf si on dit explicitement qu'on n'a pas de voiture
    possession_voiture:
      val('transport . voiture . utilisateur') !== 'non' &&
      val('transport . voiture . utilisateur') !== 'aucun',

    possession_velo: isNotNo('transport . mobilité douce . vélo . présent'),

    // Activé sauf si on dit "jamais"
    prend_avion: val('transport . avion . usager') !== 'jamais',

    // --- LOGEMENT ---
    // Ici c'est particulier, c'est mutuellement exclusif.
    // Si pas de réponse, on active tout pour laisser le choix.
    est_proprietaire:
      val('logement . propriétaire') !== 'locataire' &&
      val('logement . propriétaire') !== 'hébergé',

    vit_en_maison: val('logement . type') !== 'appartement',
    vit_en_appartement: val('logement . type') !== 'maison',

    // Activé par défaut, sauf si DPE A/B/C
    passoire_thermique: !['A', 'B', 'C'].includes(val('logement . DPE')),

    // --- ALIMENTATION ---
    viande_rouge_importante: numCheck('alimentation . plats . viande rouge . nombre', 1),

    eau_bouteille: isNotNo('alimentation . boisson . eau en bouteille . consommateur'),

    conso_pas_locaux: isNotPerfect('alimentation . local . consommation', 'oui toujours'),
    conso_pas_saison: isNotPerfect('alimentation . de saison . consommation', 'oui toujours'),

    // --- BOISSONS ---
    // On checke chaque sous-élément. Si on a répondu 0 à tout, ça désactive.
    // Si on n'a pas répondu, ça reste True.
    boissons_chaudes:
      val('alimentation . boisson . chaude . café . nombre') === undefined ||
      Number(val('alimentation . boisson . chaude . café . nombre')) > 0 ||
      val('alimentation . boisson . chaude . thé . nombre') === undefined ||
      Number(val('alimentation . boisson . chaude . thé . nombre')) > 0,

    soda: numCheck('alimentation . boisson . sucrées . litres', 0),
    alcool: numCheck('alimentation . boisson . alcool . litres', 0),

    // --- DIVERS ---
    dechets_importants: isNotPerfect('alimentation . déchets . quantité jetée', 'zéro déchet'),

    // Activé sauf si on dit "minimum"
    shopping_important: val('divers . textile . volume') !== 'minimum',

    // Activé par défaut (pour proposer d'arrêter), sauf si conso = 0
    fumeur: numCheck('divers . tabac . consommation par semaine', 0),
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
