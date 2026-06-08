<template><div v-if="totalPages>1" class="flex items-center justify-center gap-2 mt-4">
  <button @click="$emit('page',page-1)" :disabled="page<=1" class="px-3 py-1 text-sm rounded border disabled:opacity-50">{{'上一页'}}</button>
  <span class="text-sm text-gray-500">{{ page }}/{{ totalPages }}</span>
  <button @click="$emit('page',page+1)" :disabled="page>=totalPages" class="px-3 py-1 text-sm rounded border disabled:opacity-50">{{'下一页'}}</button></div></template>
<script setup>defineProps({page:Number,totalPages:Number});defineEmits(['page'])</script>
