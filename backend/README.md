# AmStar Backend - FastAPI REST API

Backend API for the Amateur Football Platform.

## Tech Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migrations
- **PostgreSQL** - Database
- **Pydantic** - Data validation
- **JWT** - Authentication

## Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+

### Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy environment file:
```bash
cp .env.example .env
```

4. Update `.env` with your database credentials

5. Run database migrations:
```bash
alembic upgrade head
```

### Running the Application

Development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── api/              # API routes
│   ├── core/             # Core configurations
│   ├── db/               # Database setup
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── crud/             # Database operations
│   ├── services/         # Business logic
│   └── main.py           # Application entry point
├── alembic/              # Database migrations
├── tests/                # Test files
└── requirements.txt      # Dependencies
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login

### Users
- `GET /api/v1/users` - List users
- `GET /api/v1/users/{id}` - Get user by ID

### Teams
- `GET /api/v1/teams` - List teams
- `GET /api/v1/teams/{id}` - Get team by ID

### Challenges
- `GET /api/v1/challenges` - List challenges
- `GET /api/v1/challenges/{id}` - Get challenge by ID

### Ratings
- `GET /api/v1/ratings` - Get rating leaderboard

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```

## Development

Run tests:
```bash
pytest
```

Format code:
```bash
black .
isort .
```

Lint code:
```bash
flake8 .
mypy .
```

## License

MIT
