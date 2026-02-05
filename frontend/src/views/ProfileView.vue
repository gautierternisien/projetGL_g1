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
const showEditMenu = ref(false)
const editMenuRef = ref<HTMLElement | null>(null)
const showEditModal = ref(false)
const selectedFieldLabel = ref('')
const selectedFieldKey = ref('')
const oldFieldValue = ref('')
const newFieldValue = ref('')
const newFieldType = ref<'text' | 'email' | 'password'>('text')
const currentPassword = ref('')
const modalErrorMessage = ref('')
const showProfileImageModal = ref(false)
const allProfileImages = ref<string[]>([])
const currentImageIndex = ref(0)
const selectedProfileImage = ref<string | undefined>(undefined)

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
  // Charger toutes les images du dossier image_profil
  try {
    const imageNames = ['plante1.png', 'plante2.png', 'plante3.png', 'plante4.png', 'plante5.png', 'plante6.png']
    allProfileImages.value = imageNames.map(name => 
      new URL(`../components/image_profil/${name}`, import.meta.url).href
    )
    currentImageIndex.value = 0
  } catch (e) {
    console.error('Erreur lors du chargement des images:', e)
  }
  // Ajouter un écouteur pour fermer le menu au clic extérieur
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  // Ensure blur is removed if we leave the page while popup is open
  uiStore.setNavigationBlur(false)
  document.removeEventListener('click', handleClickOutside)
})

function handleClickOutside(event: MouseEvent) {
  if (editMenuRef.value && !editMenuRef.value.contains(event.target as Node)) {
    showEditMenu.value = false
  }
}

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

function openProfileImageModal() {
  showProfileImageModal.value = true
  uiStore.setNavigationBlur(true)
}

function closeProfileImageModal() {
  showProfileImageModal.value = false
  uiStore.setNavigationBlur(false)
}

function saveProfileImage() {
  if (allProfileImages.value.length > 0 && currentImageIndex.value < allProfileImages.value.length) {
    const imageUrl = allProfileImages.value[currentImageIndex.value]
    if (imageUrl) {
      selectedProfileImage.value = imageUrl
      // Sauvegarder l'image dans la base de données
      authStore.updateProfileImage(imageUrl)
        .then(() => {
          closeProfileImageModal()
        })
        .catch((e: unknown) => {
          console.error('Erreur lors de la sauvegarde de l\'image:', e)
        })
    }
  }
}

function removeProfileImage() {
  // Si pas d'image, fermer le modal comme si on avait annulé
  if (!selectedProfileImage.value) {
    closeProfileImageModal()
    return
  }
  
  // Sinon, supprimer l'image
  selectedProfileImage.value = undefined
  authStore.removeProfileImage()
    .then(() => {
      closeProfileImageModal()
    })
    .catch((e: unknown) => {
      console.error('Erreur lors de la suppression de l\'image:', e)
    })
}

function nextImage() {
  if (allProfileImages.value.length > 0) {
    currentImageIndex.value = (currentImageIndex.value + 1) % allProfileImages.value.length
  }
}

function previousImage() {
  if (allProfileImages.value.length > 0) {
    currentImageIndex.value = (currentImageIndex.value - 1 + allProfileImages.value.length) % allProfileImages.value.length
  }
}

function toggleEditMenu() {
  showEditMenu.value = !showEditMenu.value
}

function handleEditOption(option: string) {
  const fieldMap: Record<string, { label: string; type: 'text' | 'email' | 'password'; old: string }> = {
    email: {
      label: 'adresse mail',
      type: 'email',
      old: authStore.user?.email ?? '',
    },
    username: {
      label: 'pseudo',
      type: 'text',
      old: authStore.user?.username ?? '',
    },
    firstname: {
      label: 'prénom',
      type: 'text',
      old: authStore.user?.first_name ?? '',
    },
    lastname: {
      label: 'nom',
      type: 'text',
      old: authStore.user?.last_name ?? '',
    },
    password: {
      label: 'mot de passe',
      type: 'password',
      old: '',
    },
  }

  const field = fieldMap[option]
  if (!field) return

  selectedFieldLabel.value = field.label
  selectedFieldKey.value = option
  newFieldType.value = field.type
  oldFieldValue.value = field.old
  newFieldValue.value = ''
  currentPassword.value = ''
  modalErrorMessage.value = ''

  showEditMenu.value = false
  showEditModal.value = true
}

