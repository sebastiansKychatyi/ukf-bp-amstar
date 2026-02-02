/**
 * API Service Layer
 * Handles all HTTP communication with FastAPI backend
 */

import axios from 'axios'

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const API_PREFIX = '/api'

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 seconds
})

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - handle errors globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error
      switch (error.response.status) {
        case 401:
          // Unauthorized - redirect to login
          localStorage.removeItem('access_token')
          window.location.href = '/login'
          break
        case 403:
          console.error('Forbidden:', error.response.data.detail)
          break
        case 404:
          console.error('Not found:', error.response.data.detail)
          break
        case 500:
          console.error('Server error:', error.response.data.detail)
          break
      }
    } else if (error.request) {
      // Request made but no response
      console.error('Network error: No response from server')
    } else {
      // Error setting up request
      console.error('Request error:', error.message)
    }
    return Promise.reject(error)
  }
)

// ============================================================================
// PLAYER API
// ============================================================================

export const playerApi = {
  /**
   * Get all players
   * @returns {Promise} List of players
   */
  async getAll() {
    const response = await apiClient.get('/players')
    return response.data
  },

  /**
   * Get player by ID
   * @param {string} playerId - Player UUID
   * @returns {Promise} Player details
   */
  async getById(playerId) {
    const response = await apiClient.get(`/players/${playerId}`)
    return response.data
  },

  /**
   * Create new player
   * @param {Object} playerData - Player creation data
   * @returns {Promise} Created player
   */
  async create(playerData) {
    const response = await apiClient.post('/players', playerData)
    return response.data
  },

  /**
   * Update player information
   * @param {string} playerId - Player UUID
   * @param {Object} updateData - Fields to update
   * @returns {Promise} Updated player
   */
  async update(playerId, updateData) {
    const response = await apiClient.patch(`/players/${playerId}`, updateData)
    return response.data
  },

  /**
   * Get player statistics
   * @param {string} playerId - Player UUID
   * @returns {Promise} Player statistics with team breakdown
   */
  async getStatistics(playerId) {
    const response = await apiClient.get(`/statistics/players/${playerId}`)
    return response.data
  },
}

// ============================================================================
// TEAM API
// ============================================================================

