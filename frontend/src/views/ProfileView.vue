<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import Card from '@/components/AppCard.vue'
import ProgressBar from '@/components/ProgressBar.vue'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { useRouter } from 'vue-router'
import { onMounted, ref, onUnmounted, computed } from 'vue'

const authStore = useAuthStore()
const uiStore = useUiStore()
const router = useRouter()
const showLogoutConfirm = ref(false)
const showDeleteConfirm = ref(false)
const selectedProfileImage = ref<string | undefined>(undefined)

const userLevel = computed(() => {
  return Math.floor(userXp.value / 100) + 1
})
const userXp = computed(() => authStore.user?.xp || 0)

onMounted(async () => {
  if (!authStore.isConnected) {
    router.push('/login')
  } else {
    authStore.fetchUser()
    // Initialiser l'image de profil depuis les données utilisateur
    if (authStore.user?.profile_image) {
      selectedProfileImage.value = authStore.user.profile_image
    }
  }
})

onUnmounted(() => {
  // Ensure blur is removed if we leave the page while popup is open
  uiStore.setNavigationBlur(false)
})

function handleLogoutClick() {
  showLogoutConfirm.value = true
  uiStore.setNavigationBlur(true)
}

function confirmLogout() {
  uiStore.setNavigationBlur(false)
  authStore.logout()
  router.push('/')
}

function cancelLogout() {
  showLogoutConfirm.value = false
  uiStore.setNavigationBlur(false)
}

function handleDeleteClick() {
  showDeleteConfirm.value = true
  uiStore.setNavigationBlur(true)
}

async function confirmDelete() {
  try {
    await authStore.deleteUser()
    uiStore.setNavigationBlur(false)
    router.push('/')
  } catch (error) {
    console.error('Erreur lors de la suppression:', error)
    // Gérer l'erreur, peut-être afficher un message
  }
}

function cancelDelete() {
  showDeleteConfirm.value = false
  uiStore.setNavigationBlur(false)
}

function navigateToEditProfile() {
  router.push('/profile/edit')
}

const xpProgress = computed(() => {
  const xp = userXp.value
  return xp % 100 // Comme un niveau = 100pts, le modulo nous donne le % directement
})
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Profil" />
    <div class="scrollable-area">
      <div
        class="profile-content"
        v-if="authStore.user"
        :class="{ 'blurred-content': showLogoutConfirm || showDeleteConfirm }"
      >
        <!-- Message de bienvenue centré -->
        <div class="welcome-message">
          <h2>Bonjour, {{ authStore.user.username }} !</h2>
        </div>

        <!-- Icône de profil -->
        <div class="profile-icon-container">
          <div v-if="selectedProfileImage" class="profile-icon">
            <img :src="selectedProfileImage" :alt="'Image de profil'" class="profile-icon-image" />
          </div>
          <div v-else class="profile-icon">
            {{ authStore.user.username.charAt(0).toUpperCase() }}
          </div>
        </div>

        <div class="xp-container">
          <div class="xp-info">
            <span class="level-badge">Niveau {{ userLevel }}</span>
            <span class="xp-text">{{ userXp }} XP</span>
          </div>
          <ProgressBar
            :value="xpProgress"
            :max="100"
            :showLabel="false"
            class="xp-progress-bar"
            color="#679436"
          />
          <div class="xp-next-level">{{ 100 - xpProgress }} pts avant le niveau suivant</div>
        </div>

        <!-- Boutons sous l'icône -->
        <div class="action-buttons">
          <button @click="navigateToEditProfile" class="edit-profile-btn">✏️ Modifier profil</button>
          <button @click="handleDeleteClick" class="delete-btn">🗑️ Supprimer mon compte</button>
          <button @click="handleLogoutClick" class="logout-btn-small">Se déconnecter</button>
        </div>

        <!-- Informations du profil -->
        <div class="user-info">
          <p><strong>Email:</strong> {{ authStore.user.email }}</p>
          <p v-if="authStore.user.first_name">
            <strong>Prénom:</strong> {{ authStore.user.first_name }}
          </p>
          <p v-if="authStore.user.last_name">
            <strong>Nom:</strong> {{ authStore.user.last_name }}
          </p>
        </div>

        <!-- Trophées -->
        <div class="menu-section">
          <div class="menu-item" @click="router.push('/trophees')">
            <Card :hasArrow="true">
              <div class="card-inner">
                <span class="emoji">🏆</span>
                <span class="label">Mes Trophées</span>
              </div>
            </Card>
          </div>
        </div>
      </div>
      <div v-else class="placeholder-content">
        <p>Chargement du profil...</p>
      </div>
    </div>

    <!-- Popup de confirmation -->
    <div v-if="showLogoutConfirm" class="blur-overlay">
      <div class="confirm-box">
        <h3>Se déconnecter ?</h3>
        <p>Êtes-vous sûr de vouloir vous déconnecter ?</p>
        <div class="confirm-actions">
          <button @click="cancelLogout" class="cancel-btn">Annuler</button>
          <button @click="confirmLogout" class="confirm-btn">Se déconnecter</button>
        </div>
      </div>
    </div>

    <!-- Popup de confirmation suppression -->
    <div v-if="showDeleteConfirm" class="blur-overlay">
      <div class="confirm-box">
        <h3>Supprimer mon compte ?</h3>
        <p>Cette action est irréversible. Votre compte sera marqué comme supprimé et vous ne pourrez plus vous connecter.</p>
        <div class="confirm-actions">
          <button @click="cancelDelete" class="cancel-btn">Annuler</button>
          <button @click="confirmDelete" class="delete-confirm-btn">Supprimer</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.profile-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  transition: filter 0.3s ease;
  align-items: center;
}

