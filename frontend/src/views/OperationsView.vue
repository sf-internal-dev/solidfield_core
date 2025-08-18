<script setup>
import { ref, computed } from 'vue'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dropdown from 'primevue/dropdown'
import Checkbox from 'primevue/checkbox'
import Divider from 'primevue/divider'
import InputText from 'primevue/inputtext'

const emit = defineEmits(['open-doc'])

/* --- Filtros --- */
const q = ref('')
const statusOptions = ['Open', 'In Progress', 'Paused', 'Done']
const status = ref(null)
const showRoutes = ref(true)

/* --- Locais no “mapa” (posições em %) --- */
const sites = [
  { id: 'plant-1', name: 'Plant 1', city: 'Curitiba',  x: 32, y: 48 },
  { id: 'plant-2', name: 'Plant 2', city: 'Campinas',  x: 58, y: 36 },
  { id: 'warehouse', name: 'Warehouse', city: 'São Paulo', x: 74, y: 62 },
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
</script>

<template>
  <section class="ops p-3">
    <div class="grid">
      <!-- Coluna esquerda: Mapa + Lista -->
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
            <div class="ops-map">
              <!-- rotas fictícias -->
              <svg v-if="showRoutes" class="route-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
                <path d="M32,48 C40,30 58,36 74,62" class="route" />
              </svg>

              <!-- marcadores -->
              <button
                v-for="s in sites"
                :key="s.id"
                class="marker"
                :style="{ left: s.x + '%', top: s.y + '%'}"
                :title="s.name + ' — ' + s.city"
                @click="focusSite(s.name)"
              >
                <span class="dot"></span>
                <span class="label">{{ s.name }}</span>
              </button>
            </div>
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
            <ul class="list-none m-0 p-0">
              <li
                v-for="o in filtered"
                :key="o.id"
                class="row-item flex align-items-center justify-content-between py-2 border-bottom-1 surface-border"
              >
                <div class="flex align-items-center gap-3">
                  <Tag :value="o.status" :severity="severity(o.status)" />
                  <div>
                    <div class="font-medium">{{ o.title }}</div>
                    <small class="text-600">#{{ o.id }} • {{ o.site }} • {{ o.tech }} • ETA {{ o.eta }}</small>
                  </div>
                </div>
                <div class="flex align-items-center gap-2">
                  <Button label="Open" size="small" @click="openWO(o)" />
                  <Button label="Complete" size="small" class="p-button-outlined" />
                </div>
              </li>
            </ul>
          </template>
        </Card>
      </div>

      <!-- Coluna direita: Ações & Updates -->
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

/* Mapa fictício */
.ops-map{
  position: relative;
  height: 360px;
  border-radius: 12px;
  background:
    linear-gradient(0deg, rgba(0,0,0,.03) 1px, transparent 1px) 0 0/100% 24px,
    linear-gradient(90deg, rgba(0,0,0,.03) 1px, transparent 1px) 0 0/24px 100%,
    #e9eef3;
  overflow: hidden;
}

/* rotas */
.route-svg{
  position:absolute; inset:0;
}
.route{
  fill:none;
  stroke:#0ea5e9;
  stroke-width:1.5;
  stroke-dasharray:3 2;
  opacity:.7;
}

/* marcadores */
.marker{
  position:absolute;
  transform: translate(-50%, -100%); /* ancora na base do pin */
  background: transparent;
  border: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
.marker .dot{
  width: 12px; height: 12px;
  border-radius: 50%;
  background: #ef4444;
  box-shadow: 0 0 0 3px rgba(239,68,68,.25);
}
.marker .label{
  background: #fff;
  color: #111827;
  font-size: .8rem;
  padding: 2px 6px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,.08);
}

/* lista */
.row-item:last-child{ border-bottom: 0 !important; }

/* feed */
.update.success{ color:#16a34a; }
.update.warn{ color:#eab308; }
.update.info{ color:#0ea5e9; }
</style>
