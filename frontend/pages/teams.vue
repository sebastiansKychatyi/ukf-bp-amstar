<template>
  <v-container class="py-8">
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center flex-wrap ga-2">
          <div>
            <h1 :class="$vuetify.display.xs ? 'text-h4' : 'text-h3'" class="font-weight-bold mb-2">
              <v-icon icon="mdi-shield-account" :size="$vuetify.display.xs ? 'default' : 'large'" class="mr-2" />
              Teams
            </h1>
            <p class="text-body-1 text-medium-emphasis">
              Browse and manage football teams
            </p>
          </div>

          <!-- Create Team Button -->
          <v-btn
            v-if="canCreateTeam"
            color="primary"
            prepend-icon="mdi-plus"
            @click="showCreateDialog = true"
          >
            Create Team
          </v-btn>
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

    <!-- Teams Table -->
    <v-row>
      <v-col cols="12">
        <v-card elevation="2">
          <v-card-title>
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              label="Search teams"
              single-line
              hide-details
              variant="outlined"
              density="comfortable"
              class="mb-4"
            />
          </v-card-title>

          <v-data-table
            :headers="headers"
            :items="teams"
            :search="search"
            :items-per-page="10"
            :loading="loading"
            class="elevation-0"
          >
            <!-- Team Name -->
            <template #item.name="{ item }">
              <div class="d-flex align-center">
                <v-avatar size="32" class="mr-2" color="primary">
                  <v-img v-if="item.logo_url" :src="item.logo_url" />
                  <v-icon v-else icon="mdi-shield" size="20" />
                </v-avatar>
                <span class="font-weight-medium">{{ item.name }}</span>
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

            <!-- Rating -->
            <template #item.rating="{ item }">
              <v-chip size="small" :color="getRatingColor(item.rating || item.rating_score)">
                {{ item.rating || item.rating_score || 1000 }}
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
                  @click="viewTeam(item)"
                />
                <v-btn
                  v-if="canJoinTeam(item)"
                  size="small"
                  color="success"
                  variant="text"
                  icon="mdi-account-plus"
                  @click="openJoinDialog(item)"
                />
              </div>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create Team Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="600" persistent>
      <v-card>
        <v-card-title class="d-flex align-center">
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
              class="mb-3"
            />
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

        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeCreateDialog">Cancel</v-btn>
          <v-btn
            color="primary"
            :loading="loading"
            :disabled="!createFormValid"
            @click="createTeam"
          >
            Create
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- View Team Dialog -->
    <v-dialog v-model="showViewDialog" max-width="800">
      <v-card v-if="selectedTeam">
        <v-card-title class="d-flex align-center pa-4">
          <v-avatar size="56" class="mr-4" color="primary">
            <v-img v-if="selectedTeam.logo_url" :src="selectedTeam.logo_url" />
            <v-icon v-else icon="mdi-shield" size="32" />
          </v-avatar>
          <div class="flex-grow-1">
            <div class="text-h5">{{ selectedTeam.name }}</div>
            <div class="text-subtitle-2 text-medium-emphasis">
              {{ selectedTeam.city || 'No city' }}
            </div>
          </div>
          <v-chip :color="getRatingColor(selectedTeam.rating || selectedTeam.rating_score)" size="large">
            {{ selectedTeam.rating || selectedTeam.rating_score || 1000 }}
          </v-chip>
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-4">
          <div v-if="selectedTeam.description" class="mb-4">
            <div class="text-overline">About</div>
            <p>{{ selectedTeam.description }}</p>
          </div>

          <v-row class="mb-4">
            <v-col cols="6" sm="3">
              <div class="text-overline">Founded</div>
              <div class="text-body-1">{{ selectedTeam.founded_year || 'Unknown' }}</div>
            </v-col>
            <v-col cols="6" sm="3">
              <div class="text-overline">Members</div>
              <div class="text-body-1">{{ teamMembers.length }}</div>
            </v-col>
            <v-col cols="6" sm="3">
              <div class="text-overline">Created</div>
              <div class="text-body-1">{{ formatDate(selectedTeam.created_at) }}</div>
            </v-col>
          </v-row>

          <!-- Team Roster -->
          <div class="text-overline mb-2">Team Roster</div>
          <v-list v-if="teamMembers.length" density="compact" class="bg-grey-lighten-4 rounded">
            <v-list-item v-for="member in teamMembers" :key="member.id">
              <template #prepend>
                <v-avatar size="36" color="grey-lighten-2">
                  <v-icon>mdi-account</v-icon>
                </v-avatar>
              </template>
              <v-list-item-title>
                {{ member.user?.full_name || member.user?.username || 'Unknown' }}
              </v-list-item-title>
              <v-list-item-subtitle>
                {{ member.position || 'No position' }}
                <v-chip v-if="member.jersey_number" size="x-small" class="ml-1">#{{ member.jersey_number }}</v-chip>
              </v-list-item-subtitle>
              <template #append>
                <v-chip size="small" :color="member.role === 'CAPTAIN' ? 'warning' : 'default'">
                  {{ member.role }}
                </v-chip>
              </template>
            </v-list-item>
          </v-list>
          <v-alert v-else type="info" variant="tonal" density="compact">
            No team members yet
          </v-alert>
        </v-card-text>

        <v-card-actions class="pa-4">
          <v-btn
            v-if="canJoinTeam(selectedTeam)"
            color="success"
            prepend-icon="mdi-account-plus"
            @click="openJoinDialogFromView"
          >
            Request to Join
          </v-btn>
          <v-spacer />
          <v-btn variant="text" @click="showViewDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Join Team Dialog -->
    <v-dialog v-model="showJoinDialog" max-width="500" persistent>
      <v-card>
        <v-card-title class="d-flex align-center">
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

        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showJoinDialog = false">Cancel</v-btn>
          <v-btn color="success" :loading="loading" @click="submitJoinRequest">
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