function closeEditModal() {
  currentPassword.value = ''
  newFieldValue.value = ''
  modalErrorMessage.value = ''
  showEditModal.value = false
}

function submitEditModal() {
  modalErrorMessage.value = ''

  if (selectedFieldKey.value === 'password') {
    if (!currentPassword.value.trim()) {
      modalErrorMessage.value = 'Mot de passe actuel requis'
      return
    }

    if (!newFieldValue.value.trim()) {
      modalErrorMessage.value = 'Nouveau mot de passe requis'
      return
    }

    if (currentPassword.value === newFieldValue.value) {
      modalErrorMessage.value = 'Le nouveau mot de passe doit être différent de l\'ancien'
      return
    }

    authStore
      .updateUserPassword(currentPassword.value, newFieldValue.value)
      .then(() => {
        showEditModal.value = false
      })
      .catch((e: unknown) => {
        if (e instanceof Error) {
          modalErrorMessage.value = e.message
        } else {
          modalErrorMessage.value = 'Erreur lors de la mise à jour'
        }
      })
    return
  }

  // Pour les autres champs (email, username, firstname, lastname)
  if (!newFieldValue.value.trim()) {
    modalErrorMessage.value = 'Nouvelle valeur requise'
    return
  }

  if (selectedFieldKey.value === 'username' && newFieldValue.value.trim().length < 3) {
    modalErrorMessage.value = 'Le pseudo doit contenir au minimum 3 caractères'
    return
  }

  if (newFieldValue.value === oldFieldValue.value) {
    modalErrorMessage.value = 'La nouvelle valeur est identique à l\'ancienne'
    return
  }

  let updatePromise: Promise<void> | null = null

  if (selectedFieldKey.value === 'email') {
    updatePromise = authStore.updateUserEmail(newFieldValue.value)
  } else if (selectedFieldKey.value === 'username') {
    updatePromise = authStore.updateUserUsername(newFieldValue.value)
  } else if (selectedFieldKey.value === 'firstname') {
    updatePromise = authStore.updateUserFirstName(newFieldValue.value)
  } else if (selectedFieldKey.value === 'lastname') {
    updatePromise = authStore.updateUserLastName(newFieldValue.value)
  }

  if (updatePromise) {
    updatePromise
      .then(() => {
        showEditModal.value = false
      })
      .catch((e: unknown) => {
        if (e instanceof Error) {
          modalErrorMessage.value = e.message
        } else {
          modalErrorMessage.value = 'Erreur lors de la mise à jour'
        }
      })
  }
}
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Profil" />
    <div class="scrollable-area">
      <div
        class="profile-content"
        v-if="authStore.user"
        :class="{ 'blurred-content': showLogoutConfirm || showEditModal }"
      >
        <!-- Message de bienvenue centré -->
        <div class="welcome-message">
          <h2>Bonjour, {{ authStore.user.username }} !</h2>
        </div>

        <!-- Icône de profil -->
        <div class="profile-icon-container">
          <div v-if="selectedProfileImage" class="profile-icon" @click="openProfileImageModal" style="cursor: pointer;">
            <img :src="selectedProfileImage" :alt="'Image de profil'" class="profile-icon-image" />
          </div>
          <div v-else class="profile-icon" @click="openProfileImageModal" style="cursor: pointer;">{{ authStore.user.username.charAt(0).toUpperCase() }}</div>
        </div>

        <!-- Boutons sous l'icône -->
        <div class="action-buttons">
          <div class="edit-menu-container" ref="editMenuRef">
            <button @click="toggleEditMenu" class="edit-profile-btn">✏️ Modifier profil</button>
            <div v-if="showEditMenu" class="edit-dropdown">
              <div @click="handleEditOption('email')" class="dropdown-item">📧 Adresse mail</div>
              <div @click="handleEditOption('username')" class="dropdown-item">👤 Pseudo</div>
              <div @click="handleEditOption('firstname')" class="dropdown-item">🖊️ Prénom</div>
              <div @click="handleEditOption('lastname')" class="dropdown-item">🖊️ Nom</div>
              <div @click="handleEditOption('password')" class="dropdown-item">🔒 Mot de passe</div>
            </div>
          </div>
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

    <!-- Popup de modification -->
    <div v-if="showEditModal" class="blur-overlay">
      <div class="modal-box">
        <h3>Modifier {{ selectedFieldLabel }}</h3>
        <div v-if="modalErrorMessage" class="modal-error">{{ modalErrorMessage }}</div>
        <form class="edit-modal-form" @submit.prevent="submitEditModal">
          <div v-if="selectedFieldKey !== 'password'" class="field-group">
            <label>Actuel</label>
            <input v-if="oldFieldValue" :value="oldFieldValue" disabled />
            <span v-else class="empty-value">Aucun</span>
          </div>

          <div v-if="selectedFieldKey === 'password'" class="field-group">
            <label>Actuel *</label>
            <input
              v-model="currentPassword"
              type="password"
              required
            />
          </div>

          <div class="field-group">
            <label>Nouveau *</label>
            <input
              v-model="newFieldValue"
              :type="newFieldType"
              required
            />
          </div>

          <div class="modal-actions">
            <button type="button" class="cancel-btn" @click="closeEditModal">Annuler</button>
            <button type="submit" class="save-btn">Enregistrer</button>
          </div>
        </form>
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

    <!-- Popup de sélection d'image de profil -->
    <div v-if="showProfileImageModal" class="blur-overlay">
      <div class="modal-box">
        <h3>Modifier l'image de profil</h3>
        <div class="carousel-container">
          <button v-if="allProfileImages.length > 0" class="carousel-arrow carousel-arrow-left" @click="previousImage">❮</button>
          <div class="profile-image-placeholder">
            <img v-if="allProfileImages.length > 0" :src="allProfileImages[currentImageIndex]" :alt="'Image de profil'" class="gallery-image" />
            <span v-else>Aucune image disponible</span>
          </div>
          <button v-if="allProfileImages.length > 0" class="carousel-arrow carousel-arrow-right" @click="nextImage">❯</button>
        </div>
        <div v-if="allProfileImages.length > 0" class="image-counter">{{ currentImageIndex + 1 }} / {{ allProfileImages.length }}</div>
        <div class="remove-link" @click="removeProfileImage">Retirer</div>
        <div class="modal-actions">
          <button type="button" class="cancel-btn" @click="closeProfileImageModal">Annuler</button>
          <button type="button" class="save-btn" @click="saveProfileImage">Enregistrer</button>
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

