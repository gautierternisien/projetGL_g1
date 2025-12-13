<script setup lang="ts">
defineProps({
  title: {
    type: String,
    default: '',
  },
  hasArrow: {
    type: Boolean,
    default: false,
  },
})
</script>

<template>
  <div class="card-container">
    <div v-if="title" class="card-header">
      <h3 class="card-title">{{ title }}</h3>
      <span v-if="hasArrow" class="arrow-icon">→</span>
    </div>

    <div class="card-content">
      <slot></slot>
    </div>
  </div>
</template>

<style scoped>
.card-container {
  background-color: #f5f5f5;
  border-radius: 24px;
  padding: 20px;
  margin-top: 10px;
  margin-left: 10px;
  margin-right: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
  position: relative;
}

.card-header {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 12px;
  position: relative;
}

.card-title {
  color: #679436;
  font-weight: 600;
  text-align: center;
  font-size: 1.1rem;
  margin: 0;
}

.arrow-icon {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);

  font-size: 1.2rem;
  color: #333;
}
</style>
