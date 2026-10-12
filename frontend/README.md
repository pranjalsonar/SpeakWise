# SpeakWise — Web App (Phase 1)

Responsive React web app (360 × 800 mobile → 1440 × 900 desktop) built from the Claude Design handoff in `design_handoff_speakwise/`. **On the FastAPI backend:** login/logout, Profile, the whole admin area, and the session's Topic → Prepare steps (topics + Wikipedia reading material, see [`../docs/TOPICS_READING_DESIGN.md`](../docs/TOPICS_READING_DESIGN.md)). **Still mock data:** Home stats/recent sessions, History, Processing and Feedback (recordings aren't saved to the backend yet).

Architecture: [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) · Build plan: [`../docs/PHASE1_PLAN.md`](../docs/PHASE1_PLAN.md) · API calls: [`src/api/README.md`](src/api/README.md)

## Run

1. Start the backend first (see [`../backend/README.md`](../backend/README.md)). It must be running on the URL in `.env` for login to work.
2. Then:

```bash
npm install
copy .env.example .env   # macOS/Linux: cp .env.example .env
npm run dev              # http://localhost:5173 (also exposed on your LAN)
```

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `http://127.0.0.1:8999` | Backend URL. Use your PC's LAN IP when testing on a phone. |
| `VITE_API_PREFIX` | `/api/v1` | Versioned API prefix |
| `VITE_API_TIMEOUT_MS` | `15000` | Request timeout |

Restart `npm run dev` after editing `.env`. Everything in it is bundled into the browser app, so never put secrets there.
The frontend's URL must be in the backend's `CORS_ORIGINS` (default allows `http://localhost:5173`). When opening the app on a phone via the LAN address, add that origin to `backend/.env`.

| Script | What it does |
|---|---|
| `npm run dev` | Vite dev server |
| `npm run build` | Type-check + production build to `dist/` |
| `npm run typecheck` / `npm run lint` | TypeScript / ESLint |
| `npm run format` / `format:check` | Prettier |
| `npm run shots` | Playwright screenshots of every screen at 360×800 and 1440×900 → `tests/visual/__shots__/` (first time: `npx playwright install chromium`) |

Camera recording needs **HTTPS** except on `localhost`. To test on a phone over the LAN, serve over HTTPS (e.g. `@vitejs/plugin-basic-ssl`). Without a camera the Record step still works in demo mode (placeholder preview, no video file).

## Demo accounts

| Email | Password | Opens |
|---|---|---|
| admin@speakwise.com | admin@123 | Admin dashboard |
| raj@gmail.com | raj@123 | Student app |

These come from the backend seed script (`backend/scripts/seed_demo_users.py`). The access token is kept in `sessionStorage`, so each browser tab logs in separately and closing the tab logs you out. Tokens last 8 hours. Registration is still mocked: a registered user stays signed in only until the page is reloaded.

## Structure

```
src/
  api/          backend calls: client.ts (fetch + token + errors), api.<module>.ts files (see src/api/README.md)
  app/          router, route guards, route constants
  core/         platform-agnostic (no DOM): types, mock data, services, session reducer, hooks, utils
  context/      Auth, Preferences, Session, Toast providers
  hooks/        web-only hooks (media query, dialogs, devices, start session)
  components/
    ui/         design-system primitives (Button, Chip, TextField, Modal, BottomSheet, …)
    layout/     AppShell, AdminShell, FocusLayout, AuthLayout, StickyActionBar
    shared/     domain pieces reused across pages (SessionRow, TopicBadges, KeyPointsList)
  features/     one folder per screen area (landing, auth, home, history, profile, session/*, feedback, admin)
  styles/       tokens.css (design tokens), base.css, motion.css
```

Conventions: one `Name.tsx` + `Name.css` per component, global CSS with a BEM prefix per component (`.btn`, `.btn--primary`, `.btn__icon`), no inline styles except dynamic values. Real backend calls live in `src/api/` (one `api.<module>.ts` file per backend module or page, imported by the page). Screens not wired to the backend yet still get mock data from `core/services`. Move each one to `src/api/` when its endpoint exists. `src/core` must stay DOM-free (enforced by ESLint) so it can be shared with the future React Native app.

A dev-only gallery of every UI primitive is at `/dev/ui`.
