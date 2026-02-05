import { ref } from 'vue'
import { defineStore } from 'pinia'
import { API_URL } from '@/config'
import { useAuthStore } from './auth'

export interface UserSummary {
  id: number
  username: string
  profile_image?: string
}

export interface FriendRequest {
  id: number
  sender: UserSummary
  receiver: UserSummary
  status: string
}

export interface FriendActivity {
  friend_username: string
  mission_title: string
  mission_id: number
  status: string
  timestamp?: string
}

export interface FriendProfile {
  id: number
  username: string
  mission_count: number
  trophy_count: number
  level: number
  xp: number
  profile_image?: string
}

export const useFriendsStore = defineStore('friends', () => {
  const friends = ref<UserSummary[]>([])
  const activities = ref<FriendActivity[]>([])
  const pendingRequests = ref<FriendRequest[]>([])
  const incomingRequests = ref<FriendRequest[]>([])

  const auth = useAuthStore()

  function authHeaders() {
    if (!auth.token) throw new Error('Utilisateur non connecté')
    return { Authorization: `Bearer ${auth.token}` }
  }

  async function fetchFriends() {
    if (!auth.token) return
    const res = await fetch(`${API_URL}/friends`, {
      headers: authHeaders(),
    })
    if (!res.ok) throw new Error('Erreur lors du chargement des amis')
    friends.value = await res.json()
  }

  async function fetchFriendProfile(userId: number): Promise<FriendProfile> {
    if (!auth.token) throw new Error('Utilisateur non connecté')
    const res = await fetch(`${API_URL}/users/${userId}/profile`, {
      headers: authHeaders(),
    })
    if (!res.ok) throw new Error('Erreur lors du chargement du profil')
    return await res.json()
  }

  async function fetchPendingRequests() {
    if (!auth.token) return
    const res = await fetch(`${API_URL}/friend-requests/pending`, {
      headers: authHeaders(),
    })
    if (!res.ok) throw new Error('Erreur lors du chargement des demandes')
    pendingRequests.value = await res.json()
  }

  async function fetchIncomingRequests() {
    if (!auth.token) return
    const res = await fetch(`${API_URL}/friend-requests/incoming`, {
      headers: authHeaders(),
    })
    if (!res.ok) throw new Error('Erreur lors du chargement des demandes')
    incomingRequests.value = await res.json()
  }
  async function fetchActivities() {
    if (!auth.token) return
    const res = await fetch(`${API_URL}/friends/activity`, {
      headers: authHeaders(),
    })
    if (!res.ok) throw new Error('Erreur lors du chargement des activités')
    activities.value = await res.json()
  }
  async function sendFriendRequest(userId: number) {
    const res = await fetch(`${API_URL}/friend-requests/${userId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders(),
      },
    })
    if (!res.ok) throw new Error("Impossible d'envoyer la demande")
    return await res.json()
  }

  async function acceptRequest(requestId: number) {
    const res = await fetch(`${API_URL}/friend-requests/${requestId}/accept`, {
      method: 'PUT',
      headers: authHeaders(),
    })
    if (!res.ok) throw new Error("Impossible d'accepter la demande")
    await fetchFriends()
    await fetchIncomingRequests()
  }

  async function rejectRequest(requestId: number) {
    const res = await fetch(`${API_URL}/friend-requests/${requestId}/reject`, {
      method: 'PUT',
      headers: authHeaders(),
    })
    if (!res.ok) throw new Error('Impossible de refuser la demande')
    await fetchIncomingRequests()
  }

  async function removeFriend(userId: number) {
    const res = await fetch(`${API_URL}/friends/${userId}`, {
      method: 'DELETE',
      headers: authHeaders(),
    })
    if (!res.ok) throw new Error('Suppression impossible')
    friends.value = friends.value.filter((f) => f.id !== userId)
  }

  async function cancelRequest(requestId: number) {
    const res = await fetch(`${API_URL}/friend-requests/${requestId}/cancel`, {
      method: 'PUT',
      headers: authHeaders(),
    })
    if (!res.ok) throw new Error("Impossible d'annuler la demande")
    await fetchPendingRequests()
  }

  async function searchUsers(prefix: string): Promise<UserSummary[]> {
    const p = prefix.trim()
    if (!p || p.length < 3 || !auth.token) return []
    const res = await fetch(`${API_URL}/users?prefix=${encodeURIComponent(p)}`, {
      headers: authHeaders(),
    })
    if (!res.ok) throw new Error('Recherche impossible')
    const found: UserSummary[] = await res.json()
    const friendIds = new Set(friends.value.map((f) => f.id))
    const pendingIds = new Set(pendingRequests.value.map((r) => r.receiver.id))
    // Exclure amis et demandes en attente
    return found.filter((u) => !friendIds.has(u.id) && !pendingIds.has(u.id))
  }

  return {
    friends,
    activities,
    pendingRequests,
    incomingRequests,
    fetchFriends,
    fetchFriendProfile,
    fetchActivities,
    fetchPendingRequests,
    fetchIncomingRequests,
    sendFriendRequest,
    acceptRequest,
    rejectRequest,
    removeFriend,
    cancelRequest,
    searchUsers,
  }
})
