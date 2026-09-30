# SpeakWise — Phase 1 Build Plan (React web app)

> Status: Approved decisions · 2026-09-28
> Goal: a responsive React web app (360 × 800 mobile → 1440 × 900 desktop) that matches the Claude Design handoff pixel-close, running entirely on mock data.
> Source of truth for visuals: `frontend/design_handoff_speakwise/` (README spec + 19 screens × 2 breakpoints).
> Backend is **not** run or called in Phase 1.

---

## 1. Decisions

| Topic | Decision | Why |
|---|---|---|
| App shape | **Single Vite app** in `frontend/`. Shared logic lives in `src/core/` under a strict no-DOM rule. | Simple now. `src/core` moves into a shared package when the mobile phase starts (ARCHITECTURE.md §2). |
| Styling | **Global plain CSS**, one `.css` per component, **BEM with a component prefix** (`.btn`, `.btn--primary`, `.btn__icon`). CSS variables from the handoff. No inline styles except dynamic values (progress %, bar heights). | Matches the handoff. The prefix rule keeps global names unique. |
| Design tokens | The handoff's **Organic** tokens (terracotta accent, sage, cream) replace the earlier "blue" direction in ARCHITECTURE.md §11. | The design is final. |
| Routes | Exactly as in the handoff README (`/session/topic`, `/feedback/:id`, `/admin/users`…). | Matches the design contract. They can switch to id-based session routes when the backend is wired. |
| Data | `mockData.ts` → `src/core/data/mockData.ts`, accessed only through async mock **services** (with delays) so pages never import mock data directly. | Swapping to the FastAPI backend later only changes the services. |
| Roles | `student` → `/home`, `admin` → `/admin/*` (role guard). Inactive users are blocked at login. | Per the handoff. |

### Versions (latest stable, checked 2026-09-28)

| Package | Version | Note |
|---|---|---|
| react / react-dom | ^19.3 | |
| vite | ^8.3 | |
| @vitejs/plugin-react | ^6.1 | |
| typescript | **~6.0** | TS 7.0 is out, but `typescript-eslint` supports only `<6.1`. Upgrade when it does. |
| react-router | ^8.4 | Handoff says `react-router-dom`. Since v7 it's the single `react-router` package. |
| lucide-react | ^1.48 | Icons, stroke 2.5 |
| eslint / typescript-eslint | ^10.11 / ^8.x | Existing flat config |
| prettier | latest | Formatting |
| @playwright/test | latest (dev) | Screenshot checks against the handoff PNGs |

Node 22 LTS / npm 10 (installed).

---

## 2. Folder structure

```
frontend/
├── design_handoff_speakwise/        # reference only (excluded from tsc/eslint/build)
├── index.html                       # Google Fonts: Caprasimo, Figtree, Literata
├── tests/visual/                    # Playwright: screenshot every route at 360×800 and 1440×900
└── src/
    ├── main.tsx
    ├── index.css                    # imports styles/*
    ├── styles/
    │   ├── tokens.css               # :root tokens from the handoff README
    │   ├── base.css                 # reset, body, headings, focus ring, type scale
    │   └── motion.css               # @keyframes cdPop, recPulse, breathe, spin + reduced-motion
    │
    ├── app/
    │   ├── App.tsx
    │   ├── router.tsx               # all routes, lazy-loaded pages
    │   ├── providers.tsx            # Auth, Preferences, Session, Toast
    │   └── guards/                  # RequireAuth, RequireRole, RequireSessionTopic
    │
    ├── core/                        # ⚠ NO DOM / window / localStorage. Portable to React Native.
    │   ├── types/                   # Topic, Session, Metric, Feedback, User, AdminUser, …
    │   ├── data/mockData.ts         # copied from the handoff (only services import it)
    │   ├── services/                # authService, topicService, sessionService,
    │   │                            #   feedbackService, historyService, adminService (async, delayed)
    │   ├── session/                 # sessionReducer + actions (phase machine from the handoff §State)
    │   ├── hooks/                   # useCountdown, useIntervalTimer (pure React, no DOM)
    │   └── utils/                   # formatClock (m:ss), passwordStrength, validators, pickRandomTopic, greeting
    │
    ├── context/                     # AuthContext, PreferencesContext, SessionContext, ToastContext
    │
    ├── hooks/                       # web-only: useMediaQuery, useIsDesktop, useFocusTrap,
    │                                #   useEscapeKey, useScrollProgress, useBodyScrollLock, useBeforeUnload
    │
    ├── components/
    │   ├── ui/                      # design-system primitives (below)
    │   ├── layout/                  # AppShell, AdminShell, FocusLayout, AuthLayout, MarketingLayout
    │   └── shared/                  # domain pieces reused across pages:
    │                                #   SessionRow, SessionList, TopicCard, CategoryChips, DurationPicker,
    │                                #   DifficultyBadge, ScoreCircle, KeyPointsList
    │
    └── features/                    # one folder per area: page + private components
        ├── landing/                 # LandingPage, Navbar, Hero, HeroIllustration, Features, FeatureCard, Footer
        ├── auth/                    # LoginPage, RegisterPage, PasswordStrength, BrandPanel
        ├── home/                    # HomePage, GreetingHeader, StartSessionCard, TodayTopicCard, StatCard, HomeEmpty
        ├── session/
        │   ├── topic/               # TopicSetupPage, OwnTopicInput, SessionSummaryCard
        │   ├── prepare/             # PreparePage, Article, PullQuote, KeyPointsBox, PrepRail, NotesSheet, TextSizeControl
        │   ├── record/              # RecordPage, CameraPreview, FaceGuide, StatusPill, MicMeter,
        │   │                        #   CountdownOverlay, RecTimer, CueCard, RecordButton, StopButton
        │   │   └── media/           # useCamera, useMediaRecorder, useMicLevel (web adapters)
        │   ├── review/              # ReviewPage, VideoPlayer
        │   └── processing/          # ProcessingPage, BreathingLoader, StepChecklist
        ├── feedback/                # FeedbackPage, ScoreRing, MetricCard, InsightList, Transcript
        ├── history/                 # HistoryPage, HistoryToolbar, HistoryTable
        ├── profile/                 # ProfilePage, ProfileCard, PreferenceRow
        └── admin/
            ├── dashboard/           # AdminDashboardPage, KpiCard, WeeklyBarChart, CategoryBars, AdminRecentSessions
            └── users/               # AdminUsersPage, UsersTable, UserCard, StatusToggle, AddUserForm
```

