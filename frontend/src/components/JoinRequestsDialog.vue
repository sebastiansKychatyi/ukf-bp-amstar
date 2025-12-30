<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="900"
    scrollable
  >
    <v-card>
      <!-- Header -->
      <v-card-title class="pa-6">
        <div class="d-flex align-center">
          <v-icon size="32" class="mr-3">mdi-account-multiple-plus</v-icon>
          <div>
            <div class="text-h5 font-weight-bold">Join Requests</div>
            <div class="text-subtitle-2 text-medium-emphasis">
              Review players who want to join your team
            </div>
          </div>
        </div>
        <v-btn
          icon="mdi-close"
          variant="text"
          position="absolute"
          location="top right"
          class="ma-2"
          @click="$emit('update:modelValue', false)"
        />
      </v-card-title>

      <v-divider />

      <!-- Loading State -->
      <v-card-text v-if="loading" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" />
        <p class="text-h6 mt-4">Loading join requests...</p>
      </v-card-text>

      <!-- Content -->
      <v-card-text v-else class="pa-0">
        <!-- Empty State -->
        <div v-if="requests.length === 0" class="text-center py-12">
          <v-icon size="64" color="grey-lighten-1">
            mdi-inbox
          </v-icon>
          <p class="text-h6 mt-4">No pending join requests</p>
          <p class="text-medium-emphasis">
            New requests will appear here for you to review
          </p>
        </div>

        <!-- Requests List -->
        <v-list v-else lines="three">
          <template v-for="(request, index) in requests" :key="request.id">
            <v-list-item class="pa-4">
              <template #prepend>
                <v-avatar
                  :color="getPositionColor(request.player.position)"
                  size="56"
                >
                  <v-icon color="white" size="32">
                    {{ getPositionIcon(request.player.position) }}
                  </v-icon>
                </v-avatar>
              </template>

              <v-list-item-title class="mb-2">
                <div class="d-flex align-center">
                  <span class="text-h6 font-weight-bold">
                    {{ request.player.first_name }} {{ request.player.last_name }}
                  </span>
                  <v-chip
                    :color="getPositionColor(request.player.position)"
                    size="small"
                    variant="flat"
                    class="ml-3"
                  >
                    {{ request.player.position }}
                  </v-chip>
                  <v-chip
                    :color="getRatingColor(request.player.skill_rating)"
                    size="small"
                    variant="flat"
                    class="ml-2"
                  >
                    {{ request.player.skill_rating.toFixed(1) }} Rating
                  </v-chip>
                </div>
              </v-list-item-title>

              <v-list-item-subtitle class="mb-3">
                <div class="d-flex align-center ga-4 mb-2">
                  <span>
                    <v-icon size="16">mdi-soccer</v-icon>
                    {{ request.player.total_goals }} goals
                  </span>
                  <span>
                    <v-icon size="16">mdi-hand-pointing-right</v-icon>
                    {{ request.player.total_assists }} assists
                  </span>
                  <span>
                    <v-icon size="16">mdi-calendar</v-icon>
                    {{ request.player.total_matches_played }} matches
                  </span>
                </div>

                <!-- Player Message -->
                <v-card
                  v-if="request.message"
                  variant="tonal"
                  class="mt-2"
                >
                  <v-card-text class="pa-3">
                    <div class="text-caption text-medium-emphasis mb-1">
                      Message:
                    </div>
                    <div class="text-body-2">{{ request.message }}</div>
                  </v-card-text>
                </v-card>
              </v-list-item-subtitle>

              <div class="text-caption text-medium-emphasis">
                Requested {{ formatDate(request.created_at) }}
              </div>

              <template #append>
                <div class="d-flex flex-column ga-2">
                  <v-btn
                    color="success"
                    prepend-icon="mdi-check"
                    :loading="processingRequest === request.id"
                    @click="handleApprove(request)"
                  >
                    Approve
                  </v-btn>
                  <v-btn
                    color="error"
                    variant="tonal"
                    prepend-icon="mdi-close"
                    :loading="processingRequest === request.id"
                    @click="showRejectDialog(request)"
                  >
                    Reject
                  </v-btn>
                </div>
              </template>
            </v-list-item>

            <v-divider v-if="index < requests.length - 1" />
          </template>
        </v-list>
      </v-card-text>

      <v-divider />

      <!-- Footer -->
      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn @click="$emit('update:modelValue', false)">Close</v-btn>
      </v-card-actions>
    </v-card>

    <!-- Reject Confirmation Dialog -->
    <v-dialog v-model="showRejectConfirm" max-width="500">
      <v-card>
        <v-card-title class="pa-6">
          <v-icon color="error" class="mr-2">mdi-alert-circle</v-icon>
          Reject Join Request
        </v-card-title>

        <v-card-text class="pa-6">
          <p class="mb-4">
            Are you sure you want to reject
            <strong>{{ selectedRequest?.player.first_name }} {{ selectedRequest?.player.last_name }}</strong>'s
            request to join the team?
          </p>

          <v-textarea
            v-model="rejectMessage"
            label="Optional message to player"
            placeholder="Let them know why or encourage them to apply again..."
            rows="3"
            variant="outlined"
          />
        </v-card-text>

        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn @click="showRejectConfirm = false">Cancel</v-btn>
          <v-btn
            color="error"
            :loading="processingRequest !== null"
            @click="handleReject"
          >
            Reject Request
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useTeamStore } from '@/stores/team'