export const teamApi = {
  /**
   * Get all teams
   * @returns {Promise} List of teams
   */
  async getAll() {
    const response = await apiClient.get('/v1/teams')
    return response.data
  },

  /**
   * Get team by ID
   * @param {number} teamId - Team ID
   * @returns {Promise} Team details
   */
  async getById(teamId) {
    const response = await apiClient.get(`/v1/teams/${teamId}`)
    return response.data
  },

  /**
   * Create new team (captain only)
   * @param {Object} teamData - Team creation data
   * @returns {Promise} Created team
   */
  async create(teamData) {
    const response = await apiClient.post('/v1/teams', teamData)
    return response.data
  },

  /**
   * Update team information (captain only)
   * @param {number} teamId - Team ID
   * @param {Object} updateData - Fields to update
   * @returns {Promise} Updated team
   */
  async update(teamId, updateData) {
    const response = await apiClient.put(`/v1/teams/${teamId}`, updateData)
    return response.data
  },

  /**
   * Delete team (captain only)
   * @param {number} teamId - Team ID
   * @returns {Promise} Deleted team
   */
  async delete(teamId) {
    const response = await apiClient.delete(`/v1/teams/${teamId}`)
    return response.data
  },

  /**
   * Search teams by name or description
   * @param {string} query - Search query
   * @returns {Promise} List of matching teams
   */
  async search(query) {
    const response = await apiClient.get('/v1/teams/search/', { params: { q: query } })
    return response.data
  },

  /**
   * Get current user's team (as captain)
   * @returns {Promise} Captain's team
   */
  async getMyTeam() {
    const response = await apiClient.get('/v1/teams/my/team')
    return response.data
  },

  /**
   * Get team members (roster)
   * @param {number} teamId - Team ID
   * @returns {Promise} List of team members
   */
  async getMembers(teamId) {
    const response = await apiClient.get(`/v1/teams/${teamId}/members`)
    return response.data
  },

  /**
   * Get a specific team member
   * @param {number} teamId - Team ID
   * @param {number} userId - User ID
   * @returns {Promise} Team member details
   */
  async getMember(teamId, userId) {
    const response = await apiClient.get(`/v1/teams/${teamId}/members/${userId}`)
    return response.data
  },

  /**
   * Remove team member (captain only)
   * @param {number} teamId - Team ID
   * @param {number} userId - User ID
   * @returns {Promise} Removed member
   */
  async removeMember(teamId, userId) {
    const response = await apiClient.delete(`/v1/teams/${teamId}/members/${userId}`)
    return response.data
  },

  /**
   * Update team member info (captain only)
   * @param {number} teamId - Team ID
   * @param {number} userId - User ID
   * @param {Object} updateData - { position?, jersey_number? }
   * @returns {Promise} Updated member
   */
  async updateMember(teamId, userId, updateData) {
    const response = await apiClient.put(`/v1/teams/${teamId}/members/${userId}`, updateData)
    return response.data
  },

  /**
   * Leave team (for current player)
   * @param {number} teamId - Team ID
   * @returns {Promise} Success message
   */
  async leaveTeam(teamId) {
    const response = await apiClient.post(`/v1/teams/${teamId}/leave`)
    return response.data
  },

  /**
   * Transfer captaincy to another member
   * @param {number} teamId - Team ID
   * @param {number} newCaptainId - New captain's user ID
   * @returns {Promise} Updated team
   */
  async transferCaptaincy(teamId, newCaptainId) {
    const response = await apiClient.post(`/v1/teams/${teamId}/transfer-captaincy/${newCaptainId}`)
    return response.data
  },

  /**
   * Get current user's team membership
   * @returns {Promise} Membership info
   */
  async getMyMembership() {
    const response = await apiClient.get('/v1/teams/my/membership')
    return response.data
  },

  /**
   * Get team the current user belongs to (as member)
   * @returns {Promise} Team info
   */
  async getMyTeamAsMember() {
    const response = await apiClient.get('/v1/teams/my/team')
    return response.data
  },

  /**
   * Get team statistics
   * @param {number} teamId - Team ID
   * @returns {Promise} Team statistics
   */
  async getStatistics(teamId) {
    const response = await apiClient.get(`/v1/statistics/teams/${teamId}`)
    return response.data
  },

  /**
   * Upload team logo
   * @param {number} teamId - Team ID
   * @param {File} logoFile - Image file
   * @returns {Promise} Updated team with logo URL
   */
  async uploadLogo(teamId, logoFile) {
    const formData = new FormData()
    formData.append('logo', logoFile)

    const response = await apiClient.post(`/v1/teams/${teamId}/logo`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  },
}

// ============================================================================
// JOIN REQUEST API
// ============================================================================

export const joinRequestApi = {
  /**
   * Create join request
   * @param {Object} requestData - { team_id, message?, position? }
   * @returns {Promise} Created join request
   */
  async create(requestData) {
    const response = await apiClient.post('/v1/join-requests', requestData)
    return response.data
  },

  /**
   * Get pending join requests for a team (captain only)
   * @param {number} teamId - Team ID
   * @returns {Promise} List of pending requests
   */
  async getPending(teamId) {
    const response = await apiClient.get(`/v1/join-requests/team/${teamId}/pending`)
    return response.data
  },

  /**
   * Review join request (captain only)
   * @param {number} requestId - Request ID
   * @param {Object} reviewData - { status: 'ACCEPTED'|'REJECTED', review_message? }
   * @returns {Promise} Updated join request
   */
  async review(requestId, reviewData) {
    const response = await apiClient.post(`/v1/join-requests/${requestId}/review`, reviewData)
    return response.data
  },

  /**
   * Get my join requests
   * @returns {Promise} List of player's join requests
   */
  async getMine() {
    const response = await apiClient.get('/v1/join-requests/my')
    return response.data
  },

  /**
   * Cancel a pending join request
   * @param {number} requestId - Request ID
   * @returns {Promise} Cancelled join request
   */
  async cancel(requestId) {
    const response = await apiClient.delete(`/v1/join-requests/${requestId}`)
    return response.data
  },

  /**
   * Get a specific join request
   * @param {number} requestId - Request ID
   * @returns {Promise} Join request details
   */
  async getById(requestId) {
    const response = await apiClient.get(`/v1/join-requests/${requestId}`)
    return response.data
  },
}

// ============================================================================
// STATISTICS API
// ============================================================================

export const statisticsApi = {
  /**
   * Update match statistics (captain only)
   * @param {Object} matchStats - Match statistics data
   * @returns {Promise} Update result
   */
  async updateMatchStats(matchStats) {
    const response = await apiClient.post('/statistics/matches/update', matchStats)
    return response.data
  },
}

// ============================================================================
// AUTH API (placeholder - implement based on your auth system)
// ============================================================================

export const authApi = {
  /**
   * Login user
   * @param {string} email - User email
   * @param {string} password - User password
   * @returns {Promise} Auth tokens and user data
   */
  async login(email, password) {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)

    const response = await apiClient.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })

    // Store token
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token)
    }

    return response.data
  },

  /**
   * Register new user
   * @param {Object} userData - User registration data
   * @returns {Promise} Created user
   */
  async register(userData) {
    const response = await apiClient.post('/auth/register', userData)
    return response.data
  },

  /**
   * Logout user
   */
  logout() {
    localStorage.removeItem('access_token')
    window.location.href = '/login'
  },

  /**
   * Get current user
   * @returns {Promise} Current user data
   */
  async getCurrentUser() {
    const response = await apiClient.get('/auth/me')
    return response.data
  },
}

// Export the axios instance for custom requests
export default apiClient