.edit-menu-container {
  position: relative;
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

.edit-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 180px;
  z-index: 10;
  overflow: hidden;
}

.dropdown-item {
  padding: 0.75rem 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 0.9rem;
}

.dropdown-item:hover {
  background-color: #f5f5f5;
}

.dropdown-item:not(:last-child) {
  border-bottom: 1px solid #eee;
}

.modal-box {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 85%;
  max-width: 360px;
  animation: popIn 0.2s ease-out;
}

.modal-box h3 {
  text-align: center;
  margin-top: 0;
  margin-bottom: 1rem;
}

.modal-error {
  color: #ff4d4d;
  background: #ffe6e6;
  padding: 0.6rem 0.75rem;
  border-radius: 10px;
  text-align: center;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.edit-modal-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.edit-modal-form label {
  font-weight: 600;
  font-size: 0.9rem;
}

.edit-modal-form input {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 10px;
  font-size: 1rem;
  font-family: inherit;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.save-btn {
  background-color: #679436;
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  flex: 1;
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

.profile-image-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 200px;
  background: #ffffff;
  border-radius: 12px;
  color: #999;
  margin-bottom: 1rem;
  font-size: 0.95rem;
  overflow: hidden;
}

.gallery-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.carousel-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  width: 100%;
}

.carousel-arrow {
  background-color: #679436;
  color: white;
  border: none;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 1.2rem;
  flex-shrink: 0;
  transition: background-color 0.2s;
}

.carousel-arrow:hover {
  background-color: #8ab858;
}

.image-counter {
  text-align: center;
  color: #666;
  font-size: 0.85rem;
  margin-top: 0.5rem;
}

.remove-link {
  text-align: center;
  color: #ff9800;
  cursor: pointer;
  font-size: 0.9rem;
  margin: 0.75rem 0;
  text-decoration: underline;
  transition: color 0.2s;
}

.remove-link:hover {
  color: #f57c00;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.empty-value {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 10px;
  font-size: 1rem;
  color: #999;
}
</style>
