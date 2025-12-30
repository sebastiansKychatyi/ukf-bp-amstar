# Frontend Integration Guide

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env.local
```

Edit `.env.local`:
```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## API Integration Examples

### Fetching Data

**Example: Load Players**
```javascript
// In a Vue component
import { onMounted } from 'vue'
import { usePlayerStore } from '@/stores/player'

export default {
  setup() {
    const playerStore = usePlayerStore()

    onMounted(async () => {
      await playerStore.fetchAllPlayers()
    })

    return {
      players: playerStore.players,
      loading: playerStore.loading,
      error: playerStore.error,
    }
  }
}
```

**Example: Load Team with Members**
```javascript
import { teamApi } from '@/services/api'

async function loadTeam(teamId) {
  try {
    const [team, members] = await Promise.all([
      teamApi.getById(teamId),
      teamApi.getMembers(teamId)
    ])

    console.log('Team:', team)
    console.log('Members:', members)
  } catch (error) {
    console.error('Error:', error.response?.data?.detail)
  }
}
```

### Creating Data

**Example: Create Team**
```javascript
import { useTeamStore } from '@/stores/team'

const teamStore = useTeamStore()

async function createNewTeam() {
  const teamData = {
    name: 'Thunder FC',
    captain_id: 'current-player-id',
    short_name: 'TFC',
    home_city: 'Prague',
    team_color: '#1E40AF',
    max_players: 25,
    is_recruiting: true,
    description: 'Competitive team in Prague'
  }

  try {
    const newTeam = await teamStore.createTeam(teamData)
    console.log('Team created:', newTeam.id)
  } catch (error) {
    console.error('Failed:', error)
  }
}
```

**Example: Send Join Request**
```javascript
import { joinRequestApi } from '@/services/api'

async function requestToJoin(teamId) {
  try {
    const request = await joinRequestApi.create({
      team_id: teamId,
      player_id: 'current-player-id',
      message: 'I would love to join!'
    })

    console.log('Request sent:', request.id)
  } catch (error) {
    if (error.response?.status === 409) {
      console.log('You already have a pending request')
    }
  }
}
```

### Updating Data

**Example: Review Join Request (Captain)**
```javascript
import { useTeamStore } from '@/stores/team'

const teamStore = useTeamStore()

async function approvePlayer(requestId) {
  try {
    await teamStore.reviewJoinRequest(requestId, 'APPROVED', 'Welcome!')

    // teamStore.teamMembers automatically updates
    // UI re-renders with new member
  } catch (error) {
    console.error('Failed to approve:', error)
  }
}
```

## State Management Flow

### How State Updates Work

1. **Component calls store action:**
   ```javascript
   await teamStore.createJoinRequest(teamId, message)
   ```

2. **Store calls API service:**
   ```javascript
   // In stores/team.js
   const request = await joinRequestApi.create(requestData)
   ```

3. **Store updates reactive state:**
   ```javascript
   myJoinRequests.value.push(request)
   ```

4. **All components watching state re-render:**
   ```vue
   <template>
     <!-- Automatically updates when myJoinRequests changes -->
     <div v-for="request in teamStore.myJoinRequests">
       {{ request.status }}
     </div>
   </template>
   ```

### State Synchronization After Join Approval

```
Player                  Backend                  Captain
  │                        │                        │
  │  Send Join Request     │                        │
  ├───────────────────────>│                        │
  │                        │  Notification          │
  │                        ├───────────────────────>│
  │                        │                        │
  │                        │  Approve Request       │
  │                        │<───────────────────────┤
  │                        │                        │
  │                        │  Create TeamMember     │
  │                        │  Return Updated        │
  │                        ├───────────────────────>│
  │                        │                        │
  │  Notification          │                        │  Refetch Members
  │<───────────────────────┤                        │  teamStore.fetchTeamMembers()
  │                        │                        │
  │  Refetch Requests      │                        │  UI Updates
  │  teamStore.fetchMyJoinRequests()                │  New member appears
  │                        │                        │
  │  UI Updates            │                        │
  │  Status: APPROVED      │                        │
  │                        │                        │
```

## Component Examples

### Using PlayerCard Component

```vue
<template>
  <v-container>
    <v-row>
      <v-col
        v-for="player in players"
        :key="player.id"
        cols="12"
        sm="6"
        md="4"
      >
        <player-card
          :player="player"
          @view-details="handleViewDetails"
          @view-stats="handleViewStats"
        />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { usePlayerStore } from '@/stores/player'
import PlayerCard from '@/components/PlayerCard.vue'

const playerStore = usePlayerStore()
const players = ref([])

onMounted(async () => {
  await playerStore.fetchAllPlayers()
  players.value = playerStore.players
})

function handleViewDetails(player) {
  console.log('View details:', player.id)
}

function handleViewStats(player) {
  console.log('View stats:', player.id)
}
</script>
```

### Using Join Team Dialog

```vue
<template>
  <div>
    <v-btn @click="showDialog = true">
      Join Team
    </v-btn>

    <join-team-dialog
      v-model="showDialog"
      :team="selectedTeam"
      @request-sent="handleRequestSent"
    />

    <v-snackbar v-model="showSnackbar" color="success">
      {{ message }}
    </v-snackbar>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import JoinTeamDialog from '@/components/JoinTeamDialog.vue'

const showDialog = ref(false)
const showSnackbar = ref(false)
const message = ref('')
const selectedTeam = ref({
  id: 'team-id',
  name: 'Thunder FC',
  // ... other team data
})

function handleRequestSent() {
  showDialog.value = false
  message.value = 'Join request sent successfully!'
  showSnackbar.value = true
}
</script>
```

