<template>
  <!-- Captain Dashboard: manage team info, roster, and join requests -->
  <v-container>
    <!-- Team Info Card -->
    <v-row>
      <v-col cols="12" md="8">
        <v-card v-if="team">
          <v-card-title class="d-flex align-center">
            <v-avatar size="64" class="mr-4">
              <v-img v-if="team.logo_url" :src="team.logo_url" />
              <v-icon v-else icon="mdi-shield" size="40" color="primary" />
            </v-avatar>
            <div>
              <div class="text-h4">{{ team.name }}</div>
              <div class="text-subtitle-1 text-medium-emphasis">
                {{ team.city || 'No city specified' }}
              </div>
            </div>
            <v-spacer />
            <v-chip size="large" :color="getRatingColor(team.rating_score)">
              Rating: {{ team.rating_score || 1000 }}
            </v-chip>
          </v-card-title>

          <v-card-text>
            <p v-if="team.description">{{ team.description }}</p>
            <p v-else class="text-medium-emphasis">No description provided</p>

            <v-divider class="my-4" />

            <v-row>
              <v-col cols="4">
                <div class="text-caption text-medium-emphasis">Founded</div>
                <div class="text-h6">{{ team.founded_year || 'Unknown' }}</div>
              </v-col>
              <v-col cols="4">
                <div class="text-caption text-medium-emphasis">Members</div>
                <div class="text-h6">{{ teamStore.teamMembers.length }}</div>
              </v-col>
              <v-col cols="4">
                <div class="text-caption text-medium-emphasis">Pending Requests</div>
                <div class="text-h6">{{ teamStore.pendingJoinRequests.length }}</div>
              </v-col>
            </v-row>
          </v-card-text>

          <v-card-actions>
            <v-btn color="primary" prepend-icon="mdi-pencil" @click="showEditDialog = true">
              Edit Team
            </v-btn>
            <v-btn color="error" variant="outlined" prepend-icon="mdi-delete" @click="confirmDeleteTeam">
              Delete Team
            </v-btn>
          </v-card-actions>
        </v-card>

        <v-skeleton-loader v-else type="card" />
      </v-col>

      <!-- Pending Requests Card -->
      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-account-clock</v-icon>
            Join Requests
            <v-chip v-if="teamStore.pendingJoinRequests.length" size="small" color="warning" class="ml-2">
              {{ teamStore.pendingJoinRequests.length }}
            </v-chip>
          </v-card-title>

          <v-card-text v-if="teamStore.pendingJoinRequests.length">
            <v-list density="compact">
              <v-list-item
                v-for="request in teamStore.pendingJoinRequests"
                :key="request.id"
              >
                <template #prepend>
                  <v-avatar size="32">
                    <v-icon>mdi-account</v-icon>
                  </v-avatar>
                </template>
                <v-list-item-title>{{ request.user?.full_name || request.user?.username }}</v-list-item-title>
                <v-list-item-subtitle>{{ request.position || 'No position' }}</v-list-item-subtitle>
                <template #append>
                  <v-btn icon="mdi-check" color="success" size="small" @click="acceptRequest(request)" />
                  <v-btn icon="mdi-close" color="error" size="small" @click="rejectRequest(request)" />
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>

          <v-card-text v-else class="text-center text-medium-emphasis">
            No pending requests
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Team Roster -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-account-group</v-icon>
            Team Roster
          </v-card-title>

          <v-data-table
            :headers="rosterHeaders"
            :items="teamStore.teamMembers"
            :loading="teamStore.loading"
          >
            <!-- Player Name -->
            <template #item.user="{ item }">
              <div class="d-flex align-center">
                <v-avatar size="32" class="mr-2">
                  <v-icon>mdi-account</v-icon>
                </v-avatar>
                {{ item.user?.full_name || item.user?.username }}
              </div>
            </template>

            <!-- Role -->
            <template #item.role="{ item }">
              <v-chip :color="item.role === 'CAPTAIN' ? 'warning' : 'default'" size="small">
                {{ item.role }}
              </v-chip>
            </template>

            <!-- Position -->
            <template #item.position="{ item }">
              {{ item.position || '-' }}
            </template>

            <!-- Jersey Number -->
            <template #item.jersey_number="{ item }">
              <v-chip v-if="item.jersey_number" size="small">
                #{{ item.jersey_number }}
              </v-chip>
              <span v-else>-</span>
            </template>

            <!-- Actions -->
            <template #item.actions="{ item }">
              <div v-if="item.role !== 'CAPTAIN'">
                <v-btn icon="mdi-pencil" size="small" variant="text" @click="editMember(item)" />
                <v-btn icon="mdi-account-star" size="small" variant="text" color="warning" @click="promoteMember(item)" />
                <v-btn icon="mdi-account-remove" size="small" variant="text" color="error" @click="removeMember(item)" />
              </div>
              <v-chip v-else size="small" color="warning">Captain</v-chip>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Edit Team Dialog -->
    <v-dialog v-model="showEditDialog" max-width="600">
      <v-card>
        <v-card-title>Edit Team</v-card-title>
        <v-card-text>
          <v-form ref="editForm">
            <v-text-field v-model="editedTeam.name" label="Team Name" :rules="[v => !!v || 'Required']" />
            <v-text-field v-model="editedTeam.city" label="City" />
            <v-textarea v-model="editedTeam.description" label="Description" rows="3" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showEditDialog = false">Cancel</v-btn>
          <v-btn color="primary" :loading="teamStore.loading" @click="saveTeamChanges">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Edit Member Dialog -->
    <v-dialog v-model="showMemberEditDialog" max-width="400">
      <v-card>
        <v-card-title>Edit Member</v-card-title>
        <v-card-text>
          <v-form>
            <v-select v-model="editedMember.position" label="Position" :items="positions" clearable />
            <v-text-field v-model.number="editedMember.jersey_number" label="Jersey Number" type="number" :min="1" :max="99" />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showMemberEditDialog = false">Cancel</v-btn>
          <v-btn color="primary" :loading="teamStore.loading" @click="saveMemberChanges">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-error">Delete Team?</v-card-title>
        <v-card-text>
          This action cannot be undone. All team data, members, and history will be permanently deleted.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDeleteDialog = false">Cancel</v-btn>
          <v-btn color="error" :loading="teamStore.loading" @click="deleteTeam">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Review Request Dialog -->
    <v-dialog v-model="showReviewDialog" max-width="500">
      <v-card v-if="selectedRequest">
        <v-card-title>Review Join Request</v-card-title>
        <v-card-text>
          <div class="mb-4">
            <strong>{{ selectedRequest.user?.full_name || selectedRequest.user?.username }}</strong>
            wants to join your team.
          </div>

          <div v-if="selectedRequest.message" class="mb-4">
            <div class="text-caption">Message:</div>
            <v-card variant="outlined" class="pa-2">
              {{ selectedRequest.message }}
            </v-card>
          </div>

          <div v-if="selectedRequest.position" class="mb-4">
            Preferred position: <v-chip size="small">{{ selectedRequest.position }}</v-chip>
          </div>

          <v-textarea
            v-model="reviewMessage"
            label="Response message (optional)"
            rows="2"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showReviewDialog = false">Cancel</v-btn>
          <v-btn color="error" @click="submitReview('REJECTED')">Reject</v-btn>
          <v-btn color="success" @click="submitReview('ACCEPTED')">Accept</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="showSnackbar" :color="snackbarColor" :timeout="3000">
      {{ snackbarMessage }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useTeamStore } from '@/stores/team'

