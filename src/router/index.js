import { createRouter, createWebHistory } from 'vue-router'
import MainPage from '../views/MainPage.vue'
import Home from '../views/Home.vue'
import Items from '../views/Items.vue'
import Spells from '../views/Spells.vue'
import NPCs from '../views/NPCs.vue'
import Zones from '../views/Zones.vue'
import Characters from '../views/Characters.vue'

// OAuth authentication components (lazy loaded)
const AuthCallback = () => import('../views/AuthCallback.vue')
const AuthCallbackDebug = () => import('../views/AuthCallbackDebug.vue')
const Profile = () => import('../views/Profile.vue')

// Admin components - import directly for debugging
import AdminDashboard from '../views/AdminDashboard.vue'
import AdminDashboardTest from '../views/AdminDashboardTest.vue'
import AdminUsers from '../views/AdminUsers.vue'
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
    path: '/items',
    name: 'Items',
    component: Items
  },
  {
    path: '/spells',
    name: 'Spells',
    component: Spells
  },
  {
    path: '/npcs',
    name: 'NPCs',
    component: NPCs
  },
  {
    path: '/zones',
    name: 'Zones',
    component: Zones
  },
  {
    path: '/characters',
    name: 'Characters',
    component: Characters
  },
  // OAuth authentication routes
  {
    path: '/auth/callback',
    name: 'AuthCallback',
    component: AuthCallback
  },
  {
    path: '/auth/callback-debug',
    name: 'AuthCallbackDebug',
    component: AuthCallbackDebug
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
  if (import.meta.env.MODE === 'development') {
    console.log('Navigating to:', to.path, to.name)
  }
  
  // Allow access to main page and auth callback without login
  const publicRoutes = ['MainPage', 'AuthCallback', 'Items', 'NPCs', 'Spells', 'Zones', 'Characters']
  
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
    
    if (import.meta.env.MODE === 'development') {
      console.log('Auth check - isAuthenticated:', userStore.isAuthenticated)
      console.log('Auth check - user role:', userStore.user?.role)
    }
    
    if (!userStore.isAuthenticated) {
      // Show toast message
      toastService.warning('Please sign in to access this page', 4000)
      // Redirect to main page if not authenticated
      next('/')
      return
    }
    
    // Check if route specifically requires admin
    if (to.matched.some(record => record.meta.requiresAdmin)) {
      if (import.meta.env.MODE === 'development') {
        console.log('Route requires admin. User is admin:', userStore.user?.role === 'admin')
      }
      if (userStore.user?.role !== 'admin') {
        toastService.error('Admin access required', 3000)
        next('/')
        return
      }
    }
    
    if (import.meta.env.MODE === 'development') {
      console.log('Navigation approved')
    }
    next()
  } catch (err) {
    console.error('Error in route guard:', err)
    next('/')
  }
})

export default router 