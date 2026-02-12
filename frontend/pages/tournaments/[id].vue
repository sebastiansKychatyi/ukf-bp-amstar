<template>
  <v-container class="py-8">
    <!-- Loading -->
    <v-row v-if="loading" justify="center" class="pa-12">
      <v-progress-circular indeterminate color="primary" size="48" />
    </v-row>

    <!-- Error -->
    <v-row v-else-if="error && !tournament">
      <v-col cols="12">
        <v-alert type="error">{{ error }}</v-alert>
        <v-btn class="mt-4" to="/tournaments" prepend-icon="mdi-arrow-left">Back to Tournaments</v-btn>
      </v-col>
    </v-row>

    <template v-else-if="tournament">
      <!-- Header -->
      <v-row>
        <v-col cols="12">
          <div class="d-flex align-center mb-1">
            <v-btn icon variant="text" to="/tournaments" class="mr-2">
              <v-icon>mdi-arrow-left</v-icon>
            </v-btn>
            <h1 :class="$vuetify.display.xs ? 'text-h5' : 'text-h3'" class="font-weight-bold">
              {{ tournament.name }}
            </h1>
          </div>
          <p v-if="tournament.description" class="text-body-1 text-medium-emphasis ml-12">
            {{ tournament.description }}
          </p>
        </v-col>
      </v-row>

      <!-- Info Cards -->
      <v-row class="mb-2">
        <v-col cols="6" sm="3">
          <v-card elevation="1" class="text-center pa-3">
            <v-chip :color="getStatusColor(tournament.status)" variant="flat" class="mb-1">
              {{ tournament.status.toUpperCase() }}
            </v-chip>
            <div class="text-caption text-medium-emphasis">Status</div>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card elevation="1" class="text-center pa-3">
            <v-chip
              :color="tournament.type === 'league' ? 'primary' : 'deep-purple'"
              variant="flat"
              class="mb-1"
            >
              {{ tournament.type === 'league' ? 'League' : 'Knockout' }}
            </v-chip>
            <div class="text-caption text-medium-emphasis">Format</div>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card elevation="1" class="text-center pa-3">
            <div class="text-h5 font-weight-bold">{{ tournament.participant_count || 0 }}</div>
            <div class="text-caption text-medium-emphasis">/ {{ tournament.max_teams }} Teams</div>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card elevation="1" class="text-center pa-3">
            <div class="text-h5 font-weight-bold">{{ tournament.current_round || 0 }}</div>
            <div class="text-caption text-medium-emphasis">Current Round</div>
          </v-card>
        </v-col>
      </v-row>

      <!-- Organiser Actions -->
      <v-row v-if="isOrganiser" class="mb-2">
        <v-col cols="12">
          <v-card elevation="1">
            <v-card-text class="d-flex align-center flex-wrap ga-2">
              <v-icon class="mr-1">mdi-cog</v-icon>
              <span class="font-weight-medium mr-4">Organiser Actions:</span>

              <v-btn
                v-if="tournament.status === 'draft'"
                color="info"
                variant="flat"
                size="small"
                prepend-icon="mdi-door-open"
                :loading="actionLoading === 'open'"
                @click="openRegistration"
              >
                Open Registration
              </v-btn>

              <v-btn
                v-if="tournament.status === 'registration'"
                color="success"
                variant="flat"
                size="small"
                prepend-icon="mdi-play"
                :loading="actionLoading === 'start'"
                :disabled="(tournament.participant_count || 0) < 2"
                @click="startTournament"
              >
                Start Tournament
              </v-btn>

              <v-btn
                v-if="!['completed', 'cancelled'].includes(tournament.status)"
                color="error"
                variant="outlined"
                size="small"
                prepend-icon="mdi-cancel"
                :loading="actionLoading === 'cancel'"
                @click="cancelTournament"
              >
                Cancel
              </v-btn>

              <v-btn
                v-if="['draft', 'cancelled'].includes(tournament.status)"
                color="error"
                variant="text"
                size="small"
                prepend-icon="mdi-delete"
                :loading="actionLoading === 'delete'"
                @click="deleteTournament"
              >
                Delete
              </v-btn>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Join / Leave (captain, during registration) -->
      <v-row v-if="isCaptain && tournament.status === 'registration'" class="mb-2">
        <v-col cols="12">
          <v-card elevation="1">
            <v-card-text class="d-flex align-center flex-wrap ga-2">
              <template v-if="!isTeamRegistered">
                <v-icon color="success" class="mr-1">mdi-account-plus</v-icon>
                <span class="mr-3">Registration is open!</span>
                <v-btn
                  color="success"
                  variant="flat"
                  size="small"
                  prepend-icon="mdi-plus"
                  :loading="actionLoading === 'join'"
                  @click="joinTournament"
                >
                  Register My Team
                </v-btn>
              </template>
              <template v-else>
                <v-icon color="primary" class="mr-1">mdi-check-circle</v-icon>
                <span class="mr-3">Your team is registered!</span>
                <v-btn
                  color="warning"
                  variant="outlined"
                  size="small"
                  prepend-icon="mdi-logout"
                  :loading="actionLoading === 'leave'"
                  @click="leaveTournament"
                >
                  Withdraw
                </v-btn>
              </template>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Error alert -->
      <v-row v-if="error">
        <v-col cols="12">
          <v-alert type="error" closable @click:close="error = null">{{ error }}</v-alert>
        </v-col>
      </v-row>

      <!-- Tabs -->
      <v-row>
        <v-col cols="12">
          <v-tabs v-model="activeTab" color="primary">
            <v-tab value="standings" prepend-icon="mdi-format-list-numbered">
              Standings
            </v-tab>
            <v-tab value="matches" prepend-icon="mdi-soccer-field">
              Matches
              <v-chip v-if="matches.length" size="x-small" class="ml-2">{{ matches.length }}</v-chip>
            </v-tab>
            <v-tab value="participants" prepend-icon="mdi-shield-account">
              Teams
              <v-chip v-if="tournament.participant_count" size="x-small" class="ml-2">{{ tournament.participant_count }}</v-chip>
            </v-tab>
          </v-tabs>
        </v-col>
      </v-row>

      <!-- Standings Tab -->
      <v-row v-if="activeTab === 'standings'">
        <v-col cols="12">
          <v-card elevation="2">
            <v-data-table
              :headers="standingsHeaders"
              :items="standings"
              :loading="standingsLoading"
              :items-per-page="-1"
              hover
              density="comfortable"
            >
              <!-- Rank -->
              <template #item.rank="{ index }">
                <v-avatar
                  v-if="index < 3"
                  size="28"
                  :color="index === 0 ? 'amber' : index === 1 ? 'grey-lighten-1' : 'brown-lighten-1'"
                >
                  <v-icon size="16" color="white">mdi-trophy</v-icon>
                </v-avatar>
                <span v-else class="font-weight-medium ml-1">{{ index + 1 }}</span>
              </template>

              <!-- Team name (clickable) -->
              <template #item.team="{ item }">
                <span
                  class="font-weight-medium text-primary cursor-pointer"
                  @click="navigateTo(`/teams/${item.team_id}`)"
                >
                  {{ item.team?.name || `Team #${item.team_id}` }}
                </span>
                <v-chip
                  v-if="item.is_eliminated"
                  size="x-small"
                  color="error"
                  variant="outlined"
                  class="ml-2"
                >
                  OUT
                </v-chip>
              </template>

              <!-- Points (highlighted) -->
              <template #item.points="{ item }">
                <v-chip color="primary" variant="flat" size="small">
                  {{ item.points }}
                </v-chip>
              </template>

              <!-- Goal difference (colored) -->
              <template #item.gd="{ item }">
                <span :class="gdColor(item.goal_difference)">
                  {{ item.goal_difference > 0 ? '+' : '' }}{{ item.goal_difference }}
                </span>
              </template>

              <!-- Goals -->
              <template #item.goals="{ item }">
                {{ item.goals_for }}:{{ item.goals_against }}
              </template>
            </v-data-table>
          </v-card>
        </v-col>
      </v-row>

      <!-- Matches Tab -->
      <v-row v-if="activeTab === 'matches'">
        <v-col cols="12">
          <!-- Group by round -->
          <div v-if="matches.length === 0" class="text-center pa-12">
            <v-icon icon="mdi-soccer-field" size="64" color="grey-lighten-1" class="mb-4" />
            <h3 class="text-h5 mb-2">No matches yet</h3>
            <p class="text-medium-emphasis">Matches will appear once the tournament starts.</p>
          </div>

          <div v-for="round in matchesByRound" :key="round.round_number" class="mb-4">
            <h3 class="text-h6 font-weight-medium mb-2">
              <v-icon class="mr-1" size="small">mdi-calendar</v-icon>
              {{ round.label }}
            </h3>

            <v-card
              v-for="match in round.matches"
              :key="match.id"
              class="mb-2"
              elevation="1"
            >
              <v-card-text class="pa-3">
                <v-row align="center" no-gutters>
                  <!-- Home team -->
                  <v-col cols="4" class="text-center">
                    <span
                      class="font-weight-medium cursor-pointer"
                      :class="{ 'text-success': match.winner_team_id === match.home_team_id }"
                      @click="match.home_team_id ? navigateTo(`/teams/${match.home_team_id}`) : null"
                    >
                      {{ match.home_team?.name || 'TBD' }}
                    </span>
                    <div v-if="match.home_team?.rating" class="text-caption text-medium-emphasis">
                      ELO: {{ match.home_team.rating }}
                    </div>
                  </v-col>

                  <!-- Score / Status -->
                  <v-col cols="4" class="text-center">
                    <template v-if="match.home_score !== null && match.home_score !== undefined">
                      <div class="text-h5 font-weight-bold">
                        {{ match.home_score }} - {{ match.away_score }}
                      </div>
                      <v-chip size="x-small" color="success" variant="flat">Played</v-chip>
                    </template>
                    <template v-else-if="!match.away_team_id">
                      <v-chip size="small" color="grey" variant="outlined">BYE</v-chip>
                    </template>
                    <template v-else>
                      <div class="text-h5 font-weight-bold text-medium-emphasis">VS</div>
                      <!-- Submit result button -->
                      <v-btn
                        v-if="canSubmitResult(match)"
                        size="x-small"
                        color="primary"
                        variant="flat"
                        class="mt-1"
                        @click="openResultDialog(match)"
                      >
                        Submit Result
                      </v-btn>
                    </template>
                  </v-col>

                  <!-- Away team -->
                  <v-col cols="4" class="text-center">
                    <template v-if="match.away_team_id">
                      <span
                        class="font-weight-medium cursor-pointer"
                        :class="{ 'text-success': match.winner_team_id === match.away_team_id }"
                        @click="navigateTo(`/teams/${match.away_team_id}`)"
                      >
                        {{ match.away_team?.name || 'TBD' }}
                      </span>
                      <div v-if="match.away_team?.rating" class="text-caption text-medium-emphasis">
                        ELO: {{ match.away_team.rating }}
                      </div>
                    </template>
                    <span v-else class="text-medium-emphasis">BYE</span>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </div>
        </v-col>
      </v-row>

      <!-- Participants Tab -->
      <v-row v-if="activeTab === 'participants'">
        <v-col cols="12">
          <v-card elevation="2">
            <v-data-table
              :headers="participantHeaders"
              :items="tournament.participants || []"
              :items-per-page="-1"
              hover
              density="comfortable"
            >
              <template #item.seed="{ item }">
                <v-chip size="small" variant="outlined">
                  #{{ item.seed || '-' }}
                </v-chip>
              </template>

              <template #item.team="{ item }">
                <span
                  class="font-weight-medium text-primary cursor-pointer"
                  @click="navigateTo(`/teams/${item.team_id}`)"
                >
                  {{ item.team?.name || `Team #${item.team_id}` }}
                </span>
              </template>

              <template #item.rating="{ item }">
                <v-chip :color="getRatingColor(item.team?.rating)" size="small" variant="flat">
                  {{ item.team?.rating || 1000 }}
                </v-chip>
              </template>

              <template #item.city="{ item }">
                <v-chip v-if="item.team?.city" size="small" variant="outlined">
                  <v-icon start size="small">mdi-map-marker</v-icon>
                  {{ item.team.city }}
                </v-chip>
                <span v-else class="text-medium-emphasis">-</span>
              </template>

              <template #item.status="{ item }">
                <v-chip
                  :color="item.is_eliminated ? 'error' : 'success'"
                  size="small"
                  variant="flat"
                >
                  {{ item.is_eliminated ? 'Eliminated' : 'Active' }}
                </v-chip>
              </template>
            </v-data-table>
          </v-card>
        </v-col>
      </v-row>
    </template>

    <!-- Submit Result Dialog -->
    <v-dialog v-model="showResultDialog" max-width="420" persistent>
      <v-card>
        <v-card-title>
          <v-icon class="mr-2">mdi-scoreboard</v-icon>
          Submit Match Result
        </v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model.number="matchResult.home_score"
                :label="resultMatch?.home_team?.name || 'Home'"
                type="number"
                min="0"
                max="99"
                variant="outlined"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model.number="matchResult.away_score"
                :label="resultMatch?.away_team?.name || 'Away'"
                type="number"
                min="0"
                max="99"
                variant="outlined"
              />
            </v-col>
          </v-row>
          <v-alert
            v-if="tournament?.type === 'knockout'"
            type="warning"
            variant="tonal"
            density="compact"
            class="mt-1"
          >
            Knockout match — draws are not allowed. The losing team will be eliminated.
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showResultDialog = false">Cancel</v-btn>
          <v-btn
            color="success"
            :loading="submitting"
            :disabled="matchResult.home_score < 0 || matchResult.away_score < 0"
            @click="submitResult"
          >
            Submit Result
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="showSnackbar" :color="snackbarColor" :timeout="3000">
      {{ snackbarMessage }}
      <template #actions>
        <v-btn variant="text" @click="showSnackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'

