<template>
  <v-container class="py-8">
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center flex-wrap ga-2">
          <div>
            <h1 :class="$vuetify.display.xs ? 'text-h4' : 'text-h3'" class="font-weight-bold mb-2">
              <v-icon icon="mdi-tournament" :size="$vuetify.display.xs ? 'default' : 'large'" class="mr-2" />
              Tournaments
            </h1>
            <p class="text-body-1 text-medium-emphasis">
              Compete in league and knockout tournaments
            </p>
          </div>

          <v-btn
            v-if="canCreate"
            color="primary"
            prepend-icon="mdi-plus"
            @click="showCreateDialog = true"
          >
            New Tournament
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
    </v-row>

    <!-- Error -->
    <v-row v-if="error">
      <v-col cols="12">
        <v-alert type="error" closable @click:close="error = null">{{ error }}</v-alert>
      </v-col>
    </v-row>

    <!-- Loading -->
    <v-row v-if="loading">
      <v-col cols="12">
        <v-card class="pa-8 text-center">
          <v-progress-circular indeterminate color="primary" />
          <p class="mt-4 text-medium-emphasis">Loading tournaments...</p>
        </v-card>
      </v-col>
    </v-row>

    <!-- Empty state -->
    <v-row v-else-if="tournaments.length === 0">
      <v-col cols="12">
        <div class="text-center pa-12">
          <v-icon icon="mdi-tournament" size="64" color="grey-lighten-1" class="mb-4" />
          <h3 class="text-h5 mb-2">No tournaments found</h3>
          <p class="text-medium-emphasis">
            {{ canCreate ? 'Create the first tournament to get started!' : 'Check back later for upcoming tournaments.' }}
          </p>
        </div>
      </v-col>
    </v-row>

    <!-- Tournament Cards -->
    <v-row v-else>
      <v-col
        v-for="tournament in tournaments"
        :key="tournament.id"
        cols="12"
        sm="6"
        lg="4"
      >
        <v-card
          elevation="2"
          class="h-100 d-flex flex-column cursor-pointer"
          @click="navigateTo(`/tournaments/${tournament.id}`)"
        >
          <!-- Header with type badge -->
          <v-card-title class="d-flex align-center justify-space-between">
            <span class="text-truncate">{{ tournament.name }}</span>
            <v-chip
              :color="tournament.type === 'league' ? 'primary' : 'deep-purple'"
              size="small"
              variant="flat"
            >
              <v-icon start size="small">
                {{ tournament.type === 'league' ? 'mdi-format-list-numbered' : 'mdi-tournament' }}
              </v-icon>
              {{ tournament.type === 'league' ? 'League' : 'Knockout' }}
            </v-chip>
          </v-card-title>

          <v-card-subtitle v-if="tournament.description" class="text-truncate">
            {{ tournament.description }}
          </v-card-subtitle>

          <v-card-text class="flex-grow-1">
            <!-- Status -->
            <div class="d-flex align-center mb-3">
              <v-chip :color="getStatusColor(tournament.status)" size="small" variant="flat">
                {{ tournament.status.toUpperCase() }}
              </v-chip>
              <v-spacer />
              <span class="text-caption text-medium-emphasis">
                {{ formatDate(tournament.created_at) }}
              </span>
            </div>

            <!-- Stats row -->
            <v-row dense>
              <v-col cols="4" class="text-center">
                <div class="text-h6 font-weight-bold">{{ tournament.participant_count || 0 }}</div>
                <div class="text-caption text-medium-emphasis">Teams</div>
              </v-col>
              <v-col cols="4" class="text-center">
                <div class="text-h6 font-weight-bold">{{ tournament.max_teams }}</div>
                <div class="text-caption text-medium-emphasis">Max</div>
              </v-col>
              <v-col cols="4" class="text-center">
                <div class="text-h6 font-weight-bold">{{ tournament.current_round || 0 }}</div>
                <div class="text-caption text-medium-emphasis">Round</div>
              </v-col>
            </v-row>

            <!-- Dates -->
            <div v-if="tournament.start_date || tournament.end_date" class="mt-3">
              <div v-if="tournament.start_date" class="text-caption">
                <v-icon size="small" class="mr-1">mdi-calendar-start</v-icon>
                Start: {{ formatDate(tournament.start_date) }}
              </div>
              <div v-if="tournament.end_date" class="text-caption">
                <v-icon size="small" class="mr-1">mdi-calendar-end</v-icon>
                End: {{ formatDate(tournament.end_date) }}
              </div>
            </div>

            <!-- Organiser -->
            <div class="mt-2 text-caption text-medium-emphasis">
              <v-icon size="small" class="mr-1">mdi-account</v-icon>
              Organised by {{ tournament.created_by?.username || 'Unknown' }}
            </div>
          </v-card-text>

          <v-card-actions>
            <v-btn
              variant="text"
              color="primary"
              prepend-icon="mdi-eye"
              :to="`/tournaments/${tournament.id}`"
            >
              View Details
            </v-btn>
            <v-spacer />
            <!-- Registration indicator -->
            <v-chip
              v-if="tournament.status === 'registration'"
              color="success"
              size="small"
              variant="outlined"
            >
              Open for registration
            </v-chip>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create Tournament Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="550" persistent>
      <v-card>
        <v-card-title>
          <v-icon class="mr-2">mdi-tournament</v-icon>
          Create Tournament
        </v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newTournament.name"
            label="Tournament Name *"
            variant="outlined"
            class="mb-3"
            :rules="[v => !!v || 'Name is required']"
          />

          <v-textarea
            v-model="newTournament.description"
            label="Description"
            variant="outlined"
            rows="2"
            class="mb-3"
          />

          <v-select
            v-model="newTournament.type"
            :items="typeOptions"
            label="Tournament Type *"
            variant="outlined"
            class="mb-3"
          />

          <v-text-field
            v-model.number="newTournament.max_teams"
            label="Max Teams"
            type="number"
            min="2"
            max="64"
            variant="outlined"
            class="mb-3"
          />

          <v-row>
            <v-col cols="6">
              <v-text-field
                v-model="newTournament.start_date"
                label="Start Date"
                type="datetime-local"
                variant="outlined"
              />
            </v-col>
            <v-col cols="6">
              <v-text-field
                v-model="newTournament.end_date"
                label="End Date"
                type="datetime-local"
                variant="outlined"
              />
            </v-col>
          </v-row>

          <v-alert type="info" variant="tonal" density="compact" class="mt-2">
            <template v-if="newTournament.type === 'league'">
              <strong>League:</strong> Round-robin format — every team plays every other team.
              Standings determined by Points > Goal Difference > Goals Scored.
            </template>
            <template v-else>
              <strong>Knockout:</strong> Single-elimination bracket. Lose once, you're out.
              Teams are seeded by ELO rating.
            </template>
          </v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showCreateDialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            :loading="submitting"
            :disabled="!newTournament.name"
            @click="createTournament"
          >
            Create
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

