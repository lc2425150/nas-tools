<template><div><h1 class="text-xl font-bold mb-4">储存卡浏览器</h1>
  <div v-if="cards.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    <div v-for="c in cards" :key="c.path" class="card">
      <div class="flex items-center justify-between mb-2"><h3 class="font-medium">{{ c.label }}</h3><span class="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">已连接</span></div>
      <p class="text-xs text-gray-500 font-mono mb-2">{{ c.path }}</p>
      <p class="text-sm text-gray-600">容量: {{ c.total_space?(c.total_space/1073741824).toFixed(1)+'GB':'未知' }}</p>
      <p v-if="c.matched_profile" class="text-sm text-blue-600">匹配配置: {{ c.matched_profile }}</p>
      <div class="flex gap-2 mt-3"><button @click="preview(c.path)" class="btn-secondary text-sm">预览文件</button></div></div></div>
  <EmptyState v-else title="未检测到储存卡" message="插入相机储存卡到 NAS 的 USB 接口后会自动显示" action="刷新" @action="load"/>
  <div v-if="previewFiles.length" class="mt-6"><h2 class="font-medium mb-3">文件预览</h2><div class="card"><div v-for="f in previewFiles" :key="f.path" class="flex justify-between text-sm p-1.5 even:bg-gray-50 rounded">
    <span>{{ f.name }}</span><span class="text-gray-500"> {{ (f.size/1024).toFixed(0) }}KB</span></div></div></div></div></template>
<script setup>import {ref,onMounted} from 'vue';import {cardsApi} from '../api/cards';import EmptyState from '../components/EmptyState.vue'
const cards=ref([]);const previewFiles=ref([]);const load=async()=>{try{cards.value=await cardsApi.list()}catch(e){}};onMounted(load)
const preview=async path=>{try{previewFiles.value=await cardsApi.preview(path,'all')}catch(e){alert(e.message)}}
</script>
