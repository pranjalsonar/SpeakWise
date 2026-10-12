# SpeakWise Backend Architecture

How the backend is organised and the rules every new feature follows.
For setup steps, see [README.md](README.md). For the frontend, see [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md).

## Stack

| Concern | Choice |
|---|---|
| Web framework | FastAPI |
| Database | PostgreSQL |
| ORM / migrations | SQLAlchemy 2.0 (typed `Mapped[...]` models) / Alembic |
| Password hashing | bcrypt |
| Auth | JWT bearer tokens (PyJWT, HS256) |
| Config | `backend/.env`, loaded by `app/core/config.py` |

## Folder structure

```
backend/
├── .env / .env.example        # config (never commit .env)
├── alembic/versions/          # migrations, one file per schema change
├── scripts/                   # one-off scripts: create_db.sql, seed_demo_users.py
└── app/
    ├── main.py                # creates the app, registers middleware, handlers, routers
    ├── core/                  # app-wide plumbing, no business logic
    │   ├── config.py          #   Settings, read from .env
    │   └── exceptions.py      #   AppException + subclasses, JSON error handler
    ├── db/
    │   ├── base.py            #   Declarative Base + constraint naming convention
    │   └── session.py         #   engine, SessionLocal, get_db dependency
    ├── constants/             # enums and fixed values (RoleId, Difficulty)
    ├── integrations/          # clients for external services, no business logic
    │   └── wikipedia/         #   client.py (HTTP, retries, circuit breaker), parser.py (pure)
    ├── models/                # SQLAlchemy models, shared by all modules
    ├── middleware/            # cross-cutting request handling
    │   ├── auth_middleware.py #   AuthMiddleware, get_current_user, require_roles
    │   ├── jwt_handler.py     #   create_access_token, verify_token, revoke_token
    │   └── token_blacklist.py #   in-memory revoked-token store
    └── modules/               # one folder per feature
        ├── auth/
        │   ├── auth_controller.py   # routes (HTTP layer)
        │   ├── auth_service.py      # business logic
        │   ├── auth_repository.py   # database queries
        │   ├── auth_schemas.py      # request/response models (Pydantic)
        │   └── auth_helpers.py      # module-specific utilities (password hashing)
        ├── users/
        │   ├── users_controller.py  # /users/me (self) + /users, /users/{id} (admin)
        │   ├── users_service.py     # profile rules: unique email, admin self-lockout guard
        │   ├── users_repository.py
        │   └── users_schemas.py     # PATCH bodies reject unknown fields (extra="forbid")
        ├── topics/                  # suggest / daily / custom topics (docs/TOPICS_READING_DESIGN.md)
        ├── reading/                 # reading-material versions; reading_builder.py = pure assembly logic
        ├── dashboard/
        │   ├── dashboard_controller.py  # GET /admin/dashboard (admin)
        │   ├── dashboard_service.py     # KPI maths, fills empty weeks, percentages
        │   ├── dashboard_repository.py  # aggregate SQL; periods computed in REPORTING_TIMEZONE
        │   └── dashboard_schemas.py
        └── health/
            └── health_controller.py
```

## Layers

Each request flows down through these layers. Each layer only calls the layer below it.

```
HTTP request
   │
   ▼
AuthMiddleware ────── rejects missing/invalid/revoked tokens with 401
   │                  sets request.state.user = TokenPayload
   ▼
Controller ────────── parses input (schemas), resolves dependencies, calls the service
   │
   ▼
Service ───────────── business rules; raises AppException subclasses
   │
   ▼
Repository ────────── SQLAlchemy queries only; returns models or None
   │
   ▼
PostgreSQL
```

| Layer | Does | Does not |
|---|---|---|
| **Controller** (`*_controller.py`) | Define routes, validate input with schemas, inject `db` / `current_user`, call one service function, return a response schema | Query the DB, contain business rules, raise `HTTPException` for business errors |
| **Service** (`*_service.py`) | Business logic, combine repositories, raise `UnauthorizedException`, `ForbiddenException`, `NotFoundException`, etc. | Know about `Request`/HTTP details, build raw SQL |
| **Repository** (`*_repository.py`) | Read/write models with SQLAlchemy | Contain business rules, raise HTTP errors, commit on behalf of the caller unless that's the function's whole purpose |
| **Schemas** (`*_schemas.py`) | Pydantic request/response models; never return ORM models directly | Hold logic beyond simple mapping (`from_model`) |
| **Helpers** (`*_helpers.py`) | Pure utilities used only by this module | Depend on `Request` or the DB session |

Code used by **several** modules goes in `core/`, `middleware/`, or `constants/`, not inside a module.

## Authentication

### Login flow

```
POST /api/v1/auth/login {email, password}
  → auth_controller.login
  → auth_service.login
      → auth_repository.get_user_by_email   (email is lowercased)
      → verify_password(password, user.hashed_password)   (bcrypt)
      → user missing or wrong password → 401 "Invalid email or password"
      → user.is_active is false         → 403 "Account is disabled"
      → jwt_handler.create_access_token(...)
  ← {access_token, token_type, expires_in, expires_at, user}
```

