# AmStar — Webová aplikácia pre organizáciu amatérskych futbalových zápasov

> **Bakalárska práca** | Univerzita Konštantína Filozofa v Nitre  
> Fakulta prírodných vied a informatiky  
> Autor: Sebastian Kychatyi  
> Školiteľ: RNDr. Lívia Kelebercová, PhD.  
> Študijný program: Aplikovaná informatika | Rok: 2026

---

Platformа AmStar je webová aplikácia určená na zjednodušenie a automatizáciu organizácie amatérskych futbalových zápasov — správu tímov, hráčov, zápasových výziev (Battle systém), turnajov a štatistík.

## Features

- **Team Management**: Create teams, manage rosters, assign captains
- **Player Profiles**: Track player statistics, skill ratings, and performance
- **Join Request System**: Request/approval workflow for joining teams
- **Dynamic Rating System**: Automatically calculate player and team ratings based on performance
- **Match Statistics**: Comprehensive tracking of goals, assists, cards, and clean sheets
- **Battle System Ready**: Prepared architecture for team challenges

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Database**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0 (async)
- **Validation**: Pydantic v2
- **API Docs**: Automatic OpenAPI/Swagger documentation

## Quick Start

### 1. Prerequisites

- Python 3.11 or higher
- PostgreSQL 14 or higher
- pip (Python package manager)

### 2. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd AmStars

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb amstar

# Run the schema
psql -d amstar -f database/schema.sql
```

### 4. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Update DATABASE_URL with your PostgreSQL credentials
```

### 5. Run the Application

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the API documentation at: http://localhost:8000/docs

## Project Structure

```
AmStars/
├── database/
│   └── schema.sql              # PostgreSQL database schema with triggers
├── app/
│   ├── models/
│   │   ├── database.py         # SQLAlchemy ORM models
│   │   └── schemas.py          # Pydantic validation schemas
│   ├── services/
│   │   ├── team_service.py     # Team management business logic
│   │   └── statistics_service.py # Statistics and rating calculations
│   ├── api/
│   │   └── endpoints/
│   │       ├── teams.py        # Team API endpoints
│   │       └── statistics.py   # Statistics API endpoints
│   ├── database.py             # Database connection
│   └── main.py                 # FastAPI application entry point
├── tests/                      # Test suite
├── requirements.txt            # Python dependencies
├── .env.example               # Environment configuration template
├── INTEGRATION_GUIDE.md       # Detailed integration guide
└── README.md                  # This file
```

## Core Concepts

### Teams
- Each team has at least one captain with administrative rights
- Teams can have up to 50 players (configurable)
- Teams have dynamic ratings based on player performance
- Support for recruiting mode (accepting/rejecting join requests)

### Players
- Each player has a position (Goalkeeper, Defender, Midfielder, Forward)
- Dynamic skill rating (0-100) that updates after each match
- Lifetime statistics tracked across all teams
- Team-specific statistics for each team membership

### Join Requests
- Players request to join teams
- Captains approve or reject requests
- Prevents duplicate memberships
- Respects team capacity limits

### Rating System

#### Player Rating (0-100 scale)
- Starts at 50.0 for new players
- Influenced by:
  - Match results (win/draw/loss)
  - Individual performance (goals, assists)
  - Discipline (yellow/red cards)
  - Goalkeeper-specific metrics (clean sheets)
- Uses exponential moving average for stability

#### Team Rating (0-100 scale)
- Weighted calculation:
  - 70%: Average player skill rating
  - 20%: Win rate
  - 10%: Goal difference per match

## API Endpoints

### Teams

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/teams` | Create new team | Required |
| GET | `/api/teams/{id}` | Get team details | Public |
| PATCH | `/api/teams/{id}` | Update team | Captain |
| GET | `/api/teams/{id}/members` | List team members | Public |
| DELETE | `/api/teams/{id}/members/{player_id}` | Remove member | Captain/Self |
| POST | `/api/teams/{id}/members/{player_id}/promote` | Promote to captain | Captain |

### Join Requests

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/teams/join-requests` | Request to join team | Required |
| GET | `/api/teams/join-requests/{team_id}/pending` | List pending requests | Captain |
| POST | `/api/teams/join-requests/{id}/review` | Approve/reject request | Captain |

### Statistics

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/statistics/matches/update` | Update match statistics | Captain |
| GET | `/api/statistics/players/{id}` | Get player statistics | Public |
| GET | `/api/statistics/teams/{id}` | Get team statistics | Public |

## Database Schema Highlights

### Key Tables
- `players` - Player profiles and lifetime statistics
- `teams` - Team information and performance metrics
- `team_members` - Junction table for team rosters
- `team_join_requests` - Request/approval workflow
- `match_events` - Detailed match event tracking

### Database Features
- PostgreSQL ENUM types for type safety
- Automatic timestamp updates via triggers
- Captain enforcement (at least one captain per team)
- Unique constraints preventing duplicate memberships
- Cascading deletes for data integrity

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black app/
```

### Type Checking

```bash
mypy app/
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

## Example Usage

### 1. Create a Team
```python
import httpx

response = httpx.post("http://localhost:8000/api/teams", json={
    "name": "Thunder FC",
    "captain_id": "player-uuid",
    "home_city": "Prague",
    "max_players": 25
})
```

### 2. Update Match Statistics
```python
response = httpx.post("http://localhost:8000/api/statistics/matches/update", json={
    "match_id": "match-uuid",
    "team_id": "team-uuid",
    "match_result": "WIN",
    "goals_scored": 3,
    "goals_conceded": 1,
    "player_stats": [
        {
            "player_id": "player1-uuid",
            "goals": 2,
            "assists": 1,
            "yellow_cards": 0,
            "red_cards": 0
        }
    ]
})
```

## Future Enhancements

- [ ] Match scheduling system
- [ ] Battle system for team challenges
- [ ] Real-time notifications
- [ ] Advanced analytics dashboard
- [ ] Mobile app integration
- [ ] Social features (comments, likes)
- [ ] Tournament brackets
- [ ] Video highlights upload

## Contributing

This is a Bachelor's thesis project. For questions or suggestions, please contact the project maintainer.

## License

Táto práca je súčasťou bakalárskej záverečnej práce na Univerzite Konštantína Filozofa v Nitre.  
Zdrojový kód je zverejnený výhradne na účely akademického hodnotenia a demonštrácie.

© 2026 Sebastian Kychatyi. Všetky práva vyhradené.  
Komerčné využitie bez súhlasu autora je zakázané.

## Autor

**Sebastian Kychatyi**  
Bakalárska práca — Aplikovaná informatika  
Univerzita Konštantína Filozofa v Nitre, Fakulta prírodných vied a informatiky  
Školiteľ: RNDr. Lívia Kelebercová, PhD.  
Nitra, 2026

---

For detailed integration instructions, see [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
