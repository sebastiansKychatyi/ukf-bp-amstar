<template>
  <v-container class="py-8">
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center flex-wrap ga-2">
          <div>
            <h1 :class="$vuetify.display.xs ? 'text-h4' : 'text-h3'" class="font-weight-bold mb-1">
              <v-icon icon="mdi-shield-account" :size="$vuetify.display.xs ? 'default' : 'large'" class="mr-2" />
              Teams
            </h1>
            <p class="text-body-1 text-medium-emphasis">
              Browse and manage football teams
            </p>
          </div>

          <div class="d-flex ga-2 align-center">
            <!-- View Toggle -->
            <v-btn-toggle v-model="viewMode" mandatory density="comfortable" variant="outlined" rounded="lg">
              <v-btn value="table" icon="mdi-format-list-bulleted" title="Table view" />
              <v-btn value="grid" icon="mdi-view-grid" title="Grid view" />
            </v-btn-toggle>

            <!-- My Team Button -->
            <v-btn
              v-if="isAuthenticated"
              color="secondary"
              variant="outlined"
              rounded="lg"
              prepend-icon="mdi-shield-home"
              @click="goToMyTeam"
            >
              My Team
            </v-btn>

            <!-- Create Team Button -->
            <v-btn
              v-if="canCreateTeam"
              color="primary"
              rounded="lg"
              prepend-icon="mdi-plus"
              @click="showCreateDialog = true"
            >
              Create Team
            </v-btn>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Error Alert -->
    <v-row v-if="error">
      <v-col cols="12">
        <v-alert type="error" closable @click:close="error = null">
          {{ error }}
        </v-alert>
      </v-col>
    </v-row>

    <!-- Search bar (shared) -->
    <v-row class="mt-2">
      <v-col cols="12" sm="6" md="4">
        <v-text-field
          v-model="search"
          prepend-inner-icon="mdi-magnify"
          label="Search teams"
          single-line
          hide-details
          clearable
          rounded="lg"
        />
      </v-col>
    </v-row>

    <!-- TABLE VIEW -->
    <v-row v-if="viewMode === 'table'" class="mt-2">
      <v-col cols="12">
        <v-card elevation="0" border>
          <v-data-table
            :headers="headers"
            :items="filteredTeams"
            :items-per-page="10"
            :loading="loading"
            class="elevation-0"
            hover
            @click:row="(_e: any, { item }: any) => navigateToTeam(item)"
          >
            <!-- Team Name -->
            <template #item.name="{ item }">
              <div class="d-flex align-center cursor-pointer">
                <v-avatar size="32" class="mr-2" color="primary">
                  <v-img v-if="item.logo_url" :src="item.logo_url" />
                  <span v-else class="text-caption font-weight-bold text-white">
                    {{ getInitials(item.name) }}
                  </span>
                </v-avatar>
                <span class="font-weight-medium text-primary">{{ item.name }}</span>
              </div>
            </template>

            <!-- City -->
            <template #item.city="{ item }">
              <v-chip v-if="item.city" size="small" variant="outlined">
                <v-icon start size="small">mdi-map-marker</v-icon>
                {{ item.city }}
              </v-chip>
              <span v-else class="text-medium-emphasis">-</span>
            </template>

            <!-- Members -->
            <template #item.member_count="{ item }">
              <v-chip size="small" variant="outlined" prepend-icon="mdi-account-group">
                {{ item.member_count || 0 }}
              </v-chip>
            </template>

            <!-- Rating -->
            <template #item.rating_score="{ item }">
              <v-chip size="small" :color="getRatingColor(item.rating_score)">
                {{ item.rating_score || 1000 }}
              </v-chip>
            </template>

            <!-- Actions -->
            <template #item.actions="{ item }">
              <div class="d-flex ga-1">
                <v-btn
                  size="small"
                  color="primary"
                  variant="text"
                  icon="mdi-eye"
                  @click.stop="navigateToTeam(item)"
                />
                <v-btn
                  v-if="canJoinTeam(item)"
                  size="small"
                  color="success"
                  variant="text"
                  icon="mdi-account-plus"
                  @click.stop="openJoinDialog(item)"
                />
              </div>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- GRID VIEW -->
    <template v-else>
      <!-- Loading grid skeletons -->
      <v-row v-if="loading" class="mt-2">
        <v-col v-for="n in 8" :key="n" cols="12" sm="6" md="4" lg="3">
          <v-skeleton-loader type="card" height="220" />
        </v-col>
      </v-row>

      <!-- Empty grid state -->
      <v-row v-else-if="filteredTeams.length === 0" class="mt-4">
        <v-col cols="12" class="text-center py-12">
          <v-icon icon="mdi-shield-off" size="64" color="medium-emphasis" class="mb-4" />
          <h3 class="text-h5 mb-2">No teams found</h3>
          <p class="text-medium-emphasis">Try a different search term</p>
        </v-col>
      </v-row>

      <!-- Team cards grid -->
      <v-row v-else class="mt-2">
        <v-col
          v-for="team in filteredTeams"
          :key="team.id"
          cols="12" sm="6" md="4" lg="3"
        >
          <v-card
            class="team-grid-card h-100 cursor-pointer"
            elevation="0"
            border
            @click="navigateToTeam(team)"
          >
            <!-- Card header with gradient -->
            <div class="team-grid-header d-flex align-center justify-center">
              <v-avatar size="56" color="white" class="team-grid-avatar">
                <v-img v-if="team.logo_url" :src="team.logo_url" />
                <span v-else class="text-h6 font-weight-black text-primary">{{ getInitials(team.name) }}</span>
              </v-avatar>
            </div>

            <v-card-text class="text-center pt-3 pb-2">
              <div class="text-subtitle-1 font-weight-bold mb-1 text-truncate">{{ team.name }}</div>
              <div class="d-flex justify-center align-center ga-1 mb-3">
                <v-chip v-if="team.city" size="x-small" variant="outlined">
                  <v-icon start size="x-small">mdi-map-marker</v-icon>
                  {{ team.city }}
                </v-chip>
                <v-chip size="x-small" :color="getRatingColor(team.rating_score)">
                  <v-icon start size="x-small">mdi-star</v-icon>
                  {{ team.rating_score || 1000 }}
                </v-chip>
              </div>
              <div class="d-flex justify-center ga-2 text-caption text-medium-emphasis">
                <span>
                  <v-icon size="x-small">mdi-account-group</v-icon>
                  {{ team.member_count || 0 }} members
                </span>
              </div>
            </v-card-text>

            <v-card-actions class="justify-center pa-3 pt-0 ga-1">
              <v-btn
                size="small"
                color="primary"
                variant="tonal"
                rounded="lg"
                @click.stop="navigateToTeam(team)"
              >
                View
              </v-btn>
              <v-btn
                v-if="canJoinTeam(team)"
                size="small"
                color="success"
                variant="outlined"
                rounded="lg"
                @click.stop="openJoinDialog(team)"
              >
                Join
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
    </template>

    <!-- Create Team Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="600" persistent>
      <v-card>
        <v-card-title class="d-flex align-center pa-4">
          <v-icon class="mr-2">mdi-plus</v-icon>
          Create New Team
        </v-card-title>

        <v-card-text>
          <v-form ref="createForm" v-model="createFormValid">
            <v-text-field
              v-model="newTeam.name"
              label="Team Name *"
              :rules="[v => !!v || 'Team name is required', v => v.length >= 2 || 'Min 2 characters']"
              required
              class="mb-3"
            />
            <v-text-field
              v-model="newTeam.city"
              label="City"
              class="mb-2"
            />

            <!-- Geocoding controls -->
            <div class="d-flex align-center flex-wrap ga-2 mb-3">
              <v-btn
                variant="outlined"
                size="small"
                :loading="geocoding"
                :disabled="!newTeam.city.trim()"
                prepend-icon="mdi-crosshairs-gps"
                @click="geocodeCity"
              >
                Locate City
              </v-btn>
              <v-chip
                v-if="geocodeResult"
                size="small"
                color="success"
                variant="tonal"
                closable
                @click:close="clearGeocode"
              >
                <v-icon start size="small">mdi-map-marker-check</v-icon>
                {{ geocodeResult }}
              </v-chip>
              <v-chip v-if="geocodeError" size="small" color="error" variant="tonal">
                <v-icon start size="small">mdi-alert-circle</v-icon>
                {{ geocodeError }}
              </v-chip>
            </div>

            <v-textarea
              v-model="newTeam.description"
              label="Description"
              rows="3"
              class="mb-3"
            />
            <v-text-field
              v-model.number="newTeam.founded_year"
              label="Founded Year"
              type="number"
              :min="1800"
              :max="2100"
            />
          </v-form>
        </v-card-text>

        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="closeCreateDialog">Cancel</v-btn>
          <v-btn
            color="primary"
            rounded="lg"
            :loading="submitting"
            :disabled="!createFormValid"
            @click="createTeam"
          >
            Create
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Join Team Dialog -->
    <v-dialog v-model="showJoinDialog" max-width="500" persistent>
      <v-card>
        <v-card-title class="d-flex align-center pa-4">
          <v-icon class="mr-2">mdi-account-plus</v-icon>
          Join {{ selectedTeam?.name }}
        </v-card-title>

        <v-card-text>
          <v-textarea
            v-model="joinRequest.message"
            label="Message to Captain (optional)"
            hint="Introduce yourself"
            rows="3"
            class="mb-3"
          />
          <v-select
            v-model="joinRequest.position"
            label="Preferred Position"
            :items="positions"
            clearable
          />
        </v-card-text>

        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="showJoinDialog = false">Cancel</v-btn>
          <v-btn color="success" rounded="lg" :loading="submitting" @click="submitJoinRequest">
            Send Request
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
import { ref, computed, onMounted } from 'vue'

