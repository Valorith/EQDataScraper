<template>
  <div class="admin-users">
    <div class="page-header">
      <div class="header-content">
        <router-link to="/admin" class="back-link">
          <i class="fas fa-arrow-left"></i>
          Back to Dashboard
        </router-link>
        <h1>User Management</h1>
      </div>
      <div class="header-actions">
        <div class="search-box">
          <i class="fas fa-search"></i>
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="Search users by name or email..."
            @input="debouncedSearch"
          >
        </div>
      </div>
    </div>

    <!-- User Stats -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ stats.total || 0 }}</div>
        <div class="stat-label">Total Users</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.active_30d || 0 }}</div>
        <div class="stat-label">Active (30d)</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.new_7d || 0 }}</div>
        <div class="stat-label">New (7d)</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ stats.admins || 0 }}</div>
        <div class="stat-label">Admins</div>
      </div>
    </div>

    <!-- Users Table -->
    <div class="users-table-container">
      <table class="users-table">
        <thead>
          <tr>
            <th>User</th>
            <th>Email</th>
            <th>Role</th>
            <th>Joined</th>
            <th>Last Login</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>
              <div class="user-info">
                <img 
                  v-if="user.avatar_url" 
                  :src="user.avatar_url" 
                  alt="Avatar"
                  class="user-avatar"
                >
                <div v-else class="user-avatar-fallback">
                  {{ getInitials(user) }}
                </div>
                <span class="user-name">
                  {{ user.first_name }} {{ user.last_name }}
                </span>
              </div>
            </td>
            <td>{{ user.email }}</td>
            <td>
              <span class="role-badge" :class="user.role">
                {{ user.role }}
              </span>
            </td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td>{{ formatDate(user.last_login) || 'Never' }}</td>
            <td>
              <div class="action-buttons">
                <button 
                  @click="viewUserDetails(user)" 
                  class="action-btn view"
                  title="View Details"
                >
                  <i class="fas fa-eye"></i>
                </button>
                <button 
                  v-if="user.role !== 'admin' && user.id !== currentUserId" 
                  @click="promoteToAdmin(user)" 
                  class="action-btn promote"
                  title="Promote to Admin"
                >
                  <i class="fas fa-user-shield"></i>
                </button>
                <button 
                  v-else-if="user.role === 'admin' && user.id !== currentUserId" 
                  @click="demoteToUser(user)" 
                  class="action-btn demote"
                  title="Demote to User"
                >
                  <i class="fas fa-user"></i>
                </button>
                <button 
                  v-if="user.id !== currentUserId"
                  @click="deleteSessions(user)" 
                  class="action-btn delete"
                  title="Delete All Sessions"
                >
                  <i class="fas fa-sign-out-alt"></i>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="loading" class="loading">
        <i class="fas fa-spinner fa-spin"></i>
        Loading users...
      </div>

      <div v-if="!loading && users.length === 0" class="no-users">
        <p>No users found</p>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="pagination">
      <button 
        @click="changePage(currentPage - 1)" 
        :disabled="currentPage === 1"
        class="page-btn"
      >
        <i class="fas fa-chevron-left"></i>
      </button>
      <span class="page-info">
        Page {{ currentPage }} of {{ totalPages }}
      </span>
      <button 
        @click="changePage(currentPage + 1)" 
        :disabled="currentPage === totalPages"
        class="page-btn"
      >
        <i class="fas fa-chevron-right"></i>
      </button>
    </div>

    <!-- User Details Modal -->
    <div v-if="selectedUser" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>User Details</h2>
          <button @click="closeModal" class="close-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="detail-section">
            <h3>Profile Information</h3>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="label">Name:</span>
                <span class="value">{{ selectedUser.first_name }} {{ selectedUser.last_name }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Email:</span>
                <span class="value">{{ selectedUser.email }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Role:</span>
                <span class="value role-badge" :class="selectedUser.role">{{ selectedUser.role }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Google ID:</span>
                <span class="value">{{ selectedUser.google_id }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Joined:</span>
                <span class="value">{{ formatDateTime(selectedUser.created_at) }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Last Login:</span>
                <span class="value">{{ formatDateTime(selectedUser.last_login) || 'Never' }}</span>
              </div>
            </div>
          </div>

          <div v-if="userDetails" class="detail-section">
            <h3>Preferences</h3>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="label">Theme:</span>
                <span class="value">{{ userDetails.preferences?.theme_preference || 'auto' }}</span>
              </div>
              <div class="detail-item">
                <span class="label">Results per page:</span>
                <span class="value">{{ userDetails.preferences?.results_per_page || 20 }}</span>
              </div>
            </div>
          </div>

          <div v-if="userDetails?.sessions" class="detail-section">
            <h3>Active Sessions ({{ userDetails.session_count }})</h3>
            <div class="sessions-list">
              <div v-for="session in userDetails.sessions" :key="session.id" class="session-item">
                <div class="session-info">
                  <div class="session-ip">IP: {{ session.ip_address || 'Unknown' }}</div>
                  <div class="session-time">Created: {{ formatDateTime(session.created_at) }}</div>
                  <div class="session-time">Last used: {{ formatDateTime(session.last_used) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()

// API base URL
const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || 
  (import.meta.env.PROD ? 'https://eqdatascraper-backend-production.up.railway.app' : '')

// State
const users = ref([])
const stats = ref({})
const loading = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const perPage = ref(20)
const totalPages = ref(1)
const selectedUser = ref(null)
const userDetails = ref(null)

// Computed
const currentUserId = computed(() => userStore.user?.id)

// Methods
const loadUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      per_page: perPage.value
    }
    if (searchQuery.value) {
      params.search = searchQuery.value
    }

    const response = await axios.get(`${API_BASE_URL}/api/admin/users`, {
      headers: { Authorization: `Bearer ${userStore.accessToken}` },
      params
    })

    const data = response.data.data
    users.value = data.users
    totalPages.value = data.total_pages
    
    // Load stats separately
    const statsResponse = await axios.get(`${API_BASE_URL}/api/admin/stats`, {
      headers: { Authorization: `Bearer ${userStore.accessToken}` }
    })
    stats.value = statsResponse.data.data.users
  } catch (error) {
    console.error('Error loading users:', error)
  } finally {
    loading.value = false
  }
}

const viewUserDetails = async (user) => {
  selectedUser.value = user
  try {
    const response = await axios.get(`${API_BASE_URL}/api/admin/users/${user.id}`, {
      headers: { Authorization: `Bearer ${userStore.accessToken}` }
    })
    userDetails.value = response.data.data
  } catch (error) {
    console.error('Error loading user details:', error)
  }
}

const promoteToAdmin = async (user) => {
  if (confirm(`Promote ${user.first_name} ${user.last_name} to admin?`)) {
    try {
      await axios.put(`${API_BASE_URL}/api/admin/users/${user.id}`, 
        { role: 'admin' },
        { headers: { Authorization: `Bearer ${userStore.accessToken}` } }
      )
      await loadUsers()
    } catch (error) {
      console.error('Error promoting user:', error)
    }
  }
}

const demoteToUser = async (user) => {
  if (confirm(`Demote ${user.first_name} ${user.last_name} to regular user?`)) {
    try {
      await axios.put(`${API_BASE_URL}/api/admin/users/${user.id}`, 
        { role: 'user' },
        { headers: { Authorization: `Bearer ${userStore.accessToken}` } }
      )
      await loadUsers()
    } catch (error) {
      console.error('Error demoting user:', error)
    }
  }
}

const deleteSessions = async (user) => {
  if (confirm(`Delete all sessions for ${user.first_name} ${user.last_name}? They will need to log in again.`)) {
    try {
      await axios.delete(`${API_BASE_URL}/api/admin/users/${user.id}/sessions`, {
        headers: { Authorization: `Bearer ${userStore.accessToken}` }
      })
      alert('Sessions deleted successfully')
    } catch (error) {
      console.error('Error deleting sessions:', error)
    }
  }
}

const changePage = (page) => {
  currentPage.value = page
  loadUsers()
}

const closeModal = () => {
  selectedUser.value = null
  userDetails.value = null
}

const getInitials = (user) => {
  const first = user.first_name?.[0] || ''
  const last = user.last_name?.[0] || ''
  return (first + last).toUpperCase() || user.email[0].toUpperCase()
}

const formatDate = (date) => {
  if (!date) return null
  return new Date(date).toLocaleDateString()
}

const formatDateTime = (date) => {
  if (!date) return null
  return new Date(date).toLocaleString()
}

// Debounced search
let searchTimeout = null
const debouncedSearch = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    currentPage.value = 1
    loadUsers()
  }, 300)
}

// Lifecycle
onMounted(() => {
  loadUsers()
})
</script>

<style scoped>
.admin-users {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
  gap: 20px;
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #667eea;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.back-link:hover {
  color: #764ba2;
}

.page-header h1 {
  font-size: 2.5rem;
  margin: 0;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.search-box {
  position: relative;
  width: 300px;
}

.search-box i {
  position: absolute;
  left: 15px;
  top: 50%;
  transform: translateY(-50%);
  color: #666;
}

.search-box input {
  width: 100%;
  padding: 12px 12px 12px 45px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.2s;
}

.search-box input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #1a202c;
  margin-bottom: 5px;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
}

.users-table-container {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
}

.users-table th {
  background: #f7fafc;
  padding: 15px;
  text-align: left;
  font-weight: 600;
  color: #4a5568;
  border-bottom: 1px solid #e5e7eb;
}

.users-table td {
  padding: 15px;
  border-bottom: 1px solid #e5e7eb;
}

.users-table tbody tr:hover {
  background: #f7fafc;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.user-avatar-fallback {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 14px;
}

.user-name {
  font-weight: 500;
  color: #1a202c;
}

.role-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.role-badge.user {
  background: #e6f2ff;
  color: #3182ce;
}

.role-badge.admin {
  background: #fed7d7;
  color: #c53030;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn.view {
  background: #e6f2ff;
  color: #3182ce;
}

.action-btn.view:hover {
  background: #3182ce;
  color: white;
}

.action-btn.promote {
  background: #d6f5d6;
  color: #22863a;
}

.action-btn.promote:hover {
  background: #22863a;
  color: white;
}

.action-btn.demote {
  background: #fff5e6;
  color: #dd6b20;
}

.action-btn.demote:hover {
  background: #dd6b20;
  color: white;
}

.action-btn.delete {
  background: #fed7d7;
  color: #c53030;
}

.action-btn.delete:hover {
  background: #c53030;
  color: white;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.no-users {
  text-align: center;
  padding: 40px;
  color: #666;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 30px;
}

.page-btn {
  padding: 8px 16px;
  border: 1px solid #e5e7eb;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  border-color: #667eea;
  color: #667eea;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #666;
  font-weight: 500;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 800px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 25px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.close-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: #f7fafc;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e2e8f0;
}

.modal-body {
  padding: 25px;
}

.detail-section {
  margin-bottom: 30px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-section h3 {
  margin: 0 0 15px 0;
  color: #4a5568;
  font-size: 1.1rem;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.detail-item .label {
  color: #718096;
  font-size: 0.85rem;
  font-weight: 500;
}

.detail-item .value {
  color: #1a202c;
  font-weight: 500;
}

.sessions-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.session-item {
  background: #f7fafc;
  padding: 15px;
  border-radius: 8px;
}

.session-info {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.session-ip {
  font-weight: 500;
}

.session-time {
  color: #666;
  font-size: 0.85rem;
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .search-box {
    width: 100%;
  }

  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }

  .users-table {
    font-size: 0.9rem;
  }

  .action-buttons {
    flex-wrap: wrap;
  }
}
</style>