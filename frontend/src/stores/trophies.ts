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

export const useTrophiesStore = defineStore('trophies', () => {
  const obtainedTrophies = ref<Trophy[]>([])

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

  return {
    obtainedTrophies,
    fetchObtainedTrophies
  }
})
