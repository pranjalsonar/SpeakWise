# Handoff: SpeakWise — Landing + Core Session Flow

## Overview
SpeakWise is an AI public-speaking coach for students. This handoff covers the **Landing page**, **Login**, **Register**, **Admin dashboard**, **Admin user management**, **Home**, **History**, **Profile**, and the core session flow: **Topic → Prepare (reading) → Record (camera check, countdown, live) → Review → Processing → Feedback**, each designed for **mobile (360×800)** and **desktop (1440×900)**, plus a design-system reference board.

## About the Design Files
`SpeakWise.dc.html` is a **design reference built in HTML**, a clickable prototype that shows the intended look and behavior. It is not production code to copy. Recreate it in the existing codebase at `speakwise/frontend` (**React + TypeScript + Vite, plain CSS, ESLint**), following its conventions:
- Components in `src/components/` (one `.tsx` + one `.css` each), functional components, typed props, individual exports.
- **Plain CSS with CSS variables. No inline styles and no Bootstrap.** The prototype uses inline styles only because of how it was authored. Convert them to classes.
- Use `mockData.ts` (in this folder) as the dummy data source → copy to `src/data/mockData.ts`.
- Add `react-router-dom` for routes (see below), and `lucide-react` for icons.

To view the prototype, open `SpeakWise.dc.html` in a browser (keep `support.js` and `_ds/` next to it). Use the pill tabs at the top to jump between screens, or click through inside either frame.

## Fidelity
**High-fidelity.** Final colors, type, radii, spacing, copy and interactions. Recreate it pixel-close.

## Suggested routes & components
```
/                 Landing        Navbar, Hero, HeroIllustration, Features, FeatureCard, Footer
/login            Login          AuthLayout(BrandPanel | FormCard), TextField, PasswordField, Banner
/register         Register       AuthLayout, TextField, PasswordField, PasswordStrength, ConfirmPasswordField
/admin            AdminDashboard AdminShell(dark sidebar | admin tab bar), KpiCard×5, BarChart, CategoryBars, RecentSessionsTable
/admin/users      AdminUsers     AdminShell, SearchInput, SegmentedControl, UsersTable/UserCard, StatusToggle, AddUserModal/AddUserSheet, Toast
/history          History        AppShell, SearchInput, SegmentedControl, SortChips, SessionRow/SessionTable, EmptyState
/profile          Profile        AppShell, ProfileCard, PreferenceRow, DurationChips, SegmentedControl, Select, Toggle
/home             Home           AppShell(Sidebar | TopBar+TabBar), GreetingHeader, StartSessionCard, StatCard×3, TodayTopicCard, SessionRow, EmptyState
/session/topic    TopicSetup     FocusLayout, StepIndicator, SegmentedControl, ChipGroup, TopicCard, DurationPicker, SessionSummaryCard, StickyActionBar
/session/prepare  Prepare        FocusLayout, ReadingProgressBar, Article, PullQuote, KeyPointsBox, PrepRail(Notes, TextSize, KeyPoints), NotesSheet, ConfirmDialog/BottomSheet
/session/record   Record         CameraPreview, FaceGuide, StatusPill, MicMeter, CountdownOverlay, RecTimer, CueCard, RecordButton/StopButton
/session/review   Review         VideoPlayer, SessionSummary, ConfirmDialog
/session/processing Processing   BreathingLoader, ProgressBar, StepChecklist
/feedback/:id     Feedback       ScoreRing, MetricCard×7, BulletList(well/improve), Transcript(collapsible)
```
Shared primitives: `Button` (primary/secondary/ghost/danger/icon), `Chip`, `Badge` (difficulty/status), `Card`, `ProgressBar`, `ScoreRing`, `Modal` (desktop), `BottomSheet` (mobile).

**Breakpoint:** a mobile layout below 768px and a desktop layout at 1024px and up (tablet can use desktop with narrower rails). Design the mobile layout for **360px wide**.

