# SpeakWise — Frontend Architecture

> Status: Draft v2 · 2026-09-27 (v2 adds the cross-platform plan: web + Android + iOS)
> Scope: Frontend clients (responsive web now, native Android + iOS next), built against **dummy data** first. The backend (FastAPI + PostgreSQL, analysis pipeline) is developed in parallel and is **not** required to run the frontend.

> **Phase 1 (current): React web app only.** See [PHASE1_PLAN.md](PHASE1_PLAN.md). Where the two docs differ, Phase 1 uses:
> - a **single Vite app** in `frontend/`, with shared logic in `src/core/` (the no-DOM rule from §4.6). The monorepo in §4 is set up when mobile work starts, by moving `src/core` into `packages/`.
> - **global plain CSS with BEM prefixes** instead of CSS Modules.
> - the **Organic design tokens** from `frontend/design_handoff_speakwise/README.md` instead of §11's blue direction.
> - the handoff's routes (`/session/topic`, `/feedback/:id`, …) and the **admin** area (`/admin`, `/admin/users`).

---

## 1. Product summary

SpeakWise is an AI public-speaking coach for students and interview candidates. A user picks (or is given) a topic, reads a ~15-minute briefing on it, then records themselves speaking about it on camera for a fixed duration. The recording is sent to the backend, which analyses video + audio and returns feedback.

The frontend owns everything up to and including the upload, plus rendering the feedback the backend returns.

### Core user journey

```
Login ──► Home (welcome) ──► Choose topic + duration ──► Read material (~15 min)
                                                              │
                                                              ▼
Feedback ◄── Processing ◄── Review recording ◄── Record (camera, 5-4-3-2-1, timer)
```

| # | Step | What the user does | Backend status |
|---|------|--------------------|----------------|
| 1 | Login | Signs in with email + password (or registers) | — |
| 2 | Home | Sees a welcome message, stats, recent sessions, and a **Start talk session** CTA | — |
| 3 | Topic setup | Types a custom topic **or** taps "Suggest a topic" (random, can reroll). Picks a speaking duration. | `CREATED` |
| 4 | Prepare | Reads ~15 min of material on the topic, with optional notes. Clicks **I'm ready**. | `LEARNING` |
| 5 | Camera check | Grants camera/mic permission, sees a mirrored preview. Clicks **Start**. | `READY_TO_RECORD` |
| 6 | Record | A 5-4-3-2-1 countdown plays over the preview, then recording starts with a countdown timer for the chosen duration. Stops automatically at 0:00 (or early). | `RECORDING` |
| 7 | Review | Plays back the clip. **Submit** or **Re-record**. | — |
| 8 | Processing | Upload progress, then "Analyzing your talk…" | `PROCESSING` |
| 9 | Feedback | Scores and insights from the backend (dummy for now) | `FEEDBACK_READY` → `COMPLETED` |

Secondary screens: **History** (past sessions), **Profile/Settings**.

---

## 2. Platform strategy: web + Android + iOS

### 2.1 The key fact

**Neither a React (Vite) web app nor a Next.js app converts into an Android/iOS app.** Web code renders HTML (`<div>`, CSS). React Native renders native views (`<View>`, `StyleSheet`). In both cases the **screens and styling get rewritten** for native. What carries over is everything that isn't UI:

| Reusable across web and native | Rewritten per platform |
|---|---|
| TypeScript types, constants, validation | Screens and layout components |
| API client (`fetch` works in React Native) | Styling (CSS Modules vs `StyleSheet`) |
| Mock/dummy data and the mock service layer | Navigation (`react-router` vs `expo-router`) |
| Session state machine (pure TS) | Camera and recording |
| React hooks with no DOM (auth, session flow, countdown, timer, TanStack Query hooks) | Secure token storage, file upload |
| Design tokens (colors, spacing, type, radii) | Platform-specific UX (back gesture, permissions) |

So React vs Next.js makes **almost no difference to how much code reaches mobile**. The difference is what gets in the way:

