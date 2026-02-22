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
  milestoneKey: string
}

const getSeenTrophiesKey = (userId: number) => `seen_trophy_ids_${userId}`

export const useTrophiesStore = defineStore('trophies', () => {
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

  function getAllAchievedMilestones(trophy: Trophy): Array<{ key: string; label: string; icon: string; value: number }> {
    const progress = trophy.progress || 0
    const finalValue = trophy.requirement_value || 5
    const milestones = trophy.milestones || []
    const achieved: Array<{ key: string; label: string; icon: string; value: number }> = []
    
    // Ajouter tous les milestones atteints
    for (const milestone of milestones) {
      if (progress >= milestone.value) {
        achieved.push({
          key: `${trophy.id}_milestone_${milestone.value}`,
          label: milestone.label,
          icon: milestone.icon,
          value: milestone.value
        })
      }
    }
    
    // Ajouter le trophée final si atteint
    if (progress >= finalValue) {
      achieved.push({
        key: `${trophy.id}_final`,
        label: 'Trophée',
        icon: trophy.icon || '🏆',
        value: finalValue
      })
    }
    
    // Trier par valeur croissante pour notifier du plus petit au plus grand
    return achieved.sort((a, b) => a.value - b.value)
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
        
        // Créer un Set de tous les milestones actuellement atteints
        const currentMilestoneKeys = new Set<string>()
        trophies.forEach(trophy => {
          const achieved = getAllAchievedMilestones(trophy)
          achieved.forEach(m => currentMilestoneKeys.add(m.key))
        })
        
        // Nettoyer le localStorage : retirer les milestones vus qui ne sont plus atteints
        const cleanedSeenIds = new Set<string>()
        seenIds.forEach(seenKey => {
          if (currentMilestoneKeys.has(seenKey)) {
            cleanedSeenIds.add(seenKey)
          }
        })
        
        // Sauvegarder la liste nettoyée
        if (cleanedSeenIds.size !== seenIds.size) {
          saveSeenTrophyIds(userId, cleanedSeenIds)
        }
        
        // En mode silencieux, marquer tous les milestones comme vus sans notification
        if (silent) {
          saveSeenTrophyIds(userId, currentMilestoneKeys)
          newTrophyNotification.value = null
          return
        }
        
        // Trouver le premier nouveau milestone non vu
        for (const trophy of trophies) {
          const achievedMilestones = getAllAchievedMilestones(trophy)
          
          for (const milestone of achievedMilestones) {
            if (!cleanedSeenIds.has(milestone.key)) {
              // Nouveau milestone trouvé !
              newTrophyNotification.value = { 
                trophy, 
                milestone: milestone.label,
                milestoneIcon: milestone.icon,
                milestoneKey: milestone.key
              }
              return
            }
          }
        }
        
        newTrophyNotification.value = null
      }
    } catch (error) {
      console.error('Erreur lors de la vérification des trophées:', error)
    }
  }

  function markMilestoneAsSeen(userId: number, milestoneKey: string) {
    const seenIds = getSeenTrophyIds(userId)
    seenIds.add(milestoneKey)
    saveSeenTrophyIds(userId, seenIds)
    newTrophyNotification.value = null
  }

  function dismissNotification(userId: number) {
    if (newTrophyNotification.value) {
      markMilestoneAsSeen(userId, newTrophyNotification.value.milestoneKey)
    }
  }

  return {
    newTrophyNotification,
    checkNewTrophies,
    dismissNotification
  }
})
