<script setup lang="ts">
defineProps({
  title: {
    type: String,
    default: '',
  },
  subtitle: {
    type: String,
    default: '',
  },
  isConnected: {
    type: Boolean,
    default: true,
  },
  showResumeBtn: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['resumeLater'])
</script>

<template>
  <header class="top-header">
    <div class="header-content">
      <div class="header-left">
        <!-- Regroupement du bouton et du titre sur une même ligne -->
        <div class="header-title-row">
          <h1>{{ title }}</h1>
          <button class="resume-btn" v-if="showResumeBtn" @click="$emit('resumeLater')">
            Reprendre plus tard
          </button>
        </div>
        <!-- Le sous-titre reste en dessous -->
        <div class="header-sub-row">
          <h2 v-if="subtitle">{{ subtitle }}</h2>
        </div>
      </div>

      <RouterLink to="/profile" v-if="isConnected">
        <div class="user-avatar">👤</div>
      </RouterLink>
      <div v-else class="auth-buttons">
        <RouterLink to="/login">
          <button class="auth-btn">Se connecter</button>
        </RouterLink>
        <RouterLink to="/register">
          <button class="auth-btn">S'inscrire</button>
        </RouterLink>
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
  height: 100px;
  padding-top: env(safe-area-inset-top);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  color: white;
  box-sizing: border-box;
  width: 100%;
  padding: 0 20px 15px 20px;
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

/* Nouvelle classe pour aligner bouton et titre */
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
  padding: 4px 8px;
  font-size: 0.65rem;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
  transition: background 0.2s;
}

.resume-btn:hover {
  background: rgba(255, 255, 255, 0.25);
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
  gap: 5px;
  align-items: center;
  flex-shrink: 0;
}

.auth-btn {
  background-color: white;
  color: #6d8b46;
  border: none;
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  font-size: 0.7rem;
  transition:
    transform 0.1s ease,
    background-color 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  white-space: nowrap;
}

.auth-btn:active {
  transform: scale(0.95);
}
</style>
