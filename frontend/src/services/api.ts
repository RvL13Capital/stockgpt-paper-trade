import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Authentication API
export const authAPI = {
  login: async (email: string, otp: string) => {
    const response = await api.post('/auth/login', { email, otp })
    return response.data
  },

  requestOTP: async (email: string) => {
    const response = await api.post('/auth/request-otp', { email })
    return response.data
  },

  logout: async () => {
    const response = await api.post('/auth/logout')
    return response.data
  },

  verifyToken: async () => {
    const response = await api.get('/auth/verify-token')
    return response.data
  },
}

// Stocks API
export const stocksAPI = {
  getStocks: async (params?: { skip?: number; limit?: number; sector?: string; search?: string }) => {
    const response = await api.get('/stocks', { params })
    return response.data
  },

  getStockPrices: async (symbol: string, params?: { start_date?: string; end_date?: string; limit?: number }) => {
    const response = await api.get(`/stocks/${symbol}/prices`, { params })
    return response.data
  },

  getStockFeatures: async (symbol: string, params?: { start_date?: string; end_date?: string; limit?: number }) => {
    const response = await api.get(`/stocks/${symbol}/features`, { params })
    return response.data
  },

  getLatestPrice: async (symbol: string) => {
    const response = await api.get(`/stocks/${symbol}/latest`)
    return response.data
  },

  getSectors: async () => {
    const response = await api.get('/stocks/sectors')
    return response.data
  },

  getIndustries: async () => {
    const response = await api.get('/stocks/industries')
    return response.data
  },
}

// Signals API
export const signalsAPI = {
  getSignals: async (params?: {
    symbol?: string
    action?: string
    confidence_min?: number
    confidence_max?: number
    sector?: string
    limit?: number
    skip?: number
  }) => {
    const response = await api.get('/signals', { params })
    return response.data
  },

  getSignalDetails: async (signal_id: number) => {
    const response = await api.get(`/signals/${signal_id}`)
    return response.data
  },

  takeSignalAction: async (signal_id: number, action: string, notes?: string) => {
    const response = await api.post(`/signals/${signal_id}/action`, { action, notes })
    return response.data
  },

  getPerformanceSummary: async () => {
    const response = await api.get('/signals/performance/summary')
    return response.data
  },
}

// Portfolio API
export const portfolioAPI = {
  getSummary: async () => {
    const response = await api.get('/portfolio/summary')
    return response.data
  },

  getPositions: async (params?: { symbol?: string; sector?: string; status?: string }) => {
    const response = await api.get('/portfolio/positions', { params })
    return response.data
  },

  getPositionDetails: async (position_id: number) => {
    const response = await api.get(`/portfolio/positions/${position_id}`)
    return response.data
  },

  getAllocation: async () => {
    const response = await api.get('/portfolio/allocation')
    return response.data
  },

  getPerformance: async (period?: string) => {
    const response = await api.get('/portfolio/performance', { params: { period } })
    return response.data
  },

  createPosition: async (symbol: string, quantity: number, price: number) => {
    const response = await api.post('/portfolio/positions', { symbol, quantity, price })
    return response.data
  },

  updatePosition: async (position_id: number, params: { target_price?: number; stop_loss?: number; notes?: string }) => {
    const response = await api.put(`/portfolio/positions/${position_id}`, params)
    return response.data
  },

  closePosition: async (position_id: number) => {
    const response = await api.delete(`/portfolio/positions/${position_id}`)
    return response.data
  },
}

// Data API
export const dataAPI = {
  ingestStockData: async (symbols: string[], days_back?: number, background?: boolean) => {
    const response = await api.post('/data/ingest/stocks', symbols, { params: { days_back, background } })
    return response.data
  },

  updateStockList: async (background?: boolean) => {
    const response = await api.post('/data/ingest/stock-list', { params: { background } })
    return response.data
  },

  getAvailableSymbols: async (limit?: number) => {
    const response = await api.get('/data/symbols/available', { params: { limit } })
    return response.data
  },

  runScheduledIngestion: async (background?: boolean) => {
    const response = await api.post('/data/ingest/scheduled', { params: { background } })
    return response.data
  },

  getStatus: async () => {
    const response = await api.get('/data/status')
    return response.data
  },

  getHealth: async () => {
    const response = await api.get('/data/health')
    return response.data
  },
}

// Users API
export const usersAPI = {
  getCurrentUser: async () => {
    const response = await api.get('/users/me')
    return response.data
  },

  updateUserProfile: async (profile: any) => {
    const response = await api.put('/users/me', profile)
    return response.data
  },

  getUserPreferences: async () => {
    const response = await api.get('/users/preferences')
    return response.data
  },

  updateUserPreferences: async (preferences: any) => {
    const response = await api.put('/users/preferences', preferences)
    return response.data
  },
}

// WebSocket connection for real-time updates
export const createWebSocketConnection = () => {
  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws'
  return new WebSocket(wsUrl)
}

export default api