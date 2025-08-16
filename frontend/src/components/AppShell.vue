<template>
  <div class="app-shell">
    <!-- TOPBAR atravessa toda a largura -->
    <header class="topbar">
      <div class="top-left">
        <img src="/solidfield_logo.svg" alt="Logo" class="brand" />
      </div>

      <!-- Abas estilo navegador no centro -->
      <ul class="tab-list" role="tablist" aria-label="Open views">
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
            <i :class="t.icon" aria-hidden="true" />
            <span class="tab-title">{{ t.title }}</span>
          </button>
          <button
            v-if="t.closable"
            class="tab-close"
            @click="closeTab(t.id)"
            aria-label="Close tab"
          >
            <i class="pi pi-times" />
          </button>
        </li>
      </ul>

      <div class="top-actions">
        <!-- ações (perfil, notificações, etc.) -->
      </div>
    </header>

    <!-- SIDEBAR fica abaixo da topbar, à esquerda -->
    <aside class="sidebar">
      <nav class="side-icons" aria-label="Primary navigation">
        <button
          v-for="item in sideItems"
          :key="item.key"
          class="icon-btn"
          :class="{ active: activeKey === item.key }"
          @click="openFromSidebar(item.key)"
          :title="item.label"
        >
          <i :class="item.icon" />
        </button>
      </nav>
    </aside>

    <!-- CONTEÚDO à direita da sidebar -->
    <main class="content">
      <div class="canvas" aria-live="polite">
        <div class="square-frame">
          <component :is="activeComponent" />
        </div>
      </div>
    </main>
  </div>
</template>


<script setup>
import { ref, computed } from 'vue'

/** Ícones da sidebar (apenas um por “seção” de alto nível) */
const sideItems = [
  { key: 'home',      label: 'Home',        icon: 'pi pi-home' },
  { key: 'orders',    label: 'Work Orders', icon: 'pi pi-clipboard' },
  { key: 'customers', label: 'Customers',   icon: 'pi pi-users' },
  { key: 'settings',  label: 'Settings',    icon: 'pi pi-cog' }
]

/** Pedaços de UI (demos). Em prod, troque por imports de componentes reais. */
const panes = {
  HomePane:      { template: `<div class="pane"><h2>Home</h2><p>Bem-vindo! Selecione um item na barra lateral.</p></div>` },
  OrdersPane:    { template: `<div class="pane"><h2>Work Orders</h2><p>Conteúdo de ordens de serviço.</p></div>` },
  CustomersPane: { template: `<div class="pane"><h2>Customers</h2><p>Lista/gestão de clientes.</p></div>` },
  SettingsPane:  { template: `<div class="pane"><h2>Settings</h2><p>Preferências do sistema.</p></div>` },
}

/** Abas internas (sem router): cada aba guarda o OBJETO do componente */
const tabs = ref([
  { id: 'home', key: 'home', title: 'Home', icon: 'pi pi-home', closable: false, component: panes.HomePane }
])
const activeId = ref('home')
const activeKey = computed(() => tabs.value.find(t => t.id === activeId.value)?.key)
const activeComponent = computed(() => tabs.value.find(t => t.id === activeId.value)?.component)

/** Abre/ativa aba a partir da sidebar (deduplica por key) */
function openFromSidebar(key) {
  const exists = tabs.value.find(t => t.key === key)
  if (exists) return activate(exists.id)

  const cfg = {
    home:      { title: 'Home',        icon: 'pi pi-home',      component: panes.HomePane,      closable: false },
    orders:    { title: 'Work Orders', icon: 'pi pi-clipboard', component: panes.OrdersPane,    closable: true  },
    customers: { title: 'Customers',   icon: 'pi pi-users',     component: panes.CustomersPane, closable: true  },
    settings:  { title: 'Settings',    icon: 'pi pi-cog',       component: panes.SettingsPane,  closable: true  },
  }[key]
  if (!cfg) return

  const id = `${key}-${Math.random().toString(36).slice(2,7)}`
  tabs.value.push({ id, key, ...cfg })
  activate(id)
}

/** Ativa aba pelo id */
function activate(id) {
  activeId.value = id
}

/** Fecha aba e escolhe a próxima ativa de forma inteligente */
function closeTab(id) {
  const idx = tabs.value.findIndex(t => t.id === id)
  if (idx === -1) return
  const wasActive = tabs.value[idx].id === activeId.value
  tabs.value.splice(idx, 1)

  if (!tabs.value.length) {
    // garante pelo menos uma aba (Home)
    tabs.value.push({ id: 'home', key: 'home', title: 'Home', icon: 'pi pi-home', closable: false, component: panes.HomePane })
    activeId.value = 'home'
    return
  }
  if (wasActive) {
    const next = tabs.value[idx] || tabs.value[idx - 1] || tabs.value[0]
    activeId.value = next.id
  }
}

