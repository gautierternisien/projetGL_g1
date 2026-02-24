import { defineStore } from 'pinia'
import { ref } from 'vue'
import { API_URL } from '@/config'
import { useAuthStore } from './auth'

// Interfaces matching Backend Pydantic models
export interface LeagueMember {
    id: number
    user_id: number
    username: string
    joined_at: string
    missions_completed?: number
}

export interface League {
    id: number
    name: string
    start_date: string
    end_date: string
    is_archived: boolean
    created_at: string
    members_count: number
    start_timestamp: number  // Computed by backend: start_date at 00:00:00 in milliseconds
    end_timestamp: number  // Computed by backend: end_date at 23:59:59 in milliseconds
}

export interface LeagueDetail extends League {
    members: LeagueMember[]
}

export interface LeagueInvite {
    id: number
    league_id: number
    league_name: string
    inviter_id: number
    inviter_name: string
    invitee_id: number
    status: string
}

export interface CreateLeaguePayload {
    name: string
    start_date: string
    end_date: string
}

export const useLeaguesStore = defineStore('leagues', () => {
    const activeLeagues = ref<League[]>([])
    const archivedLeagues = ref<League[]>([])
    const invitations = ref<LeagueInvite[]>([])
    const currentLeague = ref<LeagueDetail | null>(null)

    const auth = useAuthStore()

    function authHeaders() {
        if (!auth.token) throw new Error('Utilisateur non connecté')
        return {
            'Authorization': `Bearer ${auth.token}`,
            'Content-Type': 'application/json'
        }
    }

    async function fetchActiveLeagues() {
        if (!auth.token) return
        const res = await fetch(`${API_URL}/leagues/active`, { headers: authHeaders() })
        if (res.ok) activeLeagues.value = await res.json()
    }

    async function fetchArchivedLeagues() {
        if (!auth.token) return
        const res = await fetch(`${API_URL}/leagues/archived`, { headers: authHeaders() })
        if (res.ok) archivedLeagues.value = await res.json()
    }

    async function fetchInvites() {
        if (!auth.token) return
        const res = await fetch(`${API_URL}/leagues/invites`, { headers: authHeaders() })
        if (res.ok) invitations.value = await res.json()
    }

    async function fetchLeaguePendingInvites(leagueId: number) {
        if (!auth.token) return []
        const res = await fetch(`${API_URL}/leagues/${leagueId}/invites`, { headers: authHeaders() })
        if (res.ok) {
             return await res.json() as LeagueInvite[]
        }
        return []
    }

    async function createLeague(payload: CreateLeaguePayload) {
        const res = await fetch(`${API_URL}/leagues/`, {
            method: 'POST',
            headers: authHeaders(),
            body: JSON.stringify(payload)
        })
        if (!res.ok) throw new Error("Erreur lors de la création de la ligue")
        await fetchActiveLeagues() // Refresh list
        return await res.json()
    }

    async function fetchLeagueDetail(id: number) {
         const res = await fetch(`${API_URL}/leagues/${id}`, { headers: authHeaders() })
         if (!res.ok) throw new Error("Ligue introuvable")
         currentLeague.value = await res.json()
    }

    async function inviteUser(leagueId: number, userId: number) {
        const res = await fetch(`${API_URL}/leagues/${leagueId}/invite/${userId}`, {
            method: 'POST',
            headers: authHeaders()
        })
        if (!res.ok) throw new Error("Impossible d'inviter cet utilisateur")
        return await res.json()
    }

    async function acceptInvite(inviteId: number) {
        const res = await fetch(`${API_URL}/leagues/invites/${inviteId}/accept`, {
            method: 'PUT',
            headers: authHeaders()
        })
        if (!res.ok) throw new Error("Erreur acceptance")
        await fetchInvites()
        await fetchActiveLeagues()
    }

    async function rejectInvite(inviteId: number) {
        const res = await fetch(`${API_URL}/leagues/invites/${inviteId}/reject`, {
            method: 'PUT',
            headers: authHeaders()
        })
        if (!res.ok) throw new Error("Erreur rejet")
        await fetchInvites()
    }

    async function leaveLeague(leagueId: number) {
         const res = await fetch(`${API_URL}/leagues/${leagueId}/leave`, {
            method: 'DELETE',
            headers: authHeaders()
        })
        if (!res.ok) throw new Error("Erreur lors du départ")
        // Refresh local state if current league was the one left
        if (currentLeague.value?.id === leagueId) {
            currentLeague.value = null
        }
        await fetchActiveLeagues()
    }

    return {
        activeLeagues,
        archivedLeagues,
        invitations,
        currentLeague,
        fetchActiveLeagues,
        fetchArchivedLeagues,
        fetchInvites,
        fetchLeaguePendingInvites,
        createLeague,
        fetchLeagueDetail,
        inviteUser,
        acceptInvite,
        rejectInvite,
        leaveLeague
    }
})
