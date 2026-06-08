<template><div class="card"><div class="flex items-center justify-between mb-2">
  <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400">{{ title }}</h3>
  <span v-if="badge" class="text-xs px-2 py-0.5 rounded-full" :class="badgeCls">{{ badge }}</span></div>
  <p class="text-2xl font-bold">{{ value }}</p>
  <p v-if="subtext" class="text-xs text-gray-500 mt-1">{{ subtext }}</p></div></template>
<script setup>import {computed} from 'vue'
const props=defineProps({title:String,value:[String,Number],subtext:String,badge:String,badgeType:{type:String,default:'info'}})
const badgeCls=computed(()=>({success:'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',warning:'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',danger:'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',info:'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'}[props.badgeType]||'bg-blue-100 text-blue-800'))
</script>
