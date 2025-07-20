<template>
  <div class="admin-dashboard">
    <div class="dashboard-header">
      <h1>Admin Dashboard</h1>
      <p class="subtitle">Manage users, monitor app performance, and control system settings</p>
    </div>

    <div class="dashboard-grid">
      <!-- User Management Card -->
      <div class="dashboard-card">
        <div class="card-header">
          <div class="card-icon">
            <i class="fas fa-users"></i>
          </div>
          <h2>User Management</h2>
        </div>
        <div class="card-content">
          <div class="stat-row">
            <span class="stat-label">Total Users</span>
            <span class="stat-value" :class="{ 'loading': statsLoading }">
              <span v-if="!statsLoading">{{ stats.users?.total || stats.totalUsers || 0 }}</span>
              <span v-else class="skeleton-text">--</span>
            </span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Active Today</span>
            <span class="stat-value" :class="{ 'loading': statsLoading }">
              <span v-if="!statsLoading">{{ stats.users?.active_today || stats.activeToday || 0 }}</span>
              <span v-else class="skeleton-text">--</span>
            </span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Admin Users</span>
            <span class="stat-value" :class="{ 'loading': statsLoading }">
              <span v-if="!statsLoading">{{ stats.users?.admins || stats.adminUsers || 0 }}</span>
              <span v-else class="skeleton-text">--</span>
            </span>
          </div>
        </div>
        <div class="card-actions">
          <router-link to="/admin/users" class="action-button primary">
            <i class="fas fa-arrow-right"></i>
            Manage Users
          </router-link>
        </div>
      </div>


      <!-- System Health Card -->
      <div class="dashboard-card">
        <div class="card-header">
          <div class="card-icon health">
            <i class="fas fa-heartbeat"></i>
          </div>
          <h2>System Health</h2>
        </div>
        <div class="card-content">
          <div class="stat-row">
            <span class="stat-label">API Status</span>
            <span class="stat-value success">{{ systemHealth.apiStatus || 'Online' }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Response Time</span>
            <span class="stat-value">{{ systemHealth.avgResponseTime || 0 }}ms</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Error Rate</span>
            <span class="stat-value" :class="(systemHealth.errorRate || 0) > 5 ? 'warning' : 'success'">
              {{ systemHealth.errorRate || 0 }}%
            </span>
          </div>
        </div>
        <div class="card-actions">
          <button @click="navigateToSystem" class="action-button primary">
            <i class="fas fa-arrow-right"></i>
            System Details
          </button>
          <button @click.stop="openBackendDiagnostic" class="action-button secondary backend-diagnostic-btn">
            <i class="fas fa-stethoscope"></i>
            Diagnostic
          </button>
        </div>
      </div>

      <!-- Content Database Card -->
      <div class="dashboard-card">
        <div class="card-header">
          <div class="card-icon database" :class="{
            'status-connected': databaseStatus.connected,
            'status-connecting': databaseStatus.connecting,
            'status-disconnected': !databaseStatus.connected && !databaseStatus.connecting
          }">
            <i class="fas" :class="{
              'fa-check-circle': databaseStatus.connected,
              'fa-sync-alt fa-spin': databaseStatus.connecting,
              'fa-exclamation-circle': !databaseStatus.connected && !databaseStatus.connecting
            }"></i>
          </div>
          <h2>Content Database</h2>
        </div>
        <div class="card-content">
          <div class="stat-row">
            <span class="stat-label">Status</span>
            <span class="stat-value" :class="{
              'success': databaseStatus.connected,
              'warning': databaseStatus.connecting || (!databaseStatus.connected && databaseStatus.retryDelay > 0),
              'error': !databaseStatus.connected && databaseStatus.retryDelay === 0
            }">
              {{ databaseStatus.connecting ? 'Connecting...' :
                 databaseStatus.connected ? 'Connected' :
                 databaseStatus.retryDelay > 0 ? `Reconnecting in ${databaseStatus.retryDelay}s` :
                 'Disconnected' }}
            </span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Host</span>
            <span class="stat-value">{{ databaseStatus.host || 'Not configured' }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Database</span>
            <span class="stat-value">{{ databaseStatus.database || 'None' }}</span>
          </div>
          <div v-if="databaseStatus.lastAttempt && !databaseStatus.connected" class="stat-row">
            <span class="stat-label">Last Attempt</span>
            <span class="stat-value small">{{ databaseStatus.lastAttempt }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">Config Source</span>
            <span class="stat-value" :class="{
              'success': storageInfo.config_source === 'persistent_storage',
              'info': storageInfo.config_source === 'environment_variable',
              'warning': storageInfo.config_source === 'config_json' || storageInfo.config_source === 'none'
            }">
              {{ formatConfigSource(storageInfo.config_source) }}
            </span>
          </div>
          <div v-if="storageInfo.config_source === 'none'" class="stat-row warning-row">
            <i class="fas fa-exclamation-triangle"></i>
            <span class="warning-text">Database configuration will be lost on deployment!</span>
          </div>
        </div>
        <div class="card-actions database-actions">
          <button @click="openDatabaseModal" class="action-button primary">
            <i class="fas fa-cog"></i>
            Configure
          </button>
          <button @click="openDiagnosticsModal" class="action-button secondary">
            <i class="fas fa-stethoscope"></i>
            Diagnose
          </button>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions">
      <h2>Quick Actions</h2>
      <div class="action-grid">
        <button @click="exportData" class="quick-action-btn">
          <i class="fas fa-file-export"></i>
          <span>Export Data</span>
        </button>
        <button @click="viewLogs" class="quick-action-btn">
          <i class="fas fa-history"></i>
          <span>View Logs</span>
        </button>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="recent-activity">
      <h2>Recent Activity</h2>
      <div class="activity-list">
        <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
          <div v-if="isUserActivity(activity.type) && activity.userAvatar" class="activity-avatar">
            <img :src="activity.userAvatar" :alt="activity.userName || 'User'" />
          </div>
          <div v-else class="activity-icon" :class="activity.type">
            <i :class="getActivityIcon(activity.type)"></i>
          </div>
          <div class="activity-content">
            <p class="activity-description">{{ activity.description }}</p>
            <span class="activity-time">{{ formatTime(activity.timestamp) }}</span>
          </div>
        </div>
        <div v-if="recentActivities.length === 0" class="no-activity">
          <p>No activity logged yet</p>
          <p class="activity-help">Activity will appear here when users log in, search spells, or perform admin actions</p>
        </div>
      </div>
    </div>

    <!-- Network Test Modal -->
    <div v-if="showNetworkTestModal" class="modal-overlay" @click.self="closeNetworkTestModal">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Network Connectivity Test</h2>
          <button @click="closeNetworkTestModal" class="close-button">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <p class="modal-description">
            Test network connectivity from Railway to various hosts to diagnose connection issues.
          </p>
          
          <div class="form-group">
            <label for="test-host">Host (IP or Domain)</label>
            <input 
              id="test-host"
              v-model="networkTestForm.host" 
              type="text" 
              placeholder="e.g., 8.8.8.8 or google.com"
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <label for="test-port">Port</label>
            <input 
              id="test-port"
              v-model.number="networkTestForm.port" 
              type="number" 
              placeholder="3306"
              class="form-input"
            />
          </div>
          
          <div class="form-group">
            <label for="test-type">Test Type</label>
            <select id="test-type" v-model="networkTestForm.test_type" class="form-input">
              <option value="tcp">TCP Connection</option>
              <option value="ping">ICMP Ping</option>
              <option value="mysql">MySQL Connection</option>
            </select>
          </div>
          
          <!-- Quick test buttons -->
          <div class="quick-tests">
            <p>Quick Tests:</p>
            <button @click="setQuickTest('76.251.85.36', 3306, 'tcp')" class="quick-test-btn">
              Your SQL Server
            </button>
            <button @click="setQuickTest('8.8.8.8', 53, 'tcp')" class="quick-test-btn">
              Google DNS
            </button>
            <button @click="setQuickTest('1.1.1.1', 53, 'tcp')" class="quick-test-btn">
              Cloudflare DNS
            </button>
            <button @click="setQuickTest('google.com', 80, 'tcp')" class="quick-test-btn">
              Google.com
            </button>
          </div>
          
          <!-- Test Results -->
          <div v-if="networkTestResult" class="test-results" :class="{ 'success': networkTestResult.overall_success, 'error': !networkTestResult.overall_success }">
            <h3>Test Results for {{ networkTestResult.host }}:{{ networkTestResult.port }}</h3>
            
            <div v-for="(test, name) in networkTestResult.tests" :key="name" class="test-item">
              <div class="test-header">
                <i class="fas" :class="test.success ? 'fa-check-circle' : 'fa-times-circle'"></i>
                <strong>{{ formatTestName(name) }}</strong>
                <span v-if="test.time_ms" class="test-time">({{ test.time_ms }}ms)</span>
              </div>
              <div class="test-message">{{ test.message }}</div>
              <div v-if="test.error" class="test-error">
                Error: {{ test.error_type || 'Unknown' }} - {{ test.error }}
              </div>
              <div v-if="test.resolved_addresses" class="test-detail">
                Resolved IPs: {{ test.resolved_addresses.join(', ') }}
              </div>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button 
            @click="runNetworkTest" 
            class="primary-button"
            :disabled="testingNetwork || !networkTestForm.host"
          >
            <i class="fas" :class="testingNetwork ? 'fa-spinner fa-spin' : 'fa-network-wired'"></i>
            {{ testingNetwork ? 'Testing...' : 'Run Test' }}
          </button>
          <button @click="closeNetworkTestModal" class="secondary-button">
            Cancel
          </button>
        </div>
      </div>
    </div>

    <!-- Database Diagnostics Modal -->
    <div v-if="showDiagnosticsModal" class="modal-overlay" @click.self="closeDiagnosticsModal">
      <div class="modal-content diagnostics-modal">
        <div class="modal-header">
          <h2>Database Diagnostics</h2>
          <button @click="closeDiagnosticsModal" class="close-button">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <p class="modal-description">
            Run various diagnostic tests to troubleshoot database connection issues.
          </p>
          
          <!-- Test Options -->
          <div class="diagnostic-tests">
            <div class="test-card">
              <div class="test-header">
                <i class="fas fa-sync-alt"></i>
                <h3>Refresh Connection</h3>
              </div>
              <p>Attempt to reconnect to the database using stored configuration.</p>
              <button 
                @click="refreshConnection" 
                class="test-button"
                :disabled="refreshingConnection"
              >
                <i class="fas fa-sync-alt" :class="{ 'fa-spin': refreshingConnection }"></i>
                {{ refreshingConnection ? 'Refreshing...' : 'Refresh Connection' }}
              </button>
            </div>
            
            <div class="test-card">
              <div class="test-header">
                <i class="fas fa-clipboard-check"></i>
                <h3>Full Diagnostics</h3>
              </div>
              <p>Run comprehensive diagnostics including environment checks, configuration validation, and connection tests.</p>
              <button 
                @click="runDiagnostics" 
                class="test-button"
                :disabled="runningDiagnostics"
              >
                <i class="fas fa-clipboard-check" :class="{ 'fa-spin': runningDiagnostics }"></i>
                {{ runningDiagnostics ? 'Running...' : 'Run Full Diagnostics' }}
              </button>
            </div>
            
            <div class="test-card">
              <div class="test-header">
                <i class="fas fa-network-wired"></i>
                <h3>Network Test</h3>
              </div>
              <p>Test network connectivity to various hosts to isolate connection issues.</p>
              <button 
                @click="openNetworkTest" 
                class="test-button"
              >
                <i class="fas fa-network-wired"></i>
                Open Network Test
              </button>
            </div>
            
            <div class="test-card">
              <div class="test-header">
                <i class="fas fa-server"></i>
                <h3>Backend Check</h3>
              </div>
              <p>Quick check to verify the backend server is reachable.</p>
              <button 
                @click="checkBackendConnectivity" 
                class="test-button"
                :disabled="checkingBackend"
              >
                <i class="fas" :class="checkingBackend ? 'fa-spinner fa-spin' : 'fa-server'"></i>
                {{ checkingBackend ? 'Checking...' : 'Check Backend' }}
              </button>
            </div>
          </div>
          
          <!-- Diagnostics Results -->
          <div v-if="diagnosticsResult" class="diagnostics-result">
            <div class="result-header">
              <h3><i class="fas fa-clipboard-list"></i> Diagnostics Report</h3>
              <button @click="copyDiagnostics" class="copy-button" :title="copiedDiagnostics ? 'Copied!' : 'Copy to clipboard'">
                <i :class="copiedDiagnostics ? 'fas fa-check' : 'fas fa-copy'"></i>
                {{ copiedDiagnostics ? 'Copied!' : 'Copy Report' }}
              </button>
            </div>
            
            <!-- Environment Section -->
            <div v-if="diagnosticsResult.environment" class="result-section">
              <h4><i class="fas fa-server"></i> Environment</h4>
              <div class="section-content">
                <div v-for="(value, key) in diagnosticsResult.environment" :key="key" class="result-item">
                  <span class="result-label">{{ formatPropertyName(key) }}:</span>
                  <span class="result-value">{{ value }}</span>
                </div>
              </div>
            </div>
            
            <!-- Configuration Section -->
            <div v-if="diagnosticsResult.config_checks" class="result-section">
              <h4><i class="fas fa-cog"></i> Configuration</h4>
              <div class="section-content">
                <div class="result-item">
                  <span class="result-label">Config Found:</span>
                  <span class="result-value" :class="diagnosticsResult.config_checks.persistent_config_found ? 'success' : 'error'">
                    {{ diagnosticsResult.config_checks.persistent_config_found ? 'Yes' : 'No' }}
                  </span>
                </div>
                <div v-if="diagnosticsResult.config_checks.persistent_config_found" class="result-item">
                  <span class="result-label">Source:</span>
                  <span class="result-value">{{ diagnosticsResult.config_checks.config_source }}</span>
                </div>
                <div v-if="diagnosticsResult.config_checks.host" class="result-item">
                  <span class="result-label">Host:</span>
                  <span class="result-value">{{ diagnosticsResult.config_checks.host }}</span>
                </div>
                <div v-if="diagnosticsResult.config_checks.port" class="result-item">
                  <span class="result-label">Port:</span>
                  <span class="result-value">{{ diagnosticsResult.config_checks.port }}</span>
                </div>
                <div v-if="diagnosticsResult.config_checks.database" class="result-item">
                  <span class="result-label">Database:</span>
                  <span class="result-value">{{ diagnosticsResult.config_checks.database }}</span>
                </div>
                <div v-if="diagnosticsResult.config_checks.error" class="result-item">
                  <span class="result-label">Error:</span>
                  <span class="result-value error">{{ diagnosticsResult.config_checks.error }}</span>
                </div>
              </div>
            </div>
            
            <!-- Connection Test Section -->
            <div v-if="diagnosticsResult.connection_test" class="result-section">
              <h4><i class="fas fa-plug"></i> Connection Test</h4>
              <div class="section-content">
                <div class="result-item">
                  <span class="result-label">Status:</span>
                  <span class="result-value" :class="diagnosticsResult.connection_test.success ? 'success' : 'error'">
                    {{ diagnosticsResult.connection_test.success ? 'Connected' : 'Failed' }}
                  </span>
                </div>
                <div v-if="diagnosticsResult.connection_test.db_type" class="result-item">
                  <span class="result-label">Database Type:</span>
                  <span class="result-value">{{ diagnosticsResult.connection_test.db_type }}</span>
                </div>
                <div v-if="diagnosticsResult.connection_test.query_test" class="result-item">
                  <span class="result-label">Query Test:</span>
                  <span class="result-value success">{{ diagnosticsResult.connection_test.query_test }}</span>
                </div>
                <div v-if="diagnosticsResult.connection_test.error" class="result-item">
                  <span class="result-label">Error:</span>
                  <span class="result-value error">{{ diagnosticsResult.connection_test.error }}</span>
                </div>
              </div>
            </div>
            
            <!-- Persistent Storage Section -->
            <div v-if="diagnosticsResult.persistent_storage" class="result-section">
              <h4><i class="fas fa-hdd"></i> Persistent Storage</h4>
              <div class="section-content">
                <div class="result-item">
                  <span class="result-label">Data Directory:</span>
                  <span class="result-value">{{ diagnosticsResult.persistent_storage.data_directory || 'Not available' }}</span>
                </div>
                <div class="result-item">
                  <span class="result-label">Directory Exists:</span>
                  <span class="result-value" :class="diagnosticsResult.persistent_storage.directory_exists ? 'success' : 'error'">
                    {{ diagnosticsResult.persistent_storage.directory_exists ? 'Yes' : 'No' }}
                  </span>
                </div>
                <div class="result-item">
                  <span class="result-label">Directory Writable:</span>
                  <span class="result-value" :class="diagnosticsResult.persistent_storage.directory_writable ? 'success' : 'error'">
                    {{ diagnosticsResult.persistent_storage.directory_writable ? 'Yes' : 'No' }}
                  </span>
                </div>
                <div class="result-item">
                  <span class="result-label">Config File Exists:</span>
                  <span class="result-value" :class="diagnosticsResult.persistent_storage.config_file_exists ? 'success' : 'error'">
                    {{ diagnosticsResult.persistent_storage.config_file_exists ? 'Yes' : 'No' }}
                  </span>
                </div>
              </div>
            </div>
            
            <!-- Config Validation Section -->
            <div v-if="diagnosticsResult.config_validation" class="result-section">
              <h4><i class="fas fa-check-double"></i> Configuration Validation</h4>
              <div class="section-content">
                <div class="result-item">
                  <span class="result-label">Validation Status:</span>
                  <span class="result-value" :class="diagnosticsResult.config_validation.valid ? 'success' : 'error'">
                    {{ diagnosticsResult.config_validation.valid ? 'Valid' : 'Invalid' }}
                  </span>
                </div>
                
                <!-- Show errors if any -->
                <div v-if="diagnosticsResult.config_validation.errors && diagnosticsResult.config_validation.errors.length > 0" class="validation-errors">
                  <h5><i class="fas fa-exclamation-circle"></i> Configuration Mismatches:</h5>
                  <div v-for="(error, index) in diagnosticsResult.config_validation.errors" :key="`error-${index}`" class="mismatch-item">
                    <div class="mismatch-header">
                      <strong>{{ formatFieldName(error.field) }}</strong>
                      <span class="mismatch-description">{{ error.message }}</span>
                      <div v-if="error.url_value && error.env_value" class="mismatch-info">
                        <span v-if="error.url_value.toLowerCase() === error.env_value.toLowerCase()" class="info-badge case-diff">
                          <i class="fas fa-info-circle"></i> Case difference only
                        </span>
                        <span v-else-if="Math.abs(error.url_value.length - error.env_value.length) <= 2" class="info-badge typo-likely">
                          <i class="fas fa-exclamation-triangle"></i> Likely typo ({{ Math.abs(error.url_value.length - error.env_value.length) }} char difference)
                        </span>
                        <span v-else class="info-badge major-diff">
                          <i class="fas fa-times-circle"></i> Significant difference
                        </span>
                      </div>
                    </div>
                    <div v-if="error.url_value && error.env_value" class="mismatch-resolution">
                      <div class="mismatch-option">
                        <input 
                          type="radio" 
                          :id="`url-${error.field}`" 
                          :name="`resolve-${error.field}`"
                          :value="error.url_value"
                          v-model="mismatchResolutions[error.field]"
                        />
                        <label :for="`url-${error.field}`">
                          <span class="option-source">URL Value:</span>
                          <code v-html="highlightDifferences(error.url_value, error.env_value).str1"></code>
                        </label>
                      </div>
                      <div class="mismatch-option">
                        <input 
                          type="radio" 
                          :id="`env-${error.field}`" 
                          :name="`resolve-${error.field}`"
                          :value="error.env_value"
                          v-model="mismatchResolutions[error.field]"
                        />
                        <label :for="`env-${error.field}`">
                          <span class="option-source">Environment Variable:</span>
                          <code v-html="highlightDifferences(error.url_value, error.env_value).str2"></code>
                        </label>
                      </div>
                      <button 
                        v-if="mismatchResolutions[error.field]"
                        @click="resolveMismatch(error.field)"
                        class="resolve-button"
                        :disabled="resolvingMismatch[error.field]"
                      >
                        <i class="fas" :class="resolvingMismatch[error.field] ? 'fa-spinner fa-spin' : 'fa-check'"></i>
                        {{ resolvingMismatch[error.field] ? 'Applying...' : 'Apply Selected Value' }}
                      </button>
                    </div>
                  </div>
                </div>
                
                <!-- Show warnings if any -->
                <div v-if="diagnosticsResult.config_validation.warnings && diagnosticsResult.config_validation.warnings.length > 0" class="validation-warnings">
                  <h5><i class="fas fa-exclamation-triangle"></i> Configuration Warnings:</h5>
                  <div v-for="(warning, index) in diagnosticsResult.config_validation.warnings" :key="`warn-${index}`" class="warning-item">
                    <div class="warning-header">
                      <strong>{{ formatFieldName(warning.field) }}</strong>
                      <span class="warning-message">{{ warning.message }}</span>
                    </div>
                    <!-- Show resolution UI for warnings with url_value but no env_value -->
                    <div v-if="warning.url_value && !warning.env_value" class="mismatch-resolution">
                      <div class="resolution-options">
                        <label class="resolution-option" :class="{ 'selected': mismatchResolutions[warning.field] === warning.url_value }">
                          <input 
                            type="radio" 
                            :name="`resolve-warn-${warning.field}`"
                            :value="warning.url_value"
                            v-model="mismatchResolutions[warning.field]"
                          />
                          <span class="option-content">
                            <span class="option-label">Use URL Value:</span>
                            <code class="option-value">{{ warning.url_value }}</code>
                          </span>
                        </label>
                        <label class="resolution-option" :class="{ 'selected': mismatchResolutions[warning.field] === '' }">
                          <input 
                            type="radio" 
                            :name="`resolve-warn-${warning.field}`"
                            value=""
                            v-model="mismatchResolutions[warning.field]"
                          />
                          <span class="option-content">
                            <span class="option-label">Keep Empty:</span>
                            <code class="option-value">(not set)</code>
                          </span>
                        </label>
                      </div>
                      <button 
                        v-if="mismatchResolutions[warning.field] !== undefined"
                        @click="resolveMismatch(warning.field)"
                        class="resolve-button"
                        :disabled="resolvingMismatch[warning.field]"
                      >
                        <i class="fas" :class="resolvingMismatch[warning.field] ? 'fa-spinner fa-spin' : 'fa-check'"></i>
                        {{ resolvingMismatch[warning.field] ? 'Saving...' : 'Save' }}
                      </button>
                    </div>
                  </div>
                </div>
                
                <!-- Show config comparison -->
                <div v-if="diagnosticsResult.config_validation.config_comparison && Object.keys(diagnosticsResult.config_validation.config_comparison).length > 0" class="config-comparison">
                  <h5><i class="fas fa-columns"></i> Configuration Comparison:</h5>
                  <table class="comparison-table">
                    <thead>
                      <tr>
                        <th>Field</th>
                        <th>URL Value</th>
                        <th>Env Variable</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(comp, field) in diagnosticsResult.config_validation.config_comparison" :key="field">
                        <td>{{ formatFieldName(comp.field) }}</td>
                        <td>
                          <code v-if="comp.url_value && comp.env_value && comp.url_value !== comp.env_value" 
                                v-html="highlightDifferences(comp.url_value, comp.env_value).str1">
                          </code>
                          <code v-else>{{ comp.url_value || '(not set)' }}</code>
                        </td>
                        <td>
                          <code v-if="comp.url_value && comp.env_value && comp.url_value !== comp.env_value" 
                                v-html="highlightDifferences(comp.url_value, comp.env_value).str2">
                          </code>
                          <code v-else>{{ comp.env_value || '(not set)' }}</code>
                        </td>
                        <td>
                          <span :class="comp.match ? 'success' : 'error'">
                            <i class="fas" :class="comp.match ? 'fa-check' : 'fa-times'"></i>
                          </span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                
                <!-- Show suggested fix if available -->
                <div v-if="diagnosticsResult.config_validation.suggested_fix" class="suggested-fix">
                  <h5><i class="fas fa-wrench"></i> Suggested Fix:</h5>
                  <div class="fix-details">
                    <p><strong>Action:</strong> {{ diagnosticsResult.config_validation.suggested_fix.action }}</p>
                    <p><strong>Reason:</strong> {{ diagnosticsResult.config_validation.suggested_fix.reason }}</p>
                    <div class="fix-command">
                      <code>{{ diagnosticsResult.config_validation.suggested_fix.value }}</code>
                      <button @click="copySuggestedFix" class="copy-button" :title="copiedFix ? 'Copied!' : 'Copy to clipboard'">
                        <i :class="copiedFix ? 'fas fa-check' : 'fas fa-copy'"></i>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Recommendations Section -->
            <div v-if="diagnosticsResult.recommendations && diagnosticsResult.recommendations.length > 0" class="result-section recommendations">
              <h4><i class="fas fa-lightbulb"></i> Recommendations</h4>
              <div class="section-content">
                <ul class="recommendations-list">
                  <li v-for="(rec, index) in diagnosticsResult.recommendations" :key="index">
                    {{ rec }}
                  </li>
                </ul>
              </div>
            </div>
          </div>
          
          <!-- Connection Status -->
          <div v-if="connectionTestResult" class="connection-result" :class="connectionTestResult.success ? 'success' : 'error'">
            <div class="result-header">
              <i class="fas" :class="connectionTestResult.success ? 'fa-check-circle' : 'fa-times-circle'"></i>
              <strong>{{ connectionTestResult.message }}</strong>
            </div>
            <div v-if="connectionTestResult.details" class="result-details">
              {{ connectionTestResult.details }}
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="closeDiagnosticsModal" class="secondary-button">
            Close
          </button>
        </div>
      </div>
    </div>

    <!-- Database Configuration Modal -->
    <div v-if="showDatabaseModal" class="modal-overlay" @click="closeDatabaseModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Database Configuration</h3>
          <button @click="closeDatabaseModal" class="close-button">
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <form @submit.prevent="saveDatabaseConfig">
            <div class="form-group">
              <label for="db-type">Database Type</label>
              <select 
                id="db-type"
                v-model="databaseForm.db_type" 
                @change="updateDefaultPort"
                class="form-input"
                required
              >
                <option value="mssql">Microsoft SQL Server</option>
                <option value="mysql">MySQL</option>
                <option value="postgresql">PostgreSQL</option>
              </select>
            </div>
            
            <div class="form-group">
              <label for="db-host">Host</label>
              <input 
                id="db-host"
                v-model="databaseForm.host" 
                type="text" 
                class="form-input"
                placeholder="localhost"
                required
              />
            </div>
            
            <div class="form-group">
              <label for="db-port">Port</label>
              <input 
                id="db-port"
                v-model="databaseForm.port" 
                type="number" 
                class="form-input"
                placeholder="5432"
                min="1"
                max="65535"
                required
              />
            </div>
            
            <div class="form-group">
              <label for="db-name">Database Name</label>
              <input 
                id="db-name"
                v-model="databaseForm.database" 
                type="text" 
                class="form-input"
                placeholder="eqdata"
                required
              />
            </div>
            
            <div class="form-group">
              <label for="db-username">Username</label>
              <input 
                id="db-username"
                v-model="databaseForm.username" 
                type="text" 
                class="form-input"
                placeholder="postgres"
                required
              />
            </div>
            
            <div class="form-group">
              <label for="db-password">Password</label>
              <input 
                id="db-password"
                v-model="databaseForm.password" 
                type="password" 
                class="form-input"
                placeholder="Enter password"
                required
              />
            </div>
            
            <div class="form-group checkbox-group">
              <label class="checkbox-label">
                <input 
                  v-model="databaseForm.use_ssl" 
                  type="checkbox" 
                  class="form-checkbox"
                />
                <span class="checkbox-text">Use SSL Connection</span>
              </label>
            </div>
            
            <div v-if="databaseTestResult" class="test-result" :class="databaseTestResult.success ? 'success' : 'error'">
              <i :class="databaseTestResult.success ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
              <span>{{ databaseTestResult.message }}</span>
              
              <!-- Success details -->
              <div v-if="databaseTestResult.success && databaseTestResult.data" class="test-details">
                <p v-if="databaseTestResult.data.read_only_mode">✓ Read-only mode enabled</p>
                <p v-if="databaseTestResult.data.tables">
                  ✓ Items table: {{ databaseTestResult.data.tables.items_accessible ? 'Accessible' : 'Not accessible' }}
                  <span v-if="databaseTestResult.data.tables.items_count">({{ databaseTestResult.data.tables.items_count }} items)</span>
                </p>
                <p v-if="databaseTestResult.data.tables">
                  ✓ Discovered items table: {{ databaseTestResult.data.tables.discovered_items_accessible ? 'Accessible' : 'Not accessible' }}
                  <span v-if="databaseTestResult.data.tables.discovered_items_count">({{ databaseTestResult.data.tables.discovered_items_count }} discovered)</span>
                </p>
              </div>
              
              <!-- Error details -->
              <div v-if="!databaseTestResult.success && databaseTestResult.error" class="error-details">
                <div class="error-issue">
                  <strong>Issue:</strong> {{ databaseTestResult.error.details?.issue || 'Unknown error' }}
                </div>
                <div class="error-suggestion">
                  <strong>Suggestion:</strong> {{ databaseTestResult.error.details?.suggestion || 'Please check your connection details' }}
                </div>
                <div v-if="databaseTestResult.error.error_message" class="error-technical">
                  <details>
                    <summary>Technical details</summary>
                    <code>{{ databaseTestResult.error.error_message }}</code>
                  </details>
                </div>
              </div>
            </div>
          </form>
        </div>
        
        <div class="modal-footer">
          <button 
            @click="testDatabaseConnection" 
            class="test-button"
            :disabled="testingConnection"
          >
            <i class="fas fa-plug" :class="{ 'fa-spin': testingConnection }"></i>
            {{ testingConnection ? 'Testing...' : 'Test Connection' }}
          </button>
          
          <button 
            @click="saveDatabaseConfig" 
            class="save-button"
            :disabled="savingConfig || !databaseTestResult?.success"
          >
            <i class="fas fa-save" :class="{ 'fa-spin': savingConfig }"></i>
            {{ savingConfig ? 'Saving...' : 'Save Configuration' }}
          </button>
          
          <button @click="closeDatabaseModal" class="cancel-button">
            Cancel
          </button>
        </div>
      </div>
    </div>
    
    <!-- Backend Diagnostic Modal -->
    <div v-if="showBackendDiagnostic" class="modal-overlay" @click.self="showBackendDiagnostic = false">
      <BackendDiagnostic 
        @close="showBackendDiagnostic = false" 
        @backendChanged="handleBackendChanged"
      />
    </div>
  </div>
  
  <!-- Toast Notifications -->
  <div class="toast-container">
    <transition-group name="toast">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast"
        :class="toast.type"
      >
        <i class="fas" :class="getToastIcon(toast.type)"></i>
        <div class="toast-content">
          <div class="toast-title">{{ toast.title }}</div>
          <div v-if="toast.message" class="toast-message">{{ toast.message }}</div>
        </div>
        <button @click="removeToast(toast.id)" class="toast-close">
          <i class="fas fa-times"></i>
        </button>
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/userStore'
import { API_BASE_URL, buildApiUrl, API_ENDPOINTS, getApiBaseUrl } from '../config/api'
import { api } from '../utils/apiClient'
import { resilientApi } from '../utils/resilientRequest'
import { requestManager } from '../utils/requestManager'
import { trackAsync } from '../utils/threadManager'
import { debounce } from '../utils/performance'
import BackendDiagnostic from '../components/BackendDiagnostic.vue'

const router = useRouter()
const userStore = useUserStore()

// State
const showBackendDiagnostic = ref(false)
const statsLoading = ref(true)
const stats = ref({
  totalUsers: 0,
  activeToday: 0,
  adminUsers: 0
})


const systemHealth = ref({
  apiStatus: 'Online',
  avgResponseTime: 0,
  errorRate: 0
})

const recentActivities = ref([])

// Database configuration state
const showDatabaseModal = ref(false)
const databaseStatus = ref({
  connected: false,
  host: null,
  database: null,
  status: 'unknown'
})

// Circuit breaker to prevent overwhelming backend with failed requests
const apiFailureCount = ref({
  activities: 0,
  database: 0,
  stats: 0
})
const maxFailures = 5  // Increased threshold to be less aggressive

// Circuit breaker reset timer - allow retry after 2 minutes (reduced from 5)
setInterval(() => {
  if (apiFailureCount.value.activities >= maxFailures || 
      apiFailureCount.value.database >= maxFailures || 
      apiFailureCount.value.stats >= maxFailures) {
    
    // Reset circuit breakers more aggressively
    apiFailureCount.value.activities = Math.max(0, apiFailureCount.value.activities - 2)
    apiFailureCount.value.database = Math.max(0, apiFailureCount.value.database - 2)
    apiFailureCount.value.stats = Math.max(0, apiFailureCount.value.stats - 2)
    
    console.log('🔄 Circuit breakers reset - retrying failed endpoints')
  }
}, 120000) // 2 minutes

// Network test state
const showNetworkTestModal = ref(false)
const testingNetwork = ref(false)
const networkTestResult = ref(null)
const networkTestForm = ref({
  host: '',
  port: 3306,
  test_type: 'tcp',
  username: '',
  password: '',
  database: ''
})

// Diagnostics modal state
const showDiagnosticsModal = ref(false)
const connectionTestResult = ref(null)
const copiedDiagnostics = ref(false)
const diagnosticsResult = ref(null)
const copiedFix = ref(false)
const mismatchResolutions = ref({})
const resolvingMismatch = ref({})
const checkingBackend = ref(false)
const runningDiagnostics = ref(false)
const refreshingConnection = ref(false)

// Toast notifications
const toasts = ref([])
let toastId = 0
const storageInfo = ref({
  config_source: 'unknown',
  storage_available: false,
  directory_writable: false,
  data_directory: null
})
const databaseForm = ref({
  db_type: 'mssql',
  host: '',
  port: 1433,
  database: '',
  username: '',
  password: '',
  use_ssl: true
})
const databaseTestResult = ref(null)
const testingConnection = ref(false)
const savingConfig = ref(false)

let refreshInterval = null
let activityRefreshInterval = null

// Methods
const loadDashboardDataRaw = async () => {
  // Track the entire dashboard load operation
  await trackAsync('AdminDashboard.loadData', async () => {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    
    // Use Promise.allSettled to load data in parallel without failing if one request fails
    const results = await Promise.allSettled([
      // Load stats with resilient API client
      api.get('/api/admin/stats', {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 5000, // 5 second timeout
        cancelToken: requestManager.getCancelToken('admin-stats')
      }),
      
      // Load database config with resilient API client
      apiFailureCount.value.database < maxFailures ? 
        api.get('/api/admin/database/config', {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 5000, // 5 second timeout
          cancelToken: requestManager.getCancelToken('admin-database-config')
        }) : 
        Promise.reject(new Error('Circuit breaker open'))
    ])
    
    // Process stats result
    const [statsResult, dbConfigResult] = results
    
    if (statsResult.status === 'fulfilled' && statsResult.value) {
      const statsRes = statsResult.value
      // Handle both success response formats
      if (statsRes.data.data) {
        stats.value = statsRes.data.data
      } else {
        stats.value = statsRes.data
      }
      statsLoading.value = false
    } else if (statsResult.status === 'rejected') {
      const error = statsResult.reason
      if (error?.response?.status === 401) {
        console.log('Admin stats require authentication')
      } else if (error?.response?.status === 403) {
        console.log('Admin stats require admin privileges')
      } else if (error?.response?.status === 404) {
        console.log('Admin stats endpoint not found - OAuth may be disabled')
      } else {
        console.warn('Error loading stats:', error?.message || 'Unknown error')
      }
      // Set default values
      stats.value = { totalUsers: 0, activeToday: 0, adminUsers: 0 }
      statsLoading.value = false
    }

    // Process database config result
    if (dbConfigResult.status === 'fulfilled' && dbConfigResult.value) {
      const dbConfigRes = dbConfigResult.value
    
    if (dbConfigRes.data.success && dbConfigRes.data.data?.database) {
      const dbData = dbConfigRes.data.data.database
      databaseStatus.value = {
        connected: dbData.connected || false,
        host: dbData.host || null,
        port: dbData.port || null,
        database: dbData.database || null,
        username: dbData.username || null,
        db_type: dbData.db_type || null,
        use_ssl: dbData.use_ssl !== undefined ? dbData.use_ssl : true,
        status: dbData.status || 'unknown',
        version: dbData.version || null,
        connection_type: dbData.connection_type || 'unknown'
      }
      
      // Update storage info if available
      if (dbConfigRes.data.data?.storage_info) {
        storageInfo.value = {
          config_source: dbConfigRes.data.data.storage_info.config_source || 'unknown',
          storage_available: dbConfigRes.data.data.storage_info.storage_available || false,
          directory_writable: dbConfigRes.data.data.storage_info.directory_writable || false,
          data_directory: dbConfigRes.data.data.storage_info.data_directory || null
        }
      }
    } else {
      // No database configured
      databaseStatus.value = {
        connected: false,
        host: null,
        port: null,
        database: null,
        username: null,
        db_type: null,
        use_ssl: true,
        status: 'not_configured',
        connection_type: 'none'
      }
      
      // Reset failure count on success
      apiFailureCount.value.database = 0
    }
    } else if (dbConfigResult.status === 'rejected') {
      const error = dbConfigResult.reason
      // Increment failure count
      apiFailureCount.value.database++
      
      if (error?.message === 'Circuit breaker open') {
        // Circuit breaker is open - skip logging
        databaseStatus.value = {
          connected: false,
          host: null,
          database: null,
          status: 'circuit_breaker_open'
        }
      } else if (error?.response?.status === 404) {
        console.log('Database config endpoint not found - OAuth may be disabled')
      } else if (error?.response?.status === 401 || error?.response?.status === 403) {
        console.log('Database config requires admin authentication')
      } else if (import.meta.env.MODE === 'development' && apiFailureCount.value.database <= 2) {
        console.warn(`Database config error (${apiFailureCount.value.database}/${maxFailures}):`, error?.message || 'Unknown error')
      }
      
      // Set default values
      databaseStatus.value = {
        connected: false,
        host: null,
        database: null,
        status: 'error'
      }
    }


    // Load health and system metrics
    try {
      // First get basic health status using resilient API
      const healthRes = await resilientApi.get('/api/health', {
        timeout: 3000 // 3 second timeout
      }, 'admin-health')
    const healthData = healthRes.data
    
    // Update content database status from health endpoint
    if (healthData.content_database) {
      const contentDb = healthData.content_database
      databaseStatus.value = {
        ...databaseStatus.value,
        connected: contentDb.connected || false,
        connecting: contentDb.pool_active && !contentDb.connected,
        retryDelay: contentDb.retry_delay || 0,
        lastAttempt: contentDb.last_attempt ? new Date(contentDb.last_attempt * 1000).toLocaleString() : null
      }
    }
    
    // Then try to get detailed metrics if user is admin
    if (userStore.user?.role === 'admin') {
      try {
        const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
        const metricsRes = await api.get('/api/admin/system/metrics', {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 3000, // 3 second timeout
          cancelToken: requestManager.getCancelToken('admin-metrics')
        })
        
        if (metricsRes.data.success && metricsRes.data.data) {
          const metrics = metricsRes.data.data
          systemHealth.value = {
            apiStatus: healthData.status === 'healthy' ? 'Online' : 'Offline',
            avgResponseTime: Math.round(metrics.performance.avg_response_time || 0),
            errorRate: Math.round(metrics.performance.error_rate * 10) / 10 || 0
          }
        } else {
          // Fallback to basic health data
          systemHealth.value = {
            apiStatus: healthData.status === 'healthy' ? 'Online' : 'Offline',
            avgResponseTime: 0,
            errorRate: 0
          }
        }
      } catch (metricsError) {
        // Silently fall back to basic health data for non-critical errors
        if (metricsError.response?.status !== 404 && metricsError.response?.status !== 401) {
          console.log('Using basic health data')
        }
        // Use basic health data
        systemHealth.value = {
          apiStatus: healthData.status === 'healthy' ? 'Online' : 'Offline',
          avgResponseTime: 0,
          errorRate: 0
        }
      }
    } else {
      // Non-admin users just see basic status
      systemHealth.value = {
        apiStatus: healthData.status === 'healthy' ? 'Online' : 'Offline',
        avgResponseTime: 0,
        errorRate: 0
      }
    }
  } catch (error) {
    if (error.response?.status === 404) {
      console.log('Health endpoint not found')
    } else if (error.request) {
      console.warn('Backend server is not responding')
    } else {
      console.warn('Error checking system health:', error.message)
    }
    // If health check fails, API is likely down
    systemHealth.value = { apiStatus: 'Offline', avgResponseTime: 0, errorRate: 0 }
  }


    // Load activities (with circuit breaker)
    if (apiFailureCount.value.activities < maxFailures) {
      try {
        const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
        const activitiesRes = await api.get('/api/admin/activities', {
          headers: { Authorization: `Bearer ${token}` },
          params: {
            limit: 10  // Show last 10 activities
          },
          timeout: 5000,  // 5 second timeout
          cancelToken: requestManager.getCancelToken('admin-activities')
        })
    // Handle both response formats
    if (activitiesRes.data.success && activitiesRes.data.data) {
      recentActivities.value = activitiesRes.data.data.activities || []
    } else if (activitiesRes.data.activities) {
      recentActivities.value = activitiesRes.data.activities
    } else if (Array.isArray(activitiesRes.data)) {
      recentActivities.value = activitiesRes.data
    } else {
      recentActivities.value = []
    }
    
    // Ensure activities have proper structure
    recentActivities.value = recentActivities.value.map(activity => ({
      ...activity,
      // Map backend fields to frontend expectations
      type: activity.action || activity.type,
      timestamp: activity.created_at || activity.timestamp || new Date().toISOString(),
      userAvatar: activity.user?.avatar_url || activity.userAvatar || null,
      userName: activity.user?.display_name || activity.userName || 'Unknown User',
      description: activity.description || formatActivityDescription(activity)
    }))
    
    // Reset failure count on success
    apiFailureCount.value.activities = 0
    } catch (error) {
      // Increment failure count
      apiFailureCount.value.activities++
      
      if (error.response?.status === 429) {
        console.log('Rate limit reached for activities - will retry later')
      } else if (error.response?.status === 401 || error.response?.status === 403) {
        console.log('Activities require admin authentication')
      } else if (error.response?.status === 404) {
        if (import.meta.env.MODE === 'development') {
          console.log('Activities endpoint not found - OAuth may be disabled')
        }
      } else if (error.response?.status === 500) {
        if (import.meta.env.MODE === 'development' && apiFailureCount.value.activities <= 2) {
          console.warn(`Activities service error (${apiFailureCount.value.activities}/${maxFailures})`)
        }
      } else if (error.response) {
        if (import.meta.env.MODE === 'development' && apiFailureCount.value.activities <= 2) {
          console.warn(`Error loading activities: ${error.response.status} (${apiFailureCount.value.activities}/${maxFailures})`)
        }
      }
      // Show empty state if no activities can be loaded
      recentActivities.value = []
    }
  } else {
    // Circuit breaker is open - skip API call (suppress logging to reduce spam)
    recentActivities.value = []
  }
  
    // Activities loaded successfully
  }, {
    warningThreshold: 5000,
    timeout: 15000,
    metadata: { component: 'AdminDashboard' }
  })
}

// Create a debounced version to prevent overwhelming the backend
// Fast user stats loader for immediate feedback
const loadUserStatsOnly = async () => {
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const response = await api.get('/api/admin/stats', {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 3000, // Shorter timeout for faster feedback
      cancelToken: requestManager.getCancelToken('admin-stats-fast')
    })
    
    if (response.data) {
      const statsData = response.data.data || response.data
      stats.value = statsData
      statsLoading.value = false
    }
  } catch (error) {
    // Silently fail and let the full load handle errors
    console.debug('Fast user stats load failed, falling back to full load')
  }
}

