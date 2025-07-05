import { createRouter, createWebHistory } from 'vue-router'
import MainPage from '../views/MainPage.vue'
import Home from '../views/Home.vue'
import Spells from '../views/Spells.vue'
import ClassSpells from '../views/ClassSpells.vue'

// OAuth authentication components (lazy loaded)
const AuthCallback = () => import('../views/AuthCallback.vue')
const Profile = () => import('../views/Profile.vue')

// Admin components - import directly for debugging
import AdminDashboard from '../views/AdminDashboard.vue'
import AdminDashboardTest from '../views/AdminDashboardTest.vue'
import AdminUsers from '../views/AdminUsers.vue'
import AdminCache from '../views/AdminCache.vue'
import AdminScraping from '../views/AdminScraping.vue'
import AdminSystem from '../views/AdminSystem.vue'

const routes = [
  {
    path: '/',
    name: 'MainPage',
    component: MainPage
  },
  {
    path: '/home',
    name: 'Home',
    component: Home
  },
  {
    path: '/spells',
    name: 'Spells',
    component: Spells
  },
  {
    path: '/class/:className',
    name: 'ClassSpells',
    component: ClassSpells,
    props: true
  },
  // OAuth authentication routes
  {
    path: '/auth/callback',
    name: 'AuthCallback',
    component: AuthCallback
  },
  {
    path: '/profile',
    name: 'Profile',
    component: Profile
  },
  // Admin routes
  {
    path: '/admin-test',
    name: 'AdminTest',
    component: AdminDashboardTest
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/users',
    name: 'AdminUsers',
    component: AdminUsers,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/cache',
    name: 'AdminCache',
    component: AdminCache,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/scraping',
    name: 'AdminScraping',
    component: AdminScraping,
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/admin/system',
    name: 'AdminSystem',
    component: AdminSystem,
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guards for admin routes
router.beforeEach(async (to, from, next) => {
  // Check if route requires authentication
  if (to.matched.some(record => record.meta.requiresAuth)) {
    try {
      const { useUserStore } = await import('../stores/userStore')
      const userStore = useUserStore()
      
      if (!userStore.isAuthenticated) {
        next('/')
        return
      }
      
      // Check if route requires admin
      if (to.matched.some(record => record.meta.requiresAdmin)) {
        if (userStore.user?.role !== 'admin') {
          next('/')
          return
        }
      }
      
      next()
    } catch (err) {
      console.error('Error in route guard:', err)
      next('/')
    }
  } else {
    next()
  }
})

export default router 