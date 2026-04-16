<template>
  <v-container class="py-8">
    <!-- Header -->
    <div class="d-flex align-center mb-6">
      <v-icon icon="mdi-shield-crown" color="warning" size="36" class="mr-3" />
      <div>
        <h1 class="text-h4 font-weight-bold">Admin Panel</h1>
        <p class="text-body-2 text-medium-emphasis">Platform management dashboard</p>
      </div>
    </div>

    <!-- Tabs -->
    <v-tabs v-model="tab" class="mb-6" color="primary">
      <v-tab value="users">
        <v-icon start>mdi-account-group</v-icon>
        Users ({{ users.length }})
      </v-tab>
      <v-tab value="teams">
        <v-icon start>mdi-shield-account</v-icon>
        Teams ({{ teams.length }})
      </v-tab>
      <v-tab value="announcement">
        <v-icon start>mdi-bullhorn</v-icon>
        Announcement
      </v-tab>
    </v-tabs>

    <v-window v-model="tab">
      <!-- Users tab -->
      <v-window-item value="users">
        <v-card>
          <v-card-title class="d-flex align-center py-4 px-4">
            <span>User Management</span>
            <v-spacer />
            <v-btn icon variant="text" @click="loadUsers" :loading="usersLoading">
              <v-icon>mdi-refresh</v-icon>
            </v-btn>
          </v-card-title>

          <v-data-table
            :headers="userHeaders"
            :items="users"
            :loading="usersLoading"
            item-value="id"
            density="comfortable"
          >
            <template #item.is_active="{ item }">
              <v-chip :color="item.is_active ? 'success' : 'error'" size="small" label>
                {{ item.is_active ? 'Active' : 'Inactive' }}
              </v-chip>
            </template>

            <template #item.role="{ item }">
              <v-chip size="small" :color="roleColor(item.role)" label>{{ item.role }}</v-chip>
            </template>

            <template #item.is_superuser="{ item }">
              <v-icon v-if="item.is_superuser" color="warning" size="20">mdi-shield-crown</v-icon>
              <span v-else class="text-medium-emphasis">—</span>
            </template>

            <template #item.actions="{ item }">
              <div class="d-flex gap-1">
                <v-tooltip location="top" bg-color="white">
                  <template #activator="{ props }">
                    <v-btn
                      v-bind="props"
                      :icon="item.is_active ? 'mdi-account-cancel' : 'mdi-account-check'"
                      variant="text"
                      size="small"
                      :color="item.is_active ? 'warning' : 'success'"
                      :disabled="item.is_superuser"
                      @click="item.is_active ? deactivateUser(item) : activateUser(item)"
                    />
                  </template>
                  <span class="text-black">{{ item.is_active ? 'Deactivate' : 'Activate' }}</span>
                </v-tooltip>

                <v-tooltip text="Delete user" location="top">
                  <template #activator="{ props }">
                    <v-btn
                      v-bind="props"
                      icon="mdi-delete"
                      variant="text"
                      size="small"
                      color="error"
                      :disabled="item.is_superuser"
                      @click="confirmDelete('user', item)"
                    />
                  </template>
                </v-tooltip>
              </div>
            </template>
          </v-data-table>
        </v-card>
      </v-window-item>

      <!-- Teams tab -->
      <v-window-item value="teams">
        <v-card>
          <v-card-title class="d-flex align-center py-4 px-4">
            <span>Team Management</span>
            <v-spacer />
            <v-btn icon variant="text" @click="loadTeams" :loading="teamsLoading">
              <v-icon>mdi-refresh</v-icon>
            </v-btn>
          </v-card-title>

          <v-data-table
            :headers="teamHeaders"
            :items="teams"
            :loading="teamsLoading"
            item-value="id"
            density="comfortable"
          >
            <template #item.rating_score="{ item }">
              <v-chip size="small" color="primary" label>{{ item.rating_score }}</v-chip>
            </template>

            <template #item.actions="{ item }">
              <v-tooltip text="Delete team" location="top">
                <template #activator="{ props }">
                  <v-btn
                    v-bind="props"
                    icon="mdi-delete"
                    variant="text"
                    size="small"
                    color="error"
                    @click="confirmDelete('team', item)"
                  />
                </template>
              </v-tooltip>
            </template>
          </v-data-table>
        </v-card>
      </v-window-item>

      <!-- Announcement tab -->
      <v-window-item value="announcement">
        <v-card>
          <v-card-title>Global Announcement</v-card-title>
          <v-card-subtitle class="pb-2">
            Published messages appear as a banner on all users' dashboards.
          </v-card-subtitle>

          <v-card-text>
            <v-alert
              v-if="currentAnnouncement"
              type="info"
              variant="tonal"
              class="mb-4"
              icon="mdi-bullhorn"
            >
              <strong>Current:</strong> {{ currentAnnouncement }}
            </v-alert>
            <p v-else class="text-medium-emphasis mb-4">No active announcement.</p>

            <v-textarea
              v-model="announcementText"
              label="Announcement message"
              rows="4"
              variant="outlined"
              placeholder="Enter a platform-wide message visible to all users..."
              counter
              maxlength="500"
            />
          </v-card-text>

          <v-card-actions class="px-4 pb-4">
            <v-btn
              color="primary"
              :loading="announcementSaving"
              prepend-icon="mdi-bullhorn"
              @click="saveAnnouncement"
            >
              Publish
            </v-btn>
            <v-btn
              color="error"
              variant="text"
              :disabled="!currentAnnouncement"
              @click="clearAnnouncement"
            >
              Clear
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-window-item>
    </v-window>

    <!-- Delete confirmation dialog -->
    <v-dialog v-model="deleteDialog" max-width="420">
      <v-card>
        <v-card-title class="text-h6">Confirm Delete</v-card-title>
        <v-card-text>
          Are you sure you want to permanently delete
          <strong>{{ deleteTarget?.name || deleteTarget?.username }}</strong>?
          This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="error" :loading="deleteLoading" @click="executeDelete">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="3000" location="bottom">
      {{ snackbar.text }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

definePageMeta({ middleware: ['admin'] })

const { token } = useAuth()
const config = useRuntimeConfig()
const apiBase = config.public.apiBaseUrl || 'http://localhost:8000/api/v1'

const tab = ref('users')
const users = ref<any[]>([])
const teams = ref<any[]>([])
const usersLoading = ref(false)
const teamsLoading = ref(false)

const currentAnnouncement = ref<string | null>(null)
const announcementText = ref('')
const announcementSaving = ref(false)

const deleteDialog = ref(false)
const deleteTarget = ref<any>(null)
const deleteType = ref<'user' | 'team'>('user')
const deleteLoading = ref(false)

const snackbar = ref({ show: false, text: '', color: 'success' })

const userHeaders = [
  { title: 'ID', key: 'id', width: 70 },
  { title: 'Username', key: 'username' },
  { title: 'Email', key: 'email' },
  { title: 'Role', key: 'role', width: 130 },
  { title: 'Status', key: 'is_active', width: 110 },
  { title: 'Admin', key: 'is_superuser', width: 80 },
  { title: 'Actions', key: 'actions', sortable: false, width: 120 },
]

const teamHeaders = [
  { title: 'ID', key: 'id', width: 70 },
  { title: 'Name', key: 'name' },
  { title: 'City', key: 'city' },
  { title: 'ELO', key: 'rating_score', width: 100 },
  { title: 'Members', key: 'member_count', width: 110 },
  { title: 'Actions', key: 'actions', sortable: false, width: 100 },
]

const authHeaders = computed(() => ({
  Authorization: `Bearer ${token.value}`,
}))

const roleColor = (role: string) => {
  if (role === 'CAPTAIN') return 'primary'
  if (role === 'REFEREE') return 'secondary'
  return 'default'
}

const showSnack = (text: string, color = 'success') => {
  snackbar.value = { show: true, text, color }
}

// Data loading

const loadUsers = async () => {
  usersLoading.value = true
  try {
    users.value = await $fetch<any[]>(`${apiBase}/admin/users`, { headers: authHeaders.value })
  } catch {
    showSnack('Failed to load users', 'error')
  } finally {
    usersLoading.value = false
  }
}

const loadTeams = async () => {
  teamsLoading.value = true
  try {
    teams.value = await $fetch<any[]>(`${apiBase}/admin/teams`, { headers: authHeaders.value })
  } catch {
    showSnack('Failed to load teams', 'error')
  } finally {
    teamsLoading.value = false
  }
}

const loadAnnouncement = async () => {
  try {
    const data = await $fetch<{ message: string | null }>(`${apiBase}/admin/announcement`)
    currentAnnouncement.value = data.message ?? null
    announcementText.value = data.message ?? ''
  } catch { /* non-critical; failure does not affect core functionality */ }
}

// User actions

const deactivateUser = async (user: any) => {
  try {
    await $fetch(`${apiBase}/admin/users/${user.id}/deactivate`, {
      method: 'PATCH',
      headers: authHeaders.value,
    })
    user.is_active = false
    showSnack(`User '${user.username}' deactivated`)
  } catch {
    showSnack('Failed to deactivate user', 'error')
  }
}

const activateUser = async (user: any) => {
  try {
    await $fetch(`${apiBase}/admin/users/${user.id}/activate`, {
      method: 'PATCH',
      headers: authHeaders.value,
    })
    user.is_active = true
    showSnack(`User '${user.username}' activated`)
  } catch {
    showSnack('Failed to activate user', 'error')
  }
}

// Delete

const confirmDelete = (type: 'user' | 'team', item: any) => {
  deleteType.value = type
  deleteTarget.value = item
  deleteDialog.value = true
}

const executeDelete = async () => {
  deleteLoading.value = true
  try {
    const url = deleteType.value === 'user'
      ? `${apiBase}/admin/users/${deleteTarget.value.id}`
      : `${apiBase}/admin/teams/${deleteTarget.value.id}`

    await $fetch(url, { method: 'DELETE', headers: authHeaders.value })

    if (deleteType.value === 'user') {
      users.value = users.value.filter(u => u.id !== deleteTarget.value.id)
    } else {
      teams.value = teams.value.filter(t => t.id !== deleteTarget.value.id)
    }

    showSnack(`${deleteType.value === 'user' ? 'User' : 'Team'} deleted successfully`)
    deleteDialog.value = false
  } catch {
    showSnack('Delete failed', 'error')
  } finally {
    deleteLoading.value = false
  }
}

// Announcement

const saveAnnouncement = async () => {
  announcementSaving.value = true
  try {
    await $fetch(`${apiBase}/admin/announcement`, {
      method: 'POST',
      headers: authHeaders.value,
      body: { message: announcementText.value || null },
    })
    currentAnnouncement.value = announcementText.value || null
    showSnack('Announcement published')
  } catch {
    showSnack('Failed to save announcement', 'error')
  } finally {
    announcementSaving.value = false
  }
}

const clearAnnouncement = async () => {
  announcementText.value = ''
  await saveAnnouncement()
}

// Init

onMounted(() => {
  loadUsers()
  loadTeams()
  loadAnnouncement()
})
</script>

<style scoped>
.gap-1 {
  gap: 4px;
}
</style>
