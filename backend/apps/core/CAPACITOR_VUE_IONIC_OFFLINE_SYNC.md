# Vue 3 + Ionic + Capacitor — offline (outbox) + SolidField queue

Complements **`CLIENT_OFFLINE_LOCAL_SYNC_SCHEMA.md`** (states and contract) and **`OFFLINE_SYNC_QUEUE.md`** (Django APIs).

---

## 1. Suggested dependencies

| Package | Use |
|---------|-----|
| `@capacitor/network` | `Network.addListener('networkStatusChange', …)` and `Network.getStatus()` before sync |
| `@capacitor/app` | `App.addListener('resume', …)` to sync when returning from the background |
| Capacitor SQLite | For example **@capawesome-team/capacitor-sqlite** (good Vue/Ionic support) or **@capacitor-community/sqlite** — one `pending_mutations` table |
| `axios` or `ofetch` | HTTP client with the SolidField API `baseURL` |
| **Pinia** (optional but recommended) | Pending counter, last sync error, queue “visible” in the UI |

---

## 2. Folder layout (in the Ionic app, not in Django)

```text
src/
  db/
    schema.ts              -- types + SQL CREATE TABLE
    mutation-repository.ts -- insert/list/update by status
  services/
    api-client.ts          -- axios instance + interceptors (token / tenant)
    solidfield-sync.ts     -- enqueue(), process(), listRemoteQueue() optional
    sync-worker.ts         -- syncPending(): orchestrates repo + API + Network
  composables/
    useOfflineSync.ts      -- exposes runSync(), pendingCount, isOnline
  views/...
```

Keep **`payload`** and **`client_mutation_id`** as in the generic schema; `mutation-repository` only persists JSON.

---

## 3. Flow in Ionic + Vue

1. **Checklist screen (offline OK):** on shift save → `mutationRepository.insert({ client_mutation_id: crypto.randomUUID(), status: 'local_only', payload })`.
2. **`useOfflineSync` / `sync-worker`:**
   - Call **`runSync()`** when: `networkStatusChange` → connected, `App` resume, and on **`onIonViewWillEnter`** of the home / operations dashboard.
3. **`runSync()`:** for each row in `local_only` | `enqueued` | `needs_retry` (see the schema):
   - no `server_queue_id` → `POST enqueue_offline_sync_api`
   - with `server_queue_id` → `POST process_offline_sync_api/<id>/`
4. **UI:** an “N pending” badge from `SELECT COUNT(*) WHERE status != 'synced'` (or Pinia updated after each step).

Use **debounce** (for example 2–5 s) after a network event to avoid bursts on flaky Wi‑Fi.

---

## 4. Minimal composable example (a sketch, not the only source of truth)

```ts
// composables/useOfflineSync.ts — skeleton
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

## 5. Integration with Ionic routes

- On **`/operations`** or the post-login home: `onIonViewWillEnter(() => runSync())`.
- Optional: a **toast** only on persistent failure (`needs_retry` + `last_error_codes`), not on every retry.

---

## 6. Authentication

The same `Authorization` / cookie / header that Django already requires for `technician_operating` must go on the **`api-client`**. Without a valid session, `enqueue`/`process` return 401/422 — treat that as “sync blocked” and keep mutations in `local_only`.

---

## 7. Summary

| Layer | Vue + Ionic + Capacitor |
|-------|-------------------------|
| Persistence | SQLite + repository |
| Network | `@capacitor/network` + `@capacitor/app` |
| Orchestration | `sync-worker.ts` + composable |
| Global state | Pinia (optional) |
| Server | `enqueue` → `process` (SolidField) |

Django stays an **API** only; all “offline” logic lives **in this app**.
