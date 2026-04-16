<template>
  <v-container class="py-8">
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <h1 :class="$vuetify.display.xs ? 'text-h4' : 'text-h3'" class="font-weight-bold mb-2">
          <v-icon icon="mdi-account-group" :size="$vuetify.display.xs ? 'default' : 'large'" class="mr-2" />
          Players
        </h1>
        <p class="text-body-1 text-medium-emphasis">
          Browse all registered players and their statistics
        </p>
      </v-col>
    </v-row>

    <!-- Search & Filter -->
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
      <v-col cols="12" md="3">
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
      <v-col cols="12" md="3">
        <v-select
          v-model="roleFilter"
          :items="roles"
          label="Filter by role"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
        />
      </v-col>
    </v-row>

    <!-- Error -->
    <v-row v-if="error">
      <v-col cols="12">
        <v-alert type="error" closable @click:close="error = null">{{ error }}</v-alert>
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
        <v-card elevation="2" hover class="player-card" @click="openProfile(player)">
          <v-card-text class="text-center pa-4">
            <v-avatar size="64" color="primary" class="mb-3">
              <span class="text-h5 font-weight-bold">
                {{ getInitials(player) }}
              </span>
            </v-avatar>

            <h3 class="text-subtitle-1 font-weight-bold mb-1">
              {{ player.full_name || player.username }}
            </h3>

            <v-chip size="small" variant="outlined" class="mb-2">
              {{ player.role }}
            </v-chip>

            <div v-if="player.team_name" class="text-caption text-medium-emphasis mb-2">
              <v-icon size="small">mdi-shield</v-icon>
              {{ player.team_name }}
            </div>

            <div v-if="player.position" class="mb-2">
              <v-chip size="small" color="primary" variant="flat">{{ player.position }}</v-chip>
            </div>

            <!-- Stats row -->
            <div v-if="player.statistics" class="d-flex justify-center ga-3 mt-2">
              <div class="text-center">
                <div class="text-h6 font-weight-bold">{{ player.statistics.matches_played }}</div>
                <div class="text-caption">Matches</div>
              </div>
              <div class="text-center">
                <div class="text-h6 font-weight-bold text-success">{{ player.statistics.goals }}</div>
                <div class="text-caption">Goals</div>
              </div>
              <div class="text-center">
                <div class="text-h6 font-weight-bold text-info">{{ player.statistics.assists }}</div>
                <div class="text-caption">Assists</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Loading -->
      <v-col v-if="loading" cols="12" class="text-center pa-8">
        <v-progress-circular indeterminate color="primary" />
      </v-col>

      <!-- Empty State -->
      <v-col v-if="!loading && filteredPlayers.length === 0" cols="12">
        <v-card class="pa-12 text-center" elevation="0" color="surface-variant">
          <v-icon icon="mdi-account-search" size="64" color="medium-emphasis" class="mb-4" />
          <h3 class="text-h5 mb-2">No players found</h3>
          <p class="text-body-1 text-medium-emphasis">
            Try adjusting your search or filter criteria
          </p>
        </v-card>
      </v-col>
    </v-row>

    <!-- Player Profile Dialog -->
    <v-dialog v-model="showProfileDialog" max-width="600">
      <v-card v-if="selectedPlayer">
        <v-card-title class="d-flex align-center">
          <v-avatar size="40" color="primary" class="mr-3">
            <span class="font-weight-bold">{{ getInitials(selectedPlayer) }}</span>
          </v-avatar>
          {{ selectedPlayer.full_name || selectedPlayer.username }}
        </v-card-title>

        <v-card-text>
          <v-row>
            <v-col cols="6">
              <div class="text-caption text-medium-emphasis">Role</div>
              <v-chip size="small">{{ selectedPlayer.role }}</v-chip>
            </v-col>
            <v-col cols="6">
              <div class="text-caption text-medium-emphasis">Team</div>
              <div>{{ selectedPlayer.team_name || 'Free Agent' }}</div>
            </v-col>
            <v-col v-if="selectedPlayer.email" cols="12">
              <div class="text-caption text-medium-emphasis">Email</div>
              <a :href="`mailto:${selectedPlayer.email}`" class="text-body-2">{{ selectedPlayer.email }}</a>
            </v-col>
            <v-col v-if="selectedPlayer.position" cols="6">
              <div class="text-caption text-medium-emphasis">Position</div>
              <v-chip size="small" color="primary">{{ selectedPlayer.position }}</v-chip>
            </v-col>
            <v-col v-if="selectedPlayer.jersey_number" cols="6">
              <div class="text-caption text-medium-emphasis">Jersey</div>
              <div>#{{ selectedPlayer.jersey_number }}</div>
            </v-col>
          </v-row>

          <!-- Statistics -->
          <v-divider class="my-4" />
          <h4 class="text-subtitle-1 font-weight-bold mb-3">Statistics</h4>

          <div v-if="selectedPlayer.statistics">
            <v-row dense>
              <v-col v-for="stat in statFields" :key="stat.key" cols="4" sm="3">
                <v-card variant="outlined" class="pa-2 text-center">
                  <div class="text-h6 font-weight-bold" :class="stat.color">
                    {{ selectedPlayer.statistics[stat.key] || 0 }}
                  </div>
                  <div class="text-caption">{{ stat.label }}</div>
                </v-card>
              </v-col>
            </v-row>
          </div>
          <div v-else class="text-center text-medium-emphasis pa-4">
            No statistics recorded yet
          </div>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showProfileDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

