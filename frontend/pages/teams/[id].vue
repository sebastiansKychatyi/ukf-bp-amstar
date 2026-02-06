<template>
  <v-container class="py-8">
    <!-- Loading State -->
    <div v-if="loading" class="d-flex justify-center align-center" style="min-height: 400px">
      <v-progress-circular indeterminate size="64" color="primary" />
    </div>

    <!-- Error State -->
    <v-alert v-else-if="error" type="error" class="mb-4">
      {{ error }}
      <template #append>
        <v-btn variant="text" @click="fetchTeam">Retry</v-btn>
      </template>
    </v-alert>

    <!-- Team Detail Content -->
    <template v-else-if="team">
      <!-- Back Button + Team Header -->
      <v-row class="mb-2">
        <v-col cols="12">
          <v-btn variant="text" prepend-icon="mdi-arrow-left" @click="$router.push('/teams')">
            Back to Teams
          </v-btn>
        </v-col>
      </v-row>

      <!-- Team Profile Header -->
      <v-card class="mb-6" elevation="2">
        <v-card-text class="pa-6">
          <v-row align="center">
            <v-col cols="auto">
              <v-avatar size="80" color="primary" class="elevation-2">
                <v-img v-if="team.logo_url" :src="team.logo_url" />
                <v-icon v-else icon="mdi-shield" size="48" />
              </v-avatar>
            </v-col>
            <v-col>
              <h1 class="text-h4 font-weight-bold">{{ team.name }}</h1>
              <div class="d-flex align-center flex-wrap ga-2 mt-1">
                <v-chip v-if="team.city" size="small" variant="outlined" prepend-icon="mdi-map-marker">
                  {{ team.city }}
                </v-chip>
                <v-chip size="small" :color="getRatingColor(team.rating_score)">
                  Rating: {{ team.rating_score || 1000 }}
                </v-chip>
                <v-chip size="small" variant="outlined" prepend-icon="mdi-account-group">
                  {{ team.member_count }} members
                </v-chip>
                <v-chip v-if="team.founded_year" size="small" variant="outlined" prepend-icon="mdi-calendar">
                  Est. {{ team.founded_year }}
                </v-chip>
              </div>
              <p v-if="team.description" class="text-body-2 text-medium-emphasis mt-2 mb-0">
                {{ team.description }}
              </p>
              <div v-if="team.captain" class="text-body-2 mt-2">
                <v-icon size="small" class="mr-1">mdi-crown</v-icon>
                Captain: <strong>{{ team.captain.full_name || team.captain.username }}</strong>
              </div>
            </v-col>
            <v-col cols="auto" class="d-flex flex-column ga-2">
              <!-- Join Button (for non-members) -->
              <v-btn
                v-if="canJoinTeam"
                color="success"
                prepend-icon="mdi-account-plus"
                @click="showJoinDialog = true"
              >
                Request to Join
              </v-btn>
              <!-- Leave Button (for members who are not captain) -->
              <v-btn
                v-if="canLeaveTeam"
                color="warning"
                variant="outlined"
                prepend-icon="mdi-account-minus"
                @click="showLeaveDialog = true"
              >
                Leave Team
              </v-btn>
              <!-- Captain Actions -->
              <template v-if="isCaptainOfTeam">
                <v-btn
                  color="primary"
                  variant="outlined"
                  prepend-icon="mdi-pencil"
                  @click="showEditDialog = true"
                >
                  Edit Team
                </v-btn>
                <v-btn
                  color="error"
                  variant="outlined"
                  prepend-icon="mdi-delete"
                  @click="showDeleteDialog = true"
                >
                  Delete Team
                </v-btn>
              </template>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- Statistics Summary Cards -->
      <v-row class="mb-6">
        <v-col cols="6" sm="3">
          <v-card elevation="1" class="text-center pa-4">
            <div class="text-h4 font-weight-bold text-primary">{{ stats.total_matches }}</div>
            <div class="text-caption text-medium-emphasis">Matches Played</div>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card elevation="1" class="text-center pa-4">
            <div class="text-h4 font-weight-bold text-success">{{ stats.wins }}</div>
            <div class="text-caption text-medium-emphasis">Wins</div>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card elevation="1" class="text-center pa-4">
            <div class="text-h4 font-weight-bold text-grey">{{ stats.draws }}</div>
            <div class="text-caption text-medium-emphasis">Draws</div>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card elevation="1" class="text-center pa-4">
            <div class="text-h4 font-weight-bold text-error">{{ stats.losses }}</div>
            <div class="text-caption text-medium-emphasis">Losses</div>
          </v-card>
        </v-col>
      </v-row>

      <!-- Goal Stats Row -->
      <v-row class="mb-6">
        <v-col cols="4">
          <v-card elevation="1" class="text-center pa-3">
            <div class="text-h5 font-weight-bold">{{ stats.goals_scored }}</div>
            <div class="text-caption text-medium-emphasis">Goals Scored</div>
          </v-card>
        </v-col>
        <v-col cols="4">
          <v-card elevation="1" class="text-center pa-3">
            <div class="text-h5 font-weight-bold">{{ stats.goals_conceded }}</div>
            <div class="text-caption text-medium-emphasis">Goals Conceded</div>
          </v-card>
        </v-col>
        <v-col cols="4">
          <v-card elevation="1" class="text-center pa-3">
            <div class="text-h5 font-weight-bold" :class="stats.goal_difference >= 0 ? 'text-success' : 'text-error'">
              {{ stats.goal_difference >= 0 ? '+' : '' }}{{ stats.goal_difference }}
            </div>
            <div class="text-caption text-medium-emphasis">Goal Difference</div>
          </v-card>
        </v-col>
      </v-row>

      <!-- Tabs: Roster | Match History | Join Requests (captain only) -->
      <v-card elevation="2">
        <v-tabs v-model="activeTab" color="primary">
          <v-tab value="roster">
            <v-icon start>mdi-account-group</v-icon>
            Roster
          </v-tab>
          <v-tab value="matches">
            <v-icon start>mdi-soccer-field</v-icon>
            Match History
          </v-tab>
          <v-tab v-if="isCaptainOfTeam" value="requests">
            <v-icon start>mdi-account-clock</v-icon>
            Join Requests
            <v-badge v-if="pendingRequests.length" :content="pendingRequests.length" color="error" inline />
          </v-tab>
        </v-tabs>

        <v-divider />

        <v-window v-model="activeTab">
          <!-- ROSTER TAB -->
          <v-window-item value="roster">
            <v-card-text>
              <v-data-table
                :headers="rosterHeaders"
                :items="rosterWithStats"
                :items-per-page="15"
                class="elevation-0"
                no-data-text="No team members yet"
              >
                <template #item.user="{ item }">
                  <div class="d-flex align-center">
                    <v-avatar size="32" class="mr-2" color="grey-lighten-2">
                      <v-icon>mdi-account</v-icon>
                    </v-avatar>
                    <div>
                      <div class="font-weight-medium">
                        {{ item.user?.full_name || item.user?.username }}
                      </div>
                      <div class="text-caption text-medium-emphasis">
                        @{{ item.user?.username }}
                      </div>
                    </div>
                  </div>
                </template>

                <template #item.role="{ item }">
                  <v-chip
                    size="small"
                    :color="item.role === 'CAPTAIN' ? 'warning' : 'default'"
                    :prepend-icon="item.role === 'CAPTAIN' ? 'mdi-crown' : 'mdi-account'"
                  >
                    {{ item.role }}
                  </v-chip>
                </template>

                <template #item.position="{ item }">
                  <v-chip v-if="item.position" size="small" variant="outlined">
                    {{ item.position }}
                  </v-chip>
                  <span v-else class="text-medium-emphasis">-</span>
                </template>

                <template #item.jersey_number="{ item }">
                  <span v-if="item.jersey_number" class="font-weight-bold">#{{ item.jersey_number }}</span>
                  <span v-else class="text-medium-emphasis">-</span>
                </template>

                <template #item.goals="{ item }">
                  {{ item.goals || 0 }}
                </template>

                <template #item.assists="{ item }">
                  {{ item.assists || 0 }}
                </template>

                <template #item.matches_played="{ item }">
                  {{ item.matches_played || 0 }}
                </template>

                <template #item.cards="{ item }">
                  <div class="d-flex ga-1">
                    <v-chip v-if="item.yellow_cards" size="x-small" color="yellow-darken-2" variant="flat">
                      {{ item.yellow_cards }}
                    </v-chip>
                    <v-chip v-if="item.red_cards" size="x-small" color="red" variant="flat" class="text-white">
                      {{ item.red_cards }}
                    </v-chip>
                    <span v-if="!item.yellow_cards && !item.red_cards" class="text-medium-emphasis">-</span>
                  </div>
                </template>

                <template #item.actions="{ item }">
                  <div v-if="isCaptainOfTeam && item.role !== 'CAPTAIN'" class="d-flex ga-1">
                    <v-btn size="small" icon="mdi-pencil" variant="text" @click="openEditMember(item)" />
                    <v-btn size="small" icon="mdi-account-remove" variant="text" color="error" @click="openRemoveMember(item)" />
                  </div>
                </template>
              </v-data-table>
            </v-card-text>
          </v-window-item>

          <!-- MATCH HISTORY TAB -->
          <v-window-item value="matches">
            <v-card-text>
              <v-data-table
                :headers="matchHeaders"
                :items="matches"
                :items-per-page="10"
                class="elevation-0"
                no-data-text="No matches played yet"
              >
                <template #item.result="{ item }">
                  <v-chip
                    v-if="item.result"
                    size="small"
                    :color="item.result === 'W' ? 'success' : item.result === 'L' ? 'error' : 'grey'"
                  >
                    {{ item.result === 'W' ? 'Win' : item.result === 'L' ? 'Loss' : 'Draw' }}
                  </v-chip>
                  <v-chip v-else size="small" color="info" variant="outlined">
                    Upcoming
                  </v-chip>
                </template>

                <template #item.score="{ item }">
                  <span v-if="item.team_score !== null && item.opponent_score !== null" class="font-weight-bold">
                    {{ item.team_score }} - {{ item.opponent_score }}
                  </span>
                  <span v-else class="text-medium-emphasis">-</span>
                </template>

                <template #item.match_date="{ item }">
                  {{ item.match_date ? formatDate(item.match_date) : 'TBD' }}
                </template>

                <template #item.opponent_name="{ item }">
                  <span class="font-weight-medium">{{ item.opponent_name }}</span>
                </template>
              </v-data-table>
            </v-card-text>
          </v-window-item>

          <!-- JOIN REQUESTS TAB (Captain only) -->
          <v-window-item v-if="isCaptainOfTeam" value="requests">
            <v-card-text>
              <v-alert v-if="!pendingRequests.length" type="info" variant="tonal" density="compact" class="mb-4">
                No pending join requests
              </v-alert>

              <v-list v-else>
                <v-list-item
                  v-for="request in pendingRequests"
                  :key="request.id"
                  class="mb-2 border rounded"
                >
                  <template #prepend>
                    <v-avatar color="grey-lighten-2">
                      <v-icon>mdi-account</v-icon>
                    </v-avatar>
                  </template>

                  <v-list-item-title class="font-weight-medium">
                    {{ request.user?.full_name || request.user?.username || 'Unknown Player' }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    <span v-if="request.position">Position: {{ request.position }} | </span>
                    Requested: {{ formatDate(request.created_at) }}
                  </v-list-item-subtitle>
                  <div v-if="request.message" class="text-body-2 mt-1 text-medium-emphasis">
                    "{{ request.message }}"
                  </div>

                  <template #append>
                    <div class="d-flex ga-2">
                      <v-btn
                        size="small"
                        color="success"
                        variant="flat"
                        prepend-icon="mdi-check"
                        :loading="reviewingId === request.id"
                        @click="reviewRequest(request.id, 'ACCEPTED')"
                      >
                        Accept
                      </v-btn>
                      <v-btn
                        size="small"
                        color="error"
                        variant="outlined"
                        prepend-icon="mdi-close"
                        :loading="reviewingId === request.id"
                        @click="reviewRequest(request.id, 'REJECTED')"
                      >
                        Reject
                      </v-btn>
                    </div>
                  </template>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-window-item>
        </v-window>
      </v-card>
    </template>

    <!-- JOIN TEAM DIALOG -->
    <v-dialog v-model="showJoinDialog" max-width="500" persistent>
      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-account-plus</v-icon>
          Join {{ team?.name }}
        </v-card-title>
        <v-card-text>
          <v-textarea
            v-model="joinForm.message"
            label="Message to Captain (optional)"
            hint="Introduce yourself and why you want to join"
            rows="3"
            class="mb-3"
          />
          <v-select
            v-model="joinForm.position"
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

    <!-- LEAVE TEAM DIALOG -->
    <v-dialog v-model="showLeaveDialog" max-width="450">
      <v-card>
        <v-card-title class="text-error">
          <v-icon class="mr-2" color="error">mdi-alert</v-icon>
          Leave Team
        </v-card-title>
        <v-card-text>
          Are you sure you want to leave <strong>{{ team?.name }}</strong>?
          This action cannot be undone. You will need to send a new join request to rejoin.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showLeaveDialog = false">Cancel</v-btn>
          <v-btn color="error" :loading="submitting" @click="leaveTeam">
            Leave Team
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- DELETE TEAM DIALOG -->
    <v-dialog v-model="showDeleteDialog" max-width="450">
      <v-card>
        <v-card-title class="text-error">
          <v-icon class="mr-2" color="error">mdi-alert-circle</v-icon>
          Delete Team
        </v-card-title>
        <v-card-text>
          <p class="mb-3">
            Are you sure you want to permanently delete <strong>{{ team?.name }}</strong>?
          </p>
          <v-alert type="warning" variant="tonal" density="compact">
            This will remove all team members and pending join requests. This action cannot be undone.
          </v-alert>
          <v-text-field
            v-model="deleteConfirmation"
            :label="`Type '${team?.name}' to confirm`"
            class="mt-4"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDeleteDialog = false">Cancel</v-btn>
          <v-btn
            color="error"
            :loading="submitting"
            :disabled="deleteConfirmation !== team?.name"
            @click="deleteTeam"
          >
            Delete Permanently
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- EDIT TEAM DIALOG -->
    <v-dialog v-model="showEditDialog" max-width="600" persistent>
      <v-card>
        <v-card-title>
          <v-icon class="mr-2">mdi-pencil</v-icon>
          Edit Team
        </v-card-title>
        <v-card-text>
          <v-form ref="editForm" v-model="editFormValid">
            <v-text-field
              v-model="editData.name"
              label="Team Name *"
              :rules="[v => !!v || 'Required', v => v.length >= 2 || 'Min 2 characters']"
              class="mb-3"
            />
            <v-text-field v-model="editData.city" label="City" class="mb-3" />
            <v-textarea v-model="editData.description" label="Description" rows="3" class="mb-3" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showEditDialog = false">Cancel</v-btn>
          <v-btn color="primary" :loading="submitting" :disabled="!editFormValid" @click="updateTeam">
            Save Changes
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- EDIT MEMBER DIALOG -->
    <v-dialog v-model="showEditMemberDialog" max-width="400">
      <v-card>
        <v-card-title>Edit Member</v-card-title>
        <v-card-text>
          <v-select
            v-model="editMemberData.position"
            label="Position"
            :items="positions"
            clearable
            class="mb-3"
          />
          <v-text-field
            v-model.number="editMemberData.jersey_number"
            label="Jersey Number"
            type="number"
            :min="1"
            :max="99"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showEditMemberDialog = false">Cancel</v-btn>
          <v-btn color="primary" :loading="submitting" @click="updateMember">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- REMOVE MEMBER DIALOG -->
    <v-dialog v-model="showRemoveMemberDialog" max-width="400">
      <v-card>
        <v-card-title class="text-error">Remove Member</v-card-title>
        <v-card-text>
          Are you sure you want to remove
          <strong>{{ selectedMember?.user?.full_name || selectedMember?.user?.username }}</strong>
          from the team?
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showRemoveMemberDialog = false">Cancel</v-btn>
          <v-btn color="error" :loading="submitting" @click="removeMember">Remove</v-btn>
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
const router = useRouter()
const { user, isAuthenticated, isCaptain } = useAuth()

const teamId = computed(() => Number(route.params.id))

// State
const team = ref<any>(null)
const rosterWithStats = ref<any[]>([])
const matches = ref<any[]>([])
const stats = ref({
  total_matches: 0, wins: 0, draws: 0, losses: 0,
  goals_scored: 0, goals_conceded: 0, goal_difference: 0, win_rate: 0,
})
const pendingRequests = ref<any[]>([])
const loading = ref(true)
const submitting = ref(false)
const error = ref<string | null>(null)
const activeTab = ref('roster')
const reviewingId = ref<number | null>(null)

// Dialog states
const showJoinDialog = ref(false)
const showLeaveDialog = ref(false)
const showDeleteDialog = ref(false)
const showEditDialog = ref(false)
const showEditMemberDialog = ref(false)
const showRemoveMemberDialog = ref(false)

// Form states
const joinForm = ref({ message: '', position: null as string | null })
const deleteConfirmation = ref('')
const editFormValid = ref(false)
const editData = ref({ name: '', city: '', description: '' })
const editMemberData = ref({ position: null as string | null, jersey_number: null as number | null })
const selectedMember = ref<any>(null)

// Snackbar
const showSnackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

// Constants
const positions = ['GK', 'DEF', 'MID', 'FWD']

const rosterHeaders = [
  { title: 'Player', key: 'user', align: 'start' as const },
  { title: 'Role', key: 'role', align: 'center' as const },
  { title: 'Position', key: 'position', align: 'center' as const },
  { title: '#', key: 'jersey_number', align: 'center' as const },
  { title: 'Goals', key: 'goals', align: 'center' as const },
  { title: 'Assists', key: 'assists', align: 'center' as const },
  { title: 'Matches', key: 'matches_played', align: 'center' as const },
  { title: 'Cards', key: 'cards', align: 'center' as const },
  { title: '', key: 'actions', align: 'end' as const, sortable: false },
]

const matchHeaders = [
  { title: 'Result', key: 'result', align: 'center' as const },
  { title: 'Score', key: 'score', align: 'center' as const },
  { title: 'Opponent', key: 'opponent_name', align: 'start' as const },
  { title: 'Date', key: 'match_date', align: 'center' as const },
  { title: 'Location', key: 'location', align: 'start' as const },
]

// Computed
const isCaptainOfTeam = computed(() => {
  return isAuthenticated.value && user.value && team.value && team.value.captain_id === user.value.id
})

const isMemberOfTeam = computed(() => {
  if (!isAuthenticated.value || !user.value || !rosterWithStats.value.length) return false
  return rosterWithStats.value.some((m: any) => m.user_id === user.value!.id)
})

const canJoinTeam = computed(() => {
  if (!isAuthenticated.value || !user.value || !team.value) return false
  if (isMemberOfTeam.value) return false
  if (team.value.captain_id === user.value.id) return false
  return true
})

const canLeaveTeam = computed(() => {
  return isMemberOfTeam.value && !isCaptainOfTeam.value
})

// API
const config = useRuntimeConfig()
const apiBase = computed(() => config.public.apiBaseUrl || 'http://localhost:8000/api/v1')

const getAuthHeaders = () => {
  const token = useCookie('auth_token')
  return token.value ? { Authorization: `Bearer ${token.value}` } : {}
}

// Helper
const getRatingColor = (rating: number) => {
  if (!rating) return 'grey'
  if (rating >= 1500) return 'success'
  if (rating >= 1200) return 'primary'
  if (rating >= 900) return 'warning'
  return 'error'
}

const formatDate = (dateString: string) => {
  if (!dateString) return 'Unknown'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

const showMessage = (message: string, color: string) => {
  snackbarMessage.value = message
  snackbarColor.value = color
  showSnackbar.value = true
}

// Fetch all data
const fetchTeam = async () => {
  loading.value = true
  error.value = null
  try {
    team.value = await $fetch<any>(`${apiBase.value}/teams/${teamId.value}`, {
      headers: getAuthHeaders(),
    })
  } catch (err: any) {
    error.value = err.data?.detail || 'Failed to load team'
    return
  } finally {
    loading.value = false
  }

  // Fetch remaining data in parallel
  await Promise.allSettled([
    fetchRosterStats(),
    fetchStats(),
    fetchMatches(),
    ...(isCaptainOfTeam.value ? [fetchPendingRequests()] : []),
  ])
}

const fetchRosterStats = async () => {
  try {
    rosterWithStats.value = await $fetch<any[]>(`${apiBase.value}/teams/${teamId.value}/roster-stats`, {
      headers: getAuthHeaders(),
    })
  } catch {
    rosterWithStats.value = []
  }
}

const fetchStats = async () => {
  try {
    stats.value = await $fetch<any>(`${apiBase.value}/teams/${teamId.value}/stats`, {
      headers: getAuthHeaders(),
    })
  } catch {
    // Keep defaults
  }
}

const fetchMatches = async () => {
  try {
    matches.value = await $fetch<any[]>(`${apiBase.value}/teams/${teamId.value}/matches`, {
      headers: getAuthHeaders(),
    })
  } catch {
    matches.value = []
  }
}

const fetchPendingRequests = async () => {
  try {
    pendingRequests.value = await $fetch<any[]>(
      `${apiBase.value}/join-requests/team/${teamId.value}/pending`,
      { headers: getAuthHeaders() }
    )
  } catch {
    pendingRequests.value = []
  }
}

// Actions
const submitJoinRequest = async () => {
  submitting.value = true
  try {
    await $fetch(`${apiBase.value}/join-requests`, {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: {
        team_id: teamId.value,
        message: joinForm.value.message || undefined,
        position: joinForm.value.position || undefined,
      },
    })
    showJoinDialog.value = false
    showMessage('Join request sent successfully!', 'success')
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to send join request', 'error')
  } finally {
    submitting.value = false
  }
}

const leaveTeam = async () => {
  submitting.value = true
  try {
    await $fetch(`${apiBase.value}/teams/${teamId.value}/leave`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    showLeaveDialog.value = false
    showMessage('You have left the team', 'success')
    await fetchTeam()
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to leave team', 'error')
  } finally {
    submitting.value = false
  }
}

const deleteTeam = async () => {
  submitting.value = true
  try {
    await $fetch(`${apiBase.value}/teams/${teamId.value}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    })
    showMessage('Team deleted', 'success')
    router.push('/teams')
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to delete team', 'error')
  } finally {
    submitting.value = false
  }
}

const updateTeam = async () => {
  submitting.value = true
  try {
    const updated = await $fetch<any>(`${apiBase.value}/teams/${teamId.value}`, {
      method: 'PUT',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: {
        name: editData.value.name,
        city: editData.value.city || undefined,
        description: editData.value.description || undefined,
      },
    })
    team.value = { ...team.value, ...updated }
    showEditDialog.value = false
    showMessage('Team updated', 'success')
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to update team', 'error')
  } finally {
    submitting.value = false
  }
}

const reviewRequest = async (requestId: number, status: string) => {
  reviewingId.value = requestId
  try {
    await $fetch(`${apiBase.value}/join-requests/${requestId}/review`, {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: { status },
    })
    showMessage(`Request ${status.toLowerCase()}`, status === 'ACCEPTED' ? 'success' : 'info')
    // Refresh data
    await Promise.allSettled([fetchPendingRequests(), fetchRosterStats()])
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to review request', 'error')
  } finally {
    reviewingId.value = null
  }
}

// Member management
const openEditMember = (member: any) => {
  selectedMember.value = member
  editMemberData.value = {
    position: member.position,
    jersey_number: member.jersey_number,
  }
  showEditMemberDialog.value = true
}

const openRemoveMember = (member: any) => {
  selectedMember.value = member
  showRemoveMemberDialog.value = true
}

const updateMember = async () => {
  if (!selectedMember.value) return
  submitting.value = true
  try {
    await $fetch(`${apiBase.value}/teams/${teamId.value}/members/${selectedMember.value.user_id}`, {
      method: 'PUT',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: editMemberData.value,
    })
    showEditMemberDialog.value = false
    showMessage('Member updated', 'success')
    await fetchRosterStats()
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to update member', 'error')
  } finally {
    submitting.value = false
  }
}

const removeMember = async () => {
  if (!selectedMember.value) return
  submitting.value = true
  try {
    await $fetch(`${apiBase.value}/teams/${teamId.value}/members/${selectedMember.value.user_id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    })
    showRemoveMemberDialog.value = false
    showMessage('Member removed', 'success')
    await fetchRosterStats()
  } catch (err: any) {
    showMessage(err.data?.detail || 'Failed to remove member', 'error')
  } finally {
    submitting.value = false
  }
}

// Watch for edit dialog opening
watch(showEditDialog, (val) => {
  if (val && team.value) {
    editData.value = {
      name: team.value.name,
      city: team.value.city || '',
      description: team.value.description || '',
    }
  }
})

// Watch for captain status to load join requests
watch(isCaptainOfTeam, (val) => {
  if (val) fetchPendingRequests()
})

onMounted(() => {
  fetchTeam()
})
</script>

<style scoped>
:deep(.v-data-table) {
  background-color: transparent;
}
</style>