/** (Opcional) exemplo para abrir “documentos” em abas (multi-instâncias) */
function openDoc(type, id, title) {
  const tabId = `${type}:${id}`
  const exists = tabs.value.find(t => t.id === tabId)
  if (exists) return activate(tabId)
  const component = { template: `<div class="pane"><h2>${title}</h2><p>${type} #${id}</p></div>` }
  tabs.value.push({ id: tabId, key: type, title, icon: 'pi pi-file', closable: true, component })
  activate(tabId)
}
</script>


<style scoped>
/* ====== Grid base com áreas nomeadas ====== */
.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 80px 1fr;         /* sidebar | conteúdo */
  grid-template-rows: 56px 1fr;            /* topbar | resto     */
  grid-template-areas:
    "topbar  topbar"
    "sidebar content";
  background: #f5f5f5;
}

/* ====== Topbar ====== */
.topbar {
  grid-area: topbar;
  display: grid;
  grid-template-columns: auto 1fr auto;    /* logo | abas | ações */
  align-items: center;
  gap: 8px;
  background: #ffffff;
  border-bottom: 1px solid rgba(0,0,0,0.06);
  padding: 0 8px;
}

.top-left {
  display: flex; align-items: center; gap: 8px;
}
.brand {
  height: 28px;           /* experimente 48–52px; cabe numa topbar de 56px */
  width: auto;            /* mantém proporção 1088x227 */
  max-height: calc(100% - 8px); /* evita encostar nas bordas da topbar */
  max-width: min(260px, 40vw);  /* não deixa a logo esmagar as abas */
  object-fit: contain;
  display: block;
}

/* Abas estilo navegador */
.tab-list {
  list-style: none; margin: 0; padding: 0 8px;
  display: flex; gap: 6px; overflow: auto;
}
.tab-item {
  display: flex; align-items: stretch; gap: 2px;
  border-radius: 10px; background: transparent;
}
.tab-item.active { background: rgba(0,0,0,0.04); }
.tab-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 8px 12px; border: 0; background: transparent; border-radius: 10px;
  color: var(--text-color, #111827); cursor: pointer;
}
.tab-btn:hover { background: rgba(0,0,0,0.05); }
.tab-title { white-space: nowrap; }
.tab-close {
  border: 0; background: transparent; cursor: pointer;
  color: #6b7280; padding: 0 8px; border-radius: 8px;
}
.tab-close:hover { background: rgba(0,0,0,0.08); color: #111827; }
.top-actions { padding-right: 4px; }

/* ====== Sidebar ====== */
.sidebar {
  grid-area: sidebar;
  background: #ffffff;
  color: #fff;
  display: flex; flex-direction: column; align-items: center;
  padding: 12px 8px; gap: 12px;
  border-right: 1px solid rgba(0,0,0,0.06);
}
.side-icons { display: flex; flex-direction: column; gap: 8px; margin-top: 4px; }
.icon-btn {
  width: 48px; height: 48px;
  border: 0; border-radius: 12px;
  background: transparent; color: #cfd9e3;
  display: grid; place-items: center; cursor: pointer;
}
.icon-btn:hover { background: rgba(255,255,255,0.08); color: #071039; }
.icon-btn.active { background: rgba(255,255,255,0.16); color: #0e0c27; }

/* ====== Conteúdo ====== */
.content { grid-area: content; padding: 16px; }
.canvas  { width: 100%; height: 100%; display: grid; place-items: center; }
.square-frame {
  aspect-ratio: 1 / 1;
  width: min(90vmin, 900px);
  background: #fff; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.06);
  display: grid; place-items: center; padding: 24px;
}
.pane { text-align: center; }
.pane h2 { margin: 0 0 8px; font-size: 1.25rem; }

/* ====== Responsivo ====== */
@media (max-width: 768px) {
  .app-shell { grid-template-columns: 64px 1fr; }
  .brand { width: 104px;  }
  .icon-btn { width: 44px; height: 44px; }
}

</style>

<!--
USO:
1) Salve este arquivo como src/components/AppShell.vue
2) No App.vue: <template><AppShell /></template>
3) Ajuste sideItems, títulos e panes conforme suas rotas reais.
4) Para renderizar páginas reais, troque a <component :is="activeComponent"/> por <router-view/>,
   e faça as abas refletirem a navegação (opcionalmente usando vue-router).
-->
