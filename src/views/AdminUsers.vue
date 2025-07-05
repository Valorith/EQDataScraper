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
                  <span v-if="user.display_name" class="display-name">({{ user.display_name }})</span>
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
                  title="View user details and sessions"
                >
                  <i class="fas fa-eye"></i>
                  <span class="btn-text">View</span>
                </button>
                
                <!-- Role Dropdown -->
                <div class="role-dropdown" v-if="user.id !== currentUserId">
                  <button 
                    @click="toggleRoleDropdown(user.id)"
                    class="role-dropdown-btn"
                    :class="{ 'active': activeRoleDropdown === user.id }"
                  >
                    <i class="fas fa-user-cog"></i>
                    <span class="btn-text">Role</span>
                    <i class="fas fa-chevron-down dropdown-arrow"></i>
                  </button>
                  <div 
                    v-if="activeRoleDropdown === user.id" 
                    class="role-dropdown-menu"
                    @click.stop
                  >
                    <div class="dropdown-header">Select Role</div>
                    <button
                      v-for="role in availableRoles"
                      :key="role.value"
                      @click="changeUserRole(user, role.value)"
                      class="role-option"
                      :class="{ 'current': user.role === role.value }"
                    >
                      <i v-if="user.role === role.value" class="fas fa-check"></i>
                      <i v-else class="role-spacer"></i>
                      <span>{{ role.label }}</span>
                    </button>
                  </div>
                </div>
                
                <button 
                  v-if="user.id !== currentUserId"
                  @click="deleteSessions(user)" 
                  class="action-btn delete"
                  title="Force logout from all devices"
                >
                  <i class="fas fa-sign-out-alt"></i>
                  <span class="btn-text">Logout All</span>
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
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()

// API base URL - in development, use empty string so proxy handles /api routes
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
const activeRoleDropdown = ref(null)

// Available roles
const availableRoles = [
  { value: 'user', label: 'User' },
  { value: 'admin', label: 'Administrator' }
]

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
    
    // Store total count if available
    const totalCount = data.total || (data.total_pages * perPage.value) || users.value.length
    
    // Load stats separately - but don't fail the whole page if stats fail
    try {
      const statsResponse = await axios.get(`${API_BASE_URL}/api/admin/stats`, {
        headers: { Authorization: `Bearer ${userStore.accessToken}` }
      })
      // Handle both possible response formats
      if (statsResponse.data.data?.users) {
        stats.value = statsResponse.data.data.users
      } else if (statsResponse.data.users) {
        stats.value = statsResponse.data.users
      } else {
        // Fallback to direct data if structure is different
        stats.value = statsResponse.data
      }
    } catch (statsError) {
      console.error('Error loading stats (non-critical):', statsError)
      // Calculate stats from the users we already loaded
      // Since this is paginated, we'll use the total from the response
      const adminCount = users.value.filter(u => u.role === 'admin').length
      stats.value = {
        total: totalCount,
        active_30d: totalCount, // We don't have this data, so use total
        new_7d: totalCount, // We don't have this data, so use total
        admins: adminCount
      }
    }
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

const toggleRoleDropdown = (userId) => {
  if (activeRoleDropdown.value === userId) {
    activeRoleDropdown.value = null
  } else {
    activeRoleDropdown.value = userId
  }
}

const changeUserRole = async (user, newRole) => {
  // Don't do anything if it's the same role
  if (user.role === newRole) {
    activeRoleDropdown.value = null
    return
  }
  
  const roleLabel = availableRoles.find(r => r.value === newRole)?.label
  const confirmMessage = `Change ${user.first_name} ${user.last_name}'s role from ${user.role} to ${newRole}?`
  
  if (confirm(confirmMessage)) {
    try {
      await axios.put(`${API_BASE_URL}/api/admin/users/${user.id}`, 
        { role: newRole },
        { headers: { Authorization: `Bearer ${userStore.accessToken}` } }
      )
      activeRoleDropdown.value = null
      await loadUsers()
    } catch (error) {
      console.error('Error changing user role:', error)
      alert('Failed to change user role. Please try again.')
    }
  }
  activeRoleDropdown.value = null
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

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
  if (!event.target.closest('.role-dropdown')) {
    activeRoleDropdown.value = null
  }
}

// Lifecycle
onMounted(() => {
  loadUsers()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.admin-users {
  padding: 20px;
  padding-top: 80px; /* Add padding to account for fixed header elements */
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 30px;
  flex-wrap: wrap;
  gap: 20px;
  margin-top: 20px; /* Add space from top to avoid logo overlap */
}

.header-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.header-actions {
  margin-top: 30px; /* Add significant space above search bar */
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
  max-width: 100%;
  z-index: 10; /* Ensure it's below the user menu */
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
  color: #1a202c;
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

.display-name {
  color: #6b7280;
  font-weight: 400;
  font-style: italic;
  margin-left: 4px;
}

.role-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
}

.role-badge.user {
  background: #dbeafe;
  color: #1e40af;
  border: 1px solid #93c5fd;
}

.role-badge.admin {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}

.action-buttons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.85rem;
  font-weight: 500;
  white-space: nowrap;
}

.action-btn.view {
  background: #e6f2ff;
  color: #3182ce;
}

.action-btn.view:hover {
  background: #3182ce;
  color: white;
}

.btn-text {
  display: none;
}

@media (min-width: 1200px) {
  .btn-text {
    display: inline;
  }
}

@media (max-width: 1199px) {
  .action-btn,
  .role-dropdown-btn {
    width: 36px;
    height: 36px;
    padding: 0;
  }
  
  .dropdown-arrow {
    display: none;
  }
}

.role-dropdown {
  position: relative;
  display: inline-block;
}

.role-dropdown-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.85rem;
  font-weight: 500;
  white-space: nowrap;
  background: #e6f2ff;
  color: #3182ce;
}

.role-dropdown-btn:hover,
.role-dropdown-btn.active {
  background: #3182ce;
  color: white;
}

.dropdown-arrow {
  font-size: 0.7rem;
  transition: transform 0.2s;
}

.role-dropdown-btn.active .dropdown-arrow {
  transform: rotate(180deg);
}

.role-dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 100;
  min-width: 150px;
  overflow: hidden;
}

.dropdown-header {
  padding: 8px 12px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
  border-bottom: 1px solid #e5e7eb;
  background: #f7fafc;
}

.role-option {
  width: 100%;
  padding: 10px 12px;
  border: none;
  background: white;
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: background 0.2s;
  font-size: 0.9rem;
  text-align: left;
}

.role-option:hover {
  background: #f7fafc;
}

.role-option.current {
  background: #e6f2ff;
  color: #3182ce;
  font-weight: 500;
}

.role-option i {
  width: 16px;
  text-align: center;
}

.role-spacer {
  display: inline-block;
  width: 16px;
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

@media (max-width: 1200px) {
  .admin-users {
    padding-top: 100px; /* More space on smaller screens */
  }
  
  .page-header {
    margin-top: 40px;
  }
}

@media (max-width: 768px) {
  .admin-users {
    padding-top: 120px; /* Even more space on mobile */
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    margin-top: 60px;
  }
  
  .header-content h1 {
    font-size: 2rem; /* Smaller title on mobile */
  }

  .search-box {
    width: 100%;
    margin-top: 10px;
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