const loadDashboardData = debounce(loadDashboardDataRaw, 1000)

const exportData = () => {
  router.push('/admin/export')
}

const viewLogs = () => {
  router.push('/admin/logs')
}

const formatLastUpdate = (timestamp) => {
  if (!timestamp) return 'Never'
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  const hours = Math.floor(diff / (1000 * 60 * 60))
  if (hours < 1) return 'Just now'
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

const formatTime = (timestamp) => {
  if (!timestamp) return 'Unknown'
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / (1000 * 60))
  if (minutes < 1) return 'Just now'
  if (minutes === 1) return '1m ago'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours === 1) return '1h ago'
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days === 1) return '1d ago'
  return `${days}d ago`
}

const formatConfigSource = (source) => {
  const sourceMap = {
    'persistent_storage': 'Persistent Storage',
    'environment_variable': 'Environment Variable',
    'config_json': 'Config File (Temporary)',
    'none': 'Not Configured',
    'unknown': 'Unknown'
  }
  return sourceMap[source] || source
}

const getActivityIcon = (type) => {
  const icons = {
    // User actions
    login: 'fas fa-sign-in-alt',
    logout: 'fas fa-sign-out-alt',
    user_login: 'fas fa-sign-in-alt',
    user_register: 'fas fa-user-plus',
    user_create: 'fas fa-user-plus',
    user_update: 'fas fa-user-edit',
    token_refresh: 'fas fa-key',
    
    
    // Scraping actions
    scrape_start: 'fas fa-download',
    scrape_complete: 'fas fa-check-circle',
    scrape_error: 'fas fa-exclamation-triangle',
    
    // Other actions
    spell_view: 'fas fa-eye',
    spell_search: 'fas fa-search',
    admin_action: 'fas fa-shield-alt',
    system_error: 'fas fa-exclamation-circle',
    api_error: 'fas fa-times-circle',
    error: 'fas fa-exclamation-triangle'
  }
  return icons[type] || 'fas fa-info-circle'
}

