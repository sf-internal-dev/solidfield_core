<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import Divider from 'primevue/divider'
import Toast from 'primevue/toast'
import { useToast } from 'primevue/usetoast'
import Message from 'primevue/message'



/* mostra o banner se alguém tocou em um campo e ainda há erro */
const showBanner = computed(() =>
  (touched.value.username || touched.value.password) && !formValid.value
)

/* texto do banner (agrega os erros visíveis no momento) */
const bannerText = computed(() => {
  const msgs = []
  if (touched.value.username && usernameError.value) msgs.push('Set your Technician Username. ')
  if (touched.value.password && passwordError.value) msgs.push('Set your Password.')
  return msgs.join(' ')
})

// se usa login por username:
import { login } from '../services/api'

const router = useRouter()
const toast = useToast()

const username = ref('')
const password = ref('')
const remember = ref(false)
const loading = ref(false)
const touched = ref({ username: false, password: false })
const submitted = ref(false)

const usernameError = computed(() => (username.value ? '' : 'Set your Technician Username. '))
const passwordError = computed(() => (password.value ? '' : 'Set your Password. '))
const formValid = computed(() => !usernameError.value && !passwordError.value)

const submit = async () => {
  submitted.value = true
  touched.value = { username: true, password: true }
  if (!formValid.value || loading.value) return
  loading.value = true
  try {
    const { access_token } = await login(username.value, password.value)
    localStorage.setItem('token', access_token)
    if (remember.value) localStorage.setItem('remember', '1')
    toast.add({ severity: 'success', summary: 'Bem-vindo!', life: 1500 })
    router.push({ name: 'dashboard' })
  } catch (err) {
    const detail = err?.response?.data?.detail || 'Credenciais inválidas.'
    toast.add({ severity: 'error', summary: 'Erro ao entrar', detail, life: 3000 })
  } finally {
    loading.value = false
  }
}

const onSubmit = (e) => {
  e.preventDefault()
  submit()
}
</script>

<template>

  <div class="auth-shell">
    <div class="flex flex-column align-items-center justify-content-center gap-4 p-3 w-full">
      <!-- Logo (coloque em /public/solidfield_logo.svg) -->
      <img src="/solidfield_logo.svg" alt="SolidField" class="logo-auth w-auto h-4rem md:h-4rem" />

      <Toast />

      <!-- Card largo/responsivo -->
      <Card class="auth-card shadow-2 w-11/12 sm:w-40rem md:w-48rem lg:w-56rem">
  <template #title>
    <div class="text-center text-2xl font-semibold">Access Workspace</div>
  </template>

  <template #content>
    <!-- Banner aparece assim que usuário começa a digitar e faltar algo -->
    <div class="form-alert">
      <Message v-show="showBanner" severity="warn" :closable="false" class="w-full">
        {{ bannerText || 'Please fill the required fields.' }}
      </Message>
    </div>

    <form class="flex flex-column gap-4" @submit="onSubmit" novalidate>
      <!-- Username -->
      <div class="flex flex-column gap-2">
        <label for="username" class="text-sm font-medium">Technician</label>
        <InputText
          id="username"
          v-model="username"
          class="w-full ctl-input"
          :invalid="touched.username && !!usernameError"
          @input="touched.username = true"   
          @blur="touched.username = true"
          placeholder="your_technician_username"
          autocomplete="username"
          autofocus
        />
      </div>

      <!-- Password -->
      <div class="flex flex-column gap-2">
        <label for="password" class="text-sm font-medium">Password</label>
        <Password
          inputId="password"
          v-model="password"
          :feedback="false"
          toggleMask
          class="w-full"
          :invalid="touched.password && !!passwordError"
          :inputProps="{
            class: 'w-full ctl-input',
            placeholder: '••••••••',
            autocomplete: 'current-password',
            oninput: () => (touched.password = true),   // idem aqui
            onblur: () => (touched.password = true)
          }"
        />
      </div>

      <Button
        type="submit"
        label="Unlock"
        icon="pi pi-unlock"
        class="w-full ctl-btn custom-login-btn"
        :loading="loading"
        :disabled="!formValid"
      />
    </form>
    <div class="text-center text-sm support-line">
      Having trouble with technician access?
      <a class="support-link" href="mailto:support@solidfield.com">
        Contact your administrator
      </a>.
    </div>
  </template>
  
