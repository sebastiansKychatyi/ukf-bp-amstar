<template>
  <v-container fluid class="pa-6">
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center justify-space-between mb-4">
          <div>
            <h1 class="text-h4 font-weight-bold mb-2">
              <v-icon size="32" class="mr-2">mdi-account-group</v-icon>
              Players Dashboard
            </h1>
            <p class="text-medium-emphasis">
              Browse and discover talented football players
            </p>
          </div>

          <v-btn
            color="primary"
            size="large"
            prepend-icon="mdi-plus"
            @click="showCreateDialog = true"
          >
            Add Player
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Filters and Search -->
    <v-row>
      <v-col cols="12" md="4">
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          label="Search players..."
          variant="outlined"
          clearable
          hide-details
        />
      </v-col>

      <v-col cols="12" md="3">
        <v-select
          v-model="filterPosition"
          :items="positionOptions"
          label="Filter by Position"
          variant="outlined"
          clearable
          hide-details
        />
      </v-col>

      <v-col cols="12" md="3">
        <v-select
          v-model="sortBy"
          :items="sortOptions"
          label="Sort by"
          variant="outlined"
          hide-details
        />
      </v-col>

      <v-col cols="12" md="2">
        <v-btn-toggle
          v-model="viewMode"
          mandatory
          variant="outlined"
          divided
          class="w-100"
        >
          <v-btn value="grid" icon="mdi-view-grid" />
          <v-btn value="table" icon="mdi-table" />
        </v-btn-toggle>
      </v-col>
    </v-row>

    <!-- Loading State -->
    <v-row v-if="playerStore.loading" class="mt-4">
      <v-col cols="12" class="text-center py-12">
        <v-progress-circular
          indeterminate
          color="primary"
          size="64"
        />
        <p class="text-h6 mt-4">Loading players...</p>
      </v-col>
    </v-row>

    <!-- Error State -->
    <v-alert
      v-if="playerStore.error"
      type="error"
      variant="tonal"
      closable
      class="mt-4"
      @click:close="playerStore.clearError()"
    >
      {{ playerStore.error }}
    </v-alert>

    <!-- Grid View -->
    <v-row v-if="viewMode === 'grid' && !playerStore.loading" class="mt-4">
      <v-col
        v-for="player in filteredPlayers"
        :key="player.id"
        cols="12"
        sm="6"
        md="4"
        lg="3"
      >
        <player-card
          :player="player"
          @view-details="viewPlayerDetails"
          @view-stats="viewPlayerStats"
        />
      </v-col>

      <!-- Empty State -->
      <v-col v-if="filteredPlayers.length === 0" cols="12">
        <v-card class="text-center py-12" variant="outlined">
          <v-icon size="64" color="grey-lighten-1">mdi-account-search</v-icon>
          <p class="text-h6 mt-4">No players found</p>
          <p class="text-medium-emphasis">
            Try adjusting your filters or search query
          </p>
        </v-card>
      </v-col>
    </v-row>

    <!-- Table View -->
    <v-card v-if="viewMode === 'table' && !playerStore.loading" class="mt-4">
      <v-data-table
        :headers="tableHeaders"
        :items="filteredPlayers"
        :search="search"
        :items-per-page="10"
        class="elevation-0"
      >
        <!-- Player Name with Avatar -->
        <template #item.name="{ item }">
          <div class="d-flex align-center py-2">
            <v-avatar
              :color="getPositionColor(item.position)"
              size="40"
              class="mr-3"
            >
              <v-icon color="white">
                {{ getPositionIcon(item.position) }}
              </v-icon>
            </v-avatar>
            <div>
              <div class="font-weight-bold">
                {{ item.first_name }} {{ item.last_name }}
              </div>
              <div class="text-caption text-medium-emphasis">
                {{ item.email }}
              </div>
            </div>
          </div>
        </template>

        <!-- Position with icon -->
        <template #item.position="{ item }">
          <v-chip
            :color="getPositionColor(item.position)"
            variant="flat"
            size="small"
            :prepend-icon="getPositionIcon(item.position)"
          >
            {{ item.position }}
          </v-chip>
        </template>

        <!-- Rating with color -->
        <template #item.skill_rating="{ item }">
          <v-chip
            :color="getRatingColor(item.skill_rating)"
            variant="flat"
            class="font-weight-bold"
          >
            {{ item.skill_rating.toFixed(1) }}
          </v-chip>
        </template>

        <!-- Stats columns -->
        <template #item.total_goals="{ item }">
          <div class="d-flex align-center">
            <v-icon color="success" size="20" class="mr-1">mdi-soccer</v-icon>
            {{ item.total_goals }}
          </div>
        </template>

        <template #item.total_assists="{ item }">
          <div class="d-flex align-center">
            <v-icon color="info" size="20" class="mr-1">
              mdi-hand-pointing-right
            </v-icon>
            {{ item.total_assists }}
          </div>
        </template>

        <template #item.cards="{ item }">
          <div class="d-flex align-center ga-2">
            <v-chip color="warning" size="x-small">
              {{ item.total_yellow_cards }}
            </v-chip>
            <v-chip color="error" size="x-small">
              {{ item.total_red_cards }}
            </v-chip>
          </div>
        </template>

        <!-- Actions -->
        <template #item.actions="{ item }">
          <v-btn
            icon="mdi-eye"
            variant="text"
            size="small"
            @click="viewPlayerDetails(item)"
          />
          <v-btn
            icon="mdi-chart-line"
            variant="text"
            size="small"
            @click="viewPlayerStats(item)"
          />
        </template>
      </v-data-table>
    </v-card>

    <!-- Player Details Dialog -->
    <player-details-dialog
      v-model="showDetailsDialog"
      :player="selectedPlayer"
    />

    <!-- Player Statistics Dialog -->
    <player-stats-dialog
      v-model="showStatsDialog"
      :player="selectedPlayer"
    />

    <!-- Create Player Dialog (placeholder) -->
    <v-dialog v-model="showCreateDialog" max-width="600">
      <v-card>
        <v-card-title>Add New Player</v-card-title>
        <v-card-text>
          <p class="text-medium-emphasis">
            Player creation form will be implemented here
          </p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="showCreateDialog = false">Cancel</v-btn>
          <v-btn color="primary">Create</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePlayerStore } from '@/stores/player'