const isUserActivity = (type) => {
  return ['login', 'logout', 'user_login', 'user_register', 'user_create', 'user_update', 'admin_action'].includes(type)
}

const formatActivityDescription = (activity) => {
  // Format activity description from backend data
  const action = activity.action || activity.type
  const user = activity.user?.display_name || 'User'
  
  switch (action) {
    case 'login':
      return `${user} logged in`
    case 'logout':
      return `${user} logged out`
    case 'user_register':
    case 'user_create':
      return `${user} created account`
    case 'scrape_start':
      return `Started scraping ${activity.resource_type || 'data'}`
    case 'scrape_complete':
      return `Completed scraping ${activity.resource_type || 'data'}`
    case 'scrape_error':
      return `Error scraping ${activity.resource_type || 'data'}`
    default:
      return activity.description || `${action} performed`
  }
}

// Navigate to system page
const navigateToSystem = async () => {
  console.log('Navigating to system page...')
  console.log('Current user:', userStore.user)
  console.log('Is authenticated:', userStore.isAuthenticated)
  console.log('Is admin:', userStore.user?.role === 'admin')
  
  try {
    // Check if user is admin
    if (userStore.user?.role === 'admin') {
      await router.push('/admin/system')
      console.log('Navigation successful')
    } else {
      console.error('Admin access required')
      showToast('error', 'Access Denied', 'Admin access required to view system page')
    }
  } catch (err) {
    console.error('Navigation error:', err)
    showToast('error', 'Navigation Failed', 'Failed to navigate to system page')
  }
}

