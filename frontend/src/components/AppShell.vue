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
      <Fa :icon="t.icon || ['fas','house']" class="fa" />
      <span class="tab-title">{{ t.title }}</span>

      <!-- X DENTRO da aba -->
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

/** Ícones da sidebar (apenas um por “seção” de alto nível) */
const sideItems = [
  { key: 'home',      label: 'Home',        icon: ['fas', 'house'] },
  { key: 'orders',    label: 'Work Orders', icon: ['fas', 'clipboard-list'] },
  { key: 'customers', label: 'Customers',   icon: ['fas', 'users'] },
  { key: 'settings',  label: 'Settings',    icon: ['fas', 'gear'] },
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
/* ================= TOKENS ================= */
.app-shell{
  --topbar-h:56px;
  --sidebar-w:80px;

  --surface:#ffffff;        /* fundo da topbar e do conteúdo (para fundir a aba ativa) */
  --ground:#f5f5f5;         /* fundo geral */
  --text:#0f172a;
  --muted:#6b7280;

  --side-bg:#0f172a;

  /* Tabs tipo navegador */
  --tab-h:36px;
  --tab-pad-x:14px;
  --tab-radius:12px;        /* só no topo */
  --tab-gap:10px;

  --tab-inactive-bg:#f1f3f5;
  --tab-inactive-fg:#111827;
  --tab-border:#d8dbe2;

  --tab-active-bg:var(--surface);
  --tab-active-fg:#111827;
  --tab-active-border:#cfd3da;
}

/* ================= GRID BASE ================= */
.app-shell{
  min-height:100vh;
  display:grid;
  grid-template-columns:var(--sidebar-w) 1fr;
  grid-template-rows:var(--topbar-h) 1fr;
  grid-template-areas:
    "topbar topbar"
    "sidebar content";
  background:var(--ground);
overflow: hidden;

}

/* ================= TOPBAR ================= */
.topbar{
  grid-area:topbar;
  display:grid;
  grid-template-columns:auto 1fr auto;  /* logo | tabs | ações */
  align-items:center;
  background:var(--surface);
  gap:8px;
  padding:0 8px;
  position:relative;
  overflow: hidden;
}

.topbar .tab-btn,
.topbar .tab-x {
  outline: none;
  -webkit-tap-highlight-color: transparent; /* mobile */
}

.top-left{display:flex;align-items:center;gap:8px;}
.brand{
  height:28px; width:auto; max-height:calc(100% - 8px);
  object-fit:contain; display:block;
}
.top-actions{padding-right:4px;color:var(--muted);}

/* ================= TABS — ESTILO NAVEGADOR ================= */
/* faixa de abas colada à borda inferior da topbar */
.topbar .tab-list{
  list-style:none; margin:0; padding:0 12px;
  height:var(--topbar-h);
  display:flex; align-items:flex-end; gap:var(--tab-gap);
  overflow:auto;
}

/* cada item envolve o botão + fechar */
.topbar .tab-item{
  position:relative; display:inline-flex; align-items:center;
}

/* botão da aba: topo arredondado, base reta, sem borda inferior */
.topbar .tab-btn{
  display:inline-flex; align-items:center; gap:10px;
  height:var(--tab-h); padding:0 var(--tab-pad-x);
  background:var(--tab-inactive-bg);
  color:var(--tab-inactive-fg);
  border:1px solid var(--tab-border);
  border-bottom:none;                         /* FUNDIR com a “meiota” */
  border-top-left-radius:var(--tab-radius);
  border-top-right-radius:var(--tab-radius);
  border-bottom-left-radius:0;
  border-bottom-right-radius:0;
  cursor:pointer;

  font-size:.82rem; font-weight:700; text-transform:uppercase; letter-spacing:.02em;
  transition:background .15s,color .15s,box-shadow .15s,filter .15s;
}
.topbar .tab-btn:hover{ filter:brightness(.97); }

/* ativa = mesma cor do conteúdo e esconde a borda da topbar por baixo */
.topbar .tab-item.active .tab-btn{
  background:var(--tab-active-bg);
  color:var(--tab-active-fg);
  border-color:var(--tab-active-border);
  z-index:2;
}

/* “ponte” para cobrir a borda inferior da topbar sob a aba ativa (efeito fundido) */
.topbar .tab-item.active::after{
  content:"";
  position:absolute; left:1px; right:1px; bottom:-1px;
  height:1px; background:var(--surface);     /* mesmo fundo do conteúdo */
  z-index:1;
}

.topbar .tab-title{white-space:nowrap;}

/* botão de fechar ao lado da aba */
.topbar .tab-close{
  margin-left:-6px; margin-right:4px;        /* entra um pouco sobre a aba */
  width:20px; height:20px;
  display:grid; place-items:center;
  border:0; background:transparent; color:inherit;
  cursor:pointer; border-radius:10px;
  transition:background .15s;
}
.topbar .tab-close:hover{ background:rgba(0,0,0,.08); }
.topbar .tab-close i, .topbar .tab-close .fa{ font-size:.8rem; line-height:1; }

/* --- Tabs tipo navegador (aba ativa “fundida” com o conteúdo) --- */
.topbar {
  --tab-h: 36px;
  --tab-pad-x: 14px;
  --tab-radius: 12px; /* só no topo */
  --tab-gap: 10px;

  --tab-inactive-bg: #f5f5f5;
  --tab-inactive-fg: #111827;
  --tab-border: #d8dbe2;

  --tab-active-bg:  #FCC800;
  --tab-active-fg: #111827;
  --tab-active-border: #cfd3da;
}

.topbar .tab-list{
  list-style:none; margin:0; padding:0 12px;
  height: var(--topbar-h, 56px);
  display:flex; align-items:flex-end; gap:var(--tab-gap);
  overflow:auto;
}

.topbar .tab-item{ position:relative; display:inline-flex; align-items:center; }

.topbar .tab-btn{
  display:inline-flex; align-items:center; gap:10px;
  height:var(--tab-h); padding:0 var(--tab-pad-x);
  background:var(--tab-inactive-bg);
  color:var(--tab-inactive-fg);
  border:1px solid var(--tab-border);
  border-bottom:none; /* “funde” com o conteúdo */
  border-top-left-radius:var(--tab-radius);
  border-top-right-radius:var(--tab-radius);
  cursor:pointer;

  font-size:.82rem; font-weight:700; text-transform:uppercase; letter-spacing:.02em;
  transition:background .15s, color .15s, box-shadow .15s, filter .15s;
}

.topbar .tab-btn:hover{ filter:brightness(.97); }

.topbar .tab-item.active .tab-btn{
  background:var(--tab-active-bg);
  color:var(--tab-active-fg);
  border-color:var(--tab-active-border);
  z-index:2;
}

/* “ponte” pra cobrir a borda da topbar sob a aba ativa (efeito fundido) */
.topbar .tab-item.active::after{
  content:"";
  position:absolute; left:1px; right:1px; bottom:-1px;
  height:1px; background:var(--surface, #fff);
  z-index:1;
}

.topbar .tab-title{ white-space:nowrap; }

/* --- X DENTRO DA ABA --- */
.topbar .tab-x{
  margin-left: 8px;
  width: 18px; height: 18px;
  display: grid; place-items: center;
  border-radius: 9px;
  color: inherit;                  /* branco/escuro conforme a aba */
  background: transparent;
  cursor: pointer;
  transition: background .15s;
}
.topbar .tab-x i, .topbar .tab-x .fa{ font-size: .8rem; line-height: 1; }

/* ================= SIDEBAR ================= */
.sidebar{
  grid-area:sidebar;
  background:var(--side-bg); color:#fff;
  display:flex; flex-direction:column; align-items:center;
  padding:12px 8px; gap:12px; border-right:1px solid rgba(0,0,0,.06);
}
.side-icons{display:flex;flex-direction:column;gap:8px;margin-top:4px;}

.icon-btn{
  width:52px;height:52px;border-radius:14px;
  display:grid;place-items:center;
  color:#cfd9e3;background:transparent;border:0;cursor:pointer;
  transition:background .15s,color .15s,transform .12s;
}
.icon-btn .fa{font-size:1.25rem;}
.icon-btn:hover{background:rgba(255,255,255,.08);color:#fff;}
.icon-btn.active{background:rgba(255,255,255,.16);color:#fff;}
.icon-btn.active .fa{font-size:1.3rem;}

/* ================= CONTEÚDO ================= */
.content{ grid-area:content; padding:16px; background:var(--ground); }
.canvas{ width:100%; height:100%; }

/* seu conteúdo pode ser livre; se quiser um “card” central:
.square-frame{ background:#fff; border-radius:16px; box-shadow:0 10px 30px rgba(0,0,0,.06); padding:24px; }
*/

/* ================= RESPONSIVO ================= */
@media (max-width:768px){
  .app-shell{ grid-template-columns:64px 1fr; }
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
