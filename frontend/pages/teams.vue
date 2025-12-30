<template>
  <!--
    Teams Page
    ==========
    Displays all teams in a clean, searchable data table

    Features:
    - Server-side data (mock data for now)
    - Search functionality
    - Sortable columns
    - Responsive layout
  -->
  <v-container class="py-8">
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <h1 class="text-h3 font-weight-bold mb-2">
          <v-icon icon="mdi-shield-account" size="large" class="mr-2" />
          Teams
        </h1>
        <p class="text-body-1 text-medium-emphasis">
          Browse and manage football teams in the platform
        </p>
      </v-col>
    </v-row>

    <!-- Data Table -->
    <v-row>
      <v-col cols="12">
        <v-card elevation="2">
          <v-card-title>
            <!-- Search Bar -->
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              label="Search teams"
              single-line
              hide-details
              variant="outlined"
              density="comfortable"
              class="mb-4"
            />
          </v-card-title>

          <!-- Teams Table -->
          <v-data-table
            :headers="headers"
            :items="teams"
            :search="search"
            :items-per-page="10"
            class="elevation-0"
          >
            <!-- Team Name Column with Icon -->
            <template #item.name="{ item }">
              <div class="d-flex align-center">
                <v-icon icon="mdi-shield" class="mr-2" color="primary" />
                <span class="font-weight-medium">{{ item.name }}</span>
              </div>
            </template>

            <!-- Captain Column with Badge -->
            <template #item.captain="{ item }">
              <v-chip size="small" color="secondary" variant="flat">
                <v-icon start>mdi-account-star</v-icon>
                {{ item.captain }}
              </v-chip>
            </template>

            <!-- Members Count Column -->
            <template #item.members="{ item }">
              <v-chip size="small" variant="outlined">
                {{ item.members }} players
              </v-chip>
            </template>

            <!-- Actions Column -->
            <template #item.actions="{ item }">
              <v-btn
                size="small"
                color="primary"
                variant="text"
                @click="viewTeamDetails(item)"
              >
                View Details
              </v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'

/**
 * Table Configuration
 * ==================
 * Defines columns for the teams data table
 */
const headers = [
  { title: 'Team Name', key: 'name', align: 'start' as const },
  { title: 'Captain', key: 'captain', align: 'start' as const },
  { title: 'Members', key: 'members', align: 'center' as const },
  { title: 'Actions', key: 'actions', align: 'center' as const, sortable: false },
]

/**
 * Search State
 * ============
 * Reactive search query for filtering teams
 */
const search = ref('')

/**
 * Mock Data
 * =========
 * Sample teams data (replace with API call in production)
 * TODO: Connect to backend API endpoint
 */
const teams = ref([
  { id: 1, name: 'Thunder FC', captain: 'John Martinez', members: 15 },
  { id: 2, name: 'Eagles United', captain: 'Sarah Johnson', members: 12 },
  { id: 3, name: 'Phoenix FC', captain: 'Alex Chen', members: 18 },
  { id: 4, name: 'Warriors FC', captain: 'Marcus Robinson', members: 14 },
  { id: 5, name: 'Titans FC', captain: 'Emma Williams', members: 16 },
  { id: 6, name: 'Strikers FC', captain: 'David Brown', members: 13 },
  { id: 7, name: 'Panthers FC', captain: 'Lisa Anderson', members: 17 },
  { id: 8, name: 'Raptors FC', captain: 'Mike Taylor', members: 11 },
])

/**
 * Event Handlers
 * ==============
 */
const viewTeamDetails = (team: any) => {
  // TODO: Navigate to team details page or open dialog
  console.log('View team details:', team)
  // Example: navigateTo(`/teams/${team.id}`)
}
</script>

<style scoped>
/**
 * Page-Specific Styles
 * ====================
 * Minimal scoped styles for table customization
 */

/* Ensure table has proper spacing */
:deep(.v-data-table) {
  background-color: transparent;
}

/* Add hover effect to table rows */
:deep(.v-data-table tbody tr:hover) {
  background-color: rgba(0, 0, 0, 0.02);
}

/* Dark mode hover effect */
:deep(.v-theme--dark .v-data-table tbody tr:hover) {
  background-color: rgba(255, 255, 255, 0.05);
}
</style>
