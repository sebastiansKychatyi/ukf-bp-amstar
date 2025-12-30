<template>
  <!--
    Players Page
    ============
    Displays all players using the reusable PlayerCard component

    Features:
    - Grid layout with responsive columns
    - Search/filter functionality
    - Reusable PlayerCard component
    - Clean, minimalist design
  -->
  <v-container class="py-8">
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <h1 class="text-h3 font-weight-bold mb-2">
          <v-icon icon="mdi-account-group" size="large" class="mr-2" />
          Players
        </h1>
        <p class="text-body-1 text-medium-emphasis">
          Browse all registered players and their ratings
        </p>
      </v-col>
    </v-row>

    <!-- Search and Filter Bar -->
    <v-row>
      <v-col cols="12" md="6">
        <v-text-field
          v-model="searchQuery"
          prepend-inner-icon="mdi-magnify"
          label="Search players"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-select
          v-model="positionFilter"
          :items="positions"
          label="Filter by position"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
        />
      </v-col>
    </v-row>

    <!-- Players Grid -->
    <v-row class="mt-4">
      <v-col
        v-for="player in filteredPlayers"
        :key="player.id"
        cols="12"
        sm="6"
        md="4"
        lg="3"
      >
        <!-- Reusable PlayerCard Component -->
        <PlayerCard
          :player="player"
          @view-details="handleViewDetails"
        />
      </v-col>

      <!-- Empty State -->
      <v-col v-if="filteredPlayers.length === 0" cols="12">
        <v-card class="pa-12 text-center" elevation="0" color="surface-variant">
          <v-icon icon="mdi-account-search" size="64" color="medium-emphasis" class="mb-4" />
          <h3 class="text-h5 mb-2">No players found</h3>
          <p class="text-body-1 text-medium-emphasis">
            Try adjusting your search or filter criteria
          </p>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

/**
 * Player Interface
 * ================
 * Defines the structure of a player object
 */
interface Player {
  id: number
  name: string
  position: string
  rating: number
}

/**
 * Search and Filter State
 * =======================
 * Reactive state for search and filtering functionality
 */
const searchQuery = ref('')
const positionFilter = ref('')

/**
 * Available Positions
 * ==================
 * List of football positions for the filter dropdown
 */
const positions = [
  'Goalkeeper',
  'Defender',
  'Midfielder',
  'Forward',
]

/**
 * Mock Data
 * =========
 * Sample players data (replace with API call in production)
 * TODO: Connect to backend API endpoint
 */
const players = ref<Player[]>([
  { id: 1, name: 'John Martinez', position: 'Forward', rating: 4.8 },
  { id: 2, name: 'Sarah Johnson', position: 'Goalkeeper', rating: 4.9 },
  { id: 3, name: 'Alex Chen', position: 'Midfielder', rating: 4.7 },
  { id: 4, name: 'Marcus Robinson', position: 'Defender', rating: 4.6 },
  { id: 5, name: 'Emma Williams', position: 'Forward', rating: 4.5 },
  { id: 6, name: 'David Brown', position: 'Midfielder', rating: 4.3 },
  { id: 7, name: 'Lisa Anderson', position: 'Defender', rating: 4.4 },
  { id: 8, name: 'Mike Taylor', position: 'Goalkeeper', rating: 4.2 },
  { id: 9, name: 'Jessica Lee', position: 'Forward', rating: 4.6 },
  { id: 10, name: 'Chris Wilson', position: 'Midfielder', rating: 4.1 },
  { id: 11, name: 'Anna Garcia', position: 'Defender', rating: 4.5 },
  { id: 12, name: 'Tom Harris', position: 'Forward', rating: 3.9 },
])

/**
 * Filtered Players Computed Property
 * ==================================
 * Filters players based on search query and position filter
 * This computed property automatically updates when search or filter changes
 */
const filteredPlayers = computed(() => {
  return players.value.filter(player => {
    // Filter by search query (name)
    const matchesSearch = !searchQuery.value ||
      player.name.toLowerCase().includes(searchQuery.value.toLowerCase())

    // Filter by position
    const matchesPosition = !positionFilter.value ||
      player.position === positionFilter.value

    return matchesSearch && matchesPosition
  })
})

/**
 * Event Handlers
 * ==============
 */
const handleViewDetails = (player: Player) => {
  // TODO: Navigate to player details page or open dialog
  console.log('View player details:', player)
  // Example: navigateTo(`/players/${player.id}`)
}
</script>

<style scoped>
/**
 * Page-Specific Styles
 * ====================
 * No additional styles needed - Vuetify and PlayerCard handle all styling
 */
</style>
