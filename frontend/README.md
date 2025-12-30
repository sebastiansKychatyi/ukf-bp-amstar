# AmStar Football Platform - Frontend

Modern Vue.js 3 frontend application for managing amateur football teams, players, and matches.

## Tech Stack

- **Framework**: Vue.js 3 (Composition API)
- **UI Library**: Vuetify 3 (Material Design)
- **State Management**: Pinia
- **Routing**: Vue Router 4
- **HTTP Client**: Axios
- **Icons**: Material Design Icons (MDI)
- **Build Tool**: Vite

## Features

### Player Management
- Browse and search players
- View detailed player profiles
- Track comprehensive statistics
- Position-based filtering
- Dynamic skill ratings (0-100 scale)
- Grid and table view modes

### Team Management
- Create and manage teams
- Team roster management
- Captain assignment and promotion
- Team join request/approval workflow
- Upload team logos
- View team statistics and ratings

### Battle System
- Challenge other teams
- Filter by team rating
- View win probabilities
- Match scheduling
- Real-time team comparisons

### Additional Features
- Dark/Light theme toggle
- Responsive design (mobile-first)
- Real-time notifications
- Search and filtering
- Sorting capabilities

## Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable Vue components
│   │   ├── PlayerCard.vue
│   │   ├── PlayerDetailsDialog.vue
│   │   ├── PlayerStatsDialog.vue
│   │   ├── JoinTeamDialog.vue
│   │   └── JoinRequestsDialog.vue
│   ├── layouts/             # Application layouts
│   │   └── DefaultLayout.vue
│   ├── views/               # Page components
│   │   ├── PlayerDashboard.vue
│   │   ├── TeamCreate.vue
│   │   ├── TeamDetail.vue
│   │   └── BattleSystem.vue
│   ├── stores/              # Pinia stores
│   │   ├── player.js
│   │   └── team.js
│   ├── services/            # API services
│   │   └── api.js
│   ├── router/              # Vue Router config
│   │   └── index.js
│   ├── plugins/             # Vuetify config
│   │   └── vuetify.js
│   ├── App.vue              # Root component
│   └── main.js              # App entry point
├── package.json
└── vite.config.js
```

## Installation

### Prerequisites
- Node.js 18+ and npm/yarn
- Backend API running (see backend README)

### Setup

```bash
# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with your API URL

# Start development server
npm run dev

# Open browser to http://localhost:5173
```

## Environment Variables

Create a `.env.local` file:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Available Scripts

```bash
# Development server with hot-reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint and fix files
npm run lint
```

## API Integration

### Example: Fetch All Players

```javascript
import { playerApi } from '@/services/api'

async function loadPlayers() {
  try {
    const players = await playerApi.getAll()
    console.log(players)
  } catch (error) {
    console.error('Failed to load players:', error)
  }
}
```

### Example: Create Team

```javascript
import { teamApi } from '@/services/api'

async function createTeam() {
  const teamData = {
    name: 'Thunder FC',
    captain_id: 'player-uuid',
    home_city: 'Prague',
    max_players: 25,
    is_recruiting: true,
  }

  try {
    const newTeam = await teamApi.create(teamData)
    console.log('Team created:', newTeam)
  } catch (error) {
    console.error('Failed to create team:', error)
  }
}
```

### Example: Send Join Request

```javascript
import { joinRequestApi } from '@/services/api'

async function joinTeam(teamId) {
  const requestData = {
    team_id: teamId,
    player_id: 'current-player-id',
    message: 'I would love to join your team!',
  }

  try {
    const request = await joinRequestApi.create(requestData)
    console.log('Join request sent:', request)
  } catch (error) {
    console.error('Failed to send join request:', error)
  }
}
```

## State Management with Pinia

### Player Store

```javascript
import { usePlayerStore } from '@/stores/player'

export default {
  setup() {
    const playerStore = usePlayerStore()

    // Fetch all players
    playerStore.fetchAllPlayers()

    // Access players
    const players = playerStore.players

    // Filter by position
    const forwards = playerStore.playersByPosition('FORWARD')

    // Top rated players
    const topPlayers = playerStore.topRatedPlayers

    return { players, forwards, topPlayers }
  }
}
```

### Team Store

```javascript
import { useTeamStore } from '@/stores/team'

