<template>
  <!-- Hero Section — full-width gradient, outside v-container -->
  <div>
    <div class="hero-section">
      <v-container class="py-16">
        <v-row justify="center" align="center">
          <v-col cols="12" md="8" class="text-center">
            <div class="hero-icon-wrap mb-6">
              <v-icon icon="mdi-soccer" size="72" color="white" class="hero-icon" />
            </div>

            <h1 class="text-h2 text-md-h1 font-weight-black text-white mb-4 hero-title">
              AmStar Football
            </h1>

            <p class="text-h6 text-md-h5 mb-8 hero-subtitle">
              Organize matches · Build teams · Track your ELO
            </p>

            <div class="d-flex justify-center gap-4 flex-wrap">
              <v-btn
                color="white"
                size="large"
                rounded="xl"
                to="/teams"
                class="hero-btn-primary font-weight-bold"
                elevation="4"
              >
                <v-icon start>mdi-shield-account</v-icon>
                Browse Teams
              </v-btn>

              <v-btn
                variant="outlined"
                color="white"
                size="large"
                rounded="xl"
                to="/auth/register"
                class="hero-btn-outline font-weight-bold"
              >
                <v-icon start>mdi-account-plus</v-icon>
                Join for Free
              </v-btn>
            </div>
          </v-col>
        </v-row>
      </v-container>

      <!-- Wave divider -->
      <div class="hero-wave">
        <svg viewBox="0 0 1440 80" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">
          <path d="M0,40 C360,80 1080,0 1440,40 L1440,80 L0,80 Z" fill="currentColor" />
        </svg>
      </div>
    </div>

    <!-- Stats Section -->
    <v-container class="py-12">
      <v-row justify="center" class="mb-4">
        <v-col cols="12" class="text-center">
          <h2 class="text-h4 font-weight-bold mb-2">Platform at a Glance</h2>
          <p class="text-body-1 text-medium-emphasis">Live numbers from our community</p>
        </v-col>
      </v-row>

      <v-row ref="statsRow">
        <!-- Players -->
        <v-col cols="12" sm="6" md="3">
          <v-card class="stat-card text-center pa-6" elevation="0" border>
            <div class="stat-icon-wrap mb-4">
              <v-icon icon="mdi-account-group" size="36" color="primary" />
            </div>
            <div class="text-h3 font-weight-black text-primary mb-1">
              <v-skeleton-loader v-if="statsLoading" type="text" class="mx-auto" width="80" />
              <span v-else class="stat-number">{{ displayStats.total_users }}</span>
            </div>
            <div class="text-body-1 text-medium-emphasis font-weight-medium">Players</div>
          </v-card>
        </v-col>

        <!-- Teams -->
        <v-col cols="12" sm="6" md="3">
          <v-card class="stat-card text-center pa-6" elevation="0" border>
            <div class="stat-icon-wrap mb-4">
              <v-icon icon="mdi-shield-account" size="36" color="secondary" />
            </div>
            <div class="text-h3 font-weight-black text-secondary mb-1">
              <v-skeleton-loader v-if="statsLoading" type="text" class="mx-auto" width="80" />
              <span v-else class="stat-number">{{ displayStats.total_teams }}</span>
            </div>
            <div class="text-body-1 text-medium-emphasis font-weight-medium">Teams</div>
          </v-card>
        </v-col>

        <!-- Matches Played -->
        <v-col cols="12" sm="6" md="3">
          <v-card class="stat-card text-center pa-6" elevation="0" border>
            <div class="stat-icon-wrap mb-4">
              <v-icon icon="mdi-trophy" size="36" color="success" />
            </div>
            <div class="text-h3 font-weight-black text-success mb-1">
              <v-skeleton-loader v-if="statsLoading" type="text" class="mx-auto" width="80" />
              <span v-else class="stat-number">{{ displayStats.completed_matches }}</span>
            </div>
            <div class="text-body-1 text-medium-emphasis font-weight-medium">Matches Played</div>
          </v-card>
        </v-col>

        <!-- Challenges -->
        <v-col cols="12" sm="6" md="3">
          <v-card class="stat-card text-center pa-6" elevation="0" border>
            <div class="stat-icon-wrap mb-4">
              <v-icon icon="mdi-sword-cross" size="36" color="warning" />
            </div>
            <div class="text-h3 font-weight-black text-warning mb-1">
              <v-skeleton-loader v-if="statsLoading" type="text" class="mx-auto" width="80" />
              <span v-else class="stat-number">{{ displayStats.total_challenges }}</span>
            </div>
            <div class="text-body-1 text-medium-emphasis font-weight-medium">Challenges</div>
          </v-card>
        </v-col>
      </v-row>
    </v-container>

    <!-- Features Section -->
    <div class="features-section py-12">
      <v-container>
        <v-row justify="center" class="mb-8">
          <v-col cols="12" class="text-center">
            <h2 class="text-h4 font-weight-bold mb-2">Everything you need</h2>
            <p class="text-body-1 text-medium-emphasis">Built for amateur football communities</p>
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="12" md="4">
            <v-card class="feature-card pa-6 h-100" elevation="0" border>
              <div class="feature-icon-wrap mb-4">
                <v-icon icon="mdi-shield-account" size="40" color="primary" />
              </div>
              <h3 class="text-h6 font-weight-bold mb-2">Team Management</h3>
              <p class="text-body-2 text-medium-emphasis">
                Create your team, invite players, manage your roster and track join requests — all in one place.
              </p>
            </v-card>
          </v-col>

          <v-col cols="12" md="4">
            <v-card class="feature-card pa-6 h-100" elevation="0" border>
              <div class="feature-icon-wrap mb-4">
                <v-icon icon="mdi-sword-cross" size="40" color="secondary" />
              </div>
              <h3 class="text-h6 font-weight-bold mb-2">Challenge System</h3>
              <p class="text-body-2 text-medium-emphasis">
                Challenge rival teams, schedule matches, submit scores and assign goals and assists to players.
              </p>
            </v-card>
          </v-col>

          <v-col cols="12" md="4">
            <v-card class="feature-card pa-6 h-100" elevation="0" border>
              <div class="feature-icon-wrap mb-4">
                <v-icon icon="mdi-chart-line" size="40" color="success" />
              </div>
              <h3 class="text-h6 font-weight-bold mb-2">ELO Rankings</h3>
              <p class="text-body-2 text-medium-emphasis">
                Fair skill-based ratings update after every match. Climb the leaderboard and prove your team's worth.
              </p>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </div>

    <!-- CTA Footer Banner -->
    <div class="cta-section py-16 text-center">
      <v-container>
        <v-icon icon="mdi-soccer" size="48" color="primary" class="mb-4" />
        <h2 class="text-h4 font-weight-bold mb-3">Ready to play?</h2>
        <p class="text-body-1 text-medium-emphasis mb-6">
          Join the community — it's free and takes less than a minute.
        </p>
        <v-btn color="primary" size="x-large" rounded="xl" to="/auth/register" elevation="2">
          <v-icon start>mdi-account-plus</v-icon>
          Create an Account
        </v-btn>
      </v-container>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'

