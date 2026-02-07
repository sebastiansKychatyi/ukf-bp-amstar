<template>
  <v-container class="py-8">
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <h1 :class="$vuetify.display.xs ? 'text-h4' : 'text-h3'" class="font-weight-bold mb-2">
          <v-icon icon="mdi-trophy" :size="$vuetify.display.xs ? 'default' : 'large'" class="mr-2" />
          Leaderboard
        </h1>
        <p class="text-body-1 text-medium-emphasis">
          Teams ranked by ELO rating
        </p>
      </v-col>
    </v-row>

    <!-- Tab Switch: Teams / Players -->
    <v-row>
      <v-col cols="12">
        <v-tabs v-model="activeTab" color="primary">
          <v-tab value="teams" prepend-icon="mdi-shield-account">Team Rankings</v-tab>
          <v-tab value="scorers" prepend-icon="mdi-soccer">Top Scorers</v-tab>
          <v-tab value="assists" prepend-icon="mdi-shoe-cleat">Top Assists</v-tab>
        </v-tabs>
      </v-col>
    </v-row>

    <!-- Error -->
    <v-row v-if="error">
      <v-col cols="12">
        <v-alert type="error" closable @click:close="error = null">{{ error }}</v-alert>
      </v-col>
    </v-row>

    <!-- Team Leaderboard -->
    <v-row v-if="activeTab === 'teams'">
      <v-col cols="12">
        <v-card elevation="2">
          <v-data-table
            :headers="teamHeaders"
            :items="teamRankings"
            :loading="loading"
            :items-per-page="25"
            hover
          >
            <!-- Rank -->
            <template #item.rank="{ item }">
              <div class="d-flex align-center">
                <v-avatar
                  v-if="item.rank <= 3"
                  size="32"
                  :color="item.rank === 1 ? 'amber' : item.rank === 2 ? 'grey-lighten-1' : 'brown-lighten-1'"
                >
                  <v-icon size="18" color="white">mdi-trophy</v-icon>
                </v-avatar>
                <span v-else class="text-h6 font-weight-medium ml-1">{{ item.rank }}</span>
              </div>
            </template>

            <!-- Team Name -->
            <template #item.team_name="{ item }">
              <span class="font-weight-medium text-primary cursor-pointer" @click="navigateTo(`/teams/${item.team_id}`)">
                {{ item.team_name }}
              </span>
            </template>

            <!-- Rating -->
            <template #item.rating="{ item }">
              <v-chip :color="getRatingColor(item.rating)" variant="flat" size="small">
                {{ item.rating }}
              </v-chip>
            </template>

            <!-- City -->
            <template #item.city="{ item }">
              <v-chip v-if="item.city" size="small" variant="outlined">
                <v-icon start size="small">mdi-map-marker</v-icon>
                {{ item.city }}
              </v-chip>
              <span v-else class="text-medium-emphasis">-</span>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Top Scorers -->
    <v-row v-if="activeTab === 'scorers'">
      <v-col cols="12">
        <v-card elevation="2">
          <v-data-table
            :headers="playerHeaders('Goals')"
            :items="topScorers"
            :loading="loading"
            :items-per-page="25"
            hover
          >
            <template #item.rank="{ item }">
              <v-avatar
                v-if="item.rank <= 3"
                size="32"
                :color="item.rank === 1 ? 'amber' : item.rank === 2 ? 'grey-lighten-1' : 'brown-lighten-1'"
              >
                <v-icon size="18" color="white">mdi-trophy</v-icon>
              </v-avatar>
              <span v-else class="text-h6 font-weight-medium ml-1">{{ item.rank }}</span>
            </template>

            <template #item.username="{ item }">
              <span class="font-weight-medium">{{ item.full_name || item.username }}</span>
            </template>

            <template #item.goals="{ item }">
              <v-chip color="success" variant="flat" size="small">{{ item.goals }}</v-chip>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Top Assists -->
    <v-row v-if="activeTab === 'assists'">
      <v-col cols="12">
        <v-card elevation="2">
          <v-data-table
            :headers="playerHeaders('Assists')"
            :items="topAssists"
            :loading="loading"
            :items-per-page="25"
            hover
          >
            <template #item.rank="{ item }">
              <v-avatar
                v-if="item.rank <= 3"
                size="32"
                :color="item.rank === 1 ? 'amber' : item.rank === 2 ? 'grey-lighten-1' : 'brown-lighten-1'"
              >
                <v-icon size="18" color="white">mdi-trophy</v-icon>
              </v-avatar>
              <span v-else class="text-h6 font-weight-medium ml-1">{{ item.rank }}</span>
            </template>

            <template #item.username="{ item }">
              <span class="font-weight-medium">{{ item.full_name || item.username }}</span>
            </template>

            <template #item.assists="{ item }">
              <v-chip color="info" variant="flat" size="small">{{ item.assists }}</v-chip>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'

const config = useRuntimeConfig()
const apiBase = computed(() => config.public.apiBaseUrl || 'http://localhost:8000/api/v1')

// State
const activeTab = ref('teams')
const loading = ref(false)
const error = ref<string | null>(null)
const teamRankings = ref<any[]>([])
const topScorers = ref<any[]>([])
const topAssists = ref<any[]>([])

// Headers
const teamHeaders = [
  { title: '#', key: 'rank', width: '60px', sortable: false },
  { title: 'Team', key: 'team_name' },
  { title: 'City', key: 'city' },
  { title: 'Rating', key: 'rating', align: 'center' as const },
  { title: 'Matches', key: 'matches_played', align: 'center' as const },
]

const playerHeaders = (stat: string) => [
  { title: '#', key: 'rank', width: '60px', sortable: false },
  { title: 'Player', key: 'username' },
  { title: stat, key: stat.toLowerCase(), align: 'center' as const },
  { title: 'Matches', key: 'matches_played', align: 'center' as const },
]

// Fetch
const fetchTeamRankings = async () => {
  loading.value = true
  try {
    teamRankings.value = await $fetch<any[]>(`${apiBase.value}/ratings/leaderboard?limit=50`)
  } catch (err: any) {
    error.value = err.data?.detail || 'Failed to load leaderboard'
  } finally {
    loading.value = false
  }
}

const fetchTopScorers = async () => {
  loading.value = true
  try {
    topScorers.value = await $fetch<any[]>(`${apiBase.value}/statistics/top-scorers?limit=50`)
  } catch (err: any) {
    error.value = err.data?.detail || 'Failed to load top scorers'
  } finally {
    loading.value = false
  }
}

const fetchTopAssists = async () => {
  loading.value = true
  try {
    topAssists.value = await $fetch<any[]>(`${apiBase.value}/statistics/top-assists?limit=50`)
  } catch (err: any) {
    error.value = err.data?.detail || 'Failed to load top assists'
  } finally {
    loading.value = false
  }
}

const getRatingColor = (rating: number) => {
  if (!rating) return 'grey'
  if (rating >= 1500) return 'success'
  if (rating >= 1200) return 'primary'
  if (rating >= 900) return 'warning'
  return 'error'
}

watch(activeTab, (tab) => {
  if (tab === 'teams') fetchTeamRankings()
  else if (tab === 'scorers') fetchTopScorers()
  else if (tab === 'assists') fetchTopAssists()
})

onMounted(() => fetchTeamRankings())
</script>

<style scoped>
.cursor-pointer { cursor: pointer; }
</style>
