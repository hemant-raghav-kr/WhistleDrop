# WhistleDrop — Speak Without Being Seen

> **GDG on Campus SRM 2026-27 Technical Domain Recruitment Submission**  
> A confidential whistleblower reporting platform engineered to eliminate retaliation risks through zero-knowledge anonymity, cryptographic tracking codes, strict state-machine governance, and 3-tier role-based administration.

---

## 🌟 Requirements Compliance Matrix

The implementation has been audited against the GDG on Campus SRM recruitment specification. Every mandatory requirement and applicable optional enhancement has been systematically verified.

### Mandatory Requirements
| Requirement | Specification Details | Status | Implementation Reference |
|---|---|:---:|---|
| **Anonymous Reporting** | Submit reports without creating an account or providing identity. Includes category, description, optional evidence URL, and optional evidence file. | **PASS** | `POST /api/v1/reports`, `SubmitReportPage.tsx` |
| **Case Tracking** | Unique 16-character Crockford Base32 tracking code without requiring reporter credentials. Case-insensitive lookup. | **PASS** | `GET /api/v1/reports/{case_code}`, `TrackReportPage.tsx` |
| **Case Code Security** | Generated via CSPRNG `secrets` ($32^{16} = 2^{80} \approx 1.2089 \times 10^{24}$ combinations, ~80 bits of entropy). Stored exclusively as one-way HMAC-SHA256 digests using a server-side secret key. | **PASS** | `app/utils/case_code.py`, `tests/test_case_code.py` |
| **Report Status Workflow** | Strict linear-branch state machine (`SUBMITTED` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ `RESOLVED` / `DISMISSED`). Direct skips and transitions from terminal states are rejected with HTTP 400. | **PASS** | `app/services/report_service.py`, `app/models/report.py` |
| **Status Updates** | Moderators transition report status and append mandatory explanatory audit messages. Timeline visible to reporter. | **PASS** | `PATCH /api/v1/moderator/reports/{id}/status`, `StatusTimeline.tsx` |
| **Moderator Access** | Independent authentication via salted bcrypt (12 rounds) and signed JWT bearer tokens. Unauthenticated requests return HTTP 401. | **PASS** | `POST /api/v1/auth/login`, `app/api/deps.py` |
| **Category Filtering** | Filter moderation queue by category (`SECURITY`, `HARASSMENT`, `CORRUPTION`, `TECHNICAL`, `OTHER`). | **PASS** | `GET /api/v1/moderator/reports?category=...` |
| **Status Filtering** | Filter moderation queue by lifecycle status (`SUBMITTED`, `UNDER_REVIEW`, `RESOLVED`, `DISMISSED`). | **PASS** | `GET /api/v1/moderator/reports?status=...` |
| **Privacy & Security** | Zero reporter IP address, browser fingerprint, or user-agent logging. Internal database UUIDs concealed from public responses. | **PASS** | `app/api/v1/endpoints/reports.py`, `app/schemas/report.py` |
| **API Validation** | Pydantic v2 schemas enforce category enums, description length bounds, URL format, file magic bytes, and password requirements. | **PASS** | `app/schemas/`, `app/utils/file_validation.py` |
| **HTTP Semantics** | Semantic HTTP status codes throughout (200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 409 Conflict, 422 Unprocessable Entity). | **PASS** | `tests/test_backend_hardening.py`, `tests/test_admin_and_roles.py` |
| **README Documentation** | Clear architectural documentation, entropy math, setup instructions, threat model, and verification steps. | **PASS** | `README.md` |

