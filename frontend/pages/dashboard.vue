<template>
  <v-container class="py-8">
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <h1 :class="$vuetify.display.xs ? 'text-h4' : 'text-h3'" class="font-weight-bold mb-2">
          <v-icon icon="mdi-view-dashboard" :size="$vuetify.display.xs ? 'default' : 'large'" class="mr-2" />
          Dashboard
        </h1>
        <p class="text-body-1 text-medium-emphasis">
          Welcome back, {{ user?.full_name || user?.username }}
        </p>
      </v-col>
    </v-row>

    <!-- Loading -->
    <v-row v-if="loading" justify="center" class="pa-12">
      <v-progress-circular indeterminate color="primary" size="48" />
    </v-row>

    <!-- No Team State -->
    <v-row v-else-if="!myTeam">
      <v-col cols="12" md="8">
        <v-card class="pa-8 text-center" elevation="2">
          <v-icon icon="mdi-shield-off" size="64" color="medium-emphasis" class="mb-4" />
          <h2 class="text-h5 mb-2">You're not in a team yet</h2>
          <p class="text-body-1 text-medium-emphasis mb-6">
            Join a team or create your own to unlock the full platform
          </p>
          <div class="d-flex justify-center ga-3">
            <v-btn color="primary" size="large" to="/teams" prepend-icon="mdi-magnify">
              Browse Teams
            </v-btn>
            <v-btn v-if="isCaptain" color="success" size="large" variant="outlined" to="/teams" prepend-icon="mdi-plus">
              Create Team
            </v-btn>
          </div>
        </v-card>
      </v-col>

      <!-- Recent Notifications (even without a team) -->
      <v-col cols="12" md="4">
        <NotificationsList :notifications="notifications" :loading="notifLoading" />
      </v-col>
    </v-row>

    <!-- Main Dashboard (has team) -->
    <template v-else>
      <!-- Row 1: Team Card + Quick Stats -->
      <v-row>
        <!-- My Team Card -->
        <v-col cols="12" md="4">
          <v-card elevation="2" class="h-100">
            <v-card-text class="text-center pa-6">
              <v-avatar size="72" color="primary" class="mb-3">
                <span class="text-h4 font-weight-bold">{{ teamInitials }}</span>
              </v-avatar>
              <h2 class="text-h5 font-weight-bold mb-1">{{ myTeam.name }}</h2>
              <v-chip v-if="myTeam.city" size="small" variant="outlined" class="mb-3">
                <v-icon start size="small">mdi-map-marker</v-icon>
                {{ myTeam.city }}
              </v-chip>

              <v-divider class="my-3" />

              <v-row dense>
                <v-col cols="4">
                  <div class="text-h5 font-weight-bold text-primary">{{ myTeam.rating || 1000 }}</div>
                  <div class="text-caption">ELO</div>
                </v-col>
                <v-col cols="4">
                  <div class="text-h5 font-weight-bold">{{ myTeam.member_count || 0 }}</div>
                  <div class="text-caption">Members</div>
                </v-col>
                <v-col cols="4">
                  <div class="text-h5 font-weight-bold text-success">{{ teamStats.wins }}</div>
                  <div class="text-caption">Wins</div>
                </v-col>
              </v-row>
            </v-card-text>
            <v-card-actions class="justify-center">
              <v-btn variant="text" color="primary" :to="`/teams/${myTeam.id}`" prepend-icon="mdi-eye">
                View Team
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>

        <!-- ELO Rating Chart -->
        <v-col cols="12" md="8">
          <v-card elevation="2" class="h-100">
            <v-card-title>
              <v-icon class="mr-2">mdi-chart-line</v-icon>
              ELO Rating History
            </v-card-title>
            <v-card-text>
              <div v-if="ratingHistory.length === 0" class="text-center text-medium-emphasis pa-8">
                <v-icon icon="mdi-chart-line-variant" size="48" class="mb-3" />
                <div>No rating history yet. Complete matches to see your progression.</div>
              </div>
              <div v-else style="height: 280px; position: relative;">
                <canvas ref="chartCanvas"></canvas>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Row 2: Upcoming Challenges + Recent Results -->
      <v-row class="mt-2">
        <!-- Upcoming / Pending Challenges -->
        <v-col cols="12" md="6">
          <v-card elevation="2">
            <v-card-title>
              <v-icon class="mr-2">mdi-sword-cross</v-icon>
              Active Challenges
              <v-chip v-if="activeChallenges.length" size="small" color="primary" class="ml-2">
                {{ activeChallenges.length }}
              </v-chip>
            </v-card-title>
            <v-card-text>
              <div v-if="activeChallenges.length === 0" class="text-center text-medium-emphasis pa-6">
                No active challenges
              </div>
              <v-list v-else density="compact">
                <v-list-item
                  v-for="ch in activeChallenges"
                  :key="ch.id"
                  :to="`/challenges`"
                  class="mb-1"
                >
                  <template #prepend>
                    <v-chip
                      :color="ch.status === 'pending' ? 'warning' : 'success'"
                      size="x-small"
                      variant="flat"
                      class="mr-2"
                    >
                      {{ ch.status }}
                    </v-chip>
                  </template>
                  <v-list-item-title>
                    {{ ch.challenger?.name }} vs {{ ch.opponent?.name }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    {{ ch.match_date ? new Date(ch.match_date).toLocaleDateString() : 'TBD' }}
                    {{ ch.location ? `@ ${ch.location}` : '' }}
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
            <v-card-actions>
              <v-btn variant="text" color="primary" to="/challenges" prepend-icon="mdi-arrow-right">
                All Challenges
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>

        <!-- Recent Match Results -->
        <v-col cols="12" md="6">
          <v-card elevation="2">
            <v-card-title>
              <v-icon class="mr-2">mdi-trophy</v-icon>
              Recent Results
            </v-card-title>
            <v-card-text>
              <div v-if="recentResults.length === 0" class="text-center text-medium-emphasis pa-6">
                No completed matches yet
              </div>
              <v-list v-else density="compact">
                <v-list-item v-for="r in recentResults" :key="r.id" class="mb-1">
                  <template #prepend>
                    <v-chip
                      :color="getResultColor(r)"
                      size="x-small"
                      variant="flat"
                      class="mr-2"
                    >
                      {{ getResultLabel(r) }}
                    </v-chip>
                  </template>
                  <v-list-item-title>
                    {{ r.challenger?.name }}
                    <strong>{{ r.challenger_score }} - {{ r.opponent_score }}</strong>
                    {{ r.opponent?.name }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    {{ new Date(r.updated_at).toLocaleDateString() }}
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Row 3: Notifications -->
      <v-row class="mt-2">
        <v-col cols="12">
          <NotificationsList :notifications="notifications" :loading="notifLoading" />
        </v-col>
      </v-row>
    </template>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

definePageMeta({
  middleware: ['auth'],
})

const { user, isCaptain } = useAuth()
const config = useRuntimeConfig()
const apiBase = computed(() => config.public.apiBaseUrl || 'http://localhost:8000/api/v1')

const getAuthHeaders = () => {
  const token = useCookie('auth_token')
  return token.value ? { Authorization: `Bearer ${token.value}` } : {}
}

// State
const loading = ref(true)
const notifLoading = ref(true)
const myTeam = ref<any>(null)
const ratingHistory = ref<any[]>([])
const activeChallenges = ref<any[]>([])
const recentResults = ref<any[]>([])
const notifications = ref<any[]>([])
const chartCanvas = ref<HTMLCanvasElement | null>(null)
let chartInstance: Chart | null = null

const teamStats = computed(() => {
  let wins = 0
  for (const r of recentResults.value) {
    if (!myTeam.value) break
    const isChallenger = r.challenger_id === myTeam.value.id
    const myScore = isChallenger ? r.challenger_score : r.opponent_score
    const theirScore = isChallenger ? r.opponent_score : r.challenger_score
    if (myScore > theirScore) wins++
  }
  return { wins }
})

const teamInitials = computed(() => {
  if (!myTeam.value?.name) return '?'
  return myTeam.value.name
    .split(' ')
    .map((w: string) => w[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
})

// ── Data fetching ──

const fetchMyTeam = async () => {
  try {
    const data = await $fetch<any>(`${apiBase.value}/teams/my/team`, {
      headers: getAuthHeaders(),
    })
    myTeam.value = data
  } catch {
    myTeam.value = null
  }
}

const fetchRatingHistory = async () => {
  if (!myTeam.value) return
  try {
    const data = await $fetch<any[]>(`${apiBase.value}/ratings/team/${myTeam.value.id}/history`, {
      headers: getAuthHeaders(),
    })
    ratingHistory.value = data || []
  } catch {
    ratingHistory.value = []
  }
}

const fetchChallenges = async () => {
  if (!myTeam.value) return
  try {
    // Get active (pending + accepted)
    const pending = await $fetch<any>(`${apiBase.value}/challenges/`, {
      headers: getAuthHeaders(),
      params: { team_id: myTeam.value.id, status: 'pending', limit: 5 },
    })
    const accepted = await $fetch<any>(`${apiBase.value}/challenges/`, {
      headers: getAuthHeaders(),
      params: { team_id: myTeam.value.id, status: 'accepted', limit: 5 },
    })
    activeChallenges.value = [
      ...(pending.items || []),
      ...(accepted.items || []),
    ].slice(0, 5)

    // Get recent completed
    const completed = await $fetch<any>(`${apiBase.value}/challenges/`, {
      headers: getAuthHeaders(),
      params: { team_id: myTeam.value.id, status: 'completed', limit: 5 },
    })
    recentResults.value = completed.items || []
  } catch {
    activeChallenges.value = []
    recentResults.value = []
  }
}

const fetchNotifications = async () => {
  notifLoading.value = true
  try {
    const data = await $fetch<any>(`${apiBase.value}/notifications/`, {
      headers: getAuthHeaders(),
      params: { limit: 10 },
    })
    notifications.value = data.items || []
  } catch {
    notifications.value = []
  } finally {
    notifLoading.value = false
  }
}

// ── Chart rendering ──

const renderChart = async () => {
  if (!ratingHistory.value.length || !chartCanvas.value) return

  await nextTick()

  if (chartInstance) {
    chartInstance.destroy()
  }

  const labels = ratingHistory.value.map((r: any) =>
    new Date(r.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  )
  const ratings = ratingHistory.value.map((r: any) => r.new_rating)

  // Prepend the initial rating (old_rating of first entry)
  if (ratingHistory.value.length > 0) {
    labels.unshift('Start')
    ratings.unshift(ratingHistory.value[0].old_rating)
  }

  chartInstance = new Chart(chartCanvas.value, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'ELO Rating',
          data: ratings,
          borderColor: '#1976D2',
          backgroundColor: 'rgba(25, 118, 210, 0.1)',
          fill: true,
          tension: 0.3,
          pointRadius: 4,
          pointHoverRadius: 6,
          pointBackgroundColor: '#1976D2',
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `Rating: ${ctx.parsed.y}`,
          },
        },
      },
      scales: {
        y: {
          title: { display: true, text: 'ELO Rating' },
          beginAtZero: false,
        },
        x: {
          title: { display: true, text: 'Match Date' },
        },
      },
    },
  })
}

