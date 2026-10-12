# SpeakWise Backend

FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL, with JWT auth.

Read [ARCHITECTURE.md](ARCHITECTURE.md) before adding code: it covers the folder structure, layers (controller → service → repository), and auth.

## First-time setup (after cloning / pulling)

Run every command below from the `backend` folder.

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ running locally on port 5432, and the password for its `postgres` superuser

> **`psql` not recognized?** It ships with PostgreSQL but often isn't on `PATH`.
> Use the full path instead, e.g. `& "C:\Program Files\PostgreSQL\18\bin\psql.exe"`
> (adjust the drive/version to match your install).

### 1. Install dependencies

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

macOS/Linux: use `source .venv/bin/activate` and drop the `.\.venv\Scripts\` prefix from the commands below.

### 2. Create the database user and database

```powershell
psql -U postgres -h localhost -f scripts/create_db.sql
```

Enter the `postgres` password when prompted. This creates:

| What | Value |
|---|---|
| Login role | `speakwise_app` (password `speakwise@1234`) |
| Database | `speakwise_db`, owned by `speakwise_app` |

The script is safe to re-run; it skips anything that already exists.
Run it with `psql`, not the pgAdmin query tool (it uses `psql`-only commands like `\gexec`).

### 3. Create your `.env`

```powershell
copy .env.example .env
```

`.env` is gitignored, so each developer needs their own. The default `DATABASE_URL` already matches step 2:

```
DATABASE_URL=postgresql+psycopg2://speakwise_app:speakwise%401234@localhost:5432/speakwise_db
```

The `@` in the password is written as `%40` because `@` has a special meaning in URLs.
If you change the password, URL-encode any special characters the same way.

Then generate your own JWT secret and paste it into `JWTSECRET_KEY` in `.env`:

```powershell
.\.venv\Scripts\python -c "import secrets; print(secrets.token_urlsafe(32))"
```

The app won't start without a secret of at least 32 characters. `JWT_EXPIRE_HOURS` (default `8`) sets how long a login lasts.

### 4. Create the tables

```powershell
.\.venv\Scripts\alembic upgrade head
```

This applies every migration in `alembic/versions/` in order: all tables, plus the `roles` table seeded with `1 = admin` and `2 = user`.
Confirm with `.\.venv\Scripts\alembic current`. It should end in `(head)`.

### 5. Seed the demo accounts

```powershell
.\.venv\Scripts\python scripts/seed_demo_users.py
```

| Email | Password | Role |
|---|---|---|
| admin@speakwise.com | admin@123 | admin (1) |
| raj@gmail.com | raj@123 | user (2) |

Safe to re-run; it resets these two accounts to the values above. It refuses to run when `ENVIRONMENT=production`.

Optional: fill the admin dashboard with demo data (24 students and ~200 sessions over 12 weeks):

```powershell
.\.venv\Scripts\python scripts/seed_demo_sessions.py
```

Demo students use `@demo.speakwise.com` emails and the password `demo@123`. Re-running replaces only those users and their sessions.

### 5b. Seed the topic bank and pre-build reading material

```powershell
.\.venv\Scripts\python scripts/seed_topics.py              # 30 curated topics; checks every Wikipedia title
.\.venv\Scripts\python scripts/build_reading_materials.py  # version 1 for every curated topic (~1 min)
```

Both need internet access (Wikipedia) and are safe to re-run. Preview one topic's material with `scripts/build_reading_materials.py <topic_id> --preview`.
Set `WIKIPEDIA_USER_AGENT` in `.env` to include your contact (Wikimedia policy). Design: [docs/TOPICS_READING_DESIGN.md](../docs/TOPICS_READING_DESIGN.md).

### 6. Run the API

```powershell
.\.venv\Scripts\uvicorn app.main:app --reload --port 8999
```

Open http://127.0.0.1:8999/health. You should see `{"status": "ok", "database": "connected"}`.

### 7. Try logging in

Open http://127.0.0.1:8999/docs:

1. `POST /api/v1/auth/login` → **Try it out** with `{"email": "admin@speakwise.com", "password": "admin@123"}`. Copy `access_token` from the response.
2. Click **Authorize** (top right), paste the token, and click **Authorize**.
3. `GET /api/v1/auth/me` now returns the admin's profile. `POST /api/v1/auth/logout` revokes the token.

| Endpoint | Auth | Purpose |
|---|---|---|
| `POST /api/v1/auth/login` | Public | Email + password → access token (valid `JWT_EXPIRE_HOURS`) |
| `GET /api/v1/auth/me` | Bearer token | Current user's profile |
| `POST /api/v1/auth/logout` | Bearer token | Revoke the current token |
| `GET /api/v1/users/me` | Bearer token | Your profile (incl. `created_at`) |
| `PATCH /api/v1/users/me` | Bearer token | Update your own `full_name` / `email` |
| `GET /api/v1/users?search=&status=active\|inactive&skip=0&limit=50` | Admin | Users with session count / last active, newest first, plus overall counts |
| `POST /api/v1/users` | Admin | Create a user; returns a one-time `temporary_password` |
| `GET /api/v1/users/{id}` | Admin | Any user's profile + activity |
| `PATCH /api/v1/users/{id}` | Admin | Update any user's `full_name`, `email`, `role_id`, `is_active` |
| `POST /api/v1/users/{id}/reset-password` | Admin | Replace a user's password with a new temporary one |
| `GET /api/v1/admin/dashboard` | Admin | KPIs, sessions per week, category split, recent sessions |
| `GET /api/v1/topics/suggest?category=&difficulty=&exclude_id=` | Bearer token | Random curated topic the user hasn't recorded |
| `GET /api/v1/topics/daily` | Bearer token | Today's topic (same for everyone) + whether you recorded it |
| `POST /api/v1/topics/custom` `{text}` | Bearer token | Find/create a topic from typed text (201 new, 200 existing, 422 nothing found, 429 hourly limit) |
| `GET /api/v1/topics/{id}` | Bearer token | One topic |
| `GET /api/v1/topics/{id}/reading-material` | Bearer token | ~2,500-word material from Wikipedia; never a version you already recorded with |
| `GET /health` | Public | API + database check |

## Tests

```powershell
.\.venv\Scripts\pip install -r requirements-dev.txt
.\.venv\Scripts\python -m pytest
```

Unit tests cover text normalization, the Wikipedia parser and client (mocked HTTP: redirects, retries, circuit breaker) and the reading-material builder. They don't need the database or internet.

## After pulling new changes

```powershell
.\.venv\Scripts\pip install -r requirements.txt   # if requirements.txt changed
.\.venv\Scripts\alembic upgrade head              # if new migrations were added
```

Running `alembic upgrade head` when there's nothing new is harmless.

## Troubleshooting

| Error | Fix |
|---|---|
| `password authentication failed for user "speakwise_app"` | Step 2 wasn't run, or the password in `.env` doesn't match. Re-run step 2 and check `DATABASE_URL`. |
| `database "speakwise_db" does not exist` | Run step 2. |
| `DATABASE_URL is not set` | You're missing `backend/.env` (step 3). |
| `JWTSECRET_KEY is missing or shorter than 32 characters` | Generate a secret and put it in `.env` (step 3). || `permission denied for schema public` | Re-run step 2; its last line gives `speakwise_app` ownership of the schema. |
| `Can't locate revision identified by ...` | Your database has migrations from an old branch. Pull the latest code, or reset the database (below). |