// Database configuration methods
const updateDefaultPort = () => {
  switch (databaseForm.value.db_type) {
    case 'mssql':
      databaseForm.value.port = 1433
      break
    case 'mysql':
      databaseForm.value.port = 3306
      break
    case 'postgresql':
      databaseForm.value.port = 5432
      break
  }
}

const openDatabaseModal = async () => {
  // Try to load stored configuration even if database is disconnected
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const configRes = await api.get('/api/admin/database/stored-config', {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 5000,
      cancelToken: requestManager.getCancelToken('get-stored-config')
    })
    
    if (configRes.data.success && configRes.data.data) {
      const config = configRes.data.data
      databaseForm.value = {
        db_type: config.database_type || 'mysql',
        host: config.host || '',
        port: config.port || (config.database_type === 'mysql' ? 3306 : config.database_type === 'mssql' ? 1433 : 5432),
        database: config.database_name || '',
        username: config.username || '',
        password: '', // Password is not returned for security
        use_ssl: config.database_ssl !== undefined ? config.database_ssl : true
      }
    } else {
      // Fallback to current status if stored config not available
      if (databaseStatus.value.db_type) {
        databaseForm.value = {
          db_type: databaseStatus.value.db_type || 'mysql',
          host: databaseStatus.value.host || '',
          port: databaseStatus.value.port || (databaseStatus.value.db_type === 'mysql' ? 3306 : databaseStatus.value.db_type === 'mssql' ? 1433 : 5432),
          database: databaseStatus.value.database || '',
          username: databaseStatus.value.username || '',
          password: '', // Password is not returned for security
          use_ssl: databaseStatus.value.use_ssl !== undefined ? databaseStatus.value.use_ssl : true
        }
      }
    }
  } catch (error) {
    console.log('Could not load stored configuration, using defaults')
  }
  
  showDatabaseModal.value = true
}

const closeDatabaseModal = () => {
  showDatabaseModal.value = false
  databaseTestResult.value = null
  // Reset form
  databaseForm.value = {
    db_type: 'mssql',
    host: '',
    port: 1433,
    database: '',
    username: '',
    password: '',
    use_ssl: true
  }
}

const testDatabaseConnection = async () => {
  testingConnection.value = true
  databaseTestResult.value = null
  
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const response = await api.post('/api/admin/database/test', {
      db_type: databaseForm.value.db_type,
      host: databaseForm.value.host,
      port: databaseForm.value.port,
      database: databaseForm.value.database,
      username: databaseForm.value.username,
      password: databaseForm.value.password,
      use_ssl: databaseForm.value.use_ssl
    }, {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 10000, // 10 second timeout for connection test
      cancelToken: requestManager.getCancelToken('db-connection-test')
    })
    
    if (response.data.success) {
      databaseTestResult.value = {
        success: true,
        message: `Connection successful! Database version: ${response.data.data.database_version.split(' ')[0]} (${response.data.data.connection_time_ms}ms)`,
        data: response.data.data
      }
    } else {
      databaseTestResult.value = {
        success: false,
        message: response.data.message || 'Connection test failed',
        error: response.data.error
      }
    }
  } catch (error) {
    console.error('Database test error:', error)
    const errorData = error.response?.data
    databaseTestResult.value = {
      success: false,
      message: errorData?.message || 'Connection test failed',
      error: errorData?.error || {
        error_type: 'network_error',
        error_message: error.message,
        details: {
          issue: 'Unable to reach server',
          suggestion: 'Check that the backend server is running and accessible'
        }
      }
    }
  } finally {
    testingConnection.value = false
  }
}

const refreshConnection = async () => {
  refreshingConnection.value = true
  showToast('Refreshing Connection', 'Attempting to reconnect to database...', 'info')
  
  try {
    // First, try to refresh the database configuration
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const dbConfigRes = await api.get('/api/admin/database/config', {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 5000,
      cancelToken: requestManager.getCancelToken('refresh-db-config')
    })
    
    if (dbConfigRes.data.success && dbConfigRes.data.data?.database) {
      const dbData = dbConfigRes.data.data.database
      
      // Update the database status
      databaseStatus.value = {
        connected: dbData.connected || false,
        host: dbData.host || null,
        port: dbData.port || null,
        database: dbData.database || null,
        username: dbData.username || null,
        db_type: dbData.db_type || null,
        use_ssl: dbData.use_ssl !== undefined ? dbData.use_ssl : true,
        status: dbData.status || 'unknown',
        version: dbData.version || null,
        connection_type: dbData.connection_type || 'unknown'
      }
      
      // Update storage info if available
      if (dbConfigRes.data.data.storage_info) {
        storageInfo.value = dbConfigRes.data.data.storage_info
      }
      
      // Force backend to reconnect by invalidating cache
      try {
        await api.post('/api/admin/database/reconnect', {}, {
          headers: { Authorization: `Bearer ${token}` },
          timeout: 5000,
          cancelToken: requestManager.getCancelToken('db-reconnect')
        })
      } catch (e) {
        // Endpoint might not exist yet, that's ok
        console.log('Reconnect endpoint not available, connection will refresh on next use')
      }
      
      // Show success message
      if (databaseStatus.value.connected) {
        showToast('Connection Refreshed', 'Successfully connected to the database', 'success')
      } else {
        showToast('Connection Failed', 'Database configuration loaded but connection failed', 'warning')
      }
    }
  } catch (error) {
    console.error('Failed to refresh connection:', error)
    
    // Provide more specific error messages
    let errorMessage = 'Failed to refresh database connection.'
    
    if (error.response) {
      // Server responded with an error
      if (error.response.status === 503) {
        errorMessage = 'Database service unavailable. The backend server may be unable to connect to the database.'
      } else if (error.response.data?.message) {
        errorMessage = error.response.data.message
      } else {
        errorMessage = `Server error: ${error.response.status}`
      }
    } else if (error.request) {
      // Request was made but no response
      errorMessage = 'Unable to reach the backend server. Please check your connection.'
    } else {
      // Something else happened
      errorMessage = error.message || 'An unexpected error occurred'
    }
    
    showToast('Connection Error', errorMessage, 'error')
    console.error('Detailed error information:', error)
  } finally {
    refreshingConnection.value = false
  }
}

const checkBackendConnectivity = async () => {
  checkingBackend.value = true
  
  try {
    const startTime = Date.now()
    // Use resilient API which will auto-discover backend if needed
    const response = await resilientApi.get('/api/health', {
      timeout: 5000 // 5 second timeout for quick check
    }, 'backend-check')
    
    const responseTime = Date.now() - startTime
    
    if (response.data) {
      showToast('Backend Online', `Backend server is reachable (${responseTime}ms response time)`, 'success')
      
      // Show additional info if available
      if (response.data.version) {
        console.log('Backend version:', response.data.version)
      }
      if (response.data.status) {
        console.log('Backend status:', response.data.status)
      }
    }
  } catch (error) {
    let errorMessage = 'Backend server is not reachable. '
    
    // Safe error handling to avoid "axios is not defined" errors
    try {
      if (error && error.message) {
        if (error.message.includes('timeout')) {
          errorMessage += 'Request timed out after 5 seconds.'
        } else if (error.message.includes('Network Error')) {
          errorMessage += 'Network error - check if the server is running.'
        } else {
          errorMessage += error.message
        }
      } else if (error && error.code === 'ERR_NETWORK') {
        errorMessage += 'Network error - check if the server is running.'
      } else if (error && error.response && error.response.status) {
        errorMessage += `Server responded with status ${error.response.status}.`
      } else {
        errorMessage += 'Unknown error occurred.'
      }
    } catch (e) {
      // If error object itself causes issues, use generic message
      errorMessage += 'Connection failed.'
      console.warn('Error while processing error object:', e)
    }
    
    showToast('Backend Offline', errorMessage, 'error')
    
    // Safe logging
    console.error('Backend connectivity check failed:')
    console.error('API Base URL:', API_BASE_URL)
    // Don't log the error object directly to avoid issues
    console.error('Error message:', error?.message || 'Unknown error')
  } finally {
    checkingBackend.value = false
  }
}

