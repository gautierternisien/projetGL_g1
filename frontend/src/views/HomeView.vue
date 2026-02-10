<script setup lang="ts">
import Card from '@/components/AppCard.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import Header from '@/components/AppHeader.vue'
import { ref, onMounted, onUnmounted, computed, onActivated, watch } from 'vue'
import Engine from 'publicodes'
import type { Mission } from '@/types/mission'
import { useProgressStore } from '@/stores/progress'
import { useAuthStore } from '@/stores/auth'
import { useFriendsStore } from '@/stores/friends'
import { API_URL } from '@/config'
import { loadAnswers } from '@/lib/ngc/answersStorage'
import { computeCategoryProgressFromAnswers } from '@/utils/ngcProgress'

const store = useProgressStore()
const authStore = useAuthStore()
const friendsStore = useFriendsStore()
const isConnected = computed(() => authStore.isConnected)

// Dictionnaire pour afficher de jolis noms (au lieu de 'transport', 'alimentation'...)
const CATEGORY_LABELS: Record<string, string> = {
  transport: 'Transport',
  alimentation: 'Alimentation',
  logement: 'Logement',
  divers: 'Divers',
  services_societaux: 'Services sociétaux',
}

// Couleurs fixes par catégorie
const CATEGORY_COLORS: Record<string, string> = {
  transport: '#f3ab70', // Brown
  alimentation: '#D84315', // Deep Orange
  logement: '#3951a6', // Yellow
  divers: '#24aa26', // Purple
  services_societaux: '#616161', // Dark gray
}

const globalStats = ref({
  global_score: 0,
  total_leagues: 0,
  total_missions_completed: 0,
  total_trophies: 0,
  user_count: 0,
})

