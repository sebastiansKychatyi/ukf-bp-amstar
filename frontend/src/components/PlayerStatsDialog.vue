<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="900"
    scrollable
  >
    <v-card v-if="player">
      <!-- Header -->
      <v-card-title class="pa-6">
        <div class="d-flex align-center">
          <v-icon size="32" class="mr-3">mdi-chart-line</v-icon>
          <div>
            <div class="text-h5 font-weight-bold">
              {{ player.first_name }} {{ player.last_name }}
            </div>
            <div class="text-subtitle-2 text-medium-emphasis">
              Detailed Statistics
            </div>
          </div>
        </div>
        <v-btn
          icon="mdi-close"
          variant="text"
          position="absolute"
          location="top right"
          class="ma-2"
          @click="$emit('update:modelValue', false)"
        />
      </v-card-title>

      <v-divider />

      <!-- Loading State -->
      <v-card-text v-if="loading" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" />
        <p class="text-h6 mt-4">Loading statistics...</p>
      </v-card-text>

      <!-- Statistics Content -->
      <v-card-text v-else-if="statistics" class="pa-6">
        <!-- Overall Performance -->
        <div class="mb-6">
          <div class="text-h6 font-weight-bold mb-4">Overall Performance</div>
          <v-row dense>
            <v-col cols="12" md="4">
              <v-card variant="outlined">
                <v-card-text>
                  <div class="text-center">
                    <v-progress-circular
                      :model-value="statistics.skill_rating"
                      :size="120"
                      :width="12"
                      :color="getRatingColor(statistics.skill_rating)"
                    >
                      <div class="text-h4 font-weight-bold">
                        {{ statistics.skill_rating.toFixed(1) }}
                      </div>
                    </v-progress-circular>
                    <div class="text-subtitle-1 mt-3">Skill Rating</div>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>

            <v-col cols="12" md="8">
              <v-card variant="outlined">
                <v-card-text>
                  <v-row dense>
                    <v-col cols="6">
                      <div class="text-caption text-medium-emphasis">
                        Goals per Match
                      </div>
                      <div class="text-h5 font-weight-bold">
                        {{ statistics.lifetime_stats.goals_per_match.toFixed(2) }}
                      </div>
                    </v-col>
                    <v-col cols="6">
                      <div class="text-caption text-medium-emphasis">
                        Assists per Match
                      </div>
                      <div class="text-h5 font-weight-bold">
                        {{ statistics.lifetime_stats.assists_per_match.toFixed(2) }}
                      </div>
                    </v-col>
                    <v-col cols="6">
                      <div class="text-caption text-medium-emphasis">
                        Total Contributions
                      </div>
                      <div class="text-h5 font-weight-bold">
                        {{ statistics.lifetime_stats.goals + statistics.lifetime_stats.assists }}
                      </div>
                    </v-col>
                    <v-col cols="6">
                      <div class="text-caption text-medium-emphasis">
                        Clean Sheets
                      </div>
                      <div class="text-h5 font-weight-bold">
                        {{ statistics.lifetime_stats.clean_sheets }}
                      </div>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>
        </div>

        <!-- Lifetime Statistics -->
        <div class="mb-6">
          <div class="text-h6 font-weight-bold mb-4">Lifetime Statistics</div>
          <v-card variant="outlined">
            <v-card-text>
              <v-row dense>
                <v-col cols="6" sm="4" md="2">
                  <div class="stat-box">
                    <v-icon color="info" size="32">mdi-calendar</v-icon>
                    <div class="text-h5 font-weight-bold mt-2">
                      {{ statistics.lifetime_stats.matches_played }}
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      Matches
                    </div>
                  </div>
                </v-col>

                <v-col cols="6" sm="4" md="2">
                  <div class="stat-box">
                    <v-icon color="success" size="32">mdi-soccer</v-icon>
                    <div class="text-h5 font-weight-bold mt-2">
                      {{ statistics.lifetime_stats.goals }}
                    </div>
                    <div class="text-caption text-medium-emphasis">Goals</div>
                  </div>
                </v-col>

                <v-col cols="6" sm="4" md="2">
                  <div class="stat-box">
                    <v-icon color="info" size="32">
                      mdi-hand-pointing-right
                    </v-icon>
                    <div class="text-h5 font-weight-bold mt-2">
                      {{ statistics.lifetime_stats.assists }}
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      Assists
                    </div>
                  </div>
                </v-col>

                <v-col cols="6" sm="4" md="2">
                  <div class="stat-box">
                    <v-icon color="warning" size="32">mdi-card</v-icon>
                    <div class="text-h5 font-weight-bold mt-2">
                      {{ statistics.lifetime_stats.yellow_cards }}
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      Yellow
                    </div>
                  </div>
                </v-col>

                <v-col cols="6" sm="4" md="2">
                  <div class="stat-box">
                    <v-icon color="error" size="32">mdi-card</v-icon>
                    <div class="text-h5 font-weight-bold mt-2">
                      {{ statistics.lifetime_stats.red_cards }}
                    </div>
                    <div class="text-caption text-medium-emphasis">Red</div>
                  </div>
                </v-col>

                <v-col cols="6" sm="4" md="2">
                  <div class="stat-box">
                    <v-icon color="success" size="32">mdi-shield-check</v-icon>
                    <div class="text-h5 font-weight-bold mt-2">
                      {{ statistics.lifetime_stats.clean_sheets }}
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      Clean Sheets
                    </div>
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </div>

        <!-- Team Breakdown -->
        <div v-if="statistics.team_breakdown.length > 0">
          <div class="text-h6 font-weight-bold mb-4">Performance by Team</div>
          <v-data-table
            :headers="teamHeaders"
            :items="statistics.team_breakdown"
            :items-per-page="5"
            class="elevation-1"
          >
            <template #item.team_name="{ item }">
              <div class="d-flex align-center">
                <v-chip
                  :color="item.is_active ? 'success' : 'grey'"
                  variant="dot"
                  size="small"
                  class="mr-2"
                />
                <span class="font-weight-medium">{{ item.team_name }}</span>
              </div>
            </template>

            <template #item.goals="{ item }">
              <v-chip color="success" size="small" variant="flat">
                {{ item.goals }}
              </v-chip>
            </template>

            <template #item.assists="{ item }">
              <v-chip color="info" size="small" variant="flat">
                {{ item.assists }}
              </v-chip>
            </template>
          </v-data-table>
        </div>
      </v-card-text>

      <v-divider />

      <!-- Actions -->
      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn @click="$emit('update:modelValue', false)">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'
