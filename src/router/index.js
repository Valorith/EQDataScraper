import { createRouter, createWebHistory } from 'vue-router'
import MainPage from '../views/MainPage.vue'
import Home from '../views/Home.vue'
import Spells from '../views/Spells.vue'
import ClassSpells from '../views/ClassSpells.vue'
import Items from '../views/Items.vue'

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
import AdminLogs from '../views/AdminLogs.vue'

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
  {
    path: '/items',
    name: 'Items',
    component: Items
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
  },
  {
    path: '/admin/logs',
    name: 'AdminLogs',
    component: AdminLogs,
    meta: { requiresAuth: true, requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guards for authentication
router.beforeEach(async (to, from, next) => {
  // Allow access to main page and auth callback without login
  const publicRoutes = ['MainPage', 'AuthCallback']
  
  // Check if the route is public
  if (publicRoutes.includes(to.name)) {
    next()
    return
  }
  
  // All other routes require authentication
  try {
    const { useUserStore } = await import('../stores/userStore')
    const { toastService } = await import('../services/toastService')
    const userStore = useUserStore()
    
    if (!userStore.isAuthenticated) {
      // Show toast message
      toastService.warning('Please sign in to access this page', 4000)
      // Redirect to main page if not authenticated
      next('/')
      return
    }
    
    // Check if route specifically requires admin
    if (to.matched.some(record => record.meta.requiresAdmin)) {
      if (userStore.user?.role !== 'admin') {
        toastService.error('Admin access required', 3000)
        next('/')
        return
      }
    }
    
    next()
  } catch (err) {
    console.error('Error in route guard:', err)
    next('/')
  }
})

export default router 