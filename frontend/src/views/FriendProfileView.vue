<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import { useFriendsStore, type FriendProfile } from '@/stores/friends'
import { resolveProfileImage } from '@/utils/profileImage'
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

  try {
    profile.value = await store.fetchFriendProfile(parseInt(idStr, 10))
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

const friendXp = computed(() => profile.value?.xp || 0)

const friendLevel = computed(() => Math.floor(friendXp.value / 100) + 1)

const xpProgress = computed(() => friendXp.value % 100)

const medalsSummary = computed(() => ({
  trophee: profile.value?.medals_summary?.trophee ?? profile.value?.trophy_count ?? 0,
  or: profile.value?.medals_summary?.or ?? 0,
  argent: profile.value?.medals_summary?.argent ?? 0,
  bronze: profile.value?.medals_summary?.bronze ?? 0,
}))

const missionsStats = computed(() => ({
  total: profile.value?.mission_count ?? 0,
  transport: profile.value?.missions_by_category?.transport ?? 0,
  logement: profile.value?.missions_by_category?.logement ?? 0,
  alimentation: profile.value?.missions_by_category?.alimentation ?? 0,
  divers: profile.value?.missions_by_category?.divers ?? 0,
}))

const missionItems = computed(() => [
  { key: 'transport', label: 'Transport', emoji: '🚗', value: missionsStats.value.transport },
  { key: 'logement', label: 'Logement', emoji: '🏠', value: missionsStats.value.logement },
  { key: 'alimentation', label: 'Alimentation', emoji: '🍽️', value: missionsStats.value.alimentation },
  { key: 'divers', label: 'Divers', emoji: '📦', value: missionsStats.value.divers },
])
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
        <div v-if="resolveProfileImage(profile.profile_image)" class="avatar-large avatar-image">
          <img :src="resolveProfileImage(profile.profile_image)" :alt="'Image de profil'" />
        </div>
        <div v-else class="avatar-large">{{ profile.username.charAt(0).toUpperCase() }}</div>

        <h2 class="username">{{ profile.username }}</h2>

        <div class="level-section">
          <span class="level-text">Niveau {{ friendLevel }}</span>
          <ProgressBar
            :value="xpProgress"
            :max="100"
            :showLabel="false"
            class="xp-progress-bar"
            color="#679436"
          />
        </div>

        <div class="summary-card">
          <h3 class="summary-title">Trophées obtenus</h3>
          <div class="medals-summary">
            <div class="medal-item">
              <span class="medal-icon">🏆</span>
              <span class="medal-label">Trophée</span>
              <span class="medal-count">x{{ medalsSummary.trophee }}</span>
            </div>
            <div class="medal-item">
              <span class="medal-icon">🥇</span>
              <span class="medal-label">Or</span>
              <span class="medal-count">x{{ medalsSummary.or }}</span>
            </div>
            <div class="medal-item">
              <span class="medal-icon">🥈</span>
              <span class="medal-label">Argent</span>
              <span class="medal-count">x{{ medalsSummary.argent }}</span>
            </div>
            <div class="medal-item">
              <span class="medal-icon">🥉</span>
              <span class="medal-label">Bronze</span>
              <span class="medal-count">x{{ medalsSummary.bronze }}</span>
            </div>
          </div>
        </div>

        <div class="summary-card">
          <h3 class="summary-title">Missions réalisées</h3>
          <div class="missions-grid">
            <div class="mission-item mission-total">
              <span class="mission-icon">🎯</span>
              <span class="mission-label">Total</span>
              <span class="mission-count">{{ missionsStats.total }}</span>
            </div>

            <div
              v-for="item in missionItems"
              :key="item.key"
              class="mission-item"
            >
              <span class="mission-icon">{{ item.emoji }}</span>
              <span class="mission-label">{{ item.label }}</span>
              <span class="mission-count">{{ item.value }}</span>
            </div>
          </div>
        </div>

        <button class="delete-btn" @click="openRemove">Supprimer des amis</button>
      </div>
    </div>

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
  padding: 1.5rem 1rem 2.2rem;
  gap: 1.2rem;
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
  font-size: 1.45rem;
  color: #111;
  margin: 0;
}

.level-section {
  width: 100%;
  max-width: 360px;
  display: flex;
  flex-direction: row;
  gap: 0.85rem;
  align-items: center;
}

.level-text {
  font-weight: 500;
  white-space: nowrap;
}

.xp-progress-bar {
  flex: 1;
}

.summary-card {
  width: 100%;
  max-width: 360px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e5e5e5;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.08);
  padding: 0.95rem;
}

.summary-title {
  margin: 0 0 0.85rem;
  font-size: 1rem;
  color: #679436;
  text-align: center;
}

.medals-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.45rem;
}

.medal-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.2rem;
}

.medal-icon {
  font-size: 1.2rem;
}

.medal-label {
  font-size: 0.74rem;
  color: #666;
}

.medal-count {
  font-size: 0.95rem;
  font-weight: 700;
  color: #333;
}

.missions-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.55rem;
}

.mission-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.45rem;
  border-radius: 8px;
  padding: 0.45rem 0.55rem;
  background: #f7f7f7;
}

.mission-total {
  grid-column: span 2;
  background: #eef6e4;
}

.mission-icon {
  font-size: 1rem;
}

.mission-label {
  flex: 1;
  font-size: 0.82rem;
  color: #555;
}

.mission-count {
  font-weight: 700;
  color: #222;
  font-size: 0.95rem;
}

.delete-btn {
  background-color: #ff4d4d;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 0.35rem;
}

.delete-btn:hover {
  background-color: #e60000;
}

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
  background-color: rgba(0, 0, 0, 0.2);
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
