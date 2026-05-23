# MPC Autofill — Simplified Architecture

Image aggregation & print automation for your tabletop gaming community.

## Architecture

This project consists of three main components:

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **backend/** | Python, FastAPI, SQLModel | REST API for images, sources, projects, auth |
| **frontend-v2/** | Next.js 14, TypeScript, TailwindCSS | Web UI for search, upload, project building |
| **autofill-tool/** | Python, Playwright | Desktop tool to automate MPC website |

## Features

- **Search & Browse** — Full-text search across all available card images
- **Direct Upload** — Upload your own card images (stored in S3-compatible storage)
- **Google Drive Integration** — Connect community or personal Google Drives as image sources
- **Project Builder** — Assign images to card slots (front & back faces)
- **Export & Autofill** — Export project as JSON, run the autofill tool to automate MPC

## Quick Start

### Using Docker Compose (recommended)

```bash
# Start all services (backend, frontend, MinIO storage)
docker compose up --build

# Access the app at http://localhost:3000
# API docs at http://localhost:8000/docs
# MinIO console at http://localhost:9001 (minioadmin/minioadmin)
```

### Manual Development Setup

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your settings
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend-v2
npm install
npm run dev
```

#### Autofill Tool

```bash
cd autofill-tool
pip install -r requirements.txt
playwright install chromium
python autofill.py path/to/project.json
```

## Image Sources

The system supports multiple image source types:

### 1. Community Google Drives
Pre-configured shared Google Drives indexed by the system using a service account. These are visible to all users.

### 2. Personal Google Drive
Users connect their own Google Drive via OAuth. They select folders to index, and images appear in their personal library.

### 3. Direct Upload
Users upload images directly through the web interface. Images are stored in S3-compatible storage (MinIO for self-hosting, Cloudflare R2 or AWS S3 for production).

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

### Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/google/login` | Authenticate with Google |
| GET | `/api/auth/me` | Get current user |
| POST | `/api/images/search` | Search images |
| POST | `/api/images/upload` | Upload an image |
| GET | `/api/sources/` | List image sources |
| POST | `/api/sources/` | Create a source |
| POST | `/api/sources/{id}/sync` | Sync a Google Drive source |
| GET | `/api/projects/` | List projects |
| POST | `/api/projects/` | Create a project |
| GET | `/api/projects/{id}/export` | Export project for autofill |

## Configuration

Environment variables (see `backend/.env.example`):

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | JWT signing secret |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret |
| `S3_ENDPOINT_URL` | S3 storage endpoint |
| `S3_ACCESS_KEY` | S3 access key |
| `S3_SECRET_KEY` | S3 secret key |
| `S3_BUCKET_NAME` | S3 bucket name |

## Project Structure

```
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── main.py          # App entry point
│   │   ├── config.py        # Settings from env
│   │   ├── models.py        # SQLModel database models
│   │   ├── deps.py          # Dependency injection
│   │   ├── database.py      # DB engine setup
│   │   ├── routers/         # API route handlers
│   │   │   ├── auth.py      # Authentication
│   │   │   ├── images.py    # Image CRUD & search
│   │   │   ├── sources.py   # Source management
│   │   │   └── projects.py  # Project & slot management
│   │   └── services/        # Business logic
│   │       ├── google_drive.py
│   │       ├── storage.py
│   │       └── indexer.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend-v2/             # Next.js frontend
│   ├── src/app/             # Pages (search, upload, library, projects)
│   ├── src/lib/api.ts       # API client
│   └── Dockerfile
├── autofill-tool/           # Playwright automation
│   ├── autofill.py
│   └── requirements.txt
├── docker-compose.yml       # Full stack deployment
└── ARCHITECTURE.md          # This file
```
