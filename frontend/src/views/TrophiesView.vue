<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Trophées" />
    <div class="scrollable-area">
      <div class="placeholder-content">
        <span class="emoji">🏆</span>
        <p>Vos trophées apparaîtront ici bientôt !</p>
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

.placeholder-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  text-align: center;
  color: #666;
  gap: 20px;
}

.emoji {
  font-size: 4rem;
}
</style>
