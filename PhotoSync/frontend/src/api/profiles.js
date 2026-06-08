import { api } from './client'
export const profilesApi = { list:p=>api.get(`/profiles?${new URLSearchParams(p)}`), get:id=>api.get(`/profiles/${id}`), create:d=>api.post('/profiles',d), update:(id,d)=>api.put(`/profiles/${id}`,d), delete:id=>api.delete(`/profiles/${id}`), export:id=>api.get(`/profiles/${id}/export`), import:d=>api.post('/profiles/import',d) }
