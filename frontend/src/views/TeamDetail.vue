<template>
  <v-container fluid class="pa-6">
    <!-- Loading State -->
    <v-row v-if="loading && !currentTeam" justify="center">
      <v-col cols="12" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" />
        <p class="text-h6 mt-4">Loading team details...</p>
      </v-col>
    </v-row>

    <template v-else-if="currentTeam">
      <!-- Team Header -->
      <v-card class="mb-6" elevation="4">
        <v-card-text class="pa-6">
          <v-row align="center">
            <!-- Team Logo and Info -->
            <v-col cols="12" md="auto">
              <v-avatar
                :color="currentTeam.team_color || 'primary'"
                size="120"
                class="team-logo"
              >
                <v-img
                  v-if="currentTeam.logo_url"
                  :src="currentTeam.logo_url"
                  cover
                />
                <v-icon v-else size="60" color="white">mdi-shield</v-icon>
              </v-avatar>
            </v-col>

            <v-col>
              <h1 class="text-h3 font-weight-bold mb-2">
                {{ currentTeam.name }}
                <v-chip
                  v-if="currentTeam.short_name"
                  variant="tonal"
                  class="ml-2"
                >
                  {{ currentTeam.short_name }}
                </v-chip>
              </h1>

              <div class="d-flex align-center flex-wrap ga-4 mb-3">
                <!-- Location -->
                <div v-if="currentTeam.home_city" class="d-flex align-center">
                  <v-icon size="20" class="mr-1">mdi-map-marker</v-icon>
                  <span>{{ currentTeam.home_city }}</span>
                </div>

                <!-- Founded -->
                <div v-if="currentTeam.founded_date" class="d-flex align-center">
                  <v-icon size="20" class="mr-1">mdi-calendar</v-icon>
                  <span>Founded {{ formatYear(currentTeam.founded_date) }}</span>
                </div>

                <!-- Rating -->
                <v-chip
                  :color="getRatingColor(currentTeam.team_rating)"
                  variant="flat"
                  prepend-icon="mdi-star"
                >
                  <span class="font-weight-bold">
                    {{ currentTeam.team_rating.toFixed(1) }} Rating
                  </span>
                </v-chip>

                <!-- Recruiting Status -->
                <v-chip
                  :color="currentTeam.is_recruiting ? 'success' : 'grey'"
                  variant="flat"
                  :prepend-icon="currentTeam.is_recruiting ? 'mdi-check-circle' : 'mdi-close-circle'"
                >
                  {{ currentTeam.is_recruiting ? 'Recruiting' : 'Not Recruiting' }}
                </v-chip>
              </div>

              <!-- Description -->
              <p v-if="currentTeam.description" class="text-body-1">
                {{ currentTeam.description }}
              </p>
            </v-col>

            <!-- Actions (Captain Only) -->
            <v-col v-if="isUserCaptain" cols="12" md="auto">
              <div class="d-flex flex-column ga-2">
                <v-btn
                  color="primary"
                  prepend-icon="mdi-pencil"
                  @click="showEditDialog = true"
                >
                  Edit Team
                </v-btn>
                <v-btn
                  variant="tonal"
                  prepend-icon="mdi-account-multiple-plus"
                  @click="showJoinRequestsDialog = true"
                >
                  Join Requests
                  <v-badge
                    v-if="pendingRequestsCount > 0"
                    :content="pendingRequestsCount"
                    color="error"
                    inline
                  />
                </v-btn>
              </div>
            </v-col>

            <!-- Join Team Button (Non-members) -->
            <v-col v-else cols="12" md="auto">
              <v-btn
                color="primary"
                size="large"
                prepend-icon="mdi-account-plus"
                :disabled="!currentTeam.is_recruiting"
                @click="showJoinDialog = true"
              >
                Request to Join
              </v-btn>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- Team Statistics -->
      <v-row class="mb-6">
        <v-col cols="6" sm="3">
          <v-card variant="tonal" color="info">
            <v-card-text class="text-center">
              <v-icon size="32">mdi-trophy</v-icon>
              <div class="text-h5 font-weight-bold mt-2">
                {{ currentTeam.total_wins }}
              </div>
              <div class="text-caption">Wins</div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="6" sm="3">
          <v-card variant="tonal" color="grey">
            <v-card-text class="text-center">
              <v-icon size="32">mdi-handshake</v-icon>
              <div class="text-h5 font-weight-bold mt-2">
                {{ currentTeam.total_draws }}
              </div>
              <div class="text-caption">Draws</div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="6" sm="3">
          <v-card variant="tonal" color="error">
            <v-card-text class="text-center">
              <v-icon size="32">mdi-close-circle</v-icon>
              <div class="text-h5 font-weight-bold mt-2">
                {{ currentTeam.total_losses }}
              </div>
              <div class="text-caption">Losses</div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="6" sm="3">
          <v-card variant="tonal" color="success">
            <v-card-text class="text-center">
              <v-icon size="32">mdi-soccer</v-icon>
              <div class="text-h5 font-weight-bold mt-2">
                {{ currentTeam.total_goals_scored }}
              </div>
              <div class="text-caption">Goals</div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Team Roster -->
      <v-card>
        <v-card-title class="d-flex align-center pa-6">
          <v-icon size="28" class="mr-2">mdi-account-group</v-icon>
          <span class="text-h5">Team Roster</span>
          <v-spacer />
          <v-chip variant="tonal">
            {{ teamMembers.length }} / {{ currentTeam.max_players }} Players
          </v-chip>
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-0">
          <!-- Position Tabs -->
          <v-tabs v-model="selectedPosition" bg-color="surface">
            <v-tab value="all">
              <v-icon start>mdi-account-multiple</v-icon>
              All ({{ teamMembers.length }})
            </v-tab>
            <v-tab value="GOALKEEPER">
              <v-icon start>mdi-shield-account</v-icon>
              Goalkeepers ({{ getPlayersByPosition('GOALKEEPER').length }})
            </v-tab>
            <v-tab value="DEFENDER">
              <v-icon start>mdi-shield</v-icon>
              Defenders ({{ getPlayersByPosition('DEFENDER').length }})
            </v-tab>
            <v-tab value="MIDFIELDER">
              <v-icon start>mdi-run</v-icon>
              Midfielders ({{ getPlayersByPosition('MIDFIELDER').length }})
            </v-tab>
            <v-tab value="FORWARD">
              <v-icon start>mdi-soccer</v-icon>
              Forwards ({{ getPlayersByPosition('FORWARD').length }})
            </v-tab>
          </v-tabs>

          <v-divider />

          <!-- Roster Table -->
          <v-data-table
            :headers="rosterHeaders"
            :items="filteredMembers"
            :items-per-page="15"
            class="elevation-0"
          >
            <!-- Player Name -->
            <template #item.player="{ item }">
              <div class="d-flex align-center py-2">
                <v-avatar
                  :color="getPositionColor(item.player.position)"
                  size="40"
                  class="mr-3"
                >
                  <v-icon color="white">
                    {{ getPositionIcon(item.player.position) }}
                  </v-icon>
                </v-avatar>
                <div>
                  <div class="font-weight-bold">
                    {{ item.player.first_name }} {{ item.player.last_name }}
                    <v-chip
                      v-if="item.role === 'CAPTAIN'"
                      color="warning"
                      size="x-small"
                      variant="flat"
                      class="ml-2"
                    >
                      <v-icon start size="12">mdi-star</v-icon>
                      Captain
                    </v-chip>
                  </div>
                  <div class="text-caption text-medium-emphasis">
                    {{ item.player.position }}
                  </div>
                </div>
              </div>
            </template>

            <!-- Jersey Number -->
            <template #item.jersey_number="{ item }">
              <v-chip
                v-if="item.jersey_number"
                color="primary"
                variant="outlined"
                class="font-weight-bold"
              >
                #{{ item.jersey_number }}
              </v-chip>
              <span v-else class="text-medium-emphasis">-</span>
            </template>

            <!-- Rating -->
            <template #item.rating="{ item }">
              <v-chip
                :color="getRatingColor(item.player.skill_rating)"
                variant="flat"
                class="font-weight-bold"
              >
                {{ item.player.skill_rating.toFixed(1) }}
              </v-chip>
            </template>

            <!-- Team Stats -->
            <template #item.goals="{ item }">
              <div class="d-flex align-center">
                <v-icon color="success" size="18" class="mr-1">mdi-soccer</v-icon>
                {{ item.goals }}
              </div>
            </template>

            <template #item.assists="{ item }">
              <div class="d-flex align-center">
                <v-icon color="info" size="18" class="mr-1">
                  mdi-hand-pointing-right
                </v-icon>
                {{ item.assists }}
              </div>
            </template>

            <!-- Actions (Captain Only) -->
            <template #item.actions="{ item }">
              <div v-if="isUserCaptain" class="d-flex ga-1">
                <v-btn
                  v-if="item.role !== 'CAPTAIN'"
                  icon="mdi-star"
                  variant="text"
                  size="small"
                  color="warning"
                  @click="promoteToCaptain(item)"
                >
                  <v-icon>mdi-star</v-icon>
                  <v-tooltip activator="parent" location="top">
                    Promote to Captain
                  </v-tooltip>
                </v-btn>

                <v-btn
                  icon="mdi-delete"
                  variant="text"
                  size="small"
                  color="error"
                  @click="confirmRemoveMember(item)"
                >
                  <v-icon>mdi-delete</v-icon>
                  <v-tooltip activator="parent" location="top">
                    Remove from Team
                  </v-tooltip>
                </v-btn>
              </div>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </template>

    <!-- Join Team Dialog -->
    <join-team-dialog
      v-model="showJoinDialog"
      :team="currentTeam"
      @request-sent="handleJoinRequestSent"
    />

    <!-- Join Requests Dialog (Captain Only) -->
    <join-requests-dialog
      v-model="showJoinRequestsDialog"
      :team-id="teamId"
      @request-reviewed="handleRequestReviewed"
    />

    <!-- Snackbar for notifications -->
    <v-snackbar
      v-model="showSnackbar"
      :color="snackbarColor"
      :timeout="3000"
    >
      {{ snackbarMessage }}
      <template #actions>
        <v-btn variant="text" @click="showSnackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTeamStore } from '@/stores/team'
