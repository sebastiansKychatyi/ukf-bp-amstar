<template>
  <v-container class="py-8">
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <h1 :class="$vuetify.display.xs ? 'text-h4' : 'text-h3'" class="font-weight-bold mb-1">
          <v-icon icon="mdi-view-dashboard" :size="$vuetify.display.xs ? 'default' : 'large'" class="mr-2" />
          Dashboard
        </h1>
        <p class="text-body-1 text-medium-emphasis">
          Welcome back, <strong>{{ user?.full_name || user?.username }}</strong>
        </p>
      </v-col>
    </v-row>

    <!-- Loading skeletons -->
    <template v-if="loading">
      <v-row class="mt-2">
        <v-col cols="12" md="4">
          <v-skeleton-loader type="card" height="260" />
        </v-col>
        <v-col cols="12" md="8">
          <v-skeleton-loader type="card" height="260" />
        </v-col>
      </v-row>
      <v-row class="mt-2">
        <v-col cols="12" md="6">
          <v-skeleton-loader type="list-item-three-line@4" />
        </v-col>
        <v-col cols="12" md="6">
          <v-skeleton-loader type="list-item-three-line@4" />
        </v-col>
      </v-row>
    </template>

    <!-- No Team State -->
    <v-row v-else-if="!myTeam" class="mt-4">
      <v-col cols="12" md="8">
        <v-card class="pa-8 text-center" elevation="0" border>
          <div class="empty-icon-wrap mb-5">
            <v-icon icon="mdi-shield-off" size="56" color="primary" />
          </div>
          <h2 class="text-h5 font-weight-bold mb-2">You're not in a team yet</h2>
          <p class="text-body-1 text-medium-emphasis mb-6">
            Join a team or create your own to unlock the full platform
          </p>
          <div class="d-flex justify-center ga-3">
            <v-btn color="primary" size="large" rounded="xl" to="/teams" prepend-icon="mdi-magnify">
              Browse Teams
            </v-btn>
            <v-btn v-if="isCaptain" color="success" size="large" variant="outlined" rounded="xl" to="/teams" prepend-icon="mdi-plus">
              Create Team
            </v-btn>
          </div>
        </v-card>
      </v-col>

      <!-- Notifications even without team -->
      <v-col cols="12" md="4">
        <NotificationsList :notifications="notifications" :loading="notifLoading" />
      </v-col>
    </v-row>

    <!-- Main Dashboard (has team) -->
    <template v-else>
      <!-- Row 1: Team Card + ELO Chart -->
      <v-row class="mt-2">
        <!-- My Team Card -->
        <v-col cols="12" md="4">
          <v-card elevation="0" border class="h-100 team-card overflow-hidden">
            <!-- Gradient header -->
            <div class="team-card-header d-flex flex-column align-center justify-center pa-6">
              <v-avatar size="72" color="white" class="mb-3 team-avatar">
                <span class="text-h4 font-weight-black text-primary">{{ teamInitials }}</span>
              </v-avatar>
              <h2 class="text-h6 font-weight-bold text-white mb-1">{{ myTeam.name }}</h2>
              <v-chip v-if="myTeam.city" size="small" color="white" variant="outlined" class="text-white">
                <v-icon start size="small">mdi-map-marker</v-icon>
                {{ myTeam.city }}
              </v-chip>
            </div>

            <!-- Stats row -->
            <v-card-text class="pa-0">
              <v-row dense class="ma-0">
                <v-col cols="4" class="stat-cell text-center py-4">
                  <div class="text-h5 font-weight-black text-primary">{{ myTeam.rating || 1000 }}</div>
                  <div class="text-caption text-medium-emphasis">ELO</div>
                </v-col>
                <v-divider vertical />
                <v-col cols="4" class="stat-cell text-center py-4">
                  <div class="text-h5 font-weight-black">{{ myTeam.member_count || 0 }}</div>
                  <div class="text-caption text-medium-emphasis">Members</div>
                </v-col>
                <v-divider vertical />
                <v-col cols="4" class="stat-cell text-center py-4">
                  <div class="text-h5 font-weight-black text-success">{{ teamStats.wins }}</div>
                  <div class="text-caption text-medium-emphasis">Wins</div>
                </v-col>
              </v-row>
            </v-card-text>

            <v-divider />

            <v-card-actions class="justify-center pa-3">
              <v-btn variant="tonal" color="primary" :to="`/teams/${myTeam.id}`" prepend-icon="mdi-eye" rounded="lg">
                View Team
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>

        <!-- ELO Rating Chart -->
        <v-col cols="12" md="8">
          <v-card elevation="0" border class="h-100">
            <v-card-title class="d-flex align-center pa-4 pb-2">
              <v-icon class="mr-2" color="primary">mdi-chart-line</v-icon>
              <span class="font-weight-bold">ELO Rating History</span>
            </v-card-title>
            <v-card-text>
              <div v-if="ratingHistory.length === 0" class="text-center text-medium-emphasis py-10">
                <div class="empty-icon-wrap mb-4 mx-auto">
                  <v-icon icon="mdi-chart-line-variant" size="40" color="primary" />
                </div>
                <div class="text-body-2">No rating history yet.</div>
                <div class="text-caption">Complete matches to see your progression.</div>
              </div>
              <div v-else style="height: 260px; position: relative;">
                <canvas ref="chartCanvas" />
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Row 2: Challenges + Results -->
      <v-row class="mt-2">
        <!-- Active Challenges -->
        <v-col cols="12" md="6">
          <v-card elevation="0" border>
            <v-card-title class="d-flex align-center pa-4 pb-2">
              <v-icon class="mr-2" color="warning">mdi-sword-cross</v-icon>
              <span class="font-weight-bold">Active Challenges</span>
              <v-chip v-if="activeChallenges.length" size="small" color="warning" class="ml-2">
                {{ activeChallenges.length }}
              </v-chip>
            </v-card-title>
            <v-card-text class="pt-0">
              <div v-if="activeChallenges.length === 0" class="text-center text-medium-emphasis py-6">
                <v-icon icon="mdi-check-circle-outline" size="36" color="success" class="mb-2 d-block" />
                <span class="text-body-2">No active challenges</span>
              </div>
              <v-list v-else density="compact">
                <v-list-item
                  v-for="ch in activeChallenges"
                  :key="ch.id"
                  :to="`/challenges`"
                  rounded="lg"
                  class="mb-1"
                >
                  <template #prepend>
                    <v-chip
                      :color="ch.status === 'pending' ? 'warning' : 'info'"
                      size="x-small"
                      variant="tonal"
                      class="mr-2"
                    >
                      {{ ch.status }}
                    </v-chip>
                  </template>
                  <v-list-item-title class="text-body-2 font-weight-medium">
                    {{ ch.challenger?.name }} vs {{ ch.opponent?.name }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    {{ ch.match_date ? new Date(ch.match_date).toLocaleDateString() : 'TBD' }}
                    {{ ch.location ? `@ ${ch.location}` : '' }}
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
            <v-card-actions class="pa-3 pt-0">
              <v-btn variant="text" color="primary" to="/challenges" prepend-icon="mdi-arrow-right" size="small">
                All Challenges
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>

        <!-- Recent Match Results -->
        <v-col cols="12" md="6">
          <v-card elevation="0" border>
            <v-card-title class="d-flex align-center pa-4 pb-2">
              <v-icon class="mr-2" color="success">mdi-trophy</v-icon>
              <span class="font-weight-bold">Recent Results</span>
            </v-card-title>
            <v-card-text class="pt-0">
              <div v-if="recentResults.length === 0" class="text-center text-medium-emphasis py-6">
                <v-icon icon="mdi-soccer-field" size="36" color="medium-emphasis" class="mb-2 d-block" />
                <span class="text-body-2">No completed matches yet</span>
              </div>
              <v-list v-else density="compact">
                <v-list-item v-for="r in recentResults" :key="r.id" rounded="lg" class="mb-1">
                  <template #prepend>
                    <v-chip
                      :color="getResultColor(r)"
                      size="x-small"
                      variant="flat"
                      class="mr-2 font-weight-bold"
                    >
                      {{ getResultLabel(r) }}
                    </v-chip>
                  </template>
                  <v-list-item-title class="text-body-2 font-weight-medium">
                    {{ r.challenger?.name }}
                    <strong class="mx-1">{{ r.challenger_score }} – {{ r.opponent_score }}</strong>
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
import { useTheme } from 'vuetify'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

definePageMeta({
  middleware: ['auth'],
})

const { user, isCaptain } = useAuth()
const config = useRuntimeConfig()
const apiBase = computed(() => config.public.apiBaseUrl || 'http://localhost:8000/api/v1')
const theme = useTheme()

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

// Data fetching
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

// Chart rendering (theme-aware)
const renderChart = async () => {
  if (!ratingHistory.value.length || !chartCanvas.value) return

  await nextTick()

  if (chartInstance) {
    chartInstance.destroy()
  }

  // Use Vuetify theme CSS vars for colors
  const isDark = theme.global.current.value.dark
  const primaryColor = isDark ? '#4CAF50' : '#2E7D32'
  const gridColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)'
  const textColor = isDark ? '#EEEEEE' : '#212121'

  const labels = ratingHistory.value.map((r: any) =>
    new Date(r.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  )
  const ratings = ratingHistory.value.map((r: any) => r.new_rating)

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
          borderColor: primaryColor,
          backgroundColor: isDark
            ? 'rgba(76, 175, 80, 0.12)'
            : 'rgba(46, 125, 50, 0.10)',
          fill: true,
          tension: 0.4,
          pointRadius: 5,
          pointHoverRadius: 7,
          pointBackgroundColor: primaryColor,
          pointBorderColor: isDark ? '#1E1E1E' : '#FFFFFF',
          pointBorderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: isDark ? '#2C2C2C' : '#FFFFFF',
          titleColor: textColor,
          bodyColor: textColor,
          borderColor: isDark ? '#444' : '#e0e0e0',
          borderWidth: 1,
          callbacks: {
            label: (ctx) => `Rating: ${ctx.parsed.y}`,
          },
        },
      },
      scales: {
        y: {
          title: { display: true, text: 'ELO Rating', color: textColor },
          beginAtZero: false,
          grid: { color: gridColor },
          ticks: { color: textColor },
        },
        x: {
          title: { display: true, text: 'Match Date', color: textColor },
          grid: { color: gridColor },
          ticks: { color: textColor },
        },
      },
    },
  })
}

// Helpers
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

// Lifecycle
onMounted(async () => {
  loading.value = true
  await fetchMyTeam()
  await Promise.all([fetchRatingHistory(), fetchChallenges(), fetchNotifications()])
  loading.value = false
  await nextTick()
  renderChart()
})

// Re-render chart when data or theme changes
watch(ratingHistory, () => nextTick(() => renderChart()))
watch(() => theme.global.current.value.dark, () => nextTick(() => renderChart()))
</script>

<style scoped>
/* Team card */
.team-card-header {
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  min-height: 160px;
}

.team-avatar {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
  border: 3px solid rgba(255, 255, 255, 0.4);
}

.stat-cell {
  transition: background 0.15s ease;
}

.stat-cell:hover {
  background: rgb(var(--v-theme-surface-variant));
}

/* Empty state icon wrap */
.empty-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: rgb(var(--v-theme-surface-variant));
}
</style>
