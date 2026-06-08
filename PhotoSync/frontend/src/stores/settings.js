import { defineStore } from 'pinia'
import { ref } from 'vue'
import { settingsApi } from '../api/settings'
export const useSettingsStore = defineStore('settings', () => {
  const settings = ref({}); const storage = ref([]); const health = ref({})
  const fetchSettings = async () => { try { settings.value = await settingsApi.get() } catch(e) {} }
  const fetchStorage = async () => { try { storage.value = await settingsApi.getStorage() } catch(e) {} }
  const fetchHealth = async () => { try { health.value = await settingsApi.getHealth() } catch(e) {} }
  return { settings, storage, health, fetchSettings, fetchStorage, fetchHealth }
})
