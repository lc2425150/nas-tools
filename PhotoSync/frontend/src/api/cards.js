import { api } from './client'
export const cardsApi = { list:()=>api.get('/cards'), preview:(path,ft)=>api.get(`/cards/${encodeURIComponent(path)}/preview?file_types=${ft||'photos'}`) }
