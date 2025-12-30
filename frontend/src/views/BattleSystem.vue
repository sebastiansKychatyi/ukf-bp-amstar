<template>
  <v-container fluid class="pa-6">
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center justify-space-between mb-6">
          <div>
            <h1 class="text-h4 font-weight-bold mb-2">
              <v-icon size="32" color="error" class="mr-2">
                mdi-sword-cross
              </v-icon>
              Battle System
            </h1>
            <p class="text-medium-emphasis">
              Challenge other teams and prove your dominance
            </p>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Stats Overview (Captain Only) -->
    <v-row v-if="userTeam" class="mb-6">
      <v-col cols="12" md="3">
        <v-card variant="tonal" color="info">
          <v-card-text class="text-center pa-6">
            <v-icon size="48">mdi-trophy</v-icon>
            <div class="text-h4 font-weight-bold mt-3">{{ userTeam.total_wins }}</div>
            <div class="text-caption">Battles Won</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card variant="tonal" color="success">
          <v-card-text class="text-center pa-6">
            <v-icon size="48">mdi-star</v-icon>
            <div class="text-h4 font-weight-bold mt-3">
              {{ userTeam.team_rating.toFixed(1) }}
            </div>
            <div class="text-caption">Team Rating</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card variant="tonal" color="warning">
          <v-card-text class="text-center pa-6">
            <v-icon size="48">mdi-clock-outline</v-icon>
            <div class="text-h4 font-weight-bold mt-3">3</div>
            <div class="text-caption">Pending Challenges</div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="3">
        <v-card variant="tonal" color="error">
          <v-card-text class="text-center pa-6">
            <v-icon size="48">mdi-fire</v-icon>
            <div class="text-h4 font-weight-bold mt-3">5</div>
            <div class="text-caption">Win Streak</div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Filters -->
    <v-row class="mb-4">
      <v-col cols="12" md="6">
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          label="Search teams..."
          variant="outlined"
          clearable
          hide-details
        />
      </v-col>

      <v-col cols="12" md="3">
        <v-select
          v-model="ratingFilter"
          :items="ratingFilterOptions"
          label="Filter by Rating"
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
    </v-row>

    <!-- Loading State -->
    <v-row v-if="teamStore.loading">
      <v-col cols="12" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" />
        <p class="text-h6 mt-4">Loading teams...</p>
      </v-col>
    </v-row>

    <!-- Teams Grid -->
    <v-row v-else>
      <v-col
        v-for="team in filteredTeams"
        :key="team.id"
        cols="12"
        sm="6"
        md="4"
        lg="3"
      >
        <v-card class="team-battle-card" :elevation="hover === team.id ? 8 : 2">
          <!-- Team Header -->
          <v-card-title class="pa-4">
            <div class="d-flex align-center">
              <v-avatar
                :color="team.team_color || 'primary'"
                size="48"
                class="mr-3"
              >
                <v-img v-if="team.logo_url" :src="team.logo_url" cover />
                <v-icon v-else color="white">mdi-shield</v-icon>
              </v-avatar>
              <div class="flex-grow-1">
                <div class="text-subtitle-1 font-weight-bold text-truncate">
                  {{ team.name }}
                </div>
                <div class="text-caption text-medium-emphasis">
                  {{ team.home_city }}
                </div>
              </div>
            </div>
          </v-card-title>

          <v-divider />

          <!-- Team Stats -->
          <v-card-text class="pa-4">
            <!-- Rating -->
            <div class="mb-3">
              <div class="d-flex align-center justify-space-between mb-1">
                <span class="text-caption text-medium-emphasis">Rating</span>
                <v-chip
                  :color="getRatingColor(team.team_rating)"
                  size="small"
                  variant="flat"
                  class="font-weight-bold"
                >
                  {{ team.team_rating.toFixed(1) }}
                </v-chip>
              </div>
              <v-progress-linear
                :model-value="team.team_rating"
                :color="getRatingColor(team.team_rating)"
                height="6"
                rounded
              />
            </div>

            <!-- Match Statistics -->
            <v-row dense>
              <v-col cols="4">
                <div class="text-center">
                  <div class="text-h6 font-weight-bold text-success">
                    {{ team.total_wins }}
                  </div>
                  <div class="text-caption text-medium-emphasis">Wins</div>
                </div>
              </v-col>
              <v-col cols="4">
                <div class="text-center">
                  <div class="text-h6 font-weight-bold">
                    {{ team.total_draws }}
                  </div>
                  <div class="text-caption text-medium-emphasis">Draws</div>
                </div>
              </v-col>
              <v-col cols="4">
                <div class="text-center">
                  <div class="text-h6 font-weight-bold text-error">
                    {{ team.total_losses }}
                  </div>
                  <div class="text-caption text-medium-emphasis">Losses</div>
                </div>
              </v-col>
            </v-row>

            <!-- Goal Difference -->
            <div class="mt-3 text-center">
              <v-chip
                :color="getGoalDifferenceColor(team)"
                size="small"
                variant="tonal"
              >
                <v-icon start size="16">mdi-soccer</v-icon>
                {{ getGoalDifference(team) > 0 ? '+' : '' }}{{ getGoalDifference(team) }}
                Goal Difference
              </v-chip>
            </div>

            <!-- Match Probability (Mock) -->
            <div v-if="userTeam" class="mt-4">
              <div class="text-caption text-medium-emphasis text-center mb-2">
                Win Probability
              </div>
              <div class="d-flex align-center ga-2">
                <v-chip size="x-small" color="success" variant="flat">
                  {{ calculateWinProbability(userTeam, team) }}%
                </v-chip>
                <v-progress-linear
                  :model-value="calculateWinProbability(userTeam, team)"
                  color="success"
                  height="8"
                  rounded
                />
              </div>
            </div>
          </v-card-text>

          <v-divider />

          <!-- Actions -->
          <v-card-actions class="pa-3">
            <v-btn
              variant="text"
              prepend-icon="mdi-eye"
              size="small"
              @click="viewTeamDetails(team)"
            >
              View
            </v-btn>
            <v-spacer />
            <v-btn
              color="error"
              variant="flat"
              prepend-icon="mdi-sword-cross"
              size="small"
              :disabled="!canChallenge(team)"
              @click="challengeTeam(team)"
            >
              Challenge
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- Empty State -->
      <v-col v-if="filteredTeams.length === 0" cols="12">
        <v-card variant="outlined" class="text-center py-12">
          <v-icon size="64" color="grey-lighten-1">
            mdi-shield-search
          </v-icon>
          <p class="text-h6 mt-4">No teams found</p>
          <p class="text-medium-emphasis">
            Try adjusting your filters or search query
          </p>
        </v-card>
      </v-col>
    </v-row>

    <!-- Challenge Dialog -->
    <v-dialog v-model="showChallengeDialog" max-width="600">
      <v-card v-if="selectedTeam">
        <v-card-title class="pa-6 bg-error">
          <div class="text-h5 font-weight-bold text-white">
            <v-icon color="white" class="mr-2">mdi-sword-cross</v-icon>
            Challenge {{ selectedTeam.name }}
          </div>
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-6">
          <!-- VS Display -->
          <div class="text-center mb-6">
            <div class="d-flex align-center justify-center ga-4">
              <div class="text-center">
                <v-avatar :color="userTeam.team_color" size="80">
                  <v-img v-if="userTeam.logo_url" :src="userTeam.logo_url" />
                  <v-icon v-else size="48" color="white">mdi-shield</v-icon>
                </v-avatar>
                <div class="text-h6 font-weight-bold mt-2">
                  {{ userTeam.name }}
                </div>
                <v-chip color="success" size="small" variant="flat">
                  {{ userTeam.team_rating.toFixed(1) }}
                </v-chip>
              </div>

              <div class="text-h2 font-weight-bold text-error">VS</div>

              <div class="text-center">
                <v-avatar :color="selectedTeam.team_color" size="80">
                  <v-img v-if="selectedTeam.logo_url" :src="selectedTeam.logo_url" />
                  <v-icon v-else size="48" color="white">mdi-shield</v-icon>
                </v-avatar>
                <div class="text-h6 font-weight-bold mt-2">
                  {{ selectedTeam.name }}
                </div>
                <v-chip color="info" size="small" variant="flat">
                  {{ selectedTeam.team_rating.toFixed(1) }}
                </v-chip>
              </div>
            </div>
          </div>

          <!-- Challenge Details -->
          <v-textarea
            v-model="challengeMessage"
            label="Challenge Message (Optional)"
            placeholder="Add a message to your challenge..."
            rows="3"
            variant="outlined"
          />

          <!-- Match Date/Time -->
          <v-row>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="matchDate"
                label="Proposed Match Date"
                type="date"
                variant="outlined"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="matchTime"
                label="Proposed Match Time"
                type="time"
                variant="outlined"
              />
            </v-col>
          </v-row>

          <v-alert type="info" variant="tonal">
            The challenged team will receive your request and can accept or decline
          </v-alert>
        </v-card-text>

        <v-divider />

        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn @click="showChallengeDialog = false">Cancel</v-btn>
          <v-btn
            color="error"
            variant="flat"
            :loading="sendingChallenge"
            @click="sendChallenge"
          >
            Send Challenge
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Success Snackbar -->
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
import { useRouter } from 'vue-router'
import { useTeamStore } from '@/stores/team'

