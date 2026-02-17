<template>
  <v-container class="py-8">
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <h1 :class="$vuetify.display.xs ? 'text-h4' : 'text-h3'" class="font-weight-bold mb-2">
          <v-icon icon="mdi-target" :size="$vuetify.display.xs ? 'default' : 'large'" class="mr-2" />
          Find Opponent
        </h1>
        <p class="text-body-1 text-medium-emphasis">
          Smart matchmaking algorithm finds the best opponents for your team
        </p>
      </v-col>
    </v-row>

    <!-- Not a captain warning -->
    <v-row v-if="!isCaptain">
      <v-col cols="12">
        <v-alert type="info" variant="tonal">
          Only team captains can use the matchmaking system.
          Register as a captain and create a team to find opponents.
        </v-alert>
      </v-col>
    </v-row>

    <!-- No-location warning (captain has a team but no coordinates set) -->
    <v-row v-if="isCaptain && myTeamId && !hasCoordinates">
      <v-col cols="12">
        <v-alert type="warning" variant="tonal" prepend-icon="mdi-map-marker-off" class="mb-2">
          <strong>Team location not set.</strong>
          The proximity component of matchmaking cannot rank teams by distance.
          <NuxtLink :to="`/teams/${myTeamId}`" class="ml-1">Edit your team</NuxtLink>
          to geocode your city and activate distance-based matching.
        </v-alert>
      </v-col>
    </v-row>

    <!-- Matchmaking Controls -->
    <v-row v-if="isCaptain">
      <v-col cols="12" md="8">
        <v-card elevation="2" class="pa-4">
          <v-card-title class="px-0">
            <v-icon class="mr-2">mdi-tune</v-icon>
            Algorithm Parameters
          </v-card-title>
          <v-card-text class="px-0">
            <v-row dense>
              <v-col cols="12" sm="6">
                <v-slider
                  v-model="config_weights.w_elo"
                  label="ELO Weight"
                  :min="0" :max="1" :step="0.05"
                  thumb-label
                  color="primary"
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-slider
                  v-model="config_weights.w_geo"
                  label="Location Weight"
                  :min="0" :max="1" :step="0.05"
                  thumb-label
                  color="secondary"
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-slider
                  v-model="config_weights.w_avail"
                  label="Schedule Weight"
                  :min="0" :max="1" :step="0.05"
                  thumb-label
                  color="info"
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model.number="config_weights.elo_range"
                  label="Max ELO Difference"
                  type="number"
                  :min="50" :max="2000"
                  variant="outlined"
                  density="compact"
                  hide-details
                />
              </v-col>
            </v-row>
          </v-card-text>
          <v-card-actions class="px-0">
            <v-btn
              color="primary"
              size="large"
              :loading="loading"
              prepend-icon="mdi-magnify"
              @click="findOpponents"
            >
              Find Opponents
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- Team Availability -->
      <v-col cols="12" md="4">
        <v-card elevation="2" class="pa-4">
          <v-card-title class="px-0">
            <v-icon class="mr-2">mdi-calendar-clock</v-icon>
            Your Availability
          </v-card-title>
          <v-card-text class="px-0">
            <div v-if="availabilitySlots.length === 0" class="text-medium-emphasis text-center pa-4">
              No availability set. Add time slots to improve matchmaking.
            </div>
            <v-chip
              v-for="(slot, i) in availabilitySlots"
              :key="i"
              size="small"
              variant="outlined"
              class="ma-1"
              closable
              @click:close="removeSlot(i)"
            >
              {{ dayNames[slot.day_of_week] }} {{ slot.start_time }}-{{ slot.end_time }}
            </v-chip>
          </v-card-text>
          <v-card-actions class="px-0">
            <v-btn variant="outlined" size="small" prepend-icon="mdi-plus" @click="showAvailDialog = true">
              Add Slot
            </v-btn>
            <v-btn
              v-if="availabilitySlots.length > 0"
              variant="text"
              size="small"
              color="primary"
              :loading="savingAvailability"
              @click="saveAvailability"
            >
              Save
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Error -->
    <v-row v-if="error">
      <v-col cols="12">
        <v-alert type="error" closable @click:close="error = null">{{ error }}</v-alert>
      </v-col>
    </v-row>

    <!-- Results -->
    <v-row v-if="results">
      <v-col cols="12">
        <h2 class="text-h5 font-weight-bold mb-4">
          Suggestions
          <v-chip size="small" class="ml-2">{{ results.suggestions.length }} / {{ results.total_candidates }} teams</v-chip>
        </h2>
      </v-col>

      <v-col v-if="results.suggestions.length === 0" cols="12">
        <v-alert type="info" variant="tonal">
          No suitable opponents found. Try widening the ELO range or adding availability slots.
        </v-alert>
      </v-col>

      <v-col
        v-for="suggestion in results.suggestions"
        :key="suggestion.team_id"
        cols="12"
        md="6"
      >
        <v-card elevation="2" hover>
          <v-card-text class="pa-4">
            <div class="d-flex justify-space-between align-center mb-3">
              <div>
                <h3 class="text-subtitle-1 font-weight-bold">{{ suggestion.team_name }}</h3>
                <div class="d-flex align-center flex-wrap ga-1 mt-1">
                  <v-chip v-if="suggestion.city" size="small" variant="outlined">
                    <v-icon start size="small">mdi-map-marker</v-icon>
                    {{ suggestion.city }}
                  </v-chip>
                  <v-chip
                    v-if="suggestion.distance_km !== null && suggestion.distance_km !== undefined"
                    size="small"
                    variant="tonal"
                    color="info"
                  >
                    <v-icon start size="small">mdi-map-marker-distance</v-icon>
                    {{ suggestion.distance_km }} km
                  </v-chip>
                </div>
              </div>
              <div class="text-right">
                <div class="text-h4 font-weight-bold text-primary">{{ suggestion.total_score }}</div>
                <div class="text-caption">Match Score</div>
              </div>
            </div>

            <!-- Score breakdown -->
            <v-row dense>
              <v-col cols="4">
                <div class="text-center">
                  <v-chip :color="getRatingColor(suggestion.rating)" variant="flat" size="small">
                    {{ suggestion.rating }}
                  </v-chip>
                  <div class="text-caption mt-1">ELO (diff: {{ suggestion.rating_difference }})</div>
                </div>
              </v-col>
              <v-col cols="4">
                <div class="text-center">
                  <v-chip size="small" variant="outlined">{{ suggestion.member_count }}</v-chip>
                  <div class="text-caption mt-1">Members</div>
                </div>
              </v-col>
              <v-col cols="4">
                <div class="text-center">
                  <v-chip size="small" variant="outlined" color="info">{{ suggestion.overlapping_slots }}</v-chip>
                  <div class="text-caption mt-1">Schedule Overlaps</div>
                </div>
              </v-col>
            </v-row>

            <!-- Factor bars -->
            <div class="mt-3">
              <div v-for="factor in getFactors(suggestion.breakdown)" :key="factor.label" class="mb-1">
                <div class="d-flex justify-space-between text-caption">
                  <span>{{ factor.label }}</span>
                  <span>{{ (factor.value * 100).toFixed(0) }}%</span>
                </div>
                <v-progress-linear
                  :model-value="factor.value * 100"
                  :color="factor.color"
                  height="4"
                  rounded
                />
              </div>
            </div>
          </v-card-text>

          <v-card-actions>
            <v-spacer />
            <v-btn
              color="primary"
              variant="flat"
              size="small"
              prepend-icon="mdi-sword-cross"
              @click="challengeTeam(suggestion.team_id)"
            >
              Challenge
            </v-btn>
            <v-btn
              variant="text"
              size="small"
              @click="navigateTo(`/teams/${suggestion.team_id}`)"
            >
              View Team
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Add Availability Dialog -->
    <v-dialog v-model="showAvailDialog" max-width="400">
      <v-card>
        <v-card-title>Add Time Slot</v-card-title>
        <v-card-text>
          <v-select
            v-model="newSlot.day_of_week"
            :items="dayOptions"
            item-title="title"
            item-value="value"
            label="Day of Week"
            variant="outlined"
            class="mb-3"
          />
          <v-text-field
            v-model="newSlot.start_time"
            label="Start Time"
            type="time"
            variant="outlined"
            class="mb-3"
          />
          <v-text-field
            v-model="newSlot.end_time"
            label="End Time"
            type="time"
            variant="outlined"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showAvailDialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="addSlot">Add</v-btn>
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