const runDiagnostics = async () => {
  runningDiagnostics.value = true
  diagnosticsResult.value = null
  showToast('Running Diagnostics', 'Performing comprehensive system checks...', 'info')
  
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const response = await api.get('/api/admin/database/diagnostics', {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 30000, // 30 second timeout for diagnostics (may need more time)
      cancelToken: requestManager.getCancelToken('database-diagnostics')
    })
    
    if (response.data.success && response.data.data) {
      const diag = response.data.data
      
      // Build diagnostic report
      let report = 'Database Diagnostics Report\n' + '='.repeat(40) + '\n\n'
      
      // Environment
      report += 'Environment:\n'
      for (const [key, value] of Object.entries(diag.environment || {})) {
        report += `  ${key}: ${value}\n`
      }
      
      // Config checks
      report += '\nConfiguration:\n'
      if (diag.config_checks) {
        report += `  Config found: ${diag.config_checks.persistent_config_found ? 'Yes' : 'No'}\n`
        if (diag.config_checks.persistent_config_found) {
          report += `  Source: ${diag.config_checks.config_source}\n`
          report += `  Host: ${diag.config_checks.host || 'N/A'}\n`
          report += `  Port: ${diag.config_checks.port || 'N/A'}\n`
          report += `  Database: ${diag.config_checks.database || 'N/A'}\n`
          report += `  Username: ${diag.config_checks.username || 'N/A'}\n`
          report += `  Has password: ${diag.config_checks.has_password ? 'Yes' : 'No'}\n`
        }
        if (diag.config_checks.error) {
          report += `  Error: ${diag.config_checks.error}\n`
        }
      }
      
      // Connection test
      report += '\nConnection Test:\n'
      if (diag.connection_test) {
        report += `  Success: ${diag.connection_test.success ? 'Yes' : 'No'}\n`
        if (diag.connection_test.success) {
          report += `  Database type: ${diag.connection_test.db_type}\n`
          report += `  Query test: ${diag.connection_test.query_test}\n`
        } else {
          report += `  Error: ${diag.connection_test.error || 'Unknown'}\n`
        }
      }
      
      // Persistent storage
      report += '\nPersistent Storage:\n'
      if (diag.persistent_storage) {
        report += `  Data directory: ${diag.persistent_storage.data_directory || 'N/A'}\n`
        report += `  Directory exists: ${diag.persistent_storage.directory_exists ? 'Yes' : 'No'}\n`
        report += `  Directory writable: ${diag.persistent_storage.directory_writable ? 'Yes' : 'No'}\n`
        report += `  Config file exists: ${diag.persistent_storage.config_file_exists ? 'Yes' : 'No'}\n`
      }
      
      // Recommendations
      if (diag.recommendations && diag.recommendations.length > 0) {
        report += '\nRecommendations:\n'
        for (const rec of diag.recommendations) {
          report += `  • ${rec}\n`
        }
      }
      
      // Store the diagnostics result for display
      diagnosticsResult.value = diag
      showToast('Diagnostics Complete', 'System diagnostic report is ready', 'success')
    } else {
      showToast('Diagnostics Failed', 'Unable to generate diagnostic report', 'error')
    }
  } catch (error) {
    console.error('Diagnostics error:', error)
    
    let errorMessage = 'Failed to run diagnostics: '
    let errorDetails = ''
    
    if (error.message && error.message.includes('timeout')) {
      errorMessage = 'Diagnostics request timed out. '
      errorDetails = 'The backend server may be slow or unresponsive. Please check:\n' +
                    '• Backend server is running\n' +
                    '• Database connection is not hanging\n' +
                    '• Network connectivity to the server'
    } else if (error.response?.data?.message) {
      errorMessage += error.response.data.message
    } else if (error.message) {
      errorMessage += error.message
    } else {
      errorMessage += 'Unknown error'
    }
    
    // Also set a partial diagnostics result with the error info
    diagnosticsResult.value = {
      error: true,
      errorMessage: errorMessage,
      errorDetails: errorDetails,
      environment: {
        frontend_url: window.location.origin,
        api_base_url: API_BASE_URL,
        timestamp: new Date().toISOString()
      }
    }
    
    showToast('Diagnostics Error', errorMessage, 'error')
  } finally {
    runningDiagnostics.value = false
  }
}

const saveDatabaseConfig = async () => {
  if (!databaseTestResult.value?.success) {
    showToast('Test Required', 'Please test the connection first before saving', 'warning')
    return
  }
  
  savingConfig.value = true
  
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const response = await api.post('/api/admin/database/config', {
      db_type: databaseForm.value.db_type,
      host: databaseForm.value.host,
      port: databaseForm.value.port,
      database: databaseForm.value.database,
      username: databaseForm.value.username,
      password: databaseForm.value.password,
      use_ssl: databaseForm.value.use_ssl
    }, {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 10000,
      cancelToken: requestManager.getCancelToken('save-db-config')
    })
    
    if (response.data.success) {
      // Update database status with all fields
      const dbData = response.data.data.database
      databaseStatus.value = {
        connected: true,
        host: dbData.host,
        port: dbData.port,
        database: dbData.database,
        username: dbData.username,
        db_type: dbData.db_type,
        use_ssl: dbData.use_ssl,
        status: 'connected',
        version: dbData.version,
        connection_type: 'config'
      }
      
      // Close modal
      closeDatabaseModal()
      
      // Show success message
      showToast('Configuration Saved', 'Database configuration saved successfully!', 'success')
      
      // Refresh dashboard data
      await loadDashboardData()
    } else {
      showToast('Save Failed', response.data.message || 'Failed to save database configuration', 'error')
    }
  } catch (error) {
    console.error('Save database config error:', error)
    showToast('Save Error', error.response?.data?.message || 'Failed to save database configuration', 'error')
  } finally {
    savingConfig.value = false
  }
}

// Remove mock data generation - we'll use real data from the API

// Toast notification functions
const showToast = (title, message = '', type = 'info') => {
  const id = ++toastId
  toasts.value.push({ id, title, message, type })
  
  // Auto-remove after 5 seconds
  setTimeout(() => {
    removeToast(id)
  }, 5000)
}

const removeToast = (id) => {
  const index = toasts.value.findIndex(t => t.id === id)
  if (index > -1) {
    toasts.value.splice(index, 1)
  }
}

const getToastIcon = (type) => {
  switch (type) {
    case 'success': return 'fa-check-circle'
    case 'error': return 'fa-exclamation-circle'
    case 'warning': return 'fa-exclamation-triangle'
    default: return 'fa-info-circle'
  }
}

// Diagnostics modal functions
const openDiagnosticsModal = () => {
  showDiagnosticsModal.value = true
  diagnosticsResult.value = null
  connectionTestResult.value = null
  copiedDiagnostics.value = false
  mismatchResolutions.value = {}
  resolvingMismatch.value = {}
}

const closeDiagnosticsModal = () => {
  showDiagnosticsModal.value = false
}

const copyDiagnostics = async () => {
  if (!diagnosticsResult.value) return
  
  try {
    await navigator.clipboard.writeText(JSON.stringify(diagnosticsResult.value, null, 2))
    copiedDiagnostics.value = true
    showToast('Copied!', 'Diagnostics report copied to clipboard', 'success')
    setTimeout(() => {
      copiedDiagnostics.value = false
    }, 2000)
  } catch (error) {
    showToast('Copy Failed', 'Unable to copy to clipboard', 'error')
  }
}

const copySuggestedFix = async () => {
  if (!diagnosticsResult.value?.config_validation?.suggested_fix?.value) return
  
  try {
    await navigator.clipboard.writeText(diagnosticsResult.value.config_validation.suggested_fix.value)
    copiedFix.value = true
    showToast('Copied!', 'Suggested fix copied to clipboard', 'success')
    setTimeout(() => {
      copiedFix.value = false
    }, 2000)
  } catch (error) {
    showToast('Copy Failed', 'Unable to copy to clipboard', 'error')
  }
}

const parseDiagnostics = (data) => {
  if (typeof data === 'string') {
    try {
      return JSON.parse(data)
    } catch {
      return { raw_data: { content: data } }
    }
  }
  return data || {}
}

const formatSectionTitle = (key) => {
  return key.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
}

const formatPropertyName = (prop) => {
  return prop.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
}

const formatValue = (value) => {
  if (typeof value === 'boolean') {
    return value ? '✓ Yes' : '✗ No'
  }
  if (value === null || value === undefined) {
    return 'Not set'
  }
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return String(value)
}

const getValueClass = (value) => {
  if (typeof value === 'boolean') {
    return value ? 'value-success' : 'value-error'
  }
  if (value === 'connected' || value === 'success' || value === 'set') {
    return 'value-success'
  }
  if (value === 'disconnected' || value === 'error' || value === 'not set') {
    return 'value-error'
  }
  return ''
}

const openNetworkTest = () => {
  closeDiagnosticsModal()
  setTimeout(() => {
    openNetworkTestModal()
  }, 300)
}

// Network test functions
const openNetworkTestModal = () => {
  showNetworkTestModal.value = true
  networkTestResult.value = null
}

const closeNetworkTestModal = () => {
  showNetworkTestModal.value = false
  networkTestResult.value = null
}

const setQuickTest = (host, port, type) => {
  networkTestForm.value.host = host
  networkTestForm.value.port = port
  networkTestForm.value.test_type = type
}

const formatTestName = (name) => {
  return name.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
}

const formatFieldName = (field) => {
  const fieldNames = {
    'host': 'Host',
    'port': 'Port',
    'database': 'Database Name',
    'username': 'Username',
    'password': 'Password',
    'database_type': 'Database Type',
    'ssl': 'SSL'
  }
  return fieldNames[field] || field.split('_').map(word => 
    word.charAt(0).toUpperCase() + word.slice(1)
  ).join(' ')
}

const highlightDifferences = (str1, str2) => {
  // Convert to strings and handle null/undefined
  const s1 = String(str1 || '')
  const s2 = String(str2 || '')
  
  // If strings are identical, return plain text
  if (s1 === s2) {
    return { str1: s1, str2: s2, hasDiff: false }
  }
  
  // For simpler visualization, use a character-by-character approach with some optimization
  let result1 = []
  let result2 = []
  
  // Find common prefix
  let prefixLen = 0
  while (prefixLen < s1.length && prefixLen < s2.length && s1[prefixLen] === s2[prefixLen]) {
    prefixLen++
  }
  
  // Find common suffix
  let suffixLen = 0
  while (suffixLen < (s1.length - prefixLen) && 
         suffixLen < (s2.length - prefixLen) && 
         s1[s1.length - 1 - suffixLen] === s2[s2.length - 1 - suffixLen]) {
    suffixLen++
  }
  
  // Add common prefix
  if (prefixLen > 0) {
    const prefix = s1.substring(0, prefixLen)
    result1.push(prefix)
    result2.push(prefix)
  }
  
  // Add different middle part
  const mid1 = s1.substring(prefixLen, s1.length - suffixLen)
  const mid2 = s2.substring(prefixLen, s2.length - suffixLen)
  
  if (mid1 || mid2) {
    // For better visualization of small differences, highlight character by character for short strings
    if (mid1.length <= 10 && mid2.length <= 10) {
      // Character-by-character comparison for short differences
      const maxLen = Math.max(mid1.length, mid2.length)
      let diff1 = []
      let diff2 = []
      
      for (let i = 0; i < maxLen; i++) {
        const c1 = i < mid1.length ? mid1[i] : ''
        const c2 = i < mid2.length ? mid2[i] : ''
        
        if (c1 === c2 && c1 !== '') {
          // Same character
          diff1.push(c1)
          diff2.push(c2)
        } else {
          // Different or missing character
          if (c1) diff1.push(`<span class="diff-highlight">${escapeHtml(c1)}</span>`)
          if (c2) diff2.push(`<span class="diff-highlight">${escapeHtml(c2)}</span>`)
        }
      }
      
      result1.push(diff1.join(''))
      result2.push(diff2.join(''))
    } else {
      // For longer differences, highlight the whole section
      if (mid1) result1.push(`<span class="diff-highlight">${escapeHtml(mid1)}</span>`)
      if (mid2) result2.push(`<span class="diff-highlight">${escapeHtml(mid2)}</span>`)
    }
  }
  
  // Add common suffix
  if (suffixLen > 0) {
    const suffix = s1.substring(s1.length - suffixLen)
    result1.push(suffix)
    result2.push(suffix)
  }
  
  return {
    str1: result1.join(''),
    str2: result2.join(''),
    hasDiff: true
  }
}

// Helper function to escape HTML
const escapeHtml = (str) => {
  const div = document.createElement('div')
  div.textContent = str
  return div.innerHTML
}