## Routing

### Navigate Programmatically

```javascript
import { useRouter } from 'vue-router'

const router = useRouter()

// Go to team detail page
router.push(`/teams/${teamId}`)

// Go to create team page
router.push({ name: 'TeamCreate' })

// Go back
router.back()
```

### Route Guards Example

```javascript
// Protect a route
{
  path: '/teams/create',
  component: TeamCreate,
  meta: { requiresAuth: true }
}

// In router/index.js
router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('access_token')

  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login')
  } else {
    next()
  }
})
```

## Error Handling

### Global Error Handler

```javascript
// In services/api.js
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Redirect to login
      localStorage.removeItem('access_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
```

### Component-Level Error Handling

```vue
<script setup>
import { ref } from 'vue'
import { usePlayerStore } from '@/stores/player'

const playerStore = usePlayerStore()
const error = ref(null)

async function loadPlayers() {
  error.value = null
  try {
    await playerStore.fetchAllPlayers()
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to load players'
  }
}
</script>

<template>
  <v-alert v-if="error" type="error" closable>
    {{ error }}
  </v-alert>
</template>
```

## Theme Customization

### Change Theme Colors

Edit `src/plugins/vuetify.js`:

```javascript
const lightTheme = {
  colors: {
    primary: '#YOUR_COLOR',
    secondary: '#YOUR_COLOR',
    // ...
  }
}
```

### Toggle Theme in Component

```vue
<script setup>
import { useTheme } from 'vuetify'

const theme = useTheme()

function toggleTheme() {
  theme.global.name.value =
    theme.global.name.value === 'light' ? 'dark' : 'light'
}
</script>

<template>
  <v-btn @click="toggleTheme">
    Toggle Theme
  </v-btn>
</template>
```

## Form Validation

### Using Vuetify Forms

```vue
<template>
  <v-form ref="formRef" v-model="formValid" @submit.prevent="handleSubmit">
    <v-text-field
      v-model="teamName"
      :rules="[rules.required, rules.minLength(3)]"
      label="Team Name"
    />

    <v-btn
      type="submit"
      :disabled="!formValid"
    >
      Submit
    </v-btn>
  </v-form>
</template>

<script setup>
import { ref } from 'vue'

const formRef = ref(null)
const formValid = ref(false)
const teamName = ref('')

const rules = {
  required: v => !!v || 'Required',
  minLength: min => v => (v && v.length >= min) || `Min ${min} chars`
}

async function handleSubmit() {
  const { valid } = await formRef.value.validate()
  if (valid) {
    console.log('Form is valid')
  }
}
</script>
```

## Performance Optimization

### Lazy Loading Routes

```javascript
// Already implemented in router/index.js
{
  path: '/teams/:id',
  component: () => import('@/views/TeamDetail.vue')
}
```

### Computed Properties for Filtering

```javascript
const filteredPlayers = computed(() => {
  return players.value.filter(p =>
    p.name.toLowerCase().includes(search.value.toLowerCase())
  )
})
```

### Debounce Search Input

```javascript
import { ref, watch } from 'vue'
import { debounce } from 'lodash'

const search = ref('')

const debouncedSearch = debounce(async (value) => {
  await performSearch(value)
}, 300)

watch(search, (newValue) => {
  debouncedSearch(newValue)
})
```

## Common Patterns

### Loading States

```vue
<template>
  <div v-if="loading" class="text-center">
    <v-progress-circular indeterminate />
  </div>

  <div v-else-if="error">
    <v-alert type="error">{{ error }}</v-alert>
  </div>

  <div v-else>
    <!-- Content -->
  </div>
</template>
```

### Empty States

```vue
<template>
  <div v-if="items.length === 0" class="text-center py-12">
    <v-icon size="64" color="grey">mdi-inbox</v-icon>
    <p class="text-h6 mt-4">No items found</p>
  </div>
</template>
```

### Infinite Scroll (Future Enhancement)

```javascript
import { ref, onMounted } from 'vue'

const page = ref(1)
const items = ref([])

async function loadMore() {
  const newItems = await api.getItems(page.value)
  items.value.push(...newItems)
  page.value++
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll)
})

function handleScroll() {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 100) {
    loadMore()
  }
}
```

## Testing

### Unit Test Example

```javascript
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PlayerCard from '@/components/PlayerCard.vue'

describe('PlayerCard', () => {
  it('renders player name', () => {
    const player = {
      id: '1',
      first_name: 'John',
      last_name: 'Doe',
      position: 'FORWARD',
      skill_rating: 75
    }

    const wrapper = mount(PlayerCard, {
      props: { player }
    })

    expect(wrapper.text()).toContain('John Doe')
  })
})
```

## Troubleshooting

### API Connection Issues

1. Check `.env.local` has correct API URL
2. Ensure backend is running on port 8000
3. Check browser console for CORS errors
4. Verify authentication token in localStorage

### Component Not Updating

1. Ensure data is reactive (use `ref` or `reactive`)
2. Check if Pinia store is properly connected
3. Verify computed properties are used correctly
4. Check Vue DevTools for state changes

### Build Errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

## Next Steps

1. Implement authentication pages (Login/Register)
2. Add real-time notifications with WebSockets
3. Implement match scheduling
4. Add data export functionality
5. Implement advanced statistics charts

## Resources

- [Vue.js Documentation](https://vuejs.org/)
- [Vuetify Documentation](https://vuetifyjs.com/)
- [Pinia Documentation](https://pinia.vuejs.org/)
- [Vue Router Documentation](https://router.vuejs.org/)
