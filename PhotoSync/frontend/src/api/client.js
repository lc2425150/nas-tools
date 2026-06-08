const BASE = '/api/v1'
async function request(path, opts = {}) {
  const r = await fetch(`${BASE}${path}`, { headers: { 'Content-Type': 'application/json', ...opts.headers }, ...opts })
  if (!r.ok) { const e = await r.json().catch(()=>({error:{message:r.statusText}})); throw new Error(e.error?.message||`HTTP ${r.status}`) }
  return r.json()
}
export const api = { get:p=>request(p), post:(p,d)=>request(p,{method:'POST',body:JSON.stringify(d)}), put:(p,d)=>request(p,{method:'PUT',body:JSON.stringify(d)}), delete:p=>request(p,{method:'DELETE'}) }