const router = useRouter()
const teamStore = useTeamStore()

// State
const search = ref('')
const ratingFilter = ref(null)
const sortBy = ref('rating')
const hover = ref(null)
const showChallengeDialog = ref(false)
const selectedTeam = ref(null)
const challengeMessage = ref('')
const matchDate = ref('')
const matchTime = ref('')
const sendingChallenge = ref(false)

// Snackbar
const showSnackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

// Mock user team (in real app, get from auth/team store)
const userTeam = ref({
  id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
  name: 'Thunder FC',
  team_color: '#1E40AF',
  team_rating: 72.5,
  total_wins: 18,
  total_draws: 4,
  total_losses: 3,
})

// Options
const ratingFilterOptions = [
  { title: 'Similar Rating (±10)', value: 'similar' },
  { title: 'Lower Rating', value: 'lower' },
  { title: 'Higher Rating', value: 'higher' },
]

const sortOptions = [
  { title: 'Highest Rating', value: 'rating' },
  { title: 'Most Wins', value: 'wins' },
  { title: 'Alphabetical', value: 'name' },
]

// Computed
const filteredTeams = computed(() => {
  let teams = [...teamStore.teams].filter(t => t.id !== userTeam.value?.id)

  // Search filter
  if (search.value) {
    const searchLower = search.value.toLowerCase()
    teams = teams.filter(t =>
      t.name.toLowerCase().includes(searchLower) ||
      t.home_city?.toLowerCase().includes(searchLower)
    )
  }

  // Rating filter
  if (ratingFilter.value && userTeam.value) {
    const userRating = userTeam.value.team_rating
    teams = teams.filter(t => {
      if (ratingFilter.value === 'similar') {
        return Math.abs(t.team_rating - userRating) <= 10
      } else if (ratingFilter.value === 'lower') {
        return t.team_rating < userRating
      } else if (ratingFilter.value === 'higher') {
        return t.team_rating > userRating
      }
      return true
    })
  }

  // Sort
  teams.sort((a, b) => {
    if (sortBy.value === 'rating') {
      return b.team_rating - a.team_rating
    } else if (sortBy.value === 'wins') {
      return b.total_wins - a.total_wins
    } else if (sortBy.value === 'name') {
      return a.name.localeCompare(b.name)
    }
    return 0
  })

  return teams
})

