// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import LoginView from '@/views/LoginView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    // rota SEM shell
    { path: '/login', name: 'login', component: LoginView, meta: { layout: 'blank' } },

    // rotas COM shell (AppShell é o layout pai)
    {
      path: '/',
      component: AppShell,
      meta: { requiresAuth: true },
      children: [
        { path: '', name: 'home', component: () => import('@/views/HomeView.vue') },
        { path: 'orders', name: 'orders', component: () => import('@/views/OrdersView.vue') },
        { path: 'customers', name: 'customers', component: () => import('@/views/CustomersView.vue') },
        { path: 'settings', name: 'settings', component: () => import('@/views/SettingsView.vue') },
      ],
    },

    // fallback
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
})

export default router