const { isAuthenticated } = useAuth()
const runtimeConfig = useRuntimeConfig()
const apiBase = runtimeConfig.public.apiBaseUrl || 'http://localhost:8000/api/v1'

const statsLoading = ref(true)

const globalStats = ref({
  total_users: 0,
  total_teams: 0,
  completed_matches: 0,
  total_challenges: 0,
})

// Animated display values (count up)
const displayStats = reactive({
  total_users: 0,
  total_teams: 0,
  completed_matches: 0,
  total_challenges: 0,
})

const animateCount = (key: keyof typeof displayStats, target: number) => {
  const duration = 1200
  const start = performance.now()
  const tick = (now: number) => {
    const elapsed = now - start
    const progress = Math.min(elapsed / duration, 1)
    // Ease out cubic
    const ease = 1 - Math.pow(1 - progress, 3)
    displayStats[key] = Math.round(target * ease)
    if (progress < 1) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
}

const fetchGlobalStats = async () => {
  try {
    const data = await $fetch<typeof globalStats.value>(`${apiBase}/stats/global`)
    globalStats.value = data
    // Animate each counter
    ;(Object.keys(data) as Array<keyof typeof displayStats>).forEach((key) => {
      if (key in displayStats) animateCount(key, data[key])
    })
  } catch {
    // Backend unreachable — show zeros silently
  } finally {
    statsLoading.value = false
  }
}

onMounted(() => {
  if (isAuthenticated.value) {
    navigateTo('/dashboard')
    return
  }
  fetchGlobalStats()
})
</script>

<style scoped>
/* Hero */
.hero-section {
  position: relative;
  background: linear-gradient(135deg, rgb(var(--v-theme-primary)) 0%, rgb(var(--v-theme-secondary)) 100%);
  padding-bottom: 0;
  overflow: hidden;
}

.hero-section::before {
  content: '';
  position: absolute;
  inset: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.04'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}

.hero-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(4px);
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.hero-icon {
  filter: drop-shadow(0 2px 8px rgba(0,0,0,0.2));
}

.hero-title {
  text-shadow: 0 2px 16px rgba(0, 0, 0, 0.25);
  letter-spacing: -0.5px;
}

.hero-subtitle {
  color: rgba(255, 255, 255, 0.85) !important;
}

.hero-btn-primary {
  color: rgb(var(--v-theme-primary)) !important;
}

.hero-btn-outline {
  border-color: rgba(255, 255, 255, 0.7) !important;
}

.hero-wave {
  line-height: 0;
  color: rgb(var(--v-theme-background));
}

.hero-wave svg {
  width: 100%;
  height: 80px;
  display: block;
}

/* Stats cards */
.stat-card {
  border-radius: 16px !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1) !important;
}

.stat-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: rgba(var(--v-theme-surface-variant), 1);
}

/* Features */
.features-section {
  background: rgb(var(--v-theme-surface-variant));
}

.feature-card {
  border-radius: 16px !important;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1) !important;
}

.feature-icon-wrap {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: rgb(var(--v-theme-background));
}

/* CTA */
.cta-section {
  background: rgb(var(--v-theme-background));
}

/* Gap utility (Vuetify 3 uses ga-N but scoped style needs this too) */
.gap-4 {
  gap: 1rem;
}
</style>