- **React + Vite**: plain React that the team already knows. Nothing web-framework-specific ends up in shared logic. **This is the easier path.**
- **Next.js**: adds server components, server actions, `next/router`, `next/image`, and API routes. None of these run in React Native, and logic written around them has to be untangled before it can be shared.

### 2.2 Options considered

| Option | How it works | Code reuse | Verdict |
|---|---|---|---|
| **A. Monorepo: Vite web app + Expo native app + shared packages** | Two apps, one repo. Types, API, mocks, state, hooks, and tokens live in shared packages. | ~40–50% (all non-UI logic) | ✅ **Chosen.** This is the most conventional and reliable setup. Each platform gets idiomatic UI, and the shared boundary is enforced by package imports. |
| B. Expo "universal" app (Expo Router + React Native Web) | One React Native codebase also exported to web | ~85–95% | Strong option, but the web output is React Native styled rather than CSS. Browser video recording isn't covered by `expo-camera`, so we'd still write a web recording path. We'd also throw away the Vite setup. Worth revisiting if keeping two UIs becomes too costly. |
| C. Capacitor (wrap the web app in a native shell) | Ships the web app inside a WebView | ~100% | Fastest route to stores, but it's not React Native. Camera recording in a WebView is less reliable and the app feels less native. Rejected, since native quality was requested. |
| D. Next.js web + Expo (via Solito) | Shared navigation across Next.js and Expo | ~50–60% | Extra complexity with no benefit for an app behind a login. Rejected. |

### 2.3 Decision

- **Web**: React + TypeScript + **Vite** (already scaffolded).
- **Android + iOS**: **React Native via Expo** (the framework the React Native team recommends), with **Expo Router** for navigation and **EAS Build/Submit** for builds and store releases.
- **Sharing**: an **npm workspaces monorepo** inside `frontend/`, with shared TypeScript packages consumed as source (no build step, the "internal packages" pattern).
- **Marketing/SEO site** (if ever needed): a separate small Next.js or Astro site. It doesn't affect this plan.

---

## 3. Tech stack

| Layer | Web (`apps/web`) | Mobile (`apps/mobile`) | Shared (`packages/*`) |
|---|---|---|---|
| Language | TypeScript (strict) | TypeScript (strict) | TypeScript (strict) |
| Runtime/build | Vite | Expo SDK (Metro), EAS Build | Consumed as TS source |
| UI | React 19 + DOM | React Native (same React version) | — |
| Navigation | `react-router` v7 | `expo-router` (file-based, same paths) | Route name constants |
| Styling | CSS Modules + CSS variables generated from tokens | `StyleSheet` using token values | `@speakwise/tokens` |
| Server state | TanStack Query | TanStack Query | Query hooks in `@speakwise/hooks` |
| Client state | Context + `useReducer` | Context + `useReducer` | Session reducer in `@speakwise/core` |
| Validation | Zod | Zod | Schemas in `@speakwise/core` |
| Icons | `lucide-react` | `lucide-react-native` | Same icon names |
| Camera/recording | `getUserMedia` + `MediaRecorder` | `expo-camera` (`CameraView`, `recordAsync`) | `Recorder` interface in core |
| Token storage | `localStorage` (later an httpOnly cookie) | `expo-secure-store` | `StorageAdapter` interface in core |
| Video playback | `<video>` | `expo-video` | — |
| Upload | `fetch` + `FormData(Blob)` | `expo-file-system` upload / `FormData({ uri })` | `Uploader` interface in core |
| Lint/format | ESLint + Prettier | ESLint + Prettier | `packages/config` |
| Tests | Vitest + RTL, Playwright | Jest + RNTL, Maestro (E2E, later) | Vitest |

> **React version rule:** the Expo SDK sets the React version. The web app must use the **same React version** so the shared hooks run against one React. Upgrade them together.

---

## 4. Repository & folder structure

`backend/` is untouched. `frontend/` becomes an npm workspaces root:

```
SpeakWise/
├── backend/                         # FastAPI (colleague)
├── docs/
├── prompts/
└── frontend/
    ├── package.json                 # "workspaces": ["apps/*", "packages/*"]
    ├── apps/
    │   ├── web/                     # Vite + React (current frontend/ app moves here)
    │   └── mobile/                  # Expo app (Android + iOS), added in phase 8
    └── packages/
        ├── core/                    # @speakwise/core   — pure TS, NO React, NO DOM, NO RN
        ├── hooks/                   # @speakwise/hooks  — React hooks, NO DOM, NO RN imports
        ├── tokens/                  # @speakwise/tokens — design tokens as TS objects
        └── config/                  # shared tsconfig.base.json, eslint config
```

### 4.1 `packages/core`: `@speakwise/core`

```
core/src/
├── types/          # User, Topic, ReadingMaterial, PracticeSession, Feedback…
├── constants/      # ALLOWED_DURATIONS, READING_TIME_MIN, COUNTDOWN_SECONDS, ROUTES
├── schemas/        # Zod schemas (login form, topic input, API responses)
├── api/            # createApiClient({ baseUrl, getToken }) + endpoint functions
├── mocks/          # dummy data + mock implementations of the same API
├── services/       # createServices({ useMocks, adapters }) → one services object
├── session/        # session flow reducer / state machine
├── adapters/       # INTERFACES only: StorageAdapter, Recorder, Uploader
└── utils/          # formatDuration, readingTime, snake↔camel case mapping
```

### 4.2 `packages/hooks`: `@speakwise/hooks`

React hooks that run on both platforms: `useAuth`, `useSessionFlow`, `useCountdown(5)`, `useRecordingTimer(duration)`, `useTopicSuggestion`, `useReadingMaterial`, `useSessions`, `useFeedback`, plus the `ServicesProvider` that injects the platform adapters.

### 4.3 `packages/tokens`: `@speakwise/tokens`

```ts
export const colors = { primary600: '#2563EB', slate900: '#0F172A', recording: '#DC2626', … };
export const space = { 1: 4, 2: 8, 3: 12, 4: 16, 6: 24, 8: 32 };
export const radius = { sm: 8, md: 12, lg: 16, full: 9999 };
export const typography = { … };
```

The web app runs a small script (`npm run tokens`) that generates `apps/web/src/styles/tokens.css` (CSS variables) from this file. Mobile imports the objects directly into `StyleSheet.create`. There is one source of truth.

### 4.4 `apps/web`

```
web/src/
├── app/                 # App.tsx, router.tsx, providers.tsx (injects web adapters), ProtectedRoute
├── adapters/            # webStorage.ts, webRecorder.ts (MediaRecorder), webUploader.ts
├── features/            # auth, home, session/{setup,prepare,record,review,processing}, feedback, history, profile
├── components/ui/       # Button, Card, Input, Chip, Badge, Modal, Sheet, ProgressBar, ScoreRing…
├── components/layout/   # AppShell, SideNav, BottomTabBar, TopBar, FocusLayout
├── hooks/               # web-only hooks: useMediaQuery, useBeforeUnload
├── styles/              # tokens.css (generated), reset.css, globals.css
├── marketing/           # existing Sprint-1 landing page (Navbar, Hero…)
└── main.tsx
```

### 4.5 `apps/mobile` (Expo)

```
mobile/
├── app/                           # expo-router: file = route, mirrors web paths
│   ├── _layout.tsx                # providers (injects native adapters)
│   ├── (auth)/login.tsx, register.tsx
│   ├── (tabs)/_layout.tsx         # bottom tabs: home, history, profile
│   ├── (tabs)/home.tsx, history.tsx, profile.tsx
│   └── session/new.tsx, [id]/prepare.tsx, camera.tsx, record.tsx, review.tsx, processing.tsx, feedback.tsx
├── src/adapters/                  # nativeStorage (secure-store), nativeRecorder (expo-camera), nativeUploader
├── src/components/ui/             # same component names + props as web, native implementation
├── app.json                       # name, bundle IDs, camera/mic permission strings, plugins
└── eas.json                       # build profiles: development, preview (APK), production (AAB/IPA)
```

### 4.6 Rules (these keep code shareable)