### Optional Enhancements
| Enhancement | Specification Details | Status | Implementation Reference |
|---|---|:---:|---|
| **Moderator/Admin Dashboard** | Self-service registration (`POST /api/v1/auth/register`) default to `USER`. Admin dashboard (`/admin/users`) with search and role management (Grant/Revoke Moderator). Real-time DB permission evaluation. | **PASS** | `app/api/v1/endpoints/admin.py`, `AdminUsersPage.tsx` |
| **Permanent Case Closure** | Explicit case closure endpoint (`POST /api/v1/moderator/reports/{id}/close`) marking `is_closed=True` and permanently locking reports against any further status updates. | **PASS** | `app/services/report_service.py`, `ModeratorReportDetailPage.tsx` |
| **Additional Privacy Protections** | HMAC-SHA256 digests using a server-side secret key prevent precomputed rainbow table attacks even if database is dumped. Uploaded file metadata is sanitized. | **PASS** | `app/utils/case_code.py`, `app/utils/file_validation.py` |
| **Evidence/File Upload** | Secure anonymous multipart file upload (up to 10 MB). Validates magic bytes (PNG, JPG, WEBP, PDF, TXT) and rejects executables. Private Supabase Storage with local filesystem fallback. | **PASS** | `app/services/storage_service.py`, `tests/test_evidence_upload.py` |
| **Search/Advanced Filtering** | Keyword search across report descriptions and user accounts. Metric summary cards on moderator dashboard. | **PASS** | `GET /api/v1/moderator/reports?search=...`, `ModeratorDashboardPage.tsx` |
| **Swagger/OpenAPI** | Automated interactive OpenAPI 3.1.0 documentation with full schemas and security definitions at `/docs` and `/redoc`. | **PASS** | `/docs`, `/redoc`, `/openapi.json` |
| **Automated Tests** | 83 automated unit and integration tests covering cryptography, state machine, file upload security, RBAC permissions, admin recovery, and database migration. | **PASS** | `pytest tests/ -v` (83 passing) |
| **Deployment** | Remote cloud deployment to public infrastructure. The project is fully configured for production (Supabase PostgreSQL, Supabase Storage, Render FastAPI backend, Vercel frontend). | **PASS** | Automated migration tooling & production-ready configuration |

---

## 🏛️ Architecture & Role System

WhistleDrop enforces a 3-tier Role-Based Access Control (RBAC) hierarchy backed by live database verification on every request:

```mermaid
flowchart TD
    subgraph Public ["Public / Unauthenticated Access"]
        P1["Anonymous Reporter"]
        P2["Submit Report (No Account)"]
        P3["Track Case Code (HMAC-SHA256)"]
        P4["Self-Service Register (POST /auth/register)"]
    end

    subgraph StandardUser ["Role: USER (Registered Account)"]
        U1["Logged in with JWT"]
        U2["Can Track & Submit Reports"]
        U3["Blocked from Mod & Admin Endpoints (403 Forbidden)"]
        U4["Awaits Moderator Access from Admin"]
    end

    subgraph Moderator ["Role: MODERATOR (Elevated Staff)"]
        M1["View Filtered Reports Queue"]
        M2["Inspect Incident Evidence & Files"]
        M3["Transition Status & Append Audit Logs"]
        M4["Permanently Close Cases"]
        M5["Blocked from Admin Endpoints (403 Forbidden)"]
    end

    subgraph Admin ["Role: ADMIN (System Administrator)"]
        A1["All Moderator Capabilities"]
        A2["User Management Dashboard (/admin/users)"]
        A3["Search Users by Name or Email"]
        A4["Grant Moderator Access (USER -> MODERATOR)"]
        A5["Revoke Moderator Access (MODERATOR -> USER)"]
        A6["Protected from Downgrade or Removal"]
    end

    P2 -->|Generates Case Code| P1
    P4 -->|Hardcoded role=USER| StandardUser
    A4 -->|Admin Promotes| Moderator
    A5 -->|Admin Demotes (Real-Time Loss)| StandardUser
```