definePageMeta({
  middleware: ['captain'],
})

const { isCaptain } = useAuth()
const runtimeConfig = useRuntimeConfig()
const apiBase = computed(() => runtimeConfig.public.apiBaseUrl || 'http://localhost:8000/api/v1')

const getAuthHeaders = () => {
  const token = useCookie('auth_token')
  return token.value ? { Authorization: `Bearer ${token.value}` } : {}
}

// State
const loading = ref(false)
const savingAvailability = ref(false)
const error = ref<string | null>(null)
const results = ref<any>(null)
const showAvailDialog = ref(false)
const showSnackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

const config_weights = ref({
  w_elo: 0.35,
  w_geo: 0.25,
  w_avail: 0.20,
  w_recency: 0.10,
  w_activity: 0.10,
  elo_range: 500,
  max_results: 10,
})

const availabilitySlots = ref<any[]>([])
const newSlot = ref({ day_of_week: 0, start_time: '18:00', end_time: '20:00' })

const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const dayOptions = dayNames.map((d, i) => ({ title: d, value: i }))

const myTeamId = ref<number | null>(null)
const myTeam = ref<any>(null)

const hasCoordinates = computed(
  () => myTeam.value?.latitude !== null && myTeam.value?.latitude !== undefined,
)

// Find my team
const findMyTeam = async () => {
  try {
    const data = await $fetch<any>(`${apiBase.value}/teams/my/team`, { headers: getAuthHeaders() })
    myTeam.value = data
    myTeamId.value = data.id
    // Load existing availability
    try {
      const avail = await $fetch<any>(`${apiBase.value}/matchmaking/team/${data.id}/availability`)
      availabilitySlots.value = (avail.slots || []).map((s: any) => ({
        day_of_week: s.day_of_week,
        start_time: s.start_time,
        end_time: s.end_time,
        location_preference: s.location_preference,
      }))
    } catch { /* no availability yet */ }
  } catch { /* no team */ }
}

