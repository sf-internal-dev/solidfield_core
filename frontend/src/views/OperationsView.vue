<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watchEffect } from 'vue'

import Card from 'primevue/card'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dropdown from 'primevue/dropdown'
import Checkbox from 'primevue/checkbox'
import InputText from 'primevue/inputtext'

/* Leaflet */
// Leaflet
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'

// Força o bundler a tratar como URL
import iconUrl from 'leaflet/dist/images/marker-icon.png?url'
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png?url'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png?url'

// Define um ícone padrão explícito (com tamanhos/anchors)
const defaultIcon = L.icon({
  iconUrl,
  iconRetinaUrl,
  shadowUrl,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  tooltipAnchor: [16, -28],
  shadowSize: [41, 41]
})
L.Marker.prototype.options.icon = defaultIcon

const emit = defineEmits(['open-doc'])

/* --- Filtros --- */
const q = ref('')
const statusOptions = ['Open', 'In Progress', 'Paused', 'Done']
const status = ref(null)
const showRoutes = ref(true)

/* --- Locais (coordenadas reais) --- */
const sites = [
  { id: 'plant-1', name: 'Plant 1', city: 'Curitiba',   lat: -25.4284, lng: -49.2733 },
  { id: 'plant-2', name: 'Plant 2', city: 'Campinas',   lat: -22.9056, lng: -47.0608 },
  { id: 'warehouse', name: 'Warehouse', city: 'São Paulo', lat: -23.5505, lng: -46.6333 },
]

/* --- Work Orders ativas --- */
const orders = ref([
  { id:'SOLISO-0039', title:'Replace bearing - Line B', site:'Plant 1', tech:'Ana S.',   status:'Open',        eta:'2h' },
  { id:'SOLISO-0038', title:'Safety checklist',         site:'Warehouse', tech:'Diego T.', status:'In Progress', eta:'50m' },
  { id:'SOLISO-0037', title:'Calibrate pump',           site:'Plant 2', tech:'Marcos R.', status:'Paused',      eta:'—' },
])

/* --- Feed de updates --- */
const updates = ref([
  { id:1, when:'5m',  text:'Ana iniciou SOLISO-0039', sev:'info' },
  { id:2, when:'22m', text:'Checklist concluído (SOLISO-0038)', sev:'success' },
  { id:3, when:'1h',  text:'Pausa em SOLISO-0037 aguardando peças', sev:'warn' },
])

const filtered = computed(() => {
  const ql = q.value.trim().toLowerCase()
  return orders.value.filter(o => {
    const okStatus = !status.value || o.status === status.value
    const okSearch = !ql || [o.id,o.title,o.site,o.tech].some(s => (s||'').toLowerCase().includes(ql))
    return okStatus && okSearch
  })
})

function severity(s) {
  if (s === 'Open') return 'warning'
  if (s === 'In Progress') return 'info'
  if (s === 'Paused') return 'danger'
  if (s === 'Done') return 'success'
  return null
}

function openWO(o) {
  emit('open-doc', 'workorder', o.id, o.title)
}

function focusSite(name) {
  q.value = name
}

/* === Leaflet map === */
const mapEl = ref(null)
let map, routeLayer
const markerRefs = []

onMounted(async () => {
  await nextTick()

  map = L.map(mapEl.value, {
    center: [-23.5, -47.5], // centro inicial (SP interior)
    zoom: 6,
    zoomControl: true
  })

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
  }).addTo(map)

  // Marcadores
  const group = L.featureGroup()
  sites.forEach(s => {
    const m = L.marker([s.lat, s.lng], { title: `${s.name} — ${s.city}` })
      .addTo(map)
      .bindPopup(`<b>${s.name}</b><br>${s.city}`)
      .on('click', () => focusSite(s.name))
    markerRefs.push(m)
    group.addLayer(m)
  })

  // Enquadra todos
  if (sites.length) map.fitBounds(group.getBounds().pad(0.2))

  // Rota fictícia entre Plant 1 -> Plant 2 -> Warehouse
  drawRoute()
})