const props = defineProps({
  modelValue: Boolean,
  teamId: String,
})

const emit = defineEmits(['update:modelValue', 'request-reviewed'])

const teamStore = useTeamStore()

// State
const loading = ref(false)
const requests = ref([])
const processingRequest = ref(null)
const showRejectConfirm = ref(false)
const selectedRequest = ref(null)
const rejectMessage = ref('')

// Watch for dialog open
watch(
  () => props.modelValue,
  async (isOpen) => {
    if (isOpen && props.teamId) {
      await loadRequests()
    }
  },
  { immediate: true }
)

// Methods
async function loadRequests() {
  loading.value = true
  try {
    await teamStore.fetchPendingJoinRequests(props.teamId)
    requests.value = teamStore.pendingJoinRequests
  } catch (error) {
    console.error('Failed to load join requests:', error)
  } finally {
    loading.value = false
  }
}

async function handleApprove(request) {
  processingRequest.value = request.id

  try {
    await teamStore.reviewJoinRequest(request.id, 'APPROVED')

    // Remove from local list
    requests.value = requests.value.filter(r => r.id !== request.id)

    // Emit event
    emit('request-reviewed')
  } catch (error) {
    console.error('Failed to approve request:', error)
  } finally {
    processingRequest.value = null
  }
}

function showRejectDialog(request) {
  selectedRequest.value = request
  showRejectConfirm.value = true
}

async function handleReject() {
  if (!selectedRequest.value) return

  processingRequest.value = selectedRequest.value.id

  try {
    await teamStore.reviewJoinRequest(
      selectedRequest.value.id,
      'REJECTED',
      rejectMessage.value
    )

    // Remove from local list
    requests.value = requests.value.filter(
      r => r.id !== selectedRequest.value.id
    )

    // Emit event
    emit('request-reviewed')

    // Close dialog
    showRejectConfirm.value = false
    rejectMessage.value = ''
    selectedRequest.value = null
  } catch (error) {
    console.error('Failed to reject request:', error)
  } finally {
    processingRequest.value = null
  }
}

function getPositionIcon(position) {
  const icons = {
    GOALKEEPER: 'mdi-shield-account',
    DEFENDER: 'mdi-shield',
    MIDFIELDER: 'mdi-run',
    FORWARD: 'mdi-soccer',
  }
  return icons[position] || 'mdi-account'
}

function getPositionColor(position) {
  const colors = {
    GOALKEEPER: '#F59E0B',
    DEFENDER: '#3B82F6',
    MIDFIELDER: '#10B981',
    FORWARD: '#EF4444',
  }
  return colors[position] || 'grey'
}

function getRatingColor(rating) {
  if (rating >= 80) return 'success'
  if (rating >= 60) return 'info'
  if (rating >= 40) return 'warning'
  return 'error'
}

function formatDate(dateString) {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}
</script>