## Design Tokens (Organic design system)
Put these in `src/index.css` `:root`:
```css
--color-bg:#f5ead8;          /* page ground */
--color-surface:#ebddc5;     /* cards, sidebar, rails */
--color-raised:#f9f4ed;      /* neutral-100: inputs, list rows, tab bar, sticky bars */
--color-text:#201e1d;
--color-divider:rgba(32,30,29,.16);
--color-accent:#c67139;      /* primary */
--accent-100:#fff2eb; --accent-200:#ffe1d0; --accent-300:#ffc6a5; --accent-500:#d67f48;
--accent-600:#b2622d; /* hover */ --accent-700:#8c491a; /* pressed, accent text */ --accent-800:#643312; --accent-900:#402310;
--sage-100:#f0fae1; --sage-200:#e1eecc; --sage-300:#ccdbb2; --sage-400:#aebf92; --sage-500:#8fa073;
--sage-600:#728157; --sage-700:#56633f; --sage-800:#3d472b; --sage-900:#272e1b;
--neutral-200:#eee7db; --neutral-300:#dcd3c4; --neutral-400:#c0b6a5; --neutral-700:#645c50; /* muted text */ --neutral-800:#474238; --neutral-900:#2e2b25;
--danger:#b3402c; --warning:#b7791f; --recording:#e04a33; --rec-dot:#ff5a3d; --timer-final:#ff7a5f;
--camera-bg:#1f1d1a; --on-dark:#f9f4ed;
--font-heading:"Caprasimo",system-ui,sans-serif;   /* headings AND button labels */
--font-body:"Figtree",system-ui,sans-serif;       /* 400/600/700 */
--font-reading:"Literata",Georgia,serif;          /* article body only */
--shadow-sm:0 1px 2px rgba(46,43,37,.14);
--shadow-md:0 3px 10px rgba(46,43,37,.16);
--shadow-lg:0 12px 32px rgba(46,43,37,.22);
```
Google Fonts: `Caprasimo`, `Figtree:wght@400;600;700`, `Literata:opsz,wght@7..72,400;7..72,600`.

**Type scale:** Display 56–72 · H1 42–48 (desktop) / 26–30 (mobile) · H2 32 · H3 24 · Body L 18 · Body 16 (min on mobile) · Caption 13 · Overline 12 (uppercase, letter-spacing .1em, 700, `--accent-700`). Headings are Caprasimo 400 with line-height 1.05–1.2. Reading text is Literata 18px mobile / 20px desktop, line-height 1.7, max width 700px. A−/A+ steps by ±2px (range −2…+4).

**Radius:** chips/rows 24 · cards 32 · large panels/hero 36–44 · buttons, inputs, pills, segmented control **999px** · avatar/icon circles 50%.
**Spacing:** 4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48 / 64. Mobile side padding 20. Desktop content padding 48–64, max width ~1100–1200.

**Buttons:** min-height 48 (52 for the main CTA on mobile, full width). Label is Caprasimo 15–17px, `line-height:1`, flex-centered. Primary: bg `--color-accent`, text `--color-raised`, hover `--accent-600`, active `--accent-700`. Secondary: transparent with a 1.5px `--color-divider` border, hover `--neutral-200`. Ghost: `--accent-700` text. Danger: `--danger`. Disabled: opacity .45. Focus: `outline:2px solid var(--color-accent); outline-offset:2px`.
**Chips (selectable):** 40px tall pill. Off state: `--color-raised` with a 2px transparent border. On state: `--accent-100` bg, 2px `--color-accent` border, `--accent-800` text.
**Difficulty badges:** Beginner `--sage-200`/`--sage-800` · Intermediate `--accent-200`/`--accent-800` · Advanced `--neutral-800`/`--color-raised`. Status "Processing" uses the accent-200 tint.
**Icons:** Lucide, stroke 2.5, 16/20/28px.