### Reset the database (deletes all data)

```powershell
.\.venv\Scripts\alembic downgrade base
.\.venv\Scripts\alembic upgrade head
.\.venv\Scripts\python scripts/seed_demo_users.py
```

## Database schema

The schema follows [docs/speak_wise_db_design (1).md](../docs/speak_wise_db_design%20(1).md), plus:

- `users`: login via `email` + `hashed_password` (bcrypt); emails are stored lowercase
- `roles`: fixed IDs `1 = admin`, `2 = user`; `users.role_id` defaults to `2`. Use `app.constants.roles.RoleId` in code instead of raw numbers.
- `topic_categories`: fixed IDs `1 = Technology`, `2 = Environment`, `3 = Business`, `4 = Society`, `5 = Science`
- `talk_session` extra columns for the dashboard: `topic_title`, `category_id`, `duration_seconds`

## Making schema changes

1. Change or add a model in `app/models/`. A new model must also be imported in `app/models/__init__.py`, or Alembic won't see it.
2. Generate a migration: `.\.venv\Scripts\alembic revision --autogenerate -m "describe change"`
3. Review the generated file in `alembic/versions/`, since autogenerate can miss things like renames.
4. Apply it: `.\.venv\Scripts\alembic upgrade head`
5. Commit the migration file together with the model change.

Other useful commands:

- `alembic downgrade -1`: undo the last migration
- `alembic check`: confirm the models and database are in sync
- `alembic history`: list all migrations

Never edit a migration that has already been pushed. Add a new one instead.