// ── Helpers ──

const getResultColor = (challenge: any) => {
  if (!myTeam.value) return 'grey'
  const isChallenger = challenge.challenger_id === myTeam.value.id
  const myScore = isChallenger ? challenge.challenger_score : challenge.opponent_score
  const theirScore = isChallenger ? challenge.opponent_score : challenge.challenger_score
  if (myScore > theirScore) return 'success'
  if (myScore < theirScore) return 'error'
  return 'warning'
}

const getResultLabel = (challenge: any) => {
  if (!myTeam.value) return '?'
  const isChallenger = challenge.challenger_id === myTeam.value.id
  const myScore = isChallenger ? challenge.challenger_score : challenge.opponent_score
  const theirScore = isChallenger ? challenge.opponent_score : challenge.challenger_score
  if (myScore > theirScore) return 'WIN'
  if (myScore < theirScore) return 'LOSS'
  return 'DRAW'
}

// ── Lifecycle ──

onMounted(async () => {
  loading.value = true
  await fetchMyTeam()
  await Promise.all([fetchRatingHistory(), fetchChallenges(), fetchNotifications()])
  loading.value = false

  // Render chart after data loads
  await nextTick()
  renderChart()
})

// Re-render chart when data changes
watch(ratingHistory, () => {
  nextTick(() => renderChart())
})
</script>