// Matchmaking
const findOpponents = async () => {
  loading.value = true
  error.value = null
  results.value = null
  try {
    const data = await $fetch<any>(`${apiBase.value}/matchmaking/find-opponent`, {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: config_weights.value,
    })
    results.value = data
  } catch (err: any) {
    error.value = err.data?.detail || 'Failed to find opponents'
  } finally {
    loading.value = false
  }
}

// Availability
const addSlot = () => {
  availabilitySlots.value.push({ ...newSlot.value })
  showAvailDialog.value = false
  newSlot.value = { day_of_week: 0, start_time: '18:00', end_time: '20:00' }
}

const removeSlot = (index: number) => {
  availabilitySlots.value.splice(index, 1)
}

const saveAvailability = async () => {
  if (!myTeamId.value) return
  savingAvailability.value = true
  try {
    await $fetch(`${apiBase.value}/matchmaking/team/${myTeamId.value}/availability`, {
      method: 'PUT',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: { slots: availabilitySlots.value },
    })
    showMsg('Availability saved!', 'success')
  } catch (err: any) {
    showMsg(err.data?.detail || 'Failed to save availability', 'error')
  } finally {
    savingAvailability.value = false
  }
}

const challengeTeam = async (opponentId: number) => {
  try {
    await $fetch(`${apiBase.value}/challenges/`, {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: { opponent_id: opponentId },
    })
    showMsg('Challenge sent!', 'success')
  } catch (err: any) {
    showMsg(err.data?.detail || 'Failed to send challenge', 'error')
  }
}

// Helpers
const getRatingColor = (rating: number) => {
  if (!rating) return 'grey'
  if (rating >= 1500) return 'success'
  if (rating >= 1200) return 'primary'
  if (rating >= 900) return 'warning'
  return 'error'
}

const getFactors = (breakdown: any) => [
  { label: 'ELO Similarity', value: breakdown.elo_similarity, color: 'primary' },
  { label: 'Location', value: breakdown.geo_proximity, color: 'secondary' },
  { label: 'Schedule', value: breakdown.availability_overlap, color: 'info' },
  { label: 'Activity', value: breakdown.activity_bonus, color: 'success' },
]

const showMsg = (message: string, color: string) => {
  snackbarMessage.value = message
  snackbarColor.value = color
  showSnackbar.value = true
}

onMounted(() => {
  if (isCaptain.value) findMyTeam()
})
</script>
