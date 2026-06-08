<template><div><h1 class="text-xl font-bold mb-4">照片画廊</h1>
  <div v-if="photos.length" class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
    <div v-for="p in photos" :key="p.id" class="aspect-square rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 cursor-pointer hover:opacity-90 transition-opacity" @click="view(p)">
      <img :src="p.thumbnail_url" :alt="p.filename" class="w-full h-full object-cover" loading="lazy"/></div></div>
  <EmptyState v-else title="暂无已同步的照片" message="同步完成后，照片会在这里以缩略图形式展示"/>
  <Pagination v-if="totalPages>1" :page="page" :totalPages="totalPages" @page="p=>{page=p;load()}"/></div>
  <div v-if="viewerImg" class="fixed inset-0 bg-black/80 z-50 flex items-center justify-center" @click="viewerImg=null">
    <img :src="viewerImg" class="max-h-[90vh] max-w-[90vw] object-contain"/></div></template>
<script setup>import {ref,computed,onMounted} from 'vue';import EmptyState from '../components/EmptyState.vue';import Pagination from '../components/Pagination.vue'
import {api} from '../api/client'
const photos=ref([]);const page=ref(1);const total=ref(0);const viewerImg=ref(null);const totalPages=computed(()=>Math.ceil(total.value/50))
const load=async()=>{try{const d=await api.get(`/gallery?page=${page.value}&page_size=50`);photos.value=d.items;total.value=d.total}catch(e){}};onMounted(load)
const view=p=>{viewerImg.value=p.image_url}
</script>
