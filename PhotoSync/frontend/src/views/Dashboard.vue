<template>
  <div>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <StatusCard title="储存卡" :value="cards.length+' 张'" :badge="cards.length?'已连接':'未检测到'" :badgeType="cards.length?'success':'warning'"/>
      <StatusCard title="同步配置" :value="profileCount+' 个'" badgeType="info"/>
      <StatusCard title="今日同步" :value="todayCount+' 个文件'" :subtext="todaySize"/>
      <StatusCard title="系统状态" value="运行中" badge="健康" badgeType="success"/>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
      <div class="lg:col-span-2"><SyncProgress :running="sync.status" :current="sync.current" :total="sync.total" :speed="sync.speed_mbps" :currentFile="sync.current_file" :eta="fmtETA(sync.eta_seconds)"/></div>
      <QueuePanel :queue="syncQueue" @cancel="cancelQ"/>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <StorageChart :storage="storage"/>
      <div class="card"><h3 class="font-medium mb-3">最近同步</h3>
        <div v-if="recent.length" class="space-y-2 text-sm">
          <div v-for="h in recent" :key="h.id" class="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-700/50 rounded cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700" @click="$router.push('/history/'+h.id)">
            <div><span class="font-medium">{{ h.profile_name||'未知' }}</span><span class="ml-2 text-xs" :class="h.status==='completed'?'text-green-600':h.status==='failed'?'text-red-600':'text-blue-600'">{{{'completed':'已完成','running':'同步中','failed':'失败'}[h.status]||h.status }}</span></div>
            <div class="text-xs text-gray-500">{{ h.synced_files }} 个文件 · {{ new Date(h.started_at).toLocaleString() }}</div></div></div>
        <p v-else class="text-sm text-gray-500">暂无同步记录</p></div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import StatusCard from '../components/StatusCard.vue'
import SyncProgress from '../components/SyncProgress.vue'
import StorageChart from '../components/StorageChart.vue'
import QueuePanel from '../components/QueuePanel.vue'
import { useWebSocket } from '../composables/useWebSocket'
import { syncApi } from '../api/sync'
import { settingsApi } from '../api/settings'
import { historyApi } from '../api/history'
import { profilesApi } from '../api/profiles'
import { cardsApi } from '../api/cards'

const cards=ref([]); const sync=ref({}); const syncQueue=ref([]); const storage=ref([])
const recent=ref([]); const profileCount=ref(0); const todayCount=ref(0); const todaySize=ref('')

async function load(){
  try { cards.value=await cardsApi.list() } catch(e){}
  try { const d=await syncApi.status(); sync.value=d } catch(e){}
  try { syncQueue.value=await syncApi.getQueue() } catch(e){}
  try { storage.value=await settingsApi.getStorage() } catch(e){}
  try { const d=await profilesApi.list({page:1,page_size:1}); profileCount.value=d.total } catch(e){}
  try {
    const d=await historyApi.list({page_size:100})
    const t=new Date().toISOString().split('T')[0]
    const ti=d.items.filter(h=>h.started_at?.startsWith(t))
    todayCount.value=ti.reduce((s,h)=>s+h.synced_files,0)
    const b=ti.reduce((s,h)=>s+h.synced_bytes,0)
    todaySize.value=b>1073741824?(b/1073741824).toFixed(1)+'GB':(b/1048576).toFixed(1)+'MB'
  }catch(e){}
  try { const d=await historyApi.list({page:1,page_size:5}); recent.value=d.items } catch(e){}
}
onMounted(load)
useWebSocket(d=>{
  if(d.type==='sync_progress') sync.value={...sync.value,...d}
  if(d.type==='sync_completed'){sync.value={running:false};load()}
  if(d.type==='queue_updated') syncApi.getQueue().then(r=>syncQueue.value=r).catch(()=>{})
})
const cancelQ=async id=>{try{await syncApi.cancelQueue(id);syncQueue.value=await syncApi.getQueue()}catch(e){alert(e.message)}}
const fmtETA=s=>{if(!s)return'';if(s<60)return s+'秒';if(s<3600)return Math.floor(s/60)+'分钟';return Math.floor(s/3600)+'小时'+Math.floor((s%3600)/60)+'分钟'}
</script>
