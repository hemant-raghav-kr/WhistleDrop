# WhistleDrop — Speak Without Being Seen

> **GDG on Campus SRM 2026-27 Technical Domain Recruitment Submission**  
> A confidential whistleblower reporting platform engineered to eliminate retaliation risks through zero-knowledge anonymity, cryptographic tracking codes, and strict state-machine governance.

---

## Features

- **Zero-Knowledge Anonymous Reporting**: Submit sensitive misconduct, harassment, corruption, and technical reports without creating an account, logging in, or providing any personal identifying information.
- **Cryptographic Case Code Tracking**: Each report receives an unguessable 16-character case code generated via CSPRNG ($2^{80}$ entropy). Reporters check progress using this code without identifying themselves.
- **One-Way HMAC-SHA256 Storage**: Raw case codes are never stored on the server. The database persists only one-way HMAC-SHA256 digests, ensuring that even a database dump cannot reveal active tracking codes.
- **Strict Linear-Branch Lifecycle State Machine**: Enforces valid status transitions:
  - `SUBMITTED` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ `RESOLVED`
  - `SUBMITTED` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ `DISMISSED`
  - Terminal states (`RESOLVED` and `DISMISSED`) are immutable.
- **Staff Moderator Portal**: Authorized moderators authenticate via salted bcrypt password verification and signed JWT bearer tokens to inspect reports and append audit updates.
- **Secure Anonymous Evidence File Upload**: Submit supporting screenshots, logs, or PDF documents up to 10 MB. Files are stored in private object storage (Supabase Storage with automatic local filesystem fallback). Magic byte verification, MIME matching, and filename sanitization prevent executable uploads while stripping reporter metadata.
- **Audit Update History**: Every state change atomically records a public update message displayed on the reporter's case tracking timeline.
- **Concealed Internal Identifiers**: Database UUIDs, cryptographic hashes, and staff identities are strictly stripped from all public reporter endpoints.
- **Interactive Documentation**: Full OpenAPI 3.1.0 specification with interactive Swagger UI and ReDoc.

---

## Architecture

WhistleDrop enforces a clear separation of concerns between client and server layers:

```mermaid
flowchart TD
    subgraph Reporter ["Anonymous Reporter (Public Browser)"]
        R1["Submit Confidential Report"]
        R2["Store Plaintext Case Code (WD-XXXX-...)"]
        R3["Track Status by Case Code"]
    end

    subgraph BackendAPI ["WhistleDrop Backend (FastAPI Layered)"]
        direction TB
        E1["POST /api/v1/reports<br/>(CSPRNG generates Case Code)"]
        E2["GET /api/v1/reports/{case_code}<br/>(Computes HMAC-SHA256 for Lookup)"]
        E3["POST /api/v1/auth/login<br/>(Issues JWT Token)"]
        E4["PATCH /api/v1/moderator/reports/{id}/status<br/>(Enforces Strict State Machine)"]
    end

    subgraph ModeratorPortal ["Authenticated Moderator"]
        M1["Login via Username/Password"]
        M2["Review Reports Queue (Filtered)"]
        M3["Transition Status & Append Audit Updates"]
    end

    subgraph Database ["PostgreSQL / SQLite Storage"]
        T1[("reports<br/>• id: UUID<br/>• case_code_hash: HMAC-SHA256<br/>• category, status<br/>• description, evidence_url")]
        T2[("status_updates<br/>• id: UUID<br/>• report_id: FK<br/>• status, update_message")]
        T3[("moderators<br/>• id: UUID<br/>• email, username<br/>• hashed_password")]
    end

    R1 -->|Zero Personal Data| E1
    E1 -->|Hashes Code with Salt| T1
    E1 -->|Inserts Initial Update| T2
    E1 -.->|Returns Raw Code Once| R2

    R3 -->|Sends Case Code| E2
    E2 -->|Queries via HMAC Hash| T1
    E2 -->|Loads Sanitized Timeline| T2

    M1 -->|Credentials| E3
    E3 -->|Verifies Bcrypt Hash| T3
    M2 -->|JWT Auth| E4
    E4 -->|Updates Status| T1
    E4 -->|Appends Audit Entry| T2
```

---

