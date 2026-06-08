<template><div class="flex flex-col items-center justify-center py-16 text-gray-400">
  <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" :d="icon"/></svg>
  <p class="text-lg font-medium">{{ title }}</p><p class="text-sm mt-1">{{ message }}</p>
  <button v-if="action" @click="$emit('action')" class="btn-primary mt-4">{{ action }}</button></div></template>
<script setup>defineProps({title:{type:String,default:'暂无数据'},message:String,action:String,icon:{type:String,default:'M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4'}});defineEmits(['action'])</script>
