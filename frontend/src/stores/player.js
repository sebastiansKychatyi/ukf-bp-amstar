/**
 * Player Store - Pinia
 * Manages player state and operations
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { playerApi } from '@/services/api'

export const usePlayerStore = defineStore('player', () => {
  // State
  const players = ref([])
  const currentPlayer = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const getPlayerById = computed(() => {
    return (playerId) => players.value.find(p => p.id === playerId)
  })

  const playersByPosition = computed(() => {
    return (position) => players.value.filter(p => p.position === position)
  })

  const topRatedPlayers = computed(() => {
    return [...players.value]
      .sort((a, b) => b.skill_rating - a.skill_rating)
      .slice(0, 10)
  })

  // Actions
  async function fetchAllPlayers() {
    loading.value = true
    error.value = null

    try {
      players.value = await playerApi.getAll()
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch players'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchPlayerById(playerId) {
    loading.value = true
    error.value = null

    try {
      const player = await playerApi.getById(playerId)

      // Update in players array if exists
      const index = players.value.findIndex(p => p.id === playerId)
      if (index !== -1) {
        players.value[index] = player
      } else {
        players.value.push(player)
      }

      return player
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch player'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function createPlayer(playerData) {
    loading.value = true
    error.value = null

    try {
      const newPlayer = await playerApi.create(playerData)
      players.value.push(newPlayer)
      return newPlayer
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to create player'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function updatePlayer(playerId, updateData) {
    loading.value = true
    error.value = null

    try {
      const updatedPlayer = await playerApi.update(playerId, updateData)

      // Update in players array
      const index = players.value.findIndex(p => p.id === playerId)
      if (index !== -1) {
        players.value[index] = updatedPlayer
      }

      // Update current player if it's the same
      if (currentPlayer.value?.id === playerId) {
        currentPlayer.value = updatedPlayer
      }

      return updatedPlayer
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to update player'
      throw err
    } finally {
      loading.value = false
    }
  }

  async function fetchPlayerStatistics(playerId) {
    loading.value = true
    error.value = null

    try {
      const stats = await playerApi.getStatistics(playerId)
      return stats
    } catch (err) {
      error.value = err.response?.data?.detail || 'Failed to fetch statistics'
      throw err
    } finally {
      loading.value = false
    }
  }

  function setCurrentPlayer(player) {
    currentPlayer.value = player
  }

  function clearError() {
    error.value = null
  }

  function resetStore() {
    players.value = []
    currentPlayer.value = null
    loading.value = false
    error.value = null
  }

  return {
    // State
    players,
    currentPlayer,
    loading,
    error,

    // Getters
    getPlayerById,
    playersByPosition,
    topRatedPlayers,

    // Actions
    fetchAllPlayers,
    fetchPlayerById,
    createPlayer,
    updatePlayer,
    fetchPlayerStatistics,
    setCurrentPlayer,
    clearError,
    resetStore,
  }
})