const router = useRouter()
const { user, isAuthenticated, isCaptain } = useAuth()

// State
const teams = ref<any[]>([])
const selectedTeam = ref<any>(null)
const loading = ref(false)
const submitting = ref(false)
const error = ref<string | null>(null)
const search = ref('')

// View mode persisted in localStorage
const viewMode = ref<'table' | 'grid'>(
  (typeof localStorage !== 'undefined' && localStorage.getItem('teams-view') as 'table' | 'grid') || 'table'
)

// Watch and persist view mode changes
watch(viewMode, (val) => {
  if (typeof localStorage !== 'undefined') localStorage.setItem('teams-view', val)
})

// Dialog states
const showCreateDialog = ref(false)
const showJoinDialog = ref(false)

// Form states
const createForm = ref()
const createFormValid = ref(false)
const newTeam = ref({
  name: '',
  city: '',
  description: '',
  founded_year: null as number | null,
  latitude: null as number | null,
  longitude: null as number | null,
})

// Geocoding state
const geocoding = ref(false)
const geocodeResult = ref<string | null>(null)
const geocodeError = ref<string | null>(null)

const joinRequest = ref({
  message: '',
  position: null as string | null,
})

// Snackbar
const showSnackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

// Constants
const positions = ['GK', 'DEF', 'MID', 'FWD']

