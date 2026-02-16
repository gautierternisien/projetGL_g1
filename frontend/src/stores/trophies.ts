import { ref } from 'vue'
import { defineStore } from 'pinia'
import { API_URL } from '@/config'

export interface Trophy {
  id: number
  name: string
  title: string
  description: string
  icon: string
  tier: string
  requirement_type?: string
  requirement_value?: number
  progress?: number
  is_obtained?: boolean
  obtained_at?: string
  last_milestone_date?: string
  milestones?: { value: number; label: string; icon: string }[]
}

export interface NewTrophyNotification {
  trophy: Trophy
  milestone: string
  milestoneIcon: string
}

const getSeenTrophiesKey = (userId: number) => `seen_trophy_ids_${userId}`

export const useTrophiesStore = defineStore('trophies', () => {
  const obtainedTrophies = ref<Trophy[]>([])
  const newTrophyNotification = ref<NewTrophyNotification | null>(null)

  function getSeenTrophyIds(userId: number): Set<string> {
    try {
      const stored = localStorage.getItem(getSeenTrophiesKey(userId))
      return stored ? new Set(JSON.parse(stored)) : new Set()
    } catch {
      return new Set()
    }
  }

  function saveSeenTrophyIds(userId: number, ids: Set<string>) {
    try {
      localStorage.setItem(getSeenTrophiesKey(userId), JSON.stringify(Array.from(ids)))
    } catch {
      // ignore
    }
  }

  function getLastObtainedMilestone(trophy: Trophy): { label: string; icon: string } {
    const progress = trophy.progress || 0
    const finalValue = trophy.requirement_value || 5
    const milestones = trophy.milestones || []
    
    // Si le trophée final est obtenu
    if (progress >= finalValue) {
      return { label: 'Trophée', icon: trophy.icon || '🏆' }
    }
    
    // Sinon, trouver la médaille la plus haute obtenue
    const sortedMilestones = [...milestones].sort((a, b) => b.value - a.value)
    for (const milestone of sortedMilestones) {
      if (progress >= milestone.value) {
        return { label: milestone.label, icon: milestone.icon }
      }
    }
    return { label: 'Récompense', icon: '🎁' }
  }

  async function fetchObtainedTrophies(token: string) {
    try {
      const response = await fetch(`${API_URL}/trophies/obtained`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        obtainedTrophies.value = data.trophies || []
      }
    } catch (error) {
      console.error('Erreur lors du chargement des trophées:', error)
    }
  }

  async function checkNewTrophies(token: string, userId: number, silent: boolean = false) {
    try {
      const response = await fetch(`${API_URL}/trophies/obtained`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        const trophies: Trophy[] = data.trophies || []
        const seenIds = getSeenTrophyIds(userId)
        
        // Créer un Set des trophées actuellement obtenus pour nettoyage
        const currentTrophyKeys = new Set(
          trophies.map(t => `${t.id}_${t.progress}`)
        )
        
        // Nettoyer le localStorage : retirer les trophées vus qui ne sont plus obtenus
        const cleanedSeenIds = new Set<string>()
        seenIds.forEach(seenKey => {
          if (currentTrophyKeys.has(seenKey)) {
            cleanedSeenIds.add(seenKey)
          }
        })
        
        // Sauvegarder la liste nettoyée
        if (cleanedSeenIds.size !== seenIds.size) {
          saveSeenTrophyIds(userId, cleanedSeenIds)
        }
        
        // En mode silencieux, marquer tous les trophées comme vus sans notification
        if (silent) {
          const allTrophyKeys = new Set(trophies.map(t => `${t.id}_${t.progress}`))
          saveSeenTrophyIds(userId, allTrophyKeys)
          newTrophyNotification.value = null
          return
        }
        
        // Trouver le premier nouveau trophée non vu
        for (const trophy of trophies) {
          const trophyKey = `${trophy.id}_${trophy.progress}`
          if (!cleanedSeenIds.has(trophyKey)) {
            const milestoneData = getLastObtainedMilestone(trophy)
            newTrophyNotification.value = { 
              trophy, 
              milestone: milestoneData.label,
              milestoneIcon: milestoneData.icon
            }
            return
          }
        }
        
        newTrophyNotification.value = null
      }
    } catch (error) {
      console.error('Erreur lors de la vérification des trophées:', error)
    }
  }

  function markTrophyAsSeen(userId: number, trophyId: number, progress: number) {
    const seenIds = getSeenTrophyIds(userId)
    const trophyKey = `${trophyId}_${progress}`
    seenIds.add(trophyKey)
    saveSeenTrophyIds(userId, seenIds)
    newTrophyNotification.value = null
  }

  function dismissNotification(userId: number) {
    if (newTrophyNotification.value) {
      markTrophyAsSeen(
        userId,
        newTrophyNotification.value.trophy.id,
        newTrophyNotification.value.trophy.progress || 0
      )
    }
  }

  return {
    obtainedTrophies,
    newTrophyNotification,
    fetchObtainedTrophies,
    checkNewTrophies,
    markTrophyAsSeen,
    dismissNotification
  }
})
