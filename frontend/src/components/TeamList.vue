<template>
  <div class="team-list">
    <div class="team-list-header">
      <h2>Amateur Football Team List (Frontend Placeholder)</h2>
      <p class="description">
        This is a placeholder component for displaying amateur football teams.
        It will be connected to the FastAPI backend in the implementation phase.
      </p>
    </div>

    <div class="team-cards">
      <div
        v-for="team in placeholderTeams"
        :key="team.id"
        class="team-card"
      >
        <div class="team-icon">⚽</div>
        <h3>{{ team.name }}</h3>
        <p class="team-city">{{ team.city }}</p>
        <div class="team-rating">
          <span class="rating-label">Rating:</span>
          <span class="rating-value">{{ team.rating_score }}</span>
        </div>
      </div>
    </div>

    <div class="status-info">
      <p>
        <strong>Status:</strong> Frontend placeholder - Ready for API integration
      </p>
      <p>
        <strong>API Endpoint:</strong> <code>GET /api/v1/teams</code>
      </p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TeamList',
  data() {
    return {
      placeholderTeams: [
        {
          id: 1,
          name: 'FC Barcelona Amateur',
          city: 'Barcelona',
          rating_score: 1850
        },
        {
          id: 2,
          name: 'Madrid Warriors',
          city: 'Madrid',
          rating_score: 1720
        },
        {
          id: 3,
          name: 'Valencia United',
          city: 'Valencia',
          rating_score: 1650
        },
        {
          id: 4,
          name: 'Sevilla Stars',
          city: 'Sevilla',
          rating_score: 1580
        }
      ]
    }
  },
  mounted() {
    console.log('TeamList component mounted - Ready for backend integration')
  }
}
</script>

<style scoped>
.team-list {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.team-list-header {
  margin-bottom: 2rem;
  text-align: center;
}

.team-list-header h2 {
  color: #667eea;
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.description {
  color: #666;
  font-size: 1rem;
  line-height: 1.5;
  max-width: 600px;
  margin: 0 auto;
}

.team-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.team-card {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  cursor: pointer;
}

.team-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.team-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.team-card h3 {
  color: #2c3e50;
  font-size: 1.3rem;
  margin-bottom: 0.5rem;
}

.team-city {
  color: #666;
  font-size: 0.95rem;
  margin-bottom: 1rem;
}

.team-rating {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 4px;
}

.rating-label {
  font-weight: 600;
  color: #667eea;
}

.rating-value {
  font-size: 1.2rem;
  font-weight: bold;
  color: #764ba2;
}

.status-info {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #f0f4ff;
  border-left: 4px solid #667eea;
  border-radius: 4px;
}

.status-info p {
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.status-info code {
  background: #e0e7ff;
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  color: #667eea;
}

/* Responsive design */
@media (max-width: 768px) {
  .team-cards {
    grid-template-columns: 1fr;
  }

  .team-list-header h2 {
    font-size: 1.5rem;
  }
}
</style>
