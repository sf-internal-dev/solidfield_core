import { createApp } from 'vue'
import './style.css'
import PrimeVue from 'primevue/config'
import { createPinia } from 'pinia'
import App from './App.vue'
import Aura from '@primeuix/themes/aura'
import router from './router'
import ToastService from 'primevue/toastservice'
import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css'
import 'primeflex/primeflex.css'
// import 'primevue/resources/themes/lara-light-blue/theme.css'


const pinia = createPinia()
const app = createApp(App)

app.use(PrimeVue, {
  theme: {
    preset: Aura
  }
})

app.use(router)
app.use(pinia)
app.use(ToastService)
app.mount('#app') // ← só monta por último




createApp(App)
  .use(router)
  .use(PrimeVue)
  .use(ToastService)
  .mount('#app')