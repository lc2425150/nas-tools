<template><div class="card"><h3 class="font-medium mb-3">存储空间</h3>
  <div v-for="d in storage" :key="d.path" class="mb-3 last:mb-0">
    <div class="flex justify-between text-xs mb-1"><span class="font-mono">{{ d.path }}</span><span>{{ d.free_gb }}GB / {{ d.total_gb }}GB 可用</span></div>
    <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2"><div class="h-2 rounded-full transition-all" :class="d.usage_percent>90?'bg-red-500':d.usage_percent>70?'bg-yellow-500':'bg-green-500'" :style="{width:d.usage_percent+'%'}"></div></div>
    <span class="text-xs text-gray-500">{{ d.usage_percent }}% 已用</span></div>
  <p v-if="!storage.length" class="text-sm text-gray-500">无法获取存储信息</p></div></template>
<script setup>defineProps({storage:{type:Array,default:()=>[]}})</script>
