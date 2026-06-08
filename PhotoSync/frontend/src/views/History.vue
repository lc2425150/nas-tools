<template><div><h1 class="text-xl font-bold mb-4">同步记录</h1>
  <div class="card"><div v-if="items.length" class="space-y-2">
    <div v-for="h in items" :key="h.id" class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700" @click="$router.push('/history/'+h.id)">
      <div><div class="font-medium">{{ h.profile_name||'未知' }}</div><div class="text-xs text-gray-500">{{ h.synced_files }} 个文件 ({{ (h.synced_bytes/1048576).toFixed(1) }}MB) · {{ new Date(h.started_at).toLocaleString() }}</div></div>
      <span class="text-xs px-2 py-1 rounded-full" :class="h.status==='completed'?'bg-green-100 text-green-700':h.status==='failed'?'bg-red-100 text-red-700':'bg-blue-100 text-blue-700'">{{ {'completed':'已完成','running':'同步中','failed':'失败','cancelled':'已取消'}[h.status]||h.status }}</span></div>
    <Pagination :page="page" :totalPages="totalPages" @page="p=>{page=p;load()}"/></div>
  <EmptyState v-else title="暂无同步记录" message="插入储存卡或手动触发同步后，这里会显示记录"/></div></div></template>
<script setup>import {ref,onMounted,computed} from 'vue';import {historyApi} from '../api/history';import EmptyState from '../components/EmptyState.vue';import Pagination from '../components/Pagination.vue'
const items=ref([]);const page=ref(1);const total=ref(0);const totalPages=computed(()=>Math.ceil(total.value/50))
const load=async()=>{try{const d=await historyApi.list({page:page.value,page_size:50});items.value=d.items;total.value=d.total}catch(e){}};onMounted(load)
</script>