## Layout system
- **Desktop app shell (Home, Feedback):** 240px sidebar (`--color-surface`, padding 28/20) with the logo (Caprasimo 24), a full-width "Start session" primary button, nav (Home/History/Profile as pill rows; active = `--color-raised` bg + `--accent-800` text), and the avatar + name + email at the bottom.
- **Mobile app shell (Home):** top bar (logo + 40px avatar) and an 84px bottom tab bar (Home · **Start**, a raised 52px accent circle · History · Profile).
- **Focus layout (all session steps):** no nav. Desktop has a 76px top bar with a × exit (44px circle), a centred step indicator (28px numbered circles joined by 48px lines; done = sage-600 with check, current = accent, todo = outlined), and "Step n · Name" on the right. Mobile has × + step name + "Step n of 4" and a 4-segment progress bar (5px). Primary actions sit in a **sticky bottom bar on mobile** (`--color-raised`, top border) and in a right rail on desktop.

## Screens

### 1. Landing (`/`)
Desktop: a nav (logo left; Home/Features/About/Contact; "Get Started" primary). Hero is a 2-column grid (1.05fr/1fr, gap 64): overline, H1 72px "Master Public Speaking with AI", body 20px, then "Get Started" (primary) and "Learn More" (secondary), 56px tall. On the right is a **styled-div illustration**: a 520px panel with radius 56 in `--color-surface`, two decorative circles (accent-300 and sage-300), a dark "● REC 2:41" pill, a "Today's topic" mini card, and a score card with Clarity/Pace bars. Next comes "Why SpeakWise?" (H2 44) with 4 feature cards (radius 36, 56px icon circle in accent-200; hover `translateY(-4px)` + shadow-md). The footer is dark `--neutral-900` with 3 columns: brand + © 2026, Quick links, and social placeholder circles.
Mobile: a sticky top bar with logo + menu button, which toggles a dropdown with the links and Get Started. Content is stacked, buttons are full width, the illustration is 300px tall, and the feature cards stack.

### 1b. Login (`/login`)
Landing's "Get Started" goes to Login, and Log in goes to Home.
- Desktop: a 50/50 split. On the left is an accent brand panel (radius 48, 20px inset margin) with 3 decorative circles, the logo, the headline "Read. Speak. Get better every day." (Caprasimo 48) and a supporting line. On the right is a centred 440px form.
- Mobile: a 150px accent brand banner, then the form.
- Form: "Welcome back" + "Practice speaking. Build confidence.", an Email field, and a Password field with a Show/Hide toggle button inside the pill. "Forgot password?" is a link. **Log in** is the primary button; while logging in it's darker (accent-600) with a spinner and "Logging in…". Below it: "New here? Create an account".
- Validation on submit: an invalid email shows "Enter a valid email address."; an empty password shows "Enter your password.". The field border turns #B3402C and the error text sits below. A failed login shows a banner (bg #F7DDD6, text #7D2A1B, radius 24): "Email or password is incorrect. Check them and try again." Errors clear as you type.

### 1c. Register (`/register`)
You get here from Login's "Create an account". **Login credentials are email + password.**
- Fields: Full name, Email, **Password** (with a Show/Hide toggle) and **Confirm password**. When the two passwords match, a sage check appears inside the confirm field.
- Password strength shows under the password field while you type: a 3-segment bar (5px pills) plus a label and hint. Weak = #B3402C (1 segment), Fair = #B7791F (2), Strong = sage-600 (3). The text color is #B3402C / #8A5A12 / sage-700.
- Validation on submit: name required; email valid; password at least 8 characters; confirm must match ("Passwords don't match."). Errors use the same style as Login. On success, go to /home.
- Desktop: the same split as Login, but the brand panel is **sage-600** with the headline "Your first talk is 20 minutes away." Mobile: a back arrow + logo, then the form, then "Already have an account? Log in".

