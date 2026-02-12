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
          prepend-icon="mdi-account-circle"
          title="Profile"
          to="/profile"
          @click="drawer = false"
        />
      </v-list>

      <v-divider />

      <!-- Theme Toggle in Drawer -->
      <v-list density="compact">
        <v-list-item
          :prepend-icon="isDark ? 'mdi-white-balance-sunny' : 'mdi-weather-night'"
          :title="isDark ? 'Light Mode' : 'Dark Mode'"
          @click="toggleTheme"
        />
      </v-list>
    </v-navigation-drawer>

    <!-- App Bar (Navigation Header) -->
    <v-app-bar
      color="primary"
      elevation="1"
      app
    >
      <!-- Hamburger Menu (Mobile Only) -->
      <v-app-bar-nav-icon
        @click="drawer = !drawer"
        class="d-md-none"
      />

      <!-- Logo and Title -->
      <v-app-bar-title class="font-weight-bold">
        <v-icon icon="mdi-soccer" class="mr-2" />
        <span class="d-none d-sm-inline">AmStar Football</span>
        <span class="d-inline d-sm-none">AmStar</span>
      </v-app-bar-title>

      <v-spacer />

      <!-- Desktop Navigation Links (Hidden on Mobile) -->
      <template v-if="$vuetify.display.mdAndUp">
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

        <v-btn variant="text" to="/tournaments">
          <v-icon start>mdi-tournament</v-icon>
          Tournaments
        </v-btn>

        <v-btn variant="text" to="/profile">
          <v-icon start>mdi-account-circle</v-icon>
          Profile
        </v-btn>

        <!-- Theme Toggle Button (Desktop) -->
        <v-btn
          icon
          @click="toggleTheme"
          class="ml-2"
        >
          <v-icon>{{ isDark ? 'mdi-white-balance-sunny' : 'mdi-weather-night' }}</v-icon>
        </v-btn>
      </template>

      <!-- Mobile: Show only theme toggle icon -->
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
          <span v-if="$vuetify.display.smAndUp"> - Amateur Football Management System</span>
        </p>
      </v-container>
    </v-footer>
  </v-app>
</template>

<script setup lang="ts">
import { useTheme, useDisplay } from 'vuetify'
import { ref, computed } from 'vue'


const theme = useTheme()

// Computed property to check if dark mode is active
const isDark = computed(() => theme.global.current.value.dark)

// Toggle between light and dark themes
const toggleTheme = () => {
  theme.global.name.value = isDark.value ? 'light' : 'dark'
}


const drawer = ref(false)

const currentYear = new Date().getFullYear()
</script>

<style>

html {
  scroll-behavior: smooth;
}

/* Remove default margins from body */
body {
  margin: 0;
  padding: 0;
}


</style>
