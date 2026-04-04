# Vue 3 + Ionic + Capacitor — offline (outbox) + fila SolidField

Complementa **`CLIENT_OFFLINE_LOCAL_SYNC_ESQUEMA.md`** (estados e contrato) e **`OFFLINE_SYNC_QUEUE.md`** (APIs Django).

---

## 1. Dependências sugeridas

| Pacote | Uso |
|--------|-----|
| `@capacitor/network` | `Network.addListener('networkStatusChange', …)` e `Network.getStatus()` antes do sync |
| `@capacitor/app` | `App.addListener('resume', …)` para sync ao voltar do background |
| SQLite Capacitor | Ex.: **@capawesome-team/capacitor-sqlite** (bom suporte a Vue/Ionic) ou **@capacitor-community/sqlite** — uma tabela `pending_mutations` |
| `axios` ou `ofetch` | Cliente HTTP com `baseURL` da API SolidField |
| **Pinia** (opcional mas recomendado) | Contador de pendentes, último erro de sync, fila “visível” na UI |

---

## 2. Estrutura de pastas (no app Ionic, não no Django)

```text
src/
  db/
    schema.ts              -- tipos + SQL CREATE TABLE
    mutation-repository.ts -- insert/list/update por status
  services/
    api-client.ts          -- axios instance + interceptors (token / tenant)
    solidfield-sync.ts     -- enqueue(), process(), listRemoteQueue() opcional
    sync-worker.ts         -- syncPending(): orquestra repo + API + Network
  composables/
    useOfflineSync.ts      -- expõe runSync(), pendingCount, isOnline
  views/...
```

Mantenha **`payload`** e **`client_mutation_id`** como no esquema genérico; o `mutation-repository` só persiste JSON.

---

## 3. Fluxo no Ionic + Vue

1. **Tela de checklist (offline OK):** ao salvar turno → `mutationRepository.insert({ client_mutation_id: crypto.randomUUID(), status: 'local_only', payload })`.
2. **`useOfflineSync` / `sync-worker`:**  
   - Chamar **`runSync()`** quando: `networkStatusChange` → connected, `App` resume, e no **`onIonViewWillEnter`** da home / dashboard operacional.
3. **`runSync()`:** para cada linha `local_only` | `enqueued` | `needs_retry` (ver esquema):  
   - sem `server_queue_id` → `POST enqueue_offline_sync_api`  
   - com `server_queue_id` → `POST process_offline_sync_api/<id>/`  
4. **UI:** badge “N pendentes” a partir de `SELECT COUNT(*) WHERE status != 'synced'` (ou Pinia atualizado após cada passo).

Use **debounce** (ex. 2–5 s) após evento de rede para evitar rajadas com Wi‑Fi oscilante.

---

## 4. Exemplo mínimo de composable (ideia, não copiar como única fonte)

```ts
// composables/useOfflineSync.ts — esqueleto
import { ref, onMounted, onUnmounted } from 'vue'
import { Network } from '@capacitor/network'
import { App } from '@capacitor/app'
import { runSync } from '@/services/sync-worker'

export function useOfflineSync() {
  const isOnline = ref(true)
  let removeNet: (() => void) | undefined
  let removeResume: (() => void) | undefined

  onMounted(async () => {
    const s = await Network.getStatus()
    isOnline.value = s.connected
    const h = await Network.addListener('networkStatusChange', (e) => {
      isOnline.value = e.connected
      if (e.connected) void runSync()
    })
    removeNet = () => h.remove()
    const r = await App.addListener('resume', () => void runSync())
    removeResume = () => r.remove()
  })

  onUnmounted(() => {
    removeNet?.()
    removeResume?.()
  })

  return { isOnline, forceSync: runSync }
}
```

---

## 5. Integração com rotas Ionic

- Em **`/operacoes`** ou home pós-login: `onIonViewWillEnter(() => runSync())`.
- Opcional: **toast** só em falha persistente (`needs_retry` + `last_error_codes`), não a cada retry.

---

## 6. Autenticação

O mesmo `Authorization` / cookie / header que o Django já exige para `technician_operating` deve ir no **`api-client`**. Sem sessão válida, `enqueue`/`process` retornam 401/422 — tratar como “sync bloqueado” e manter mutações em `local_only`.

---

## 7. Resumo

| Camada | Vue + Ionic + Capacitor |
|--------|-------------------------|
| Persistência | SQLite + repositório |
| Rede | `@capacitor/network` + `@capacitor/app` |
| Orquestração | `sync-worker.ts` + composable |
| Estado global | Pinia (opcional) |
| Servidor | `enqueue` → `process` (SolidField) |

O Django permanece só como **API**; toda a lógica “sem rede” é **neste app**.
