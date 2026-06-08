<template><div v-if="h"><div class="flex items-center gap-2 mb-4"><button @click="$router.back()" class="text-blue-600">&larr; 返回</button><h1 class="text-xl font-bold">同步详情</h1></div>
  <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
    <StatusCard title="状态" :value="{'completed':'已完成','failed':'失败','running':'同步中','cancelled':'已取消'}[h.status]||h.status" :badgeType="h.status==='completed'?'success':'danger'"/>
    <StatusCard title="同步文件" :value="h.synced_files+' / '+h.total_files+' 个'"/>
    <StatusCard title="数据量" :value="(h.synced_bytes/1048576).toFixed(1)+'MB'"/>
    <StatusCard title="跳过/失败" :value="(h.skipped_files+h.failed_files)+' 个'" :badge="h.failed_files>0?'有失败':'正常'" :badgeType="h.failed_files>0?'danger':'success'"/></div>
  <div class="card"><h3 class="font-medium mb-3">文件列表</h3><div v-if="files.length" class="space-y-1">
    <div v-for="f in files" :key="f.id" class="flex justify-between text-sm p-1.5 even:bg-gray-50 dark:even:bg-gray-800/50 rounded">
      <span class="truncate flex-1">{{ f.filename }}</span><span class="text-gray-500 w-20 text-right">{{ (f.file_size/1024).toFixed(0) }}KB</span>
      <span class="w-16 text-right" :class="f.status==='synced'?'text-green-600':'text-red-600'">{{ {synced:'成功',skipped:'跳过',failed:'失败'}[f.status]||f.status }}</span></div>
    <Pagination :page="fpage" :totalPages="ftotalPages" @page="p=>{fpage=p;loadFiles()}"/></div>
    <p v-else class="text-sm text-gray-500">暂无文件记录</p></div></div>
<EmptyState v-else title="记录未找到"/></template>
<script setup>import {ref,computed,onMounted} from 'vue';import {useRoute} from 'vue-router';import {historyApi} from '../api/history';import StatusCard from '../components/StatusCard.vue';import EmptyState from '../components/EmptyState.vue';import Pagination from '../components/Pagination.vue'
const route=useRoute();const h=ref(null);const files=ref([]);const fpage=ref(1);const ftotal=ref(0);const ftotalPages=computed(()=>Math.ceil(ftotal.value/50))
const loadFiles=async()=>{try{const d=await historyApi.getFiles(route.params.id,{page:fpage.value,page_size:50});files.value=d.items;ftotal.value=d.total}catch(e){}};onMounted(async()=>{try{h.value=await historyApi.get(route.params.id);loadFiles()}catch(e){}})
</script>
