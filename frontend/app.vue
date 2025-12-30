<template>
  <!--
    Root Application Layout
    =====================
    This is the main layout wrapper for the AmStar Football Platform.
    - v-app: Required Vuetify root component for theming and layout system
    - v-app-bar: Fixed navigation header
    - v-main: Content area with automatic spacing
    - v-footer: Fixed bottom footer
  -->
  <v-app>
    <!-- Navigation Bar -->
    <v-app-bar
      color="primary"
      elevation="1"
      app
    >
      <!-- Logo and Title -->
      <v-app-bar-title class="font-weight-bold">
        <v-icon icon="mdi-soccer" class="mr-2" />
        AmStar Football
      </v-app-bar-title>

      <v-spacer />

      <!-- Main Navigation Links -->
      <v-btn variant="text" to="/" exact>
        <v-icon start>mdi-home</v-icon>
        Home
      </v-btn>

      <v-btn variant="text" to="/teams">
        <v-icon start>mdi-shield-account</v-icon>
        Teams
      </v-btn>

      <v-btn variant="text" to="/players">
        <v-icon start>mdi-account-group</v-icon>
        Players
      </v-btn>

      <v-btn variant="text" to="/profile">
        <v-icon start>mdi-account-circle</v-icon>
        Profile
      </v-btn>

      <!-- Theme Toggle Button -->
      <v-btn
        icon
        @click="toggleTheme"
        class="ml-2"
      >
        <v-icon>{{ isDark ? 'mdi-white-balance-sunny' : 'mdi-weather-night' }}</v-icon>
      </v-btn>
    </v-app-bar>

    <!-- Main Content Area -->
    <v-main>
      <!--
        NuxtPage renders the current route's page component
        This is where pages/index.vue, pages/teams.vue, etc. are displayed
      -->
      <NuxtPage />
    </v-main>

    <!-- Footer -->
    <v-footer
      color="surface"
      app
      class="text-center"
    >
      <v-container>
        <p class="text-body-2 text-medium-emphasis mb-0">
          © {{ currentYear }} AmStar Football Platform - Amateur Football Management System
        </p>
      </v-container>
    </v-footer>
  </v-app>
</template>

<script setup lang="ts">
import { useTheme } from 'vuetify'
import { computed } from 'vue'

/**
 * Theme Management
 * ===============
 * Vuetify's useTheme composable provides access to the theme system
 * Allows runtime theme switching between light and dark modes
 */
const theme = useTheme()

// Computed property to check if dark mode is active
const isDark = computed(() => theme.global.current.value.dark)

// Toggle between light and dark themes
const toggleTheme = () => {
  theme.global.name.value = isDark.value ? 'light' : 'dark'
}

// Current year for copyright notice
const currentYear = new Date().getFullYear()
</script>

<style>
/**
 * Global Styles
 * =============
 * Minimal global styles - Vuetify handles most styling through props
 * These styles ensure consistent spacing and readability
 */

/* Ensure smooth scrolling behavior */
html {
  scroll-behavior: smooth;
}

/* Remove default margins from body */
body {
  margin: 0;
  padding: 0;
}
</style>
