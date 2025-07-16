import { createApp } from 'vue'
import './style.css'
import PrimeVue from 'primevue/config'
import { createPinia } from 'pinia'
import App from './App.vue'
import Aura from '@primeuix/themes/aura'
import Button from 'primevue/button'

const pinia = createPinia()
const app = createApp(App)

app.use(PrimeVue, {
  theme: {
    preset: Aura
  }
})

app.component('Button', Button)
app.use(pinia)
app.mount('#app') // ← só monta por último