### Roles
Login routes by role. `role:'admin'` goes to /admin and students go to /home. *(In the prototype, any email starting with admin@ opens the admin area.)* Protect /admin/* with a role guard. Inactive users can't log in: show the banner "Your account is inactive. Contact your administrator."

### 2. Home (`/home`)
Greeting "Good evening, Priya 👋" + "Ready for today's talk?". The **Start card** is an accent fill with a decorative circle, the title "Start a talk session", a description, a "Start session" button (raised bg, accent-800 text) and a "Suggest me a topic" underlined link. It picks a random topic and opens Topic. Then the **Today's topic** card, **3 stat cards** (Sessions completed 12, Minutes spoken 38, Current streak 4 days; the streak card is sage-200) and **Recent sessions**. On desktop Recent sessions is a table-like list (title | category chip | duration | date | score circle / Processing badge). On mobile it's stacked rows. Clicking a row opens Feedback.
**Empty state** (new user): hide the stats and recent sessions and show a dashed-border card with a mic icon, "No sessions yet" and "Your first talk takes about 20 minutes: 15 to read, a few to speak…".
On desktop, the Start card and Today's topic sit in a 1.6fr/1fr grid.

### 3. Topic setup (step 1)
- Segmented control: **Suggest a topic | My own topic** (the active segment is filled `--color-text` with light text).
- *Suggest*: category chips (All, Technology, Environment, Business, Society, Science). They scroll horizontally on mobile and wrap on desktop. The topic card shows the category chip, difficulty badge, title (Caprasimo 40 desktop / 28 mobile, wraps up to 2+ lines), teaser, and a **"Suggest another"** secondary button with a shuffle icon. It picks a random topic from the filtered pool other than the current one. Choosing a category that excludes the current topic rerolls automatically.
- *My own*: input "What do you want to talk about?" (max 120 chars, counter "n/120") plus 3 example chips that fill the input when tapped. Continue is disabled while the input is empty.
- **Duration:** three large chips, 1 min · 3 min · 5 min (3 is the default), with the helper "You'll speak for this long after reading."
- Summary line "~15 min reading · {n} min speaking". Primary button: **Continue to reading**.
- Desktop: the choice sits on the left; on the right is a 380px sticky "Your session" summary card (Reading ~15 min, Speaking n min, Front camera Required) + CTA.

### 4. Prepare / Reading (step 2)
- A thin 4px reading progress bar under the top bar, driven by the article's scroll position (`scrollTop / (scrollHeight - clientHeight)`).
- Header: category + difficulty, H1 topic title, "≈ 15 min read · 2,800 words".
- Article: H2 sections, Literata paragraphs, a **pull-quote** (4–5px sage-500 left border, Caprasimo 22/30, sage-800), and a **Key points** box (sage-200, radius 28–32, numbered list) after section 1.
- Desktop right rail (380px, `--color-surface`): tiles for suggested time left (a 15:00 countdown, advisory only) and "% read", Key points to cover, Text size A−/A+, a Notes textarea, and **"I'm ready, start talk"**.
- Mobile: A−/A+ in the top bar, a floating dark **Notes** pill that opens a bottom sheet with a textarea, and a sticky bar showing "n% read" + CTA. *(Mobile shows no timer.)*
- If you tap ready with less than 90% read, confirm with "You've read n%. Start anyway?" (Start anyway / Keep reading). This is a Modal on desktop and a BottomSheet on mobile.

### 5. Record (step 3) — dark surface `--camera-bg`
- **Camera check:** a mirrored front-camera preview (use `getUserMedia({video:{facingMode:'user'}})` with `transform:scaleX(-1)`), a dashed rounded face guide, "✓ Camera" / "✓ Microphone" sage pills, a mic level meter (10 bars), the topic title, "Speaking for 3:00", tips (Look at the camera · Speak clearly · Find good light), and a round red **Start** button (84–88px, 5px light border).
- **Countdown:** a dim overlay (rgba(31,29,26,.6)) with "GET READY" and a huge Caprasimo numeral (180px mobile / 240px desktop) counting 5→1, one per second. Each numeral animates `cdPop`: scale 1.4→1 while fading in, then scale .85 while fading out, over 1s ease-out.
- **Live:** a "● REC" pill (the dot pulses, opacity/scale, 1.2s infinite), a large remaining-time countdown (64px mobile / 88px desktop), an elapsed progress bar, and a collapsible **Cue card** with the key points. **Stop** asks for confirmation ("End early?" · "You have m:ss left…" · End recording (danger) / Keep talking) and pauses the timer while the dialog is open. At **≤10s** the timer turns `--timer-final` with "Wrap up now". Recording stops automatically at 0:00.
- Desktop: a 16:9 preview (radius 36) with a controls row below and a 360px right panel (timer card + topic & cue card).
- Mobile: full-screen portrait preview with top/bottom gradients and the controls overlaid.

### 6. Review (step 4)
A video player (placeholder frame, play button, duration), a summary (topic, duration, date), and the actions **Submit for feedback** (primary), **Re-record** (secondary; confirm "This will discard your current recording."), and **Download** (ghost).

### 7. Processing
A breathing circle loader (sage-200 outer / sage-600 inner with an audio icon, scale .88↔1.06 over 3s), "Uploading… n%" then "Analysing your talk", a progress bar, and a checklist: Uploaded · Transcribing speech · Analyzing delivery · Generating feedback (done = sage check, active = spinner ring, todo = outline). Subtext: "This usually takes under a minute. You can leave this page. We'll notify you." Secondary action: **Back to home**. When done, it auto-navigates to Feedback. *(Mock: upload +4% every 200ms, then each step takes 1s.)*

### 8. Feedback report
- A score ring made with a `conic-gradient(sage-600 0 78%, neutral-300 0)` and an inner disc: **78/100** + "Solid talk! Your pacing was excellent."
- 7 metric cards (name, score, bar, optional value, insight). Bar color: ≥80 sage-600, ≥70 accent, otherwise accent-700.
- "What went well" (sage-200) and "What to improve" (accent-200) lists.
- A collapsible **Transcript** with filler words highlighted (`--accent-300` bg, `--accent-900` text, radius 6).
- Actions: **Practice again** (goes back to Prepare with the same topic), **New topic** (Topic with a reroll), **Back to home**.
- Desktop: app shell; a header with the title and actions on the right; a grid of a 340px left column (ring + well/improve) and a right 3-column metric grid + transcript.
- Mobile: back-arrow top bar, stacked layout, a 2-column metric grid, and stacked actions.

### 9. History (`/history`)
Search (title/category), a segmented filter **All · Completed · In progress** (In progress = processing), and sort chips **Date · Score** (score desc; processing sorts last). The count shows "n sessions".
- Desktop: app shell with History active. The toolbar row is search (320px) + filter + "Sort by" chips aligned right. Below is a table-card (radius 40) with an uppercase header (Topic · n sessions | Category | Length | Date | Score) and pill-shaped hover rows (grid `1fr 150px 90px 90px 110px`).
- Mobile: top bar "History" + avatar, full-width search, full-width segmented filter, then "n sessions · Sort [Date][Score]" and stacked session rows. The tab bar has History active.
- Clicking a row opens Feedback. **Empty state** (no results): history icon, "No sessions found", "Try another search or filter." and a **Clear filters** button.

### 10. Profile (`/profile`)
A profile card (avatar initials PS on sage-300, name, email) + **Edit profile** (secondary).
Preferences:
- Default speaking duration: chips 1/3/5 min (preselects Topic).
- Reading text size: segmented Small/Medium/Large.
- Camera and Microphone: pill `<select>`s (use `navigator.mediaDevices.enumerateDevices()` in production).
- Notifications: a toggle (52×32, accent when on and neutral-400 when off, 24px cream knob), "Tell me when feedback is ready".

**Log out** is a danger outline button on desktop and danger text on mobile, and goes to /login.
- Desktop: app shell with Profile active, max width 780, and preferences as rows (label + helper on the left, control on the right) divided by hairlines.
- Mobile: stacked controls and the tab bar with Profile active.

### 11. Admin dashboard (`/admin`)
- **Admin shell (desktop):** a 240px **dark** sidebar (#2E2B25, text #F9F4ED) with the logo + an "Admin" badge (sage-300/sage-900), nav Dashboard · Users · Back to app (active = rgba(249,244,237,.12) pill), and the admin avatar at the bottom. **Mobile:** a top title + "Admin" badge and a 3-tab bar: Dashboard · Users · App.
- Header: H1 "Dashboard", "Platform activity · last updated …", and a "Manage users" secondary button.
- **5 KPI cards** (surface, radius 32): Total users 1,248 · Active users 890 (71% of all users) · Talk sessions recorded 5,630 · Minutes spoken 14,215 · Average score 74. Each has a label (14/600 muted), a value (Caprasimo 34) and a delta (13/600 sage-700). This is a 5-column grid on desktop and 2 columns on mobile.
- **Talk sessions per week:** a CSS bar chart over the last 8 weeks. Bars are accent-colored, radius 14 at the top, with the value above and the week label below. Height = value/800.
- **Sessions by category:** labelled horizontal bars (sage-600 on neutral-300, 8px).
- **Recent sessions:** avatar initials · user · topic · time ago · score circle.
- Desktop grid: chart 1.6fr + category 1fr, with recent sessions full width below.

### 12. Admin users (`/admin/users`)
- Header: "Users", "{active} active · add people and control who can log in.", and a primary **+ Add user** button.
- Toolbar: search (name/email, 340px), a filter segmented control **All · Active · Inactive**, and "Showing n of N users" on the right.
- **Desktop table** (radius 40 card): User (avatar + name + email) | Sessions | Last active | Joined | Status. **Mobile:** stacked cards with the toggle on the right.
- **Status toggle:** a 48×28 pill. **Active = sage-600** with the knob right and the label "Active" in sage-700; **Inactive = neutral-400** with the knob left and the label "Inactive" muted. Clicking flips the status immediately (optimistic) and the KPIs update. In production, PATCH `/users/:id {status}`.
- **Add user:** a Modal on desktop (480px, radius 40) or a BottomSheet on mobile. Fields: Full name, Email, and Status (segmented Active/Inactive, default Active). Helper: "They'll get an email invite to set their password." Validation: name required, email valid, and the email must be unique ("A user with this email already exists."). On success, add the user to the top of the list, close, and show a dark toast: "{name} was added. An invite was sent to {email}." (auto-hides after 3.5s).

## Screenshots
`screenshots/desktop/*.png` (1440×900, 1x) and `screenshots/mobile/*.png` (360×800 inside a device frame, 2x), numbered in flow order:
01 landing · 02 login · 02b register · 03 home · 04 home-empty · 05 topic · 06 prepare · 07 prepare-confirm · 08 record-camera-check · 09 record-countdown · 10 record-live · 11 record-final-10s · 12 review · 13 processing · 14 feedback (transcript open) · 15 history · 16 profile · 17 admin-dashboard · 18 admin-users · 19 admin-add-user.
Each image has a small "MOBILE/DESKTOP" label strip at the top. It isn't part of the UI.

## State (suggested `SessionContext`)
`mode: 'suggest'|'own'`, `topic`, `category`, `ownTopic`, `durationMin: 1|3|5`, `readPct`, `prepSecondsLeft`, `notes`, `textStep`, `phase: 'check'|'countdown'|'live'|'review'|'processing'`, `countdown`, `remainingSec`, `spokenSec`, `uploadPct`, `procStep`, `recordingBlob` (MediaRecorder), `dialog: null|'notes'|'early'|'endEarly'|'rerecord'`. Swap the mock data for API calls later (the FastAPI backend in `speakwise/backend`).

## Motion
Countdown `cdPop` 1s ease-out · REC dot `recPulse` 1.2s infinite · the processing circle `breathe` 3s infinite · cards lift 3–4px on hover (desktop only, .2s). Respect `prefers-reduced-motion`.

## Accessibility
WCAG AA text contrast (use accent-700 for accent-colored body text), touch targets ≥44px, 16px minimum body text on mobile, and visible focus rings. Dialogs trap focus and close on Esc.

## Assets
There are no images. Icons come from Lucide (`lucide-react`): x, shuffle, home, history, user, plus, mic, video, check, clock, book-open, arrow-right/left, square, play, rotate-ccw, download, audio-lines, trending-up, pen, menu, chevron-up/down, flame, eye, sun. The camera, video and illustration are styled divs/placeholders.

## Files
- `SpeakWise.dc.html` — the clickable prototype (both breakpoints side by side, plus a Design system tab).
- `support.js`, `_ds/.../styles.css` — needed only to open the prototype locally.
- `mockData.ts` — typed dummy data for every screen (history, preferences, auth rules, mock accounts, admin KPIs/charts/users).
- `screenshots/` — a PNG of every screen and state, desktop + mobile.