const getCategoryColor = (key: string) => {
  if (key === 'services_societaux') return CATEGORY_COLORS.services_societaux

  const score = store.getCategoryScore(key)

  // Si le score est 0 (ou inexistant), on retourne du GRIS
  if (!score || score === 0) {
    return '#BDBDBD' // Gris moyen (tu peux changer par '#E0E0E0' pour plus clair)
  }

  // Sinon, on retourne la couleur officielle de la catégorie
  return CATEGORY_COLORS[key] // Fallback au cas où
}
function normalizeCategoryKey(rawKey: string): string {
  const normalized = rawKey
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()

  if (normalized === 'transport') return 'transport'
  if (normalized === 'alimentation') return 'alimentation'
  if (normalized === 'logement') return 'logement'
  if (normalized === 'divers') return 'divers'
  if (normalized === 'services societaux') return 'services_societaux'

  return rawKey
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

function evaluateServicesSocietaux(engine: Engine, rules: Record<string, any>): number {
  const servicesRuleName = findRuleNameByNormalizedName(rules, 'services societaux')
  if (!servicesRuleName) return 0

  try {
    const r: any = engine.evaluate(servicesRuleName)
    return typeof r?.nodeValue === 'number' ? Math.round(r.nodeValue) : 0
  } catch {
    return 0
  }
}

// --- ÉTATS ---
const userScore = ref(0)
const averageScore = ref(0)
const scoreColor = ref('#333') // Couleur par défaut
const scoreEmoji = ref('🥀') // Emoji par défaut
const scoreComment = ref('Chargement...')

const sectors = ref<{ key: string; name: string; pct: number; color: string }[]>([])
const rulesCache = ref<any | null>(null)
type NgcStats = {
  globalScore: number
  detailsByCategory: Record<string, number>
  categoryProgress?: Record<string, number>
}
const modelDefaultStatsCache = ref<NgcStats | null>(null)
let disconnectedRefreshTimer: ReturnType<typeof setInterval> | null = null

// Dashboard missions: load actual missions from backend (show title + category)
const displayMissions = ref<{ mission: Mission; category: string }[]>([])

async function loadDashboardMissions() {
  try {
    const keys = ['transport', 'logement', 'alimentation', 'divers']
    const userIdParam = authStore.user ? `?user_id=${authStore.user.id}` : ''
    const results = await Promise.all(
      keys.map((k) =>
        fetch(`${API_URL}/missions/${k}${userIdParam}`, { cache: 'no-store' })
          .then((r) => (r.ok ? r.json() : []))
          .catch(() => []),
      ),
    )

    const rows: { mission: Mission; category: string }[] = []
    for (let i = 0; i < keys.length; i++) {
      const k = keys[i]
      const data = results[i]
      if (Array.isArray(data)) {
        for (const d of data) {
          const status = (d.status ?? d.desc ?? 'new').toString().toLowerCase()
          if (
            status.includes('en_cours') ||
            status.includes('encours') ||
            status.includes('in_progress') ||
            status.includes('ongoing')
          ) {
            rows.push({
              mission: {
                id: Number(d.id),
                title: String(d.title || ''),
                description: d.description ?? d.desc ?? '',
                status,
              },
              category: k as string,
            })
          }
          if (rows.length >= 6) break
        }
      }
      if (rows.length >= 6) break
    }

    displayMissions.value = rows
  } catch (e) {
    console.error('Erreur loadDashboardMissions', e)
  }
}

const events = computed(() => {
  return friendsStore.activities.slice(0, 6)
})

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

function flattenAnswers(source: Record<string, any>) {
  const flat: Record<string, any> = {}
  for (const [k, v] of Object.entries(source)) {
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

function hasFilledAnswer(value: any): boolean {
  if (value === undefined || value === null || value === '') return false
  if (Array.isArray(value)) return value.some(hasFilledAnswer)
  if (typeof value === 'object') {
    const values = Object.values(value)
    if (values.length === 0) return false
    return values.some(hasFilledAnswer)
  }
  return true
}

async function getRules() {
  if (rulesCache.value) return rulesCache.value
  const res = await fetch(`${API_URL}/rules`, { cache: 'no-store' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  rulesCache.value = await res.json()
  return rulesCache.value
}

function normalizeDetails(
  details: Record<string, number> | null | undefined,
): Record<string, number> {
  const normalized: Record<string, number> = {}
  for (const [rawKey, rawValue] of Object.entries(details ?? {})) {
    const key = normalizeCategoryKey(rawKey)
    if (!(key in CATEGORY_LABELS)) continue

    const numeric = typeof rawValue === 'number' ? rawValue : Number(rawValue)
    const safeValue = Number.isFinite(numeric) ? numeric : 0
    normalized[key] = (normalized[key] ?? 0) + safeValue
  }
  return normalized
}

function enrichDetailsWithServices(
  details: Record<string, number> | null | undefined,
  total: number,
  defaults: NgcStats | null,
): Record<string, number> {
  const enriched = normalizeDetails(details)
  if ((enriched.services_societaux ?? 0) > 0 || total <= 0) return enriched

  const knownTotal =
    (enriched.transport ?? 0) +
    (enriched.logement ?? 0) +
    (enriched.alimentation ?? 0) +
    (enriched.divers ?? 0)

  const remainder = total - knownTotal
  if (remainder > 0.0001) {
    enriched.services_societaux = remainder
    return enriched
  }

  if (!defaults || defaults.globalScore <= 0) return enriched

  const defaultServices = Number(defaults.detailsByCategory.services_societaux ?? 0)
  if (!Number.isFinite(defaultServices) || defaultServices <= 0) return enriched

  const servicesRatio = defaultServices / defaults.globalScore
  const inferredServices = Math.max(0, total * servicesRatio)
  const targetKnownTotal = Math.max(0, total - inferredServices)
  const scale = knownTotal > 0 ? targetKnownTotal / knownTotal : 0

  for (const key of ['transport', 'logement', 'alimentation', 'divers']) {
    if (enriched[key] !== undefined) enriched[key] *= scale
  }

  enriched.services_societaux = inferredServices
  return enriched
}

async function computeLocalNgcStats() {
  try {
    const rules = await getRules()
    const engine = new Engine(rules)
    const answers = loadAnswers() ?? {}
    const flat = flattenAnswers(answers)
    const hasAnswers = Object.values(flat).some(hasFilledAnswer)

    const situation = Object.fromEntries(
      Object.entries(flat)
        .map(([k, v]) => [k, toPublicodesValue(v)] as const)
        .filter(([, v]) => v !== undefined),
    )

    engine.setSituation(situation)

    const bilanRes: any = engine.evaluate('bilan')
    let globalScore =
      typeof bilanRes?.nodeValue === 'number' ? Math.round(bilanRes.nodeValue) : 8559
    if (!hasAnswers) globalScore = 8559

    const detailsByCategory: Record<string, number> = {}
    for (const key of ['transport', 'logement', 'alimentation', 'divers']) {
      const r: any = engine.evaluate(key)
      detailsByCategory[key] = typeof r?.nodeValue === 'number' ? Math.round(r.nodeValue) : 0
    }

    detailsByCategory.services_societaux = evaluateServicesSocietaux(engine, rules)
    const categoryProgress = computeCategoryProgressFromAnswers(answers)

    return { globalScore, detailsByCategory, categoryProgress }
  } catch (error) {
    console.error('Erreur calcul local NGC:', error)
    return null
  }
}

async function getModelDefaultStatsCached(): Promise<NgcStats | null> {
  if (modelDefaultStatsCache.value) return modelDefaultStatsCache.value
  const computedDefaults = await computeModelDefaultStats()
  if (computedDefaults) modelDefaultStatsCache.value = computedDefaults
  return computedDefaults
}

async function pushNgcStatsToBackend(stats: NgcStats) {
  if (!authStore.isConnected || !authStore.token) return

  try {
    await fetch(`${API_URL}/ngc/stats/me`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify({
        global_score: stats.globalScore,
        details_by_category: stats.detailsByCategory,
        category_progress: stats.categoryProgress ?? {},
      }),
    })
  } catch {
    // Best-effort sync only.
  }
}

async function loadGlobalStats() {
  try {
    const response = await fetch(`${API_URL}/global-stats`)
    if (response.ok) {
      const data = await response.json()
      globalStats.value = data
    }
  } catch (e) {
    console.error('Erreur chargement stats globales', e)
  }
}

async function refreshProgressAndScore() {
  // 1. Synchronisation initiale si connecté
  if (isConnected.value && authStore.user) {
    await store.fetchAllProgress(authStore.user.id)
  }

  // Récupération des réponses locales (utile pour le mode connecté et invité)
  store.syncFromLocalAnswers()

  // --- ÉTAPE A : Récupérer les données globales (Reference) ---
  let globalApiData = null
  try {
    const response = await fetch(`${API_URL}/global-stats`, { cache: 'no-store' })
    if (response.ok) {
      globalApiData = await response.json()

      // On met à jour la moyenne nationale affichée (benchmark)
      // Si l'API renvoie une moyenne nationale, on la prend, sinon défaut 8559
      averageScore.value = globalApiData.average_national_score || 8559
    }
  } catch (error) {
    console.error('Erreur chargement stats globales:', error)
  }

  // On prépare les données par défaut (NGC) au cas où on en a besoin (fallback)
  const defaults = await getModelDefaultStatsCached()
  const defaultScore = defaults ? defaults.globalScore : 8559
  const defaultDetails = defaults ? defaults.detailsByCategory : {}

  // --- ÉTAPE B : Gestion du Score Utilisateur (Gros Chiffre) ---

  if (isConnected.value) {
    // === CAS 1 : CONNECTÉ ===
    // On calcule le score précis basé sur les réponses de l'utilisateur
    const localStats = await computeLocalNgcStats()

    if (localStats) {
      userScore.value = localStats.globalScore

      // On enrichit avec les services sociétaux (impôts, services publics...)
      // Assure-toi que cette fonction existe et gère les nulls
      const enrichedDetails = enrichDetailsWithServices(
        localStats.detailsByCategory,
        userScore.value,
        defaults,
      )

      processSectors(enrichedDetails, userScore.value)

      // On sauvegarde ce nouveau score dans le backend
      await pushNgcStatsToBackend(localStats)
    } else {
      // Fallback si le calcul local échoue
      userScore.value = defaultScore
      processSectors(defaultDetails, defaultScore)
    }
  } else {
    // === CAS 2 : NON CONNECTÉ (INVITÉ) ===
    // On veut afficher la moyenne de la communauté ("Empreinte moyenne des utilisateurs")

    if (globalApiData && globalApiData.user_count > 0) {
      // S'il y a des données globales réelles
      userScore.value = Number(globalApiData.global_score) || defaultScore

      // On utilise les détails globaux venant de l'API
      // Note: On passe 'defaults' en 3ème argument si enrichDetailsWithServices en a besoin pour combler les trous
      const enrichedDetails = enrichDetailsWithServices(
        globalApiData.details_by_category,
        userScore.value,
        defaults,
      )

      processSectors(enrichedDetails, userScore.value)
    } else {
      // S'il n'y a pas encore d'utilisateurs ou erreur API -> On affiche la moyenne française par défaut
      userScore.value = defaultScore
      processSectors(defaultDetails, defaultScore)
    }
  }

  // --- ÉTAPE C : Mise à jour des couleurs/emojis ---
  calculateStatus(userScore.value, averageScore.value || 8559)
}

// --- COMPUTED POUR LE GRAPHIQUE ---
const donutStyle = computed(() => {
  if (sectors.value.length === 0) {
    return { background: '#e0e0e0' }
  }

  let current = 0
  const segments = sectors.value
    .map((s) => {
      if (s.pct <= 0) return null

      const start = current
      const end = Math.min(100, current + s.pct)
      current = end
      return `${s.color} ${start}% ${end}%`
    })
    .filter((segment): segment is string => !!segment)

  if (current < 100) {
    segments.push(`#E0E0E0 ${current}% 100%`)
  }

  if (segments.length === 0) {
    return { background: '#e0e0e0' }
  }

  return {
    background: `conic-gradient(${segments.join(', ')})`,
  }
})

const legendSectors = computed(() => sectors.value.filter((s) => s.key in CATEGORY_LABELS))

// --- LOGIQUE DE CALCUL ---
const calculateStatus = (score: number, avg: number) => {
  // On définit une marge de tolérance de 15% autour de la moyenne
  const lowThreshold = avg * 0.85
  const highThreshold = avg * 1.15
  const objetiveTreshold = 2000

  if (score < objetiveTreshold) {
    // Cas JAUNE : En dessous des 2 tonnes
    scoreColor.value = '#4CAF50' // Jaune
    scoreEmoji.value = '👑'
    scoreComment.value = 'Objectif atteint !'
  } else if (score <= lowThreshold) {
    // Cas VERT : Bien en dessous de la moyenne
    scoreColor.value = '#FFC01F' // Vert
    scoreEmoji.value = '🌹'
    scoreComment.value = 'Excellent !'
  } else if (score > highThreshold) {
    // Cas ROUGE : Bien au-dessus de la moyenne
    scoreColor.value = '#D32F2F' // Rouge
    scoreEmoji.value = '🪾' //
    scoreComment.value = 'Attention'
  } else {
    // Cas ORANGE : Dans la moyenne
    scoreColor.value = '#FB8C00' // Orange
    scoreEmoji.value = '🥀️'
    scoreComment.value = 'Dans la moyenne'
  }
}

// 2. Traitement des secteurs pour le graphique
const processSectors = (details: Record<string, number>, total: number) => {
  const aggregated: Record<string, number> = {}

  for (const [rawKey, rawValue] of Object.entries(details)) {
    const key = normalizeCategoryKey(rawKey)
    if (!(key in CATEGORY_LABELS)) continue

    const numeric = typeof rawValue === 'number' ? rawValue : Number(rawValue)
    const safeValue = Number.isFinite(numeric) ? numeric : 0
    aggregated[key] = (aggregated[key] ?? 0) + safeValue
  }

  const hasServicesFromDetails = (aggregated.services_societaux ?? 0) > 0
  if (!hasServicesFromDetails && total > 0) {
    const knownTotal =
      (aggregated.transport ?? 0) +
      (aggregated.logement ?? 0) +
      (aggregated.alimentation ?? 0) +
      (aggregated.divers ?? 0)

    const remainder = total - knownTotal
    if (remainder > 0.0001) aggregated.services_societaux = remainder
  }

  const aggregatedTotal = Object.values(aggregated).reduce((sum, value) => {
    if (!Number.isFinite(value) || value <= 0) return sum
    return sum + value
  }, 0)
  const denominator = aggregatedTotal > 0 ? aggregatedTotal : total

  const rawSectors = Object.entries(aggregated).map(([key, value]) => ({
    key,
    name: CATEGORY_LABELS[key] || key,
    rawScore: value,
    pct: denominator > 0 ? (value / denominator) * 100 : 0,
  }))

  const activeSectors = rawSectors.filter((s) => s.pct > 0)
  activeSectors.sort((a, b) => b.pct - a.pct)

  sectors.value = activeSectors.map((sector) => {
    let color

    if (sector.key === 'services_societaux') {
      color = CATEGORY_COLORS.services_societaux
    } else if (!isConnected.value) {
      color = CATEGORY_COLORS[sector.key] || '#333'
    } else {
      color = getCategoryColor(sector.key)
    }

    return {
      name: sector.name,
      pct: sector.pct,
      color: String(color),
      key: sector.key,
    }
  })
}

async function computeModelDefaultStats() {
  try {
    const rules = await getRules()
    const engine = new Engine(rules)
    engine.setSituation({})

    const bilanRes: any = engine.evaluate('bilan')
    const globalScore =
      typeof bilanRes?.nodeValue === 'number' ? Math.round(bilanRes.nodeValue) : 8559

    const detailsByCategory: Record<string, number> = {}
    for (const key of ['transport', 'logement', 'alimentation', 'divers']) {
      const r: any = engine.evaluate(key)
      detailsByCategory[key] = typeof r?.nodeValue === 'number' ? Math.round(r.nodeValue) : 0
    }

    detailsByCategory.services_societaux = evaluateServicesSocietaux(engine, rules)

    return { globalScore, detailsByCategory }
  } catch (error) {
    console.error('Erreur calcul moyenne par dÃ©faut NGC:', error)
    return null
  }
}

async function onWindowFocus() {
  await refreshProgressAndScore()
  if (isConnected.value) {
    await loadDashboardMissions()
    await friendsStore.fetchActivities()
  }
}

function stopDisconnectedRefreshTimer() {
  if (disconnectedRefreshTimer) {
    clearInterval(disconnectedRefreshTimer)
    disconnectedRefreshTimer = null
  }
}

function startDisconnectedRefreshTimer() {
  stopDisconnectedRefreshTimer()
  if (isConnected.value) return

  disconnectedRefreshTimer = setInterval(() => {
    void refreshProgressAndScore()
  }, 5000)
}

// --- CHARGEMENT DES DONNEES ---
onMounted(async () => {
  if (isConnected.value && !authStore.user) {
    await authStore.fetchUser()
  }

  await refreshProgressAndScore()

  await loadGlobalStats()

  if (isConnected.value) {
    await loadDashboardMissions()
    await friendsStore.fetchActivities()
  }

  window.addEventListener('focus', onWindowFocus)
  startDisconnectedRefreshTimer()
})

onUnmounted(() => {
  window.removeEventListener('focus', onWindowFocus)
  stopDisconnectedRefreshTimer()
})

// Refresh when navigating back to this view (if cached)
onActivated(async () => {
  await refreshProgressAndScore()
  if (isConnected.value) {
    await loadDashboardMissions()
    await friendsStore.fetchActivities()
  }
})

watch(
  () => authStore.user,
  async () => {
    await refreshProgressAndScore()
    if (isConnected.value) {
      await loadDashboardMissions()
      await friendsStore.fetchActivities()
    }
    startDisconnectedRefreshTimer()
  },
)

watch(isConnected, () => {
  startDisconnectedRefreshTimer()
})
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Tableau de bord" />

    <div class="scrollable-area">
      <Card :title="isConnected ? 'Mon empreinte carbone' : 'Empreinte moyenne des utilisateurs'">
        <div class="split-content">
          <div class="info-side">
            <span class="big-number" :style="{ color: scoreColor }">{{
              (userScore / 1000).toFixed(2)
            }}</span>
            <span class="unit-text">Tonnes CO₂</span>
            <div v-if="!isConnected" class="cta-container">
              <RouterLink to="/login" class="cta-link">
                ⚠️ Moyenne des utilisateurs 👉 Connectez vous pour voir votre propre empreinte
                carbone !
              </RouterLink>
            </div>
            <div v-else class="cta-container">
              <div v-if="store.globalAverage === 0" class="cta-container">
                <RouterLink to="/questionnaires" class="cta-link">
                  ⚠️ Moyenne française prise en compte pour le calcul 👉 Commencez les
                  questionnaires !
                </RouterLink>
              </div>
              <div
                v-if="store.globalAverage < 100 && store.globalAverage > 0"
                class="cta-container"
              >
                <RouterLink to="/questionnaires" class="cta-link">
                  ⚠️ Moyenne nationale prise en compte pour certaines catégories 👉 Continuez les
                  questionnaires
                </RouterLink>
              </div>
            </div>
          </div>
          <div class="image-side">
            <span class="emoji-img">{{ scoreEmoji }}</span>
          </div>
        </div>
      </Card>

      <Card :title="isConnected ? 'Mes émissions par secteur' : 'Émissions moyennes par secteur'">
        <div class="split-content">
          <div class="info-side">
            <ul class="legend-list">
              <li v-for="sector in legendSectors" :key="sector.name">
                <span class="dot" :style="{ backgroundColor: sector.color }"></span>
                <span :style="{ color: sector.color }">
                  {{ sector.name }} ({{ Math.round(sector.pct) }}%)
                </span>
              </li>
            </ul>
          </div>
          <div class="image-side">
            <div class="donut-chart" :style="donutStyle"></div>
          </div>
        </div>
      </Card>

      <RouterLink to="/questionnaires" class="unstyled-link">
        <Card title="Questionnaires" :hasArrow="true">
          <ProgressBar v-if="isConnected" :value="store.globalAverage"></ProgressBar>
          <div v-else class="lock-placeholder">🔒</div>
        </Card>
      </RouterLink>

      <RouterLink to="/missions" class="unstyled-link">
        <Card title="Missions en cours" :hasArrow="true">
          <div v-if="isConnected" class="carousel-container">
            <div v-for="item in displayMissions" :key="item.mission.id" class="mission-card">
              <RouterLink
                :to="`/missions/${item.category}?missionId=${item.mission.id}`"
                class="unstyled-link inner-mission-link"
              >
                <div class="card-content">
                  <span class="card-icon">🎯</span>
                  <div class="card-texts">
                    <span class="card-title">{{ item.mission.title }}</span>
                    <span class="card-subtitle">{{ CATEGORY_LABELS[item.category] }}</span>
                  </div>
                </div>
              </RouterLink>
            </div>
            <div v-if="displayMissions.length === 0" class="mission-card empty">
              Aucune mission en cours
            </div>
          </div>
          <div v-else class="lock-placeholder">🔒</div>
        </Card>
      </RouterLink>

      <RouterLink to="/communaute" class="unstyled-link">
        <Card title="Évènements communautaires " :hasArrow="true">
          <div v-if="isConnected" class="carousel-container">
            <div v-for="(event, i) in events" :key="i" class="mission-card">
              <RouterLink to="/communaute/evenements" class="unstyled-link inner-mission-link">
                <div class="card-content">
                  <span class="card-icon">👥</span>
                  <div class="card-texts">
                    <span class="card-title">{{ event.friend_username }}</span>
                    <span class="card-subtitle">a terminé : {{ event.mission_title }}</span>
                  </div>
                </div>
              </RouterLink>
            </div>
            <div v-if="events.length === 0" class="mission-card empty">Aucun évènement récent</div>
          </div>
          <div v-else class="lock-placeholder">🔒</div>
        </Card>
      </RouterLink>

      <Card title="Statistiques Globales">
        <div class="stats-grid">
          <div class="stat-item wide-item">
            <div class="stat-content-side">
              <span class="stat-icon">👣</span>
              <div class="stat-info">
                <div class="stat-value-row">
                  <span class="stat-number">
                    {{ (globalStats.global_score / 1000).toFixed(1) }}
                  </span>
                  <span class="stat-unit">Tonnes CO₂</span>
                </div>
                <span class="stat-label"
                  >Moyenne des<br />
                  utilisateurs</span
                >
              </div>
            </div>

            <div class="stat-separator"></div>

            <div class="stat-content-side">
              <span class="stat-icon">🎯</span>
              <div class="stat-info">
                <div class="stat-value-row">
                  <span class="stat-number goal-value">2.0</span>
                  <span class="stat-unit goal-value">Tonnes CO₂</span>
                </div>
                <span class="stat-label">Objectif 2050</span>
              </div>
            </div>
          </div>

          <div class="stat-item small-item">
            <span class="stat-icon">🏆</span>
            <div class="stat-info">
              <span class="stat-number">{{ globalStats.total_leagues }}</span>
              <span class="stat-label">Ligues<br />actives</span>
            </div>
          </div>

          <div class="stat-item small-item">
            <span class="stat-icon">✅</span>
            <div class="stat-info">
              <span class="stat-number">{{ globalStats.total_missions_completed }}</span>
              <span class="stat-label">Missions<br />finies</span>
            </div>
          </div>

          <div class="stat-item small-item">
            <span class="stat-icon">🥇</span>
            <div class="stat-info">
              <span class="stat-number">{{ globalStats.total_trophies }}</span>
              <span class="stat-label">Trophées<br />gagnés</span>
            </div>
          </div>

          <div class="stat-item small-item">
            <span class="stat-icon">👥</span>
            <div class="stat-info">
              <span class="stat-number">{{ globalStats.user_count }}</span>
              <span class="stat-label">Utilisateurs<br />inscrits</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  </div>
</template>

<style scoped>
/* --- LAYOUT GLOBAL --- */
/* .dashboard-wrapper est dans global.css */

/* --- ZONE DE SCROLL --- */
/* Géré dans global.css (.scrollable-area) */

/* --- MISE EN PAGE CONTENU (GAUCHE / DROITE) --- */
.split-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-side {
  flex: 1;
  display: flex;
  flex-direction: column; /* Pour empiler les infos */
  justify-content: center;
}

.image-side {
  flex-shrink: 0;
  margin-left: 15px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.emoji-img {
  font-size: 3.5rem;
}

/* --- GRAPHIQUE DONUT (Custom CSS car v-pie n'existe pas) --- */
.donut-chart {
  position: relative;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  /* Le background est géré dynamiquement via :style */
}

/* Le trou du donut */
.donut-chart::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60%; /* Épaisseur du donut */
  height: 60%;
  background-color: #f5f5f5; /* Couleur de fond de la carte */
  border-radius: 50%;
}

/* --- STYLE SPÉCIFIQUE EMPREINTE --- */
.big-number {
  font-size: 2.2rem;
  font-weight: 800;
}
.unit-text {
  display: block;
  font-weight: 600;
  color: #333;
}

/* --- STYLE SPÉCIFIQUE LISTE --- */
.legend-list {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 0.8rem;
  font-weight: 600;
}
.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  margin-right: 6px;
}

/* --- CARROUSEL --- */
.carousel-container {
  display: flex;
  gap: 12px;
  overflow-x: auto;

  /* MODIFICATION : On ajoute du padding tout autour pour que l'ombre ne soit pas coupée */
  padding: 10px 10px 20px 10px;
  /* (Haut Droite Bas Gauche) - On met un peu plus en bas pour l'ombre portée */

  /* On compense le padding pour que le scroll commence bien au bord visuel si besoin */
  margin: -10px;

  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  touch-action: pan-x;
  overscroll-behavior-x: contain;
  scroll-behavior: smooth;
  width: 100%;
}

/* Masquer la barre de scroll du carrousel (Optionnel mais joli) */
.carousel-container::-webkit-scrollbar {
  height: 8px;
}
.carousel-container {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.mission-card {
  /* Dimensions réduites pour voir les cartes adjacentes */
  width: 230px;
  height: 110px;

  /* Apparence : Fond blanc + Ombre */
  background-color: white;
  border-radius: 16px;
  border: 1px solid #f0f0f0; /* Bordure très subtile */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08); /* L'effet "pop" */

  /* Positionnement */
  position: relative; /* Indispensable pour placer les flèches */
  display: flex;
  align-items: center;
  justify-content: center;

  /* Comportement scroll : centré pour voir avant/après */
  flex-shrink: 0;
  scroll-snap-align: center;
  transition: transform 0.2s ease;
}

/* Effet au clic/toucher (optionnel) */
.mission-card:active {
  transform: scale(0.98);
}

/* Contenu central (Icône + Texte) */
.card-content {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px; /* Espace entre icône et textes */
  justify-content: flex-start;
  padding: 6px 8px;
}

.card-icon {
  font-size: 1.8rem;
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-texts {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.card-title {
  font-size: 0.95rem;
  color: #333;
  font-weight: 600;
  text-align: left;
}

.card-subtitle {
  font-size: 0.8rem;
  color: #679436; /* app green */
  font-weight: 600;
}

.unstyled-link {
  text-decoration: none;
  color: inherit;
  display: block;
  cursor: pointer;
}

.lock-placeholder {
  text-align: center;
  font-size: 1.5rem;
  color: #999;
  padding: 10px;
}

/* Conteneur pour centrer ou caler le message */
.cta-container {
  margin-top: 8px; /* Un peu d'espace sous "Tonnes CO2" */
}

/* Style du lien */
.cta-link {
  color: #679436; /* Ta couleur verte principale */
  font-size: 0.85rem; /* Un peu plus petit que le reste */
  font-weight: 700; /* Gras pour attirer l'oeil */
  text-decoration: none;
  border-bottom: 1px solid #679436; /* Petit soulignement propre */
  transition: opacity 0.2s;
}

.cta-link:hover {
  opacity: 0.8;
}

/* --- GRILLE --- */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr); /* 2 colonnes */
  gap: 12px;
}

/* --- STYLE GÉNÉRAL DES BOITES --- */
.stat-item {
  display: flex;
  align-items: center; /* Centre verticalement l'icône par rapport au texte */
  background-color: white;
  padding: 12px;
  border-radius: 12px;
  transition: transform 0.2s;
  gap: 16px;
}

/* --- BOITES 1x1 (PETITES) --- */
.small-item {
  justify-content: center; /* Centre le bloc (Icone+Texte) horizontalement dans la case */
  text-align: left; /* Le texte reste aligné à gauche par rapport à lui-même */
}

/* --- BOITE 2x1 (LARGE / EMPREINTE) --- */
.wide-item {
  grid-column: span 2;
  display: flex;
  justify-content: space-around; /* Espacement équitable entre gauche et droite */
  padding: 16px 12px;
  background: white;
  border: 1px solid #f0f0f0;
  align-items: flex-start;
  gap: 0;
}

.stat-content-side {
  display: flex;
  align-items: flex-start; /* Centre l'icône verticalement par rapport au bloc texte */
  gap: 16px;
  flex: 1;
  justify-content: center; /* Centre le contenu dans sa moitié */
}

.stat-separator {
  width: 1px;
  height: 45px; /* Hauteur fixe pour le trait de séparation */
  background-color: #ddd;
  margin: 0 5px;
  align-self: center;
}

/* --- TYPOGRAPHIE ET ICONES --- */
.stat-icon {
  font-size: 2rem; /* Taille unifiée des émojis */
  line-height: 1;
  flex-shrink: 0;
  margin-right: 0;
  margin-top: 4px;
}

.wide-item .stat-icon {
  margin-top: 4px;
}

.stat-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

/* Ligne contenant "5.1" et "Tonnes" */
.stat-value-row {
  display: flex;
  align-items: baseline; /* ALIGNEMENT MAGIQUE : Aligne le bas du chiffre avec le bas du texte */
  gap: 4px;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-number {
  font-weight: 800;
  font-size: 1.4rem; /* Le gros chiffre */
  color: #679436;
}

.stat-unit {
  font-weight: 600;
  font-size: 0.75rem; /* Le petit texte */
  color: #666;
}

.stat-label {
  font-size: 0.75rem;
  color: #666;
  line-height: 1.2;
}

/* --- RESPONSIVE MOBILE --- */
@media (max-width: 380px) {
  .stats-grid {
    grid-template-columns: 1fr; /* Une seule colonne */
  }

  .wide-item {
    grid-column: span 1;
    flex-direction: column; /* Empile les deux parties de l'empreinte */
    gap: 15px;
    align-items: flex-start;
  }

  .stat-content-side {
    justify-content: flex-start;
    width: 100%;
  }

  .stat-separator {
    display: none; /* Cache le trait vertical sur mobile */
  }

  .small-item {
    justify-content: flex-start; /* Aligne à gauche sur mobile */
  }
}
</style>
