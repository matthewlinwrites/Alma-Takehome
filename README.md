# Alma Lead Management API

A FastAPI backend for managing immigration law firm leads. Prospects can submit their information publicly, while attorneys access and manage leads through authenticated endpoints.

## Quick Start

### Prerequisites

- Python 3.11+

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd Alma

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
```

### Running the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`

### Running Tests

```bash
pytest tests/ -v
```

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/leads` | No | Submit a new lead (public) |
| `GET` | `/api/leads` | Yes | List all leads |
| `GET` | `/api/leads/{id}` | Yes | Get a specific lead |
| `PUT` | `/api/leads/{id}` | Yes | Update lead state |
| `DELETE` | `/api/leads/{id}` | Yes | Soft-delete a lead |

### Authentication

Protected endpoints require an `X-API-Key` header:

```bash
curl -H "X-API-Key: changeme-to-a-secure-key" http://127.0.0.1:8000/api/leads
```

For local development, you can disable auth:

```bash
AUTH_ENABLED=false uvicorn app.main:app --reload
```

### Example Usage

**Submit a lead (public):**
```bash
curl -X POST http://127.0.0.1:8000/api/leads \
  -F "first_name=Jane" \
  -F "last_name=Doe" \
  -F "email=jane@example.com" \
  -F "resume=@/path/to/resume.pdf"
```

**List all leads (authenticated):**
```bash
curl -H "X-API-Key: changeme-to-a-secure-key" http://127.0.0.1:8000/api/leads
```

**Mark lead as reached out:**
```bash
curl -X PUT http://127.0.0.1:8000/api/leads/{id} \
  -H "X-API-Key: changeme-to-a-secure-key" \
  -H "Content-Type: application/json" \
  -d '{"state": "REACHED_OUT"}'
```

## Interactive API Docs

Visit `http://127.0.0.1:8000/docs` for Swagger UI where you can test all endpoints interactively.

## Configuration

Environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./alma.db` | Database connection string |
| `API_KEY` | `changeme-to-a-secure-key` | API key for protected endpoints |
| `UPLOAD_DIR` | `./uploads` | Directory for resume uploads |
| `ATTORNEY_EMAIL` | `attorney@alma.com` | Email address for attorney notifications |
| `AUTH_ENABLED` | `true` | Set to `false` to disable auth for development |

## Project Structure

```
Alma/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── api/
│   │   ├── deps.py          # Dependencies (DB, auth)
│   │   └── routes/leads.py  # API endpoints
│   ├── models/lead.py       # SQLAlchemy ORM model
│   ├── schemas/lead.py      # Pydantic schemas
│   ├── services/
│   │   ├── lead.py          # Business logic
│   │   └── email.py         # Email notifications
│   └── db/session.py        # Database setup
├── tests/                   # Integration tests
├── uploads/                 # Resume storage
├── SYSTEM_DESIGN.md         # Design document
└── requirements.txt
```
