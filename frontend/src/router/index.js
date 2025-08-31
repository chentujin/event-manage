import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/utils/auth'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/',
    component: () => import('@/components/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue')
      },
      {
        path: '/incidents',
        name: 'Incidents',
        component: () => import('@/views/Incidents.vue')
      },
      {
        path: '/alerts',
        name: 'Alerts',
        component: () => import('@/views/Alerts.vue')
      },
      {
        path: '/incidents-new',
        name: 'IncidentsNew',
        component: () => import('@/views/IncidentsNew.vue')
      },
      {
        path: '/postmortems',
        name: 'PostMortems',
        component: () => import('@/views/PostMortems.vue')
      },
      {
        path: '/problems',
        name: 'Problems',
        component: () => import('@/views/Problems.vue')
      },
      {
        path: '/services',
        name: 'Services',
        component: () => import('@/views/Services.vue')
      },
      {
        path: '/approvals',
        name: 'Approvals',
        component: () => import('@/views/Approvals.vue')
      },
      {
        path: '/users',
        name: 'Users',
        component: () => import('@/views/Users.vue')
      },
      {
        path: '/notifications',
        name: 'Notifications',
        component: () => import('@/views/Notifications.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = getToken()
  
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if (to.meta.requiresGuest && token) {
    next('/')
  } else {
    next()
  }
})

export default router