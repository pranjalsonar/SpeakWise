# SpeakWise — Web App (Phase 1)

Responsive React web app (360 × 800 mobile → 1440 × 900 desktop) built from the Claude Design handoff in `design_handoff_speakwise/`. It runs entirely on **mock data**; the FastAPI backend is not needed.

Architecture: [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md) · Build plan: [`../docs/PHASE1_PLAN.md`](../docs/PHASE1_PLAN.md)

## Run

```bash
npm install
npm run dev          # http://localhost:5173 (also exposed on your LAN)
```

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
| priya.sharma@example.com | Speak2026! | Student app (with history) |
| admin@speakwise.app | Admin2026! | Admin dashboard |

Any other valid email with a 6+ character password logs in as a new student (empty history); `admin@…` emails get the admin role. Newly registered users start with no sessions.

## Structure

```
src/
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

Conventions: one `Name.tsx` + `Name.css` per component, global CSS with a BEM prefix per component (`.btn`, `.btn--primary`, `.btn__icon`), no inline styles except dynamic values. Pages get data only through `core/services`, so swapping the mocks for the FastAPI backend happens there. `src/core` must stay DOM-free (enforced by ESLint) so it can be shared with the future React Native app.

A dev-only gallery of every UI primitive is at `/dev/ui`.
