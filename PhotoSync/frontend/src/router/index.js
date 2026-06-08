import { createRouter, createWebHistory } from 'vue-router'
const routes = [
  { path:'/', name:'Dashboard', component:()=>import('../views/Dashboard.vue') },
  { path:'/setup', name:'SetupWizard', component:()=>import('../views/SetupWizard.vue') },
  { path:'/profiles', name:'Profiles', component:()=>import('../views/Profiles.vue') },
  { path:'/profiles/new', name:'ProfileNew', component:()=>import('../views/ProfileDetail.vue') },
  { path:'/profiles/:id', name:'ProfileDetail', component:()=>import('../views/ProfileDetail.vue') },
  { path:'/history', name:'History', component:()=>import('../views/History.vue') },
  { path:'/history/:id', name:'HistoryDetail', component:()=>import('../views/HistoryDetail.vue') },
  { path:'/cards', name:'CardBrowser', component:()=>import('../views/CardBrowser.vue') },
  { path:'/gallery', name:'Gallery', component:()=>import('../views/Gallery.vue') },
  { path:'/settings', name:'Settings', component:()=>import('../views/Settings.vue') },
  { path:'/logs', name:'Logs', component:()=>import('../views/Logs.vue') },
]
export default createRouter({ history: createWebHistory(), routes })