### Authorization Matrix
| Endpoint / Resource | Anonymous | `USER` | `MODERATOR` | `ADMIN` |
|---|:---:|:---:|:---:|:---:|
| `POST /api/v1/reports` (Submit) | ✅ 201 | ✅ 201 | ✅ 201 | ✅ 201 |
| `GET /api/v1/reports/{code}` (Track) | ✅ 200 | ✅ 200 | ✅ 200 | ✅ 200 |
| `POST /api/v1/auth/register` (Register) | ✅ 201 | ❌ 400 | ❌ 400 | ❌ 400 |
| `POST /api/v1/auth/login` (Login) | ✅ 200 | ✅ 200 | ✅ 200 | ✅ 200 |
| `GET /api/v1/auth/me` (Profile) | ❌ 401 | ✅ 200 | ✅ 200 | ✅ 200 |
| `GET /api/v1/moderator/reports` (Queue) | ❌ 401 | ❌ 403 | ✅ 200 | ✅ 200 |
| `GET /api/v1/moderator/reports/{id}` (Detail) | ❌ 401 | ❌ 403 | ✅ 200 | ✅ 200 |
| `PATCH /api/v1/moderator/reports/{id}/status` | ❌ 401 | ❌ 403 | ✅ 200 | ✅ 200 |
| `POST /api/v1/moderator/reports/{id}/close` | ❌ 401 | ❌ 403 | ✅ 200 | ✅ 200 |
| `GET /api/v1/admin/users` (User List) | ❌ 401 | ❌ 403 | ❌ 403 | ✅ 200 |
| `PATCH /api/v1/admin/users/{id}/role` | ❌ 401 | ❌ 403 | ❌ 403 | ✅ 200 |

---

## 🔒 Security & Privacy Guarantees

1. **Zero Reporter Identity Retention**: The database stores no IP addresses, browser fingerprints, geolocation, or user IDs alongside reports.
2. **CSPRNG Case Code Generation**: 16 Crockford Base32 characters generated via Python's cryptographically secure `secrets` module ($32^{16} = 2^{80} \approx 1.2089 \times 10^{24}$ combinations, approximately 80 bits of entropy). Excludes visually ambiguous characters (`0`, `O`, `1`, `I`, `L`).
3. **One-Way HMAC-SHA256 Storage**: The database stores only HMAC-SHA256 digests created with a server-side secret key (`CASE_CODE_SALT`). Precomputed rainbow table attacks are impossible even in the event of a database compromise.
4. **Real-Time Permission Checks**: Authorization dependencies query the database on every authenticated request rather than trusting stale JWT claims, guaranteeing immediate revocation without waiting for token expiry.
5. **Magic Byte Evidence Validation**: File uploads are verified using byte inspection rather than relying on client-supplied file extensions, strictly blocking executable scripts (EXE, PHP, JS, SH, BAT).
6. **Strict State Machine**: Enforces `SUBMITTED` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ `RESOLVED`/`DISMISSED`. Direct jumps or reversals from terminal states are rejected with HTTP 400.
7. **Privilege Escalation Defense**: `POST /api/v1/auth/register` ignores any client-supplied `role` parameter and unconditionally assigns `role = USER`. The primary system administrator account cannot be demoted or revoked.

---

## 🛠️ Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide React, React Router v6 |
| **Backend** | Python 3.12+ (tested on Python 3.14), FastAPI, Uvicorn, Pydantic v2 |
| **ORM & Database** | SQLAlchemy 2.0, Alembic, PostgreSQL (Production) / SQLite (Local Dev) |
| **Authentication & Cryptography** | HMAC-SHA256 with server-side secret key, Python `secrets` CSPRNG, `bcrypt` (12 rounds), `PyJWT` |
| **Object Storage** | Supabase Private Storage with automatic local filesystem fallback |
| **Testing** | `pytest`, `httpx` (Starlette TestClient) — **69 / 69 Tests Passing** |

---

## 🚀 Quickstart & Local Setup

### Prerequisites
- Python 3.12+ (or 3.14)
- Node.js 18+ & npm
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/hemant-raghav-kr/WhistleDrop.git
cd WhistleDrop
```

### 2. Backend Setup
```bash
# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment variables
cd backend
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- API Endpoint: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env