## Tech Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, Lucide React, React Router v6 |
| **Backend** | Python 3.12+ (tested on Python 3.14), FastAPI, Uvicorn, Pydantic v2 |
| **ORM & Database** | SQLAlchemy 2.0, Alembic, PostgreSQL (Production) / SQLite (Local Dev) |
| **Authentication & Cryptography** | HMAC-SHA256, Python `secrets` CSPRNG, `bcrypt` (12 rounds), `PyJWT` |
| **Testing** | `pytest`, `httpx` (Starlette TestClient) |

---

## Privacy Model

WhistleDrop is built from the ground up around **confidentiality by design**:

1. **Zero Reporter Identity Attributes**: The report submission schema (`ReportCreate`) has no fields for name, email, phone number, department, or student ID.
2. **Zero Network & Device Footprints**: The application never collects or stores client IP addresses, browser user-agents, tracking cookies, or device fingerprints alongside reports.
3. **No Reporter Accounts**: There is no user table for reporters. Anonymity is absolute; reporters cannot be de-anonymized because no identity metadata exists.
4. **Internal ID Concealment**: Public endpoints never reveal database primary keys (UUIDs). Case lookup queries compute the HMAC-SHA256 hash of the tracking code to query the record.
5. **Sanitized Public Responses**: Case tracking returns only category, status, timestamps, and public status update messages. Narrative descriptions and moderator identities are concealed from public responses to prevent shoulder-surfing and unauthorized enumeration.

---

## Case Code Security

WhistleDrop case codes are formatted as `WD-XXXX-XXXX-XXXX-XXXX`:

```
WD - 7 K 9 X - 3 M P 8 - Y 4 B 2 - R T C 1
     └─ Blk 1 ─┘ └─ Blk 2 ─┘ └─ Blk 3 ─┘ └─ Blk 4 ─┘
```

### Cryptographic Entropy Calculation
- **CSPRNG Source**: Python's `secrets.choice()` draws securely from the system entropy pool.
- **Alphabet**: Crockford-inspired 32-character safe alphabet (`23456789ABCDEFGHJKMNPQRSTUVWXYZ`), excluding visually ambiguous characters (`0`, `O`, `1`, `I`, `L`).
- **Length**: 16 characters across 4 hyphenated blocks.
- **Total Combinations**:
  $$32^{16} = (2^5)^{16} = 2^{80} \approx 1.2089 \times 10^{24} \text{ possibilities}$$
- At 80 bits of cryptographic entropy, brute-force guessing or random enumeration is mathematically impossible.

### One-Way HMAC-SHA256 Server Storage
- The server computes $\text{HMAC-SHA256}(\text{CASE\_CODE\_SALT}, \text{normalized\_code})$ upon submission and tracking.
- Only the 64-character hexadecimal digest is stored in `reports.case_code_hash`.
- Even in the event of an unauthorized database dump, an attacker cannot reverse hashes into active tracking codes.

---

## Status Workflow

WhistleDrop implements a deterministic state machine:

```
          ┌─────────────┐
          │  SUBMITTED  │
          └──────┬──────┘
                 │
                 ▼
          ┌─────────────┐
          │UNDER_REVIEW │
          └──┬───────┬──┘
             │       │
      ┌──────┘       └──────┐
      ▼                     ▼
┌───────────┐         ┌───────────┐
│ RESOLVED  │         │ DISMISSED │
└───────────┘         └───────────┘
 (Terminal)            (Terminal)
```

- **`SUBMITTED` $\rightarrow$ `UNDER_REVIEW`**: Permitted when a moderator begins formal review.
- **`UNDER_REVIEW` $\rightarrow$ `RESOLVED`**: Permitted upon completion of corrective actions.
- **`UNDER_REVIEW` $\rightarrow$ `DISMISSED`**: Permitted if report lacks actionable evidence.
- **Illegal Transitions**: Direct jumps (e.g., `SUBMITTED` $\rightarrow$ `RESOLVED`) and transitions out of terminal states are rejected with `HTTP 400 Bad Request`.
- **Atomicity**: The status transition and its corresponding audit history entry are committed in a single database transaction.

---

## API

All endpoints are hosted under `/api/v1`.

