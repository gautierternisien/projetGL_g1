<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { computed } from 'vue'

const authStore = useAuthStore()
const isConnected = computed(() => authStore.isConnected)

defineProps({
  title: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
  showResumeBtn: {
    type: Boolean,
    default: false,
  },
  resumeBtnLabel: {
    type: String,
    default: 'Reprendre plus tard',
  },
})

defineEmits(['resumeLater'])
</script>

<template>
  <header class="top-header">
    <div class="header-content">
      <div class="header-left">
        <!-- Le titre reste à gauche -->
        <div class="header-title-row">
          <h1>{{ title }}</h1>
        </div>
        <div class="header-sub-row">
          <h2 v-if="subtitle">{{ subtitle }}</h2>
        </div>
      </div>

      <!-- Bouton déplacé ici : il sera poussé à droite par le flex:1 de header-left, juste avant l'avatar -->
      <button class="resume-btn" v-if="showResumeBtn" @click="$emit('resumeLater')">
        {{ resumeBtnLabel }}
      </button>

      <RouterLink to="/profile" v-if="isConnected">
        <div class="user-avatar">👤</div>
      </RouterLink>
      <div v-else class="auth-buttons">
        <RouterLink to="/login" class="login-btn"> Se connecter </RouterLink>
      </div>
    </div>
  </header>
</template>

<style scoped>
/* --- HEADER FIXE --- */
.top-header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background-color: #679436;
  z-index: 1000;
  border-bottom-left-radius: 20px;
  border-bottom-right-radius: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);

  /* Ajustement pour la marge en haut et la hauteur flexible */
  min-height: 90px;
  height: auto;
  padding-top: calc(env(safe-area-inset-top) + 10px);
  padding-bottom: 10px;
  box-sizing: border-box;

  /* Flex column pour aligner le contenu en bas du header */
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  color: white;
  box-sizing: border-box;
  width: 100%;
  /* Padding latéral réduit */
  padding: 0 10px;
}

.header-left {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: flex-start;
  min-width: 0;
  flex: 1;
  margin-right: 10px;
}

.header-title-row {
  display: flex;
  align-items: center;
  gap: 15px;
}

.header-sub-row {
  display: flex;
  align-items: center;
  margin-top: 2px;
  min-width: 0;
}

.header-content h1 {
  margin: 0;
  font-size: 1.4rem;
  text-overflow: ellipsis;
  line-height: 1.2;
  white-space: nowrap;
  font-weight: 500;
}

.header-content h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 400;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.2;
}

.resume-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: white;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 0.75rem;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: background 0.2s;
  /* Positionnement à côté de l'avatar */
  margin-right: 12px;
  margin-bottom: 4px; /* Léger ajustement vertical pour centrer avec l'avatar */
}

.login-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.4);
  color: white;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 0.75rem;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: background 0.2s;
  text-decoration: none;
  margin-bottom: 4px;
}

.user-avatar {
  font-size: 1.5rem;
  background: rgba(255, 255, 255, 0.2);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(5px);
  flex-shrink: 0;
}

.auth-buttons {
  display: flex;
  gap: 10px;
}
</style>
