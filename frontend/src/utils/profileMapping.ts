// Type pour nos préférences déduites
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
      // C'est un objet (Mosaïque), on extrait ses sous-clés
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
 * Analyse les réponses brutes du questionnaire pour en déduire le profil.
 * @param answers L'objet contenant toutes les réponses (clés Publicodes)
 */
export function derivePreferencesFromAnswers(rawAnswers: Record<string, any>): DerivedPreferences {
  // 1. On aplatit les réponses pour trouver les clés des Mosaïques
  const answers = flattenAnswers(rawAnswers)

  // Nettoie la valeur
  const clean = (val: any) => {
    if (typeof val === 'string') {
      return val.replace(/['"]+/g, '').trim()
    }
    return val
  }

  const val = (key: string) => clean(answers[key])

  const isOui = (key: string) => {
    const v = val(key)
    return v === 'oui' || v === true
  }

  const num = (key: string) => {
    const v = val(key)
    return v ? Number(v) : 0
  }

  const isDefinedAndNot = (key: string, target: string) => {
    const v = val(key)
    return v !== undefined && v !== target
  }

  return {
    // --- TRANSPORT ---
    possession_voiture:
      val('transport . voiture . utilisateur') === 'propriétaire' ||
      val('transport . voiture . utilisateur') === 'régulier non propriétaire',

    // Ajout du VAE (Vélo à assistance électrique)
    possession_velo:
      isOui('transport . mobilité douce . vélo . présent') ||
      isOui('transport . mobilité douce . vae . présent'),

    prend_avion:
      val('transport . avion . usager') !== 'jamais' &&
      val('transport . avion . usager') !== undefined,

    // --- LOGEMENT ---
    est_proprietaire: val('logement . propriétaire') === 'propriétaire',
    vit_en_maison: val('logement . type') === 'maison',
    vit_en_appartement: val('logement . type') === 'appartement',

    passoire_thermique:
      val('logement . chauffage . précision consommation . ressenti') === 'passoire thermique' ||
      ['F', 'G'].includes(val('logement . DPE')),

    // --- ALIMENTATION ---
    // Seuil > 0 : Si on en mange, on peut réduire
    viande_rouge_importante: num('alimentation . plats . viande rouge . nombre') > 0,

    eau_bouteille: isOui('alimentation . boisson . eau en bouteille . consommateur'),

    conso_pas_locaux: isDefinedAndNot('alimentation . local . consommation', 'oui toujours'),
    conso_pas_saison: isDefinedAndNot('alimentation . de saison . consommation', 'oui toujours'),

    // --- BOISSONS ---
    boissons_chaudes:
      num('alimentation . boisson . chaude . café . nombre') +
        num('alimentation . boisson . chaude . thé . nombre') +
        num('alimentation . boisson . chaude . chocolat chaud . nombre') >
      0,

    soda: num('alimentation . boisson . sucrées . litres') > 0,
    alcool: num('alimentation . boisson . alcool . litres') > 0,

    // --- DIVERS ---
    dechets_importants: isDefinedAndNot('alimentation . déchets . quantité jetée', 'zéro déchet'),

    shopping_important: ['accro au shopping', 'renouvellement occasionnel'].includes(
      val('divers . textile . volume'),
    ),

    // Tabac : C'est une consommation en cigarettes/semaine ou paquets/semaine selon le modèle
    // Si la valeur existe et est > 0, c'est fumeur.
    // La clé exacte peut être 'divers . tabac . consommation par semaine' ou juste une réponse liée à la présence.
    // Dans le doute, on check la présence d'une valeur positive.
    fumeur: num('divers . tabac . consommation par semaine') > 0,
  }
}

// Labels pour l'affichage dans la modale (plus jolis)
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
  shopping_important: "J'achète souvent des vêtements/objets",
  fumeur: 'Je fume',
}
