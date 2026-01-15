<script setup lang="ts">
import Header from '@/components/AppHeader.vue'
import { useRouter } from 'vue-router'
const router = useRouter()
const goBack = () => router.push('/communaute')
</script>

<template>
  <div class="dashboard-wrapper">
    <Header title="Ligues" :showResumeBtn="true" resumeBtnLabel="Retour" @resumeLater="goBack" />
    <div class="scrollable-area">
      <div class="placeholder-content">
        <span class="emoji">🏆</span>
        <p>Les ligues apparaîtront ici bientôt !</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
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