// No auth required — tournament list is public

const { user, isAuthenticated, isCaptain, isReferee } = useAuth()
const config = useRuntimeConfig()
const apiBase = computed(() => config.public.apiBaseUrl || 'http://localhost:8000/api/v1')

const getAuthHeaders = () => {
  const token = useCookie('auth_token')
  return token.value ? { Authorization: `Bearer ${token.value}` } : {}
}

// State
const tournaments = ref<any[]>([])
const loading = ref(false)
const submitting = ref(false)
const error = ref<string | null>(null)
const statusFilter = ref<string | null>(null)

// Dialog
const showCreateDialog = ref(false)
const newTournament = ref({
  name: '',
  description: '',
  type: 'league',
  max_teams: 8,
  start_date: '',
  end_date: '',
})

// Snackbar
const showSnackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

const canCreate = computed(() => isAuthenticated.value && (isCaptain.value || isReferee.value))

const statusOptions = [
  { title: 'Draft', value: 'draft' },
  { title: 'Registration', value: 'registration' },
  { title: 'Active', value: 'active' },
  { title: 'Completed', value: 'completed' },
  { title: 'Cancelled', value: 'cancelled' },
]

const typeOptions = [
  { title: 'League (Round-Robin)', value: 'league' },
  { title: 'Knockout (Single Elimination)', value: 'knockout' },
]

// Fetch
const fetchTournaments = async () => {
  loading.value = true
  error.value = null
  try {
    let url = `${apiBase.value}/tournaments/`
    const params = new URLSearchParams()
    if (statusFilter.value) params.append('status', statusFilter.value)
    params.append('limit', '50')
    const query = params.toString()
    if (query) url += `?${query}`

    const data = await $fetch<any>(url, { headers: getAuthHeaders() })
    const items: any[] = data.items || []

    const statusPriority: Record<string, number> = {
      active: 0,
      registration: 1,
      draft: 2,
      completed: 3,
      cancelled: 4,
    }
    const now = Date.now()
    const ONE_WEEK = 7 * 24 * 60 * 60 * 1000

    tournaments.value = items.sort((a, b) => {
      const pa = statusPriority[a.status] ?? 5
      const pb = statusPriority[b.status] ?? 5

      // Completed within 7 days stays near active; older sinks to bottom
      const ageA = a.status === 'completed' && a.updated_at
        ? (now - new Date(a.updated_at).getTime() > ONE_WEEK ? 1 : 0)
        : 0
      const ageB = b.status === 'completed' && b.updated_at
        ? (now - new Date(b.updated_at).getTime() > ONE_WEEK ? 1 : 0)
        : 0

      if (pa !== pb) return pa - pb
      if (ageA !== ageB) return ageA - ageB
      // Within same group — newest first
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })
  } catch (err: any) {
    error.value = err.data?.detail || 'Failed to load tournaments'
  } finally {
    loading.value = false
  }
}

const createTournament = async () => {
  submitting.value = true
  try {
    const body: any = {
      name: newTournament.value.name,
      type: newTournament.value.type,
      max_teams: newTournament.value.max_teams,
    }
    if (newTournament.value.description) body.description = newTournament.value.description
    if (newTournament.value.start_date) body.start_date = newTournament.value.start_date
    if (newTournament.value.end_date) body.end_date = newTournament.value.end_date

    const created = await $fetch<any>(`${apiBase.value}/tournaments/`, {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body,
    })

    showCreateDialog.value = false
    newTournament.value = { name: '', description: '', type: 'league', max_teams: 8, start_date: '', end_date: '' }
    showMessage('Tournament created!', 'success')
    navigateTo(`/tournaments/${created.id}`)
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to create tournament', 'error')
  } finally {
    submitting.value = false
  }
}

// Helpers
const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    draft: 'grey', registration: 'info', active: 'success', completed: 'primary', cancelled: 'error',
  }
  return colors[status] || 'grey'
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  })
}

const showMessage = (message: string, color: string) => {
  snackbarMessage.value = message
  snackbarColor.value = color
  showSnackbar.value = true
}

watch(statusFilter, () => fetchTournaments())

onMounted(() => fetchTournaments())
</script>

<style scoped>
.cursor-pointer { cursor: pointer; }
</style>
