<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter, RouterLink } from 'vue-router'
import Header from '@/components/Header.vue'

const authStore = useAuthStore()
const router = useRouter()

const regEmail = ref('')
const regUsername = ref('')
const regPassword = ref('')
const regFirstName = ref('')
const regLastName = ref('')

const errorMessage = ref('')

async function handleRegister() {
  errorMessage.value = ''
  try {
    await authStore.register(
      regEmail.value,
      regUsername.value,
      regPassword.value,
      regFirstName.value,
      regLastName.value,
    )
    // After register, switch to login or auto-login
    // For simplicity, let's auto login
    await authStore.login(regUsername.value, regPassword.value)
    router.push('/')
  } catch (e: unknown) {
    if (e instanceof Error) {
      errorMessage.value = e.message
    } else {
      errorMessage.value = "Erreur lors de l'inscription"
    }
  }
}
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Inscription" />
    <div class="scrollable-area">
      <div class="auth-container">
        <div class="auth-card">
          <div v-if="errorMessage" class="error-msg">{{ errorMessage }}</div>

          <form @submit.prevent="handleRegister" class="auth-form">
            <div class="form-group">
              <label>Email *</label>
              <input v-model="regEmail" type="email" required />
            </div>
            <div class="form-group">
              <label>Pseudo *</label>
              <input v-model="regUsername" type="text" required />
            </div>
            <div class="form-group">
              <label>Prénom</label>
              <input v-model="regFirstName" type="text" />
            </div>
            <div class="form-group">
              <label>Nom</label>
              <input v-model="regLastName" type="text" />
            </div>
            <div class="form-group">
              <label>Mot de passe *</label>
              <input v-model="regPassword" type="password" required />
            </div>
            <p class="mandatory-fields">* Champs obligatoires</p>
            <button type="submit" class="submit-btn">S'inscrire</button>
          </form>

          <div class="toggle-auth">
            <p>Déjà un compte ? <RouterLink to="/login">Se connecter</RouterLink></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-wrapper {
  background-color: white;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: 'Instrument Sans', sans-serif;
}

.scrollable-area {
  padding: 100px 20px;
  overflow-y: auto;
  flex: 1;
  -webkit-overflow-scrolling: touch;
}

.auth-container {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 2rem;
}

.auth-card {
  background: #f5f5f5;
  padding: 2rem;
  border-radius: 24px;
  width: 100%;
  max-width: 400px;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

input {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 12px;
  font-size: 1rem;
  font-family: inherit;
}

.submit-btn {
  background-color: #679436;
  color: white;
  padding: 0.75rem;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  cursor: pointer;
  margin-top: 1rem;
  font-family: inherit;
  font-weight: 500;
}

.toggle-auth {
  text-align: center;
  margin-top: 1.5rem;
  font-size: 0.9rem;
}

.toggle-auth a {
  color: #000;
  font-weight: 600;
  text-decoration: underline;
}

.error-msg {
  color: #ff4d4d;
  text-align: center;
  margin-bottom: 1rem;
  background: #ffe6e6;
  padding: 0.5rem;
  border-radius: 8px;
}

.mandatory-fields {
  font-size: 0.8rem;
  color: #666;
  margin-top: -0.5rem;
}
</style>