1. `@speakwise/core` imports nothing from React, the DOM, or React Native. `@speakwise/hooks` may import `react` and `@tanstack/react-query`, but never `react-dom` or `react-native`.
2. Platform features (storage, camera, upload) are reached only through **adapter interfaces** defined in core and injected by each app's provider.
3. UI primitives have the **same name and props on both platforms** (`<Button variant="primary" size="lg" loading>`), so screens read the same and move between platforms easily.
4. Screens stay thin: layout + primitives + shared hooks. Business logic goes into shared hooks, never into a screen.
5. Components never call `fetch` directly. They always go through services and hooks.
6. No `window`, `document`, `localStorage`, or `navigator` outside `apps/web`.

### 4.7 Adapter example

```ts
// packages/core/src/adapters/recorder.ts
export interface Recording { uri: string; mimeType: string; durationMs: number; sizeBytes?: number }
export interface Recorder {
  start(opts: { maxDurationSec: number }): Promise<void>;
  stop(): Promise<Recording>;
}

// apps/web/src/adapters/webRecorder.ts    → MediaRecorder, uri = URL.createObjectURL(blob)
// apps/mobile/src/adapters/nativeRecorder.ts → cameraRef.recordAsync({ maxDuration }), uri = file://…
```

`useRecordingTimer`, `useCountdown`, and the session reducer are shared, so the 5-4-3-2-1 countdown and auto-stop behave identically on every platform.

---

## 5. Routing

The same path structure on web and mobile (Expo Router is file-based and supports deep links such as `speakwise://session/42/feedback`).

| Path | Page | Web layout | Mobile | Auth |
|---|---|---|---|---|
| `/` | Landing (marketing) | Marketing | — (opens login/home) | Public |
| `/login`, `/register` | Auth | Centered card | `(auth)` stack | Public only |
| `/home` | Welcome / dashboard | AppShell | `(tabs)` | 🔒 |
| `/session/new` | Topic + duration | Focus | Stack, full screen | 🔒 |
| `/session/:id/prepare` | Reading | Focus | Stack | 🔒 |
| `/session/:id/camera` | Camera + mic check | Focus (dark) | Stack, dark | 🔒 |
| `/session/:id/record` | Countdown + recording | Focus (dark, full-bleed) | Full screen, gestures disabled | 🔒 |
| `/session/:id/review` | Playback | Focus | Stack | 🔒 |
| `/session/:id/processing` | Upload + analysis | Focus | Stack | 🔒 |
| `/session/:id/feedback` | Results | AppShell | Stack | 🔒 |
| `/history`, `/profile` | Secondary | AppShell | `(tabs)` | 🔒 |

- **Web AppShell**: sidebar ≥1024px, bottom tab bar on small screens.
- **Mobile**: native bottom tabs (Home · History · Profile) with a Start action. Session steps are a stack on top of the tabs.
- **Focus layout** for session steps: no navigation chrome, just a step indicator (Topic → Prepare → Record → Review) and an exit (×) that confirms before leaving. On mobile, the Android back button and the iOS swipe-back gesture are intercepted during recording.
- Route guards stop users jumping ahead, for example to `record` without a session in `READY_TO_RECORD`.

---

## 6. Domain model (shared types, `@speakwise/core/types`)

Mirrors `backend/app/schemas` and `backend/app/enums`. Keep these in sync.

```ts
export interface User { id: number; name: string; email: string; avatarUrl?: string }

export type Difficulty = 'Beginner' | 'Intermediate' | 'Advanced';
export interface Topic { title: string; category: string; difficulty: Difficulty }

export interface ReadingMaterial {
  topic: Topic;
  estimatedMinutes: number;  // ~15
  wordCount: number;         // ~2,500–3,000 words at ~200 wpm
  summary: string;
  keyPoints: string[];       // shown as a cue card during recording
  sections: { heading: string; paragraphs: string[] }[];
  sources?: { title: string; url: string }[];
}

export type SessionMode = 'RANDOM' | 'CUSTOM' | 'DAILY';
export type SessionStatus =
  | 'CREATED' | 'LEARNING' | 'READY_TO_RECORD'
  | 'RECORDING' | 'PROCESSING' | 'FEEDBACK_READY' | 'COMPLETED';
export type DurationMinutes = 1 | 3 | 5;   // backend ALLOWED_DURATIONS

export interface PracticeSession {
  id: number;
  title: string;
  mode: SessionMode;
  status: SessionStatus;
  selectedDuration: DurationMinutes;
  topicTitle?: string;
  topicCategory?: string;
  topicDifficulty?: string;
  createdAt: string;
  updatedAt: string;
}

// PLACEHOLDER until the analysis contract is agreed with backend
export interface Feedback {
  sessionId: number;
  overallScore: number;              // 0–100
  metrics: {
    key: 'clarity' | 'pace' | 'confidence' | 'fillerWords' | 'eyeContact' | 'relevance' | 'vocabulary';
    label: string;
    score: number;
    value?: string;                  // e.g. "142 wpm", "7 fillers"
    insight: string;
  }[];
  strengths: string[];
  improvements: string[];
  transcript?: string;
}
```