### Rules
1. `src/core/**` must not use `window`, `document`, `navigator`, `localStorage`, or `react-dom`. Enforced with an ESLint `no-restricted-globals` / `no-restricted-imports` override for that folder.
2. Pages import data only through `core/services` (or context), never `mockData` directly.
3. Features never import another feature's internals. Shared pieces are promoted to `components/shared` or `components/ui`.
4. Every component is `Name.tsx` + `Name.css`, a named export, and typed props. Its CSS classes start with its kebab-case name.
5. Path alias `@/` → `src/`.

---

## 3. Design-system primitives (`components/ui`)

| Component | Variants / props | Used on |
|---|---|---|
| `Button` | `primary · secondary · ghost · danger · onAccent`, `size md/lg`, `block`, `loading`, `iconLeft/Right`, `as` link | Everywhere |
| `IconButton` | circle 44px, `light/dark`, `aria-label` required | Focus top bar, menus |
| `Chip` / `ChipGroup` | selectable, 40px pill, `scroll` (mobile) / `wrap` | Categories, durations, sort, examples |
| `Badge` | `beginner · intermediate · advanced · processing · category · admin` | Topics, sessions |
| `Card` | `surface · raised · accent · sage · dashed`, radius tokens | Everywhere |
| `TextField` / `PasswordField` / `Textarea` / `Select` | label, error, helper, counter, end adornment (Show/Hide, check) | Auth, topic, notes, profile, admin |
| `SearchInput` | pill with search icon | History, admin |
| `SegmentedControl` | dark-fill active segment, full-width option | Topic, history, profile, admin |
| `Toggle` | 52×32 (profile), 48×28 compact (admin status) | Profile, admin |
| `ProgressBar` | thin/regular, light/dark track | Reading, recording, processing |
| `ScoreCircle` | small score disc | Session rows, admin |
| `Avatar` | initials, sizes 40/48/64 | Shells, tables |
| `Banner` | `error` | Auth |
| `Spinner` | inline, ring | Buttons, checklist |
| `Modal` / `BottomSheet` / `ResponsiveDialog` | focus trap, Esc, scroll lock. `ResponsiveDialog` = Modal ≥768px, Sheet below | Confirmations, notes, add user |
| `ConfirmDialog` | title, body, confirm/cancel, `danger` | Prepare, record, review |
| `Toast` | dark, auto-hide 3.5s | Admin add user |
| `EmptyState` | icon, title, body, action | Home, history |
| `Overline` / `PageHeader` | typography helpers | Many |

A dev-only route **`/dev/ui`** shows every primitive in every state so it can be checked against the prototype's Design System tab.

---

## 4. Responsive approach

