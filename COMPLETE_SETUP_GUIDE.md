# AmStar Platform - Complete Setup & Verification Guide

## Technology Stack
- **Frontend:** Nuxt.js 3.x (Node 18 Alpine)
- **Backend:** FastAPI (Python 3.11)
- **Database:** PostgreSQL 15
- **Reverse Proxy:** Caddy 2

---

## Quick Start - Build & Launch

### Step 1: Copy Environment File

```bash
cd C:\Users\ninja\Desktop\AmStar
cp .env.local.example .env.local
```

### Step 2: Launch All Services

```bash
# Build and start all containers in the background
docker-compose -f docker-compose.local.yml up -d --build
```

**What This Does:**
1. Builds backend Docker image (FastAPI + PostgreSQL client)
2. Starts PostgreSQL 15 container
3. Waits for database using `pg_isready`
4. Runs database migrations (`alembic upgrade head`)
5. Starts FastAPI backend on port 8000
6. Starts Nuxt.js dev server on port 3000

**Expected Output:**
```
[+] Running 3/3
 ✔ Container amstar_db_local        Started
 ✔ Container amstar_backend_local   Started
 ✔ Container amstar_frontend_local  Started
```

---

## Health Check Guide

### 1. Verify All Containers Are Running

```bash
docker-compose -f docker-compose.local.yml ps
```

**Expected Output:**
```
NAME                     STATUS              PORTS
amstar_db_local          Up (healthy)        0.0.0.0:5432->5432/tcp
amstar_backend_local     Up (healthy)        0.0.0.0:8000->8000/tcp
amstar_frontend_local    Up                  0.0.0.0:3000->3000/tcp
```

✅ **All services should show "Up" or "Up (healthy)"**

---

### 2. IP & URL Verification

Open these URLs in your browser to confirm each service:

#### A. Frontend (Nuxt.js)
**URL:** http://localhost:3000

**Expected Result:**
- Nuxt.js application loads
- No console errors in browser DevTools (F12)
- Page renders correctly

#### B. Backend API Documentation (Swagger UI)
**URL:** http://localhost:8000/docs

**Expected Result:**
- FastAPI Swagger UI interface
- All API endpoints listed:
  - `/api/v1/auth/*`
  - `/api/v1/users/*`
  - `/api/v1/challenges/*`
  - `/api/v1/ratings/*`
- "Try it out" buttons are functional

#### C. Backend Health Endpoint
**URL:** http://localhost:8000/health

**Expected JSON Response:**
```json
{"status": "healthy"}
```

#### D. Caddy Proxy Entry Point (Optional - Production Only)
**Note:** In local development, Caddy is NOT used. Services are accessed directly.
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

In production (`docker-compose.prod.yml`), Caddy runs on:
- HTTP: `http://localhost`
- HTTPS: `https://your-domain.com`

---

### 3. Check Container Logs

#### View All Logs
```bash
docker-compose -f docker-compose.local.yml logs -f
```

#### View Individual Service Logs

**Database Logs:**
```bash
docker-compose -f docker-compose.local.yml logs -f db
```

Look for:
```
database system is ready to accept connections
```

**Backend Logs:**
```bash
docker-compose -f docker-compose.local.yml logs -f backend
```

Look for:
```
Waiting for PostgreSQL at db:5432...
PostgreSQL is up - continuing...
Running database migrations...
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Frontend Logs:**
```bash
docker-compose -f docker-compose.local.yml logs -f frontend
```

Look for:
```
✔ Nuxt 3.x ready
  > Local:    http://localhost:3000/
  > Network:  http://0.0.0.0:3000/
```

---

### 4. Network Connectivity Check

Verify that the frontend can communicate with the backend inside the Docker network.

#### A. Test Backend Health from Host Machine

```bash
curl http://localhost:8000/health
```

**Expected:**
```json
{"status":"healthy"}
```

#### B. Test Backend API Call from Frontend

Open `http://localhost:3000` and open browser console (F12):

```javascript
// Test API call from frontend to backend
fetch('http://localhost:8000/api/v1/health')
  .then(res => res.json())
  .then(data => console.log('Backend response:', data))
  .catch(err => console.error('Error:', err));
```

**Expected in Console:**
```
Backend response: {status: "healthy"}
```

#### C. Verify Container-to-Container Communication

Test that backend can reach database using service name `db`:

```bash
# Access backend container
docker-compose -f docker-compose.local.yml exec backend /bin/bash

# Inside container, test database connection
psql postgresql://amstar:amstar_dev_password@db:5432/amstar_db -c "SELECT 1;"

# Exit
exit
```

**Expected:**
```
 ?column?
----------
        1
```

#### D. Verify Frontend Can See Backend (Internal Network)

The frontend makes API calls using the environment variable:
- **From browser (external):** `http://localhost:8000/api/v1`
- **From server-side (SSR):** Uses Docker network service name `backend:8000`

Verify in `.env.local`:
```bash
NUXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

---

## Troubleshooting

### Issue 1: Database Connection Failed

**Symptom:**
```
psycopg2.OperationalError: could not connect to server
```

**Check Logs:**
```bash
docker-compose -f docker-compose.local.yml logs backend | grep -i error
```

**Solution:**
```bash
# 1. Verify database is healthy
docker-compose -f docker-compose.local.yml exec db pg_isready -U amstar

# 2. Check DATABASE_URL uses service name "db"
cat .env.local | grep DATABASE_URL
# Should be: postgresql://amstar:amstar_dev_password@db:5432/amstar_db

# 3. Restart backend
docker-compose -f docker-compose.local.yml restart backend
```

### Issue 2: Frontend Can't Reach Backend (CORS Errors)

**Symptom:** Console shows CORS errors or network errors

**Solution:**
```bash
# 1. Check CORS settings in .env.local
cat .env.local | grep BACKEND_CORS_ORIGINS
# Should include: "http://localhost:3000"

