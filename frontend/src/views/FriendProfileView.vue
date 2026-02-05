<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import { useFriendsStore, type FriendProfile } from '@/stores/friends'
import { useRoute, useRouter } from 'vue-router'
import { onMounted, ref, computed } from 'vue'

const store = useFriendsStore()
const route = useRoute()
const router = useRouter()
const profile = ref<FriendProfile | null>(null)
const loading = ref(true)
const error = ref('')

const confirmState = ref<{ open: boolean; id: number | null; name: string }>({
  open: false,
  id: null,
  name: '',
})

const isBlurred = computed(() => confirmState.value.open)

onMounted(async () => {
  const idStr = route.params.id as string
  if (!idStr) {
    error.value = 'ID manquant'
    loading.value = false
    return
  }
  const id = parseInt(idStr)
  try {
    profile.value = await store.fetchFriendProfile(id)
  } catch {
    error.value = 'Impossible de charger le profil'
  } finally {
    loading.value = false
  }
})

function openRemove() {
  if (!profile.value) return
  confirmState.value = { open: true, id: profile.value.id, name: profile.value.username }
}

function closeRemove() {
  confirmState.value = { open: false, id: null, name: '' }
}

async function confirmRemove() {
  if (!confirmState.value.id) return
  await store.removeFriend(confirmState.value.id)
  closeRemove()
  router.push('/communaute/amis')
}

const goBack = () => router.push('/communaute/amis')

// For progress bar
const progressProps = computed(() => ({
  value: profile.value?.xp || 0,
  max: 100,
}))
</script>

<template>
  <div class="dashboard-wrapper">
    <Header
      title="Profil Ami"
      :showResumeBtn="true"
      resumeBtnLabel="Retour"
      @resumeLater="goBack"
    />
    <div class="scrollable-area" :class="{ 'blurred-content': isBlurred }">
      <div v-if="loading" class="loading">Chargement...</div>
      <div v-else-if="error" class="error">{{ error }}</div>
      <div v-else-if="profile" class="profile-container">
        <div v-if="profile.profile_image" class="avatar-large avatar-image">
          <img :src="profile.profile_image" :alt="'Image de profil'" />
        </div>
        <div v-else class="avatar-large">{{ profile.username.charAt(0).toUpperCase() }}</div>
        <h2 class="username">{{ profile.username }}</h2>

        <div class="level-section">
          <span class="level-text">Niveau {{ profile.level }}</span>
          <ProgressBar
            :value="progressProps.value"
            :max="progressProps.max"
            :showLabel="false"
            class="xp-bar"
          />
        </div>

        <div class="stats-grid">
          <div class="stat-card">
            <span class="stat-value">{{ profile.mission_count }}</span>
            <span class="stat-label">Missions terminées</span>
          </div>
          <div class="stat-card">
            <span class="stat-value">{{ profile.trophy_count }}</span>
            <span class="stat-label">Trophées</span>
          </div>
        </div>

        <button class="delete-btn" @click="openRemove">Supprimer des amis</button>
      </div>
    </div>

    <!-- Pop-up de confirmation -->
    <div v-if="confirmState.open" class="confirm-overlay">
      <div class="confirm-modal">
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
.loading,
.error {
  text-align: center;
  margin-top: 2rem;
  color: #666;
}
.profile-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  gap: 1.5rem;
}

.avatar-large {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background-color: #679436;
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 3rem;
  font-weight: bold;
  overflow: hidden;
}

.avatar-image {
  background-color: transparent;
  padding: 0;
}

.avatar-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.username {
  font-size: 1.5rem;
  color: #000;
}

.level-section {
  width: 100%;
  max-width: 300px;
  display: flex;
  flex-direction: row;
  gap: 1rem;
  align-items: center;
}

.level-text {
  font-weight: 400;
  white-space: nowrap;
}

.xp-bar {
  width: 100%;
  height: 10px;
}

.stats-grid {
  display: flex;
  gap: 1rem;
  margin: 1rem 0;
}

.stat-card {
  background: white;
  padding: 1rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 120px;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #679436;
}

.stat-label {
  font-size: 0.8rem;
  color: #666;
  text-align: center;
}

.delete-btn {
  background-color: #ff4d4d;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  margin-top: 1rem;
}
.delete-btn:hover {
  background-color: #e60000;
}

/* Copié de FriendsView.vue pour le style popup - à centraliser potentiellement */
.blurred-content {
  filter: blur(4px);
  pointer-events: none;
  user-select: none;
}

.confirm-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 999;
  display: flex;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.2); /* Fond semi-transparent */
}

.confirm-modal {
  background: white;
  padding: 1.5rem;
  border-radius: 12px;
  width: 80%;
  max-width: 300px;
  text-align: center;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
}

.confirm-modal h3 {
  margin-top: 0;
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
}

.confirm-modal p {
  color: #666;
  margin-bottom: 1.5rem;
  font-size: 0.95rem;
}

.confirm-actions {
  display: flex;
  justify-content: space-around;
  gap: 1rem;
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
