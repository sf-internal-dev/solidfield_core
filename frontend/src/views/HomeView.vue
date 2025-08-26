<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'

/* ====== Estado “técnico” ====== */
const cams = reactive([
  { id: 'cam-entrance', label: 'Entrance RTSP', addr: 'rtsp://10.0.0.12:554/entrance', fps: 24, connected: true },
  { id: 'cam-warehouse', label: 'Warehouse RTSP', addr: 'rtsp://10.0.0.21:554/wh1', fps: 18, connected: false },
  { id: 'cam-yard', label: 'Yard RTSP', addr: 'rtsp://10.0.0.35:554/yard', fps: 22, connected: true },
])
const activeCamId = ref(cams[0].id)
const activeCam = computed(() => cams.find(c => c.id === activeCamId.value))

const ws = reactive({ url: 'wss://broker.example/ws', connected: false, rtt: 0 })
const mqtt = reactive({ url: 'mqtts://iot.example:8883', connected: true, msgs: 0 })

const queue = reactive({ ingest: 3, transcode: 1, dispatch: 2 })
const cpu = ref(22)   // %
const mem = ref(48)   // %
const net = reactive({ up: 1.2, down: 7.6 }) // MB/s

/* telemetria p/ sparklines */
const spark = reactive({
  cpu: Array.from({length: 40}, () => 20 + Math.random()*10),
  net: Array.from({length: 40}, () => 5 + Math.random()*5),
  fps: Array.from({length: 40}, () => activeCam.value?.fps ?? 20),
})

/* Dispatch */
const address = ref('')
const techns = ['alice.t','bob.k','carol.m','diego.r'].map(v => ({label:v, value:v}))
const techSel = ref(null)
const priority = ref('P2')
const priOpts = [{label:'P1',value:'P1'},{label:'P2',value:'P2'},{label:'P3',value:'P3'}]