onBeforeUnmount(() => {
  if (map) {
    map.remove()
    map = null
  }
})

function drawRoute() {
  if (!map) return;                // <— evita rodar antes do map existir
  if (routeLayer) { map.removeLayer(routeLayer); routeLayer = null; }
  if (!showRoutes.value || sites.length < 2) return;
  const coords = sites.map(s => [s.lat, s.lng]);
  routeLayer = L.polyline(coords, { color: '#0ea5e9', weight: 3, dashArray: '6,4', opacity: .8 });
  routeLayer.addTo(map);
}
watchEffect(() => { showRoutes.value; drawRoute(); });
watchEffect(drawRoute)
</script>

<template>
  <section class="ops p-3">
    <div class="grid">
      <!-- Esquerda -->
      <div class="col-12 lg:col-8 flex flex-column gap-3">
        <Card>
          <template #title>
            <div class="flex align-items-center justify-content-between">
              <span>Live Operations Map</span>
              <div class="flex align-items-center gap-3">
                <div class="flex align-items-center gap-2">
                  <Checkbox v-model="showRoutes" :binary="true" inputId="routes" />
                  <label for="routes" class="text-sm">Show routes</label>
                </div>
              </div>
            </div>
          </template>
          <template #content>
            <div ref="mapEl" class="leaflet-host"></div>
          </template>
        </Card>

        <Card>
          <template #title>
            <div class="flex align-items-center justify-content-between">
              <span>Active Work Orders</span>
              <div class="flex align-items-center gap-2">
                <InputText v-model="q" placeholder="Search…" class="w-12rem" />
                <Dropdown v-model="status" :options="statusOptions" placeholder="Status" class="w-10rem" />
              </div>
            </div>
          </template>
          <template #content>
            <ul
            class="tab-list"
            ref="tabList"
            :class="['density-' + density]"
            role="tablist"
            aria-label="Open views"
          >
            <li
              v-for="t in tabs"
              :key="t.id"
              class="tab-item"
              :class="{ active: t.id === activeId }"
              role="presentation"
            >
              <button
                class="tab-btn"
                role="tab"
                :aria-selected="t.id === activeId"
                :tabindex="t.id === activeId ? 0 : -1"
                @click="activate(t.id)"
              >
                <Fa v-if="t.icon" :icon="t.icon" class="fa" />
                <span class="tab-title">{{ t.title }}</span>
                <span v-if="t.closable" class="tab-x" @click.stop="closeTab(t.id)">
                  <Fa :icon="['fas','xmark']" />
                </span>
              </button>
            </li>
          </ul>
          </template>
        </Card>
      </div>

      <!-- Direita -->
      <div class="col-12 lg:col-4 flex flex-column gap-3">
        <Card>
          <template #title>Quick Actions</template>
          <template #content>
            <div class="flex flex-column gap-2">
              <Button label="Dispatch Technician" icon="pi pi-send" class="w-full" />
              <Button label="Create Work Order" icon="pi pi-plus" class="w-full p-button-outlined" />
              <Button label="Pause All at Site" icon="pi pi-pause" class="w-full p-button-text" />
            </div>
          </template>
        </Card>

        <Card>
          <template #title>Recent Updates</template>
          <template #content>
            <ul class="m-0 p-0 list-none">
              <li v-for="u in updates" :key="u.id" class="py-2 flex align-items-center gap-2">
                <Tag :value="u.when" severity="secondary" />
                <span :class="['update', u.sev]">{{ u.text }}</span>
              </li>
            </ul>
          </template>
        </Card>
      </div>
    </div>
  </section>
</template>

<style scoped>
.text-600 { color: var(--muted); }

/* Leaflet container */
.leaflet-host{
  height: 360px;
  border-radius: 12px;
  overflow: hidden;
}
.leaflet-container { font: inherit; } /* usa sua fonte Inter */

/* Feed cores */
.update.success{ color:#16a34a; }
.update.warn{ color:#eab308; }
.update.info{ color:#0ea5e9; }
</style>
