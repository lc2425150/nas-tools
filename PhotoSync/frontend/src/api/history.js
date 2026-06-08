import { api } from './client'
export const historyApi = { list:p=>api.get(`/history?${new URLSearchParams(p)}`), get:id=>api.get(`/history/${id}`), getFiles:(id,p)=>api.get(`/history/${id}/files?${new URLSearchParams(p)}`), clean:d=>api.delete(`/history?days=${d}`) }
