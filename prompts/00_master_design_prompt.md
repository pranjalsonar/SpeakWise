# SpeakWise — Master UI Design Prompt

> Paste everything below the line into Claude Design. It is self-contained.

---

## Role

You are a senior product designer creating the complete UI for **SpeakWise**, a responsive web app that will also ship as **native Android and iOS apps** (React Native). Design **every screen in two frames**:

- **Mobile**: **360 × 800** (common Android size, our primary test device). Design at this size first, so everything must fit comfortably at 360px wide: 16px side gutters (328px content width), no horizontal scrolling, no truncated primary buttons, and key actions reachable without scrolling on the camera and record screens. It must also scale up cleanly to 390–430px phones. This frame is the reference for **both** the mobile web layout **and** the native Android/iOS app, so design it like a native app: bottom tab bar, full-screen stack screens, bottom sheets, a native-feeling camera screen, and safe areas for notch and home indicator. Avoid hover-only interactions and web-only patterns.
- **Desktop**: 1440 × 900

Use components that can be built on both web and React Native (no CSS-only tricks such as complex blend modes, backdrop filters as essential UI, or hover-dependent content).

Use realistic dummy content (provided below), not lorem ipsum. Build a small, consistent design system first, then use it on every screen.

---

## The product

SpeakWise is an AI public-speaking coach for college students and interview candidates. It builds speaking confidence and subject knowledge at the same time.

**How it works:**

1. The user logs in and lands on a welcome page.
2. They start a **talk session**: they either type their own topic or let SpeakWise **suggest a random topic** (and can reroll). They pick how long they will speak (**1, 3, or 5 minutes**).
3. SpeakWise gives them **~15 minutes of reading material** on the topic. They read, optionally take notes, then tap **I'm ready**.
4. The **front camera** opens. They tap **Start**, a big **5 · 4 · 3 · 2 · 1** countdown plays over the camera preview, then recording begins with a **countdown timer** for their chosen duration. They talk about the topic. Recording stops automatically at 0:00, or early if they choose.
5. They review the clip, then **submit** it (or re-record).
6. The video and audio are analysed on the server. The user sees a processing state, then a **feedback report**.

---

## Brand & visual direction

