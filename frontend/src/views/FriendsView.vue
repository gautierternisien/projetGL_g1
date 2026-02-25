<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import { useFriendsStore } from '@/stores/friends'
import { resolveProfileImage } from '@/utils/profileImage'
import { useRouter } from 'vue-router'
import { onMounted, ref, computed } from 'vue'

const store = useFriendsStore()
const router = useRouter()
const activeTab = ref(0)

const tabs = [
  { id: 0, label: "Liste\nd'amis" },
  { id: 2, label: 'Nouvelles\ndemandes' },
  { id: 1, label: 'Demandes\nen attente' },
]

const confirmState = ref<{ open: boolean; id: number | null; name: string }>({
  open: false,
  id: null,
  name: '',
})

const isBlurred = computed(() => confirmState.value.open)

function goAdd() {
  router.push({ name: 'CommunityFriendsAdd' })
}

onMounted(async () => {
  try {
    await store.fetchFriends()
    await store.fetchPendingRequests()
    await store.fetchIncomingRequests()
  } catch {
    // silent fallback
  }
})

function openRemove(id: number, name: string) {
  confirmState.value = { open: true, id, name }
}

function closeRemove() {
  confirmState.value = { open: false, id: null, name: '' }
}

async function confirmRemove() {
  if (!confirmState.value.id) return
  await store.removeFriend(confirmState.value.id)
  closeRemove()
}

async function acceptRequest(requestId: number) {
  await store.acceptRequest(requestId)
}

async function rejectRequest(requestId: number) {
  await store.rejectRequest(requestId)
}

async function cancelRequest(requestId: number) {
  await store.cancelRequest(requestId)
}

function goToProfile(id: number) {
  router.push({ name: 'CommunityFriendProfile', params: { id } })
}

const goBack = () => router.push('/communaute')
</script>

<template>
  <div class="dashboard-wrapper">
    <Header
      title="Liste d'amis"
      :showResumeBtn="true"
      resumeBtnLabel="Retour"
      @resumeLater="goBack"
    />
    <div class="scrollable-area" :class="{ 'blurred-content': isBlurred }">
      <div class="tabs">
        <button
          v-for="t in tabs"
          :key="t.id"
          :class="['tab-btn', { active: activeTab === t.id }]"
          @click="activeTab = t.id"
        >
          {{ t.label }}
          <span v-if="t.id === 2 && store.incomingRequests.length > 0" class="badge">
            {{ store.incomingRequests.length }}
          </span>
        </button>
      </div>

      <!-- Onglet 0: Liste d'amis -->
      <div v-if="activeTab === 0">
        <div class="top-actions">
          <button class="add-btn" @click="goAdd">➕ Ajouter un ami</button>
        </div>

        <div v-if="store.friends.length" class="friends-list">
          <div
            v-for="f in store.friends"
            :key="f.id"
            @click="goToProfile(f.id)"
            class="friend-item"
          >
            <div v-if="resolveProfileImage(f.profile_image)" class="avatar avatar-image">
              <img :src="resolveProfileImage(f.profile_image)" :alt="'Image de profil'" />
            </div>
            <div v-else class="avatar">{{ f.username.charAt(0).toUpperCase() }}</div>
            <div class="name">{{ f.username }}</div>
            <button class="remove-btn" @click.stop="openRemove(f.id, f.username)">✕</button>
          </div>
        </div>
        <div v-else class="placeholder-content">
          <span class="emoji">👥</span>
          <p>Ajoutez vos amis pour les voir ici</p>
        </div>
      </div>

      <!-- Onglet 1: Demandes en attente -->
      <div v-if="activeTab === 1">
        <div v-if="store.pendingRequests.length" class="requests-list">
          <div v-for="r in store.pendingRequests" :key="r.id" class="request-item pending">
            <div v-if="resolveProfileImage(r.receiver.profile_image)" class="avatar avatar-image">
              <img :src="resolveProfileImage(r.receiver.profile_image)" :alt="'Image de profil'" />
            </div>
            <div v-else class="avatar">{{ r.receiver.username.charAt(0).toUpperCase() }}</div>
            <div class="request-info">
              <div class="name">{{ r.receiver.username }}</div>
              <div class="status">Demande en attente</div>
            </div>
            <button class="cancel-btn" @click="cancelRequest(r.id)">✕</button>
          </div>
        </div>
        <div v-else class="placeholder-content">
          <span class="emoji">⏳</span>
          <p>Aucune demande en attente</p>
        </div>
      </div>

      <!-- Onglet 2: Nouvelles demandes -->
      <div v-if="activeTab === 2">
        <div v-if="store.incomingRequests.length" class="requests-list">
          <div v-for="r in store.incomingRequests" :key="r.id" class="request-item incoming">
            <div v-if="resolveProfileImage(r.sender.profile_image)" class="avatar avatar-image">
              <img :src="resolveProfileImage(r.sender.profile_image)" :alt="'Image de profil'" />
            </div>
            <div v-else class="avatar">{{ r.sender.username.charAt(0).toUpperCase() }}</div>
            <div class="request-info">
              <div class="name">{{ r.sender.username }}</div>
              <div class="status">Demande reçue</div>
            </div>
            <div class="request-actions">
              <button class="reject-btn" @click="rejectRequest(r.id)">Refuser</button>
              <button class="accept-btn" @click="acceptRequest(r.id)">Accepter</button>
            </div>
          </div>
        </div>
        <div v-else class="placeholder-content">
          <span class="emoji">📬</span>
          <p>Aucune nouvelle demande</p>
        </div>
      </div>
    </div>

    <div v-if="confirmState.open" class="blur-overlay">
      <div class="confirm-box">
        <h3>Supprimer {{ confirmState.name }} ?</h3>
        <p>Cette personne sera retirée de votre liste d'amis.</p>
        <div class="confirm-actions">
          <button @click="closeRemove" class="cancel-btn">Annuler</button>
          <button @click="confirmRemove" class="confirm-btn">Supprimer</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* .dashboard-wrapper est dans global.css */