> The backend's API uses `snake_case`. The shared API client converts to `camelCase` at the boundary.

---

## 7. Data layer & dummy data

```
Screen ──► shared hook (@speakwise/hooks) ──► services (@speakwise/core) ──► mock | api
                                                     └── adapters injected by the app (storage, recorder, uploader)
```

- `createServices({ useMocks })` returns one `services` object. Web reads `VITE_USE_MOCKS`, mobile reads `EXPO_PUBLIC_USE_MOCKS`. Both default to `true` for now.
- **Mocks live in `@speakwise/core/mocks`, so web and mobile show the same dummy data.**
- Mocks return Promises with a 300–800 ms delay so loading states get designed.
- Mock data to provide:
  - 1 demo user (any email + password logs in).
  - ~20 topics across 5 categories and 3 difficulties.
  - 3 full reading materials (~2,500 words each). Other topics fall back to a template.
  - 6–8 past sessions in mixed statuses.
  - 2–3 feedback reports with different score profiles.
- Mock upload simulates progress. Mock analysis resolves after ~5 s.

Real endpoints that exist today: `POST /auth/login`, `POST /users/register`, `GET /users/me`, `POST /sessions`, `POST /speech/analyze`. Endpoints still needed: topic suggestion, reading material, video upload, session status polling, feedback fetch.

---

## 8. Session flow state machine (shared)

A pure reducer in `@speakwise/core/session` drives the flow on every platform. The UI dispatches events and never sets status directly.

```
CREATED ──START_READING──► LEARNING ──READY──► READY_TO_RECORD
                                                    │ START (after 5-4-3-2-1)
                                                    ▼
                  ┌──── RE_RECORD ────────────── RECORDING
                  │                                 │ TIME_UP / STOP
                  ▼                                 ▼
          READY_TO_RECORD                    (local: REVIEW)
                                                    │ SUBMIT
                                                    ▼
                         COMPLETED ◄── VIEWED ── FEEDBACK_READY ◄── PROCESSING
```

Non-media flow state (topic, duration, reading progress, notes) is persisted through the `StorageAdapter`: `sessionStorage` on web, `AsyncStorage` on mobile. The recording is kept as a URI (a blob URL on web, a local file on mobile).

---

## 9. Camera & recording

Shared: `Recorder` interface, `useCountdown`, `useRecordingTimer`, session reducer. Platform code: only the adapter and the preview component.

**Common behaviour.** Pressing **Start** shows a full-screen 5 → 4 → 3 → 2 → 1 overlay, then `recorder.start({ maxDurationSec })`. The timer counts **down** from the chosen duration, turns amber/red in the last 10 s, and auto-stops at 0:00 before going to Review. Leaving mid-recording asks for confirmation. The preview is mirrored and the recorded file is not.

### Web (`apps/web/src/adapters/webRecorder.ts`)
- `getUserMedia({ video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } }, audio: { echoCancellation: true, noiseSuppression: true } })`.
- `MediaRecorder` MIME fallback: `video/webm;codecs=vp9,opus` → `video/webm;codecs=vp8,opus` → `video/webm` → `video/mp4` (Safari).
- Mic level meter via Web Audio `AnalyserNode`. `beforeunload` guard.
- Requires **HTTPS** (localhost is exempt). For phone testing over LAN, use `@vitejs/plugin-basic-ssl`.

