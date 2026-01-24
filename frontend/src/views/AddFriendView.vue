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
  } catch {
    // silent fallback
  }
})

function openAdd(userId: number) {
  const user = results.value.find((u) => u.id === userId) || null
  confirmState.value = { open: true, user }
}

function closeAdd() {
  confirmState.value = { open: false, user: null }
}

async function confirmAdd() {
  if (!confirmState.value.user) return
  await store.sendFriendRequest(confirmState.value.user.id)
  success.value = `Demande d'ami envoyée à ${confirmState.value.user.username}`
  closeAdd()
  router.push({ name: 'CommunityFriends' })
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
          <div class="avatar">{{ u.username.charAt(0).toUpperCase() }}</div>
          <div class="name">{{ u.username }}</div>
          <button class="add-btn" @click="openAdd(u.id)">+</button>
        </div>
      </div>
      <p v-else class="empty">Tapez au moins 3 lettres pour voir des suggestions</p>
      <p v-if="success" class="success-msg">{{ success }}</p>
    </div>
  </div>
  <div v-if="confirmState.open && confirmState.user" class="blur-overlay">
    <div class="confirm-box">
      <h3>Ajouter {{ confirmState.user.username }} ?</h3>
      <p>Une demande d'ami sera envoyée à cette personne.</p>
      <div class="confirm-actions">
        <button @click="closeAdd" class="cancel-btn">Annuler</button>
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

.top-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.back-btn {
  background: #eaeaea;
  border: 1px solid #d0d0d0;
  border-radius: 10px;
  padding: 8px 12px;
  cursor: pointer;
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
  background: #2d4a5b;
  color: #fff;
  padding: 12px;
  border-radius: 12px;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #c9b6ff;
  color: #333;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
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

.cancel-btn {
  background-color: #f0f0f0;
  color: #333;
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
</style>