/* Logs */
const logs = ref([])
const logBox = ref(null)
function pushLog(line){
  const ts = new Date().toISOString().replace('T',' ').split('.')[0]
  logs.value.push(`[${ts}] ${line}`)
  nextTick(() => {
    const el = logBox.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

/* Ações fake */
function toggleCamConnection(cam){
  cam.connected = !cam.connected
  pushLog(`CAM ${cam.id} ${cam.connected ? 'CONNECTED' : 'DISCONNECTED'}`)
}
function connectWS(){ ws.connected = true; ws.rtt = 42; pushLog(`WS CONNECTED ${ws.url}`) }
function disconnectWS(){ ws.connected = false; ws.rtt = 0; pushLog('WS DISCONNECTED') }
function connectMQTT(){ mqtt.connected = true; pushLog(`MQTT CONNECTED ${mqtt.url}`) }
function disconnectMQTT(){ mqtt.connected = false; pushLog('MQTT DISCONNECTED') }

function dispatchJob(){
  if (!address.value || !techSel.value) {
    pushLog('DISPATCH ERROR missing address/technician')
    return
  }
  const jobId = Math.random().toString(36).slice(2,7).toUpperCase()
  queue.dispatch++
  pushLog(`DISPATCH ${jobId} -> ${techSel.value} @ "${address.value}" (${priority.value})`)
  address.value = ''; techSel.value = null
}

/* Simuladores */
let t
onMounted(() => {
  pushLog('TECH OPS LAB READY')
  t = setInterval(() => {
    // CPU/Mem/Net “noise”
    cpu.value = Math.max(5, Math.min(98, cpu.value + (Math.random()*6 - 3)))
    mem.value = Math.max(10, Math.min(96, mem.value + (Math.random()*4 - 2)))
    net.up = Math.max(0.2, Math.min(20, net.up + (Math.random()*2 - 1)))
    net.down = Math.max(1, Math.min(50, net.down + (Math.random()*6 - 3)))

    // filas
    queue.ingest = Math.max(0, queue.ingest + (Math.random() > .6 ? 1 : -1))
    queue.transcode = Math.max(0, queue.transcode + (Math.random() > .75 ? 1 : -1))
    queue.dispatch = Math.max(0, queue.dispatch + (Math.random() > .5 ? 1 : -1))

    // mqtt msgs
    if (mqtt.connected) mqtt.msgs += Math.floor(Math.random()*5)

    // ws RTT oscila
    if (ws.connected) ws.rtt = Math.max(20, Math.min(180, ws.rtt + (Math.random()*20 - 10)))

    // sparklines shift
    spark.cpu.shift(); spark.cpu.push(cpu.value)
    spark.net.shift(); spark.net.push(net.down)
    spark.fps.shift(); spark.fps.push((activeCam.value?.fps ?? 20) + (Math.random()*2 - 1))
  }, 1200)
})
onBeforeUnmount(() => clearInterval(t))

/* helpers sparkline */
function linePath(values, w=140, h=36, pad=2){
  if (!values.length) return ''
  const min = Math.min(...values), max = Math.max(...values)
  const dx = (w - pad*2) / (values.length - 1 || 1)
  const scaleY = (v) => {
    if (max === min) return h/2
    const t = (v - min) / (max - min)
    return h - pad - t*(h - pad*2)
  }
  return values.map((v,i) => `${i===0?'M':'L'} ${pad + i*dx} ${scaleY(v)}`).join(' ')
}
</script>

<template>
  <div class="techlab">
    <!-- COL ESQ: Câmeras -->
    <section class="col camcol">
      <header class="pane-head">
        <h3>Cameras</h3>
        <select v-model="activeCamId">
          <option v-for="c in cams" :key="c.id" :value="c.id">{{ c.label }}</option>
        </select>
      </header>

      <div class="cam-card">
        <div class="fake-video" :class="{ offline: !activeCam?.connected }">
          <div class="scan"></div>
          <div class="v-meta">
            <div class="row">
              <span class="tag">{{ activeCam?.id }}</span>
              <span class="dot" :class="activeCam?.connected ? 'ok':'err'"></span>
            </div>
            <div class="mono small">{{ activeCam?.addr }}</div>
            <div class="row tiny">
              <span>FPS ~ {{ Math.round(spark.fps.at(-1) || 0) }}</span>
              <span>Q: {{ queue.transcode }}</span>
            </div>
          </div>
        </div>
        <div class="cam-actions">
          <button class="btn" @click="toggleCamConnection(activeCam)">Toggle Link</button>
          <button class="btn ghost" @click="pushLog('PTZ: MOVE PRESET #2')">PTZ Preset #2</button>
          <button class="btn ghost" @click="pushLog('Snapshot saved')">Snapshot</button>
        </div>
      </div>

      <div class="mini-grid">
        <div v-for="c in cams" :key="c.id" class="mini">
          <div class="mini-thumb" :class="{ off: !c.connected }"></div>
          <div class="mini-meta">
            <div class="name">{{ c.label }}</div>
            <div class="addr mono tiny">{{ c.addr }}</div>
          </div>
          <button class="mini-btn" @click="activeCamId = c.id">Open</button>
        </div>
      </div>
    </section>

    <!-- COL CENTRO: Dispatch + mapa -->
    <section class="col centercol">
      <header class="pane-head">
        <h3>Dispatch Console</h3>
        <div class="badges">
          <span class="pill p1" v-if="priority==='P1'">P1</span>
          <span class="pill p2" v-else-if="priority==='P2'">P2</span>
          <span class="pill p3" v-else>P3</span>
        </div>
      </header>

      <div class="dispatch">
        <div class="row">
          <input class="input" v-model="address" placeholder="Address / Asset / Geo (lat,lng)" />
          <select class="select" v-model="techSel">
            <option :value="null" disabled>Select technician</option>
            <option v-for="t in techns" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
          <select class="select sm" v-model="priority">
            <option v-for="p in priOpts" :key="p.value" :value="p.value">{{ p.label }}</option>
          </select>
          <button class="btn primary" @click="dispatchJob">Dispatch</button>
        </div>

        <div class="map-stub">
          <div class="gridlines"></div>
          <div class="node a"></div>
          <div class="node b"></div>
          <div class="node c"></div>
          <div class="legend">
            <span class="dot ok"></span> online
            <span class="dot warn"></span> delayed
            <span class="dot err"></span> offline
          </div>
        </div>
      </div>
    </section>

    <!-- COL DIR: Conectividade + Telemetria -->
    <section class="col rightcol">
      <header class="pane-head"><h3>Connectivity</h3></header>
      <div class="net-card">
        <div class="kv">
          <div class="k">WebSocket</div>
          <div class="v">
            <span class="badge" :class="ws.connected ? 'ok':'err'">{{ ws.connected ? 'connected' : 'down' }}</span>
            <span class="mono url">{{ ws.url }}</span>
          </div>
        </div>
        <div class="kv">
          <div class="k">RTT</div>
          <div class="v mono">{{ ws.connected ? ws.rtt + ' ms' : '—' }}</div>
        </div>
        <div class="kv">
          <div class="k">MQTT</div>
          <div class="v">
            <span class="badge" :class="mqtt.connected ? 'ok':'err'">{{ mqtt.connected ? 'connected' : 'down' }}</span>
            <span class="mono url">{{ mqtt.url }}</span>
          </div>
        </div>
        <div class="kv">
          <div class="k">Messages</div>
          <div class="v mono">{{ mqtt.msgs }}</div>
        </div>
        <div class="row actions">
          <button class="btn ghost" @click="ws.connected ? disconnectWS() : connectWS()">
            {{ ws.connected ? 'Disconnect WS' : 'Connect WS' }}
          </button>
          <button class="btn ghost" @click="mqtt.connected ? disconnectMQTT() : connectMQTT()">
            {{ mqtt.connected ? 'Disconnect MQTT' : 'Connect MQTT' }}
          </button>
        </div>
      </div>

      <header class="pane-head mt"><h3>System</h3></header>
      <div class="sys-card">
        <div class="kv"><div class="k">CPU</div><div class="v"><span class="mono">{{ Math.round(cpu) }}%</span></div></div>
        <svg class="spark" viewBox="0 0 140 36" preserveAspectRatio="none">
          <path :d="linePath(spark.cpu)" />
        </svg>
        <div class="kv"><div class="k">Downlink</div><div class="v"><span class="mono">{{ net.down.toFixed(1) }} MB/s</span></div></div>
        <svg class="spark" viewBox="0 0 140 36" preserveAspectRatio="none">
          <path :d="linePath(spark.net)" />
        </svg>
        <div class="grid q">
          <div class="qbox"><div class="qk">Ingest</div><div class="qv mono">{{ queue.ingest }}</div></div>
          <div class="qbox"><div class="qk">Transcode</div><div class="qv mono">{{ queue.transcode }}</div></div>
          <div class="qbox"><div class="qk">Dispatch</div><div class="qv mono">{{ queue.dispatch }}</div></div>
        </div>
      </div>
    </section>

    <!-- RODAPÉ: logs -->
    <section class="footer">
      <div class="logs" ref="logBox">
        <pre v-for="(l,i) in logs" :key="i">{{ l }}</pre>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* Layout */
.techlab{
  --bg:#0b1323;
  --panel:#0e172a;
  --card:#101827;
  --muted:#97a3b6;
  --ok:#22c55e; --warn:#eab308; --err:#ef4444;
  --pri:#fcc800; --pri-ink:#0d1f2e;

  display:grid;
  grid-template-columns: 1.2fr 1.8fr 1.2fr;
  grid-template-rows: auto 220px;
  gap:14px;
  padding:16px;
  background: var(--bg);
  color:#e5e7eb;
}
.pane-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.pane-head h3{margin:0;font-size:0.95rem;letter-spacing:.04em;text-transform:uppercase;color:#cdd6e3}

.col{background:var(--panel); border:1px solid rgba(255,255,255,.05); border-radius:12px; padding:12px}
.footer{grid-column: 1 / -1; background:var(--panel); border:1px solid rgba(255,255,255,.05); border-radius:12px; padding:8px}

/* Câmera */
.cam-card{background:var(--card); border:1px solid rgba(255,255,255,.06); border-radius:10px; padding:10px}
.fake-video{
  position:relative; height:220px; border-radius:10px;
  background: radial-gradient(ellipse at center, #0a1020 0%, #050813 100%);
  overflow:hidden; border:1px solid rgba(255,255,255,.08);
}
.fake-video.offline{ background:#1b2433; }
.fake-video .scan{
  position:absolute; inset:0; background:repeating-linear-gradient( to bottom, rgba(255,255,255,.05), rgba(255,255,255,.05) 1px, transparent 1px, transparent 3px );
  animation:scan 4s linear infinite;
  mix-blend-mode: overlay; pointer-events:none;
}
@keyframes scan { 0%{background-position-y:0} 100%{background-position-y:200px} }
.v-meta{
  position:absolute; left:10px; right:10px; bottom:10px;
  font-size:.8rem; color:#cfd9e3; text-shadow:0 1px 0 #000;
}
.v-meta .row{display:flex; align-items:center; gap:8px; justify-content:space-between}
.v-meta .tiny{opacity:.8; font-size:.72rem}
.tag{background:rgba(255,255,255,.08); padding:2px 6px; border-radius:6px}
.dot{width:10px;height:10px;border-radius:50%;}
.dot.ok{background:var(--ok)} .dot.warn{background:var(--warn)} .dot.err{background:var(--err)}
.mono{font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace}
.small{font-size:.78rem}

.cam-actions{display:flex; gap:8px; margin-top:10px}
.btn{background:#1a2333; color:#e5e7eb; border:1px solid rgba(255,255,255,.08); border-radius:8px; padding:8px 10px; cursor:pointer}
.btn:hover{filter:brightness(1.06)}
.btn.ghost{background:transparent}
.btn.primary{background:var(--pri); color:var(--pri-ink); border-color:transparent; font-weight:700}
.btn.primary:hover{filter:brightness(.95)}

.mini-grid{display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:8px; margin-top:10px}
.mini{display:grid; grid-template-columns: 56px 1fr auto; gap:8px; align-items:center; background:#0f1a2d; border:1px solid rgba(255,255,255,.06); border-radius:8px; padding:6px}
.mini-thumb{width:56px;height:36px;border-radius:6px;background:linear-gradient(135deg,#243a63,#16233d)}
.mini-thumb.off{filter:grayscale(1) brightness(.6)}
.mini-meta .name{font-size:.86rem}
.mini-meta .addr{opacity:.7}
.mini-btn{background:transparent; color:#cdd6e3; border:1px solid rgba(255,255,255,.12); border-radius:8px; padding:6px 8px; cursor:pointer}

/* Dispatch + mapa */
.dispatch .row{display:flex; gap:8px; margin-bottom:8px}
.input,.select{
  background:#0f1a2d; color:#e5e7eb; border:1px solid rgba(255,255,255,.12);
  padding:8px 10px; border-radius:8px; outline:none; min-width:0;
}
.select.sm{ width: 88px }
.badges .pill{padding:2px 8px;border-radius:999px;font-size:.75rem}
.p1{background:#ef4444} .p2{background:#eab308} .p3{background:#22c55e}

.map-stub{
  position:relative; height:300px; border-radius:10px; background:#081222; border:1px solid rgba(255,255,255,.08); overflow:hidden;
}
.map-stub .gridlines{
  position:absolute; inset:0;
  background:
    linear-gradient(#0c1a31 1px, transparent 1px) 0 0/ 100% 28px,
    linear-gradient(90deg, #0c1a31 1px, transparent 1px) 0 0/ 28px 100%;
  opacity:.8
}
.map-stub .node{
  position:absolute; width:12px; height:12px; border-radius:50%; box-shadow:0 0 0 3px rgba(255,255,255,.06);
}
.node.a{ left:18%; top:28%; background:#22c55e; animation:pulse 1.8s infinite }
.node.b{ left:62%; top:46%; background:#eab308; animation:pulse 2.2s infinite }
.node.c{ left:42%; top:72%; background:#ef4444; animation:pulse 2.8s infinite }
@keyframes pulse {
  0%{ transform:scale(1) } 50%{ transform:scale(1.4) } 100%{ transform:scale(1) }
}
.map-stub .legend{
  position:absolute; right:10px; bottom:10px; display:flex; gap:10px; align-items:center;
  background:#0f1a2d; border:1px solid rgba(255,255,255,.08); border-radius:999px; padding:6px 10px; color:#cdd6e3; font-size:.8rem
}

/* Conectividade + sistema */
.net-card, .sys-card{
  background:var(--card); border:1px solid rgba(255,255,255,.06); border-radius:10px; padding:10px; margin-bottom:10px
}
.kv{display:grid; grid-template-columns: 88px 1fr; gap:6px; align-items:center; margin:6px 0}
.kv .k{color:#9fb0c9; font-size:.82rem}
.kv .v{display:flex; align-items:center; gap:8px}
.badge{padding:2px 8px;border-radius:999px;font-size:.7rem;text-transform:uppercase;letter-spacing:.04em}
.badge.ok{background:rgba(34,197,94,.2); color:#34d399}
.badge.err{background:rgba(239,68,68,.2); color:#f87171}
.url{opacity:.8}
.row.actions{display:flex; gap:8px; margin-top:6px}

.grid.q{display:grid; grid-template-columns: repeat(3,1fr); gap:8px; margin-top:8px}
.qbox{background:#0f1a2d; border:1px solid rgba(255,255,255,.06); border-radius:8px; padding:8px}
.qk{color:#9fb0c9; font-size:.78rem}
.qv{font-size:1.1rem}

.spark{width:100%; height:36px; margin:4px 0}
.spark path{ fill:none; stroke:#7dd3fc; stroke-width:2; vector-effect:non-scaling-stroke }

/* Logs */
.logs{
  background:#0a1426; border:1px solid rgba(255,255,255,.06); border-radius:10px;
  height:200px; overflow:auto; padding:10px
}
.logs pre{ margin:0; font: 12px/1.5 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; color:#cfe1ff }

/* Responsivo */
@media (max-width: 1100px){
  .techlab{ grid-template-columns: 1fr; grid-template-rows: auto auto auto 220px }
}
</style>
