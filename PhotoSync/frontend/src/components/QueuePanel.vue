<template><div class="card"><div class="flex items-center justify-between mb-3"><h3 class="font-medium">同步队列</h3><span class="text-xs text-gray-500">{{ queue.length }} 项</span></div>
  <div v-if="queue.length" class="space-y-2"><div v-for="item in queue" :key="item.id" class="flex items-center justify-between text-sm p-2 bg-gray-50 dark:bg-gray-700/50 rounded">
    <div><span class="font-medium">{{ item.card_label||item.card_path }}</span><span class="ml-2 text-xs text-gray-500">{{ st(item.status) }}</span></div>
    <button v-if="item.status==='queued'" @click="$emit('cancel',item.id)" class="text-red-500 hover:text-red-700 text-xs">取消</button></div></div>
  <p v-else class="text-sm text-gray-500">队列为空</p></div></template>
<script setup>defineProps({queue:{type:Array,default:()=>[]}});defineEmits(['cancel'])
const st=s=>({queued:'等待中',running:'同步中',completed:'已完成',failed:'失败',cancelled:'已取消'}[s]||s)
</script>
