<template><div class="max-w-2xl mx-auto"><div class="text-center mb-8"><h1 class="text-2xl font-bold text-blue-600">欢迎使用 PhotoSync</h1><p class="text-gray-500 mt-2">三步完成初始化设置</p></div>
  <div class="card"><div class="flex items-center gap-2 mb-6"><div v-for="(s,i) in steps" :key="i" class="flex items-center gap-2">
    <span class="w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium" :class="step>i?'bg-green-500 text-white':step===i?'bg-blue-600 text-white':'bg-gray-200 text-gray-500'">{{ i+1 }}</span>
    <span class="text-sm" :class="step===i?'font-medium':'text-gray-400'">{{ s }}</span><span v-if="i<steps.length-1" class="text-gray-300">→</span></div></div>
    <div v-if="step===0"><h2 class="text-lg font-medium mb-4">设置同步目录</h2><label class="label">照片同步目标目录</label><input v-model="dest" class="input mb-4" placeholder="/photos"/>
      <button @click="step=1" class="btn-primary">下一步</button></div>
    <div v-if="step===1"><h2 class="text-lg font-medium mb-4">创建第一个同步配置</h2>
      <label class="label">配置名称</label><input v-model="pn" class="input mb-3" placeholder="例如：索尼 A7M4"/>
      <label class="label">匹配方式</label><select v-model="mt" class="input mb-3"><option value="manual">仅手动同步</option><option value="always">插卡即同步</option><option value="label">按卷标匹配</option></select>
      <label class="label">目标目录</label><input v-model="pd" class="input mb-4" :placeholder="dest"/>
      <div class="flex gap-2"><button @click="save" class="btn-primary">保存并继续</button><button @click="step=0" class="btn-secondary">上一步</button></div></div>
    <div v-if="step===2"><div class="text-center py-8"><svg class="w-16 h-16 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>
      <h2 class="text-xl font-medium mb-2">初始化完成！</h2><p class="text-gray-500">现在可以插入储存卡或手动触发同步了</p>
      <button @click="$router.push('/')" class="btn-primary mt-6">进入仪表盘</button></div></div></div></div>
<script setup>
import { ref } from 'vue'
import { settingsApi } from '../api/settings'
import { profilesApi } from '../api/profiles'
const step=ref(0); const steps=['同步目录','同步配置','完成']; const dest=ref('/photos'); const pn=ref(''); const mt=ref('manual'); const pd=ref('')
const save=async()=>{try{await profilesApi.create({name:pn.value||'默认配置',match_type:mt.value,destination:pd.value||dest.value,sync_mode:'date',auto_sync:mt.value!=='manual'});step.value=2}catch(e){alert('保存失败: '+e.message)}}
</script>
