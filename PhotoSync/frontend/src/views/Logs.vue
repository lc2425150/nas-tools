<template><div><h1 class="text-xl font-bold mb-4">系统日志</h1>
  <div class="card"><div class="flex gap-2 mb-4"><select v-model="level" class="input w-32"><option value="">全部</option><option value="INFO">INFO</option><option value="WARN">WARN</option><option value="ERROR">ERROR</option></select>
    <input v-model="search" class="input flex-1" placeholder="搜索日志..."/><button @click="load" class="btn-primary">刷新</button></div>
    <div class="space-y-1 max-h-[60vh] overflow-y-auto"><div v-for="l in logs" :key="l.id" class="text-xs font-mono p-1.5 even:bg-gray-50 dark:even:bg-gray-800/50 rounded">
      <span class="text-gray-400">{{ l.timestamp?.split('.')[0]||l.timestamp }} </span>
      <span :class="l.level==='ERROR'?'text-red-600':l.level==='WARN'?'text-yellow-600':'text-green-600'">{{ l.level }} </span>
      <span>{{ l.message }}</span></div>
      <p v-if="!logs.length" class="text-sm text-gray-500 text-center py-4">暂无日志</p></div>
    <Pagination :page="page" :totalPages="totalPages" @page="p=>{page=p;load()}"/></div></div></template>
<script setup>import {ref,onMounted,computed} from 'vue';import {settingsApi} from '../api/settings';import Pagination from '../components/Pagination.vue'
const logs=ref([]);const page=ref(1);const total=ref(0);const level=ref('');const search=ref('');const totalPages=computed(()=>Math.ceil(total.value/50))
const load=async()=>{try{const d=await settingsApi.getLogs({page:page.value,page_size:50,level:level.value,search:search.value});logs.value=d.items;total.value=d.total}catch(e){}};onMounted(load)
</script>