.blurred-content {
  filter: blur(5px);
  pointer-events: none;
  user-select: none;
}

.welcome-message {
  text-align: center;
  width: 100%;
}

.welcome-message h2 {
  margin: 0;
  font-size: 1.5rem;
}

.profile-icon-container {
  display: flex;
  justify-content: center;
  margin: 1rem 0;
}

.profile-icon {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: linear-gradient(135deg, #679436 0%, #8ab858 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  overflow: hidden;
  flex-shrink: 0;
}

.profile-icon-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.action-buttons {
  display: flex;
  gap: 0.75rem;
  justify-content: center;
  width: 100%;
  flex-wrap: wrap;
}

.edit-profile-btn {
  background-color: #679436;
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
}

.delete-btn {
  background-color: #dc3545;
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
}

.logout-btn-small {
  background-color: #ff4d4d;
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  text-align: left;
  width: 100%;
  background: #f9f9f9;
  padding: 1.25rem;
  border-radius: 12px;
}

.menu-section {
  width: 100%;
}

.menu-item {
  cursor: pointer;
}

.card-inner {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 500;
}

.emoji {
  font-size: 1.5rem;
}

.placeholder-content {
  padding: 20px;
  text-align: center;
  color: #666;
}

/* Popup Styles */
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
  padding: 2rem;
  border-radius: 16px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 85%;
  max-width: 320px;
  animation: popIn 0.2s ease-out;
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
  font-size: 1.2rem;
}

.confirm-box p {
  color: #666;
  margin-bottom: 20px;
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
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  flex: 1;
}

.confirm-btn {
  background-color: #ff4d4d;
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  flex: 1;
}

.delete-confirm-btn {
  background-color: #dc3545;
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  flex: 1;
}

/* --- Styles pour l'XP --- */
.xp-container {
  width: 100%;
  margin-bottom: 1.5rem;
  padding: 0 10px;
}

.xp-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.level-badge {
  background-color: #679436;
  color: white;
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 0.9rem;
}

.xp-text {
  font-weight: 600;
  color: #555;
  font-size: 0.9rem;
}

.xp-next-level {
  text-align: right;
  font-size: 0.75rem;
  color: #888;
  margin-top: 4px;
  font-style: italic;
}

.xp-progress-bar {
  height: 12px; /* Un peu plus épais pour le profil */
}
</style>
