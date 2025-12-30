<template>
  <v-container fluid class="pa-6">
    <v-row justify="center">
      <v-col cols="12" md="8" lg="6">
        <!-- Page Header -->
        <div class="text-center mb-8">
          <v-icon size="64" color="primary">mdi-shield-plus</v-icon>
          <h1 class="text-h4 font-weight-bold mt-4 mb-2">Create Your Team</h1>
          <p class="text-medium-emphasis">
            Build your squad and start competing
          </p>
        </div>

        <!-- Create Team Form -->
        <v-card elevation="4">
          <v-card-text class="pa-6">
            <v-form ref="formRef" v-model="formValid" @submit.prevent="handleSubmit">
              <!-- Team Name -->
              <div class="mb-4">
                <label class="text-subtitle-2 font-weight-bold mb-2 d-block">
                  Team Name *
                </label>
                <v-text-field
                  v-model="form.name"
                  placeholder="e.g., Thunder FC"
                  :rules="[rules.required, rules.minLength(3), rules.maxLength(100)]"
                  counter="100"
                  prepend-inner-icon="mdi-shield"
                />
              </div>

              <!-- Short Name -->
              <div class="mb-4">
                <label class="text-subtitle-2 font-weight-bold mb-2 d-block">
                  Short Name (Abbreviation)
                </label>
                <v-text-field
                  v-model="form.short_name"
                  placeholder="e.g., TFC"
                  :rules="[rules.maxLength(20)]"
                  counter="20"
                  prepend-inner-icon="mdi-text-short"
                />
              </div>

              <!-- Home City -->
              <div class="mb-4">
                <label class="text-subtitle-2 font-weight-bold mb-2 d-block">
                  Home City
                </label>
                <v-text-field
                  v-model="form.home_city"
                  placeholder="e.g., Prague"
                  :rules="[rules.maxLength(100)]"
                  counter="100"
                  prepend-inner-icon="mdi-map-marker"
                />
              </div>

              <v-row>
                <!-- Founded Date -->
                <v-col cols="12" sm="6">
                  <label class="text-subtitle-2 font-weight-bold mb-2 d-block">
                    Founded Date
                  </label>
                  <v-text-field
                    v-model="form.founded_date"
                    type="date"
                    prepend-inner-icon="mdi-calendar"
                  />
                </v-col>

                <!-- Team Color -->
                <v-col cols="12" sm="6">
                  <label class="text-subtitle-2 font-weight-bold mb-2 d-block">
                    Team Color
                  </label>
                  <v-text-field
                    v-model="form.team_color"
                    type="color"
                    prepend-inner-icon="mdi-palette"
                    :rules="[rules.hexColor]"
                  />
                </v-col>
              </v-row>

              <!-- Team Logo -->
              <div class="mb-4">
                <label class="text-subtitle-2 font-weight-bold mb-2 d-block">
                  Team Logo
                </label>
                <v-file-input
                  v-model="logoFile"
                  accept="image/*"
                  prepend-icon=""
                  prepend-inner-icon="mdi-image"
                  placeholder="Upload team logo"
                  :rules="[rules.fileSize]"
                  show-size
                  @change="handleLogoPreview"
                />

                <!-- Logo Preview -->
                <v-card
                  v-if="logoPreview"
                  variant="outlined"
                  class="mt-3 pa-4"
                >
                  <div class="text-center">
                    <v-img
                      :src="logoPreview"
                      max-width="200"
                      max-height="200"
                      contain
                      class="mx-auto"
                    />
                  </div>
                </v-card>
              </div>

              <!-- Max Players -->
              <div class="mb-4">
                <label class="text-subtitle-2 font-weight-bold mb-2 d-block">
                  Maximum Players (11-50)
                </label>
                <v-slider
                  v-model="form.max_players"
                  :min="11"
                  :max="50"
                  :step="1"
                  thumb-label
                  prepend-icon="mdi-account-multiple"
                  show-ticks
                />
              </div>

              <!-- Is Recruiting -->
              <div class="mb-4">
                <v-switch
                  v-model="form.is_recruiting"
                  color="primary"
                  label="Currently Recruiting Players"
                  hint="Allow players to send join requests"
                  persistent-hint
                />
              </div>

              <!-- Description -->
              <div class="mb-4">
                <label class="text-subtitle-2 font-weight-bold mb-2 d-block">
                  Team Description
                </label>
                <v-textarea
                  v-model="form.description"
                  placeholder="Tell others about your team..."
                  :rules="[rules.maxLength(500)]"
                  counter="500"
                  rows="4"
                  prepend-inner-icon="mdi-text"
                />
              </div>

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

              <!-- Submit Buttons -->
              <div class="d-flex ga-3">
                <v-btn
                  type="submit"
                  color="primary"
                  size="large"
                  :loading="loading"
                  :disabled="!formValid || loading"
                  prepend-icon="mdi-check"
                  block
                >
                  Create Team
                </v-btn>
              </div>
            </v-form>
          </v-card-text>
        </v-card>

        <!-- Info Card -->
        <v-card variant="tonal" color="info" class="mt-6">
          <v-card-text>
            <div class="d-flex align-start">
              <v-icon size="24" class="mr-3">mdi-information</v-icon>
              <div>
                <div class="font-weight-bold mb-2">What happens next?</div>
                <ul class="text-body-2">
                  <li>You'll be automatically assigned as team captain</li>
                  <li>You can invite players or accept join requests</li>
                  <li>Customize your team profile and upload a logo</li>
                  <li>Start challenging other teams!</li>
                </ul>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Success Dialog -->
    <v-dialog v-model="showSuccessDialog" max-width="500" persistent>
      <v-card>
        <v-card-text class="text-center pa-8">
          <v-icon size="80" color="success">mdi-check-circle</v-icon>
          <h2 class="text-h5 font-weight-bold mt-4 mb-2">
            Team Created Successfully!
          </h2>
          <p class="text-medium-emphasis mb-4">
            {{ form.name }} is ready to compete
          </p>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-btn
            color="primary"
            variant="flat"
            block
            size="large"
            @click="goToTeamPage"
          >
            View My Team
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useTeamStore } from '@/stores/team'