const headers = [
  { title: 'Team', key: 'name', align: 'start' as const },
  { title: 'City', key: 'city', align: 'start' as const },
  { title: 'Members', key: 'member_count', align: 'center' as const },
  { title: 'Rating', key: 'rating_score', align: 'center' as const },
  { title: 'Actions', key: 'actions', align: 'center' as const, sortable: false },
]

// Computed
const canCreateTeam = computed(() => isAuthenticated.value && isCaptain.value)

const filteredTeams = computed(() => {
  if (!search.value) return teams.value
  const q = search.value.toLowerCase()
  return teams.value.filter(t =>
    t.name?.toLowerCase().includes(q) || t.city?.toLowerCase().includes(q)
  )
})

// Methods
const getInitials = (name: string) => {
  if (!name) return '?'
  return name.split(' ').map((w: string) => w[0]).join('').toUpperCase().slice(0, 2)
}

const canJoinTeam = (team: any) => {
  if (!isAuthenticated.value || !user.value) return false
  if (team.captain_id === user.value.id) return false
  return true
}

const getRatingColor = (rating: number) => {
  if (!rating) return 'grey'
  if (rating >= 1500) return 'success'
  if (rating >= 1200) return 'primary'
  if (rating >= 900) return 'warning'
  return 'error'
}

const navigateToTeam = (team: any) => {
  router.push(`/teams/${team.id}`)
}

const goToMyTeam = async () => {
  try {
    const data = await $fetch<any>(`${apiBase.value}/teams/my/team`, {
      headers: getAuthHeaders(),
    })
    router.push(`/teams/${data.id}`)
  } catch {
    showMessage('You are not part of any team yet', 'info')
  }
}