import PlayerCard from '@/components/PlayerCard.vue'
import PlayerDetailsDialog from '@/components/PlayerDetailsDialog.vue'
import PlayerStatsDialog from '@/components/PlayerStatsDialog.vue'

const playerStore = usePlayerStore()

// State
const search = ref('')
const filterPosition = ref(null)
const sortBy = ref('rating')
const viewMode = ref('grid')
const showDetailsDialog = ref(false)
const showStatsDialog = ref(false)
const showCreateDialog = ref(false)
const selectedPlayer = ref(null)

// Options
const positionOptions = [
  { title: 'Goalkeeper', value: 'GOALKEEPER' },
  { title: 'Defender', value: 'DEFENDER' },
  { title: 'Midfielder', value: 'MIDFIELDER' },
  { title: 'Forward', value: 'FORWARD' },
]

const sortOptions = [
  { title: 'Highest Rating', value: 'rating' },
  { title: 'Most Goals', value: 'goals' },
  { title: 'Most Assists', value: 'assists' },
  { title: 'Most Matches', value: 'matches' },
  { title: 'Name (A-Z)', value: 'name' },
]

const tableHeaders = [
  { title: 'Player', key: 'name', sortable: true },
  { title: 'Position', key: 'position', sortable: true },
  { title: 'Rating', key: 'skill_rating', sortable: true },
  { title: 'Goals', key: 'total_goals', sortable: true },
  { title: 'Assists', key: 'total_assists', sortable: true },
  { title: 'Cards (Y/R)', key: 'cards', sortable: false },
  { title: 'Matches', key: 'total_matches_played', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false },
]

// Computed
const filteredPlayers = computed(() => {
  let players = [...playerStore.players]

  // Filter by position
  if (filterPosition.value) {
    players = players.filter(p => p.position === filterPosition.value)
  }

  // Filter by search
  if (search.value) {
    const searchLower = search.value.toLowerCase()
    players = players.filter(p =>
      p.first_name.toLowerCase().includes(searchLower) ||
      p.last_name.toLowerCase().includes(searchLower) ||
      p.email.toLowerCase().includes(searchLower)
    )
  }

  // Sort
  players.sort((a, b) => {
    switch (sortBy.value) {
      case 'rating':
        return b.skill_rating - a.skill_rating
      case 'goals':
        return b.total_goals - a.total_goals
      case 'assists':
        return b.total_assists - a.total_assists
      case 'matches':
        return b.total_matches_played - a.total_matches_played
      case 'name':
        return a.first_name.localeCompare(b.first_name)
      default:
        return 0
    }
  })

  return players
})

// Methods
function viewPlayerDetails(player) {
  selectedPlayer.value = player
  showDetailsDialog.value = true
}

function viewPlayerStats(player) {
  selectedPlayer.value = player
  showStatsDialog.value = true
}

function getPositionIcon(position) {
  const icons = {
    GOALKEEPER: 'mdi-shield-account',
    DEFENDER: 'mdi-shield',
    MIDFIELDER: 'mdi-run',
    FORWARD: 'mdi-soccer',
  }
  return icons[position] || 'mdi-account'
}

function getPositionColor(position) {
  const colors = {
    GOALKEEPER: '#F59E0B',
    DEFENDER: '#3B82F6',
    MIDFIELDER: '#10B981',
    FORWARD: '#EF4444',
  }
  return colors[position] || 'grey'
}

function getRatingColor(rating) {
  if (rating >= 80) return 'success'
  if (rating >= 60) return 'info'
  if (rating >= 40) return 'warning'
  return 'error'
}

// Lifecycle
onMounted(async () => {
  await playerStore.fetchAllPlayers()
})
</script>

<style scoped>
.w-100 {
  width: 100%;
}
</style>