### Mobile (`apps/mobile/src/adapters/nativeRecorder.ts`)
- `expo-camera`: `<CameraView facing="front" mode="video" mirror />`, `recordAsync({ maxDuration })`, `stopRecording()`.
- Permissions via `useCameraPermissions()` + `useMicrophonePermissions()`. Usage strings are set in `app.json` (iOS `NSCameraUsageDescription` / `NSMicrophoneUsageDescription`, Android `CAMERA` / `RECORD_AUDIO`).
- Keep the screen awake while recording (`expo-keep-awake`). Lock the recording screen to portrait (`expo-screen-orientation`).
- Intercept Android hardware back and iOS swipe-back during recording.
- Output is `.mp4` (Android) or `.mov`/`.mp4` (iOS).

### Backend implication
Uploads arrive as **WebM** (Chrome/Firefox/Android web), **MP4** (Safari, Android app), or **MOV** (iOS app). The analysis service must accept all three (e.g. normalise with ffmpeg). **Needs agreement with backend.**

### Edge states to design (both platforms)
Permission prompt explainer, permission denied (with settings instructions / "Open Settings" on mobile), no camera, camera busy, unsupported browser (web), recording too short, app backgrounded mid-recording (mobile: stop and discard, then offer a re-record).

---

## 10. Responsive & mobile design strategy

One design language, three targets. The **mobile frames from the design are the reference for both the mobile web layout and the native app**, so users get the same experience on either.

