import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useUiStore = defineStore('ui', () => {
  const isNavigationBlurred = ref(false)

  function setNavigationBlur(value: boolean) {
    isNavigationBlurred.value = value
  }

  return {
    isNavigationBlurred,
    setNavigationBlur,
  }
})