| Method | Endpoint | Access | Status Codes | Description |
|---|---|---|---|---|
| `POST` | `/api/v1/reports` | Public | `201`, `422` | Submit confidential report (JSON or multipart with optional evidence file). Returns case code once. |
| `GET` | `/api/v1/reports/{case_code}` | Public | `200`, `404` | Track report status by case code. Excludes internal IDs. |
| `POST` | `/api/v1/auth/login` | Public | `200`, `401`, `403`, `422` | Moderator authentication. Issues signed JWT token. |
| `GET` | `/api/v1/moderator/reports` | Moderator JWT | `200`, `401`, `403` | List reports with pagination and status/category filters. |
| `GET` | `/api/v1/moderator/reports/{report_id}` | Moderator JWT | `200`, `401`, `403`, `404`, `422` | Get full report details by internal UUID including evidence files. |
| `PATCH` | `/api/v1/moderator/reports/{report_id}/status` | Moderator JWT | `200`, `400`, `401`, `403`, `404`, `422` | Transition report status and append audit note. |
| `GET` | `/api/v1/moderator/reports/{report_id}/evidence/{file_id}` | Moderator JWT | `200`, `401`, `403`, `404`, `422` | Get evidence metadata and signed download URL. |
| `GET` | `/api/v1/moderator/reports/{report_id}/evidence/{file_id}/stream` | Moderator JWT | `200`, `401`, `403`, `404`, `422` | Stream evidence file bytes directly. |
| `GET` | `/health` | Public | `200` | Liveness health probe. |

---

## Local Setup

### 1. Prerequisites
- Python 3.12+ (tested on Python 3.14)
- Node.js 18+ (tested on Node v24)
- PostgreSQL 14+ (optional for local dev; SQLite fallback is supported)

### 2. Backend Setup
```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Run database migrations (when PostgreSQL is active)
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
- API Base: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
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

## Environment Variables

### Backend (`backend/.env`)
| Variable | Required | Default / Placeholder | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | `postgresql+psycopg://user:pass@localhost:5432/whistledrop` | Database connection string |
| `JWT_SECRET` | Yes | `replace_with_a_secure_random_jwt_secret` | Secret key for signing moderator JWTs |
| `JWT_ALGORITHM` | No | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `60` | Moderator session lifetime (minutes) |
| `CASE_CODE_SALT` | Yes | `replace_with_a_random_salt` | HMAC-SHA256 pepper for case codes |
| `ENVIRONMENT` | No | `development` | Environment mode (`development` / `production`) |
| `PROJECT_NAME` | No | `"WhistleDrop API"` | Application display name |
| `CORS_ORIGINS` | No | `["http://localhost:5173", "http://localhost:3000"]` | Allowed CORS origins |
| `SUPABASE_URL` | No | `https://your-project.supabase.co` | Supabase project URL for cloud object storage |
| `SUPABASE_SERVICE_ROLE_KEY` | No | `your-supabase-service-role-key` | Private service role key for cloud storage |
| `SUPABASE_STORAGE_BUCKET` | No | `whistledrop-evidence` | Private bucket name for evidence files |
| `STORAGE_LOCAL_FALLBACK_DIR` | No | `storage_evidence` | Directory for local filesystem storage fallback |

### Frontend (`frontend/.env`)
| Variable | Required | Default / Placeholder | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | No | `/api/v1` | Base URL path for backend API requests |

> [!CAUTION]
> Never commit `.env` files containing real production credentials. Always use `.env.example` templates.

---

## Testing

### Backend Test Suite
WhistleDrop includes a comprehensive automated test suite (51 tests) using an in-memory SQLite database:

```bash
cd backend
python -m pytest -v
```

Test coverage includes:
- `tests/test_api_foundation.py`: Route accessibility, health check, CORS headers, error response structures.
- `tests/test_case_code.py`: Crockford alphabet validity, 80-bit entropy guarantees, HMAC-SHA256 deterministic hashing, normalization.
- `tests/test_backend_hardening.py`: Anonymous submission, case tracking, moderator auth (bcrypt + JWT), active/inactive guards, combinable filters, atomic state machine transitions, terminal state immutability, and authenticated UUID/auth matrix (401, 422, 404, 200).
- `tests/test_evidence_upload.py`: Comprehensive test coverage (18 scenarios) for secure anonymous evidence uploads: URL-only, file-only, URL+file, neither, supported MIME/magic-byte checks (PNG, JPG, WEBP, PDF, TXT), reject unsupported/executable types, reject oversized (>10MB) files, signature mismatch rejection, moderator authorized download/stream endpoints, cross-report authorization guards, and atomic storage cleanup on transaction rollback.

