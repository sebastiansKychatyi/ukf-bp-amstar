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

    <!-- Submit Result Dialog -->
    <v-dialog v-model="showResultDialog" max-width="400" persistent>
      <v-card>
        <v-card-title>
          <v-icon class="mr-2">mdi-scoreboard</v-icon>
          Submit Match Result
        </v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model.number="matchResult.challenger_score"
                :label="resultChallenge?.challenger?.name || 'Challenger'"
                type="number"
                min="0"
                max="99"
                variant="outlined"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model.number="matchResult.opponent_score"
                :label="resultChallenge?.opponent?.name || 'Opponent'"
                type="number"
                min="0"
                max="99"
                variant="outlined"
              />
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showResultDialog = false">Cancel</v-btn>
          <v-btn
            color="success"
            :loading="submitting"
            :disabled="matchResult.challenger_score < 0 || matchResult.opponent_score < 0"
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
    error.value = err.data?.detail || 'Failed to load challenges'
  } finally {
    loading.value = false
  }
}

const fetchTeams = async () => {
  try {
    const data = await $fetch<any[]>(`${apiBase.value}/teams`, { headers: getAuthHeaders() })
    availableTeams.value = data
  } catch { /* ignore */ }
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

const handleAction = async (challenge: any, action: string) => {
  if (action === 'result') {
    resultChallenge.value = challenge
    matchResult.value = { challenger_score: 0, opponent_score: 0 }
    showResultDialog.value = true
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
    showMessage(err.data?.detail || `Failed to ${action} challenge`, 'error')
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
    showMessage(err.data?.detail || 'Failed to create challenge', 'error')
  } finally {
    submitting.value = false
  }
}

const submitResult = async () => {
  if (!resultChallenge.value) return
  submitting.value = true
  try {
    const data = await $fetch<any>(`${apiBase.value}/challenges/${resultChallenge.value.id}/result`, {
      method: 'PUT',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: matchResult.value,
    })
    showResultDialog.value = false
    // Show ELO changes
    if (data.elo_updates?.length) {
      const updates = data.elo_updates.map((u: any) =>
        `${u.team_name}: ${u.old_rating} → ${u.new_rating} (${u.rating_change > 0 ? '+' : ''}${u.rating_change})`
      ).join(' | ')
      showMessage(`Result submitted! ELO: ${updates}`, 'success')
    } else {
      showMessage('Result submitted!', 'success')
    }
    await fetchChallenges()
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to submit result', 'error')
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

watch([statusFilter, viewMode], () => fetchChallenges())

onMounted(() => {
  fetchChallenges()
  fetchTeams()
})
</script>
