import { defineStore } from 'pinia'
import { ref } from 'vue'
import { profilesApi } from '../api/profiles'
export const useProfileStore = defineStore('profiles', () => {
  const profiles = ref([]); const total = ref(0)
  const fetchProfiles = async (p=1) => { const d=await profilesApi.list({page:p,page_size:50}); profiles.value=d.items; total.value=d.total }
  return { profiles, total, fetchProfiles }
})
