<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Button from 'primevue/button'
import SelectButton from 'primevue/selectbutton'
import Toast from 'primevue/toast'
import Message from 'primevue/message'
import { useToast } from 'primevue/usetoast'

import { login } from '../services/api' // mantém seu serviço

const router = useRouter()
const toast = useToast()

/** ====== Steps ====== */
const step = ref<'company' | 'auth'>('company')
const goingForward = ref(true) // controla a direção da animação

const transitionName = computed(() => (goingForward.value ? 'slide-left' : 'slide-right'))

/** ====== Step 1: Company Identifier ====== */
const identifierTypeOptions = [
  { label: 'Workspace Handle', value: 'name' },
  { label: 'Company Email', value: 'email' },
]
const identifierType = ref<'name' | 'email'>('name')
const identifier = ref('')
const touchedCompany = ref(false)

const companyError = computed(() => {
  if (!touchedCompany.value) return ''
  if (!identifier.value) return identifierType.value === 'email'
    ? 'Enter the company email.'
    : 'Enter the workspace handle.'
  if (identifierType.value === 'email') {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!re.test(identifier.value)) return 'Enter a valid email.'
  } else {
    if (identifier.value.trim().length < 2) return 'Workspace Handle is too short.'
  }
  return ''
})

/** (Opcional) resolve tenant/empresa aqui
async function resolveCompany() { ... }
*/

/** ====== Step 2: Auth (Technician) ====== */
const username = ref('')
const password = ref('')
const remember = ref(false)
const loading = ref(false)
const touchedAuth = ref({ username: false, password: false })

const usernameError = computed(() => (touchedAuth.value.username && !username.value ? 'Provide your username.' : ''))
const passwordError = computed(() => (touchedAuth.value.password && !password.value ? 'Provide your password.' : ''))
const formValid = computed(() => !!username.value && !!password.value)

/** ====== Banner (sem deformar card) ====== */
const showBanner = computed(() => {
  if (step.value === 'company') return touchedCompany.value && !!companyError.value
  return (touchedAuth.value.username || touchedAuth.value.password) && !formValid.value
})
const bannerText = computed(() => {
  if (step.value === 'company') return companyError.value || 'Please fill the required field.'
  const msgs: string[] = []
  if (touchedAuth.value.username && !username.value) msgs.push('Username is required.')
  if (touchedAuth.value.password && !password.value) msgs.push('Password is required.')
  return msgs.join(' ')
})

/** ====== Handlers ====== */
const goCompanyNext = async () => {
  touchedCompany.value = true
  if (companyError.value) return
  goingForward.value = true
  // await resolveCompany() // se precisar
  step.value = 'auth'
}

const goBackToCompany = () => {
  goingForward.value = false
  step.value = 'company'
}

const onSubmitCompany = (e: Event) => {
  e.preventDefault()
  goCompanyNext()
}

