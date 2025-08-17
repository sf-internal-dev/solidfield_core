<template>
  <div class="app-shell">
    <!-- TOPBAR atravessa toda a largura -->
    <header class="topbar">
      <div class="top-left">
        <img src="/solidfield_logo.svg" alt="Logo" class="brand" />
      </div>

      <!-- Abas estilo navegador no centro -->
      <Draggable
  v-model="tabs"
  item-key="id"
  tag="ul"
  class="tab-list"
  handle=".tab-handle"
  :animation="150"
  :force-fallback="true"
  :scroll="true"
  ghost-class="tab-ghost"
  chosen-class="tab-chosen"
  drag-class="tab-drag"
  @end="onReorder"
>
  <template #item="{ element: t }">
    <li
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
        <!-- HANDLE de arraste (não ativa a aba) -->
        <span class="tab-handle" title="Drag tab" @mousedown.stop @touchstart.stop>
          <Fa :icon="['fas','grip-vertical']" />
        </span>

        <!-- Ícone da aba -->
        <Fa :icon="t.icon || ['fas','house']" class="fa" />

        <!-- Título -->
        <span class="tab-title">{{ t.title }}</span>

        <!-- X dentro da aba -->
        <span
          v-if="t.closable"
          class="tab-x"
          role="button"
          aria-label="Close tab"
          @click.stop="closeTab(t.id)"
        >
          <Fa :icon="['fas','xmark']" />
        </span>
      </button>
    </li>
  </template>
</Draggable>



      <div class="top-actions">
         <button class="help-btn" type="button" @click="openDocs" title="Open documentation">
          <Fa :icon="['fas','circle-question']" class="icn" />
          <span class="label">Help</span>
        </button>
        <div class="lang-switch" @keydown.esc="langMenuOpen=false">
          <button class="lang-btn" type="button" @click="toggleLangMenu">
            <span class="fi" :class="'fi-' + currentLang.cc"></span>
            <span class="lang-code">{{ currentLang.code.toUpperCase() }}</span>
            <Fa :icon="['fas','angle-down']" class="caret" />
          </button>

          <ul v-if="langMenuOpen" class="lang-menu">
            <li v-for="l in langs" :key="l.code" :class="{ active: l.code === currentLang.code }" @click="setLang(l)">
              <span class="fi" :class="'fi-' + l.cc"></span>
              <span class="label">{{ l.label }}</span>
            </li>
          </ul>
        </div>
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
            <Fa :icon="item.icon" :fixed-width="true" class="fa" />
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
import HomeView from '@/views/HomeView.vue'
import Draggable from 'vuedraggable'
// ícone FA usado no botão/aba: 'circle-question' ou 'book'
// (no main.js, lembre de add à lib: faCircleQuestion ou faBook)

function openDocs() {
  const tabId = 'docs:main'
  const exists = tabs.value.find(t => t.id === tabId)
  if (exists) return activate(tabId)

  const component = {
    template: `
      <div class="pane">
        <h2>Documentation</h2>
        <p>Central de ajuda e guias do sistema.</p>
        <ul style="margin: 0; padding-left: 1rem; line-height: 1.6;">
          <li><a href="#" target="_blank" rel="noopener">Getting Started</a></li>
          <li><a href="#" target="_blank" rel="noopener">Work Orders Guide</a></li>
          <li><a href="#" target="_blank" rel="noopener">API Reference</a></li>
        </ul>
      </div>
    `
  }

  tabs.value.push({
    id: tabId,
    key: 'docs',
    title: 'Documentation',
    icon: ['fas','book'],   // ou ['fas','circle-question']
    closable: true,
    component
  })
  activate(tabId)
}

const langMenuOpen = ref(false)
const currentLang = ref({ code: 'en', cc: 'us', label: 'English' })
const langs = [
  { code: 'en', cc: 'us', label: 'English' },
  { code: 'es', cc: 'es', label: 'Español' },
  { code: 'de', cc: 'de', label: 'Deutsch' }
]

function toggleLangMenu() { langMenuOpen.value = !langMenuOpen.value }
function setLang(l) { currentLang.value = l; langMenuOpen.value = false }

/** Ícones da sidebar (apenas um por “seção” de alto nível) */
const sideItems = [
  { key: 'home',      label: 'Home',        icon: ['fas', 'house'] },
  { key: 'orders',    label: 'Work Orders', icon: ['fas', 'clipboard-list'] },
  { key: 'customers', label: 'Customers',   icon: ['fas', 'users'] },
  { key: 'settings',  label: 'Settings',    icon: ['fas', 'gear'] },
]