- **Personality**: calm, confident, encouraging, professional. It should feel like a premium coaching tool, not a game or a social app.
- **Keywords**: clean · focused · trustworthy · modern · airy.
- **Color**
  - Surfaces: white and a very light cool gray background (#F8FAFC-ish)
  - Neutrals: slate scale for text and borders
  - Primary: one confident blue (around #2563EB) for primary actions and focus
  - Semantic: success green, warning amber, danger red
  - **Recording red** is reserved for the live recording indicator and timer warning
  - Camera and recording screens use a **dark** surface (near-black slate) so the video stands out
- **Typography**: Inter (or a similar geometric sans) for UI. A comfortable **serif for the long reading article** (Source Serif 4, Literata, or similar), ~18px on mobile and ~20px on desktop, line-height ~1.7, max width ~70 characters.
- **Shape & depth**: 12–16px radius on cards, 10–12px on buttons and inputs, soft low-contrast shadows, 1px hairline borders. 8px spacing grid, generous whitespace.
- **Iconography**: Lucide-style outline icons, 1.5–2px stroke.
- **Imagery**: no stock photos. Use subtle abstract shapes, soft gradients, or simple line illustrations sparingly (empty states, login).
- **Motion notes** (annotate, don't animate): countdown numbers scale and fade, recording dot pulses, cards lift slightly on hover (desktop only).

---

## Layout system

- **Desktop app shell**: left sidebar (240px) with logo, nav (Home, History, Profile), a prominent **Start session** button, and the user avatar at the bottom. Content max width ~1200px.
- **Mobile app shell**: top bar (logo/greeting + avatar) and a bottom tab bar (Home · Start (center, emphasized) · History · Profile). Respect safe areas.
- **Focus layout** (all session steps: Topic, Prepare, Camera, Record, Review, Processing): no nav, only a slim top bar with an **× exit** (left), a **step indicator** (Topic → Prepare → Record → Review), and the step name. Primary actions sit in a **sticky bottom bar on mobile** and inline or in a right rail on desktop.
- Touch targets ≥ 48px on mobile. Primary button full-width on mobile.
- **Fit at 360 × 800**: after the status bar (~24px), top bar (~56px) and bottom tab bar (~64px), roughly **650px** of content height remains. The home hero CTA must be visible without scrolling. The 3 stat cards fit in one row at 360px (compact) or wrap to a scrollable row. The duration chips (1 / 3 / 5 min) fit in one row. Topic titles wrap to at most 2 lines at H2 size.

---

## Design system page (deliver first)

One frame showing:

- Color palette with token names (`primary-600`, `slate-900`, `danger-500`, `surface`, `surface-muted`, `recording`, …)
- Type scale (Display, H1, H2, H3, Body L, Body, Caption, Overline) + reading serif sample
- Spacing scale and radius tokens
- Buttons: primary, secondary, ghost, danger, icon button, with default / hover / pressed / disabled / loading states
- Inputs: text, password with show/hide, textarea, with error and helper text
- Chips (selectable, used for categories and durations), badges (difficulty: Beginner / Intermediate / Advanced, status)
- Cards: session card, stat card, topic card
- Progress bar, circular score ring (0–100), step indicator, tabs/segmented control
- Modal (desktop) and bottom sheet (mobile), toast, skeleton loader, empty state

---

## Screens to design (mobile + desktop for each)

### 1. Login
- Logo, headline "Welcome back", subtext "Practice speaking. Build confidence."
- Email, password (show/hide), "Forgot password?", **Log in** primary button, "New here? Create an account".
- Desktop: split layout. Left side is a brand panel with a short value proposition and a subtle illustration; right side is the form card.
- States: default, field validation errors, loading button, wrong-credentials error banner.

### 2. Register
- Name, email, password (with strength hint), **Create account**, link back to login. Same layout as Login.

### 3. Home / Welcome
- Greeting: "Good evening, Priya 👋" + subline "Ready for today's talk?"
- **Hero card**: "Start a talk session" with short description and **Start session** primary button. Secondary link: "Suggest me a topic".
- **Stats row** (3 stat cards): Sessions completed **12**, Minutes spoken **38**, Current streak **4 days**.
- **Recent sessions** list (3–4 items): topic title, category chip, duration, date, status badge or score. "View all" link.
- Optional **Today's topic** card: "Should AI tutors replace homework help?" · Technology · Intermediate.
- Also design the **empty state** for a brand-new user (no sessions yet).

### 4. Topic setup (step 1: Topic)
- Segmented control: **Suggest a topic** | **My own topic**.
- *Suggest* tab: a large topic card showing title, category chip, difficulty badge, and a one-line teaser, with a **🔀 Suggest another** button. Optional category filter chips: Technology, Environment, Business, Society, Science.
- *My own* tab: text input "What do you want to talk about?", character counter, a few example suggestions as chips.
- **Speaking duration**: three large selectable chips: **1 min** · **3 min** · **5 min** (3 min preselected), with helper text "You'll speak for this long after reading."
- Summary line: "~15 min reading · 3 min speaking".
- Primary: **Continue to reading**.
- Desktop: topic choice on the left, sticky summary card on the right.

### 5. Prepare / Reading (step 2: Prepare)
- Header: topic title, category + difficulty, "≈ 15 min read · 2,800 words".
- **Reading article** with section headings, paragraphs, a pull-quote, and a "Key points" box.
- **Reading progress** (thin bar at top + "42% read").
- **Prep timer** showing suggested time remaining (e.g. "11:24 left"). It's advisory, not blocking.
- **Notes**: desktop has a right-rail notes panel. Mobile has a floating "Notes" button that opens a bottom sheet.
- Right rail on desktop also shows **Key points to cover** (4–5 bullets) and a text-size control (A− / A+).
- Primary: **I'm ready, start talk** (sticky bottom on mobile).
- A confirmation sheet or modal if tapped early: "You've read 42%. Start anyway?"

### 6. Camera check (step 3: Record, before starting)
- Dark screen. **Mirrored front-camera preview** (use a neutral placeholder silhouette of a person framed head-and-shoulders).
- Face framing guide (subtle rounded outline), mic level meter, "Camera ✓ · Microphone ✓" status pills.
- Topic title and duration shown ("Speaking for 3:00").
- Tips: "Look at the camera · Speak clearly · Find good light".
- Primary: large round **Start** button.
- Desktop: 16:9 preview centered, right panel with topic + key points cue card.
- **States to design**: permission request (explainer before the browser prompt), **permission denied** (how to enable in browser settings + Retry), no camera found.

### 7. Recording
- **Countdown overlay**: huge centered numeral over the dimmed preview. Show the "3" frame and label the sequence as 5 → 4 → 3 → 2 → 1.
- **Live recording**: pulsing red "● REC" pill, large **countdown timer** (e.g. "2:41") at top, thin progress ring or bar showing time elapsed, collapsible **cue card** with key points, **Stop** button (with confirm "End early?").
- Show a variant for the **final 10 seconds** (timer turns red/amber, "0:08").
- Mobile: full-screen portrait video, controls overlaid with a bottom gradient. Desktop: preview with side panel.

### 8. Review (step 4: Review)
- Video player with the recorded clip (placeholder frame), duration "3:00".
- Session summary: topic, duration, date.
- Actions: **Submit for feedback** (primary), **Re-record** (secondary), **Download** (ghost).
- A confirm modal for re-record: "This will discard your current recording."

### 9. Processing
- Upload progress bar ("Uploading… 68%"), then an analysis state with calm animated illustration notes.
- Checklist of steps: ✓ Uploaded · ◌ Transcribing speech · ◌ Analyzing delivery · ◌ Generating feedback.
- Subtext: "This usually takes under a minute. You can leave this page. We'll notify you."
- Secondary: **Back to home**. Also design an upload-failed state with **Retry**.

### 10. Feedback report
- Header: topic, date, duration, and a large **overall score ring (78/100)** with a one-line verdict ("Solid talk! Your pacing was excellent.").
- **Metric cards** (score 0–100, a value, and one-line insight each):
  - Clarity **82**: "Most sentences were clear and well-structured."
  - Pace **88**, 142 wpm: "Right in the ideal range (130–160 wpm)."
  - Confidence **74**: "Steady voice, slight hesitation at the start."
  - Filler words **65**, 9 fillers: "'um' ×5, 'like' ×4. Try pausing instead."
  - Eye contact **70**: "Looked away from the camera ~30% of the time."
  - Relevance **85**: "Covered 4 of 5 key points."
  - Vocabulary **79**: "Good range; try more topic-specific terms."
- **What went well** (3 bullets) and **What to improve** (3 bullets).
- Collapsible **Transcript** with filler words highlighted.
- Actions: **Practice again** (same topic), **New topic**, **Back to home**.
- Desktop: score overview on the left, 2–3 column metric grid on the right.

### 11. History
- Filter/sort bar (All · Completed · In progress; sort by date or score) and search.
- List of session cards (topic, category, duration, date, score or status). Desktop can use a table-like list.
- Empty state.

### 12. Profile & settings
- Avatar, name, email, edit profile.
- Preferences: default speaking duration, reading text size, camera/mic device selection, notifications toggle.
- Log out.

---

## Dummy data

**User**: Priya Sharma · priya.sharma@example.com

**Topics** (title · category · difficulty):
- Should AI tutors replace homework help? · Technology · Intermediate
- The case for a four-day work week · Business · Intermediate
- Fast fashion and its environmental cost · Environment · Beginner
- Is social media making us lonelier? · Society · Beginner
- CRISPR and the ethics of gene editing · Science · Advanced
- Remote work vs. office culture · Business · Beginner
- Space exploration: worth the cost? · Science · Intermediate

**Reading sample** (topic: *Fast fashion and its environmental cost*):
- Sections: "What is fast fashion?", "The true cost of a $5 T-shirt", "Water, waste and microplastics", "Who pays the price?", "What can change?"
- Opening paragraph: "Fast fashion is a business model built on speed: trend-driven clothing designed, produced, and sold in a matter of weeks at very low prices. Brands release new collections constantly, encouraging shoppers to buy more and wear items fewer times. The result is an industry that produces over 100 billion garments a year, and a growing mountain of textile waste."
- Key points: 1) What defines fast fashion, 2) Environmental impact (water, carbon, waste), 3) Human and labour costs, 4) Role of consumers, 5) Solutions: circular fashion, regulation, buying less.

**Recent sessions**:
- Fast fashion and its environmental cost · 3 min · Sep 25 · Score 78
- Is social media making us lonelier? · 1 min · Sep 23 · Score 71
- The case for a four-day work week · 5 min · Sep 20 · Score 84
- Remote work vs. office culture · 3 min · Sep 18 · Processing

---

## Deliverables

1. Design system frame.
2. All 12 screens × {mobile, desktop}, including the listed states (empty, error, permission denied, countdown, final 10 s, processing, upload failed).
3. A **user-flow overview** frame connecting the screens: Login → Home → Topic → Prepare → Camera → Record → Review → Processing → Feedback.
4. Short annotations for interactions and motion.

**Constraints**
- Everything must be implementable with plain CSS (flex/grid) in React. No exotic effects.
- WCAG AA contrast, clear focus states, readable 16px minimum body text on mobile.
- Keep it consistent: same components, spacing, and radii everywhere.
- Design for real content lengths (long topic titles should wrap gracefully to 2 lines).
