export type MissionStatus = 'en_cours' | 'termine' | 'new'

export interface Mission {
  id: number
  title: string
  description?: string
  category?: string
  status?: MissionStatus
  points?: number
}
