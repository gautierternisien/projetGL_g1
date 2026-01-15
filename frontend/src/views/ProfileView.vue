<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import Card from '@/components/AppCard.vue'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { useRouter } from 'vue-router'
import { onMounted, ref, onUnmounted } from 'vue'

const authStore = useAuthStore()
const uiStore = useUiStore()
const router = useRouter()
const showLogoutConfirm = ref(false)

onMounted(() => {
  if (!authStore.isConnected) {
    router.push('/login')
  } else {
    authStore.fetchUser()
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
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Profil" />
    <div class="scrollable-area">
      <div
        class="profile-content"
        v-if="authStore.user"
        :class="{ 'blurred-content': showLogoutConfirm }"
      >
        <div class="profile-header">
          <h2>Bonjour, {{ authStore.user.username }} !</h2>
          <button @click="handleLogoutClick" class="logout-btn-small">Se déconnecter</button>
        </div>

        <div class="user-info">
          <p><strong>Email:</strong> {{ authStore.user.email }}</p>
          <p v-if="authStore.user.first_name">
            <strong>Prénom:</strong> {{ authStore.user.first_name }}
          </p>
          <p v-if="authStore.user.last_name">
            <strong>Nom:</strong> {{ authStore.user.last_name }}
          </p>
        </div>

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
  </div>
</template>

<style scoped>
.profile-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  transition: filter 0.3s ease;
}

.blurred-content {
  filter: blur(5px);
  pointer-events: none;
  user-select: none;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
}

.menu-section {
  margin-top: 1rem;
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
</style>