definePageMeta({
  middleware: ['auth'],
})

const route = useRoute()
const tournamentId = computed(() => Number(route.params.id))
const { user, isAuthenticated, isCaptain, isReferee } = useAuth()
const config = useRuntimeConfig()
const apiBase = computed(() => config.public.apiBaseUrl || 'http://localhost:8000/api/v1')

const getAuthHeaders = () => {
  const token = useCookie('auth_token')
  return token.value ? { Authorization: `Bearer ${token.value}` } : {}
}

// State
const tournament = ref<any>(null)
const standings = ref<any[]>([])
const matches = ref<any[]>([])
const myTeam = ref<any>(null)
const loading = ref(true)
const standingsLoading = ref(false)
const submitting = ref(false)
const actionLoading = ref<string | null>(null)
const error = ref<string | null>(null)
const activeTab = ref('standings')

// Result dialog
const showResultDialog = ref(false)
const resultMatch = ref<any>(null)
const matchResult = ref({ home_score: 0, away_score: 0 })

// Snackbar
const showSnackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

// Computed
const isOrganiser = computed(() =>
  user.value && tournament.value && tournament.value.created_by_id === user.value.id
)

const isTeamRegistered = computed(() => {
  if (!myTeam.value || !tournament.value?.participants) return false
  return tournament.value.participants.some((p: any) => p.team_id === myTeam.value.id)
})

