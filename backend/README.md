# WhistleDrop Backend Service

Layered REST API service powering **WhistleDrop** ("Speak Without Being Seen") for the GDG on Campus SRM Technical Domain recruitment.

## Features & Hardened Capabilities

1. **Anonymous Reporting**:
   - Zero identity footprints (no user accounts, names, emails, phones, IP logging, or device fingerprinting).
   - Supported categories: `SECURITY`, `HARASSMENT`, `CORRUPTION`, `TECHNICAL`, `OTHER` (with case-insensitive normalization).
   - Input validation on description length (10-10,000 characters) and evidence URLs (HTTP/HTTPS).

2. **Cryptographic Case Codes**:
   - Unpredictable codes generated via Python `secrets` CSPRNG using 32 Crockford safe characters (`23456789ABCDEFGHJKMNPQRSTUVWXYZ`).
   - Entropy: 16 characters $\times$ 32 symbols = $32^{16} = 2^{80} \approx 1.2089 \times 10^{24}$ combinations (~80 bits of entropy).
   - Stored strictly as a one-way HMAC-SHA256 digest using a server-side secret key in the database.

3. **Case Tracking**:
   - Query by case code: `GET /api/v1/reports/{case_code}`.
   - Strictly sanitizes public output: exposes category, status, submitted_at, updated_at, and public updates timeline.
   - Internal database UUIDs, cryptographic hashes, and moderator identities are completely concealed.

4. **Strict Linear Status Workflow**:
   - Valid lifecycle branches:
     - `SUBMITTED` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ `RESOLVED`
     - `SUBMITTED` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ `DISMISSED`
   - All invalid transitions rejected with HTTP 400 Bad Request.
   - Status updates are **transactionally atomic** with audit logging into `status_updates`.

5. **Moderator Management & JWT Auth**:
   - Salted bcrypt password verification.
   - Signed JWT bearer authentication.
   - Granular error codes: HTTP 401 for bad credentials; HTTP 403 for deactivated moderator accounts.
   - Filter reports queue by status, category, or both combined with pagination.

## Local Execution & Commands

```powershell
cd backend
..\.venv\Scripts\Activate.ps1
copy .env.example .env

# Run automated test suite (69 tests covering all core and optional features):
pytest tests/ -v

# Run database migrations:
alembic upgrade head

# Start development server:
uvicorn app.main:app --reload --port 8000
```

Swagger API Documentation: `http://localhost:8000/docs`
Health probe: `http://localhost:8000/health`