.blurred-content {
  filter: blur(4px);
  pointer-events: none;
  user-select: none;
}

.tabs {
  display: flex;
  gap: 8px;
  margin: 12px 0 18px;
  align-items: center;
}

.tab-btn {
  padding: 8px 12px;
  border-radius: 8px;
  border: none;
  background: #f0f0f0;
  cursor: pointer;
  width: 100%;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  white-space: pre-line;
  font-family: 'Instrument Sans', sans-serif;
  line-height: 1.2;
  position: relative; /* Pour positionner le badge */
}

.badge {
  position: absolute;
  top: -5px;
  right: -5px;
  background-color: #ff4d4d;
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
  min-width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid white;
}

.tab-btn.active {
  background: #679436;
  color: white;
}

.top-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.add-btn {
  background: #e0f5e9;
  border: 1px solid #bfe8cd;
  color: #1f7a3a;
  border-radius: 10px;
  padding: 8px 12px;
  cursor: pointer;
}

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
  color: #666;
  gap: 20px;
}

.emoji {
  font-size: 4rem;
}

.friends-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.friend-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f7f9f5;
  color: #1f2a2c;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #dbe5d3;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e3eddd;
  color: #2f3b2f;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
  overflow: hidden;
}

.avatar-image {
  background: transparent;
  padding: 0;
}

.avatar-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.name {
  flex: 1;
}

.remove-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f4e5e5;
  color: #b23b3b;
  border: 1px solid #e7caca;
  font-size: 1rem;
  cursor: pointer;
  flex-shrink: 0;
}

.requests-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.request-item {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #f5f5f5;
  padding: 12px;
  border-radius: 12px;
  border-left: 4px solid;
}

.request-item.pending {
  border-left-color: #ffa500;
}

.request-item.incoming {
  border-left-color: #679436;
}

.request-info {
  flex: 1;
}

.request-info .name {
  font-weight: 600;
  margin-bottom: 4px;
}

.request-info .status {
  font-size: 0.85rem;
  color: #666;
}

.request-actions {
  display: flex;
  gap: 8px;
}

.accept-btn {
  background: #679436;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.reject-btn {
  background: #f44336;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.cancel-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #f8d7b3;
  color: #d97706;
  border: 1px solid #ffa500;
  font-size: 1rem;
  cursor: pointer;
  flex-shrink: 0;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.blur-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1000;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.6);
}

.confirm-box {
  background: white;
  padding: 1.5rem;
  border-radius: 16px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 85%;
  max-width: 320px;
  animation: popIn 0.2s ease-out;
  font-family: 'Instrument Sans', sans-serif;
}

@keyframes popIn {
  from {
    transform: scale(0.9);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}

.confirm-box h3 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 1.1rem;
}

.confirm-box p {
  color: #666;
  margin-bottom: 16px;
}

.confirm-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.confirm-actions .cancel-btn {
  background-color: #f0f0f0;
  color: #333;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  flex: 1;
  font-size: 1rem;
  height: auto;
  width: auto;
}

.confirm-actions .confirm-btn {
  background-color: #ff4d4d;
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  flex: 1;
  font-size: 1rem;
}
</style>
