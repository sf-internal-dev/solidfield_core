<script setup>
import Card from 'primevue/card'
import Button from 'primevue/button'
import Tag from 'primevue/tag'

const kpis = [
  { key: 'orders',   label: 'Open Orders',   value: 12,       delta: +8,  sub: 'vs. last week' },
  { key: 'tickets',  label: 'Open Tickets',  value: 4,        delta: -12, sub: 'vs. last week' },
  { key: 'customers',label: 'Customers',     value: 267,      delta: +2,  sub: 'active' },
  { key: 'uptime',   label: 'Uptime',        value: '99.98%', delta: null, sub: 'last 30 days' },
]

const recent = [
  { id: 'SOLISO-0034', title: 'Replace sensor - Plant 2', status: 'Open',        when: '2h ago' },
  { id: 'SOLISO-0033', title: 'Calibrate pump - Line A',  status: 'In Progress', when: 'yesterday' },
  { id: 'SOLISO-0032', title: 'Inspection - Cooling unit',status: 'Done',        when: '2d ago' },
]

function statusSeverity(s) {
  if (s === 'Open') return 'warning'
  if (s === 'In Progress') return 'info'
  if (s === 'Done') return 'success'
  return null
}

/** Recent Audit Logs (mock) */
const auditLogs = [
  { dt: '2025-08-17T08:12:00Z', msg: 'Technician James Nunez accessed workspace' },
  { dt: '2025-08-17T07:56:10Z', msg: 'Technician Laura Kim created work order SOLISO-0035' },
  { dt: '2025-08-16T22:04:31Z', msg: 'Admin Marcos Silva updated customer Acme Corp' },
  { dt: '2025-08-16T18:42:03Z', msg: 'Technician Priya Shah closed work order SOLISO-0032' },
  { dt: '2025-08-16T10:15:27Z', msg: 'System sync completed (ERP connector)' },
]

function fmt(dt) {
  return new Date(dt).toLocaleString(undefined, {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  })
}

const emit = defineEmits(['open-doc'])
function openItem(w) {
  emit('open-doc', 'workorder', w.id, w.title)
}

/* >>> Botão "View all" abre a aba/página completa de logs */
function openAllLogs() {
  emit('open-doc', 'auditlogs', 'all', 'Audit Logs')
}

function openAllOrders() {
  emit('open-doc', 'orders', 'all', 'Work Orders')
}
</script>

<template>
  <section class="home p-3">
    <!-- KPIs -->
    <div class="grid">
      <div class="col-12 md:col-6 lg:col-3" v-for="card in kpis" :key="card.key">
        <Card class="h-full">
          <template #title>
            <div class="flex align-items-center justify-content-between">
              <span class="text-600 text-sm">{{ card.label }}</span>
              <Tag
                v-if="card.delta !== null"
                :value="(card.delta>0?'+':'') + card.delta + '%'"
                :severity="card.delta>0 ? 'success' : (card.delta<0 ? 'danger' : null)"
              />
            </div>
          </template>
          <template #content>
            <div class="text-3xl font-semibold">{{ card.value }}</div>
            <small class="text-600">{{ card.sub }}</small>
          </template>
        </Card>
      </div>
    </div>

    <div class="grid mt-3">
      <!-- Recent Work Orders -->
      <div class="col-12 lg:col-8">
        <Card>
          <template #title>
            <div class="flex align-items-center justify-content-between">
              <span>Recent Work Orders</span>
              <Button
                label="View all"
                icon="pi pi-arrow-right"
                iconPos="right"
                size="small"
                class="p-button-text"
                @click="openAllOrders"
              />
            </div>
          </template>
          
          <template #content>
            <ul class="list-none m-0 p-0">
              <li
                v-for="w in recent"
                :key="w.id"
                class="flex align-items-center justify-content-between py-2 border-bottom-1 surface-border"
              >
                <div class="flex align-items-center gap-3">
                  <Tag :value="w.status" :severity="statusSeverity(w.status)" />
                  <div>
                    <div class="font-medium">{{ w.title }}</div>
                    <small class="text-600">#{{ w.id }} • {{ w.when }}</small>
                  </div>
                </div>
                <Button label="Open" size="small" @click="openItem(w)" />
              </li>
            </ul>
          </template>
        </Card>
      </div>

      <!-- Right column: Actions + Audit Logs + Announcements -->
      <div class="col-12 lg:col-4">
        <Card>
          <template #title>Quick Actions</template>
          <template #content>
            <div class="flex flex-column gap-2">
              <Button label="New Work Order" icon="pi pi-plus" class="w-full" />
              <Button label="New Customer" icon="pi pi-user-plus" class="w-full p-button-outlined" />
              <Button label="Sync Now" icon="pi pi-refresh" class="w-full p-button-text" />
            </div>
          </template>
        </Card>

        <!-- Recent Audit Logs + botão "View all" -->
        <Card class="mt-3">
          <template #title>
            <div class="flex align-items-center justify-content-between">
              <span>Recent Audit Logs</span>
              <Button
                label="View all"
                icon="pi pi-arrow-right"
                iconPos="right"
                size="small"
                class="p-button-text"
                @click="openAllLogs"
              />
            </div>
          </template>
          <template #content>
            <ul class="list-none m-0 p-0">
              <li
                v-for="(log, i) in auditLogs"
                :key="i"
                class="py-2 border-bottom-1 surface-border"
              >
                <div class="text-sm text-600">{{ fmt(log.dt) }}</div>
                <div class="mt-1">{{ log.msg }}</div>
              </li>
            </ul>
          </template>
        </Card>

        <Card class="mt-3">
          <template #title>Announcements</template>
          <template #content>
            <ul class="m-0 pl-3">
              <li>Scheduled maintenance on Friday 22:00.</li>
              <li>New mobile app version 1.2.0 available.</li>
            </ul>
          </template>
        </Card>
      </div>
    </div>
  </section>
</template>

<style scoped>
.home :deep(.p-card){ border-radius: 12px; }
.text-600 { color: var(--muted); }
</style>
