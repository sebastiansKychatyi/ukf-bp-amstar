<template>
  <v-app>
    <!-- Navigation Drawer (Mobile) -->
    <v-navigation-drawer
      v-model="drawer"
      temporary
      :width="280"
    >
      <v-list density="compact" nav>
        <!-- Logo -->
        <v-list-item
          prepend-icon="mdi-soccer-field"
          title="AmStar"
          subtitle="Football Platform"
          class="mb-2"
        />

        <v-divider class="mb-2" />

        <!-- Navigation Items -->
        <v-list-item
          v-for="item in navigationItems"
          :key="item.to"
          :to="item.to"
          :prepend-icon="item.icon"
          :title="item.title"
          color="primary"
          rounded="xl"
        />
      </v-list>

      <template #append>
        <div class="pa-4">
          <v-btn
            block
            prepend-icon="mdi-logout"
            variant="tonal"
            @click="handleLogout"
          >
            Logout
          </v-btn>
        </div>
      </template>
    </v-navigation-drawer>

    <!-- App Bar -->
    <v-app-bar
      elevation="0"
      :height="64"
      class="border-b"
    >
      <!-- Mobile Menu Button -->
      <v-app-bar-nav-icon
        class="d-md-none"
        @click="drawer = !drawer"
      />

      <!-- Logo and Title -->
      <v-app-bar-title class="d-flex align-center">
        <v-icon size="32" color="primary" class="mr-2">
          mdi-soccer-field
        </v-icon>
        <span class="text-h6 font-weight-bold d-none d-sm-inline">
          AmStar
        </span>
      </v-app-bar-title>

      <!-- Desktop Navigation -->
      <div class="d-none d-md-flex align-center ga-2">
        <v-btn
          v-for="item in navigationItems"
          :key="item.to"
          :to="item.to"
          :prepend-icon="item.icon"
          variant="text"
          rounded="lg"
        >
          {{ item.title }}
        </v-btn>
      </div>

      <v-spacer />

      <!-- Theme Toggle -->
      <v-btn
        :icon="themeIcon"
        variant="text"
        @click="toggleTheme"
      >
        <v-icon>{{ themeIcon }}</v-icon>
        <v-tooltip activator="parent" location="bottom">
          Toggle {{ theme.global.name.value === 'light' ? 'Dark' : 'Light' }} Mode
        </v-tooltip>
      </v-btn>

      <!-- Notifications (Mock) -->
      <v-btn icon variant="text">
        <v-badge content="3" color="error" offset-x="-4" offset-y="4">
          <v-icon>mdi-bell</v-icon>
        </v-badge>
        <v-tooltip activator="parent" location="bottom">
          Notifications
        </v-tooltip>
      </v-btn>

      <!-- User Menu -->
      <v-menu offset-y>
        <template #activator="{ props }">
          <v-btn
            icon
            v-bind="props"
            class="ml-2"
          >
            <v-avatar color="primary" size="40">
              <v-icon color="white">mdi-account</v-icon>
            </v-avatar>
          </v-btn>
        </template>

        <v-list>
          <v-list-item
            prepend-icon="mdi-account-circle"
            title="Profile"
            subtitle="View your profile"
            @click="goToProfile"
          />

          <v-list-item
            prepend-icon="mdi-shield-account"
            title="My Team"
            subtitle="Manage your team"
            @click="goToMyTeam"
          />

          <v-list-item
            prepend-icon="mdi-cog"
            title="Settings"
            subtitle="Account settings"
            @click="goToSettings"
          />

          <v-divider class="my-2" />

          <v-list-item
            prepend-icon="mdi-logout"
            title="Logout"
            @click="handleLogout"
          />
        </v-list>
      </v-menu>
    </v-app-bar>

    <!-- Main Content -->
    <v-main>
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </v-main>

    <!-- Footer -->
    <v-footer class="bg-surface border-t">
      <v-container>
        <v-row align="center">
          <v-col cols="12" md="6" class="text-center text-md-start">
            <div class="d-flex align-center justify-center justify-md-start">
              <v-icon color="primary" size="24" class="mr-2">
                mdi-soccer-field
              </v-icon>
              <span class="font-weight-bold">AmStar Football Platform</span>
            </div>
            <p class="text-caption text-medium-emphasis mt-2 mb-0">
              © 2024 AmStar. All rights reserved.
            </p>
          </v-col>

          <v-col cols="12" md="6" class="text-center text-md-end">
            <v-btn
              variant="text"
              size="small"
              href="#"
            >
              About
            </v-btn>
            <v-btn
              variant="text"
              size="small"
              href="#"
            >
              Privacy
            </v-btn>
            <v-btn
              variant="text"
              size="small"
              href="#"
            >
              Terms
            </v-btn>
            <v-btn
              variant="text"
              size="small"
              href="#"
            >
              Contact
            </v-btn>
          </v-col>
        </v-row>
      </v-container>
    </v-footer>
  </v-app>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from 'vuetify'

const router = useRouter()
const theme = useTheme()
const drawer = ref(false)

// Navigation items
const navigationItems = [
  { title: 'Dashboard', icon: 'mdi-view-dashboard', to: '/' },
  { title: 'Players', icon: 'mdi-account-group', to: '/players' },
  { title: 'Teams', icon: 'mdi-shield-account', to: '/teams' },
  { title: 'Battles', icon: 'mdi-sword-cross', to: '/battles' },
]

// Theme
const themeIcon = computed(() =>
  theme.global.name.value === 'light' ? 'mdi-weather-night' : 'mdi-weather-sunny'
)

function toggleTheme() {
  theme.global.name.value = theme.global.name.value === 'light' ? 'dark' : 'light'
}

// Navigation
function goToProfile() {
  router.push('/profile')
}

function goToMyTeam() {
  router.push('/my-team')
}

function goToSettings() {
  router.push('/settings')
}

function handleLogout() {
  // Implement logout logic
  console.log('Logout clicked')
  router.push('/login')
}
</script>

<style scoped>
.border-b {
  border-bottom: 1px solid rgb(var(--v-theme-surface-variant));
}

.border-t {
  border-top: 1px solid rgb(var(--v-theme-surface-variant));
}

/* Page transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
