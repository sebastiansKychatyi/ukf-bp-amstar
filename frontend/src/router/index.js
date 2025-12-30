/**
 * Vue Router Configuration
 */

import { createRouter, createWebHistory } from 'vue-router'
import DefaultLayout from '@/layouts/DefaultLayout.vue'

const routes = [
  {
    path: '/',
    component: DefaultLayout,
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: 'Dashboard' },
      },
      {
        path: 'players',
        name: 'Players',
        component: () => import('@/views/PlayerDashboard.vue'),
        meta: { title: 'Players' },
      },
      {
        path: 'teams',
        name: 'Teams',
        component: () => import('@/views/TeamList.vue'),
        meta: { title: 'Teams' },
      },
      {
        path: 'teams/create',
        name: 'TeamCreate',
        component: () => import('@/views/TeamCreate.vue'),
        meta: { title: 'Create Team', requiresAuth: true },
      },
      {
        path: 'teams/:id',
        name: 'TeamDetail',
        component: () => import('@/views/TeamDetail.vue'),
        meta: { title: 'Team Details' },
      },
      {
        path: 'battles',
        name: 'Battles',
        component: () => import('@/views/BattleSystem.vue'),
        meta: { title: 'Battle System' },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: 'Profile', requiresAuth: true },
      },
      {
        path: 'my-team',
        name: 'MyTeam',
        component: () => import('@/views/MyTeam.vue'),
        meta: { title: 'My Team', requiresAuth: true },
      },
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: 'Settings', requiresAuth: true },
      },
    ],
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: 'Login', guest: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: 'Register', guest: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '404 - Not Found' },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  },
})

// Navigation guards
router.beforeEach((to, from, next) => {
  // Set page title
  document.title = to.meta.title ? `${to.meta.title} - AmStar` : 'AmStar Football Platform'

  // Authentication check
  const isAuthenticated = !!localStorage.getItem('access_token')

  if (to.meta.requiresAuth && !isAuthenticated) {
    // Redirect to login if not authenticated
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.meta.guest && isAuthenticated) {
    // Redirect to home if already authenticated
    next({ name: 'Home' })
  } else {
    next()
  }
})

export default router