/** Pedaços de UI (demos). Em prod, troque por imports de componentes reais. */
const panes = {
  HomePane:       HomeView,
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
    customers: { title: 'Technicians',   icon: 'pi pi-users',     component: panes.CustomersPane, closable: true  },
    settings:  { title: 'Work Order #SOLIWO01534',    icon: 'pi pi-cog',       component: panes.SettingsPane,  closable: true  },
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
/* =============== TOKENS & GRID =============== */
.app-shell{
  /* tokens */
  --topbar-h:56px; --sidebar-w:80px;
  --surface:#fff; --ground:#f5f5f5;
  --text:#0f172a; --muted:#6b7280; --side-bg:#0f172a;

  /* tabs (browser) */
  --tab-h:36px; --tab-pad-x:14px; --tab-radius:12px; --tab-gap:10px;
  --tab-inactive-bg:#f5f5f5; --tab-inactive-fg:#111827; --tab-border:#d8dbe2;
  --tab-active-bg:#FCC800;   --tab-active-fg:#111827;  --tab-active-border:#cfd3da;

  /* layout */
  min-height:100vh; width:100vw; height:100vh;
  display:grid;
  grid-template-columns:var(--sidebar-w) minmax(0,1fr);
  grid-template-rows:var(--topbar-h) 1fr;
  grid-template-areas:
    "topbar topbar"
    "sidebar content";
  background:var(--ground);
  overflow:hidden;
}

/* === Language switch (topbar) === */
.topbar{ overflow: visible;   z-index: 1000;   overflow: visible;}  /* permite o dropdown sair da barra */

.lang-switch{
  position: relative;
  z-index: 6;
}

.lang-btn{
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 32px;
  padding: 0 10px;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
}
.lang-btn .flag{ font-size: 18px; line-height: 1; }
.lang-btn .lang-code{ font-weight: 600; font-size: .85rem; }
.lang-btn .caret{ width: 12px; height: 12px; opacity: .7; }

.lang-menu{
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  min-width: 180px;
  padding: 6px;
  margin: 0;
  list-style: none;
  background: #fff;
  border: 1px solid rgba(0,0,0,.08);
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0,0,0,.08);
  z-index: 2000;
}

.square-frame{ position: relative; z-index: 0; }


.lang-menu li{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
  white-space: nowrap;
}
.lang-menu li:hover{ background: rgba(0,0,0,.04); }
.lang-menu li.active{
  background: rgba(0,0,0,.06);
  font-weight: 600;
}
.lang-menu .flag{ font-size: 18px; line-height: 1; }
.lang-menu .label{ font-size: .95rem; }

/* =============== TOPBAR =============== */
.topbar{
  grid-area:topbar;
  display:grid;
  grid-template-columns:auto minmax(0,1fr) auto; /* logo | tabs | ações */
  align-items:center; gap:8px;
  background:#0f172a;
  padding:0 8px;
  position:relative;
  overflow:visible;   /* <<< was hidden */
  z-index:1000;       /* acima do conteúdo */
}
.top-left{display:flex;align-items:center;gap:8px;}
.brand{ height:28px; width:auto; max-height:calc(100% - 8px); object-fit:contain; display:block; }
.top-actions { position: relative; z-index: 2; display: inline-flex; align-items: center; gap: 8px; }

