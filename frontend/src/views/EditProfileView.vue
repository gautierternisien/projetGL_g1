<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import { useRouter } from 'vue-router'
import { ref, onMounted, onUnmounted } from 'vue'

const authStore = useAuthStore()
const uiStore = useUiStore()
const router = useRouter()

const email = ref('')
const username = ref('')
const firstName = ref('')
const lastName = ref('')
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

const errorMessage = ref('')
const successMessage = ref('')

const showProfileImageModal = ref(false)
const allProfileImages = ref<string[]>([])
const currentImageIndex = ref(0)
const selectedProfileImage = ref<string | undefined>(undefined)
const initialProfileImage = ref<string | undefined>(undefined)
const tempSelectedImage = ref<string | undefined>(undefined)

onMounted(async () => {
  if (!authStore.isConnected) {
    router.push('/login')
    return
  }
  
  // Recharger les données utilisateur pour être sûr d'avoir les dernières valeurs
  await authStore.fetchUser()
  
  if (authStore.user) {
    email.value = authStore.user.email
    username.value = authStore.user.username
    firstName.value = authStore.user.first_name || ''
    lastName.value = authStore.user.last_name || ''
    if (authStore.user.profile_image) {
      selectedProfileImage.value = authStore.user.profile_image
      initialProfileImage.value = authStore.user.profile_image
      tempSelectedImage.value = authStore.user.profile_image
    }
  }
  
  // Charger toutes les images du dossier image_profil
  try {
    const imageNames = [
      'plante1.png',
      'plante2.png',
      'plante3.png',
      'plante4.png',
      'plante5.png',
      'plante6.png',
    ]
    allProfileImages.value = imageNames.map(
      (name) => new URL(`../components/image_profil/${name}`, import.meta.url).href,
    )
    currentImageIndex.value = 0
  } catch (e) {
    console.error('Erreur lors du chargement des images:', e)
  }
})

onUnmounted(() => {
  uiStore.setNavigationBlur(false)
})

function goBack() {
  router.back()
}

function openProfileImageModal() {
  // Sauvegarder l'image actuelle pour pouvoir la restaurer en cas d'annulation
  tempSelectedImage.value = selectedProfileImage.value
  
  // Si une image est déjà sélectionnée, positionner le carousel sur cette image
  if (selectedProfileImage.value && allProfileImages.value.length > 0) {
    const index = allProfileImages.value.findIndex(img => img === selectedProfileImage.value)
    if (index !== -1) {
      currentImageIndex.value = index
    }
  }
  
  showProfileImageModal.value = true
  uiStore.setNavigationBlur(true)
}

function closeProfileImageModal() {
  // Restaurer l'image d'origine en cas d'annulation
  selectedProfileImage.value = tempSelectedImage.value
  showProfileImageModal.value = false
  uiStore.setNavigationBlur(false)
}

function saveProfileImage() {
  if (
    allProfileImages.value.length > 0 &&
    currentImageIndex.value < allProfileImages.value.length
  ) {
    const imageUrl = allProfileImages.value[currentImageIndex.value]
    if (imageUrl) {
      selectedProfileImage.value = imageUrl
      tempSelectedImage.value = imageUrl
      // Ne pas sauvegarder maintenant, juste sélectionner
      // La sauvegarde se fera lors du clic sur "Enregistrer" du formulaire principal
      // Fermer la modal sans restaurer (on garde la sélection)
      showProfileImageModal.value = false
      uiStore.setNavigationBlur(false)
    }
  }
}

function removeProfileImage() {
  // Juste désélectionner l'image sans sauvegarder
  // La suppression réelle se fera lors du clic sur "Enregistrer" du formulaire principal
  selectedProfileImage.value = undefined
  tempSelectedImage.value = undefined
  // Fermer la modal sans restaurer (on garde la désélection)
  showProfileImageModal.value = false
  uiStore.setNavigationBlur(false)
}

function nextImage() {
  if (allProfileImages.value.length > 0) {
    currentImageIndex.value = (currentImageIndex.value + 1) % allProfileImages.value.length
  }
}

function previousImage() {
  if (allProfileImages.value.length > 0) {
    currentImageIndex.value =
      (currentImageIndex.value - 1 + allProfileImages.value.length) % allProfileImages.value.length
  }
}

