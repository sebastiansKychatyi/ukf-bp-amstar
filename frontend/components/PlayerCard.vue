<template>
  <!--
    PlayerCard Component
    ===================
    Reusable card component for displaying player information

    Props:
    - player: Object containing player data (name, position, rating, etc.)

    Features:
    - Clean, minimalist design
    - Rating visualization with color coding
    - Responsive layout
    - Action button for viewing details
  -->
  <v-card
    elevation="2"
    rounded="lg"
    class="player-card"
  >
    <!-- Player Avatar/Icon -->
    <div class="d-flex justify-center pt-6">
      <v-avatar
        size="80"
        color="primary"
      >
        <v-icon
          icon="mdi-account"
          size="40"
          color="white"
        />
      </v-avatar>
    </div>

    <!-- Player Information -->
    <v-card-title class="text-center pb-2">
      {{ player.name }}
    </v-card-title>

    <v-card-subtitle class="text-center">
      {{ player.position }}
    </v-card-subtitle>

    <!-- Player Rating -->
    <v-card-text class="text-center">
      <v-chip
        :color="getRatingColor(player.rating)"
        size="large"
        class="font-weight-bold"
      >
        <v-icon start>mdi-star</v-icon>
        {{ player.rating }} Rating
      </v-chip>
    </v-card-text>

    <!-- Actions -->
    <v-card-actions class="justify-center pb-4">
      <v-btn
        color="primary"
        variant="outlined"
        @click="$emit('view-details', player)"
      >
        View Details
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
/**
 * Component Props Definition
 * ==========================
 * Defines the expected player object structure
 */
interface Player {
  id?: number | string
  name: string
  position: string
  rating: number
}

defineProps<{
  player: Player
}>()

/**
 * Component Events
 * ===============
 * Emits 'view-details' event when user clicks the action button
 */
defineEmits<{
  'view-details': [player: Player]
}>()

/**
 * Rating Color Logic
 * ==================
 * Returns appropriate color based on rating value
 * - Excellent (4.5+): Success green
 * - Good (4.0-4.4): Info blue
 * - Average (3.5-3.9): Warning amber
 * - Below Average (<3.5): Error red
 */
const getRatingColor = (rating: number): string => {
  if (rating >= 4.5) return 'success'
  if (rating >= 4.0) return 'info'
  if (rating >= 3.5) return 'warning'
  return 'error'
}
</script>

<style scoped>
/**
 * Component-Specific Styles
 * =========================
 * Minimal scoped styles - Vuetify props handle most styling
 */

.player-card {
  /* Ensures cards have consistent height in grid layouts */
  height: 100%;
  transition: transform 0.2s ease-in-out;
}

.player-card:hover {
  /* Subtle hover effect for better UX */
  transform: translateY(-4px);
}
</style>