const matchesByRound = computed(() => {
  if (!matches.value.length) return []
  const groups: Record<number, any[]> = {}
  for (const m of matches.value) {
    if (!groups[m.round_number]) groups[m.round_number] = []
    groups[m.round_number].push(m)
  }

  const totalRounds = Math.max(...Object.keys(groups).map(Number))

  return Object.keys(groups)
    .map(Number)
    .sort((a, b) => a - b)
    .map(rnd => ({
      round_number: rnd,
      label: tournament.value?.type === 'knockout'
        ? roundName(rnd, totalRounds)
        : `Round ${rnd}`,
      matches: groups[rnd],
    }))
})

// Table headers
const standingsHeaders = computed(() => {
  const headers: any[] = [
    { title: '#', key: 'rank', width: '50px', sortable: false },
    { title: 'Team', key: 'team', sortable: false },
    { title: 'P', key: 'played', align: 'center' as const, width: '50px' },
    { title: 'W', key: 'wins', align: 'center' as const, width: '50px' },
    { title: 'D', key: 'draws', align: 'center' as const, width: '50px' },
    { title: 'L', key: 'losses', align: 'center' as const, width: '50px' },
    { title: 'GF:GA', key: 'goals', align: 'center' as const, width: '70px', sortable: false },
    { title: 'GD', key: 'gd', align: 'center' as const, width: '60px', sortable: false },
    { title: 'Pts', key: 'points', align: 'center' as const, width: '60px' },
  ]
  return headers
})