async function saveChanges() {
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const promises: Promise<void>[] = []
    let hasImageChanged = false

    // Image de profil - sauvegarder maintenant si elle a changé
    if (selectedProfileImage.value !== initialProfileImage.value) {
      hasImageChanged = true
      // Sauvegarder l'image en base de données
      if (selectedProfileImage.value === undefined) {
        promises.push(authStore.removeProfileImage())
      } else {
        promises.push(authStore.updateProfileImage(selectedProfileImage.value))
      }
    }

    // Email
    if (email.value !== authStore.user?.email) {
      promises.push(authStore.updateUserEmail(email.value))
    }

    // Username
    if (username.value !== authStore.user?.username) {
      if (username.value.trim().length < 3) {
        errorMessage.value = 'Le pseudo doit contenir au minimum 3 caractères'
        return
      }
      promises.push(authStore.updateUserUsername(username.value))
    }

    // Prénom
    if (firstName.value !== (authStore.user?.first_name || '')) {
      promises.push(authStore.updateUserFirstName(firstName.value))
    }

    // Nom
    if (lastName.value !== (authStore.user?.last_name || '')) {
      promises.push(authStore.updateUserLastName(lastName.value))
    }

    // Mot de passe
    if (newPassword.value.trim()) {
      if (!currentPassword.value.trim()) {
        errorMessage.value = 'Mot de passe actuel requis pour changer le mot de passe'
        return
      }
      if (newPassword.value !== confirmPassword.value) {
        errorMessage.value = 'Les nouveaux mots de passe ne correspondent pas'
        return
      }
      if (currentPassword.value === newPassword.value) {
        errorMessage.value = "Le nouveau mot de passe doit être différent de l'ancien"
        return
      }
      promises.push(authStore.updateUserPassword(currentPassword.value, newPassword.value))
    }

    if (promises.length === 0 && !hasImageChanged) {
      errorMessage.value = 'Aucune modification détectée'
      return
    }

    await Promise.all(promises)
    
    successMessage.value = 'Profil mis à jour avec succès !'
    
    // Mettre à jour l'image initiale et temporaire si elle a changé
    if (hasImageChanged) {
      initialProfileImage.value = selectedProfileImage.value
      tempSelectedImage.value = selectedProfileImage.value
    }
    
    // Réinitialiser les champs de mot de passe
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    
    // Rediriger après 1.5 secondes
    setTimeout(() => {
      router.push('/profile')
    }, 600)
    
  } catch (e: unknown) {
    if (e instanceof Error) {
      errorMessage.value = e.message
    } else {
      errorMessage.value = 'Erreur lors de la mise à jour du profil'
    }
  }
}
</script>