import JoinTeamDialog from '@/components/JoinTeamDialog.vue'
import JoinRequestsDialog from '@/components/JoinRequestsDialog.vue'

const route = useRoute()
const teamStore = useTeamStore()

const teamId = route.params.id
const loading = ref(false)
const selectedPosition = ref('all')
const showJoinDialog = ref(false)
const showJoinRequestsDialog = ref(false)
const showEditDialog = ref(false)

// Snackbar
const showSnackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

// Computed
const currentTeam = computed(() => teamStore.currentTeam)
const teamMembers = computed(() => teamStore.teamMembers)
const isUserCaptain = computed(() => teamStore.isUserCaptain)
const pendingRequestsCount = computed(() => teamStore.pendingJoinRequests.length)

const filteredMembers = computed(() => {
  if (selectedPosition.value === 'all') {
    return teamMembers.value
  }
  return teamMembers.value.filter(
    m => m.player.position === selectedPosition.value
  )
})

const rosterHeaders = [
  { title: 'Player', key: 'player', sortable: false },
  { title: 'Jersey #', key: 'jersey_number', sortable: true },
  { title: 'Rating', key: 'rating', sortable: false },
  { title: 'Matches', key: 'matches_played', sortable: true },
  { title: 'Goals', key: 'goals', sortable: true },
  { title: 'Assists', key: 'assists', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false },
]