// Methods
function getRatingColor(rating) {
  if (rating >= 80) return 'success'
  if (rating >= 60) return 'info'
  if (rating >= 40) return 'warning'
  return 'error'
}

function getGoalDifference(team) {
  return team.total_goals_scored - team.total_goals_conceded
}

function getGoalDifferenceColor(team) {
  const diff = getGoalDifference(team)
  if (diff > 10) return 'success'
  if (diff > 0) return 'info'
  if (diff === 0) return 'grey'
  return 'error'
}

function calculateWinProbability(team1, team2) {
  // Simple probability based on rating difference
  const ratingDiff = team1.team_rating - team2.team_rating
  const baseProbability = 50
  const probabilityAdjustment = ratingDiff * 1.5

  const probability = Math.round(
    Math.max(10, Math.min(90, baseProbability + probabilityAdjustment))
  )

  return probability
}

function canChallenge(team) {
  // Check if user has a team and team is active
  return userTeam.value && team.is_active && team.is_recruiting
}

function viewTeamDetails(team) {
  router.push(`/teams/${team.id}`)
}

function challengeTeam(team) {
  selectedTeam.value = team
  showChallengeDialog.value = true
}

async function sendChallenge() {
  sendingChallenge.value = true

  try {
    // Mock API call
    await new Promise(resolve => setTimeout(resolve, 1000))

    showNotification('Challenge sent successfully!', 'success')
    showChallengeDialog.value = false

    // Reset form
    challengeMessage.value = ''
    matchDate.value = ''
    matchTime.value = ''
    selectedTeam.value = null
  } catch (error) {
    showNotification('Failed to send challenge', 'error')
  } finally {
    sendingChallenge.value = false
  }
}

function showNotification(message, color = 'success') {
  snackbarMessage.value = message
  snackbarColor.value = color
  showSnackbar.value = true
}

// Lifecycle
onMounted(async () => {
  await teamStore.fetchAllTeams()
})
</script>

<style scoped>
.team-battle-card {
  transition: all 0.3s ease;
  height: 100%;
}

.team-battle-card:hover {
  transform: translateY(-4px);
}
</style>
