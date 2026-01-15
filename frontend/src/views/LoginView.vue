<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter, RouterLink } from 'vue-router'
import Header from '@/components/AppHeader.vue'

const authStore = useAuthStore()
const router = useRouter()

// Login form
const loginUsername = ref('')
const loginPassword = ref('')

const errorMessage = ref('')

async function handleLogin() {
  errorMessage.value = ''
  try {
    await authStore.login(loginUsername.value, loginPassword.value)
    router.push('/')
  } catch (e) {
    console.error(e)
    errorMessage.value = 'Échec de la connexion. Vérifiez vos identifiants.'
  }
}
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Connexion" />
    <div class="scrollable-area">
      <div class="auth-container">
        <div class="auth-card">
          <div v-if="errorMessage" class="error-msg">{{ errorMessage }}</div>

          <form @submit.prevent="handleLogin" class="auth-form">
            <div class="form-group">
              <label>Email ou Pseudo</label>
              <input v-model="loginUsername" type="text" required />
            </div>
            <div class="form-group">
              <label>Mot de passe</label>
              <input v-model="loginPassword" type="password" required />
            </div>
            <button type="submit" class="submit-btn">Se connecter</button>
          </form>

          <div class="toggle-auth">
            <p>Pas encore de compte ? <RouterLink to="/register">Créer un compte</RouterLink></p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
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
</style>
