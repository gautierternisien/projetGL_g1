<script setup lang="ts">
defineProps({
  title: {
    type: String,
    default: '',
  },
  isConnected: {
    type: Boolean,
    default: true,
  },
})
</script>

<template>
  <header class="top-header">
    <div class="header-content">
      <h1>{{ title }}</h1>
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
  background-color: #6d8b46;
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

.header-content h1 {
  margin: 0;
  font-size: 1.4rem; /* Légère réduction pour gagner de la place */
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-right: 8px; /* Petit espace de sécurité avant les boutons */
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
}

.auth-buttons {
  display: flex;
  gap: 5px; /* Espace très réduit entre les boutons */
  align-items: center;
  flex-shrink: 0; /* Empêche les boutons d'être écrasés */
}

.auth-btn {
  background-color: white;
  color: #6d8b46;
  border: none;
  padding: 4px 10px; /* Boutons très compacts */
  border-radius: 12px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  font-size: 0.7rem; /* Police réduite */
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
