<template>
  <!--
    Teams Page
    ==========
    Displays all teams with full CRUD functionality

    Features:
    - List all teams from API
    - Search and filter
    - Create team (for captains)
    - View team details
    - Join team requests
  -->
  <v-container class="py-8">
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center flex-wrap">
          <div>
            <h1 :class="$vuetify.display.xs ? 'text-h4' : 'text-h3'" class="font-weight-bold mb-2">
              <v-icon icon="mdi-shield-account" :size="$vuetify.display.xs ? 'default' : 'large'" class="mr-2" />
              Teams
            </h1>
            <p class="text-body-1 text-medium-emphasis">
              Browse and manage football teams in the platform
            </p>
          </div>

          <!-- Create Team Button (Captain only) -->
          <v-btn
            v-if="isCaptain && !hasTeam"
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
    <v-row v-if="teamStore.error">
      <v-col cols="12">
        <v-alert type="error" closable @click:close="teamStore.clearError()">
          {{ teamStore.error }}
        </v-alert>
      </v-col>
    </v-row>

    <!-- Data Table -->
    <v-row>
      <v-col cols="12">
        <v-card elevation="2">
          <v-card-title>
            <!-- Search Bar -->
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

          <!-- Teams Table -->
          <v-data-table
            :headers="headers"
            :items="teamStore.teams"
            :search="search"
            :items-per-page="10"
            :mobile-breakpoint="600"
            :loading="teamStore.loading"
            class="elevation-0"
          >
            <!-- Team Name Column with Logo -->
            <template #item.name="{ item }">
              <div class="d-flex align-center">
                <v-avatar size="32" class="mr-2">
                  <v-img v-if="item.logo_url" :src="item.logo_url" />
                  <v-icon v-else icon="mdi-shield" color="primary" />
                </v-avatar>
                <span class="font-weight-medium">{{ item.name }}</span>
              </div>
            </template>

            <!-- City Column -->
            <template #item.city="{ item }">
              <v-chip v-if="item.city" size="small" variant="outlined">
                <v-icon start size="small">mdi-map-marker</v-icon>
                {{ item.city }}
              </v-chip>
              <span v-else class="text-medium-emphasis">-</span>
            </template>

            <!-- Rating Column -->
            <template #item.rating_score="{ item }">
              <v-chip size="small" :color="getRatingColor(item.rating_score)">
                {{ item.rating_score || 1000 }}
              </v-chip>
            </template>

            <!-- Actions Column -->
            <template #item.actions="{ item }">
              <div class="d-flex gap-1">
                <v-btn
                  size="small"
                  color="primary"
                  variant="text"
                  @click="viewTeamDetails(item)"
                >
                  View
                </v-btn>
                <v-btn
                  v-if="isAuthenticated && !userTeam && item.captain_id !== user?.id"
                  size="small"
                  color="success"
                  variant="text"
                  @click="openJoinDialog(item)"
                >
                  Join
                </v-btn>
              </div>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create Team Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="600">
      <v-card>
        <v-card-title>
          <v-icon class="mr-2">mdi-plus</v-icon>
          Create New Team
        </v-card-title>

        <v-card-text>
          <v-form ref="createForm" @submit.prevent="createTeam">
            <v-text-field
              v-model="newTeam.name"
              label="Team Name"
              :rules="[v => !!v || 'Team name is required']"
              required
            />
            <v-text-field
              v-model="newTeam.city"
              label="City"
            />
            <v-textarea
              v-model="newTeam.description"
              label="Description"
              rows="3"
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
          <v-btn variant="text" @click="showCreateDialog = false">Cancel</v-btn>
          <v-btn color="primary" :loading="teamStore.loading" @click="createTeam">
            Create
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Join Team Dialog -->
    <v-dialog v-model="showJoinDialog" max-width="500">
      <v-card>
        <v-card-title>
          <v-icon class="mr-2">mdi-account-plus</v-icon>
          Join {{ selectedTeam?.name }}
        </v-card-title>

        <v-card-text>
          <v-form ref="joinForm" @submit.prevent="submitJoinRequest">
            <v-textarea
              v-model="joinRequest.message"
              label="Message to Captain (optional)"
              hint="Introduce yourself and explain why you want to join"
              rows="3"
            />
            <v-select
              v-model="joinRequest.position"
              label="Preferred Position"
              :items="positions"
              clearable
            />
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showJoinDialog = false">Cancel</v-btn>
          <v-btn color="success" :loading="teamStore.loading" @click="submitJoinRequest">
            Send Request
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Team Details Dialog -->
    <v-dialog v-model="showDetailsDialog" max-width="800">
      <v-card v-if="selectedTeam">
        <v-card-title class="d-flex align-center">
          <v-avatar size="48" class="mr-3">
            <v-img v-if="selectedTeam.logo_url" :src="selectedTeam.logo_url" />
            <v-icon v-else icon="mdi-shield" size="32" color="primary" />
          </v-avatar>
          <div>
            <div class="text-h5">{{ selectedTeam.name }}</div>
            <div class="text-caption text-medium-emphasis">
              {{ selectedTeam.city || 'No city specified' }}
            </div>
          </div>
          <v-spacer />
          <v-chip :color="getRatingColor(selectedTeam.rating_score)">
            Rating: {{ selectedTeam.rating_score || 1000 }}
          </v-chip>
        </v-card-title>

        <v-divider />

        <v-card-text>
          <!-- Description -->
          <div v-if="selectedTeam.description" class="mb-4">
            <div class="text-subtitle-2 mb-1">About</div>
            <p>{{ selectedTeam.description }}</p>
          </div>

          <!-- Team Info -->
          <v-row>
            <v-col cols="6" md="3">
              <div class="text-caption text-medium-emphasis">Founded</div>
              <div>{{ selectedTeam.founded_year || 'Unknown' }}</div>
            </v-col>
            <v-col cols="6" md="3">
              <div class="text-caption text-medium-emphasis">Members</div>
              <div>{{ teamMembers.length }}</div>
            </v-col>
            <v-col cols="6" md="3">
              <div class="text-caption text-medium-emphasis">Created</div>
              <div>{{ formatDate(selectedTeam.created_at) }}</div>
            </v-col>
          </v-row>

          <!-- Team Roster -->
          <div class="mt-6">
            <div class="text-subtitle-2 mb-2">Team Roster</div>
            <v-list density="compact">
              <v-list-item
                v-for="member in teamMembers"
                :key="member.id"
              >
                <template #prepend>
                  <v-avatar size="32">
                    <v-icon>mdi-account</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title>{{ member.user?.full_name || member.user?.username }}</v-list-item-title>
                <v-list-item-subtitle>
                  {{ member.position || 'No position' }}
                  <v-chip v-if="member.jersey_number" size="x-small" class="ml-1">
                    #{{ member.jersey_number }}
                  </v-chip>
                </v-list-item-subtitle>
                <template #append>
                  <v-chip size="small" :color="member.role === 'CAPTAIN' ? 'warning' : 'default'">
                    {{ member.role }}
                  </v-chip>
                </template>
              </v-list-item>
              <v-list-item v-if="teamMembers.length === 0">
                <v-list-item-title class="text-medium-emphasis">
                  No members yet
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </div>
        </v-card-text>

        <v-card-actions>
          <v-btn
            v-if="isAuthenticated && !userTeam && selectedTeam.captain_id !== user?.id"
            color="success"
            prepend-icon="mdi-account-plus"
            @click="openJoinDialogFromDetails"
          >
            Request to Join
          </v-btn>
          <v-spacer />
          <v-btn variant="text" @click="showDetailsDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Success Snackbar -->
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
import { useTeamStore } from '@/src/stores/team'
import { useAuth } from '@/composables/useAuth'

