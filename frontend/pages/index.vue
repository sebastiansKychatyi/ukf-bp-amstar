<template>
  <!--
    Home Page
    =========
    Landing page for the AmStar Football Platform

    Features:
    - Clean, minimalist hero section
    - Quick stats overview
    - Call-to-action buttons
    - System status indicator
  -->
  <v-container class="py-12">
    <!-- Hero Section -->
    <v-row justify="center" class="mb-12">
      <v-col cols="12" md="8" class="text-center">
        <v-icon icon="mdi-soccer" size="80" color="primary" class="mb-4" />

        <h1 class="text-h2 font-weight-bold mb-4">
          Welcome to AmStar
        </h1>

        <p class="text-h5 text-medium-emphasis mb-6">
          Amateur Football Platform
        </p>

        <p class="text-body-1 text-medium-emphasis mb-8">
          Connect with teams, organize challenges, and track your performance
          in the amateur football community.
        </p>

        <!-- Call-to-Action Buttons -->
        <div class="d-flex justify-center gap-4 flex-wrap">
          <v-btn
            color="primary"
            size="large"
            to="/teams"
          >
            <v-icon start>mdi-shield-account</v-icon>
            Browse Teams
          </v-btn>

          <v-btn
            color="secondary"
            size="large"
            variant="outlined"
            to="/challenges"
          >
            <v-icon start>mdi-sword-cross</v-icon>
            Challenges
          </v-btn>

          <v-btn
            color="success"
            size="large"
            variant="outlined"
            to="/leaderboard"
          >
            <v-icon start>mdi-trophy</v-icon>
            Leaderboard
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Platform Statistics -->
    <v-row class="mb-12">
      <v-col cols="12">
        <h2 class="text-h4 font-weight-bold text-center mb-6">
          Platform Statistics
        </h2>
      </v-col>

      <!-- Stat Cards -->
      <v-col cols="12" sm="6" md="3">
        <v-card class="text-center pa-6" color="primary" dark>
          <v-icon icon="mdi-account-group" size="48" class="mb-3" />
          <div class="text-h4 font-weight-bold mb-1">1,234</div>
          <div class="text-body-1">Players</div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="text-center pa-6" color="secondary" dark>
          <v-icon icon="mdi-shield-account" size="48" class="mb-3" />
          <div class="text-h4 font-weight-bold mb-1">456</div>
          <div class="text-body-1">Teams</div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="text-center pa-6" color="success" dark>
          <v-icon icon="mdi-trophy" size="48" class="mb-3" />
          <div class="text-h4 font-weight-bold mb-1">789</div>
          <div class="text-body-1">Matches</div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="text-center pa-6" color="info" dark>
          <v-icon icon="mdi-calendar-check" size="48" class="mb-3" />
          <div class="text-h4 font-weight-bold mb-1">321</div>
          <div class="text-body-1">Challenges</div>
        </v-card>
      </v-col>
    </v-row>

    <!-- System Status -->
    <v-row justify="center">
      <v-col cols="12" md="6">
        <v-card elevation="2">
          <v-card-title class="text-center">
            <v-icon icon="mdi-server-network" class="mr-2" />
            System Status
          </v-card-title>

          <v-card-text>
            <div class="d-flex flex-column gap-3">
              <!-- Frontend Status -->
              <div class="d-flex align-center justify-space-between">
                <span class="text-body-1">Frontend</span>
                <v-chip color="success" size="small">
                  <v-icon start>mdi-check-circle</v-icon>
                  Running
                </v-chip>
              </div>

              <!-- Backend Status -->
              <div class="d-flex align-center justify-space-between">
                <span class="text-body-1">Backend API</span>
                <v-chip color="success" size="small">
                  <v-icon start>mdi-check-circle</v-icon>
                  Connected
                </v-chip>
              </div>

              <!-- Database Status -->
              <div class="d-flex align-center justify-space-between">
                <span class="text-body-1">Database</span>
                <v-chip color="success" size="small">
                  <v-icon start>mdi-check-circle</v-icon>
                  Active
                </v-chip>
              </div>
            </div>
          </v-card-text>

          <v-card-actions class="justify-center">
            <v-btn
              href="http://localhost:8000/docs"
              target="_blank"
              color="primary"
              variant="text"
              prepend-icon="mdi-api"
            >
              View API Documentation
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
/**
 * Home Page Logic
 * ===============
 * This page is primarily static content with no complex state management
 * Statistics are hardcoded for now - replace with API calls in production
 */

// TODO: Fetch real-time statistics from backend API
// Example:
// const stats = await $fetch('/api/v1/statistics')
</script>

<style scoped>
/**
 * Page-Specific Styles
 * ====================
 * Minimal styles - Vuetify utility classes handle most layout
 */

/* Add spacing between buttons in the CTA section */
.gap-4 {
  gap: 1rem;
}

/* Ensure gap utility works in flex containers */
.gap-3 {
  gap: 0.75rem;
}
</style>