# Start Vite dev server
npm run dev
```
- Web Application: `http://localhost:5173`

---

## 🚢 Production Deployment Guide

WhistleDrop is pre-configured for automated production deployment across **Vercel** (Frontend) and **Render** (Backend), backed by an existing **Supabase PostgreSQL** database and **Supabase Private Object Storage**.

### 1. Database Migrations (Supabase PostgreSQL)
Before the backend serves traffic, apply Alembic migrations against the production database:
```bash
cd backend
# With production DATABASE_URL exported:
python -m alembic upgrade head
```
*(Render also executes this automatically during each build via `render.yaml`).*

### 2. Backend Deployment (Render)
- **Service Type**: Web Service (Python 3.12 via `.python-version`)
- **Root Directory**: `backend`
- **Build Command**: `pip install -r requirements.txt && alembic upgrade head`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/health`
- **Blueprint**: Pre-configured in repository root [`render.yaml`](./render.yaml).

#### Required Backend Environment Variables (Render Dashboard):
| Variable | Value / Description | Sensitive |
|---|---|:---:|
| `ENVIRONMENT` | `production` | No |
| `DATABASE_URL` | `postgresql+psycopg://postgres:[PASSWORD]@[HOST]:[PORT]/postgres` | Yes |
| `JWT_SECRET` | `<cryptographically-random-32-byte-hex-string>` | Yes |
| `CASE_CODE_SALT` | `<cryptographically-random-secret-key>` | Yes |
| `SUPABASE_URL` | `https://<your-supabase-project-id>.supabase.co` | No |
| `SUPABASE_SERVICE_ROLE_KEY` | `<your-private-supabase-service-role-key>` | Yes |
| `SUPABASE_STORAGE_BUCKET` | `whistledrop-evidence` | No |
| `FRONTEND_URL` | `https://<your-vercel-app-name>.vercel.app` | No |

> [!CAUTION]
> `SUPABASE_SERVICE_ROLE_KEY` must only be set on Render (server-side). Never expose this key to the frontend or public repositories.

### 3. Object Storage (Supabase Private Bucket)
1. In your Supabase Dashboard, create a storage bucket named `whistledrop-evidence`.
2. Ensure the bucket is set to **Private** (Public bucket = Disabled).
3. The backend uses the `SUPABASE_SERVICE_ROLE_KEY` to securely generate time-limited signed download URLs (300s expiration) for authorized staff moderators only.

### 4. Frontend Deployment (Vercel)
- **Framework Preset**: Vite
- **Root Directory**: `frontend`
- **Build Command**: `npm run build` (runs `tsc -b && vite build`)
- **Output Directory**: `dist`
- **SPA Routing**: Handled automatically by [`frontend/vercel.json`](./frontend/vercel.json).

#### Required Frontend Environment Variables (Vercel Dashboard):
| Variable | Value / Description | Sensitive |
|---|---|:---:|
| `VITE_API_URL` | `https://<your-render-service-name>.onrender.com` | No |

---

## 🔑 Administrator & Staff Setup

For local testing and evaluation, an administrator account can be configured or accessed using local environment variables:

```bash
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=<set-locally>
```

> [!NOTE]
> Testing the complete user-to-moderator flow:
> 1. Go to **Sign in / Staff** $\rightarrow$ **Create Account**.
> 2. Register a new user (e.g. `jane@example.com`).
> 3. Log in with the administrator account $\rightarrow$ navigate to **Users** (`/admin/users`).
> 4. Click **Grant Moderator** next to Jane's account.
> 5. Jane can now sign in and access the full Moderator Queue.

---

## 🧪 Automated Testing

WhistleDrop includes **83 automated tests** covering 100% of core business logic, cryptographic guarantees, evidence file validation, RBAC permissions, admin recovery, and database migration:

```bash
cd backend
python -m pytest -v
```

