import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'

const routes = [
  { path: '/', redirect: { name: 'dashboard' } },
  { name: 'login', path: '/login', component: LoginView },
  { name: 'dashboard', path: '/dashboard', component: DashboardView, meta: { requiresAuth: true } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, _from, next) => {
  const isAuth = !!localStorage.getItem('token') 
  if (to.meta.requiresAuth && !isAuth) return next({ name: 'login' })
  if (to.name === 'login' && isAuth) return next({ name: 'dashboard' })
  next()
})

export default router