const resolveMismatch = async (field) => {
  const selectedValue = mismatchResolutions.value[field]
  console.log('Resolving mismatch for field:', field, 'with value:', selectedValue)
  console.log('All resolutions:', mismatchResolutions.value)
  console.log('Current user:', userStore.user)
  console.log('User role:', userStore.user?.role)
  
  // Check if no radio button is selected (undefined means no selection)
  if (selectedValue === undefined) {
    showToast('No Selection', 'Please select a value to save', 'warning')
    return
  }
  
  // Check if user is admin
  if (userStore.user?.role !== 'admin') {
    showToast('Admin Required', 'You must be logged in as an admin to save configuration changes', 'error')
    return
  }
  
  // selectedValue can be an empty string "" which is valid (for "Keep Empty")
  
  resolvingMismatch.value[field] = true
  
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    
    const requestData = {
      field: field,
      selected_value: selectedValue
    }
    
    console.log('Sending request to:', '/api/admin/database/resolve-mismatch')
    console.log('Request data:', requestData)
    console.log('Authorization token exists:', !!token)
    
    const response = await api.post('/api/admin/database/resolve-mismatch', requestData, {
      headers: { 
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      timeout: 10000,
      cancelToken: requestManager.getCancelToken('resolve-mismatch')
    })
    
    if (response.data.success) {
      showToast('Configuration Updated', `${formatFieldName(field)} has been synchronized across all configurations`, 'success')
      
      // Update the diagnostics result with the new validation
      if (response.data.data?.validation_result) {
        diagnosticsResult.value.config_validation = response.data.data.validation_result
      }
      
      // Clear the resolution selection for this field
      delete mismatchResolutions.value[field]
      
      // Refresh diagnostics after a short delay
      setTimeout(() => {
        runDiagnostics()
      }, 1000)
    } else {
      showToast('Resolution Failed', response.data.message || 'Failed to resolve configuration mismatch', 'error')
    }
  } catch (error) {
    console.error('Mismatch resolution error:', error)
    console.error('Error response:', error.response)
    console.error('Error details:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      headers: error.response?.headers,
      config: {
        url: error.config?.url,
        method: error.config?.method,
        data: error.config?.data,
        headers: error.config?.headers
      },
      field: field,
      selectedValue: selectedValue
    })
    
    let errorMessage = 'Failed to resolve configuration mismatch'
    if (error.response?.data?.error) {
      errorMessage = error.response.data.error
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.response?.status === 404) {
      errorMessage = 'Resolution endpoint not found. Make sure the backend is running.'
    } else if (error.response?.status === 401) {
      errorMessage = 'Authorization required. Please ensure you are logged in as admin.'
    }
    
    showToast('Resolution Error', errorMessage, 'error')
  } finally {
    resolvingMismatch.value[field] = false
  }
}

const runNetworkTest = async () => {
  testingNetwork.value = true
  networkTestResult.value = null
  
  try {
    const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
    const response = await api.post('/api/admin/network/test', {
      host: networkTestForm.value.host,
      port: networkTestForm.value.port,
      test_type: networkTestForm.value.test_type,
      username: networkTestForm.value.username,
      password: networkTestForm.value.password,
      database: networkTestForm.value.database
    }, {
      headers: { Authorization: `Bearer ${token}` },
      timeout: 15000, // 15 second timeout for network test
      cancelToken: requestManager.getCancelToken('network-test')
    })
    
    if (response.data.success) {
      networkTestResult.value = response.data.data
    } else {
      console.error('Network test failed:', response.data.message)
    }
  } catch (error) {
    console.error('Network test error:', error)
    networkTestResult.value = {
      host: networkTestForm.value.host,
      port: networkTestForm.value.port,
      overall_success: false,
      tests: {
        api_error: {
          success: false,
          error: error.message,
          message: 'Failed to run network test'
        }
      }
    }
  } finally {
    testingNetwork.value = false
  }
}

// Open backend diagnostic modal
const openBackendDiagnostic = () => {
  console.log('Opening backend diagnostic modal')
  console.log('Current showBackendDiagnostic value:', showBackendDiagnostic.value)
  showBackendDiagnostic.value = true
  console.log('New showBackendDiagnostic value:', showBackendDiagnostic.value)
}

// Handle backend URL change from diagnostic tool
const handleBackendChanged = async (newUrl) => {
  showToast('Backend Updated', `Backend URL changed to ${newUrl}`, 'success')
  
  // Reload dashboard data with new backend
  await loadDashboardData()
  
  // Close the diagnostic modal
  showBackendDiagnostic.value = false
}

// Lifecycle
onMounted(async () => {
  // Load user stats immediately for instant feedback
  loadUserStatsOnly()
  
  // Load full dashboard data (this will also update stats with complete data)
  await loadDashboardData()
  
  // Refresh dashboard data every 60 seconds (reduced from 30s to prevent overwhelming backend)
  refreshInterval = setInterval(loadDashboardData, 60000)
  
  // Refresh activities every 60 seconds to avoid rate limits
  activityRefreshInterval = setInterval(async () => {
    try {
      const token = userStore.accessToken || localStorage.getItem('accessToken') || ''
      const activitiesRes = await api.get('/api/admin/activities', {
        headers: { Authorization: `Bearer ${token}` },
        params: { limit: 10 },
        timeout: 5000,
        cancelToken: requestManager.getCancelToken('admin-activities-refresh')
      })
      
      if (activitiesRes.data.activities) {
        recentActivities.value = activitiesRes.data.activities.map(activity => ({
          ...activity,
          type: activity.action || activity.type,
          timestamp: activity.created_at || activity.timestamp || new Date().toISOString(),
          userAvatar: activity.user?.avatar_url || null,
          userName: activity.user?.display_name || 'Unknown User',
          description: activity.description || formatActivityDescription(activity)
        }))
      }
    } catch (error) {
      // Silently fail for refresh intervals to avoid console spam
      if (import.meta.env.MODE === 'development' && error.response?.status !== 500) {
        console.debug('Activity refresh failed:', error.response?.status || error.message)
      }
    }
  }, 60000) // Refresh activities every 60 seconds instead of 10
})

onUnmounted(() => {
  // Clear intervals
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  if (activityRefreshInterval) {
    clearInterval(activityRefreshInterval)
  }
  
  // Cancel any pending requests
  requestManager.cancelRequest('admin-stats')
  requestManager.cancelRequest('admin-database-config')
  requestManager.cancelRequest('admin-health')
  requestManager.cancelRequest('admin-metrics')
  requestManager.cancelRequest('admin-activities')
  requestManager.cancelRequest('admin-activities-refresh')
})

</script>

<style scoped>
@import '../style-constants.css';

.admin-dashboard {
  padding: 20px;
  padding-top: var(--header-height);
  max-width: 1400px;
  margin: 0 auto;
}

.dashboard-header {
  margin-bottom: 40px;
  margin-top: 20px; /* Add extra spacing from the top */
}

.dashboard-header h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: #666;
  font-size: 1.1rem;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 25px;
  margin-bottom: 40px;
}

.dashboard-card {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.9) 0%, rgba(45, 55, 72, 0.9) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 30px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.dashboard-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, transparent 0%, rgba(255, 255, 255, 0.02) 100%);
  pointer-events: none;
}

.dashboard-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4),
              0 0 0 1px rgba(255, 255, 255, 0.15) inset;
  border-color: rgba(255, 255, 255, 0.2);
}

.card-header {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 1.8rem;
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.2) inset;
}


.card-icon.health {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
}

.card-icon.database {
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
}

.card-icon.database.status-connected {
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
}

.card-icon.database.status-disconnected {
  background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
}

.card-icon.database.status-connecting {
  background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%);
}


.card-header h2 {
  font-size: 1.4rem;
  margin: 0;
  color: #f7fafc;
  font-weight: 700;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  letter-spacing: 0.01em;
}

.card-content {
  margin-bottom: 20px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-row.warning-row {
  background: rgba(251, 191, 36, 0.1);
  padding: 12px;
  margin: 8px -20px -20px;
  border-radius: 0 0 8px 8px;
  border: none;
  gap: 10px;
}

.warning-text {
  color: #fbbf24;
  font-size: 0.9rem;
}

.stat-label {
  color: #9ca3af;
  font-size: 0.95rem;
  font-weight: 500;
  letter-spacing: 0.02em;
}

.stat-value {
  font-weight: 700;
  font-size: 1.2rem;
  color: #f7fafc;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
}

.stat-value.success {
  color: #34d399;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}

.stat-value.warning {
  color: #fbbf24;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}

.stat-value.info {
  color: #60a5fa;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}

.stat-value.error {
  color: #f87171;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.4);
}

.stat-value.small {
  font-size: 0.9rem;
}

.card-actions {
  text-align: center;
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

.card-actions.database-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.action-button {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  text-decoration: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  border: none;
  cursor: pointer;
}

.action-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.2) 50%, transparent 100%);
  transition: left 0.5s;
}

.action-button:hover::before {
  left: 100%;
}

.action-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

/* Secondary action button style */
.action-button.secondary {
  background: linear-gradient(135deg, rgba(107, 114, 128, 0.3) 0%, rgba(75, 85, 99, 0.3) 100%);
  color: #e5e7eb;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.action-button.secondary:hover {
  background: linear-gradient(135deg, rgba(107, 114, 128, 0.5) 0%, rgba(75, 85, 99, 0.5) 100%);
  color: #f7fafc;
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}

.quick-actions {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.9) 0%, rgba(45, 55, 72, 0.9) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 35px;
  margin-bottom: 40px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
  overflow: hidden;
}

.quick-actions::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.05) 0%, transparent 70%);
  pointer-events: none;
}

.quick-actions h2 {
  margin-bottom: 24px;
  color: #f7fafc;
  font-weight: 700;
  font-size: 1.8rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.quick-action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 32px 28px;
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.05) inset;
}

/* Gradient background overlay */
.quick-action-btn::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(102, 126, 234, 0.1) 0%, transparent 70%);
  opacity: 0;
  transition: opacity 0.5s ease;
  pointer-events: none;
}

/* Icon background circle - removed as we're applying colors directly to buttons */

.quick-action-btn:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.4),
              0 0 0 1px rgba(255, 255, 255, 0.2) inset;
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(0, 0, 0, 0.4);
}

.quick-action-btn:hover::before {
  opacity: 1;
}

/* Removed hover::after as we're not using the circle anymore */

.quick-action-btn:active {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.2),
              inset 0 1px 0 rgba(255, 255, 255, 0.5);
}

.quick-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  background: rgba(0, 0, 0, 0.2);
}

.quick-action-btn:disabled:hover {
  transform: none;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1),
              inset 0 1px 0 rgba(255, 255, 255, 0.5);
  border-color: rgba(255, 255, 255, 0.3);
}

/* Button-specific gradient backgrounds */
.action-grid button:nth-child(1) {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.05) 100%);
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.action-grid button:nth-child(1):hover {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.25) 0%, rgba(16, 185, 129, 0.15) 100%);
  border-color: rgba(16, 185, 129, 0.4);
  box-shadow: 0 12px 35px rgba(16, 185, 129, 0.3),
              inset 0 0 0 1px rgba(16, 185, 129, 0.2);
}

.action-grid button:nth-child(2) {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(59, 130, 246, 0.05) 100%);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.action-grid button:nth-child(2):hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.25) 0%, rgba(59, 130, 246, 0.15) 100%);
  border-color: rgba(59, 130, 246, 0.4);
  box-shadow: 0 12px 35px rgba(59, 130, 246, 0.3),
              inset 0 0 0 1px rgba(59, 130, 246, 0.2);
}

.action-grid button:nth-child(3) {
  background: linear-gradient(135deg, rgba(251, 146, 60, 0.15) 0%, rgba(251, 146, 60, 0.05) 100%);
  border: 1px solid rgba(251, 146, 60, 0.2);
}

.action-grid button:nth-child(3):hover {
  background: linear-gradient(135deg, rgba(251, 146, 60, 0.25) 0%, rgba(251, 146, 60, 0.15) 100%);
  border-color: rgba(251, 146, 60, 0.4);
  box-shadow: 0 12px 35px rgba(251, 146, 60, 0.3),
              inset 0 0 0 1px rgba(251, 146, 60, 0.2);
}

.action-grid button:nth-child(4) {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.15) 0%, rgba(168, 85, 247, 0.05) 100%);
  border: 1px solid rgba(168, 85, 247, 0.2);
}

.action-grid button:nth-child(4):hover {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.25) 0%, rgba(168, 85, 247, 0.15) 100%);
  border-color: rgba(168, 85, 247, 0.4);
  box-shadow: 0 12px 35px rgba(168, 85, 247, 0.3),
              inset 0 0 0 1px rgba(168, 85, 247, 0.2);
}

.quick-action-btn i {
  font-size: 2.8rem;
  z-index: 1;
  transition: all 0.3s ease;
  position: relative;
  margin-bottom: 4px;
}

/* Icon colors matching button theme */
.action-grid button:nth-child(1) i {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 2px 4px rgba(16, 185, 129, 0.2));
}

.action-grid button:nth-child(2) i {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 2px 4px rgba(59, 130, 246, 0.2));
}

.action-grid button:nth-child(3) i {
  background: linear-gradient(135deg, #fb923c 0%, #f97316 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 2px 4px rgba(251, 146, 60, 0.2));
}

.action-grid button:nth-child(4) i {
  background: linear-gradient(135deg, #a855f7 0%, #9333ea 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  filter: drop-shadow(0 2px 4px rgba(168, 85, 247, 0.2));
}

.quick-action-btn:hover i {
  transform: translateY(-2px) scale(1.15);
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.15));
}

