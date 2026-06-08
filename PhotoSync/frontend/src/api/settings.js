import { api } from './client'
export const settingsApi = { get:()=>api.get('/settings'), update:d=>api.put('/settings',d), getHealth:()=>api.get('/system/health'), getStorage:()=>api.get('/system/storage'), getLogs:p=>api.get(`/system/logs?${new URLSearchParams(p)}`) }