const router = useRouter()
const teamStore = useTeamStore()

// Form state
const formRef = ref(null)
const formValid = ref(false)
const loading = ref(false)
const error = ref(null)
const showSuccessDialog = ref(false)
const createdTeamId = ref(null)

// Logo upload
const logoFile = ref([])
const logoPreview = ref(null)

// Form data
const form = reactive({
  name: '',
  short_name: '',
  home_city: '',
  founded_date: '',
  team_color: '#1E40AF',
  max_players: 25,
  is_recruiting: true,
  description: '',
  captain_id: 'current-user-id', // Get from auth store
})

// Validation rules
const rules = {
  required: (v) => !!v || 'This field is required',
  minLength: (min) => (v) => !v || v.length >= min || `Minimum ${min} characters`,
  maxLength: (max) => (v) => !v || v.length <= max || `Maximum ${max} characters`,
  hexColor: (v) => !v || /^#[0-9A-F]{6}$/i.test(v) || 'Invalid color format',
  fileSize: (files) => {
    if (!files || files.length === 0) return true
    const file = Array.isArray(files) ? files[0] : files
    return !file || file.size < 5000000 || 'File size must be less than 5MB'
  },
}

// Methods
function handleLogoPreview(event) {
  const file = Array.isArray(logoFile.value) ? logoFile.value[0] : logoFile.value

  if (file) {
    const reader = new FileReader()
    reader.onload = (e) => {
      logoPreview.value = e.target.result
    }
    reader.readAsDataURL(file)
  } else {
    logoPreview.value = null
  }
}

async function handleSubmit() {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  loading.value = true
  error.value = null

  try {
    // Create team
    const teamData = {
      ...form,
      founded_date: form.founded_date || undefined,
    }

    const newTeam = await teamStore.createTeam(teamData)
    createdTeamId.value = newTeam.id

    // Upload logo if provided
    if (logoFile.value && logoFile.value.length > 0) {
      const file = Array.isArray(logoFile.value) ? logoFile.value[0] : logoFile.value
      await teamStore.uploadTeamLogo(newTeam.id, file)
    }

    // Show success dialog
    showSuccessDialog.value = true
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to create team'
  } finally {
    loading.value = false
  }
}

function goToTeamPage() {
  router.push(`/teams/${createdTeamId.value}`)
}
</script>

<style scoped>
label {
  color: rgb(var(--v-theme-on-surface));
}
</style>
