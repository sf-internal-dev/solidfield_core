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

import { login } from '../services/api'

const router = useRouter()
const toast = useToast()

const email = ref('')
const password = ref('')
const remember = ref(false)
const loading = ref(false)
const touched = ref({ email: false, password: false })

const emailError = computed(() => {
  if (!touched.value.email) return ''
  if (!email.value) return 'Informe seu e-mail.'
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return re.test(email.value) ? '' : 'E-mail inválido.'
})

const passwordError = computed(() => {
  if (!touched.value.password) return ''
  return password.value ? '' : 'Informe sua senha.'
})

const formValid = computed(() => !emailError.value && !passwordError.value && email.value && password.value)

const submit = async () => {
  touched.value = { email: true, password: true }
  if (!formValid.value || loading.value) return

  loading.value = true
  try {
    const { access_token } = await login(email.value, password.value)
    // Exemplo simples com localStorage (ver nota de segurança abaixo)
    localStorage.setItem('token', access_token)
    if (remember.value) localStorage.setItem('remember', '1')
    toast.add({ severity: 'success', summary: 'Bem-vindo!', detail: 'Login realizado.', life: 2000 })
    router.push({ name: 'dashboard' })
  } catch (err) {
    const detail = err?.response?.data?.detail || 'Credenciais inválidas.'
    toast.add({ severity: 'error', summary: 'Erro ao entrar', detail, life: 4000 })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex align-items-center justify-content-center surface-ground p-3">
    <Toast />
    <Card class="shadow-2 w-full sm:w-9 md:w-6 lg:w-4">
      <template #title>
        <div class="text-center">Entrar</div>
      </template>

      <template #content>
        <div class="flex flex-column gap-3">
          <!-- E-mail -->
          <div class="flex flex-column gap-2">
            <label for="email" class="text-sm">E-mail</label>
            <InputText
              id="email"
              v-model="email"
              class="w-full"
              :invalid="!!emailError"
              @blur="touched.email = true"
              @keyup.enter="submit"
              placeholder="seu@email.com"
              autofocus
            />
            <small v-if="emailError" class="p-error">{{ emailError }}</small>
          </div>

          <!-- Senha -->
          <div class="flex flex-column gap-2">
            <label for="password" class="text-sm">Senha</label>
            <Password
              id="password"
              v-model="password"
              :feedback="false"
              toggleMask
              class="w-full"
              :inputProps="{ class: 'w-full', placeholder: '••••••••', onblur: () => (touched.password = true), onkeyup: (e) => e.key === 'Enter' && submit() }"
              :invalid="!!passwordError"
            />
            <small v-if="passwordError" class="p-error">{{ passwordError }}</small>
          </div>

          <div class="flex align-items-center justify-content-between mt-1">
            <div class="flex align-items-center gap-2">
              <Checkbox inputId="remember" v-model="remember" :binary="true" />
              <label for="remember" class="text-sm">Lembrar</label>
            </div>
            <a class="text-sm cursor-pointer">Esqueci minha senha</a>
          </div>

          <Button
            label="Entrar"
            icon="pi pi-sign-in"
            class="w-full mt-2"
            :loading="loading"
            :disabled="!formValid"
            @click="submit"
          />

          <Divider />
          <div class="text-center text-sm">
            Não tem conta? <a class="cursor-pointer">Criar conta</a>
          </div>
        </div>
      </template>
    </Card>
  </div>
</template>

<style scoped>
/* Ajustes finos se quiser */
</style>
