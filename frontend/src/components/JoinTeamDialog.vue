<template>
  <v-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    max-width="600"
  >
    <v-card v-if="team">
      <!-- Header -->
      <v-card-title class="pa-6 bg-primary">
        <div class="text-h5 font-weight-bold text-white">
          <v-icon color="white" class="mr-2">mdi-account-plus</v-icon>
          Request to Join {{ team.name }}
        </div>
      </v-card-title>

      <v-divider />

      <!-- Content -->
      <v-card-text class="pa-6">
        <v-form ref="formRef" v-model="formValid" @submit.prevent="handleSubmit">
          <!-- Team Info -->
          <v-card variant="tonal" class="mb-4">
            <v-card-text>
              <div class="d-flex align-center">
                <v-avatar
                  :color="team.team_color || 'primary'"
                  size="64"
                  class="mr-4"
                >
                  <v-img v-if="team.logo_url" :src="team.logo_url" cover />
                  <v-icon v-else size="32" color="white">mdi-shield</v-icon>
                </v-avatar>
                <div>
                  <div class="text-h6 font-weight-bold">{{ team.name }}</div>
                  <div class="text-caption text-medium-emphasis">
                    {{ team.home_city }}
                  </div>
                  <div class="mt-1">
                    <v-chip
                      :color="getRatingColor(team.team_rating)"
                      size="small"
                      variant="flat"
                    >
                      {{ team.team_rating.toFixed(1) }} Rating
                    </v-chip>
                  </div>
                </div>
              </div>
            </v-card-text>
          </v-card>

          <!-- Introduction Message -->
          <div class="mb-4">
            <label class="text-subtitle-2 font-weight-bold mb-2 d-block">
              Introduction Message (Optional)
            </label>
            <v-textarea
              v-model="message"
              placeholder="Tell the team captain about yourself and why you want to join..."
              :rules="[rules.maxLength(500)]"
              counter="500"
              rows="4"
              variant="outlined"
              hint="Share your experience, position preferences, or availability"
              persistent-hint
            />
          </div>

          <!-- Info -->
          <v-alert type="info" variant="tonal" class="mb-4">
            <div class="text-body-2">
              <strong>What happens next?</strong>
              <ul class="mt-2">
                <li>Your request will be sent to the team captain</li>
                <li>You'll be notified when they review your request</li>
                <li>If approved, you'll become an active team member</li>
              </ul>
            </div>
          </v-alert>

          <!-- Error Alert -->
          <v-alert
            v-if="error"
            type="error"
            variant="tonal"
            closable
            class="mb-4"
            @click:close="error = null"
          >
            {{ error }}
          </v-alert>
        </v-form>
      </v-card-text>

      <v-divider />

      <!-- Actions -->
      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn
          @click="$emit('update:modelValue', false)"
          :disabled="loading"
        >
          Cancel
        </v-btn>
        <v-btn
          color="primary"
          :loading="loading"
          :disabled="!formValid || loading"
          @click="handleSubmit"
        >
          Send Request
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup>
import { ref } from 'vue'
import { useTeamStore } from '@/stores/team'

const props = defineProps({
  modelValue: Boolean,
  team: Object,
})

const emit = defineEmits(['update:modelValue', 'request-sent'])

const teamStore = useTeamStore()

// Form state
const formRef = ref(null)
const formValid = ref(true)
const message = ref('')
const loading = ref(false)
const error = ref(null)

// Validation rules
const rules = {
  maxLength: (max) => (v) => !v || v.length <= max || `Maximum ${max} characters`,
}

// Methods
async function handleSubmit() {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  loading.value = true
  error.value = null

  try {
    await teamStore.createJoinRequest(props.team.id, message.value)

    // Emit success event
    emit('request-sent')

    // Reset form
    message.value = ''
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to send join request'
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
