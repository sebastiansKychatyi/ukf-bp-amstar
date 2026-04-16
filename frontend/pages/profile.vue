<template>
  <v-container fluid class="pa-0">
    <!-- Profile Header Card -->
    <v-card elevation="0" rounded="0" color="primary" dark class="mb-4">
      <v-sheet color="secondary" height="100" class="d-flex align-end">
        <v-container>
          <v-avatar
            :size="$vuetify.display.xs ? 80 : 120"
            color="white"
            class="elevation-4"
            style="margin-bottom: -40px"
          >
            <span
              :class="$vuetify.display.xs ? 'text-h5' : 'text-h3'"
              class="primary--text font-weight-bold"
            >
              {{ initials }}
            </span>
          </v-avatar>
        </v-container>
      </v-sheet>

      <v-card-text class="pt-12">
        <v-container>
          <v-row align="center">
            <v-col cols="12" sm="8">
              <h1 :class="$vuetify.display.xs ? 'text-h5' : 'text-h4'" class="font-weight-bold mb-1">
                {{ user?.full_name || user?.username }}
              </h1>
              <p class="text-subtitle-1 mb-2">@{{ user?.username }}</p>
              <v-chip v-if="user?.is_active" color="success" size="small" prepend-icon="mdi-check-circle">
                Active Account
              </v-chip>
            </v-col>

            <v-col cols="12" sm="4" class="text-sm-right">
              <v-btn
                color="error"
                variant="elevated"
                prepend-icon="mdi-logout"
                :block="$vuetify.display.xs"
                @click="handleLogout"
              >
                Logout
              </v-btn>
            </v-col>
          </v-row>
        </v-container>
      </v-card-text>
    </v-card>

    <!-- Main Content Area -->
    <v-container>
      <v-row>
        <!-- Account Information (Left Column) -->
        <v-col cols="12" md="8">
          <v-card elevation="2" rounded="lg">
            <v-card-title class="text-h5 font-weight-bold">
              <v-icon start size="small">mdi-account-details</v-icon>
              Account Information
            </v-card-title>
            <v-divider />

            <v-card-text>
              <v-list lines="two" density="compact">
                <v-list-item>
                  <template #prepend>
                    <v-icon color="primary" size="small">mdi-account</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-medium-emphasis">Full Name</v-list-item-title>
                  <v-list-item-subtitle class="text-body-1 font-weight-medium">
                    {{ user?.full_name || 'Not set' }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-divider inset />

                <v-list-item>
                  <template #prepend>
                    <v-icon color="primary" size="small">mdi-at</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-medium-emphasis">Username</v-list-item-title>
                  <v-list-item-subtitle class="text-body-1 font-weight-medium">
                    {{ user?.username }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-divider inset />

                <v-list-item>
                  <template #prepend>
                    <v-icon color="primary" size="small">mdi-email</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-medium-emphasis">Email Address</v-list-item-title>
                  <v-list-item-subtitle class="text-body-1 font-weight-medium">
                    {{ user?.email }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-divider inset />

                <v-list-item>
                  <template #prepend>
                    <v-icon color="primary" size="small">mdi-shield-account</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-medium-emphasis">Role</v-list-item-title>
                  <v-list-item-subtitle class="text-body-1 font-weight-medium">
                    {{ user?.role }}
                    <v-chip
                      v-if="playerProfile?.team_name"
                      size="x-small"
                      variant="outlined"
                      class="ml-2"
                    >
                      <v-icon start size="x-small">mdi-shield-half-full</v-icon>
                      {{ playerProfile.team_name }}
                    </v-chip>
                  </v-list-item-subtitle>
                </v-list-item>

                <v-divider inset />

                <v-list-item>
                  <template #prepend>
                    <v-icon color="primary" size="small">mdi-identifier</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-medium-emphasis">User ID</v-list-item-title>
                  <v-list-item-subtitle class="text-body-1 font-weight-medium font-mono">
                    #{{ user?.id }}
                  </v-list-item-subtitle>
                </v-list-item>

                <v-divider inset />

                <v-list-item>
                  <template #prepend>
                    <v-icon color="primary" size="small">mdi-calendar-check</v-icon>
                  </template>
                  <v-list-item-title class="text-caption text-medium-emphasis">Member Since</v-list-item-title>
                  <v-list-item-subtitle class="text-body-1 font-weight-medium">
                    {{ formatDate(user?.created_at) }}
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Sidebar (Right Column) -->
        <v-col cols="12" md="4">
          <!-- Account Status Card -->
          <v-card elevation="2" rounded="lg" class="mb-4">
            <v-card-title class="text-h6 font-weight-bold">
              <v-icon start size="small">mdi-shield-account</v-icon>
              Account Status
            </v-card-title>
            <v-divider />

            <v-card-text>
              <v-list density="compact">
                <v-list-item>
                  <v-list-item-title class="text-caption text-medium-emphasis">Account Type</v-list-item-title>
                  <template #append>
                    <v-chip :color="user?.is_superuser ? 'error' : 'primary'" size="small" variant="flat">
                      {{ user?.is_superuser ? 'Admin' : 'User' }}
                    </v-chip>
                  </template>
                </v-list-item>

                <v-divider />

                <v-list-item>
                  <v-list-item-title class="text-caption text-medium-emphasis">Status</v-list-item-title>
                  <template #append>
                    <v-chip :color="user?.is_active ? 'success' : 'error'" size="small" variant="flat">
                      {{ user?.is_active ? 'Active' : 'Inactive' }}
                    </v-chip>
                  </template>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>

          <!-- Player Statistics Card -->
          <v-card elevation="2" rounded="lg" class="mb-4">
            <v-card-title class="text-h6 font-weight-bold">
              <v-icon start size="small">mdi-chart-bar</v-icon>
              Player Stats
            </v-card-title>
            <v-divider />

            <v-card-text>
              <v-row dense>
                <!-- Goals -->
                <v-col cols="6">
                  <v-card color="primary" dark class="text-center pa-3">
                    <v-icon size="large" class="mb-2">mdi-soccer</v-icon>
                    <div class="text-h4 font-weight-bold">
                      <v-progress-circular v-if="statsLoading" indeterminate size="28" width="3" />
                      <span v-else>{{ playerProfile?.statistics?.goals ?? 0 }}</span>
                    </div>
                    <div class="text-caption">Goals</div>
                  </v-card>
                </v-col>

                <!-- Matches -->
                <v-col cols="6">
                  <v-card color="secondary" dark class="text-center pa-3">
                    <v-icon size="large" class="mb-2">mdi-trophy</v-icon>
                    <div class="text-h4 font-weight-bold">
                      <v-progress-circular v-if="statsLoading" indeterminate size="28" width="3" />
                      <span v-else>{{ playerProfile?.statistics?.matches_played ?? 0 }}</span>
                    </div>
                    <div class="text-caption">Matches</div>
                  </v-card>
                </v-col>

                <!-- Team ELO or Assists fallback -->
                <v-col cols="12">
                  <v-card color="success" dark class="text-center pa-3">
                    <v-icon size="large" class="mb-2">mdi-star</v-icon>
                    <div class="text-h4 font-weight-bold">
                      <v-progress-circular
                        v-if="statsLoading || teamLoading"
                        indeterminate size="28" width="3"
                      />
                      <span v-else>{{ myTeam?.rating_score ?? playerProfile?.statistics?.assists ?? 0 }}</span>
                    </div>
                    <div class="text-caption">{{ myTeam ? 'Team ELO' : 'Assists' }}</div>
                  </v-card>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>

          <!-- Quick Actions Card -->
          <v-card elevation="2" rounded="lg">
            <v-card-title class="text-h6 font-weight-bold">
              <v-icon start size="small">mdi-lightning-bolt</v-icon>
              Quick Actions
            </v-card-title>
            <v-divider />

            <v-list density="compact">
              <v-list-item
                prepend-icon="mdi-account-edit"
                title="Edit Profile"
                subtitle="Update your information"
                link
                @click="openEditProfile"
              />
              <v-divider />

              <v-list-item
                prepend-icon="mdi-lock-reset"
                title="Change Password"
                subtitle="Secure your account"
                link
                @click="showPasswordDialog = true"
              />
              <v-divider />

              <v-list-item
                prepend-icon="mdi-bell-outline"
                title="Notifications"
                subtitle="View your notifications"
                link
                to="/dashboard"
              />
            </v-list>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </v-container>

  <!-- Edit Profile Dialog -->
  <v-dialog v-model="showEditDialog" max-width="480" persistent>
    <v-card>
      <v-card-title>
        <v-icon class="mr-2">mdi-account-edit</v-icon>
        Edit Profile
      </v-card-title>
      <v-card-text>
        <v-text-field
          v-model="editForm.full_name"
          label="Full Name"
          variant="outlined"
          class="mb-3"
          prepend-inner-icon="mdi-account"
          clearable
        />
        <v-text-field
          v-model="editForm.email"
          label="Email Address"
          type="email"
          variant="outlined"
          prepend-inner-icon="mdi-email"
        />
        <v-alert v-if="editError" type="error" density="compact" class="mt-3">
          {{ editError }}
        </v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="closeEditDialog">Cancel</v-btn>
        <v-btn color="primary" variant="flat" :loading="editSaving" @click="saveProfile">
          Save Changes
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Change Password Dialog -->
  <v-dialog v-model="showPasswordDialog" max-width="480" persistent>
    <v-card>
      <v-card-title>
        <v-icon class="mr-2">mdi-lock-reset</v-icon>
        Change Password
      </v-card-title>
      <v-card-text>
        <v-text-field
          v-model="pwForm.current_password"
          label="Current Password"
          :type="showCurrentPw ? 'text' : 'password'"
          variant="outlined"
          class="mb-3"
          prepend-inner-icon="mdi-lock"
          :append-inner-icon="showCurrentPw ? 'mdi-eye-off' : 'mdi-eye'"
          @click:append-inner="showCurrentPw = !showCurrentPw"
        />
        <v-text-field
          v-model="pwForm.new_password"
          label="New Password"
          :type="showNewPw ? 'text' : 'password'"
          variant="outlined"
          prepend-inner-icon="mdi-lock-plus"
          :append-inner-icon="showNewPw ? 'mdi-eye-off' : 'mdi-eye'"
          @click:append-inner="showNewPw = !showNewPw"
          hint="Minimum 8 characters"
          persistent-hint
        />
        <v-alert v-if="pwError" type="error" density="compact" class="mt-3">
          {{ pwError }}
        </v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="closePasswordDialog">Cancel</v-btn>
        <v-btn
          color="primary"
          variant="flat"
          :loading="pwSaving"
          :disabled="!pwForm.current_password || pwForm.new_password.length < 8"
          @click="changePassword"
        >
          Change Password
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Snackbar -->
  <v-snackbar v-model="showSnackbar" :color="snackbarColor" :timeout="3000">
    {{ snackbarMessage }}
    <template #actions>
      <v-btn variant="text" @click="showSnackbar = false">Close</v-btn>
    </template>
  </v-snackbar>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

definePageMeta({ middleware: 'auth' })

const { user, logout, fetchCurrentUser } = useAuth()
const router = useRouter()
const runtimeConfig = useRuntimeConfig()
const apiBase = computed(() => runtimeConfig.public.apiBaseUrl || 'http://localhost:8000/api/v1')

const getAuthHeaders = () => {
  const token = useCookie('auth_token')
  return token.value ? { Authorization: `Bearer ${token.value}` } : {}
}

// Data
const playerProfile = ref<any>(null)
const myTeam = ref<any>(null)
const statsLoading = ref(true)
const teamLoading = ref(false)

// Edit Profile dialog
const showEditDialog = ref(false)
const editSaving = ref(false)
const editError = ref<string | null>(null)
const editForm = ref({ full_name: '', email: '' })

// Change Password dialog
const showPasswordDialog = ref(false)
const pwSaving = ref(false)
const pwError = ref<string | null>(null)
const showCurrentPw = ref(false)
const showNewPw = ref(false)
const pwForm = ref({ current_password: '', new_password: '' })

// Snackbar
const showSnackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

// Computed
const initials = computed(() => {
  if (user.value?.full_name) {
    return user.value.full_name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2)
  }
  return user.value?.username?.slice(0, 2).toUpperCase() || 'U'
})

// Data fetching
const fetchPlayerStats = async () => {
  if (!user.value?.id) return
  statsLoading.value = true
  try {
    playerProfile.value = await $fetch<any>(
      `${apiBase.value}/statistics/player/${user.value.id}`,
      { headers: getAuthHeaders() },
    )
  } catch {
    playerProfile.value = null
  } finally {
    statsLoading.value = false
  }
}

const fetchMyTeam = async () => {
  teamLoading.value = true
  try {
    myTeam.value = await $fetch<any>(`${apiBase.value}/teams/my/team`, { headers: getAuthHeaders() })
  } catch {
    myTeam.value = null
  } finally {
    teamLoading.value = false
  }
}

// Edit Profile
const openEditProfile = () => {
  editForm.value = { full_name: user.value?.full_name || '', email: user.value?.email || '' }
  editError.value = null
  showEditDialog.value = true
}

const closeEditDialog = () => {
  showEditDialog.value = false
  editError.value = null
}

const saveProfile = async () => {
  editSaving.value = true
  editError.value = null
  try {
    const payload: Record<string, string> = {}
    if (editForm.value.full_name !== (user.value?.full_name || '')) payload.full_name = editForm.value.full_name
    if (editForm.value.email !== user.value?.email) payload.email = editForm.value.email

    if (Object.keys(payload).length === 0) {
      closeEditDialog()
      return
    }

    await $fetch(`${apiBase.value}/users/me`, {
      method: 'PATCH',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: payload,
    })
    // Refresh the global user state so the header/avatar updates immediately
    await fetchCurrentUser()
    closeEditDialog()
    showMsg('Profile updated successfully!', 'success')
  } catch (err: any) {
    editError.value = err.data?.detail || 'Failed to update profile'
  } finally {
    editSaving.value = false
  }
}

// Change Password
const closePasswordDialog = () => {
  showPasswordDialog.value = false
  pwForm.value = { current_password: '', new_password: '' }
  pwError.value = null
}

const changePassword = async () => {
  pwSaving.value = true
  pwError.value = null
  try {
    await $fetch(`${apiBase.value}/users/me/change-password`, {
      method: 'POST',
      headers: { ...getAuthHeaders(), 'Content-Type': 'application/json' },
      body: pwForm.value,
    })
    closePasswordDialog()
    showMsg('Password changed successfully!', 'success')
  } catch (err: any) {
    pwError.value = err.data?.detail || 'Failed to change password'
  } finally {
    pwSaving.value = false
  }
}

// Helpers
const formatDate = (dateString: string | undefined): string => {
  if (!dateString) return 'N/A'
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric', month: 'long', day: 'numeric',
  })
}

const handleLogout = () => {
  logout()
  router.push('/')
}

const showMsg = (message: string, color: string) => {
  snackbarMessage.value = message
  snackbarColor.value = color
  showSnackbar.value = true
}

// Init
onMounted(() => {
  fetchPlayerStats()
  fetchMyTeam()
})
</script>

<style scoped>
.font-mono {
  font-family: 'Courier New', Courier, monospace;
}
</style>