const onSubmitAuth = async (e: Event) => {
  e.preventDefault()
  touchedAuth.value = { username: true, password: true }
  if (!formValid.value || loading.value) return
  loading.value = true
  try {
    const { access_token } = await login(username.value, password.value)
    localStorage.setItem('token', access_token)
    if (remember.value) localStorage.setItem('remember', '1')
    toast.add({ severity: 'success', summary: 'Welcome!', life: 1400 })
    router.push({ name: 'dashboard' })
  } catch (err: any) {
    const detail = err?.response?.data?.detail || 'Invalid credentials.'
    toast.add({ severity: 'error', summary: 'Sign-in failed', detail, life: 3000 })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-shell">
    <div class="flex flex-column align-items-center justify-content-center gap-4 p-3 w-full">
      <img src="/solidfield_logo.svg" alt="SolidField" class="logo-auth w-auto h-4rem md:h-5rem" />
      <Toast />

      <Card class="auth-card shadow-2 w-11/12 sm:w-40rem md:w-48rem lg:w-56rem">
        <template #title>
          <div class="text-center text-2xl font-semibold">
            {{ step === 'company' ? 'Identify Your Company' : 'Access Workspace' }}
          </div>
        </template>

        <template #content>
          <!-- Banner compacto no topo (sem deformar) -->
          <div class="form-alert">
            <Message v-show="showBanner" severity="warn" :closable="false" class="w-full">
              {{ bannerText || 'Please check the highlighted fields.' }}
            </Message>
          </div>

          <!-- Transição entre passos -->
          <Transition :name="transitionName" mode="out-in">
            <!-- ===== Step 1: Company ===== -->
            <form
              v-if="step === 'company'"
              key="company"
              class="flex flex-column gap-4"
              @submit="onSubmitCompany"
              novalidate
            >
              <div class="flex flex-column gap-2 align-items-center">
                <label class="text-sm font-medium text-center">Choose an identifier</label>
                <SelectButton
                  v-model="identifierType"
                  :options="identifierTypeOptions"
                  optionLabel="label"
                  optionValue="value"
                />
              </div>

              <div class="step-inner flex flex-column gap-4">
              <div class="flex flex-column gap-2">
                <label for="identifier" class="text-sm font-medium">
                  {{ identifierType === 'email' ? 'Company Email' : 'Workspace Handle' }}
                </label>
                <InputText
                  id="identifier"
                  v-model="identifier"
                  class="w-full ctl-input"
                  :invalid="!!companyError"
                  :placeholder="identifierType === 'email' ? 'acme@company.com' : 'Acme Corp'"
                  @input="touchedCompany = true"
                  @blur="touchedCompany = true"
                  autocomplete="organization"
                />
              </div>
              


              <div class="flex gap-2 justify-content-end">
                <Button
                  type="submit"
                  label="Continue"
                  icon="pi pi-arrow-right"
                  iconPos="right"
                  class="custom-login-btn"
                />
              </div>

              <!-- linha de suporte -->
              <div class="text-center text-sm support-line">
                Having trouble with technician access?
                <a class="support-link" href="mailto:support@solidfield.com">Contact your administrator</a>.
              </div>
              </div>
            </form>

            <!-- ===== Step 2: Auth ===== -->
            <form
              v-else
              key="auth"
              class="flex flex-column gap-4"
              @submit="onSubmitAuth"
              novalidate
            >
              <div class="flex justify-content-between align-items-center">
                <Button
                  type="button"
                  label="Change company"
                  icon="pi pi-arrow-left"
                  class="p-button-text"
                  @click="goBackToCompany"
                />
              </div>

              <div class="flex flex-column gap-2">
                <label for="username" class="text-sm font-medium">Technician</label>
                <InputText
                  id="username"
                  v-model="username"
                  class="w-full ctl-input"
                  :invalid="touchedAuth.username && !!usernameError"
                  @input="touchedAuth.username = true"
                  @blur="touchedAuth.username = true"
                  placeholder="your_technician_username"
                  autocomplete="username"
                  autofocus
                />
              </div>

              <div class="flex flex-column gap-2">
                <label for="password" class="text-sm font-medium">Password</label>
                <Password
                  inputId="password"
                  v-model="password"
                  :feedback="false"
                  toggleMask
                  class="w-full"
                  :invalid="touchedAuth.password && !!passwordError"
                  :inputProps="{
                    class: 'w-full ctl-input',
                    placeholder: '••••••••',
                    autocomplete: 'current-password',
                    oninput: () => (touchedAuth.password = true),
                    onblur: () => (touchedAuth.password = true)
                  }"
                />
              </div>

              <div class="flex align-items-center justify-content-between">
                <div class="flex align-items-center gap-2">
                  <Checkbox inputId="remember" v-model="remember" :binary="true" />
                  <label for="remember" class="text-sm">Remember me</label>
                </div>
                <a class="text-sm cursor-pointer link-muted">Forgot password?</a>
              </div>

              <Button
                type="submit"
                label="Unlock"
                icon="pi pi-unlock"
                class="w-full ctl-btn custom-login-btn"
                :loading="loading"
                :disabled="!formValid"
              />

              <!-- linha de suporte -->
              <div class="text-center text-sm support-line">
                Having trouble with technician access?
                <a class="support-link" href="mailto:support@solidfield.com">Contact your administrator</a>.
              </div>
            </form>
          </Transition>
        </template>
      </Card>
    </div>
  </div>
</template>

<style scoped>
/* ===== layout base (mantém seu design) ===== */
:global(html, body, #app) { height: 100%; margin: 0; padding: 0; }

.auth-shell {
  min-height: 100vh; width: 100vw;
  display: flex; align-items: center; justify-content: center;
  background:#f5f5f5;
}

.auth-card { background: var(--surface-card, #fff); border-radius: 12px; }

/* reserva altura pro banner sem “pular” */
.form-alert { min-height: 2.25rem; }

/* ===== inputs (mantém tua escala e bordas custom) ===== */
:deep(.ctl-input) {
  font-size: 1.05rem;
  height: 3rem;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  border: 2px solid #c7cad1;
  transition: border-color .15s ease, box-shadow .15s ease;
  outline: none;
}
:deep(.ctl-input:hover) {
  border-color: var(--primary-hover-color, #E0B200) !important;
}
:deep(.ctl-input:focus) {
  border-color: var(--focus-ring-color, #FCC800) !important;
  box-shadow: 0 0 0 3px rgba(252,200,0,.28) !important;
}
:deep(.ctl-input.p-invalid) {
  border-color: #DC2626 !important;
  box-shadow: 0 0 0 2px rgba(220,38,38,.18) !important;
}

/* ===== botão primário (amarelo) ===== */
.custom-login-btn {
  height: 3rem;
  border-radius: 12px;
  background-color: var(--primary-color, #FCC800) !important;
  border-color: var(--primary-color, #FCC800) !important;
  color: var(--primary-color-text, #0D1F2E) !important;
}
.custom-login-btn:hover {
  background-color: var(--primary-hover-color, #E0B200) !important;
  border-color: var(--primary-hover-color, #E0B200) !important;
}

/* suporte */
.support-line { margin-top: .25rem; color: var(--text-color-secondary, #6B7280); }
.support-link { color: var(--text-color, #111827); text-decoration: underline; }
.support-link:hover { color: var(--primary-hover-color, #E0B200); }

/* animações entre steps */
.slide-left-enter-active, .slide-left-leave-active,
.slide-right-enter-active, .slide-right-leave-active { transition: all .22s ease; }
.slide-left-enter-from { opacity: 0; transform: translateX(16px); }
.slide-left-leave-to   { opacity: 0; transform: translateX(-16px); }
.slide-right-enter-from{ opacity: 0; transform: translateX(-16px); }
.slide-right-leave-to  { opacity: 0; transform: translateX(16px); }


/* logo */
.logo-auth { display: block; }
</style>
