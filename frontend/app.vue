<template>

  <v-app>
    <!-- Mobile Navigation Drawer -->
    <v-navigation-drawer
      v-model="drawer"
      app
      temporary
      :width="280"
    >
      <!-- Drawer Header -->
      <v-list-item
        prepend-icon="mdi-soccer"
        title="AmStar Football"
        subtitle="Amateur Football Platform"
        class="bg-primary text-white"
      />

      <v-divider />

      <!-- Drawer Navigation Links -->
      <v-list density="compact" nav>
        <v-list-item
          prepend-icon="mdi-home"
          title="Home"
          to="/"
          exact
          @click="drawer = false"
        />

        <v-list-item
          prepend-icon="mdi-shield-account"
          title="Teams"
          to="/teams"
          @click="drawer = false"
        />

        <v-list-item
          prepend-icon="mdi-account-group"
          title="Players"
          to="/players"
          @click="drawer = false"
        />

        <v-list-item
          prepend-icon="mdi-tournament"
          title="Tournaments"
          to="/tournaments"
          @click="drawer = false"
        />

        <v-list-item
          v-if="isAuthenticated"
          prepend-icon="mdi-account-circle"
          title="Profile"
          to="/profile"
          @click="drawer = false"
        />
        <v-list-item
          v-else
          prepend-icon="mdi-login"
          title="Login"
          to="/auth/login"
          @click="drawer = false"
        />
      </v-list>

      <v-divider />

      <!-- Admin Panel link (superusers only) -->
      <v-list v-if="isSuperuser" density="compact">
        <v-divider />
        <v-list-item
          prepend-icon="mdi-shield-crown"
          title="Admin Panel"
          to="/admin"
          @click="drawer = false"
          base-color="warning"
        />
      </v-list>

      <!-- Theme Toggle in Drawer -->
      <v-list density="compact">
        <v-divider />
        <v-list-item
          :prepend-icon="isDark ? 'mdi-white-balance-sunny' : 'mdi-weather-night'"
          :title="isDark ? 'Light Mode' : 'Dark Mode'"
          @click="toggleTheme"
        />
      </v-list>
    </v-navigation-drawer>

    <!-- App Bar -->
    <v-app-bar
      color="primary"
      elevation="0"
      app
      class="app-bar"
    >
      <!-- Hamburger Menu (Mobile Only) -->
      <v-app-bar-nav-icon
        @click="drawer = !drawer"
        class="d-md-none"
      />

      <!-- Logo -->
      <v-app-bar-title class="font-weight-bold">
        <NuxtLink to="/" class="logo-link d-flex align-center">
          <v-icon icon="mdi-soccer" class="mr-2" />
          <span class="d-none d-sm-inline">AmStar Football</span>
          <span class="d-inline d-sm-none">AmStar</span>
        </NuxtLink>
      </v-app-bar-title>

      <v-spacer />

      <!-- Desktop Navigation Links -->
      <template v-if="$vuetify.display.mdAndUp">
        <v-btn variant="text" to="/" exact class="nav-btn">
          <v-icon start>mdi-home</v-icon>
          Home
        </v-btn>

        <v-btn variant="text" to="/teams" class="nav-btn">
          <v-icon start>mdi-shield-account</v-icon>
          Teams
        </v-btn>

        <v-btn variant="text" to="/players" class="nav-btn">
          <v-icon start>mdi-account-group</v-icon>
          Players
        </v-btn>

        <v-btn variant="text" to="/tournaments" class="nav-btn">
          <v-icon start>mdi-tournament</v-icon>
          Tournaments
        </v-btn>

        <v-btn v-if="isAuthenticated" variant="text" to="/profile" class="nav-btn">
          <v-icon start>mdi-account-circle</v-icon>
          Profile
        </v-btn>
        <v-btn v-else variant="outlined" to="/auth/login" color="white" rounded="lg">
          <v-icon start>mdi-login</v-icon>
          Login
        </v-btn>

        <!-- Admin Panel (superusers only) -->
        <v-btn v-if="isSuperuser" variant="text" to="/admin" color="warning">
          <v-icon start>mdi-shield-crown</v-icon>
          Admin
        </v-btn>

        <!-- Theme Toggle Button -->
        <v-btn
          icon
          @click="toggleTheme"
          class="ml-1"
        >
          <v-icon>{{ isDark ? 'mdi-white-balance-sunny' : 'mdi-weather-night' }}</v-icon>
        </v-btn>
      </template>

      <!-- Mobile: theme toggle only -->
      <v-btn
        v-else
        icon
        @click="toggleTheme"
      >
        <v-icon>{{ isDark ? 'mdi-white-balance-sunny' : 'mdi-weather-night' }}</v-icon>
      </v-btn>
    </v-app-bar>

    <!-- Main Content Area -->
    <v-main>
      <!-- Global Announcement Banner -->
      <v-alert
        v-if="announcement && !announcementDismissed"
        type="info"
        variant="tonal"
        closable
        rounded="0"
        class="announcement-banner"
        prepend-icon="mdi-bullhorn"
        @click:close="announcementDismissed = true"
      >
        {{ announcement }}
      </v-alert>

      <NuxtPage />
    </v-main>

    <!-- Footer -->
    <v-footer
      color="surface-variant"
      app
      class="text-center"
      :class="$vuetify.display.xs ? 'py-2' : 'py-4'"
    >
      <v-container>
        <p :class="$vuetify.display.xs ? 'text-caption' : 'text-body-2'" class="text-medium-emphasis mb-0">
          © {{ currentYear }} AmStar Football Platform
          <span v-if="$vuetify.display.smAndUp"> · Amateur Football Management System</span>
        </p>
      </v-container>
    </v-footer>
  </v-app>
