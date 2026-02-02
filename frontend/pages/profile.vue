<template>
  <!--
    Profile Page - Mobile-First Responsive Design
    ============================================
    This page uses Vuetify's responsive grid system and breakpoints
    to provide an optimal viewing experience on all devices.

    Breakpoints:
    - xs: 0-599px (mobile phones)
    - sm: 600-959px (tablets)
    - md: 960-1279px (small desktops)
    - lg: 1280-1919px (desktops)
    - xl: 1920px+ (large desktops)

    Mobile-First Approach:
    - Single column layout on mobile (xs)
    - Two column layout on desktop (md+)
    - Smaller icons and avatars on mobile
    - Touch-friendly button sizes
  -->
  <v-container fluid class="pa-0">
    <!-- Profile Header Card -->
    <v-card elevation="0" rounded="0" color="primary" dark class="mb-4">
      <!-- Hero Background -->
      <v-sheet color="secondary" height="100" class="d-flex align-end">
        <v-container>
          <!-- Avatar positioned to overlap hero -->
          <v-avatar
            :size="$vuetify.display.xs ? 80 : 120"
            color="white"
            class="elevation-4"
            style="margin-bottom: -40px"
          >
            <span
              :class="$vuetify.display.xs ? 'text-h5' : 'text-h3'"
              class="primary--text font-weight-bold"
            >
              {{ initials }}
            </span>
          </v-avatar>
        </v-container>
      </v-sheet>

      <!-- Profile Header Info -->
      <v-card-text class="pt-12">
        <v-container>
          <v-row align="center">
            <!-- User Name and Username -->
            <v-col cols="12" sm="8">
              <h1 :class="$vuetify.display.xs ? 'text-h5' : 'text-h4'" class="font-weight-bold mb-1">
                {{ user?.full_name || user?.username }}
              </h1>
              <p class="text-subtitle-1 mb-2">@{{ user?.username }}</p>
              <v-chip
                v-if="user?.is_active"
                color="success"
                size="small"
                prepend-icon="mdi-check-circle"
              >
                Active Account
              </v-chip>
            </v-col>

            <!-- Logout Button (desktop: right aligned, mobile: full width) -->
            <v-col cols="12" sm="4" class="text-sm-right">
              <v-btn
                color="error"
                variant="elevated"
                prepend-icon="mdi-logout"
                @click="handleLogout"
                :block="$vuetify.display.xs"
              >
                Logout
              </v-btn>
            </v-col>
          </v-row>
        </v-container>
      </v-card-text>
    </v-card>

    <!-- Main Content Area -->
    <v-container>
      <v-row>
        <!-- Account Information Card (Left Column - Full width on mobile, 2/3 on desktop) -->
        <v-col cols="12" md="8">
          <v-card elevation="2" rounded="lg">
            <v-card-title class="text-h5 font-weight-bold">
              <v-icon start size="small">mdi-account-details</v-icon>
              Account Information
            </v-card-title>
            <v-divider />

            <v-card-text>
              <!-- Information List -->
              <v-list lines="two" density="compact">
                <!-- Full Name -->
                <v-list-item>
                  <template #prepend>
                    <v-icon color="primary" size="small">mdi-account</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-medium-emphasis">
                    Full Name
                  </v-list-item-title>
                  <v-list-item-subtitle class="text-body-1 font-weight-medium">
                    {{ user?.full_name || 'Not set' }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-divider inset />

                <!-- Username -->
                <v-list-item>
                  <template #prepend>
                    <v-icon color="primary" size="small">mdi-at</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-medium-emphasis">
                    Username
                  </v-list-item-title>
                  <v-list-item-subtitle class="text-body-1 font-weight-medium">
                    {{ user?.username }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-divider inset />

                <!-- Email -->
                <v-list-item>
                  <template #prepend>
                    <v-icon color="primary" size="small">mdi-email</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-medium-emphasis">
                    Email Address
                  </v-list-item-title>
                  <v-list-item-subtitle class="text-body-1 font-weight-medium">
                    {{ user?.email }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-divider inset />

                <!-- User ID -->
                <v-list-item>
                  <template #prepend>
                    <v-icon color="primary" size="small">mdi-identifier</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-medium-emphasis">
                    User ID
                  </v-list-item-title>
                  <v-list-item-subtitle class="text-body-1 font-weight-medium font-mono">
                    #{{ user?.id }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-divider inset />

                <!-- Member Since -->
                <v-list-item>
                  <template #prepend>
                    <v-icon color="primary" size="small">mdi-calendar-check</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-medium-emphasis">
                    Member Since
                  </v-list-item-title>
                  <v-list-item-subtitle class="text-body-1 font-weight-medium">
                    {{ formatDate(user?.created_at) }}
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Sidebar (Right Column - Full width on mobile, 1/3 on desktop) -->
        <v-col cols="12" md="4">
          <!-- Account Status Card -->
          <v-card elevation="2" rounded="lg" class="mb-4">
            <v-card-title class="text-h6 font-weight-bold">
              <v-icon start size="small">mdi-shield-account</v-icon>
              Account Status
            </v-card-title>
            <v-divider />

            <v-card-text>
              <v-list density="compact">
                <!-- Account Type -->
                <v-list-item>
                  <v-list-item-title class="text-caption text-medium-emphasis">
                    Account Type
                  </v-list-item-title>
                  <template #append>
                    <v-chip
                      :color="user?.is_superuser ? 'error' : 'primary'"
                      size="small"
                      variant="flat"
                    >
                      {{ user?.is_superuser ? 'Admin' : 'User' }}
                    </v-chip>
                  </template>
                </v-list-item>

                <v-divider />

                <!-- Account Status -->
                <v-list-item>
                  <v-list-item-title class="text-caption text-medium-emphasis">
                    Status
                  </v-list-item-title>
                  <template #append>
                    <v-chip
                      :color="user?.is_active ? 'success' : 'error'"
                      size="small"
                      variant="flat"
                    >
                      {{ user?.is_active ? 'Active' : 'Inactive' }}
                    </v-chip>
                  </template>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>

          <!-- Player Statistics Card (Example for future use) -->
          <v-card elevation="2" rounded="lg" class="mb-4">
            <v-card-title class="text-h6 font-weight-bold">
              <v-icon start size="small">mdi-chart-bar</v-icon>
              Player Stats
            </v-card-title>
            <v-divider />

            <v-card-text>
              <v-row dense>
                <!-- Goals Stat -->
                <v-col cols="6">
                  <v-card color="primary" dark class="text-center pa-3">
                    <v-icon size="large" class="mb-2">mdi-soccer</v-icon>
                    <div class="text-h4 font-weight-bold">0</div>
                    <div class="text-caption">Goals</div>
                  </v-card>
                </v-col>

                <!-- Matches Stat -->
                <v-col cols="6">
                  <v-card color="secondary" dark class="text-center pa-3">
                    <v-icon size="large" class="mb-2">mdi-trophy</v-icon>
                    <div class="text-h4 font-weight-bold">0</div>
                    <div class="text-caption">Matches</div>
                  </v-card>
                </v-col>

                <!-- Rating Stat -->
                <v-col cols="12">
                  <v-card color="success" dark class="text-center pa-3">
                    <v-icon size="large" class="mb-2">mdi-star</v-icon>
                    <div class="text-h4 font-weight-bold">0.0</div>
                    <div class="text-caption">Player Rating</div>
                  </v-card>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Quick Actions Card -->
          <v-card elevation="2" rounded="lg">
            <v-card-title class="text-h6 font-weight-bold">
              <v-icon start size="small">mdi-lightning-bolt</v-icon>
              Quick Actions
            </v-card-title>
            <v-divider />

            <v-list density="compact">
              <v-list-item
                prepend-icon="mdi-account-edit"
                title="Edit Profile"
                subtitle="Update your information"
                link
              />
              <v-divider />

              <v-list-item
                prepend-icon="mdi-lock-reset"
                title="Change Password"
                subtitle="Secure your account"
                link
              />
              <v-divider />

              <v-list-item
                prepend-icon="mdi-bell-outline"
                title="Notifications"
                subtitle="Manage preferences"
                link
              />
              <v-divider />

              <v-list-item
                prepend-icon="mdi-shield-check"
                title="Privacy Settings"
                subtitle="Control your data"
                link
              />
            </v-list>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </v-container>
</template>

<script setup lang="ts">
/**
 * Profile Page Component
 * =====================
 * Displays user account information and statistics
 *
 * Authentication:
 * - Protected by auth middleware
 * - Requires valid user session
 *
 * Responsive Design:
 * - Mobile: Single column layout (xs)
 * - Tablet: Single column with larger components (sm)
 * - Desktop: Two column layout (md+)
 */

// Protect route with authentication middleware
definePageMeta({
  middleware: 'auth'
})

// Composables
const { user, logout } = useAuth()
const router = useRouter()

/**
 * User Initials
 * ============
 * Computed property to generate 1-2 letter initials from user's name
 * Used for avatar display when no profile picture is available
 */
const initials = computed(() => {
  if (user.value?.full_name) {
    return user.value.full_name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }
  return user.value?.username?.slice(0, 2).toUpperCase() || 'U'
})

/**
 * Date Formatter
 * =============
 * Formats ISO date strings to human-readable format
 * Example: "2024-01-15" → "January 15, 2024"
 */
const formatDate = (dateString: string | undefined): string => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

/**
 * Logout Handler
 * =============
 * Clears user session and redirects to home page
 */
const handleLogout = () => {
  logout()
  router.push('/')
}
</script>

<style scoped>
/**
 * Component-Specific Styles
 * =========================
 * Minimal scoped styles - Vuetify handles most styling
 */

/* Ensure font-mono works in Vuetify */
.font-mono {
  font-family: 'Courier New', Courier, monospace;
}
</style>