<template>
  <div class="dashboard-wrapper">
    <Header
      title="Modifier le profil"
      :showResumeBtn="true"
      resumeBtnLabel="Retour"
      @resumeLater="goBack"
    />
    
    <div class="scrollable-area">
      <div class="edit-profile-content">
        <!-- Icône de profil -->
        <div class="profile-icon-container">
          <div 
            v-if="selectedProfileImage" 
            class="profile-icon" 
            @click="openProfileImageModal"
            style="cursor: pointer"
          >
            <img :src="selectedProfileImage" :alt="'Image de profil'" class="profile-icon-image" />
          </div>
          <div v-else class="profile-icon" @click="openProfileImageModal" style="cursor: pointer">
            {{ authStore.user?.username.charAt(0).toUpperCase() }}
          </div>
          <button type="button" @click="openProfileImageModal" class="change-image-btn">
            Changer l'image
          </button>
        </div>

        <form @submit.prevent="saveChanges" class="edit-form">
          <div class="form-section">
            <h3>Informations du compte</h3>
            
            <div class="form-group">
              <label for="email">Adresse email</label>
              <input
                id="email"
                v-model="email"
                type="email"
                required
                placeholder="votre@email.com"
              />
            </div>

            <div class="form-group">
              <label for="username">Pseudo</label>
              <input
                id="username"
                v-model="username"
                type="text"
                required
                minlength="3"
                placeholder="Votre pseudo"
              />
            </div>
          </div>

          <div class="form-section">
            <h3>Informations personnelles</h3>
            
            <div class="form-group">
              <label for="firstName">Prénom (optionnel)</label>
              <input
                id="firstName"
                v-model="firstName"
                type="text"
                placeholder="Votre prénom"
              />
            </div>

            <div class="form-group">
              <label for="lastName">Nom (optionnel)</label>
              <input
                id="lastName"
                v-model="lastName"
                type="text"
                placeholder="Votre nom"
              />
            </div>
          </div>

          <div class="form-section">
            <h3>Changer le mot de passe</h3>
            <p class="section-hint">Laissez vide pour ne pas modifier</p>
            
            <div class="form-group">
              <label for="currentPassword">Mot de passe actuel</label>
              <input
                id="currentPassword"
                v-model="currentPassword"
                type="password"
                placeholder="Votre mot de passe actuel"
              />
            </div>

            <div class="form-group">
              <label for="newPassword">Nouveau mot de passe</label>
              <input
                id="newPassword"
                v-model="newPassword"
                type="password"
                placeholder="Nouveau mot de passe"
              />
            </div>

            <div class="form-group">
              <label for="confirmPassword">Confirmer le nouveau mot de passe</label>
              <input
                id="confirmPassword"
                v-model="confirmPassword"
                type="password"
                placeholder="Confirmez le nouveau mot de passe"
              />
            </div>
          </div>

          <div v-if="errorMessage" class="message error-message">{{ errorMessage }}</div>
          <div v-if="successMessage" class="message success-message">{{ successMessage }}</div>

          <div class="form-actions">
            <button type="button" @click="goBack" class="cancel-btn">Annuler</button>
            <button type="submit" class="save-btn">Enregistrer</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Popup de sélection d'image de profil -->
    <div v-if="showProfileImageModal" class="blur-overlay">
      <div class="modal-box">
        <h3>Modifier l'image de profil</h3>
        <div class="carousel-container">
          <button
            v-if="allProfileImages.length > 0"
            class="carousel-arrow carousel-arrow-left"
            @click="previousImage"
          >
            ❮
          </button>
          <div class="profile-image-placeholder">
            <img
              v-if="allProfileImages.length > 0"
              :src="allProfileImages[currentImageIndex]"
              :alt="'Image de profil'"
              class="gallery-image"
            />
            <span v-else>Aucune image disponible</span>
          </div>
          <button
            v-if="allProfileImages.length > 0"
            class="carousel-arrow carousel-arrow-right"
            @click="nextImage"
          >
            ❯
          </button>
        </div>
        <div v-if="allProfileImages.length > 0" class="image-counter">
          {{ currentImageIndex + 1 }} / {{ allProfileImages.length }}
        </div>
        <div class="remove-link" @click="removeProfileImage">Retirer</div>
        <div class="modal-actions">
          <button type="button" class="cancel-btn-modal" @click="closeProfileImageModal">Annuler</button>
          <button type="button" class="save-btn-modal" @click="saveProfileImage">Sélectionner</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.edit-profile-content {
  padding: 0;
}

.message {
  padding: 1rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
  text-align: center;
  font-weight: 600;
}

.error-message {
  background-color: #ffe6e6;
  color: #ff4d4d;
}

.success-message {
  background-color: #e6f7e6;
  color: #4caf50;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.form-section {
  background: #f9f9f9;
  padding: 1.5rem;
  border-radius: 12px;
}

.form-section h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  color: #333;
}

.section-hint {
  font-size: 0.85rem;
  color: #666;
  margin: 0 0 1rem 0;
  font-style: italic;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #333;
  font-size: 0.9rem;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 10px;
  font-size: 1rem;
  font-family: inherit;
  box-sizing: border-box;
  transition: border-color 0.2s;
}

.form-group input:focus {
  outline: none;
  border-color: #679436;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.cancel-btn {
  flex: 1;
  background-color: #f0f0f0;
  color: #333;
  border: none;
  padding: 1rem;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.cancel-btn:hover {
  background-color: #e0e0e0;
}

.save-btn {
  flex: 1;
  background-color: #679436;
  color: white;
  border: none;
  padding: 1rem;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.save-btn:hover {
  background-color: #577a2e;
}

/* Profile Icon Styles */
.profile-icon-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  margin-bottom: 2rem;
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
  color: white;
}

.profile-icon-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.change-image-btn {
  background-color: #679436;
  color: white;
  border: none;
  padding: 0.5rem 1.5rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.change-image-btn:hover {
  background-color: #577a2e;
}

/* Modal Styles */
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

.modal-box {
  background: white;
  padding: 2rem;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  width: 85%;
  max-width: 360px;
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

.modal-box h3 {
  text-align: center;
  margin-top: 0;
  margin-bottom: 1rem;
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

.modal-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.cancel-btn-modal {
  background-color: #f0f0f0;
  color: #333;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  flex: 1;
}

.save-btn-modal {
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