- **Mobile-first CSS**: base styles target 360px. Breakpoints `@media (min-width: 768px)` (desktop layout, narrower rails) and `@media (min-width: 1024px)` (full desktop). These are literal values, documented in `tokens.css`.
- Layout differences are handled **in CSS** wherever the markup is the same (grids, stacking, sticky bars).
- Where the **markup differs** (sidebar vs tab bar, table vs cards, Modal vs BottomSheet, Record desktop panel vs full-screen overlay), a `useIsDesktop()` hook (`matchMedia('(min-width: 768px)')`) picks the component.
- `100dvh` for camera screens, `env(safe-area-inset-bottom)` on tab and sticky bars, touch targets ≥ 44px, 16px minimum body text.

---

## 5. State

| Store | Contents | Persistence |
|---|---|---|
| `AuthContext` | `user`, `role`, `login()`, `register()`, `logout()` | `localStorage` (mock session) |
| `PreferencesContext` | default duration, reading text size, camera/mic, notifications | `localStorage` |
| `SessionContext` | handoff §State: `mode, topic, category, ownTopic, durationMin, readPct, prepSecondsLeft, notes, textStep, phase, countdown, remainingSec, spokenSec, uploadPct, procStep, recording, dialog` via `sessionReducer` (in `core/session`) | `sessionStorage` for non-media fields. The recording blob stays in memory. |
| Admin data | users list + derived KPIs (toggling status updates KPIs) | Provider scoped to `/admin/*` |
| `ToastContext` | toast queue | memory |

---

## 6. Camera & recording (real, in-browser)

- `useCamera`: `getUserMedia({ video: { facingMode: 'user' }, audio: true })`, mirrored preview, statuses `idle · requesting · ready · denied · unavailable`. Falls back to the design's **placeholder silhouette** when no camera is available, so the flow still works on any machine.
- `useMicLevel`: Web Audio `AnalyserNode` → 10-bar meter.
- `useMediaRecorder`: MIME fallback `webm;vp9,opus → webm;vp8,opus → webm → mp4`. The result is a Blob + object URL, played back on Review and downloadable.
- Countdown 5→1 (`cdPop`), live timer with auto-stop at 0:00, "Wrap up now" at ≤10s, and Stop → "End early?" dialog pauses the timer.
- Mock processing: upload +4% every 200ms, then 1s per checklist step, then auto-navigate to Feedback.

---

## 7. Milestones

Each milestone ends with: `npm run lint`, `npm run typecheck`, and `npm run build` all clean, plus Playwright screenshots at **360×800** and **1440×900**, compared side by side with the handoff PNGs.

| # | Milestone | Screens | Done when |
|---|---|---|---|
| **0** | **Clean scaffold.** Remove old `src/` code and assets, update deps to the versions above, alias, Prettier, ESLint core rule, tokens/base/motion CSS, fonts, `mockData` → `core/data`, types, services, router with placeholder pages, guards | — | App boots, all routes resolve, tooling clean |
| **1** | **UI primitives** + `/dev/ui` showcase | Design System tab | Every primitive and state matches the prototype |
| **2** | **Landing, Login, Register** + AuthLayout, mock auth, role routing, validation, password strength | 01, 02, 02b | Pixel-close at both sizes, all validation states work |
| **3** | **App shell** (sidebar / top bar + tab bar), **Home** (+ empty), **History**, **Profile** | 03, 04, 15, 16 | Filters, search, sort, empty states, preferences persist |
| **4a** | **Topic + Prepare** (FocusLayout, step indicator, sticky bar, reading progress, notes sheet, confirm) | 05, 06, 07 | Reroll logic, own topic, duration, scroll progress |
| **4b** | **Record** (camera check, countdown, live, final 10s, end-early) | 08, 09, 10, 11 | Real camera recording on Chrome, Edge, and mobile Chrome |
| **4c** | **Review, Processing, Feedback** | 12, 13, 14 | Playback/download, mock processing, feedback + transcript |
| **5** | **Admin** dashboard, users, add user, toast | 17, 18, 19 | Status toggles update KPIs, add-user validation |
| **6** | **Polish**: a11y (focus trap, Esc, labels, contrast), reduced motion, full visual QA pass, dead-code sweep | all | Every screen signed off at both sizes |

---

## 8. Mock accounts (from `mockData.ts`)

| Email | Password | Role |
|---|---|---|
| priya.sharma@example.com | Speak2026! | student |
| admin@speakwise.app | Admin2026! | admin |

Any other valid email with a 6+ character password logs in as a student (an `admin@…` prefix gets the admin role). Shorter passwords show the wrong-credentials banner. Inactive admin-list users get the inactive banner.

---

## 9. Out of scope for Phase 1

Real API calls, real auth/JWT, uploads to the backend, notifications, dark mode, i18n, native apps.