const props = defineProps<{
  teamId: number
}>()

const teamStore = useTeamStore()

// Computed
const team = computed(() => teamStore.currentTeam)

// State
const showEditDialog = ref(false)
const showMemberEditDialog = ref(false)
const showDeleteDialog = ref(false)
const showReviewDialog = ref(false)

const editedTeam = ref({
  name: '',
  city: '',
  description: '',
})

const editedMember = ref({
  user_id: 0,
  position: null as string | null,
  jersey_number: null as number | null,
})

const selectedRequest = ref<any>(null)
const reviewMessage = ref('')

const showSnackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

const positions = ['GK', 'DEF', 'MID', 'FWD']

const rosterHeaders = [
  { title: 'Player', key: 'user', align: 'start' as const },
  { title: 'Role', key: 'role', align: 'center' as const },
  { title: 'Position', key: 'position', align: 'center' as const },
  { title: 'Jersey', key: 'jersey_number', align: 'center' as const },
  { title: 'Actions', key: 'actions', align: 'center' as const, sortable: false },
]

// Methods
const getRatingColor = (rating: number) => {
  if (rating >= 1500) return 'success'
  if (rating >= 1200) return 'primary'
  if (rating >= 900) return 'warning'
  return 'error'
}

const loadTeamData = async () => {
  try {
    await teamStore.fetchTeamById(props.teamId)
    await teamStore.fetchTeamMembers(props.teamId)
    await teamStore.fetchPendingJoinRequests(props.teamId)
  } catch (error) {
    console.error('Error loading team data:', error)
  }
}