const config = useRuntimeConfig()
const apiBase = computed(() => config.public.apiBaseUrl || 'http://localhost:8000/api/v1')

const getAuthHeaders = () => {
  const token = useCookie('auth_token')
  return token.value ? { Authorization: `Bearer ${token.value}` } : {}
}

// State
const players = ref<any[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const searchQuery = ref('')
const positionFilter = ref('')
const roleFilter = ref('')
const showProfileDialog = ref(false)
const selectedPlayer = ref<any>(null)

const positions = ['GK', 'DEF', 'MID', 'FWD']
const roles = ['PLAYER', 'CAPTAIN', 'REFEREE']

const statFields = [
  { key: 'matches_played', label: 'Matches', color: '' },
  { key: 'matches_won', label: 'Wins', color: 'text-success' },
  { key: 'matches_lost', label: 'Losses', color: 'text-error' },
  { key: 'goals', label: 'Goals', color: 'text-success' },
  { key: 'assists', label: 'Assists', color: 'text-info' },
  { key: 'yellow_cards', label: 'Yellows', color: 'text-warning' },
  { key: 'red_cards', label: 'Reds', color: 'text-error' },
  { key: 'clean_sheets', label: 'Clean Sheets', color: 'text-primary' },
]

const filteredPlayers = computed(() => {
  return players.value.filter(p => {
    const matchesSearch = !searchQuery.value ||
      (p.full_name || p.username || '').toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesPosition = !positionFilter.value || p.position === positionFilter.value
    const matchesRole = !roleFilter.value || p.role === roleFilter.value
    return matchesSearch && matchesPosition && matchesRole
  })
})

const fetchPlayers = async () => {
  loading.value = true
  error.value = null
  try {
    const teams = await $fetch<any[]>(`${apiBase.value}/teams`, { headers: getAuthHeaders() })
    const allPlayers: any[] = []

    for (const team of teams) {
      try {
        const rosterData = await $fetch<any>(`${apiBase.value}/teams/${team.id}/roster-stats`, {
          headers: getAuthHeaders(),
        })
        const members = rosterData.members || rosterData || []
        for (const member of members) {
          allPlayers.push({
            id: member.user_id || member.user?.id || member.id,
            username: member.user?.username || member.username,
            full_name: member.user?.full_name || member.full_name,
            email: member.user?.email || member.email,
            role: member.role,
            position: member.position,
            jersey_number: member.jersey_number,
            team_name: team.name,
            team_id: team.id,
            statistics: member.statistics || null,
          })
        }
      } catch { /* skip team */ }
    }

    players.value = allPlayers
  } catch (err: any) {
    error.value = err.data?.detail || 'Failed to load players'
  } finally {
    loading.value = false
  }
}

const getInitials = (player: any) => {
  const name = player.full_name || player.username || 'U'
  return name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2)
}

const openProfile = async (player: any) => {
  try {
    const profile = await $fetch<any>(`${apiBase.value}/statistics/player/${player.id}`, {
      headers: getAuthHeaders(),
    })
    selectedPlayer.value = { ...player, ...profile }
  } catch {
    selectedPlayer.value = player
  }
  showProfileDialog.value = true
}

onMounted(() => fetchPlayers())
</script>

<style scoped>
.player-card { height: 100%; }
</style>
