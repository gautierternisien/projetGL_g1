/**
 * Résout l'URL d'une image de profil.
 *
 * Accepte :
 *  - un nom court : "plante1.png" ou "plante1"
 *  - une URL complète déjà résolue (ancien format) : retournée telle quelle
 */

// Pré-résolution des URLs avec import.meta.url (nécessaire pour Vite)
const imageMap: Record<string, string> = {
  'plante1.png': new URL('../components/image_profil/plante1.png', import.meta.url).href,
  'plante2.png': new URL('../components/image_profil/plante2.png', import.meta.url).href,
  'plante3.png': new URL('../components/image_profil/plante3.png', import.meta.url).href,
  'plante4.png': new URL('../components/image_profil/plante4.png', import.meta.url).href,
  'plante5.png': new URL('../components/image_profil/plante5.png', import.meta.url).href,
  'plante6.png': new URL('../components/image_profil/plante6.png', import.meta.url).href,
}

export function resolveProfileImage(value?: string | null): string | undefined {
  if (!value) return undefined

  // Si c'est déjà une URL complète (http, blob, data, /src, /assets), la retourner telle quelle
  if (
    value.startsWith('http') ||
    value.startsWith('blob:') ||
    value.startsWith('data:') ||
    value.startsWith('/src/') ||
    value.startsWith('/assets/')
  ) {
    return value
  }

  // Normaliser : ajouter .png si absent
  const key = value.endsWith('.png') ? value : `${value}.png`

  return imageMap[key] || undefined
}

