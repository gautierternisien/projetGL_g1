<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import { onMounted, ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useFriendsStore, type UserSummary } from '@/stores/friends'

const router = useRouter()
const store = useFriendsStore()
const query = ref('')
const results = ref<UserSummary[]>([])
const loading = ref(false)
const error = ref('')
const success = ref('')

const confirmState = ref<{ open: boolean; user: UserSummary | null }>({
  open: false,
  user: null,
})

const isBlurred = computed(() => confirmState.value.open)

watch(query, async (val) => {
  if (val.trim().length < 3) {
    results.value = []
    return
  }
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    results.value = await store.searchUsers(val)
  } catch {
    error.value = 'Recherche impossible'
  } finally {
    loading.value = false
  }
})

onMounted(async () => {
  try {
    await store.fetchFriends()
    await store.fetchIncomingRequests()
  } catch {
    // silent fallback
  }
})

function isIncoming(userId: number) {
  return store.incomingRequests.some((req) => req.sender.id === userId)
}

function getIncomingRequestId(userId: number) {
  const req = store.incomingRequests.find((r) => r.sender.id === userId)
  return req ? req.id : null
}

function openAdd(userId: number) {
  const user = results.value.find((u) => u.id === userId) || null
  confirmState.value = { open: true, user }
}

function closeAdd() {
  confirmState.value = { open: false, user: null }
}

async function confirmAdd() {
  if (!confirmState.value.user) return

  // Si c'est une demande entrante, on ne fait rien ici (les boutons Accepter/Refuser s'en chargent)
  // Mais si on utilise le bouton "Envoyer" standard, on garde le comportement sendFriendRequest
  // qui fera l'auto-accept côté backend.
  // Cependant, l'utilisateur veut des boutons "Accepter" / "Refuser" explicites.

  await store.sendFriendRequest(confirmState.value.user.id)
  success.value = `Demande d'ami envoyée à ${confirmState.value.user.username}`
  closeAdd()
  router.push({ name: 'CommunityFriends' })
}

async function handleAccept() {
  if (!confirmState.value.user) return
  const reqId = getIncomingRequestId(confirmState.value.user.id)
  if (reqId) {
    await store.acceptRequest(reqId)
    success.value = `Vous êtes maintenant ami avec ${confirmState.value.user.username}`
    closeAdd()
    router.push({ name: 'CommunityFriends' })
  }
}

async function handleReject() {
  if (!confirmState.value.user) return
  const reqId = getIncomingRequestId(confirmState.value.user.id)
  if (reqId) {
    await store.rejectRequest(reqId)
    success.value = `Demande refusée`
    closeAdd()
    // On peut rester sur la page ou recharger les requêtes
    await store.fetchIncomingRequests()
  }
}

const goBack = () => router.push('/communaute/amis')
</script>

<template>
  <div class="dashboard-wrapper">
    <Header
      title="Ajouter un ami"
      :showResumeBtn="true"
      resumeBtnLabel="Retour"
      @resumeLater="goBack"
    />
    <div class="scrollable-area" :class="{ 'blurred-content': isBlurred }">
      <div class="search-box">
        <label for="search">Rechercher par pseudo</label>
        <input id="search" type="text" v-model="query" placeholder="Ex: Ju..." />
      </div>

      <div v-if="loading" class="empty">Recherche...</div>
      <div v-else-if="error" class="empty">{{ error }}</div>
      <div v-else-if="results.length" class="results">
        <div v-for="u in results" :key="u.id" class="result-item">
          <div class="avatar">
            <img v-if="u.profile_image" :src="u.profile_image" :alt="u.username" class="avatar-image" />
            <span v-else>{{ u.username.charAt(0).toUpperCase() }}</span>
          </div>
          <div class="name">{{ u.username }}</div>
          <button class="add-btn" @click="openAdd(u.id)">+</button>
        </div>
      </div>
      <p v-else class="empty">Tapez au moins 3 lettres pour voir des suggestions</p>
      <p v-if="success" class="success-msg">{{ success }}</p>
    </div>
  </div>
  <div v-if="confirmState.open && confirmState.user" class="blur-overlay">
    <div class="confirm-box" v-if="isIncoming(confirmState.user.id)">
      <div class="modal-avatar">
        <img v-if="confirmState.user.profile_image" :src="confirmState.user.profile_image" :alt="confirmState.user.username" class="modal-avatar-image" />
        <span v-else>{{ confirmState.user.username.charAt(0).toUpperCase() }}</span>
      </div>
      <h3>{{ confirmState.user.username }} vous demande en ami</h3>
      <p>Cette personne vous a déjà envoyé une demande.</p>
      <div class="confirm-actions">
        <button @click="handleReject" class="cancel-btn">Refuser</button>
        <button @click="handleAccept" class="confirm-btn">Accepter</button>
      </div>
    </div>
    <div class="confirm-box" v-else>
      <div class="modal-avatar">
        <img v-if="confirmState.user.profile_image" :src="confirmState.user.profile_image" :alt="confirmState.user.username" class="modal-avatar-image" />
        <span v-else>{{ confirmState.user.username.charAt(0).toUpperCase() }}</span>
      </div>
      <h3>Ajouter {{ confirmState.user.username }} ?</h3>
      <p>Une demande d'ami sera envoyée à cette personne.</p>
      <div class="confirm-actions">
        <button @click="closeAdd" class="annuler-btn">Annuler</button>
        <button @click="confirmAdd" class="confirm-btn">Envoyer</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.blurred-content {
  filter: blur(4px);
  pointer-events: none;
  user-select: none;
}

.search-box {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 16px;
}

.search-box input {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid #ccc;
  font-size: 1rem;
}

.results {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-item {
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
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: transparent;
}

.name {
  flex: 1;
}

.add-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #e0f5e9;
  color: #1f7a3a;
  border: 1px solid #bfe8cd;
  font-size: 1.2rem;
  cursor: pointer;
}

.empty {
  color: #666;
}

.success-msg {
  margin-top: 12px;
  color: #1f7a3a;
  font-weight: 600;
}

.blur-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 100;
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

.annuler-btn {
  background-color: #f0f0f0;
  color: #333;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  flex: 1;
}


.cancel-btn {
  background-color: #f44336;
  color: #fff;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  flex: 1;
}

.confirm-btn {
  background-color: #679436;
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  flex: 1;
}

.modal-avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: #e3eddd;
  color: #2f3b2f;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1.5rem;
  margin: 0 auto 1rem;
  overflow: hidden;
}

.modal-avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  background: transparent;
}
</style>