// Methods
function getPlayersByPosition(position) {
  return teamMembers.value.filter(m => m.player.position === position)
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

function formatYear(dateString) {
  return new Date(dateString).getFullYear()
}

async function promoteToCaptain(member) {
  try {
    await teamStore.promoteToCaptain(teamId, member.player_id)
    showNotification('Player promoted to captain', 'success')
  } catch (error) {
    showNotification('Failed to promote player', 'error')
  }
}

function confirmRemoveMember(member) {
  // Show confirmation dialog
  showNotification('Remove member feature coming soon', 'info')
}

function handleJoinRequestSent() {
  showNotification('Join request sent successfully!', 'success')
  showJoinDialog.value = false
}

async function handleRequestReviewed() {
  // Refresh team members
  await teamStore.fetchTeamMembers(teamId)
  showNotification('Request reviewed successfully', 'success')
}

function showNotification(message, color = 'success') {
  snackbarMessage.value = message
  snackbarColor.value = color
  showSnackbar.value = true
}

// Lifecycle
onMounted(async () => {
  loading.value = true
  try {
    await Promise.all([
      teamStore.fetchTeamById(teamId),
      teamStore.fetchTeamMembers(teamId),
    ])

    teamStore.setCurrentTeam(teamStore.getTeamById(teamId))

    // Load join requests if captain
    if (isUserCaptain.value) {
      await teamStore.fetchPendingJoinRequests(teamId)
    }
  } catch (error) {
    console.error('Failed to load team:', error)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.team-logo {
  border: 4px solid rgb(var(--v-theme-surface-variant));
}
</style>
