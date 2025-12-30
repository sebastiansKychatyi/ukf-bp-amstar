<template>
  <v-card
    :elevation="hover ? 8 : 2"
    :class="{ 'on-hover': hover }"
    class="player-card"
    @mouseenter="hover = true"
    @mouseleave="hover = false"
  >
    <!-- Player Header -->
    <v-card-title class="d-flex align-center pa-4">
      <v-avatar
        :color="getPositionColor(player.position)"
        size="56"
        class="mr-3"
      >
        <v-icon size="32" color="white">
          {{ getPositionIcon(player.position) }}
        </v-icon>
      </v-avatar>

      <div class="flex-grow-1">
        <div class="text-h6 font-weight-bold">
          {{ player.first_name }} {{ player.last_name }}
        </div>
        <div class="text-caption text-medium-emphasis">
          {{ player.position }}
        </div>
      </div>

      <!-- Rating Badge -->
      <v-chip
        :color="getRatingColor(player.skill_rating)"
        variant="flat"
        size="large"
        class="font-weight-bold"
      >
        {{ player.skill_rating.toFixed(1) }}
      </v-chip>
    </v-card-title>

    <v-divider />

    <!-- Player Statistics -->
    <v-card-text class="pa-4">
      <v-row dense>
        <!-- Goals -->
        <v-col cols="6" sm="3">
          <div class="text-center stat-item">
            <v-icon color="success" size="24">mdi-soccer</v-icon>
            <div class="text-h6 font-weight-bold mt-1">
              {{ player.total_goals }}
            </div>
            <div class="text-caption text-medium-emphasis">Goals</div>
          </div>
        </v-col>

        <!-- Assists -->
        <v-col cols="6" sm="3">
          <div class="text-center stat-item">
            <v-icon color="info" size="24">mdi-hand-pointing-right</v-icon>
            <div class="text-h6 font-weight-bold mt-1">
              {{ player.total_assists }}
            </div>
            <div class="text-caption text-medium-emphasis">Assists</div>
          </div>
        </v-col>

        <!-- Yellow Cards -->
        <v-col cols="6" sm="3">
          <div class="text-center stat-item">
            <v-icon color="warning" size="24">mdi-card</v-icon>
            <div class="text-h6 font-weight-bold mt-1">
              {{ player.total_yellow_cards }}
            </div>
            <div class="text-caption text-medium-emphasis">Yellow</div>
          </div>
        </v-col>

        <!-- Red Cards -->
        <v-col cols="6" sm="3">
          <div class="text-center stat-item">
            <v-icon color="error" size="24">mdi-card</v-icon>
            <div class="text-h6 font-weight-bold mt-1">
              {{ player.total_red_cards }}
            </div>
            <div class="text-caption text-medium-emphasis">Red</div>
          </div>
        </v-col>
      </v-row>

      <!-- Matches Played -->
      <v-row dense class="mt-2">
        <v-col cols="12">
          <div class="d-flex align-center justify-space-between">
            <span class="text-body-2 text-medium-emphasis">
              Matches Played
            </span>
            <span class="font-weight-bold">
              {{ player.total_matches_played }}
            </span>
          </div>
        </v-col>
      </v-row>

      <!-- Performance Metrics (if player has played matches) -->
      <v-row v-if="player.total_matches_played > 0" dense class="mt-2">
        <v-col cols="6">
          <div class="text-caption text-medium-emphasis">Goals/Match</div>
          <div class="font-weight-bold">
            {{ (player.total_goals / player.total_matches_played).toFixed(2) }}
          </div>
        </v-col>
        <v-col cols="6">
          <div class="text-caption text-medium-emphasis">Assists/Match</div>
          <div class="font-weight-bold">
            {{ (player.total_assists / player.total_matches_played).toFixed(2) }}
          </div>
        </v-col>
      </v-row>
    </v-card-text>

    <v-divider v-if="showActions" />

    <!-- Card Actions -->
    <v-card-actions v-if="showActions" class="pa-3">
      <v-btn
        variant="text"
        color="primary"
        prepend-icon="mdi-account-details"
        @click="$emit('view-details', player)"
      >
        View Profile
      </v-btn>
      <v-spacer />
      <v-btn
        variant="text"
        color="secondary"
        prepend-icon="mdi-chart-line"
        @click="$emit('view-stats', player)"
      >
        Statistics
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  player: {
    type: Object,
    required: true,
  },
  showActions: {
    type: Boolean,
    default: true,
  },
})

defineEmits(['view-details', 'view-stats'])

const hover = ref(false)

function getPositionIcon(position) {
  const icons = {
    GOALKEEPER: 'mdi-shield-account',
    DEFENDER: 'mdi-shield',
    MIDFIELDER: 'mdi-run',
    FORWARD: 'mdi-soccer',
  }
  return icons[position] || 'mdi-account'
}

function getPositionColor(position) {
  const colors = {
    GOALKEEPER: '#F59E0B', // Orange
    DEFENDER: '#3B82F6', // Blue
    MIDFIELDER: '#10B981', // Green
    FORWARD: '#EF4444', // Red
  }
  return colors[position] || 'grey'
}

function getRatingColor(rating) {
  if (rating >= 80) return 'success'
  if (rating >= 60) return 'info'
  if (rating >= 40) return 'warning'
  return 'error'
}
</script>

<style scoped>
.player-card {
  transition: all 0.3s ease;
}

.player-card.on-hover {
  transform: translateY(-4px);
}

.stat-item {
  padding: 8px;
  border-radius: 8px;
  transition: background-color 0.2s;
}

.stat-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
}
</style>
