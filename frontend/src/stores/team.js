/**
 * Team Store - Pinia
 * Manages team state and operations
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { teamApi, joinRequestApi } from '@/services/api'

export const useTeamStore = defineStore('team', () => {
  // State
  const teams = ref([])
  const currentTeam = ref(null)
  const teamMembers = ref([])
  const pendingJoinRequests = ref([])
  const myJoinRequests = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const getTeamById = computed(() => {
    return (teamId) => teams.value.find(t => t.id === teamId)
  })

  const teamsRecruting = computed(() => {
    return teams.value.filter(t => t.is_recruiting && t.is_active)
  })

  const topRatedTeams = computed(() => {
    return [...teams.value]
      .sort((a, b) => b.team_rating - a.team_rating)
      .slice(0, 10)
  })

  const isUserCaptain = computed(() => {
    if (!currentTeam.value || !teamMembers.value.length) return false

    // Check if current user is captain
    // Note: You'll need to pass userId from auth store
    return teamMembers.value.some(m => m.role === 'CAPTAIN')
  })

  const teamCaptains = computed(() => {
    return teamMembers.value.filter(m => m.role === 'CAPTAIN')
  })

  // Actions
  async function fetchAllTeams() {
    loading.value = true
    error.value = null

    try {
      teams.value = await teamApi.getAll()
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch teams'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchTeamById(teamId) {
    loading.value = true
    error.value = null

    try {
      const team = await teamApi.getById(teamId)

      // Update in teams array if exists
      const index = teams.value.findIndex(t => t.id === teamId)
      if (index !== -1) {
        teams.value[index] = team
      } else {
        teams.value.push(team)
      }

      return team
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch team'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createTeam(teamData) {
    loading.value = true
    error.value = null

    try {
      const newTeam = await teamApi.create(teamData)
      teams.value.push(newTeam)
      currentTeam.value = newTeam
      return newTeam
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to create team'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updateTeam(teamId, updateData) {
    loading.value = true
    error.value = null

    try {
      const updatedTeam = await teamApi.update(teamId, updateData)

      // Update in teams array
      const index = teams.value.findIndex(t => t.id === teamId)
      if (index !== -1) {
        teams.value[index] = updatedTeam
      }

      // Update current team if it's the same
      if (currentTeam.value?.id === teamId) {
        currentTeam.value = updatedTeam
      }

      return updatedTeam
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update team'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchTeamMembers(teamId) {
    loading.value = true
    error.value = null

    try {
      teamMembers.value = await teamApi.getMembers(teamId)
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch team members'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function removeMember(teamId, playerId) {
    loading.value = true
    error.value = null

    try {
      await teamApi.removeMember(teamId, playerId)

      // Remove from local state
      teamMembers.value = teamMembers.value.filter(m => m.player_id !== playerId)
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to remove member'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function promoteToCaptain(teamId, playerId) {
    loading.value = true
    error.value = null

    try {
      await teamApi.promoteToCaptain(teamId, playerId)

      // Update local state
      const member = teamMembers.value.find(m => m.player_id === playerId)
      if (member) {
        member.role = 'CAPTAIN'
      }
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to promote member'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function uploadTeamLogo(teamId, logoFile) {
    loading.value = true
    error.value = null

    try {
      const updatedTeam = await teamApi.uploadLogo(teamId, logoFile)

      // Update in teams array
      const index = teams.value.findIndex(t => t.id === teamId)
      if (index !== -1) {
        teams.value[index] = updatedTeam
      }

      // Update current team if it's the same
      if (currentTeam.value?.id === teamId) {
        currentTeam.value = updatedTeam
      }

      return updatedTeam
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to upload logo'
      throw err
    } finally {
      loading.value = false
    }
  }

  // Join Request Actions
  async function createJoinRequest(teamId, message) {
    loading.value = true
    error.value = null

    try {
      const request = await joinRequestApi.create({
        team_id: teamId,
        player_id: 'current-player-id', // Get from auth store
        message,
      })

      myJoinRequests.value.push(request)
      return request
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to create join request'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchPendingJoinRequests(teamId) {
    loading.value = true
    error.value = null

    try {
      pendingJoinRequests.value = await joinRequestApi.getPending(teamId)
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch join requests'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function reviewJoinRequest(requestId, status, reviewMessage = '') {
    loading.value = true
    error.value = null

    try {
      const updatedRequest = await joinRequestApi.review(requestId, {
        status,
        review_message: reviewMessage,
      })

      // Remove from pending requests
      pendingJoinRequests.value = pendingJoinRequests.value.filter(
        r => r.id !== requestId
      )

      // If approved, refetch team members
      if (status === 'APPROVED' && currentTeam.value) {
        await fetchTeamMembers(currentTeam.value.id)
      }

      return updatedRequest
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to review request'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchMyJoinRequests() {
    loading.value = true
    error.value = null

    try {
      myJoinRequests.value = await joinRequestApi.getMine()
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch your requests'
      throw err
    } finally {
      loading.value = false
    }
  }

  function setCurrentTeam(team) {
    currentTeam.value = team
  }

  function clearError() {
    error.value = null
  }

  function resetStore() {
    teams.value = []
    currentTeam.value = null
    teamMembers.value = []
    pendingJoinRequests.value = []
    myJoinRequests.value = []
    loading.value = false
    error.value = null
  }

  return {
    // State
    teams,
    currentTeam,
    teamMembers,
    pendingJoinRequests,
    myJoinRequests,
    loading,
    error,

    // Getters
    getTeamById,
    teamsRecruting,
    topRatedTeams,
    isUserCaptain,
    teamCaptains,

    // Actions
    fetchAllTeams,
    fetchTeamById,
    createTeam,
    updateTeam,
    fetchTeamMembers,
    removeMember,
    promoteToCaptain,
    uploadTeamLogo,
    createJoinRequest,
    fetchPendingJoinRequests,
    reviewJoinRequest,
    fetchMyJoinRequests,
    setCurrentTeam,
    clearError,
    resetStore,
  }
})