// API calls
const config = useRuntimeConfig()
const apiBase = computed(() => config.public.apiBaseUrl || 'http://localhost:8000/api/v1')

const getAuthHeaders = () => {
  const token = useCookie('auth_token')
  return token.value ? { Authorization: `Bearer ${token.value}` } : {}
}

const fetchTeams = async () => {
  loading.value = true
  error.value = null
  try {
    const data = await $fetch<any[]>(`${apiBase.value}/teams`, {
      headers: getAuthHeaders(),
    })
    teams.value = data
  } catch (err: any) {
    error.value = err.data?.error?.message || err.data?.detail || 'Failed to load teams'
  } finally {
    loading.value = false
  }
}

const openJoinDialog = (team: any) => {
  selectedTeam.value = team
  joinRequest.value = { message: '', position: null }
  showJoinDialog.value = true
}

const geocodeCity = async () => {
  const city = newTeam.value.city.trim()
  if (!city) return
  geocoding.value = true
  geocodeResult.value = null
  geocodeError.value = null
  try {
    const results = await $fetch<any[]>(
      `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(city)}&format=json&limit=1`,
    )
    if (results?.length > 0) {
      newTeam.value.latitude = parseFloat(results[0].lat)
      newTeam.value.longitude = parseFloat(results[0].lon)
      geocodeResult.value = results[0].display_name?.split(',').slice(0, 2).join(',') || city
    } else {
      geocodeError.value = `"${city}" not found`
    }
  } catch {
    geocodeError.value = 'Geocoding service unavailable'
  } finally {
    geocoding.value = false
  }
}

const clearGeocode = () => {
  newTeam.value.latitude = null
  newTeam.value.longitude = null
  geocodeResult.value = null
  geocodeError.value = null
}

const closeCreateDialog = () => {
  showCreateDialog.value = false
  newTeam.value = { name: '', city: '', description: '', founded_year: null, latitude: null, longitude: null }
  geocodeResult.value = null
  geocodeError.value = null
}

const createTeam = async () => {
  if (!createFormValid.value) return

  submitting.value = true
  try {
    const data = await $fetch<any>(`${apiBase.value}/teams`, {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: {
        name: newTeam.value.name,
        city: newTeam.value.city || undefined,
        description: newTeam.value.description || undefined,
        founded_year: newTeam.value.founded_year || undefined,
        latitude: newTeam.value.latitude !== null ? newTeam.value.latitude : undefined,
        longitude: newTeam.value.longitude !== null ? newTeam.value.longitude : undefined,
      },
    })

    closeCreateDialog()
    showMessage('Team created successfully!', 'success')
    router.push(`/teams/${data.id}`)
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to create team', 'error')
  } finally {
    submitting.value = false
  }
}

const submitJoinRequest = async () => {
  if (!selectedTeam.value) return

  submitting.value = true
  try {
    await $fetch(`${apiBase.value}/join-requests`, {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: {
        team_id: selectedTeam.value.id,
        message: joinRequest.value.message || undefined,
        position: joinRequest.value.position || undefined,
      },
    })

    showJoinDialog.value = false
    showMessage('Join request sent!', 'success')
  } catch (err: any) {
    const errorCode = err.data?.error?.code
    const errorMsg = err.data?.error?.message || err.data?.detail || 'Failed to send request'

    if (errorCode === 'JOIN_REQUEST_ALREADY_EXISTS') {
      showJoinDialog.value = false
      showMessage('You already have a pending request for this team.', 'warning')
    } else {
      showMessage(errorMsg, 'error')
    }
  } finally {
    submitting.value = false
  }
}

const showMessage = (message: string, color: string) => {
  snackbarMessage.value = message
  snackbarColor.value = color
  showSnackbar.value = true
}

import { watch } from 'vue'

onMounted(() => {
  fetchTeams()
})
</script>

<style scoped>
:deep(.v-data-table) {
  background-color: transparent;
}
.cursor-pointer {
  cursor: pointer;
}

/* Team grid cards */
.team-grid-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border-radius: 16px !important;
}

.team-grid-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12) !important;
}

.team-grid-header {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  min-height: 88px;
}

.team-grid-avatar {
  border: 3px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
}
</style>