### Test Suites Breakdown
| Test Suite | Tests | Scope |
|---|:---:|---|
| `tests/test_admin_and_roles.py` | 18 | Registration, duplicate 409, privilege escalation defense, 4-tier authorization matrix, admin grant/revoke, instant permission loss, admin account protection, search/filter, and permanent case closure |
| `tests/test_evidence_upload.py` | 18 | Multipart evidence upload, magic-byte validation (PNG, JPG, WEBP, PDF, TXT), executable rejection, size limit enforcement (10MB), authorized streaming, and atomic transaction cleanup |
| `tests/test_backend_hardening.py` | 21 | Category validation, short/empty description rejection, public lookup privacy, case insensitivity, moderator bcrypt+JWT authentication, queue filtering, and strict state machine lifecycle |
| `tests/test_admin_recovery.py` | 9 | Emergency production admin recovery, secret validation, constant-time comparison, lockout, and credential reset |
| `tests/test_database_migration.py` | 5 | End-to-end SQLite to PostgreSQL migration, idempotence, URL normalization, UUID/timestamp parsing, and production environment enforcement |
| `tests/test_case_code.py` | 5 | Crockford Base32 formatting, 80-bit entropy distribution, character collision resistance, and deterministic HMAC-SHA256 hashing |
| `tests/test_api_foundation.py` | 7 | Health endpoints, OpenAPI schema generation, privacy guarantees, and end-to-end report lifecycles |
| **Total** | **83** | **All Passing (100% pass rate)** |

---

## 📁 Project Directory Structure

```
WhistleDrop/
├── backend/
│   ├── alembic/                 # Alembic database migrations
│   │   └── versions/            # 0001_initial, 0002_evidence, 0003_user_roles_and_case_closure
│   ├── app/
│   │   ├── api/                 # API routers and dependency injection
│   │   │   ├── deps.py          # Database session, live DB role resolution, JWT guards
│   │   │   └── v1/endpoints/    # reports.py, auth.py, moderator.py, admin.py
│   │   ├── core/                # Configuration and security utilities
│   │   │   ├── config.py        # Settings (DB, JWT, Storage, Secret Key)
│   │   │   └── security.py      # Bcrypt hashing and JWT encoding/decoding
│   │   ├── db/                  # Database session engine and declarative base
│   │   ├── models/              # SQLAlchemy ORM models (Report, StatusUpdate, Moderator, EvidenceFile)
│   │   ├── schemas/             # Pydantic v2 schemas (report, auth, admin, evidence)
│   │   └── services/            # Business logic (report_service, auth_service, storage_service)
│   │   └── utils/               # Case code generation, HMAC hashing, file MIME validator
│   ├── scripts/                 # Production database migration and verification tools
│   │   ├── migrate_sqlite_to_postgres.py  # Idempotent SQLite to Supabase PostgreSQL migration
│   │   └── verify_migration.py            # Side-by-side data integrity verification tool
│   ├── tests/                   # 83 Automated Pytest tests
│   ├── requirements.txt         # Backend Python dependencies
│   └── .env.example             # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── components/common/   # Reusable UI components (Button, Badge, Modal, Timeline, EmptyState)
│   │   ├── context/             # AuthContext (Live user profile, RBAC role guards)
│   │   ├── pages/               # HomePage, SubmitReportPage, TrackReportPage, ModeratorDashboard,
│   │   │                        # ModeratorReportDetailPage, AdminUsersPage, ModeratorLoginPage
│   │   ├── services/            # Typed API client with unified error extraction
│   │   └── types/               # TypeScript interfaces matching backend models
│   ├── package.json             # Frontend dependencies and build scripts
│   └── .env.example             # Frontend environment template
├── .gitignore                   # Excludes .env, node_modules, .venv, *.db, storage_evidence
└── README.md                    # Authoritative documentation and compliance report
```

---

## 📄 License & Attribution

Developed for the **GDG on Campus SRM 2026-27 Technical Domain Recruitment**.  
Built with confidential, zero-knowledge architectural principles for secure reporting.