const participantHeaders = [
  { title: 'Seed', key: 'seed', width: '70px', align: 'center' as const },
  { title: 'Team', key: 'team', sortable: false },
  { title: 'Rating', key: 'rating', align: 'center' as const },
  { title: 'City', key: 'city', sortable: false },
  { title: 'Status', key: 'status', align: 'center' as const },
]

// ── Data Fetching ──

const fetchTournament = async () => {
  try {
    const data = await $fetch<any>(`${apiBase.value}/tournaments/${tournamentId.value}`, {
      headers: getAuthHeaders(),
    })
    tournament.value = data
    matches.value = data.matches || []
  } catch (err: any) {
    error.value = err.data?.detail || 'Failed to load tournament'
  }
}

const fetchStandings = async () => {
  standingsLoading.value = true
  try {
    const data = await $fetch<any>(`${apiBase.value}/tournaments/${tournamentId.value}/standings`, {
      headers: getAuthHeaders(),
    })
    standings.value = data.standings || []
  } catch {
    standings.value = tournament.value?.participants || []
  } finally {
    standingsLoading.value = false
  }
}

const fetchMyTeam = async () => {
  try {
    const data = await $fetch<any>(`${apiBase.value}/teams/my/team`, {
      headers: getAuthHeaders(),
    })
    myTeam.value = data
  } catch {
    myTeam.value = null
  }
}