.quick-action-btn span {
  font-weight: 600;
  font-size: 1.05rem;
  color: #f7fafc;
  z-index: 1;
  transition: all 0.3s ease;
  letter-spacing: 0.02em;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.quick-action-btn:hover span {
  color: #ffffff;
  transform: translateY(1px);
}

.recent-activity {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.9) 0%, rgba(45, 55, 72, 0.9) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  padding: 35px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.recent-activity h2 {
  margin-bottom: 24px;
  color: #f7fafc;
  font-weight: 700;
  font-size: 1.8rem;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.activity-list {
  max-height: 400px;
  overflow-y: auto;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  padding: 20px;
  backdrop-filter: blur(10px);
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 15px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  width: 45px;
  height: 45px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.activity-avatar {
  width: 45px;
  height: 45px;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.2);
}

.activity-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* User action icons */
.activity-icon.login,
.activity-icon.user_login {
  background: rgba(14, 165, 233, 0.2);
  color: #38bdf8;
  border: 1px solid rgba(14, 165, 233, 0.3);
}

.activity-icon.logout {
  background: rgba(156, 163, 175, 0.2);
  color: #9ca3af;
  border: 1px solid rgba(156, 163, 175, 0.3);
}

.activity-icon.user_register,
.activity-icon.user_create {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.activity-icon.user_update {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}


/* Scraping action icons */
.activity-icon.scrape_start {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.activity-icon.scrape_complete {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.activity-icon.scrape_error {
  background: rgba(251, 146, 60, 0.2);
  color: #fb923c;
  border: 1px solid rgba(251, 146, 60, 0.3);
}

/* Other action icons */
.activity-icon.spell_view,
.activity-icon.spell_search {
  background: rgba(99, 102, 241, 0.2);
  color: #818cf8;
  border: 1px solid rgba(99, 102, 241, 0.3);
}

.activity-icon.admin_action {
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
  border: 1px solid rgba(139, 92, 246, 0.3);
}

.activity-icon.error,
.activity-icon.system_error,
.activity-icon.api_error {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

/* Add default user icon size for activities without avatars */
.activity-icon.login i,
.activity-icon.user_login i,
.activity-icon.user_register i,
.activity-icon.user_create i {
  font-size: 1.3rem;
}

.activity-content {
  flex: 1;
}

.activity-description {
  margin: 0 0 5px 0;
  font-weight: 600;
  color: #f7fafc;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.activity-time {
  color: #9ca3af;
  font-size: 0.85rem;
}

.no-activity {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
}

/* Add animation for the spinning icons */
@keyframes gentlePulse {
  0%, 100% {
    opacity: 0.8;
  }
  50% {
    opacity: 1;
  }
}

.quick-action-btn .fa-spin {
  animation: fa-spin 1s infinite linear, gentlePulse 2s infinite ease-in-out;
}

/* Database Configuration Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

.modal-content {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.95) 0%, rgba(45, 55, 72, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5),
              0 0 0 1px rgba(255, 255, 255, 0.1) inset;
  border: 1px solid rgba(255, 255, 255, 0.1);
  max-width: 500px;
  width: 100%;
  max-height: 90vh;
  overflow: visible;
  display: flex;
  flex-direction: column;
}

/* Wider modal for diagnostics */
.modal-content.diagnostics-modal {
  max-width: 900px;
  width: 95vw;
}

@media (max-width: 960px) {
  .modal-content.diagnostics-modal {
    max-width: 100%;
    width: 100%;
    margin: 10px;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 30px 30px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f7fafc;
  margin: 0;
  background: linear-gradient(135deg, #8b5cf6 0%, #a78bfa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.modal-close,
.close-button {
  background: none;
  border: none;
  color: #9ca3af;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.modal-close:hover,
.close-button:hover {
  color: #f7fafc;
  background: rgba(255, 255, 255, 0.1);
  transform: rotate(90deg);
}

.modal-body {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 0;
}

/* More compact padding for diagnostics modal */
.modal-content.diagnostics-modal .modal-body {
  padding: 20px 25px;
  width: 100%;
  box-sizing: border-box;
  overflow-y: auto;
  overflow-x: hidden;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #f7fafc;
  font-size: 0.95rem;
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  color: #f7fafc;
  font-size: 1rem;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2);
  background: rgba(0, 0, 0, 0.4);
}

.form-input::placeholder {
  color: #9ca3af;
}

.checkbox-group {
  display: flex;
  align-items: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  margin-bottom: 0;
}

.form-checkbox {
  margin-right: 12px;
  width: 18px;
  height: 18px;
  accent-color: #8b5cf6;
}

.checkbox-text {
  color: #f7fafc;
  font-weight: 500;
}

.test-result {
  margin-top: 20px;
  padding: 16px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 500;
}

.test-result.success {
  background: rgba(34, 197, 94, 0.2);
  border: 1px solid rgba(34, 197, 94, 0.3);
  color: #4ade80;
}

.test-result.error {
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #f87171;
}

.test-details {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 0.9rem;
}

.test-details p {
  margin: 6px 0;
  opacity: 0.9;
}

.error-details {
  margin-top: 15px;
  padding: 15px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  border: 1px solid rgba(255, 107, 107, 0.2);
}

.error-issue {
  margin-bottom: 10px;
  font-size: 0.95em;
  color: #ff6b6b;
}

.error-suggestion {
  margin-bottom: 10px;
  font-size: 0.9em;
  color: rgba(255, 255, 255, 0.8);
}

.error-technical {
  margin-top: 10px;
  font-size: 0.85em;
}

.error-technical summary {
  cursor: pointer;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 5px;
}

.error-technical summary:hover {
  color: rgba(255, 255, 255, 0.8);
}

.error-technical code {
  display: block;
  margin-top: 5px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85em;
  color: rgba(255, 255, 255, 0.7);
  word-wrap: break-word;
  white-space: pre-wrap;
}

.modal-footer {
  display: flex;
  gap: 16px;
  padding: 20px 30px 30px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.test-button, .save-button, .cancel-button {
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.test-button {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  flex: 1;
}

.test-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
}

.save-button {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  flex: 1;
}

.save-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3);
}

.cancel-button {
  background: linear-gradient(135deg, rgba(107, 114, 128, 0.3) 0%, rgba(75, 85, 99, 0.3) 100%);
  color: #e5e7eb;
  border: 1px solid rgba(255, 255, 255, 0.1);
  flex: 0 0 auto;
  min-width: 100px;
}

.cancel-button:hover {
  background: linear-gradient(135deg, rgba(107, 114, 128, 0.5) 0%, rgba(75, 85, 99, 0.5) 100%);
  color: #f7fafc;
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.test-button:disabled, .save-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* Secondary button styles (for Close buttons in modals) */
.secondary-button {
  padding: 12px 24px;
  background: linear-gradient(135deg, rgba(107, 114, 128, 0.3) 0%, rgba(75, 85, 99, 0.3) 100%);
  color: #e5e7eb;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: 100px;
}

.secondary-button:hover {
  background: linear-gradient(135deg, rgba(107, 114, 128, 0.5) 0%, rgba(75, 85, 99, 0.5) 100%);
  color: #f7fafc;
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* Primary button styles (for main actions in modals) */
.primary-button {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: 120px;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.primary-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.primary-button:active:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.primary-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

@media (max-width: 768px) {
  .dashboard-header h1 {
    font-size: 2rem;
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .action-grid {
    grid-template-columns: 1fr 1fr;
  }
  
  .quick-action-btn {
    padding: 15px;
  }
  
  .quick-action-btn i {
    font-size: 1.5rem;
  }
  
  .quick-action-btn span {
    font-size: 0.85rem;
  }
  
  .modal-content {
    margin: 10px;
    max-width: none;
  }
  
  .modal-header, .modal-body, .modal-footer {
    padding: 20px;
  }
  
  .modal-footer {
    flex-direction: column;
  }
}

/* Diagnostics Result Styles */
.diagnostics-result {
  margin-top: 20px;
}

.diagnostics-result .result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.diagnostics-result h3 {
  margin: 0;
  color: #f7fafc;
  font-size: 1.3rem;
  display: flex;
  align-items: center;
  gap: 10px;
}

.copy-button {
  padding: 8px 16px;
  background: linear-gradient(135deg, rgba(138, 43, 226, 0.2), rgba(138, 43, 226, 0.1));
  border: 1px solid rgba(138, 43, 226, 0.5);
  border-radius: 8px;
  color: #f7fafc;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
}

.copy-button:hover {
  background: linear-gradient(135deg, rgba(138, 43, 226, 0.3), rgba(138, 43, 226, 0.2));
  transform: translateY(-1px);
}

.result-section {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 15px;
}

.result-section h4 {
  margin: 0 0 15px 0;
  color: #8b5cf6;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.result-item:last-child {
  border-bottom: none;
}

.result-label {
  color: #9ca3af;
  font-size: 0.95rem;
  font-weight: 500;
}

.result-value {
  color: #f7fafc;
  font-size: 0.95rem;
  font-weight: 600;
  text-align: right;
}

.result-value.success {
  color: #34d399;
}

.result-value.error {
  color: #f87171;
}

.result-value.warning {
  color: #fbbf24;
}

.recommendations-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.recommendations-list li {
  padding: 10px 0;
  padding-left: 25px;
  position: relative;
  color: #fbbf24;
  line-height: 1.5;
}

.recommendations-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  font-size: 1.2rem;
}

/* Toast Notification Styles */
.toast-container {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

.toast {
  background: linear-gradient(135deg, rgba(26, 32, 44, 0.95) 0%, rgba(45, 55, 72, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-radius: 10px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
  padding: 16px 20px;
  min-width: 300px;
  max-width: 400px;
  display: flex;
  align-items: center;
  gap: 12px;
  pointer-events: all;
  border: 1px solid rgba(255, 255, 255, 0.1);
  animation: slideIn 0.3s ease-out;
}

.toast.success {
  border-color: rgba(34, 197, 94, 0.3);
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.15) 0%, rgba(16, 185, 129, 0.15) 100%);
}

.toast.error {
  border-color: rgba(239, 68, 68, 0.3);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(220, 38, 38, 0.15) 100%);
}

.toast.warning {
  border-color: rgba(251, 191, 36, 0.3);
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.15) 0%, rgba(245, 158, 11, 0.15) 100%);
}

.toast.info {
  border-color: rgba(59, 130, 246, 0.3);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(37, 99, 235, 0.15) 100%);
}

.toast-icon {
  font-size: 1.3rem;
}

.toast.success .toast-icon {
  color: #34d399;
}

.toast.error .toast-icon {
  color: #f87171;
}

.toast.warning .toast-icon {
  color: #fbbf24;
}

.toast.info .toast-icon {
  color: #60a5fa;
}

.toast-content {
  flex: 1;
}

.toast-title {
  font-weight: 600;
  color: #f7fafc;
  margin-bottom: 2px;
}

.toast-message {
  font-size: 0.9rem;
  color: #9ca3af;
  line-height: 1.4;
}

.toast-close {
  background: none;
  border: none;
  color: #9ca3af;
  cursor: pointer;
  padding: 4px;
  transition: color 0.2s;
}

.toast-close:hover {
  color: #f7fafc;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast-enter-active {
  animation: slideIn 0.3s ease-out;
}

.toast-leave-active {
  animation: slideOut 0.3s ease-in;
}

@keyframes slideOut {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}

/* Config Validation Styles */
.validation-errors, .validation-warnings {
  margin-top: 15px;
  padding: 15px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.2);
}

.validation-errors {
  border: 1px solid rgba(248, 113, 113, 0.3);
}

.validation-warnings {
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.validation-errors h5, .validation-warnings h5 {
  margin: 0 0 10px 0;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.validation-errors h5 {
  color: #f87171;
}

.validation-warnings h5 {
  color: #fbbf24;
}

.validation-errors ul, .validation-warnings ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.validation-errors li, .validation-warnings li {
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  line-height: 1.5;
}

.validation-errors li:last-child, .validation-warnings li:last-child {
  border-bottom: none;
}

.mismatch-item {
  margin-bottom: 20px;
  padding: 15px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  border: 1px solid rgba(248, 113, 113, 0.2);
}

.mismatch-header {
  margin-bottom: 15px;
}

.mismatch-header strong {
  color: #f87171;
  display: block;
  margin-bottom: 5px;
  font-size: 1.1rem;
}

.mismatch-description {
  color: #9ca3af;
  font-size: 0.9rem;
}

.mismatch-info {
  margin-top: 10px;
  display: flex;
  gap: 10px;
}

.info-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.info-badge.case-diff {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.info-badge.typo-likely {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.info-badge.major-diff {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.mismatch-resolution {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.mismatch-option {
  display: flex;
  align-items: center;
  padding: 10px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  transition: all 0.2s;
}

.mismatch-option:hover {
  border-color: rgba(59, 130, 246, 0.3);
  background: rgba(59, 130, 246, 0.05);
}

.mismatch-option input[type="radio"] {
  margin-right: 10px;
  cursor: pointer;
}

.mismatch-option label {
  flex: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
}

.option-source {
  color: #60a5fa;
  font-weight: 600;
  min-width: 150px;
}

.mismatch-option code {
  font-family: monospace;
  color: #fde68a;
  background: rgba(0, 0, 0, 0.4);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.9rem;
  line-height: 1.4;
  word-break: break-all;
}

/* Diff highlighting styles */
.diff-highlight {
  background: rgba(239, 68, 68, 0.3);
  color: #fca5a5;
  padding: 2px 4px;
  border-radius: 3px;
  font-weight: 600;
  border: 1px solid rgba(239, 68, 68, 0.5);
  margin: 0 1px;
}

.mismatch-option:hover .diff-highlight {
  background: rgba(239, 68, 68, 0.4);
  border-color: rgba(239, 68, 68, 0.7);
}

/* Selected option styling */
.mismatch-option input[type="radio"]:checked + label {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.5);
}

.mismatch-option input[type="radio"]:checked + label code {
  background: rgba(59, 130, 246, 0.2);
}

.resolve-button {
  margin-top: 10px;
  background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
}

.resolve-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.resolve-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.validation-errors li.error {
  color: #fca5a5;
}

.validation-warnings li.warning {
  color: #fde68a;
}

.mismatch-values {
  display: block;
  font-size: 0.85rem;
  color: #9ca3af;
  margin-top: 4px;
  font-family: monospace;
}

.config-comparison {
  margin-top: 20px;
}

.config-comparison h5 {
  margin: 0 0 15px 0;
  font-size: 1rem;
  color: #e2e8f0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  overflow: hidden;
}

.comparison-table th {
  background: rgba(255, 255, 255, 0.05);
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #e2e8f0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.comparison-table td {
  padding: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  color: #9ca3af;
}

.comparison-table tr:last-child td {
  border-bottom: none;
}

.comparison-table td:last-child {
  text-align: center;
}

.suggested-fix {
  margin-top: 20px;
  padding: 15px;
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 10px;
}

.suggested-fix h5 {
  margin: 0 0 10px 0;
  font-size: 1rem;
  color: #60a5fa;
  display: flex;
  align-items: center;
  gap: 8px;
}

.fix-details p {
  margin: 8px 0;
  color: #e2e8f0;
}

.fix-details strong {
  color: #60a5fa;
}

.fix-command {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
}

.fix-command code {
  flex: 1;
  font-family: monospace;
  font-size: 0.9rem;
  color: #fde68a;
  word-break: break-all;
}

.fix-command .copy-button {
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.3);
  color: #60a5fa;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.85rem;
  white-space: nowrap;
}

.fix-command .copy-button:hover {
  background: rgba(59, 130, 246, 0.3);
  border-color: rgba(59, 130, 246, 0.5);
}

/* Network Test Modal Styles */
.quick-tests {
  margin: 20px 0;
  padding: 15px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.quick-tests p {
  margin: 0 0 10px 0;
  font-weight: bold;
  color: var(--primary);
}

.quick-test-btn {
  margin: 5px;
  padding: 8px 16px;
  background: rgba(138, 43, 226, 0.2);
  border: 1px solid var(--primary);
  border-radius: 4px;
  color: var(--text);
  cursor: pointer;
  transition: all 0.3s ease;
}

.quick-test-btn:hover {
  background: rgba(138, 43, 226, 0.3);
  transform: translateY(-1px);
}

.test-results {
  margin-top: 20px;
  padding: 20px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.05);
}

.test-results.success {
  border: 1px solid #4caf50;
}

.test-results.error {
  border: 1px solid #f44336;
}

.test-results h3 {
  margin: 0 0 15px 0;
  color: var(--primary);
}

.test-item {
  margin: 10px 0;
  padding: 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.test-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
}

.test-header .fa-check-circle {
  color: #4caf50;
}

.test-header .fa-times-circle {
  color: #f44336;
}

.test-time {
  margin-left: auto;
  font-size: 0.9em;
  color: #888;
}

.test-message {
  margin: 5px 0;
  font-size: 0.95em;
}

.test-error {
  margin: 5px 0;
  color: #ff6b6b;
  font-size: 0.9em;
}

.test-detail {
  margin: 5px 0;
  color: #888;
  font-size: 0.9em;
  font-family: monospace;
}

/* Diagnostics Modal Styles */
.modal-content.diagnostics-modal {
  overflow: visible;
}

.diagnostic-tests {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  margin: 20px 0;
}

.test-card {
  padding: 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(138, 43, 226, 0.3);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.test-card:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--primary);
  transform: translateY(-2px);
}

.test-card .test-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 10px;
}

.test-card .test-header i {
  font-size: 24px;
  color: var(--primary);
}

.test-card h3 {
  margin: 0;
  color: var(--primary);
  font-size: 1.2em;
}

.test-card p {
  margin: 10px 0 15px 0;
  color: #ccc;
  line-height: 1.5;
}

.test-button {
  padding: 10px 20px;
  background: rgba(138, 43, 226, 0.2);
  border: 1px solid var(--primary);
  border-radius: 4px;
  color: var(--text);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.test-button:hover {
  background: rgba(138, 43, 226, 0.3);
  transform: translateY(-1px);
}

.test-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.diagnostics-result {
  margin-top: 30px;
  padding: 20px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.diagnostics-result h3 {
  margin: 0 0 15px 0;
  color: var(--primary);
}

.result-content {
  background: rgba(0, 0, 0, 0.5);
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
}

.result-content pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 0.9em;
  color: #ddd;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.connection-result {
  margin-top: 20px;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid;
}

.connection-result.success {
  background: rgba(76, 175, 80, 0.1);
  border-color: #4caf50;
}

.connection-result.error {
  background: rgba(244, 67, 54, 0.1);
  border-color: #f44336;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.result-header i {
  font-size: 20px;
}

.result-header .fa-check-circle {
  color: #4caf50;
}

.result-header .fa-times-circle {
  color: #f44336;
}

.result-details {
  color: #ccc;
  font-size: 0.95em;
  line-height: 1.5;
}

/* Update database actions to prevent cramping */
.database-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.database-actions .action-button {
  flex: 1;
  min-width: 120px;
}

/* Backend diagnostic button styling */
.backend-diagnostic-btn {
  background: linear-gradient(135deg, rgba(147, 51, 234, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%) !important;
  border: 1px solid rgba(147, 51, 234, 0.4) !important;
  color: #e9d5ff !important;
  font-weight: 600;
  transition: all 0.3s ease;
  padding: 12px 20px !important;
  min-width: 130px;
}

.backend-diagnostic-btn:hover {
  background: linear-gradient(135deg, rgba(147, 51, 234, 0.3) 0%, rgba(139, 92, 246, 0.3) 100%) !important;
  border-color: rgba(147, 51, 234, 0.6) !important;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(147, 51, 234, 0.3);
  color: #f3e8ff !important;
}

.backend-diagnostic-btn i {
  font-size: 1rem;
  color: #e9d5ff;
}


/* Refined Diagnostics Modal Styles */
.modal-content.diagnostics-modal .modal-body {
  max-height: 70vh;
  overflow-y: auto;
  overflow-x: hidden;
  width: 100%;
  box-sizing: border-box;
}

.diagnostic-tests {
  display: grid;
  grid-template-columns: 1fr;
  gap: 15px;
  margin: 20px 0;
}

.test-card {
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(138, 43, 226, 0.2);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.test-card:hover {
  background: rgba(138, 43, 226, 0.05);
  border-color: rgba(138, 43, 226, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(138, 43, 226, 0.2);
}

.test-button {
  padding: 10px 20px;
  background: linear-gradient(135deg, rgba(138, 43, 226, 0.2), rgba(138, 43, 226, 0.1));
  border: 1px solid rgba(138, 43, 226, 0.5);
  border-radius: 8px;
  color: var(--text);
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.test-button:hover {
  background: linear-gradient(135deg, rgba(138, 43, 226, 0.3), rgba(138, 43, 226, 0.2));
  border-color: var(--primary);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(138, 43, 226, 0.3);
}

/* Diagnostics Result Styles */
.diagnostics-result {
  margin-top: 30px;
  padding: 0;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;
  border: 1px solid rgba(138, 43, 226, 0.2);
  overflow: hidden;
}

.diagnostics-result .result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: rgba(138, 43, 226, 0.1);
  border-bottom: 1px solid rgba(138, 43, 226, 0.2);
}

.diagnostics-result h3 {
  margin: 0;
  color: var(--primary);
  display: flex;
  align-items: center;
  gap: 10px;
}

.copy-button {
  padding: 8px 16px;
  background: rgba(138, 43, 226, 0.2);
  border: 1px solid rgba(138, 43, 226, 0.5);
  border-radius: 6px;
  color: var(--text);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9em;
}

.copy-button:hover {
  background: rgba(138, 43, 226, 0.3);
  transform: translateY(-1px);
}

.result-sections {
  padding: 20px;
}

.result-section {
  margin-bottom: 20px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.result-section h4 {
  margin: 0 0 15px 0;
  color: var(--primary);
  font-size: 1.1em;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(138, 43, 226, 0.2);
}

.section-content {
  display: grid;
  gap: 10px;
}

.result-item {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 15px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.result-item:last-child {
  border-bottom: none;
}

.result-label {
  color: #aaa;
  font-weight: 500;
}

.result-value {
  color: #fff;
  word-break: break-word;
}

.value-success {
  color: #4caf50;
}

.value-error {
  color: #f44336;
}

/* Toast Notification Styles */
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px 20px;
  background: rgba(30, 30, 40, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  pointer-events: all;
  min-width: 300px;
  max-width: 500px;
  animation: slideIn 0.3s ease;
}

.toast.success {
  border-color: #4caf50;
  background: rgba(30, 40, 30, 0.95);
}

.toast.error {
  border-color: #f44336;
  background: rgba(40, 30, 30, 0.95);
}

.toast.warning {
  border-color: #ff9800;
  background: rgba(40, 35, 30, 0.95);
}

.toast.info {
  border-color: #2196f3;
  background: rgba(30, 35, 40, 0.95);
}

.toast i {
  font-size: 20px;
  margin-top: 2px;
}

.toast.success i { color: #4caf50; }
.toast.error i { color: #f44336; }
.toast.warning i { color: #ff9800; }
.toast.info i { color: #2196f3; }

.toast-content {
  flex: 1;
}

.toast-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.toast-message {
  font-size: 0.9em;
  color: #ccc;
  line-height: 1.4;
}

.toast-close {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 0;
  margin-left: 10px;
  transition: color 0.3s ease;
}

.toast-close:hover {
  color: #fff;
}

/* Toast animations */
.toast-enter-active {
  animation: slideIn 0.3s ease;
}

.toast-leave-active {
  animation: slideOut 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes slideOut {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}

/* Network Test Modal Polish */
.quick-tests {
  background: rgba(138, 43, 226, 0.05);
  border: 1px solid rgba(138, 43, 226, 0.2);
  border-radius: 8px;
}

.quick-test-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 0.9em;
}

.quick-test-btn:hover {
  background: rgba(138, 43, 226, 0.2);
  border-color: rgba(138, 43, 226, 0.5);
}

.test-results {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(138, 43, 226, 0.2);
}

.test-results.success {
  background: rgba(76, 175, 80, 0.05);
}

.test-results.error {
  background: rgba(244, 67, 54, 0.05);
}

/* Configuration Validation Styles */
.validation-errors {
  margin-top: 15px;
}

.validation-errors h5 {
  color: #f87171;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.mismatch-item {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
}

.mismatch-header {
  margin-bottom: 15px;
}

.mismatch-header strong {
  color: #f7fafc;
  font-size: 1.1em;
}

.mismatch-description {
  color: #9ca3af;
  display: block;
  margin-top: 5px;
  font-size: 0.9em;
}

.mismatch-info {
  margin-top: 10px;
}

.info-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 0.85em;
  font-weight: 500;
}

.info-badge.case-diff {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.info-badge.typo-likely {
  background: rgba(251, 146, 60, 0.2);
  color: #fb923c;
  border: 1px solid rgba(251, 146, 60, 0.3);
}

.info-badge.major-diff {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.mismatch-resolution {
  margin-top: 15px;
  padding: 0;
  width: 100%;
  box-sizing: border-box;
}

/* Old mismatch-option styles removed - using resolution-option instead */

/* Resolution options layout */
.resolution-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 15px;
  width: 100%;
  max-width: 100%;
}

.resolution-option {
  display: flex;
  align-items: flex-start;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 6px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 100%;
  box-sizing: border-box;
  margin: 0;
}

.resolution-option:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.3);
}

.resolution-option.selected {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.6);
  box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.3) inset;
}

.resolution-option input[type="radio"] {
  margin-right: 12px;
  margin-top: 2px;
  accent-color: #8b5cf6;
  cursor: pointer;
}

.option-content {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.option-label {
  display: block;
  color: #9ca3af;
  font-weight: 500;
  font-size: 0.9em;
  margin-bottom: 4px;
}

.option-value {
  display: block;
  background: rgba(0, 0, 0, 0.5);
  padding: 6px 10px;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8em;
  color: #f7fafc;
  word-break: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
  white-space: pre-wrap;
}

/* Diff highlighting */
.diff-highlight {
  background: rgba(251, 146, 60, 0.3);
  color: #fbbf24;
  padding: 2px 4px;
  border-radius: 2px;
  font-weight: 600;
}

.resolve-button {
  margin-top: 15px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.resolve-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
}

.resolve-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Configuration Comparison Table */
.config-comparison {
  margin-top: 20px;
}

.config-comparison h5 {
  color: #a78bfa;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  overflow: hidden;
  table-layout: fixed;
}

.comparison-table th {
  background: rgba(139, 92, 246, 0.2);
  color: #f7fafc;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  border-bottom: 1px solid rgba(139, 92, 246, 0.3);
}

.comparison-table td {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  color: #e5e7eb;
  word-break: break-word;
  overflow-wrap: break-word;
}

.comparison-table td code {
  background: rgba(0, 0, 0, 0.3);
  padding: 4px 8px;
  word-break: break-all;
  display: inline-block;
  max-width: 100%;
  border-radius: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9em;
  color: #f7fafc;
}

.comparison-table tr:last-child td {
  border-bottom: none;
}

.comparison-table .success {
  color: #4ade80;
}

.comparison-table .error {
  color: #f87171;
}

/* Validation warnings */
.validation-warnings {
  margin-top: 20px;
  background: rgba(251, 146, 60, 0.1);
  border: 1px solid rgba(251, 146, 60, 0.3);
  border-radius: 8px;
  padding: 15px;
  width: 100%;
  box-sizing: border-box;
}

.validation-warnings h5 {
  color: #fb923c;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.validation-warnings ul {
  margin: 0;
  padding-left: 20px;
}

.validation-warnings .warning {
  color: #fbbf24;
  margin-bottom: 8px;
}

.warning-item {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(251, 146, 60, 0.3);
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  overflow: hidden;
  max-width: 100%;
}

.warning-header {
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 15px;
  flex-wrap: wrap;
}

.warning-header strong {
  color: #fb923c;
  display: block;
  margin-bottom: 5px;
  font-size: 1.05em;
}

.warning-message {
  color: #fbbf24;
  font-size: 0.9em;
  line-height: 1.4;
  max-width: 400px;
  word-break: break-word;
}

/* Suggested fix section */
.suggested-fix {
  margin-top: 20px;
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 8px;
  padding: 15px;
}

.suggested-fix h5 {
  color: #4ade80;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.fix-details p {
  margin: 8px 0;
  color: #e5e7eb;
}

.fix-details strong {
  color: #f7fafc;
}

.fix-command {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 15px;
  background: rgba(0, 0, 0, 0.5);
  padding: 12px;
  border-radius: 6px;
}

.fix-command code {
  flex: 1;
  font-family: 'JetBrains Mono', monospace;
  color: #4ade80;
  font-size: 0.9em;
}

/* Loading states for user management card */
.stat-value.loading {
  opacity: 0.6;
}

.skeleton-text {
  display: inline-block;
  background: linear-gradient(90deg, 
    rgba(255, 255, 255, 0.1) 25%, 
    rgba(255, 255, 255, 0.3) 50%, 
    rgba(255, 255, 255, 0.1) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
  min-width: 20px;
  height: 1em;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}
</style>