// Auth composable
const { user, isAuthenticated, isCaptain } = useAuth()

// State
const teams = ref<any[]>([])
const teamMembers = ref<any[]>([])
const selectedTeam = ref<any>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const search = ref('')

// Dialog states
const showCreateDialog = ref(false)
const showViewDialog = ref(false)
const showJoinDialog = ref(false)

// Form states
const createForm = ref()
const createFormValid = ref(false)
const newTeam = ref({
  name: '',
  city: '',
  description: '',
  founded_year: null as number | null,
})

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
  { title: 'Rating', key: 'rating', align: 'center' as const },
  { title: 'Actions', key: 'actions', align: 'center' as const, sortable: false },
]

// Computed
const canCreateTeam = computed(() => {
  return isAuthenticated.value && isCaptain.value
})

// Methods
const canJoinTeam = (team: any) => {
  if (!isAuthenticated.value) return false
  if (!user.value) return false
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

const formatDate = (dateString: string) => {
  if (!dateString) return 'Unknown'
  return new Date(dateString).toLocaleDateString()
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
    console.error('Error fetching teams:', err)
    error.value = err.data?.detail || 'Failed to load teams'
  } finally {
    loading.value = false
  }
}

const fetchTeamMembers = async (teamId: number) => {
  try {
    const data = await $fetch<any[]>(`${apiBase.value}/teams/${teamId}/members`, {
      headers: getAuthHeaders(),
    })
    teamMembers.value = data
  } catch (err: any) {
    console.error('Error fetching members:', err)
    teamMembers.value = []
  }
}

const viewTeam = async (team: any) => {
  selectedTeam.value = team
  showViewDialog.value = true
  await fetchTeamMembers(team.id)
}

const openJoinDialog = (team: any) => {
  selectedTeam.value = team
  joinRequest.value = { message: '', position: null }
  showJoinDialog.value = true
}

const openJoinDialogFromView = () => {
  showViewDialog.value = false
  joinRequest.value = { message: '', position: null }
  showJoinDialog.value = true
}

const closeCreateDialog = () => {
  showCreateDialog.value = false
  newTeam.value = { name: '', city: '', description: '', founded_year: null }
}

const createTeam = async () => {
  if (!createFormValid.value) return

  loading.value = true
  try {
    const data = await $fetch<any>(`${apiBase.value}/teams`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: {
        name: newTeam.value.name,
        city: newTeam.value.city || undefined,
        description: newTeam.value.description || undefined,
        founded_year: newTeam.value.founded_year || undefined,
      },
    })

    teams.value.push(data)
    closeCreateDialog()
    showMessage('Team created successfully!', 'success')
  } catch (err: any) {
    console.error('Error creating team:', err)
    showMessage(err.data?.detail || 'Failed to create team', 'error')
  } finally {
    loading.value = false
  }
}

const submitJoinRequest = async () => {
  if (!selectedTeam.value) return

  loading.value = true
  try {
    await $fetch(`${apiBase.value}/join-requests`, {
      method: 'POST',
      headers: {
        ...getAuthHeaders(),
        'Content-Type': 'application/json',
      },
      body: {
        team_id: selectedTeam.value.id,
        message: joinRequest.value.message || undefined,
        position: joinRequest.value.position || undefined,
      },
    })

    showJoinDialog.value = false
    showMessage('Join request sent!', 'success')
  } catch (err: any) {
    console.error('Error sending join request:', err)
    showMessage(err.data?.detail || 'Failed to send request', 'error')
  } finally {
    loading.value = false
  }
}

const showMessage = (message: string, color: string) => {
  snackbarMessage.value = message
  snackbarColor.value = color
  showSnackbar.value = true
}

// Load teams on mount
onMounted(() => {
  fetchTeams()
})
</script>

<style scoped>
:deep(.v-data-table) {
  background-color: transparent;
}
</style>
