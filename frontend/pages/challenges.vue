<template>
  <v-container class="py-8">
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center flex-wrap ga-2">
          <div>
            <h1 :class="$vuetify.display.xs ? 'text-h4' : 'text-h3'" class="font-weight-bold mb-2">
              <v-icon icon="mdi-sword-cross" :size="$vuetify.display.xs ? 'default' : 'large'" class="mr-2" />
              Challenges
            </h1>
            <p class="text-body-1 text-medium-emphasis">
              Create, accept, and manage team challenges
            </p>
          </div>

          <v-btn
            v-if="isCaptain"
            color="primary"
            prepend-icon="mdi-plus"
            @click="showCreateDialog = true"
          >
            New Challenge
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Filters -->
    <v-row class="mb-2">
      <v-col cols="12" sm="6" md="4">
        <v-select
          v-model="statusFilter"
          :items="statusOptions"
          label="Filter by status"
          variant="outlined"
          density="comfortable"
          hide-details
          clearable
        />
      </v-col>
      <v-col cols="12" sm="6" md="4">
        <v-btn-toggle v-model="viewMode" mandatory density="comfortable" variant="outlined">
          <v-btn value="all" prepend-icon="mdi-format-list-bulleted">All</v-btn>
          <v-btn v-if="isAuthenticated" value="my" prepend-icon="mdi-account">My Team</v-btn>
        </v-btn-toggle>
      </v-col>
    </v-row>

    <!-- Error -->
    <v-row v-if="error">
      <v-col cols="12">
        <v-alert type="error" closable @click:close="error = null">{{ error }}</v-alert>
      </v-col>
    </v-row>

    <!-- Challenges List -->
    <v-row>
      <v-col cols="12">
        <v-card v-if="loading" class="pa-8 text-center">
          <v-progress-circular indeterminate color="primary" />
          <p class="mt-4 text-medium-emphasis">Loading challenges...</p>
        </v-card>

        <div v-else-if="challenges.length === 0" class="text-center pa-12">
          <v-icon icon="mdi-sword-cross" size="64" color="grey-lighten-1" class="mb-4" />
          <h3 class="text-h5 mb-2">No challenges found</h3>
          <p class="text-medium-emphasis">
            {{ isCaptain ? 'Create the first challenge to get started!' : 'No challenges yet.' }}
          </p>
        </div>

        <v-card v-for="challenge in challenges" :key="challenge.id" class="mb-3" elevation="2">
          <v-card-text class="pa-4">
            <v-row align="center">
              <!-- Challenger -->
              <v-col cols="12" sm="4" class="text-center">
                <v-chip color="primary" variant="flat" class="mb-1">
                  <v-icon start>mdi-shield</v-icon>
                  {{ challenge.challenger?.name || 'Team' }}
                </v-chip>
                <div class="text-caption text-medium-emphasis">
                  ELO: {{ challenge.challenger?.rating || 1000 }}
                </div>
              </v-col>

              <!-- VS / Status -->
              <v-col cols="12" sm="4" class="text-center">
                <v-chip :color="getStatusColor(challenge.status)" variant="flat" class="mb-2">
                  {{ challenge.status.toUpperCase() }}
                </v-chip>
                <div v-if="challenge.status === 'completed'" class="text-h5 font-weight-bold">
                  {{ challenge.challenger_score }} - {{ challenge.opponent_score }}
                </div>
                <div v-else class="text-h5 font-weight-bold text-medium-emphasis">VS</div>
                <div v-if="challenge.match_date" class="text-caption mt-1">
                  <v-icon size="small">mdi-calendar</v-icon>
                  {{ formatDate(challenge.match_date) }}
                </div>
                <div v-if="challenge.location" class="text-caption">
                  <v-icon size="small">mdi-map-marker</v-icon>
                  {{ challenge.location }}
                </div>
              </v-col>

              <!-- Opponent -->
              <v-col cols="12" sm="4" class="text-center">
                <v-chip color="error" variant="flat" class="mb-1">
                  <v-icon start>mdi-shield</v-icon>
                  {{ challenge.opponent?.name || 'Team' }}
                </v-chip>
                <div class="text-caption text-medium-emphasis">
                  ELO: {{ challenge.opponent?.rating || 1000 }}
                </div>
              </v-col>
            </v-row>
          </v-card-text>

          <!-- Actions -->
          <v-card-actions v-if="getActions(challenge).length > 0">
            <v-spacer />
            <v-btn
              v-for="action in getActions(challenge)"
              :key="action.label"
              :color="action.color"
              :variant="action.variant || 'text'"
              size="small"
              :prepend-icon="action.icon"
              :loading="actionLoading === `${challenge.id}-${action.action}`"
              @click="handleAction(challenge, action.action)"
            >
              {{ action.label }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create Challenge Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="500" persistent>
      <v-card>
        <v-card-title>
          <v-icon class="mr-2">mdi-sword-cross</v-icon>
          New Challenge
        </v-card-title>
        <v-card-text>
          <v-select
            v-model="newChallenge.opponent_id"
            :items="availableTeams"
            item-title="name"
            item-value="id"
            label="Select Opponent *"
            variant="outlined"
            :rules="[v => !!v || 'Select an opponent']"
            class="mb-3"
          >
            <template #item="{ item, props }">
              <v-list-item v-bind="props">
                <template #append>
                  <v-chip size="small" :color="getRatingColor(item.raw.rating_score)">
                    {{ item.raw.rating_score || 1000 }}
                  </v-chip>
                </template>
              </v-list-item>
            </template>
          </v-select>

          <v-text-field
            v-model="newChallenge.match_date"
            label="Match Date & Time"
            type="datetime-local"
            variant="outlined"
            class="mb-3"
          />

          <v-text-field
            v-model="newChallenge.location"
            label="Location"
            variant="outlined"
            prepend-inner-icon="mdi-map-marker"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showCreateDialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            :loading="submitting"
            :disabled="!newChallenge.opponent_id"
            @click="createChallenge"
          >
            Send Challenge
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>


    <v-dialog v-model="showResultDialog" max-width="680" persistent scrollable>
      <v-card>

        <v-card-title class="d-flex align-center ga-2 py-3 px-4">
          <v-icon class="mr-1">mdi-scoreboard</v-icon>
          Submit Match Result
          <v-spacer />
          <div class="d-flex align-center ga-1">
            <v-chip
              size="small"
              :color="resultStep === 1 ? 'primary' : 'grey-lighten-1'"
              :variant="resultStep === 1 ? 'flat' : 'tonal'"
            >
              1 Score
            </v-chip>
            <v-icon size="small" color="grey">mdi-chevron-right</v-icon>
            <v-chip
              size="small"
              :color="resultStep === 2 ? 'primary' : 'grey-lighten-1'"
              :variant="resultStep === 2 ? 'flat' : 'tonal'"
            >
              2 Player Stats
            </v-chip>
          </div>
        </v-card-title>

        <v-divider />

        <!-- ── Step 1: Final Score ────────────────────────────────────────── -->
        <v-card-text v-if="resultStep === 1" class="pa-6">
          <p class="text-body-2 text-medium-emphasis mb-5">
            Enter the final score. If goals were scored you will be able to assign
            them to individual players in the next step.
          </p>

          <v-row align="center" justify="center">
            <!-- Challenger score -->
            <v-col cols="5" class="text-center">
              <div class="text-caption text-primary font-weight-bold text-uppercase mb-2">
                <v-icon size="small" color="primary" class="mr-1">mdi-shield</v-icon>
                {{ resultChallenge?.challenger?.name || 'Challenger' }}
              </div>
              <v-text-field
                v-model.number="matchResult.challenger_score"
                type="number"
                min="0"
                max="99"
                variant="outlined"
                hide-details
                density="comfortable"
                style="font-size: 1.5rem;"
                class="text-center-input"
              />
            </v-col>

            <!-- Divider -->
            <v-col cols="2" class="text-center text-h5 font-weight-bold text-medium-emphasis">
              —
            </v-col>

            <!-- Opponent score -->
            <v-col cols="5" class="text-center">
              <div class="text-caption text-error font-weight-bold text-uppercase mb-2">
                <v-icon size="small" color="error" class="mr-1">mdi-shield</v-icon>
                {{ resultChallenge?.opponent?.name || 'Opponent' }}
              </div>
              <v-text-field
                v-model.number="matchResult.opponent_score"
                type="number"
                min="0"
                max="99"
                variant="outlined"
                hide-details
                density="comfortable"
                class="text-center-input"
              />
            </v-col>
          </v-row>
        </v-card-text>

        <!-- ── Step 2: Player Stats ───────────────────────────────────────── -->
        <v-card-text v-else-if="resultStep === 2" class="pa-4">
          <!-- Loading rosters -->
          <div v-if="rosterLoading" class="text-center py-6">
            <v-progress-circular indeterminate color="primary" class="mb-3" />
            <p class="text-medium-emphasis">Loading rosters…</p>
          </div>

          <template v-else>
            <!-- Validation banner -->
            <v-alert
              :type="goalsMatchScore ? 'success' : 'warning'"
              variant="tonal"
              density="compact"
              class="mb-4"
            >
              <template v-if="goalsMatchScore">
                All goals are assigned correctly — ready to submit!
              </template>
              <template v-else>
                Distribute goals to match the score:
                <strong>{{ resultChallenge?.challenger?.name }}</strong>
                {{ challengerGoalSum }} / {{ matchResult.challenger_score }}
                &nbsp;·&nbsp;
                <strong>{{ resultChallenge?.opponent?.name }}</strong>
                {{ opponentGoalSum }} / {{ matchResult.opponent_score }}
              </template>
            </v-alert>

            <!-- No-roster fallback -->
            <v-alert
              v-if="challengerRoster.length === 0 && opponentRoster.length === 0"
              type="info"
              variant="tonal"
              density="compact"
              class="mb-4"
            >
              No roster data available. You can still submit the final score.
            </v-alert>

            <!-- ── Challenger team ── -->
            <template v-if="challengerRoster.length > 0">
              <div class="d-flex align-center mb-2">
                <v-icon color="primary" size="small" class="mr-1">mdi-shield</v-icon>
                <span class="text-subtitle-2 text-primary font-weight-bold">
                  {{ resultChallenge?.challenger?.name }}
                </span>
                <v-chip size="x-small" class="ml-2" :color="challengerGoalSum === matchResult.challenger_score ? 'success' : 'warning'">
                  {{ challengerGoalSum }} / {{ matchResult.challenger_score }} goals
                </v-chip>
              </div>

              <v-table density="compact" class="mb-5 rounded border">
                <thead>
                  <tr>
                    <th class="text-left">#</th>
                    <th class="text-left">Player</th>
                    <th class="text-center" style="width:80px">Goals</th>
                    <th class="text-center" style="width:80px">Assists</th>
                    <th class="text-center" style="width:56px">
                      <v-icon size="small" color="yellow-darken-3" title="Yellow card">mdi-card</v-icon>
                    </th>
                    <th class="text-center" style="width:56px">
                      <v-icon size="small" color="error" title="Red card">mdi-card</v-icon>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="p in challengerRoster" :key="p.user_id">
                    <td class="text-caption text-medium-emphasis">{{ p.jersey_number || '–' }}</td>
                    <td>
                      <span class="text-body-2">{{ p.user?.full_name || p.user?.username }}</span>
                      <v-chip v-if="p.position" size="x-small" class="ml-1" variant="tonal">
                        {{ p.position }}
                      </v-chip>
                    </td>
                    <td>
                      <v-text-field
                        v-model.number="playerStats[p.user_id].goals"
                        type="number"
                        min="0"
                        max="20"
                        variant="plain"
                        hide-details
                        density="compact"
                        style="max-width:60px; margin:auto;"
                      />
                    </td>
                    <td>
                      <v-text-field
                        v-model.number="playerStats[p.user_id].assists"
                        type="number"
                        min="0"
                        max="20"
                        variant="plain"
                        hide-details
                        density="compact"
                        style="max-width:60px; margin:auto;"
                      />
                    </td>
                    <td class="text-center">
                      <v-btn
                        :color="playerStats[p.user_id].yellow_cards > 0 ? 'yellow-darken-3' : 'grey-lighten-2'"
                        icon="mdi-card"
                        size="x-small"
                        variant="flat"
                        :title="playerStats[p.user_id].yellow_cards > 0 ? 'Yellow card given (click to remove)' : 'Give yellow card'"
                        @click="toggleCard(p.user_id, 'yellow_cards')"
                      />
                    </td>
                    <td class="text-center">
                      <v-btn
                        :color="playerStats[p.user_id].red_cards > 0 ? 'error' : 'grey-lighten-2'"
                        icon="mdi-card"
                        size="x-small"
                        variant="flat"
                        :title="playerStats[p.user_id].red_cards > 0 ? 'Red card given (click to remove)' : 'Give red card'"
                        @click="toggleCard(p.user_id, 'red_cards')"
                      />
                    </td>
                  </tr>
                </tbody>
              </v-table>
            </template>

            <!-- ── Opponent team ── -->
            <template v-if="opponentRoster.length > 0">
              <div class="d-flex align-center mb-2">
                <v-icon color="error" size="small" class="mr-1">mdi-shield</v-icon>
                <span class="text-subtitle-2 text-error font-weight-bold">
                  {{ resultChallenge?.opponent?.name }}
                </span>
                <v-chip size="x-small" class="ml-2" :color="opponentGoalSum === matchResult.opponent_score ? 'success' : 'warning'">
                  {{ opponentGoalSum }} / {{ matchResult.opponent_score }} goals
                </v-chip>
              </div>

              <v-table density="compact" class="rounded border">
                <thead>
                  <tr>
                    <th class="text-left">#</th>
                    <th class="text-left">Player</th>
                    <th class="text-center" style="width:80px">Goals</th>
                    <th class="text-center" style="width:80px">Assists</th>
                    <th class="text-center" style="width:56px">
                      <v-icon size="small" color="yellow-darken-3">mdi-card</v-icon>
                    </th>
                    <th class="text-center" style="width:56px">
                      <v-icon size="small" color="error">mdi-card</v-icon>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="p in opponentRoster" :key="p.user_id">
                    <td class="text-caption text-medium-emphasis">{{ p.jersey_number || '–' }}</td>
                    <td>
                      <span class="text-body-2">{{ p.user?.full_name || p.user?.username }}</span>
                      <v-chip v-if="p.position" size="x-small" class="ml-1" variant="tonal">
                        {{ p.position }}
                      </v-chip>
                    </td>
                    <td>
                      <v-text-field
                        v-model.number="playerStats[p.user_id].goals"
                        type="number"
                        min="0"
                        max="20"
                        variant="plain"
                        hide-details
                        density="compact"
                        style="max-width:60px; margin:auto;"
                      />
                    </td>
                    <td>
                      <v-text-field
                        v-model.number="playerStats[p.user_id].assists"
                        type="number"
                        min="0"
                        max="20"
                        variant="plain"
                        hide-details
                        density="compact"
                        style="max-width:60px; margin:auto;"
                      />
                    </td>
                    <td class="text-center">
                      <v-btn
                        :color="playerStats[p.user_id].yellow_cards > 0 ? 'yellow-darken-3' : 'grey-lighten-2'"
                        icon="mdi-card"
                        size="x-small"
                        variant="flat"
                        @click="toggleCard(p.user_id, 'yellow_cards')"
                      />
                    </td>
                    <td class="text-center">
                      <v-btn
                        :color="playerStats[p.user_id].red_cards > 0 ? 'error' : 'grey-lighten-2'"
                        icon="mdi-card"
                        size="x-small"
                        variant="flat"
                        @click="toggleCard(p.user_id, 'red_cards')"
                      />
                    </td>
                  </tr>
                </tbody>
              </v-table>
            </template>
          </template>
        </v-card-text>

        <v-divider />

        <!-- Actions -->
        <v-card-actions class="pa-4">
          <v-btn variant="text" @click="closeResultDialog">Cancel</v-btn>
          <v-spacer />

          <!-- Step 1 actions -->
          <template v-if="resultStep === 1">
            <v-btn
              color="primary"
              variant="flat"
              :disabled="matchResult.challenger_score < 0 || matchResult.opponent_score < 0"
              @click="advanceToStep2"
            >
              {{ totalGoals === 0 ? 'Submit 0–0' : 'Next: Player Stats' }}
              <v-icon end>mdi-chevron-right</v-icon>
            </v-btn>
          </template>

          <!-- Step 2 actions -->
          <template v-else>
            <v-btn variant="text" class="mr-1" :disabled="submitting" @click="resultStep = 1">
              <v-icon start>mdi-chevron-left</v-icon>
              Back
            </v-btn>
            <v-btn
              color="success"
              variant="flat"
              :loading="submitting"
              :disabled="rosterLoading || !goalsMatchScore"
              @click="submitResult"
            >
              <v-icon start>mdi-check</v-icon>
              Submit Result
            </v-btn>
          </template>
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
import { ref, computed, onMounted, onErrorCaptured, watch } from 'vue'

definePageMeta({
  middleware: ['auth'],
})

const { user, isAuthenticated, isCaptain } = useAuth()
const config = useRuntimeConfig()
const apiBase = computed(() => config.public.apiBaseUrl || 'http://localhost:8000/api/v1')

const getAuthHeaders = () => {
  const token = useCookie('auth_token')
  return token.value ? { Authorization: `Bearer ${token.value}` } : {}
}

// State
const challenges = ref<any[]>([])
const availableTeams = ref<any[]>([])
const loading = ref(false)
const submitting = ref(false)
const actionLoading = ref<string | null>(null)
const error = ref<string | null>(null)
const statusFilter = ref<string | null>(null)
const viewMode = ref('all')

// Dialogs
const showCreateDialog = ref(false)
const showResultDialog = ref(false)
const resultChallenge = ref<any>(null)

// Forms
const newChallenge = ref({ opponent_id: null as number | null, match_date: '', location: '' })
const matchResult = ref({ challenger_score: 0, opponent_score: 0 })

// ── Result wizard state ──────────────────────────────────────────────────────
const resultStep = ref(1)
const rosterLoading = ref(false)
const challengerRoster = ref<any[]>([])
const opponentRoster = ref<any[]>([])

interface PlayerStatEntry {
  user_id: number
  team_id: number
  goals: number
  assists: number
  yellow_cards: number
  red_cards: number
}
const playerStats = ref<Record<number, PlayerStatEntry>>({})

// Computed: running goal totals per team
const totalGoals = computed(() =>
  (matchResult.value.challenger_score || 0) + (matchResult.value.opponent_score || 0),
)
const challengerGoalSum = computed(() =>
  challengerRoster.value.reduce((s, p) => s + (playerStats.value[p.user_id]?.goals || 0), 0),
)
const opponentGoalSum = computed(() =>
  opponentRoster.value.reduce((s, p) => s + (playerStats.value[p.user_id]?.goals || 0), 0),
)
// Allow submission when all goals are distributed; fall back to true when no
// rosters could be loaded (empty teams edge-case).
const goalsMatchScore = computed(() => {
  if (challengerRoster.value.length === 0 && opponentRoster.value.length === 0) return true
  return (
    challengerGoalSum.value === (matchResult.value.challenger_score || 0) &&
    opponentGoalSum.value === (matchResult.value.opponent_score || 0)
  )
})

// Snackbar
const showSnackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

const statusOptions = [
  { title: 'Pending', value: 'pending' },
  { title: 'Accepted', value: 'accepted' },
  { title: 'Completed', value: 'completed' },
  { title: 'Rejected', value: 'rejected' },
  { title: 'Cancelled', value: 'cancelled' },
]

// Fetch
const fetchChallenges = async () => {
  loading.value = true
  error.value = null
  try {
    let url = `${apiBase.value}/challenges/`
    if (viewMode.value === 'my' && isAuthenticated.value) {
      url = `${apiBase.value}/challenges/my`
    }
    const params = new URLSearchParams()
    if (statusFilter.value) params.append('status', statusFilter.value)
    params.append('limit', '50')
    const query = params.toString()
    if (query) url += `?${query}`

    const data = await $fetch<any>(url, { headers: getAuthHeaders() })
    challenges.value = data.items || []
  } catch (err: any) {
    // Backend returns { error: { message } } from our custom handler,
    // or { detail } from FastAPI's default HTTPException format.
    error.value = err.data?.error?.message || err.data?.detail || 'Failed to load challenges'
  } finally {
    loading.value = false
  }
}

const fetchTeams = async () => {
  try {
    const data = await $fetch<any[]>(`${apiBase.value}/teams`, { headers: getAuthHeaders() })
    availableTeams.value = data
  } catch (err: any) {
    // Non-critical — captain can still view challenges, just can't create new ones.
    console.warn('Could not load teams for challenge creation:', err?.data?.error?.message || err?.message)
  }
}

// Actions
const getMyTeamId = () => {
  // Determine if user is captain of challenger or opponent
  return null // Used in getActions
}

const getActions = (challenge: any) => {
  if (!isAuthenticated.value || !user.value) return []
  const actions: any[] = []
  const isChallengerCaptain = challenge.challenger?.id && user.value.id === getCaptainId(challenge.challenger)
  const isOpponentCaptain = challenge.opponent?.id && user.value.id === getCaptainId(challenge.opponent)

  if (challenge.status === 'pending') {
    if (isOpponentCaptain) {
      actions.push({ label: 'Accept', action: 'accept', color: 'success', icon: 'mdi-check' })
      actions.push({ label: 'Reject', action: 'reject', color: 'error', icon: 'mdi-close' })
    }
    if (isChallengerCaptain) {
      actions.push({ label: 'Cancel', action: 'cancel', color: 'warning', icon: 'mdi-cancel' })
    }
  }
  if (challenge.status === 'accepted') {
    if (isChallengerCaptain || isOpponentCaptain) {
      actions.push({ label: 'Submit Result', action: 'result', color: 'primary', icon: 'mdi-scoreboard', variant: 'flat' })
    }
    if (isChallengerCaptain) {
      actions.push({ label: 'Cancel', action: 'cancel', color: 'warning', icon: 'mdi-cancel' })
    }
  }
  return actions
}

const getCaptainId = (team: any) => {
  // The challenge response has team brief (id, name, city, rating)
  // We need to check against captain_id from our teams list
  const fullTeam = availableTeams.value.find(t => t.id === team.id)
  return fullTeam?.captain_id
}

// ── Roster helpers ───────────────────────────────────────────────────────────

const fetchRosters = async (challenge: any) => {
  rosterLoading.value = true
  playerStats.value = {}
  try {
    const [cData, oData] = await Promise.all([
      $fetch<any[]>(`${apiBase.value}/teams/${challenge.challenger.id}/roster-stats`, {
        headers: getAuthHeaders(),
      }),
      $fetch<any[]>(`${apiBase.value}/teams/${challenge.opponent.id}/roster-stats`, {
        headers: getAuthHeaders(),
      }),
    ])
    challengerRoster.value = cData || []
    opponentRoster.value = oData || []
    // Pre-initialise a zero-stat entry for every player
    for (const p of [...challengerRoster.value, ...opponentRoster.value]) {
      playerStats.value[p.user_id] = {
        user_id: p.user_id,
        team_id: p.team_id,
        goals: 0,
        assists: 0,
        yellow_cards: 0,
        red_cards: 0,
      }
    }
  } catch {
    // Silently swallow roster fetch errors; the wizard degrades gracefully
  } finally {
    rosterLoading.value = false
  }
}

const toggleCard = (userId: number, field: 'yellow_cards' | 'red_cards') => {
  if (playerStats.value[userId]) {
    playerStats.value[userId][field] = playerStats.value[userId][field] > 0 ? 0 : 1
  }
}

const closeResultDialog = () => {
  showResultDialog.value = false
  resultStep.value = 1
  playerStats.value = {}
  challengerRoster.value = []
  opponentRoster.value = []
}

// Advance from Step 1. For 0-0 matches we skip Step 2 and submit immediately.
const advanceToStep2 = () => {
  if (totalGoals.value === 0) {
    submitResult()
    return
  }
  resultStep.value = 2
}

const handleAction = async (challenge: any, action: string) => {
  if (action === 'result') {
    resultChallenge.value = challenge
    matchResult.value = { challenger_score: 0, opponent_score: 0 }
    resultStep.value = 1
    showResultDialog.value = true
    // Fire roster fetch in background so data is ready by the time the user
    // reaches Step 2.
    fetchRosters(challenge)
    return
  }

  actionLoading.value = `${challenge.id}-${action}`
  try {
    await $fetch(`${apiBase.value}/challenges/${challenge.id}/${action}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
    })
    showMessage(`Challenge ${action}ed successfully!`, 'success')
    await fetchChallenges()
  } catch (err: any) {
    // Наш handler: { error: { message } } | FastAPI HTTPException: { detail }
    showMessage(err.data?.error?.message || err.data?.detail || `Failed to ${action} challenge`, 'error')
  } finally {
    actionLoading.value = null
  }
}

const createChallenge = async () => {
  submitting.value = true
  try {
    await $fetch(`${apiBase.value}/challenges/`, {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: {
        opponent_id: newChallenge.value.opponent_id,
        match_date: newChallenge.value.match_date || undefined,
        location: newChallenge.value.location || undefined,
      },
    })
    showCreateDialog.value = false
    newChallenge.value = { opponent_id: null, match_date: '', location: '' }
    showMessage('Challenge sent!', 'success')
    await fetchChallenges()
  } catch (err: any) {
    // Наш ValidationError handler: { error: { message, details.errors[] } }
    // Извлекаем первую ошибку поля, если есть — удобно для дебага
    const validationErrors: any[] = err.data?.error?.details?.errors ?? []
    const firstFieldError = validationErrors.length
      ? `${validationErrors[0].field}: ${validationErrors[0].message}`
      : null
    showMessage(firstFieldError || err.data?.error?.message || err.data?.detail || 'Failed to create challenge', 'error')
  } finally {
    submitting.value = false
  }
}

const submitResult = async () => {
  if (!resultChallenge.value) return
  submitting.value = true
  try {
    // ── Step A: record the final score and trigger ELO update ────────────────
    const data = await $fetch<any>(
      `${apiBase.value}/challenges/${resultChallenge.value.id}/result`,
      {
        method: 'PUT',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: matchResult.value,
      },
    )

    // ── Step B: submit per-player statistics (non-critical) ──────────────────
    // Only attempt when we have roster data (Step 2 was shown or rosters loaded).
    const statsPayload = Object.values(playerStats.value).map((s) => ({
      user_id: s.user_id,
      challenge_id: resultChallenge.value!.id,
      team_id: s.team_id,
      goals: s.goals || 0,
      assists: s.assists || 0,
      yellow_cards: s.yellow_cards || 0,
      red_cards: s.red_cards || 0,
      minutes_played: 0,
      shots_on_target: 0,
      saves: 0,
    }))

    if (statsPayload.length > 0) {
      await $fetch(`${apiBase.value}/statistics/match/${resultChallenge.value.id}`, {
        method: 'POST',
        headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
        body: statsPayload,
      }).catch((err: any) => {
        // Stats failure is non-critical — score is already saved.  Surface a
        // soft warning so the captain knows to re-enter stats if needed.
        console.warn('Player stats submission failed:', err?.data?.detail)
        showMessage('Score saved! Player stats could not be recorded — try again later.', 'warning')
      })
    }

    closeResultDialog()

    // Show ELO delta in snackbar
    if (data.elo_updates?.length) {
      const updates = data.elo_updates
        .map(
          (u: any) =>
            `${u.team_name}: ${u.old_rating} → ${u.new_rating} (${u.rating_change > 0 ? '+' : ''}${u.rating_change})`,
        )
        .join(' | ')
      showMessage(`Result submitted! ELO: ${updates}`, 'success')
    } else {
      showMessage('Result submitted successfully!', 'success')
    }

    await fetchChallenges()
  } catch (err: any) {
    showMessage(err.data?.error?.message || err.data?.detail || 'Failed to submit result', 'error')
  } finally {
    submitting.value = false
  }
}

// Helpers
const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'warning', accepted: 'info', completed: 'success', rejected: 'error', cancelled: 'grey',
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

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

const showMessage = (message: string, color: string) => {
  snackbarMessage.value = message
  snackbarColor.value = color
  showSnackbar.value = true
}

// Catch any unexpected component-level throw and surface it as a UI error
// instead of letting it propagate to Nuxt's module loader (which produces the
// confusing "Failed to fetch dynamically imported module" error in the console).
onErrorCaptured((err: unknown) => {
  console.error('[challenges] uncaught component error:', err)
  error.value = err instanceof Error ? err.message : 'An unexpected error occurred'
  return false // prevent further propagation
})

watch([statusFilter, viewMode], () => fetchChallenges())

onMounted(() => {
  fetchChallenges()
  fetchTeams()
})
</script>
