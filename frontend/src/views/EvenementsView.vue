<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useFriendsStore } from '@/stores/friends'
import Header from '@/components/AppHeader.vue'

const store = useFriendsStore()
const router = useRouter()

const goBack = () => router.push('/communaute')

function formatDate(ts?: string) {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleDateString()
}

onMounted(async () => {
  await store.fetchActivities()
})
</script>

<template>
  <div class="dashboard-wrapper">
    <Header
      title="Évènements"
      :showResumeBtn="true"
      resumeBtnLabel="Retour"
      @resumeLater="goBack"
    />
    <div class="scrollable-area">
      <div v-if="store.activities.length === 0" class="placeholder-content">
        <span class="emoji">😴</span>
        <p>Aucune activité récente de vos amis.</p>
      </div>
      <div v-else class="activity-list">
        <div v-for="(act, index) in store.activities" :key="index" class="activity-item">
          <span class="activity-date" v-if="act.timestamp">{{ formatDate(act.timestamp) }}</span>
          <div class="activity-content-row">
            <div class="avatar">
              <img v-if="act.profile_image" :src="act.profile_image" alt="Profil" class="avatar-image" />
              <span v-else>{{ act.friend_username.charAt(0).toUpperCase() }}</span>
            </div>
            <div class="activity-info">
              <span class="friend-name">{{ act.friend_username }}</span>
              <span v-if="act.activity_type === 'mission'" class="activity-text">a terminé la mission</span>
              <span v-if="act.activity_type === 'mission'" class="mission-badge">
                <span class="mission-icon">🎯</span>
                <span class="mission-title">{{ act.mission_title }}</span>
              </span>
              <span v-if="act.activity_type === 'trophy'" class="activity-text">a obtenu le trophée</span>
              <span v-if="act.activity_type === 'trophy'" class="trophy-badge">
                <span class="trophy-icon">{{ act.trophy_icon }}</span>
                <span class="trophy-title">{{ act.trophy_title }}</span>
              </span>
            </div>
          </div>
        </div>
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

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.activity-item {
  background: #f7f9f5;
  padding: 15px;
  border-radius: 12px;
  border: 1px solid #dbe5d3;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  position: relative;
}

.activity-date {
  position: absolute;
  top: 12px;
  right: 12px;
  font-size: 0.75rem;
  color: #999;
}

.activity-content-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-right: 70px; /* Espace pour la date */
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e3eddd;
  color: #2f3b2f;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  flex-shrink: 0;
  overflow: hidden;
}

.avatar .avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.activity-info {
  display: flex;
  flex-direction: column;
}

.friend-name {
  font-weight: 600;
  color: #1f2a2c;
}

.activity-text {
  font-size: 0.9em;
  color: #666;
}

.mission-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #b7e3b7 0%, #b7e3b7 100%);
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-weight: 600;
  color: #333;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.mission-icon {
  font-size: 1.2rem;
  color: #679436;
}

.mission-title {
  font-size: 0.9rem;
}

.trophy-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: linear-gradient(135deg, #e5cd48 0%, #e5cd48 100%);
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-weight: 600;
  color: #333;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.trophy-icon {
  font-size: 1.2rem;
}

.trophy-title {
  font-size: 0.9rem;
}
</style>
