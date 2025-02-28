<template>
  <div class="log-stream">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">Operation Logs</h5>
        <div class="controls">
          <div class="form-check form-check-inline">
            <input class="form-check-input" type="checkbox" id="auto-scroll" v-model="autoScroll">
            <label class="form-check-label" for="auto-scroll">Auto-scroll</label>
          </div>
          <button class="btn btn-sm btn-outline-secondary ms-2" @click="clearLogs">Clear</button>
        </div>
      </div>
      <div class="card-body p-0">
        <div class="log-filters p-2 border-bottom">
          <div class="row">
            <div class="col-md-4">
              <div class="form-group">
                <label for="level-filter" class="form-label">Level</label>
                <select class="form-select form-select-sm" id="level-filter" v-model="levelFilter">
                  <option value="all">All Levels</option>
                  <option value="info">Info</option>
                  <option value="warning">Warning</option>
                  <option value="error">Error</option>
                </select>
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label for="operation-filter" class="form-label">Operation</label>
                <select class="form-select form-select-sm" id="operation-filter" v-model="operationFilter">
                  <option value="all">All Operations</option>
                  <option value="system">System</option>
                  <option value="crawl">Crawl</option>
                  <option value="gather">Gather</option>
                  <option value="analyze">Analyze</option>
                </select>
              </div>
            </div>
            <div class="col-md-4">
              <div class="form-group">
                <label for="search-filter" class="form-label">Search</label>
                <input type="text" class="form-control form-control-sm" id="search-filter" v-model="searchFilter" placeholder="Filter logs...">
              </div>
            </div>
          </div>
        </div>
        <div class="log-container" ref="logContainer">
          <div v-if="filteredLogs.length === 0" class="text-center p-3 text-muted">
            No logs to display
          </div>
          <div v-else class="log-entries">
            <div 
              v-for="(log, index) in filteredLogs" 
              :key="index" 
              class="log-entry p-2" 
              :class="getLogClass(log)"
            >
              <div class="log-timestamp">{{ formatTimestamp(log.timestamp) }}</div>
              <div class="log-level">
                <span class="badge" :class="getLevelBadgeClass(log.level)">{{ log.level }}</span>
              </div>
              <div class="log-operation">
                <span class="badge bg-secondary">{{ log.operation }}</span>
              </div>
              <div class="log-message">{{ log.message }}</div>
              <div v-if="log.entity_id" class="log-entity">
                <small class="text-muted">Entity: {{ log.entity_id }}</small>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LogStream',
  props: {
    operationTypes: {
      type: Array,
      default: () => ['system', 'crawl', 'gather', 'analyze']
    },
    maxLogs: {
      type: Number,
      default: 1000
    }
  },
  data() {
    return {
      logs: [],
      socket: null,
      connected: false,
      autoScroll: true,
      levelFilter: 'all',
      operationFilter: 'all',
      searchFilter: '',
      reconnectAttempts: 0,
      maxReconnectAttempts: 5,
      reconnectTimeout: null
    }
  },
  computed: {
    filteredLogs() {
      return this.logs.filter(log => {
        // Filter by level
        if (this.levelFilter !== 'all' && log.level !== this.levelFilter) {
          return false;
        }
        
        // Filter by operation
        if (this.operationFilter !== 'all' && log.operation !== this.operationFilter) {
          return false;
        }
        
        // Filter by search text
        if (this.searchFilter && !log.message.toLowerCase().includes(this.searchFilter.toLowerCase())) {
          return false;
        }
        
        return true;
      });
    }
  },
  watch: {
    filteredLogs() {
      if (this.autoScroll) {
        this.$nextTick(() => {
          this.scrollToBottom();
        });
      }
    }
  },
  mounted() {
    this.connectWebSocket();
  },
  beforeUnmount() {
    this.disconnectWebSocket();
  },
  methods: {
    connectWebSocket() {
      // Close existing socket if any
      if (this.socket) {
        this.socket.close();
      }
      
      // Create a new WebSocket connection using a relative URL
      // This will go through the Vue.js proxy
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/ws`;
      
      console.log('Connecting to WebSocket at:', wsUrl);
      
      this.socket = new WebSocket(wsUrl);
      
      // Set up event handlers
      this.socket.onopen = this.handleSocketOpen;
      this.socket.onmessage = this.handleSocketMessage;
      this.socket.onclose = this.handleSocketClose;
      this.socket.onerror = this.handleSocketError;
    },
    
    disconnectWebSocket() {
      if (this.socket) {
        this.socket.close();
        this.socket = null;
      }
      
      if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = null;
      }
    },
    
    handleSocketOpen() {
      console.log('WebSocket connected');
      this.connected = true;
      this.reconnectAttempts = 0;
      
      // Add a system log
      this.addLog({
        timestamp: new Date().toISOString(),
        message: 'Connected to log stream',
        level: 'info',
        operation: 'system',
        entity_id: null
      });
    },
    
    handleSocketMessage(event) {
      try {
        const logMessage = JSON.parse(event.data);
        this.addLog(logMessage);
      } catch (error) {
        console.error('Error parsing log message:', error);
      }
    },
    
    handleSocketClose(event) {
      console.log('WebSocket disconnected:', event.code, event.reason);
      this.connected = false;
      
      // Add a system log
      this.addLog({
        timestamp: new Date().toISOString(),
        message: `Disconnected from log stream: ${event.reason || 'Connection closed'}`,
        level: 'warning',
        operation: 'system',
        entity_id: null
      });
      
      // Try to reconnect
      this.attemptReconnect();
    },
    
    handleSocketError(error) {
      console.error('WebSocket error:', error);
      
      // Get detailed error information
      let errorMessage = 'Unknown error';
      if (error) {
        if (error.message) {
          errorMessage = error.message;
        } else if (typeof error === 'string') {
          errorMessage = error;
        } else {
          try {
            errorMessage = JSON.stringify(error);
          } catch (e) {
            errorMessage = 'Error object could not be stringified';
          }
        }
      }
      
      console.log('WebSocket connection details:', {
        url: this.socket ? this.socket.url : 'No socket',
        protocol: window.location.protocol,
        host: window.location.host,
        readyState: this.socket ? this.socket.readyState : 'No socket'
      });
      
      // Add a system log
      this.addLog({
        timestamp: new Date().toISOString(),
        message: `WebSocket error: ${errorMessage}`,
        level: 'error',
        operation: 'system',
        entity_id: null
      });
    },
    
    attemptReconnect() {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
        
        this.addLog({
          timestamp: new Date().toISOString(),
          message: `Attempting to reconnect in ${delay / 1000} seconds (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`,
          level: 'info',
          operation: 'system',
          entity_id: null
        });
        
        this.reconnectTimeout = setTimeout(() => {
          this.connectWebSocket();
        }, delay);
      } else {
        this.addLog({
          timestamp: new Date().toISOString(),
          message: `Failed to reconnect after ${this.maxReconnectAttempts} attempts`,
          level: 'error',
          operation: 'system',
          entity_id: null
        });
      }
    },
    
    addLog(log) {
      this.logs.push(log);
      
      // Trim logs if needed
      if (this.logs.length > this.maxLogs) {
        this.logs = this.logs.slice(-this.maxLogs);
      }
      
      // Scroll to bottom if auto-scroll is enabled
      if (this.autoScroll) {
        this.$nextTick(() => {
          this.scrollToBottom();
        });
      }
    },
    
    clearLogs() {
      this.logs = [];
    },
    
    scrollToBottom() {
      const container = this.$refs.logContainer;
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    },
    
    formatTimestamp(timestamp) {
      try {
        const date = new Date(timestamp);
        return date.toLocaleTimeString();
      } catch (error) {
        return timestamp;
      }
    },
    
    getLogClass(log) {
      return {
        'log-info': log.level === 'info',
        'log-warning': log.level === 'warning',
        'log-error': log.level === 'error',
        'log-system': log.operation === 'system',
        'log-crawl': log.operation === 'crawl',
        'log-gather': log.operation === 'gather',
        'log-analyze': log.operation === 'analyze'
      };
    },
    
    getLevelBadgeClass(level) {
      switch (level) {
        case 'info':
          return 'bg-info';
        case 'warning':
          return 'bg-warning';
        case 'error':
          return 'bg-danger';
        default:
          return 'bg-secondary';
      }
    }
  }
}
</script>

<style scoped>
.log-stream {
  margin-bottom: 1rem;
}

.log-container {
  height: 300px;
  overflow-y: auto;
  background-color: #f8f9fa;
  font-family: monospace;
  font-size: 0.9rem;
}

.log-entries {
  padding: 0.5rem;
}

.log-entry {
  margin-bottom: 0.25rem;
  border-bottom: 1px solid #eee;
  display: grid;
  grid-template-columns: 80px 60px 80px 1fr;
  grid-gap: 0.5rem;
  align-items: start;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-timestamp {
  color: #666;
  font-size: 0.8rem;
}

.log-message {
  word-break: break-word;
}

.log-entity {
  grid-column: 1 / span 4;
  margin-top: 0.25rem;
}

.log-info {
  background-color: rgba(13, 202, 240, 0.05);
}

.log-warning {
  background-color: rgba(255, 193, 7, 0.1);
}

.log-error {
  background-color: rgba(220, 53, 69, 0.1);
}

.log-filters {
  background-color: #f8f9fa;
}
</style>