const refreshAll = async () => {
  await fetchTournament()
  await fetchStandings()
}

// ── Organiser Actions ──

const openRegistration = async () => {
  actionLoading.value = 'open'
  try {
    await $fetch(`${apiBase.value}/tournaments/${tournamentId.value}/open-registration`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    showMessage('Registration opened!', 'success')
    await refreshAll()
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to open registration', 'error')
  } finally {
    actionLoading.value = null
  }
}

const startTournament = async () => {
  actionLoading.value = 'start'
  try {
    await $fetch(`${apiBase.value}/tournaments/${tournamentId.value}/start`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    showMessage('Tournament started! Fixtures generated.', 'success')
    await refreshAll()
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to start tournament', 'error')
  } finally {
    actionLoading.value = null
  }
}

const cancelTournament = async () => {
  actionLoading.value = 'cancel'
  try {
    await $fetch(`${apiBase.value}/tournaments/${tournamentId.value}/cancel`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    showMessage('Tournament cancelled.', 'warning')
    await refreshAll()
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to cancel', 'error')
  } finally {
    actionLoading.value = null
  }
}

const deleteTournament = async () => {
  actionLoading.value = 'delete'
  try {
    await $fetch(`${apiBase.value}/tournaments/${tournamentId.value}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    })
    showMessage('Tournament deleted.', 'success')
    navigateTo('/tournaments')
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to delete', 'error')
  } finally {
    actionLoading.value = null
  }
}

// ── Join / Leave ──

const joinTournament = async () => {
  if (!myTeam.value) {
    showMessage('You need to be in a team first', 'error')
    return
  }
  actionLoading.value = 'join'
  try {
    await $fetch(`${apiBase.value}/tournaments/${tournamentId.value}/join`, {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: { team_id: myTeam.value.id },
    })
    showMessage('Team registered!', 'success')
    await refreshAll()
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to join', 'error')
  } finally {
    actionLoading.value = null
  }
}

const leaveTournament = async () => {
  if (!myTeam.value) return
  actionLoading.value = 'leave'
  try {
    await $fetch(`${apiBase.value}/tournaments/${tournamentId.value}/leave/${myTeam.value.id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    })
    showMessage('Team withdrawn from tournament.', 'warning')
    await refreshAll()
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to leave', 'error')
  } finally {
    actionLoading.value = null
  }
}

// ── Match Result ──

const canSubmitResult = (match: any) => {
  if (!user.value || !tournament.value) return false
  if (tournament.value.status !== 'active') return false
  if (match.home_score !== null && match.home_score !== undefined) return false
  if (!match.away_team_id) return false

  const isOrg = tournament.value.created_by_id === user.value.id
  const isHomeCaptain = match.home_team?.captain_id === user.value.id
  const isAwayCaptain = match.away_team?.captain_id === user.value.id

  // Also check if myTeam is one of the teams
  if (myTeam.value) {
    if (match.home_team_id === myTeam.value.id || match.away_team_id === myTeam.value.id) {
      return true
    }
  }

  return isOrg || isHomeCaptain || isAwayCaptain
}

const openResultDialog = (match: any) => {
  resultMatch.value = match
  matchResult.value = { home_score: 0, away_score: 0 }
  showResultDialog.value = true
}

const submitResult = async () => {
  if (!resultMatch.value) return
  submitting.value = true
  try {
    await $fetch(
      `${apiBase.value}/tournaments/${tournamentId.value}/matches/${resultMatch.value.id}/result`,
      {
        method: 'POST',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: matchResult.value,
      }
    )
    showResultDialog.value = false
    showMessage('Result submitted! Standings updated.', 'success')
    await refreshAll()
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to submit result', 'error')
  } finally {
    submitting.value = false
  }
}

// ── Helpers ──

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    draft: 'grey', registration: 'info', active: 'success', completed: 'primary', cancelled: 'error',
  }
  return colors[status] || 'grey'
}

const getRatingColor = (rating: number) => {
  if (!rating) return 'grey'
  if (rating >= 1500) return 'success'
  if (rating >= 1200) return 'primary'
  if (rating >= 900) return 'warning'
  return 'error'
}

const gdColor = (gd: number) => {
  if (gd > 0) return 'text-success font-weight-medium'
  if (gd < 0) return 'text-error font-weight-medium'
  return 'text-medium-emphasis'
}

const roundName = (round: number, totalRounds: number) => {
  const remaining = totalRounds - round
  if (remaining === 0) return 'Final'
  if (remaining === 1) return 'Semi-finals'
  if (remaining === 2) return 'Quarter-finals'
  if (remaining === 3) return 'Round of 16'
  return `Round ${round}`
}

const showMessage = (message: string, color: string) => {
  snackbarMessage.value = message
  snackbarColor.value = color
  showSnackbar.value = true
}

// Refresh standings when switching to that tab
watch(activeTab, (tab) => {
  if (tab === 'standings') fetchStandings()
})

onMounted(async () => {
  loading.value = true
  await Promise.all([fetchTournament(), fetchMyTeam()])
  await fetchStandings()
  loading.value = false
})
</script>

<style scoped>
.cursor-pointer { cursor: pointer; }
</style>
