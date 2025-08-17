import { createApp } from 'vue'
import './style.css'
import PrimeVue from 'primevue/config'
import { createPinia } from 'pinia'
import App from './App.vue'
import Aura from '@primeuix/themes/aura'
import router from './router'
import ToastService from 'primevue/toastservice'
import 'primeicons/primeicons.css'
import 'primeflex/primeflex.css'
// import 'primevue/resources/themes/lara-light-blue/theme.css'
import './assets/base.css'
import '@fontsource-variable/inter';
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import { library } from '@fortawesome/fontawesome-svg-core'
import { faGripVertical, faXmark, faHouse, faClipboardList, faUsers, faGear } from '@fortawesome/free-solid-svg-icons'

// importe só o que for usar (solid = “mais gordo”)
// adiciona à lib

const pinia = createPinia()
const app = createApp(App)

app.use(PrimeVue, {
  theme: {
    preset: Aura
  }
})
library.add(faGripVertical, faXmark, faHouse, faClipboardList, faUsers, faGear)

app.component('Fa', FontAwesomeIcon) // você usará <Fa />

app.use(router)
app.use(pinia)
app.use(ToastService)
app.mount('#app') // ← só monta por último