</template>

<script setup lang="ts">
import { useTheme } from 'vuetify'
import { ref, computed, onMounted } from 'vue'

const theme = useTheme()
const { user, isAuthenticated } = useAuth()
const config = useRuntimeConfig()
const apiBase = config.public.apiBaseUrl || 'http://localhost:8000/api/v1'

const isDark = computed(() => theme.global.current.value.dark)
const toggleTheme = () => {
  theme.global.name.value = isDark.value ? 'light' : 'dark'
}

const drawer = ref(false)
const currentYear = new Date().getFullYear()

const isSuperuser = computed(() => user.value?.is_superuser === true)

// Global announcement banner
const announcement = ref<string | null>(null)
const announcementDismissed = ref(false)

const fetchAnnouncement = async () => {
  try {
    const data = await $fetch<{ message: string | null }>(`${apiBase}/admin/announcement`)
    announcement.value = data.message ?? null
    announcementDismissed.value = false
  } catch { /* non-critical; failure does not affect core functionality */ }
}

onMounted(fetchAnnouncement)
</script>

<style>
html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  padding: 0;
}

.announcement-banner {
  border-radius: 0 !important;
}

/* Tooltip — dark background with white text in all themes */
.v-tooltip .v-overlay__content {
  background: #424242 !important;
  color: #ffffff !important;
  font-size: 12px;
}
</style>

<style scoped>
/* App bar bottom border for visual separation */
.app-bar {
  border-bottom: 1px solid rgba(255, 255, 255, 0.12) !important;
}

/* Logo link — remove default anchor styling */
.logo-link {
  color: inherit;
  text-decoration: none;
}

/* Nav buttons: active state indicator */
.nav-btn {
  position: relative;
  transition: opacity 0.15s ease;
}

.nav-btn::after {
  content: '';
  position: absolute;
  bottom: 4px;
  left: 50%;
  transform: translateX(-50%) scaleX(0);
  width: 60%;
  height: 2px;
  border-radius: 2px;
  background: white;
  transition: transform 0.2s ease;
}

/* Nuxt adds router-link-active automatically */
:deep(.router-link-active) .nav-btn::after,
.nav-btn.router-link-active::after {
  transform: translateX(-50%) scaleX(1);
}

:deep(.v-btn.router-link-active)::after {
  transform: translateX(-50%) scaleX(1);
}
</style>