const saveTeamChanges = async () => {
  try {
    await teamStore.updateTeam(props.teamId, editedTeam.value)
    showEditDialog.value = false
    showMessage('Team updated successfully')
  } catch (error) {
    console.error('Error updating team:', error)
  }
}

const editMember = (member: any) => {
  editedMember.value = {
    user_id: member.user_id,
    position: member.position,
    jersey_number: member.jersey_number,
  }
  showMemberEditDialog.value = true
}

const saveMemberChanges = async () => {
  try {
    await teamStore.updateMember(props.teamId, editedMember.value.user_id, {
      position: editedMember.value.position,
      jersey_number: editedMember.value.jersey_number,
    })
    showMemberEditDialog.value = false
    showMessage('Member updated successfully')
  } catch (error) {
    console.error('Error updating member:', error)
  }
}

const promoteMember = async (member: any) => {
  if (confirm(`Promote ${member.user?.username} to captain? You will become a regular player.`)) {
    try {
      await teamStore.promoteToCaptain(props.teamId, member.user_id)
      showMessage('Captain transferred successfully')
    } catch (error) {
      console.error('Error promoting member:', error)
    }
  }
}

const removeMember = async (member: any) => {
  if (confirm(`Remove ${member.user?.username} from the team?`)) {
    try {
      await teamStore.removeMember(props.teamId, member.user_id)
      showMessage('Member removed successfully')
    } catch (error) {
      console.error('Error removing member:', error)
    }
  }
}

const confirmDeleteTeam = () => {
  showDeleteDialog.value = true
}

const deleteTeam = async () => {
  try {
    await teamStore.deleteTeam(props.teamId)
    showDeleteDialog.value = false
    // Navigate away or show success
  } catch (error) {
    console.error('Error deleting team:', error)
  }
}

const acceptRequest = (request: any) => {
  selectedRequest.value = request
  reviewMessage.value = ''
  showReviewDialog.value = true
}

const rejectRequest = (request: any) => {
  selectedRequest.value = request
  reviewMessage.value = ''
  showReviewDialog.value = true
}

const submitReview = async (status: 'ACCEPTED' | 'REJECTED') => {
  try {
    await teamStore.reviewJoinRequest(selectedRequest.value.id, status, reviewMessage.value)
    showReviewDialog.value = false
    showMessage(status === 'ACCEPTED' ? 'Player accepted to team' : 'Request rejected')
  } catch (error) {
    console.error('Error reviewing request:', error)
  }
}

const showMessage = (message: string, color = 'success') => {
  snackbarMessage.value = message
  snackbarColor.value = color
  showSnackbar.value = true
}

// Watch for team changes to update edit form
watch(team, (newTeam) => {
  if (newTeam) {
    editedTeam.value = {
      name: newTeam.name,
      city: newTeam.city || '',
      description: newTeam.description || '',
    }
  }
}, { immediate: true })

// Load data on mount
onMounted(() => {
  loadTeamData()
})
</script>