**Baseline device: 360 × 800** (common Android size, the team's test phone). Every screen must be comfortable at this size on both web and native:

- 16px side gutters, giving 328px of content width. No horizontal scroll.
- Usable content height is ≈ 650px after the status bar, top bar (56px) and bottom tabs (64px). The main CTA on each screen is visible without scrolling. On session screens the primary action sits in a sticky bottom bar.
- Camera/record screens fit fully in 360 × 800 (`100dvh` on web). The timer, REC pill and Stop button are always visible.
- Body text is ≥ 16px, the reading article is 18px, and nothing depends on widths above 360px.
- Test at 360 × 800 first (Chrome DevTools custom device / Android emulator), then check 390 × 844 and 412 × 915.

Web breakpoints (mobile-first, base styles target 360px, `@media (min-width: …)`):

| Token | Min width | Target |
|---|---|---|
| `sm` | 480px | Large phones |
| `md` | 768px | Tablets / small laptops |
| `lg` | 1024px | Desktop (sidebar appears) |
| `xl` | 1280px | Wide desktop (max content width 1200px) |

| Screen | Mobile (web < 768 and native) | Desktop (≥ 1024) |
|---|---|---|
| Home | Single column, bottom tabs, Start CTA | Sidebar + 2-column grid |
| Topic setup | Stacked, sticky Continue button | Topic choice left, summary card right |
| Prepare | Full-width article, notes in a bottom sheet, sticky "I'm ready" | Article center (~70ch), right rail: timer, key points, notes |
| Camera / Record | Full-screen portrait preview, controls overlaid | Centered 16:9 preview + side panel |
| Review | Video on top, sticky actions | Video left, summary + actions right |
| Feedback | Stacked score cards | Score overview + metric grid |

Rules: touch targets ≥ 44 px (web) / 48 dp (Android), safe areas (`env(safe-area-inset-*)` on web, `react-native-safe-area-context` on native), `100dvh` for full-screen web camera views, and reduced motion respected (`prefers-reduced-motion` / `AccessibilityInfo.isReduceMotionEnabled`).

---

## 11. Design system (tokens)

Final values come from the Claude Design output (`prompts/00_master_design_prompt.md`) and are written once into `@speakwise/tokens`.

- **Tone**: calm, confident, professional. A coach, not a game.
- **Color**: white/near-white surfaces, slate neutrals, one blue primary (`#2563EB`-ish), semantic success/warning/danger, with red reserved for **recording**.
- **Type**: Inter (UI) plus a reading serif (Source Serif 4 / Literata) for the article. Loaded via Google Fonts on web and `expo-font` on native.
- **Shape**: 12–16px radius cards, soft shadows, 8px spacing grid.
- **Themes**: light by default. The camera/record screens are always dark. Full dark mode later.

---

## 12. Accessibility

- WCAG 2.2 AA contrast, visible focus rings, full keyboard support on web (Space/Enter to start or stop recording).
- Countdown and timer announced (`aria-live` on web, `accessibilityLiveRegion` / `AccessibilityInfo.announceForAccessibility` on native).
- Reading view supports text size adjustment and respects OS font scaling on native.
- Every icon-only button has a label (`aria-label` / `accessibilityLabel`).

---

## 13. Environment, scripts & release

```
# frontend/apps/web/.env.local
VITE_USE_MOCKS=true
VITE_API_BASE_URL=http://localhost:8000

# frontend/apps/mobile/.env
EXPO_PUBLIC_USE_MOCKS=true
EXPO_PUBLIC_API_BASE_URL=http://<your-LAN-IP>:8000   # a phone can't reach "localhost" on your PC
```

From `frontend/`:

```
npm install                      # installs all workspaces
npm run dev   -w apps/web        # Vite dev server
npm run start -w apps/mobile     # Expo dev server (scan QR with Expo Go / dev build)
npm run lint  --workspaces
npm run typecheck --workspaces
```

**Mobile builds and releases (EAS):**

| Profile | Output | Use |
|---|---|---|
| `development` | Dev client (APK / iOS simulator build) | Daily development with native modules |
| `preview` | Android **APK**, iOS ad-hoc/TestFlight | Share with testers and mentors |
| `production` | Android **AAB** → Google Play, **IPA** → App Store | Store release (`eas submit`) |

EAS builds iOS in the cloud, so **no Mac is required**. Publishing needs a Google Play Console account (one-time fee) and an Apple Developer account (annual fee). Small JS-only fixes can ship with `expo-updates` (OTA) without a store review.

---

## 14. Build plan

1. **Design**: generate mobile + desktop screens with the master prompt, then lock tokens.
2. **Monorepo foundation**: convert `frontend/` to npm workspaces and move the current Vite app to `apps/web`. Create `packages/core`, `packages/hooks`, `packages/tokens`, `packages/config`.
3. **Shared logic**: types, constants, mocks, services, session reducer, adapter interfaces, shared hooks, all with unit tests.
4. **Web foundation**: generated tokens.css, UI primitives, layouts, router, web adapters.
5. **Web screens**: Auth + Home, then Setup + Prepare, then Camera + Record + Review, then Processing + Feedback + History.
6. **Wire the real backend** endpoint by endpoint (flip the mocks flag).
7. **Mobile foundation**: `npx create-expo-app apps/mobile`, set up Expo Router, native UI primitives from tokens, native adapters.
8. **Mobile screens**: rebuild each screen using the shared hooks. Logic is already done and tested, so this is mostly layout.
9. **Mobile release**: EAS `preview` APK for testers, then Play Store / App Store.

Because shared logic is built in phases 2–3 **before** any mobile work, the mobile app starts with auth, data, the session flow, countdown, and timers already working.

---

## 15. Open questions

1. **Durations**: backend allows 1 / 3 / 5 min. Should 2 min (or a custom value) be offered? It's a one-line change in `ALLOWED_DURATIONS` on both sides.
2. **Reading time**: is 15 min a hard gate, a suggested timer, or can users skip?
3. **Feedback contract**: which metrics will the analysis service return? §6 `Feedback` is a placeholder.
4. **Video upload**: accepted formats (WebM / MP4 / MOV, see §9), max size, direct upload vs pre-signed URL, and sync vs async analysis (polling / websocket / push notification on mobile).
5. **Retakes**: how many re-records are allowed per session?
6. **Daily mode**: does `SessionMode.DAILY` need its own UI ("Today's topic" card on Home)?
7. **Mobile auth**: the backend issues bearer JWTs, which works for both. Do we need refresh tokens so mobile users stay signed in?
8. **App identity**: bundle ID / package name (e.g. `com.speakwise.app`), app icon, and store accounts. Who owns them?