export default {
  setup() {
    const teamStore = useTeamStore()

    // Create team
    const createTeam = async (teamData) => {
      await teamStore.createTeam(teamData)
    }

    // Send join request
    const joinTeam = async (teamId, message) => {
      await teamStore.createJoinRequest(teamId, message)
    }

    // Review join request (captain only)
    const approveRequest = async (requestId) => {
      await teamStore.reviewJoinRequest(requestId, 'APPROVED')
    }

    return { createTeam, joinTeam, approveRequest }
  }
}
```

## How Frontend State Updates When Player Joins Team

### Step-by-Step Flow

1. **Player sends join request:**
   ```javascript
   // In JoinTeamDialog.vue
   await teamStore.createJoinRequest(teamId, message)
   // Request saved in teamStore.myJoinRequests
   ```

2. **Captain views pending requests:**
   ```javascript
   // In TeamDetail.vue (Captain's view)
   await teamStore.fetchPendingJoinRequests(teamId)
   // Requests populated in teamStore.pendingJoinRequests
   ```

3. **Captain approves request:**
   ```javascript
   // In JoinRequestsDialog.vue
   await teamStore.reviewJoinRequest(requestId, 'APPROVED')
   // Backend creates TeamMember record
   // Request removed from pendingJoinRequests array
   ```

4. **Team roster updates automatically:**
   ```javascript
   // After approval, TeamStore refetches members
   await teamStore.fetchTeamMembers(teamId)
   // teamStore.teamMembers updates with new member
   // UI re-renders automatically (Vue reactivity)
   ```

5. **Player sees updated status:**
   ```javascript
   // Player can fetch their requests
   await teamStore.fetchMyJoinRequests()
   // Request now has status: 'APPROVED'
   ```

**Key Points:**
- **Reactive State**: All stores use Vue 3 reactivity (`ref`, `computed`)
- **Automatic UI Updates**: Components watching store state re-render
- **Event Emission**: Dialogs emit events on success
- **State Synchronization**: Parent components refetch data after events

## Component Communication

### Parent-Child (Props & Emits)

```vue
<!-- Parent Component -->
<template>
  <player-card
    :player="selectedPlayer"
    @view-details="handleViewDetails"
  />
</template>

<script setup>
function handleViewDetails(player) {
  // Handle event from child
  showDetailsDialog.value = true
}
</script>
```

### Global State (Pinia)

```javascript
// Any component can access
const teamStore = useTeamStore()
const teams = teamStore.teams

// Updates are reactive across all components
await teamStore.fetchAllTeams()
```

## Vuetify Theme Customization

The application uses a custom sports-themed color palette:

```javascript
// src/plugins/vuetify.js
const lightTheme = {
  colors: {
    primary: '#1E40AF',    // Thunder Blue
    secondary: '#059669',   // Field Green
    accent: '#DC2626',      // Red Card Red
    success: '#10B981',
    // ...
  }
}
```

To customize:
1. Edit `src/plugins/vuetify.js`
2. Modify color values
3. Changes apply globally

## Responsive Design

The application uses Vuetify's 12-column grid system:

```vue
<v-row>
  <v-col cols="12" sm="6" md="4" lg="3">
    <!-- Full width on mobile, 2 cols on tablet, 3 on desktop, 4 on large -->
  </v-col>
</v-row>
```

**Breakpoints:**
- xs: 0-599px (mobile)
- sm: 600-959px (tablet)
- md: 960-1279px (desktop)
- lg: 1280-1919px (large desktop)
- xl: 1920px+ (extra large)

## Testing

```bash
# Run unit tests
npm run test:unit

# Run E2E tests
npm run test:e2e
```

## Deployment

### Build for Production

```bash
npm run build
```

Output directory: `dist/`

### Deploy to Vercel

```bash
npm install -g vercel
vercel --prod
```

### Deploy to Netlify

```bash
npm install -g netlify-cli
netlify deploy --prod
```

## Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile: iOS Safari 12+, Chrome Android 90+

## Contributing

This is a Bachelor's thesis project. For questions or suggestions, please contact the project maintainer.

## License

[Specify your license here]

## Author

Developed as part of a Bachelor's thesis on amateur football match organization.

---

**Note**: This frontend requires the AmStar backend API to be running. See `../backend/README.md` for backend setup instructions.