// Stores
const teamStore = useTeamStore()
const { user, isAuthenticated, isCaptain } = useAuth()

// Table headers
const headers = [
  { title: 'Team Name', key: 'name', align: 'start' as const },
  { title: 'City', key: 'city', align: 'start' as const },
  { title: 'Rating', key: 'rating_score', align: 'center' as const },
  { title: 'Actions', key: 'actions', align: 'center' as const, sortable: false },
]

// Search state
const search = ref('')

// Dialog states
const showCreateDialog = ref(false)
const showJoinDialog = ref(false)
const showDetailsDialog = ref(false)

// Selected team for dialogs
const selectedTeam = ref<any>(null)
const teamMembers = ref<any[]>([])

// Form data
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

// Position options
const positions = ['GK', 'DEF', 'MID', 'FWD']

// Snackbar state
const showSnackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

// Computed properties
const userTeam = computed(() => {
  return teamStore.currentTeam
})

const hasTeam = computed(() => {
  return !!userTeam.value
})

// Methods
const getRatingColor = (rating: number) => {
  if (rating >= 1500) return 'success'
  if (rating >= 1200) return 'primary'
  if (rating >= 900) return 'warning'
  return 'error'
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'Unknown'
  return new Date(dateString).toLocaleDateString()
}

const viewTeamDetails = async (team: any) => {
  selectedTeam.value = team
  showDetailsDialog.value = true

  try {
    const members = await teamStore.fetchTeamById(team.id)
    teamMembers.value = await fetchTeamMembers(team.id)
  } catch (error) {
    console.error('Error fetching team details:', error)
  }
}

const fetchTeamMembers = async (teamId: number) => {
  try {
    await teamStore.fetchTeamMembers(teamId)
    return teamStore.teamMembers
  } catch (error) {
    console.error('Error fetching team members:', error)
    return []
  }
}

const openJoinDialog = (team: any) => {
  selectedTeam.value = team
  joinRequest.value = { message: '', position: null }
  showJoinDialog.value = true
}

const openJoinDialogFromDetails = () => {
  showDetailsDialog.value = false
  joinRequest.value = { message: '', position: null }
  showJoinDialog.value = true
}

const createTeam = async () => {
  try {
    await teamStore.createTeam({
      name: newTeam.value.name,
      city: newTeam.value.city || undefined,
      description: newTeam.value.description || undefined,
      founded_year: newTeam.value.founded_year || undefined,
    })

    showCreateDialog.value = false
    newTeam.value = { name: '', city: '', description: '', founded_year: null }
    showSuccessMessage('Team created successfully!')
  } catch (error) {
    console.error('Error creating team:', error)
  }
}

const submitJoinRequest = async () => {
  if (!selectedTeam.value) return

  try {
    await teamStore.createJoinRequest(
      selectedTeam.value.id,
      joinRequest.value.message || undefined,
      joinRequest.value.position || undefined
    )

    showJoinDialog.value = false
    showSuccessMessage('Join request sent successfully!')
  } catch (error) {
    console.error('Error sending join request:', error)
  }
}

const showSuccessMessage = (message: string) => {
  snackbarMessage.value = message
  snackbarColor.value = 'success'
  showSnackbar.value = true
}

// Fetch teams on mount
onMounted(async () => {
  try {
    await teamStore.fetchAllTeams()
  } catch (error) {
    console.error('Error fetching teams:', error)
  }
})
</script>

<style scoped>
:deep(.v-data-table) {
  background-color: transparent;
}

:deep(.v-data-table tbody tr:hover) {
  background-color: rgba(0, 0, 0, 0.02);
}

:deep(.v-theme--dark .v-data-table tbody tr:hover) {
  background-color: rgba(255, 255, 255, 0.05);
}
</style>
