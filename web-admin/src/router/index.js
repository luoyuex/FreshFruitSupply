import { createRouter, createWebHashHistory } from 'vue-router'
import store from '../store'
import AdminLayout from '../layouts/AdminLayout.vue'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: AdminLayout,
    children: [
      { path: '', redirect: '/orders' },
      { path: 'orders', name: 'orders', component: () => import('../views/OrdersView.vue'), meta: { perm: 'orders', title: '订单管理' } },
      { path: 'stats', name: 'stats', component: () => import('../views/StatsView.vue'), meta: { perm: 'stats', title: '销售统计' } },
      { path: 'verifications', name: 'verifications', component: () => import('../views/VerificationsView.vue'), meta: { perm: 'verifications', title: '认证管理' } },
      { path: 'fruits', name: 'fruits', component: () => import('../views/FruitsView.vue'), meta: { perm: 'fruits', title: '水果报价' } },
      { path: 'coupons', name: 'coupons', component: () => import('../views/CouponsView.vue'), meta: { perm: 'coupons', title: '卡券管理' } },
      { path: 'users', name: 'users', component: () => import('../views/UsersView.vue'), meta: { perm: 'users', title: '用户管理' } },
      { path: 'settings', name: 'settings', component: () => import('../views/SettingsView.vue'), meta: { perm: 'settings', title: '系统设置' } },
      { path: 'announcements', name: 'announcements', component: () => import('../views/AnnouncementsView.vue'), meta: { perm: 'settings', title: '公告管理' } },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/orders' },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (!store.state.ready) await store.dispatch('restore')
  if (to.meta.public) {
    return to.name === 'login' && store.getters.isLoggedIn ? { name: 'orders' } : true
  }
  if (!store.getters.isLoggedIn) return { name: 'login', query: { redirect: to.fullPath } }
  if (to.meta.perm && !store.getters.can(to.meta.perm)) return { name: 'orders' }
  return true
})

export default router
