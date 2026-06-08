import { defineStore } from 'pinia'
import { ref } from 'vue'
import { syncApi } from '../api/sync'
export const useSyncStore = defineStore('sync', () => {
  const status = ref({running:false,current:0,total:0,speed_mbps:null,eta_seconds:null})
  const queue = ref([])
  const fetchStatus = async () => { try { status.value = await syncApi.status() } catch(e) {} }
  const fetchQueue = async () => { try { queue.value = await syncApi.getQueue() } catch(e) {} }
  return { status, queue, fetchStatus, fetchQueue }
})
