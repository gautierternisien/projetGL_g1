import { API_URL } from '@/config'

let timeOffset = 0 // Difference between server and client time in milliseconds
let serverWeekNumber = 0 // ISO 8601 week number from server
let isSynced = false

/**
 * Synchronize client time with server time
 * Call this once at app initialization
 */
export async function syncServerTime(): Promise<void> {
  try {
    const clientRequestTime = Date.now()
    const response = await fetch(`${API_URL}/server-time`)
    const clientResponseTime = Date.now()
    
    if (!response.ok) {
      console.warn('Failed to sync server time, using local time')
      return
    }
    
    const data = await response.json()
    const serverTime = data.timestamp
    serverWeekNumber = data.week_number || 0
    
    // Estimate network latency and adjust
    const networkLatency = (clientResponseTime - clientRequestTime) / 2
    const adjustedServerTime = serverTime + networkLatency
    
    // Calculate offset: server time - client time
    timeOffset = adjustedServerTime - clientResponseTime
    isSynced = true
    
    console.log(`Server time synced. Offset: ${timeOffset}ms, Week: ${serverWeekNumber}`)
  } catch (error) {
    console.warn('Failed to sync server time:', error)
    isSynced = false
  }
}

/**
 * Get current time synchronized with server
 * Falls back to local time if sync failed
 */
export function getServerTime(): number {
  return Date.now() + timeOffset
}

/**
 * Get server time as a Date object
 */
export function getServerDate(): Date {
  return new Date(getServerTime())
}

/**
 * Get current date string in YYYY-MM-DD format (server timezone)
 */
export function getServerDateString(): string {
  return getServerDate().toISOString().substring(0, 10)
}

/**
 * Check if server time is synced
 */
export function isServerTimeSynced(): boolean {
  return isSynced
}

/**
 * Get ISO 8601 week number from server (1-53)
 * Falls back to local calculation if sync failed
 */
export function getServerWeekNumber(): number {
  if (serverWeekNumber > 0) {
    return serverWeekNumber
  }
  // Fallback: calculate locally if not synced
  const d = getServerDate()
  const date = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()))
  date.setUTCDate(date.getUTCDate() + 4 - (date.getUTCDay() || 7))
  const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1))
  return Math.ceil(((date.getTime() - yearStart.getTime()) / 86400000 + 1) / 7)
}

/**
 * Get timestamp for end of day (23:59:59) from a date string (YYYY-MM-DD)
 * This matches the backend logic for inclusive end dates
 */
export function getEndOfDayTimestamp(dateString: string): number {
  return new Date(dateString + 'T23:59:59').getTime()
}