# 2. Verify backend CORS configuration
docker-compose -f docker-compose.local.yml logs backend | grep CORS

# 3. Restart backend with new CORS settings
docker-compose -f docker-compose.local.yml restart backend
```

### Issue 3: Nuxt.js Won't Start

**Symptom:** Frontend container exits or shows errors

**Check Logs:**
```bash
docker-compose -f docker-compose.local.yml logs frontend
```

**Solution:**
```bash
# 1. Clear node_modules volume
docker-compose -f docker-compose.local.yml down -v

# 2. Rebuild
docker-compose -f docker-compose.local.yml up -d --build frontend

# 3. Check Node version
docker-compose -f docker-compose.local.yml exec frontend node --version
# Should be: v18.x
```

### Issue 4: Port Already in Use

**Symptom:**
```
Error: bind: address already in use
```

**Solution:**
```bash
# Check what's using the port
netstat -ano | findstr :3000
netstat -ano | findstr :8000
netstat -ano | findstr :5432

# Kill the process or change ports in docker-compose.local.yml
```

### Issue 5: Migrations Not Running

**Symptom:** Tables not created in database

**Check Backend Logs:**
```bash
docker-compose -f docker-compose.local.yml logs backend | grep alembic
```

**Run Manually:**
```bash
# Run migrations manually
docker-compose -f docker-compose.local.yml exec backend alembic upgrade head

# Verify tables exist
docker-compose -f docker-compose.local.yml exec db psql -U amstar -d amstar_db -c "\dt"
```

---

## Service Name & Environment Variable Reference

### Service Names (Defined in docker-compose.local.yml)

| Service | Container Name | Internal Hostname | Port |
|---------|----------------|-------------------|------|
| Database | `amstar_db_local` | `db` | 5432 |
| Backend | `amstar_backend_local` | `backend` | 8000 |
| Frontend | `amstar_frontend_local` | `frontend` | 3000 |

### Critical Environment Variables in .env.local

```bash
# Database - MUST use service name "db"
POSTGRES_USER=amstar
POSTGRES_PASSWORD=amstar_dev_password
POSTGRES_DB=amstar_db
DATABASE_URL=postgresql://amstar:amstar_dev_password@db:5432/amstar_db

# Backend CORS - MUST include frontend port
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:8000","http://localhost"]

# Nuxt.js - For API calls from browser
NUXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

**CRITICAL:**
- Database host is `db` (not `localhost`) inside containers
- Backend service is `backend` (not `localhost`) inside containers
- Browser accesses via `localhost` from outside Docker

---

## Network Architecture

### Local Development

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Browser (http://localhost:3000)                           │
│     │                                                       │
│     ├─→ Nuxt.js Frontend (container: frontend:3000)       │
│     │      │                                               │
│     │      └─→ API calls to http://localhost:8000/api/v1  │
│     │                                                       │
│     └─→ FastAPI Backend (container: backend:8000)          │
│            │                                                │
│            └─→ Database (container: db:5432)               │
│                                                             │
│  Network: amstar_network_local                             │
└─────────────────────────────────────────────────────────────┘
```

### Container-to-Container Communication

Inside the Docker network, services use service names:
- Frontend SSR calls backend: `http://backend:8000/api/v1`
- Backend connects to DB: `postgresql://amstar:password@db:5432/amstar_db`

From your browser (outside Docker):
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

---

## Complete Verification Checklist

- [ ] All containers running: `docker-compose -f docker-compose.local.yml ps`
- [ ] Database healthy: `docker-compose -f docker-compose.local.yml exec db pg_isready -U amstar`
- [ ] Backend health: `curl http://localhost:8000/health`
- [ ] Backend API docs: Open `http://localhost:8000/docs`
- [ ] Frontend loads: Open `http://localhost:3000`
- [ ] No CORS errors in browser console
- [ ] Database tables created: `docker-compose -f docker-compose.local.yml exec db psql -U amstar -d amstar_db -c "\dt"`
- [ ] Frontend can call backend API (test in browser console)
- [ ] Backend logs show migrations ran successfully
- [ ] No errors in any container logs

---

## Clean Restart

If you need to start completely fresh:

```bash
# Stop all containers
docker-compose -f docker-compose.local.yml down

# Remove volumes (WARNING: Deletes database data)
docker-compose -f docker-compose.local.yml down -v

# Rebuild everything from scratch
docker-compose -f docker-compose.local.yml up -d --build

# Watch logs
docker-compose -f docker-compose.local.yml logs -f
```

---

## Success Criteria

✅ **Your setup is successful when:**

1. All 3 containers show "Up" status
2. `http://localhost:3000` loads Nuxt.js app
3. `http://localhost:8000/docs` shows FastAPI Swagger UI
4. `http://localhost:8000/health` returns `{"status":"healthy"}`
5. Browser console shows no CORS errors
6. API calls from frontend to backend work
7. Database has tables (verified via `\dt` in psql)

---

## Next Steps

Once verified:
1. Start building your Nuxt.js pages in `frontend/pages/`
2. Create API endpoints in `backend/app/api/v1/endpoints/`
3. Run tests
4. Deploy to production using `docker-compose.prod.yml`

---

**Platform:** AmStar Amateur Football Platform
**Stack:** FastAPI + Nuxt.js + PostgreSQL 15
**Documentation:** [LOCAL_TEST_GUIDE.md](LOCAL_TEST_GUIDE.md) | [NUXT_MIGRATION_SUMMARY.md](NUXT_MIGRATION_SUMMARY.md)
