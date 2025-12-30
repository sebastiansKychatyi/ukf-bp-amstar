<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="700"
    scrollable
  >
    <v-card v-if="player">
      <!-- Header -->
      <v-card-title class="d-flex align-center pa-6 bg-primary">
        <v-avatar
          :color="getPositionColor(player.position)"
          size="64"
          class="mr-4"
        >
          <v-icon size="40" color="white">
            {{ getPositionIcon(player.position) }}
          </v-icon>
        </v-avatar>

        <div class="flex-grow-1">
          <div class="text-h5 font-weight-bold text-white">
            {{ player.first_name }} {{ player.last_name }}
          </div>
          <div class="text-subtitle-1 text-white opacity-90">
            {{ player.position }}
          </div>
        </div>

        <v-btn
          icon="mdi-close"
          variant="text"
          color="white"
          @click="$emit('update:modelValue', false)"
        />
      </v-card-title>

      <v-divider />

      <!-- Content -->
      <v-card-text class="pa-6">
        <!-- Rating Section -->
        <div class="mb-6">
          <div class="text-h6 font-weight-bold mb-3">Player Rating</div>
          <v-card variant="tonal" :color="getRatingColor(player.skill_rating)">
            <v-card-text class="text-center py-6">
              <div class="text-h2 font-weight-bold">
                {{ player.skill_rating.toFixed(1) }}
              </div>
              <div class="text-subtitle-1 mt-2">
                {{ getRatingLabel(player.skill_rating) }}
              </div>
            </v-card-text>
          </v-card>
        </div>

        <!-- Personal Information -->
        <div class="mb-6">
          <div class="text-h6 font-weight-bold mb-3">
            Personal Information
          </div>
          <v-list lines="two">
            <v-list-item>
              <template #prepend>
                <v-icon>mdi-email</v-icon>
              </template>
              <v-list-item-title>Email</v-list-item-title>
              <v-list-item-subtitle>{{ player.email }}</v-list-item-subtitle>
            </v-list-item>

            <v-list-item v-if="player.phone">
              <template #prepend>
                <v-icon>mdi-phone</v-icon>
              </template>
              <v-list-item-title>Phone</v-list-item-title>
              <v-list-item-subtitle>{{ player.phone }}</v-list-item-subtitle>
            </v-list-item>

            <v-list-item>
              <template #prepend>
                <v-icon>mdi-cake-variant</v-icon>
              </template>
              <v-list-item-title>Date of Birth</v-list-item-title>
              <v-list-item-subtitle>
                {{ formatDate(player.date_of_birth) }}
                ({{ calculateAge(player.date_of_birth) }} years)
              </v-list-item-subtitle>
            </v-list-item>

            <v-list-item v-if="player.preferred_foot">
              <template #prepend>
                <v-icon>mdi-foot-print</v-icon>
              </template>
              <v-list-item-title>Preferred Foot</v-list-item-title>
              <v-list-item-subtitle>
                {{ player.preferred_foot }}
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </div>

        <!-- Bio -->
        <div v-if="player.bio" class="mb-6">
          <div class="text-h6 font-weight-bold mb-3">About</div>
          <p class="text-body-1">{{ player.bio }}</p>
        </div>

        <!-- Statistics Summary -->
        <div class="mb-6">
          <div class="text-h6 font-weight-bold mb-3">Career Statistics</div>
          <v-row dense>
            <v-col cols="6" sm="3">
              <v-card variant="tonal" color="info">
                <v-card-text class="text-center">
                  <div class="text-h4 font-weight-bold">
                    {{ player.total_matches_played }}
                  </div>
                  <div class="text-caption">Matches</div>
                </v-card-text>
              </v-card>
            </v-col>

            <v-col cols="6" sm="3">
              <v-card variant="tonal" color="success">
                <v-card-text class="text-center">
                  <div class="text-h4 font-weight-bold">
                    {{ player.total_goals }}
                  </div>
                  <div class="text-caption">Goals</div>
                </v-card-text>
              </v-card>
            </v-col>

            <v-col cols="6" sm="3">
              <v-card variant="tonal" color="info">
                <v-card-text class="text-center">
                  <div class="text-h4 font-weight-bold">
                    {{ player.total_assists }}
                  </div>
                  <div class="text-caption">Assists</div>
                </v-card-text>
              </v-card>
            </v-col>

            <v-col cols="6" sm="3">
              <v-card variant="tonal" color="warning">
                <v-card-text class="text-center">
                  <div class="text-h4 font-weight-bold">
                    {{ player.total_yellow_cards + player.total_red_cards }}
                  </div>
                  <div class="text-caption">Cards</div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </div>

        <!-- Member Since -->
        <div class="text-center text-caption text-medium-emphasis">
          Member since {{ formatDate(player.created_at) }}
        </div>
      </v-card-text>

      <v-divider />

      <!-- Actions -->
      <v-card-actions class="pa-4">
        <v-btn
          color="primary"
          variant="flat"
          prepend-icon="mdi-chart-line"
          @click="$emit('view-stats', player)"
        >
          View Full Statistics
        </v-btn>
        <v-spacer />
        <v-btn @click="$emit('update:modelValue', false)">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
defineProps({
  modelValue: Boolean,
  player: Object,
})

defineEmits(['update:modelValue', 'view-stats'])

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
    GOALKEEPER: '#F59E0B',
    DEFENDER: '#3B82F6',
    MIDFIELDER: '#10B981',
    FORWARD: '#EF4444',
  }
  return colors[position] || 'grey'
}

function getRatingColor(rating) {
  if (rating >= 80) return 'success'
  if (rating >= 60) return 'info'
  if (rating >= 40) return 'warning'
  return 'error'
}

function getRatingLabel(rating) {
  if (rating >= 86) return 'Outstanding'
  if (rating >= 76) return 'Excellent'
  if (rating >= 61) return 'Very Good'
  if (rating >= 41) return 'Average'
  if (rating >= 21) return 'Developing'
  return 'Beginner'
}

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function calculateAge(dateOfBirth) {
  const today = new Date()
  const birthDate = new Date(dateOfBirth)
  let age = today.getFullYear() - birthDate.getFullYear()
  const m = today.getMonth() - birthDate.getMonth()
  if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
    age--
  }
  return age
}
</script>
