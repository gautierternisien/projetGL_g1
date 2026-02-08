/* eslint-disable @typescript-eslint/no-explicit-any */
import { ref, onMounted } from 'vue'
import Engine from 'publicodes'
import { API_BASE_URL } from '@/config' // adapte à ton projet

export function usePublicodesEngine() {
  const engine = ref<Engine | null>(null)
  const error = ref<string | null>(null)
  const loading = ref(true)

  onMounted(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/rules`, { cache: 'no-store' })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const rules = await res.json()

      engine.value = new Engine(rules)
    } catch (e: any) {
      error.value = e?.message ?? String(e)
    } finally {
      loading.value = false
    }
  })

  return { engine, error, loading }
}
