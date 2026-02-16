/* eslint-disable @typescript-eslint/no-explicit-any */

import { API_URL } from '@/config'

export type Category = 'logement' | 'transport' | 'alimentation' | 'divers'

/** Charge les réponses (vide, car on ne veut plus utiliser le localStorage). */
export function loadAnswers(): Record<string, any> {
  return {}
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

/** Sauvegarde les réponses (désactivé pour le localStorage). */
export function saveAnswers(answers: Record<string, any>) {
  void answers
  // Ne rien faire pour ne pas stocker en local
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

/** Charge la progression (désactivé pour le localStorage). */
export function loadProgress(): Partial<Record<Category, string>> {
  return {}
}

/** Sauvegarde la progression (désactivé pour le localStorage). */
export function saveProgress(progress: Partial<Record<Category, string>>) {
  void progress
  // Ne rien faire pour ne pas stocker en local
}
