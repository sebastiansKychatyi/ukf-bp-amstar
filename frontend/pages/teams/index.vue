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

          <div class="d-flex ga-2">
            <!-- My Team Button -->
            <v-btn
              v-if="isAuthenticated"
              color="secondary"
              variant="outlined"
              prepend-icon="mdi-shield-home"
              @click="goToMyTeam"
            >
              My Team
            </v-btn>

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
            hover
            @click:row="(_e: any, { item }: any) => navigateToTeam(item)"
          >
            <!-- Team Name -->
            <template #item.name="{ item }">
              <div class="d-flex align-center cursor-pointer">
                <v-avatar size="32" class="mr-2" color="primary">
                  <v-img v-if="item.logo_url" :src="item.logo_url" />
                  <v-icon v-else icon="mdi-shield" size="20" />
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
          <v-btn color="success" :loading="submitting" @click="submitJoinRequest">
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
  { title: 'Members', key: 'member_count', align: 'center' as const },
  { title: 'Rating', key: 'rating_score', align: 'center' as const },
  { title: 'Actions', key: 'actions', align: 'center' as const, sortable: false },
]

// Computed
const canCreateTeam = computed(() => {
  return isAuthenticated.value && isCaptain.value
})

// Methods
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
    error.value = err.data?.detail || 'Failed to load teams'
  } finally {
    loading.value = false
  }
}

const openJoinDialog = (team: any) => {
  selectedTeam.value = team
  joinRequest.value = { message: '', position: null }
  showJoinDialog.value = true
}

const closeCreateDialog = () => {
  showCreateDialog.value = false
  newTeam.value = { name: '', city: '', description: '', founded_year: null }
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
      },
    })

    closeCreateDialog()
    showMessage('Team created successfully!', 'success')
    // Navigate to the new team's page
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
    showMessage(err.data?.detail || 'Failed to send request', 'error')
  } finally {
    submitting.value = false
  }
}

const showMessage = (message: string, color: string) => {
  snackbarMessage.value = message
  snackbarColor.value = color
  showSnackbar.value = true
}

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
</style>
