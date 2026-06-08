<template><div><div class="flex items-center justify-between mb-4"><h1 class="text-xl font-bold">同步配置</h1><button @click="$router.push('/profiles/new')" class="btn-primary">+ 新建配置</button></div>
  <div v-if="items.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <div v-for="p in items" :key="p.id" class="card cursor-pointer hover:shadow-md transition-shadow" @click="$router.push('/profiles/'+p.id)">
      <div class="flex items-center justify-between mb-2"><h3 class="font-medium">{{ p.name }}</h3>
        <span class="text-xs px-2 py-0.5 rounded-full" :class="p.enabled?'bg-green-100 text-green-700':'bg-gray-100 text-gray-500'">{{ p.enabled?'已启用':'已禁用' }}</span></div>
      <div class="text-sm text-gray-500 space-y-1"><p>匹配方式: {{ {label:'按卷标',always:'自动',manual:'手动'}[p.match_type]||p.match_type }}</p><p>目标: {{ p.destination }}</p><p>归档: {{ {date:'按日期',original:'原结构',custom:'自定义'}[p.sync_mode]||p.sync_mode }}</p></div></div></div>
  <EmptyState v-else title="还没有同步配置" message="新建一个配置来开始自动同步照片" action="新建配置" @action="$router.push('/profiles/new')"/></div></template>
<script setup>import { ref, onMounted } from 'vue'; import { profilesApi } from '../api/profiles'; import EmptyState from '../components/EmptyState.vue'
const items=ref([]); onMounted(async()=>{try{const d=await profilesApi.list({page:1,page_size:100});items.value=d.items}catch(e){}})</script>
