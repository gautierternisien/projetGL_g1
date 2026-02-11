/* eslint-disable @typescript-eslint/no-explicit-any */
import { API_URL } from '@/config'

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

    const payloadText = decodeBase64Url(parts[1]!)
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
    if (!raw) return {}
    return JSON.parse(raw)
  } catch (e) {
    console.error('Failed to load answers from localStorage', e)
    return {}
  }
}

/** Récupère les réponses depuis le backend (si connecté). */
export async function fetchRemoteAnswers(token: string): Promise<Record<string, any> | null> {
  if (!token) return null
  try {
    const res = await fetch(`${API_URL}/ngc/answers/me`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) return null
    const json = await res.json()
    return json.data
  } catch (e) {
    console.warn('Failed to fetch remote answers', e)
    return null
  }
}

/** Sauvegarde les réponses dans le localStorage. */
export function saveAnswers(answers: Record<string, any>) {
  try {
    localStorage.setItem(getAnswersKey(), JSON.stringify(answers))
  } catch (e) {
    console.error('Failed to save answers to localStorage', e)
  }
}

/** Envoie les réponses au backend (si connecté). */
export async function pushRemoteAnswers(
  token: string,
  answers: Record<string, any>,
): Promise<void> {
  if (!token) return
  try {
    await fetch(`${API_URL}/ngc/answers/me`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ data: answers }),
    })
  } catch (e) {
    console.warn('Failed to push remote answers', e)
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
