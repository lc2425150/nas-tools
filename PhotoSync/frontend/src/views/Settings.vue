<template><div><h1 class="text-xl font-bold mb-4">系统设置</h1>
  <div class="space-y-4">
    <div class="card"><h3 class="font-medium mb-3">常规设置</h3>
      <div class="space-y-3"><div><label class="label">扫描路径</label><div v-for="(p,i) in scanPaths" :key="i" class="flex gap-2 mb-1"><input v-model="scanPaths[i]" class="input text-sm font-mono"/><button @click="scanPaths.splice(i,1)" class="text-red-500 text-sm">×</button></div><button @click="scanPaths.push('')" class="text-blue-600 text-sm">+ 添加路径</button></div>
      <div><label class="label">轮询间隔（秒）</label><input v-model.number="pollInterval" type="number" class="input" min="1" max="60"/></div>
      <div><label class="label">默认目标目录</label><input v-model="defaultDest" class="input"/></div>
      <div class="grid grid-cols-2 gap-4"><div><label class="label">日志保留天数</label><input v-model.number="logRet" type="number" class="input"/></div>
        <div><label class="label">历史保留天数</label><input v-model.number="histRet" type="number" class="input"/></div></div>
      <button @click="save" class="btn-primary mt-2">保存设置</button></div></div>
    <div class="card"><h3 class="font-medium mb-3">通知配置</h3>
      <div v-if="notifs.length" class="space-y-2 mb-3"><div v-for="n in notifs" :key="n.id" class="flex items-center justify-between text-sm p-2 bg-gray-50 dark:bg-gray-700/50 rounded">
        <span>{{ n.type }} {{ n.enabled?'(已启用)':'(已禁用)' }}</span><button @click="deleteNotif(n.id)" class="text-red-500 text-xs">删除</button></div></div>
      <p v-else class="text-sm text-gray-500 mb-3">尚未配置通知</p>
      <button @click="showNotifForm=true" class="btn-secondary text-sm">+ 添加通知</button>
      <div v-if="showNotifForm" class="mt-3 p-3 border rounded space-y-2">
        <select v-model="notifType" class="input"><option value="telegram">Telegram</option><option value="dingtalk">钉钉</option><option value="wechat">企业微信</option><option value="email">邮件</option><option value="webhook">Webhook</option></select>
        <input v-model="notifConfig" class="input font-mono text-sm" placeholder='{"bot_token":"...","chat_id":"..."}'/>
        <div class="flex gap-2"><button @click="addNotif" class="btn-primary text-sm">保存</button><button @click="showNotifForm=false" class="btn-secondary text-sm">取消</button></div></div></div>
    <div class="card"><h3 class="font-medium mb-3">存储</h3><StorageChart :storage="store.storage"/></div></div></div></template>
<script setup>import {ref,onMounted} from 'vue';import {settingsApi} from '../api/settings';import StorageChart from '../components/StorageChart.vue'
const store=ref({storage:[]});const scanPaths=ref(['/media','/mnt','/run/media']);const pollInterval=ref(5);const defaultDest=ref('/photos');const logRet=ref(90);const histRet=ref(90)
const notifs=ref([]);const showNotifForm=ref(false);const notifType=ref('telegram');const notifConfig=ref('{}')
onMounted(async()=>{try{const d=await settingsApi.get();scanPaths.value=d.scan_paths;pollInterval.value=d.poll_interval;defaultDest.value=d.default_destination;logRet.value=d.log_retention_days;histRet.value=d.history_retention_days}catch(e){}})
const save=async()=>{try{await settingsApi.update({scan_paths:scanPaths.value,poll_interval:pollInterval.value,default_destination:defaultDest.value,log_retention_days:logRet.value,history_retention_days:histRet.value});alert('设置已保存')}catch(e){alert(e.message)}}
const addNotif=async()=>{try{const cfg=JSON.parse(notifConfig.value);await (await fetch('/api/v1/notification-configs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({type:notifType.value,enabled:true,config:cfg})})).json();showNotifForm.value=false}catch(e){alert(e.message)}}
const deleteNotif=async id=>{try{await fetch('/api/v1/notification-configs/'+id,{method:'DELETE'});notifs.value=notifs.value.filter(n=>n.id!==id)}catch(e){}}
</script>
