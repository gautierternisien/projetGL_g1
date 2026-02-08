/* eslint-disable @typescript-eslint/no-explicit-any */


export type Category = 'logement' | 'transport' | 'alimentation' | 'divers'

const ANSWERS_KEY_PREFIX = 'ngc_answers_v2'
const PROGRESS_KEY_PREFIX = 'ngc_progress_v2'

type JwtPayload = {
  sub?: string
}

function decodeBase64Url(input: string): string {
  const normalized = input.replace(/-/g, '+').replace(/_/g, '/')
  const padded = normalized.padEnd(Math.ceil(normalized.length / 4) * 4, '=')
  return atob(padded)
}

function getCurrentUserScope(): string {
  try {
    const token = localStorage.getItem('token')
    if (!token) return 'anon'

    const parts = token.split('.')
    if (parts.length < 2) return 'anon'

    const payloadText = decodeBase64Url(parts[1])
    const payload = JSON.parse(payloadText) as JwtPayload
    const sub = String(payload?.sub ?? '').trim()
    if (!sub) return 'anon'

    // "sub" is user.id in this backend (numeric string)
    return `u_${sub}`
  } catch {
    return 'anon'
  }
}

function getAnswersKey() {
  return `${ANSWERS_KEY_PREFIX}_${getCurrentUserScope()}`
}

function getProgressKey() {
  return `${PROGRESS_KEY_PREFIX}_${getCurrentUserScope()}`
}

/** Charge les réponses depuis le localStorage. */
export function loadAnswers(): Record<string, any> {
  try {
    const raw = localStorage.getItem(getAnswersKey())
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

/** Sauvegarde les réponses dans le localStorage. */
export function saveAnswers(answers: Record<string, any>) {
  try {
    localStorage.setItem(getAnswersKey(), JSON.stringify(answers))
  } catch {
    // ignore
  }
}

/** Charge la progression (slug courant) par catégorie. */
export function loadProgress(): Partial<Record<Category, string>> {
  try {
    const raw = localStorage.getItem(getProgressKey())
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

/** Sauvegarde la progression (slug courant) par catégorie. */
export function saveProgress(progress: Partial<Record<Category, string>>) {
  try {
    localStorage.setItem(getProgressKey(), JSON.stringify(progress))
  } catch {
    // ignore
  }
}