- Unknown emails and wrong passwords return the **same** 401 message, and unknown emails still run a bcrypt check against a dummy hash. So neither the response nor the timing tells an attacker whether an email is registered.
- Passwords are never stored, logged, or returned. Only the bcrypt hash is stored (`users.hashed_password`).

### Access token

Signed with `JWTSECRET_KEY` (HS256). Valid for `JWT_EXPIRE_HOURS` (default 8).

| Claim | Example | Meaning |
|---|---|---|
| `sub` | `"2"` | User ID (string, per the JWT spec) |
| `email` | `"admin@speakwise.com"` | Username |
| `name` | `"Admin"` | Full name |
| `role_id` | `1` | `RoleId`: 1 = admin, 2 = user |
| `role` | `"admin"` | Role name |
| `type` | `"access"` | Token type (reserved for refresh tokens later) |
| `iss` | `"speakwise-api"` | Issuer; tokens from anywhere else are rejected |
| `jti` | `"6af396ff..."` | Unique token ID, used for revocation |
| `iat` / `exp` | unix seconds | Issued at / expires at |

A JWT is **signed, not encrypted**: anyone holding the token can read its claims. Never put secrets or sensitive personal data in it.

### Request verification

`CORSMiddleware` wraps everything (it's registered last in `main.py`), so browser preflight requests and error responses carry CORS headers for the origins in `CORS_ORIGINS`.

`AuthMiddleware` then runs on every request:

1. Public paths pass through: `/health`, `/api/v1/auth/login`, `/docs`, `/redoc`, `/openapi.json`, and CORS preflight (`OPTIONS`). To make a new route public, add it to `PUBLIC_PATHS` in `auth_middleware.py`.
2. Otherwise it requires `Authorization: Bearer <token>`.
3. `verify_token` checks the signature, expiry, issuer, required claims, `type`, and the blacklist.
4. On success it sets `request.state.user` to a `TokenPayload`. On failure it returns 401 `{"detail": "..."}`.

Routes then read the user through dependencies:

```python
from app.constants.roles import RoleId
from app.middleware.auth_middleware import get_current_user, require_roles

@router.get("/sessions")
def list_sessions(current_user: TokenPayload = Depends(get_current_user)):
    ...  # any logged-in user

@router.get("/admin/users")
def list_users(current_user: TokenPayload = Depends(require_roles(RoleId.ADMIN))):
    ...  # admins only; others get 403
```

Token claims are a snapshot from login time. If a route needs current data (e.g. is the account still active?), load the user from the DB, as `GET /auth/me` and `/users/me` do.

### Profile updates (`users` module)

| Who | Can change | Route |
|---|---|---|
| Any logged-in user | Own `full_name`, `email` | `PATCH /users/me` |
| Admin | Any user's `full_name`, `email`, `role_id`, `is_active` | `PATCH /users/{id}` |
| Admin | Create a user (gets a temporary password) | `POST /users` |
| Admin | Reset any user's password to a new temporary one | `POST /users/{id}/reset-password` |

- **Temporary passwords:** generated with `secrets.token_urlsafe` (12 characters) and returned **once** in the response. Only the bcrypt hash is stored. There is no email service, so the admin shares the password with the user.
- **Last active** (`last_active_at` on admin responses) is the later of `users.last_login_at` (set on every successful login) and the user's latest talk session.
- **`GET /users`** searches `full_name`/`email` (case-insensitive, `%`/`_` taken literally), filters by `status`, pages with `skip`/`limit` (max 100), and returns `counts` (all/active/inactive) across all users for the page header.

- PATCH bodies are partial: only fields that are sent change. Unknown fields are rejected (422), so a user can't sneak `role_id` into `/users/me`.
- Emails stay unique and lowercase. A taken email returns 409.
- An admin can't demote or deactivate themselves (403), so the system can't end up with no admin.
- Changes to role or email don't rewrite existing tokens. The old claims stay in effect until the user logs in again. Deactivation takes effect on the next request that loads the user from the DB (`/users/me`, login). Other routes will honor it once they check the DB user too.

### Logout and the token blacklist

`POST /api/v1/auth/logout` adds the token's `jti` to `token_blacklist` with a TTL equal to the token's remaining lifetime, which is at most `JWT_EXPIRE_HOURS` (8h). Once a token expires its entry is no longer needed, since `exp` already rejects the token. Expired entries are removed:

- lazily, whenever the blacklist is read or written, and
- by a background sweep every 10 minutes (`sweep_token_blacklist` in `main.py`, started in the app lifespan).

The cache is never wiped all at once. A full wipe would un-revoke tokens logged out recently, and they would work again until their own expiry.

**Limitation:** the blacklist is in process memory. It is cleared on restart, and with several workers or servers each has its own copy. Before running more than one process in production, replace `TokenBlacklist` with Redis (`SET blacklist:<jti> 1 EX <seconds remaining>`). Only `token_blacklist.py` needs to change.

## Admin dashboard

`GET /api/v1/admin/dashboard` returns raw numbers. The frontend formats them ("+64 this month").

| Field | Definition |
|---|---|
| `total_users`, `new_users_this_month` | All users; those created since the 1st of this month |
| `active_users`, `active_users_pct` | Users with `is_active = true` (the admin Users toggle) |
| `total_sessions`, `sessions_this_week` | All talk sessions; those since Monday 00:00 |
| `minutes_spoken`, `avg_minutes_per_session` | Sum / average of `duration_seconds` (sessions without a duration are skipped) |
| `average_score`, `average_score_change_vs_last_month` | Mean `score` of scored sessions; this month's mean minus last month's (null if either month has none) |
| `sessions_per_week` | Last 8 weeks (Monday start), oldest first, empty weeks filled with 0 |
| `sessions_by_category` | All categories incl. 0; `pct` is the share of sessions that have a category |
| `recent_sessions` | Latest 5 **scored** sessions; topic is `topic_title`, else the AI summary's `topic_name` |

Periods use `REPORTING_TIMEZONE` and are computed in SQL (`AT TIME ZONE`), so they don't depend on the server's or Python's timezone data.

## Errors

- Services raise `AppException` subclasses from `app/core/exceptions.py`. The handler in `main.py` turns them into `{"detail": "<message>"}` with the right status code.
- Request validation errors are FastAPI's standard 422 `{"detail": [...]}`.
- Add a new subclass (e.g. `ConflictException`, 409) when a new status code is needed. Don't raise `HTTPException` from services.

| Status | When |
|---|---|
| 401 | Missing/invalid/expired/revoked token, wrong credentials |
| 403 | Authenticated but not allowed (wrong role, disabled account) |
| 404 | Resource not found |
| 409 | Conflict, e.g. email already used by another account |
| 422 | Request body/params failed validation, or `UnprocessableException` (may carry extra fields, e.g. `suggestion`) |
| 429 | `TooManyRequestsException`, e.g. the hourly custom-topic limit |
| 503 | `ServiceUnavailableException`, e.g. Wikipedia unreachable and nothing cached |

## API conventions

- All feature routes live under `/api/v1` (`settings.API_PREFIX`). `/health` stays at the root.
- Each module exposes one `router = APIRouter(prefix="/<module>", tags=["<Module>"])`, included in `main.py`.
- JSON field names are `snake_case`.
- Interactive docs: `/docs`. Use **Authorize** and paste the `access_token` to call protected routes.

## Database conventions

- Every schema change is an Alembic migration. Never change tables by hand or with `Base.metadata.create_all`.
- Constraint and index names come from the naming convention in `db/base.py` (`pk_`, `fk_`, `uq_`, `ix_`), so migrations stay predictable.
- Fixed reference data that every environment needs (e.g. `roles`) is inserted **in a migration**. Demo/test data goes in `scripts/` and never runs in production.
- New models must be imported in `app/models/__init__.py`, or Alembic won't see them.
- Use `RoleId.ADMIN` / `RoleId.USER` instead of raw `1` / `2`.

## Adding a new module

Example: a `talk_session` module.

1. Create `app/modules/talk_session/` with `__init__.py`, `talk_session_controller.py`, `talk_session_service.py`, `talk_session_repository.py`, `talk_session_schemas.py` (and `talk_session_helpers.py` only if needed).
2. Protect routes with `Depends(get_current_user)` or `Depends(require_roles(...))`.
3. Register the router in `main.py`: `app.include_router(talk_session_router, prefix=settings.API_PREFIX)`.
4. If you changed models, add a migration (see README → Making schema changes).

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | none (required) | PostgreSQL connection string |
| `JWTSECRET_KEY` | none (required, ≥ 32 chars) | Signs tokens. Changing it logs everyone out. |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRE_HOURS` | `8` | Access token lifetime |
| `WIKIPEDIA_USER_AGENT` | repo URL | Identifies the app to Wikipedia; include a contact |
| `WIKI_CACHE_DAYS` / `READING_TARGET_WORDS` / `READING_MAX_VERSIONS` / `CUSTOM_TOPICS_PER_HOUR` | 30 / 2500 / 5 / 10 | Topics & reading material (see docs/TOPICS_READING_DESIGN.md) |
| `REPORTING_TIMEZONE` | `UTC` (`.env.example`: `Asia/Kolkata`) | Timezone for dashboard periods ("this week" starts Monday 00:00, "this month" on the 1st). Evaluated by PostgreSQL. |
| `CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Comma-separated frontend origins allowed to call the API from a browser |
| `ENVIRONMENT` | `development` | `production` blocks the demo seed script |

The app refuses to start if `DATABASE_URL` or `JWTSECRET_KEY` is missing.

## Known gaps / next steps

- **Refresh tokens:** users must log in again after 8 hours.
- **Shared blacklist:** move to Redis before scaling beyond one process.
- **Rate limiting** on `/auth/login` to slow password guessing.