.help-btn{
  display:inline-flex; align-items:center; gap:8px;
  height:32px; padding:0 10px;
  border:1px solid rgba(0,0,0,0.08);
  border-radius:8px;
  background:#fff; color:#0f172a;   /* contrasta com topbar escura */
  cursor:pointer;
}
.help-btn .icn{ width:14px; height:14px; }
.help-btn .label{ font-weight:600; font-size:.85rem; }
.help-btn:hover{ background:#f7f7f7; }
/* =============== TABS (NAVEGADOR) =============== */
.topbar .tab-list{
  list-style:none; margin:0; padding:0 12px;
  height:var(--topbar-h);
  display:flex; align-items:flex-end; gap:var(--tab-gap);
  min-width:0; white-space:nowrap; overflow-x:auto; overflow-y:hidden;
}

.topbar .tab-item{
  position:relative; display:inline-flex; align-items:center;
}

/* topo arredondado + base reta, sem “pular” altura */
.topbar .tab-btn{
  display:inline-flex; align-items:center; gap:10px;
  height:var(--tab-h);
  padding:0 var(--tab-pad-x);
  background:var(--tab-inactive-bg);
  color:var(--tab-inactive-fg);
  border: 1px solid transparent !important;

  border-bottom:0; /* base reta (funde com o conteúdo) */
  border-top-left-radius:var(--tab-radius);
  border-top-right-radius:var(--tab-radius);
  border-bottom-left-radius:0;
  border-bottom-right-radius:0;
  cursor:pointer; user-select:none;
  font-size:.82rem; font-weight:700; text-transform:uppercase; letter-spacing:.02em;
  transition:background .15s,color .15s,box-shadow .15s,filter .15s,border-color .15s;
  outline:none; -webkit-tap-highlight-color:transparent;
}

.topbar .tab-btn:hover{ filter:brightness(.97); }

/* ativa = mesma altura, sem “cápsula”, fundida na base */
.topbar .tab-item.active .tab-btn{
  background:var(--tab-active-bg);
  color:var(--tab-active-fg);
  border-color:var(--tab-active-border);
  box-shadow:none;
}

/* “ponte” 1px para cobrir a borda inferior da topbar sob a aba ativa */
.topbar .tab-item.active::after{
  content:"";
  position:absolute; left:1px; right:1px; bottom:-1px; height:1px;
  background:var(--surface);
  z-index:1;
}

.topbar .tab-title{ white-space:nowrap; }

/* X DENTRO da aba (não altera altura) */
.topbar .tab-x{
  margin-left:8px; width:18px; height:18px;
  display:grid; place-items:center;
  border-radius:9px; background:transparent; color:inherit;
  cursor:pointer; transition:background .15s; outline:none;
}
.topbar .tab-x:hover{ background:rgba(0,0,0,.08); }
.topbar .tab-x svg{ width:12px; height:12px; }

/* sem linha/halo no click/focus */
.topbar .tab-btn:focus, .topbar .tab-btn:active,
.topbar .tab-x:focus,  .topbar .tab-x:active{
  outline:none; box-shadow:none;
}

/* =============== SIDEBAR =============== */
/* =============== SIDEBAR (alinhamento dos ícones) =============== */
.sidebar{
  grid-area:sidebar; background:#0f172a; color:#fff;
  display:flex; flex-direction:column; align-items:center;
  padding:12px 8px; gap:12px; border-right:1px solid rgba(0,0,0,.06);
}
.side-icons{
  display:flex; flex-direction:column; gap:8px; margin-top:4px;
  align-items:center;                 /* garante coluna reta */
}

.icon-btn{
  width:52px; height:52px; padding:0; /* caixa fixa */
  border-radius:14px;
  display:grid; place-items:center;   /* centro perfeito */
  color:#cfd9e3;
  background:transparent; border:0; cursor:pointer;
  transition:background .15s,color .15s;
}

/* O <Fa> rende um <svg>; normalize o box do SVG pra não “dançar” */
.icon-btn .fa,
.icon-btn :deep(svg){
  display:block;                      /* tira baseline */
  width:22px; height:22px;            /* tamanho fixo */
  transform:translate(0,0);           /* sem deslocamentos */
  transform-box:fill-box; transform-origin:center;
}

/* estado hover/active sem mudar tamanho do ícone */
.icon-btn:hover{ background:rgba(255,255,255,.08); color:#fff; }
.icon-btn.active{ background:rgba(255,255,255,.16); color:#fff; }

/* se quiser leve destaque no ativo sem mexer no alinhamento, use um halo: */
.icon-btn.active :deep(svg){ filter: drop-shadow(0 0 0 rgba(0,0,0,0)); } /* opcional, neutro */

/* =============== CONTEÚDO =============== */
.content{ grid-area:content; padding:16px; background:var(--ground); min-width:0; min-height:0; }
.canvas{ width:100%; height:100%; }

/* se quiser um container central, descomente e ajuste:
.square-frame{ width:100%; height:100%; background:#fff; border-radius:12px; box-shadow:0 10px 30px rgba(0,0,0,.06); padding:24px; }
*/

/* =============== RESPONSIVO =============== */
@media (max-width:768px){
  .app-shell{ grid-template-columns:64px minmax(0,1fr); }
  .brand{ height:44px; }
  .icon-btn{ width:44px; height:44px; }
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
