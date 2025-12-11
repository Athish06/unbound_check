import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include API key
apiClient.interceptors.request.use(
  (config) => {
    const apiKey = localStorage.getItem('unbound_key');
    if (apiKey) {
      config.headers['X-API-Key'] = apiKey;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear invalid credentials
      localStorage.removeItem('unbound_key');
      localStorage.removeItem('unbound_user');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

export const api = {
  // ============ Authentication ============

  async verifyApiKey(apiKey) {
    const response = await axios.post(
      `${API_BASE}/auth/verify`,
      {},
      {
        headers: { 'X-API-Key': apiKey }
      }
    );
    return response.data;
  },

  // ============ Users ============

  async getAllUsers() {
    const response = await apiClient.get('/users');
    return response.data;
  },

  async createUser(userData) {
    const response = await apiClient.post('/users', userData);
    return response.data;
  },

  async updateUserCredits(userId, credits) {
    const response = await apiClient.put(`/users/${userId}/credits`, { credits });
    return response.data;
  },

  async deleteUser(userId) {
    const response = await apiClient.delete(`/users/${userId}`);
    return response.data;
  },

  // ============ Rules ============

  async getRules() {
    const response = await apiClient.get('/rules');
    return response.data;
  },

  async createRule(ruleData) {
    const response = await apiClient.post('/rules', ruleData);
    return response.data;
  },

  async deleteRule(ruleId) {
    const response = await apiClient.delete(`/rules/${ruleId}`);
    return response.data;
  },

  async updateRule(ruleId, ruleData) {
    const response = await apiClient.put(`/rules/${ruleId}`, ruleData);
    return response.data;
  },

  // ============ Commands ============

  async executeCommand(commandText) {
    const response = await apiClient.post('/commands/execute', {
      command_text: commandText
    });
    return response.data;
  },

  async getCommandHistory(isAdmin = false) {
    const response = await apiClient.get('/commands/history', {
      params: { admin_view: isAdmin }
    });
    return response.data;
  }
};

export default api;