</Card>

    </div>
  </div>
</template>

<style scoped>
/* =========  PALETA (cores da tua logo)  ========= */
:global(:root) {
  --p-inputtext-background: #FCC800
  --primary-color: #FCC800;          /* amarelo principal */
  --primary-hover-color: #E0B200;    /* hover do botão */
  --primary-color-text: #0D1F2E;     /* texto sobre botão primário */

  --secondary-color: #0D1F2E;        /* fundo escuro */
  --secondary-hover-color: #1B3346;

  --surface-ground: #0D1F2E;         /* fundo geral (override) */
  --surface-card: #ffffff;           /* cards */
  --text-color: #111827;
  --text-color-secondary: #6B7280;
  --focus-ring-color: #FCC800;       /* foco inputs */
}

/* =========  LAYOUT  ========= */
:global(html, body, #app) { height: 100%; margin: 0; padding: 0; }

.auth-shell {
  min-height: 100vh;
  width: 100vw;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
}

:deep(.p-inputtext:hover) {
  border-color: #E0B200 !important;
}
:deep(.p-inputtext:focus) {
  border-color: #FCC800 !important;
  box-shadow: 0 0 0 3px rgba(252,200,0,.28) !important;
}

/* Garantia extra pro Password (algumas versões usam .p-password-input) */
:deep(.p-password .p-inputtext:hover),
:deep(.p-password .p-password-input:hover) {
  border-color: #E0B200 !important;
}
:deep(.p-password .p-inputtext:focus),
:deep(.p-password .p-password-input:focus) {
  border-color: #FCC800 !important;
  box-shadow: 0 0 0 3px rgba(252,200,0,.28) !important;
}


.auth-card {
  background: var(--surface-card);
  border-radius: 12px;
}

/* =========  FORM SCALE  ========= */


/* foco/hover nos inputs com a primária */
:global(.p-inputtext:focus),
:global(.p-password-input:focus) {
  box-shadow: 0 0 0 2px rgba(252, 200, 0, 0.25);
  border-color: var(--focus-ring-color);
}
:global(.p-inputtext:hover),
:global(.p-password-input:hover) {
  border-color: var(--primary-color);
}

/* =========  BOTÃO PRIMÁRIO (amarelo)  ========= */
.custom-login-btn {
  height: 3rem;
  border-radius: 12px;
  background-color: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
  color: var(--primary-color-text) !important;
}
.custom-login-btn:hover {
  background-color: var(--primary-hover-color) !important;
  border-color: var(--primary-hover-color) !important;
}

/* borda/hover/foco nos inputs */
.p-inputtext:hover,
.p-password .p-inputtext:hover {
  border-color: #E0B200 !important;     /* hover amarelo */
}

.p-inputtext:focus,
.p-password .p-inputtext:focus {
  border-color: #FCC800 !important;     /* foco amarelo */
  box-shadow: 0 0 0 3px rgba(252,200,0,.28) !important;
}


/* links discretos sobre fundo claro */
.link-muted { color: var(--text-color-secondary); }
.link-muted:hover { color: var(--text-color); }

.support-line {
  margin-top: .9rem;
  color: var(--text-color-secondary);
}
.support-link {
  color: var(--text-color);
  text-decoration: underline;
}
.support-link:hover {
  color: var(--primary-hover-color);
  text-decoration: underline;
}

/* logo menor em mobile */
.logo-auth { display: block; }
</style>