### Frontend Production Build
```bash
cd frontend
npm run build
```
Runs `tsc -b` and `vite build` to verify zero TypeScript compilation errors and production bundling.

---

## API Documentation

FastAPI automatically generates interactive OpenAPI documentation:
- **Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Alternative**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## Screenshots

The following core views demonstrate the WhistleDrop experience:

| View | Screenshot |
|---|---|
| **1. Home Page** | `docs/screenshots/01_home_page.png` |
| **2. Anonymous Report Form** | `docs/screenshots/02_submit_report.png` |
| **3. Case Code Success Screen** | `docs/screenshots/03_case_code_success.png` |
| **4. Case Tracking & Status Timeline** | `docs/screenshots/04_case_tracking.png` |
| **5. Moderator Dashboard Queue** | `docs/screenshots/05_moderator_dashboard.png` |
| **6. Report Inspection & Status Transition** | `docs/screenshots/06_moderator_detail.png` |

---

## Design Decisions

1. **Why No Reporter Accounts?**  
   Any user registration system creates an identifiable footprint (IP logs, confirmation emails, hashed passwords). By completely eliminating the concept of a reporter account, WhistleDrop makes de-anonymization architecturally impossible.

2. **Why 80 Bits of Case Code Entropy ($32^{16}$)?**  
   Using 16 Crockford Base32 characters produces $32^{16} = 2^{80} \approx 1.2089 \times 10^{24}$ possibilities. This makes guessing mathematically impossible while keeping the code human-readable (`WD-XXXX-XXXX-XXXX-XXXX`) and free of ambiguous characters (`0`/`O`, `1`/`I`/`L`).

3. **Why HMAC-SHA256 Instead of Plain SHA-256?**  
   Plain SHA-256 digests are vulnerable to precomputed dictionary attacks (rainbow tables) if database records are ever leaked. HMAC-SHA256 incorporates a server-side pepper (`CASE_CODE_SALT`), rendering external precomputed lookups ineffective.

4. **Why a Deterministic Linear-Branch State Machine?**  
   WhistleDrop restricts transitions to `SUBMITTED` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ `RESOLVED`/`DISMISSED`. Skipping directly to `RESOLVED` without review is prevented, and terminal states are locked to ensure an indisputable, tamper-evident audit history.

5. **Client-Side Storage Trade-Off (Moderator JWT)**:  
   Moderator bearer tokens are stored in `localStorage` for stateless client-side routing in this recruitment application. In production environments, tokens should be transitioned to HttpOnly SameSite secure cookies to mitigate Cross-Site Scripting (XSS) risks.

---

## Project Structure

```
WhistleDrop/
├── backend/
│   ├── alembic/                 # Database migrations
│   │   └── versions/            # 0001_initial_schema.py, 0002_add_evidence_files.py
│   ├── app/
│   │   ├── api/                 # API routers and dependency injection
│   │   │   ├── deps.py          # Database and JWT auth dependencies
│   │   │   └── v1/endpoints/    # reports.py, auth.py, moderator.py
│   │   ├── core/                # Configuration and security utilities
│   │   │   ├── config.py        # Pydantic Settings (DB, JWT, Storage)
│   │   │   └── security.py      # Bcrypt and JWT utilities
│   │   ├── db/                  # Database session and declarative base
│   │   ├── models/              # SQLAlchemy ORM models (Report, StatusUpdate, Moderator, EvidenceFile)
│   │   ├── schemas/             # Pydantic request/response schemas (report, status, evidence, etc.)
│   │   ├── services/            # Business logic (report_service, auth_service, storage_service)
│   │   └── utils/               # Case code generation, HMAC hashing, file_validation
│   ├── tests/                   # Pytest automated test suite (51 tests)
│   ├── requirements.txt         # Python dependencies
│   └── .env.example             # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── components/common/   # Reusable UI components (Button, Badge, Card, Modal, etc.)
│   │   ├── context/             # AuthContext (Moderator JWT state)
│   │   ├── pages/               # HomePage, SubmitReportPage, TrackReportPage, ModeratorDashboard, etc.
│   │   ├── services/            # Typed API client
│   │   └── types/               # TypeScript interfaces
│   ├── package.json             # Frontend dependencies and scripts
│   └── .env.example             # Frontend environment template
├── .gitignore                   # Excludes .env, node_modules, .venv, *.db, storage_evidence
└── README.md                    # Authoritative project documentation
```