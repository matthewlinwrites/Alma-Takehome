# System Design: Alma Lead Management API

## Overview

This document describes the backend system for managing leads at an immigration law firm. The system allows prospective clients to submit their information publicly and enables attorneys to view and track outreach status through an authenticated internal interface.

## Goals

1. **Enable lead capture** — Provide a public-facing API for prospects to submit their contact information and resume
2. **Support attorney workflow** — Allow attorneys to view all leads and track which ones they've contacted
3. **Ensure data persistence** — Store leads reliably with support for soft deletion
4. **Notify stakeholders** — Send email confirmations to prospects and notifications to attorneys when new leads arrive
5. **Maintain security** — Protect internal endpoints while keeping the submission endpoint publicly accessible

## Non-Goals

1. **User authentication system** — No user accounts, login, or session management; simple API key suffices for internal access
2. **Frontend UI** — API-only; assumes a separate frontend will consume these endpoints
3. **Advanced lead management** — No assignment to specific attorneys, priority scoring, or pipeline stages beyond PENDING/REACHED_OUT
4. **File processing** — Resumes are stored as-is; no parsing, validation, or virus scanning
5. **Email delivery guarantees** — Email service is stubbed; production integration is out of scope

## User Stories

### Prospect (Public User)
- *As a prospect*, I want to submit my contact information and resume so that the law firm can review my case
- *As a prospect*, I want to receive a confirmation email so that I know my submission was received

### Attorney (Internal User)
- *As an attorney*, I want to view all submitted leads so that I can identify potential clients
- *As an attorney*, I want to see each lead's full details (name, email, resume) so that I can evaluate their case
- *As an attorney*, I want to mark a lead as "reached out" so that my team knows I've contacted them
- *As an attorney*, I want to delete spam or invalid leads so that the list stays clean

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                     │
├─────────────────────────────────┬───────────────────────────────────────┤
│         Prospect                │              Attorney                  │
│      (Public Form)              │          (Internal UI)                 │
└────────────┬────────────────────┴───────────────────┬───────────────────┘
             │                                        │
             │ POST /api/leads                        │ GET/PUT/DELETE /api/leads
             │ (no auth)                              │ (X-API-Key required)
             ▼                                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Application                            │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │
│  │   Routes    │───▶│  Services   │───▶│   Models    │                  │
│  │  (API Layer)│    │ (Business)  │    │   (ORM)     │                  │
│  └─────────────┘    └──────┬──────┘    └─────────────┘                  │
│                            │                                             │
│                            ▼                                             │
│                    ┌─────────────┐                                       │
│                    │Email Service│                                       │
│                    │  (Stub/SMTP)│                                       │
│                    └─────────────┘                                       │
└─────────────────────────────────────────────────────────────────────────┘
             │                                        │
             ▼                                        ▼
┌─────────────────────────────┐          ┌────────────────────────────────┐
│       SQLite Database       │          │      File Storage (uploads/)   │
│    (leads table)            │          │         (resumes)              │
└─────────────────────────────┘          └────────────────────────────────┘
```

## Data Model

### Lead Entity

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | UUID | Primary Key | Unique identifier |
| `first_name` | VARCHAR(100) | NOT NULL | Prospect's first name |
| `last_name` | VARCHAR(100) | NOT NULL | Prospect's last name |
| `email` | VARCHAR(255) | NOT NULL | Prospect's email address |
| `resume_path` | VARCHAR(500) | NULLABLE | Path to uploaded resume file |
| `state` | ENUM | NOT NULL, DEFAULT 'PENDING' | PENDING or REACHED_OUT |
| `created_at` | DATETIME | NOT NULL | Submission timestamp |
| `updated_at` | DATETIME | NOT NULL | Last modification timestamp |
| `deleted_at` | DATETIME | NULLABLE | Soft deletion timestamp |

### State Machine

```
┌─────────┐         PUT /api/leads/{id}         ┌─────────────┐
│ PENDING │ ───────────────────────────────────▶│ REACHED_OUT │
└─────────┘      {"state": "REACHED_OUT"}       └─────────────┘
   (initial)                                        (terminal)
```

- Leads start in `PENDING` state
- Only valid transition is `PENDING` → `REACHED_OUT`
- Transition is irreversible (attorneys cannot un-mark a lead)

## API Design

### Endpoints

| Method | Path | Auth | Request | Response |
|--------|------|------|---------|----------|
| `POST` | `/api/leads` | None | Multipart form (first_name, last_name, email, resume) | Lead object |
| `GET` | `/api/leads` | API Key | — | Array of Lead objects |
| `GET` | `/api/leads/{id}` | API Key | — | Lead object |
| `PUT` | `/api/leads/{id}` | API Key | `{"state": "REACHED_OUT"}` | Lead object |
| `DELETE` | `/api/leads/{id}` | API Key | — | Lead object |

### Authentication

- **Mechanism**: API key via `X-API-Key` header
- **Scope**: Required for all endpoints except `POST /api/leads`
- **Configuration**: Set via `API_KEY` environment variable
- **Development**: Can be disabled via `AUTH_ENABLED=false`

### Response Format

```json
{
  "id": "53156a9e-23c0-4bd0-9147-c1df9f13a2e2",
  "first_name": "Jane",
  "last_name": "Doe",
  "email": "jane@example.com",
  "resume_path": "./uploads/resume.pdf",
  "state": "PENDING",
  "created_at": "2026-02-05T03:35:20.460477",
  "updated_at": "2026-02-05T03:35:20.460483"
}
```

## Key Design Decisions

### 1. SQLite for Storage

**Decision**: Use SQLite as the database.

**Rationale**:
- Zero configuration required — no separate database server
- File-based persistence survives restarts
- SQLAlchemy ORM provides abstraction — can swap to PostgreSQL by changing one connection string
- Sufficient for expected load (internal tool, not high-traffic)

**Tradeoff**: Not suitable for horizontal scaling or concurrent writes at scale.

### 2. API Key Authentication

**Decision**: Use a simple shared API key rather than user accounts.

**Rationale**:
- Internal tool with small user base (attorneys at one firm)
- Avoids complexity of user registration, password management, sessions
- Easy to rotate if compromised
- Can be upgraded to OAuth/JWT later if needed

**Tradeoff**: No per-user audit trail; all authenticated requests look the same.

### 3. Soft Deletion

**Decision**: Use `deleted_at` timestamp rather than hard deletes.

**Rationale**:
- Preserves data for potential recovery or audit
- Queries automatically filter deleted records
- Simple to implement "undo" if needed later

**Tradeoff**: Database grows over time; may need periodic cleanup.

### 4. Local File Storage for Resumes

**Decision**: Store uploaded resumes on local filesystem.

**Rationale**:
- Simple to implement and debug
- No external dependencies (S3, etc.)
- Files are preserved with original names for easy identification

**Tradeoff**: Not suitable for distributed deployments; would need S3 or similar for production scale.

### 5. Stubbed Email Service

**Decision**: Email service logs to console rather than sending real emails.

**Rationale**:
- Demonstrates the integration point without requiring SMTP setup
- Easy to swap in SendGrid/SES/SMTP by implementing the same interface
- Avoids accidental email sends during development

**Tradeoff**: Must be replaced before production deployment.

## Future Considerations

1. **File storage**: Move to S3 or similar for production deployments
2. **Email integration**: Implement SendGrid or AWS SES for actual delivery
3. **Search/filtering**: Add query parameters to filter leads by state, date range, etc.
4. **Pagination**: Add limit/offset for large lead lists
5. **Audit logging**: Track who made what changes and when
6. **Rate limiting**: Protect public endpoint from abuse
