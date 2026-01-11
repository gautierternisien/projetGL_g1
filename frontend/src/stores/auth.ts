import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { API_URL } from '@/config'

interface User {
  username: string
  email: string
  first_name?: string
  last_name?: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)

  const isConnected = computed(() => !!token.value)

  async function login(username: string, password: string) {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)

    const response = await fetch(`${API_URL}/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    })

    if (!response.ok) {
      throw new Error('Login failed')
    }

    const data = await response.json()
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)

    await fetchUser()
  }

  async function register(
    email: string,
    username: string,
    password: string,
    firstName: string,
    lastName: string,
  ) {
    const response = await fetch(`${API_URL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        username,
        password,
        first_name: firstName,
        last_name: lastName,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Registration failed')
    }
  }

  async function fetchUser() {
    if (!token.value) return

    const response = await fetch(`${API_URL}/users/me`, {
      headers: {
        Authorization: `Bearer ${token.value}`,
      },
    })

    if (response.ok) {
      user.value = await response.json()
    } else {
      logout()
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    user,
    isConnected,
    login,
    register,
    fetchUser,
    logout,
  }
})
