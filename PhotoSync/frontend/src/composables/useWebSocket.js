import { ref, onMounted, onUnmounted } from 'vue'
export function useWebSocket(onMsg) {
  const connected = ref(false); let ws = null; let rt = null
  function connect() {
    const p = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${p}//${window.location.host}/api/v1/ws/sync/status`)
    ws.onopen = () => { connected.value = true }
    ws.onclose = () => { connected.value = false; rt = setTimeout(connect, 3000) }
    ws.onmessage = (e) => { try { const d = JSON.parse(e.data); if (onMsg) onMsg(d) } catch {} }
  }
  onMounted(() => connect())
  onUnmounted(() => { if(rt) clearTimeout(rt); if(ws) ws.close() })
  return { connected }
}