import { usePlayerStore } from '@/stores/player'

const props = defineProps({
  modelValue: Boolean,
  player: Object,
})

defineEmits(['update:modelValue'])

const playerStore = usePlayerStore()
const statistics = ref(null)
const loading = ref(false)

const teamHeaders = [
  { title: 'Team', key: 'team_name' },
  { title: 'Matches', key: 'matches_played' },
  { title: 'Goals', key: 'goals' },
  { title: 'Assists', key: 'assists' },
  { title: 'Yellow Cards', key: 'yellow_cards' },
  { title: 'Red Cards', key: 'red_cards' },
]

// Watch for dialog open and player change
watch(
  () => [props.modelValue, props.player?.id],
  async ([isOpen, playerId]) => {
    if (isOpen && playerId) {
      await loadStatistics(playerId)
    }
  },
  { immediate: true }
)

async function loadStatistics(playerId) {
  loading.value = true
  try {
    statistics.value = await playerStore.fetchPlayerStatistics(playerId)
  } catch (error) {
    console.error('Failed to load statistics:', error)
  } finally {
    loading.value = false
  }
}

function getRatingColor(rating) {
  if (rating >= 80) return 'success'
  if (rating >= 60) return 'info'
  if (rating >= 40) return 'warning'
  return 'error'
}
</script>

<style scoped>
.stat-box {
  text-align: center;
  padding: 16px;
  border-radius: 8px;
  transition: background-color 0.2s;
}

.stat-box:hover {
  background-color: rgba(var(--v-theme-primary), 0.05);
}
</style>
