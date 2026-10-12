// Domain types shared by every screen (and, later, the React Native app).

export type Difficulty = 'Beginner' | 'Intermediate' | 'Advanced'
export type Category = 'Technology' | 'Environment' | 'Business' | 'Society' | 'Science'
export type CategoryFilter = 'All' | Category
export type DurationMin = 1 | 3 | 5

export interface Topic {
  id: string
  title: string
  category: Category
  difficulty: Difficulty
  teaser: string
  /** Has the current user already recorded a talk on it? (from the API) */
  recorded?: boolean
}

export type SessionStatus = 'completed' | 'processing'

export interface Session {
  id: string
  topicTitle: string
  category: Category
  durationMin: DurationMin
  date: string
  score: number | null
  status: SessionStatus
}

export interface Stats {
  sessionsCompleted: number
  minutesSpoken: number
  streakDays: number
}

export interface ArticleSection {
  heading: string
  paragraphs: string[]
  pullQuote?: string
  showKeyPoints?: boolean
}

export interface ReadingSource {
  title: string
  /** Permalink to the exact Wikipedia revision used. */
  url: string
}

/** One version of a topic's reading material (GET /topics/{id}/reading-material). */
export interface ReadingMaterial {
  /** Send back when the talk session is saved, so this version isn't served again. */
  id: number
  topicId: string
  version: number
  /** The user has recorded every version; this one is shown again. */
  isRepeat: boolean
  readMinutes: number
  wordCount: number
  summary: string
  keyPoints: string[]
  sections: ArticleSection[]
  sources: ReadingSource[]
  /** "Adapted from Wikipedia articles … licensed under CC BY-SA 4.0." */
  attribution: string
  licenseUrl: string
  /** Only when isRepeat: other topics the user hasn't recorded yet. */
  relatedTopics: Topic[]
}

export interface Metric {
  key: string
  name: string
  score: number
  value?: string
  insight: string
}

export interface TranscriptSegment {
  text: string
  isFiller: boolean
}

export interface FeedbackReport {
  sessionId: string
  topicTitle: string
  date: string
  duration: string
  overallScore: number
  verdict: string
  metrics: Metric[]
  wentWell: string[]
  toImprove: string[]
  transcript: TranscriptSegment[]
}

export type Role = 'student' | 'admin'

export interface User {
  name: string
  firstName: string
  email: string
  initials: string
  role: Role
  /** ISO date the account was created (only for backend users). */
  joinedAt?: string
}

export type ReadingTextSize = 'Small' | 'Medium' | 'Large'

export interface Preferences {
  defaultDurationMin: DurationMin
  readingTextSize: ReadingTextSize
  selectedCamera: string
  selectedMicrophone: string
  notifications: boolean
}

export interface DeviceOptions {
  cameras: string[]
  microphones: string[]
}

// ---------- Admin ----------
/** A user as the admin Users screen sees them (from GET /users). */
export interface AdminUser {
  id: number
  name: string
  /** null when the account has no name set (name falls back to the email). */
  fullName: string | null
  email: string
  initials: string
  role: Role
  isActive: boolean
  sessions: number
  /** ISO dates. lastActiveAt is null if they never logged in or recorded a session. */
  lastActiveAt: string | null
  joinedAt: string
}

export interface AdminUserCounts {
  all: number
  active: number
  inactive: number
}

export interface AdminKpi {
  key: 'totalUsers' | 'activeUsers' | 'sessions' | 'minutes' | 'avgScore'
  label: string
  /** null when there's no data yet (e.g. no scored sessions); shown as "—". */
  value: number | null
  delta: string
}

export interface WeeklyCount {
  week: string
  count: number
}

export interface CategoryShare {
  category: Category
  pct: number
}

export interface AdminRecentSession {
  id?: string
  user: string
  topic: string
  score: number
  when: string
}

export interface AdminDashboard {
  kpis: AdminKpi[]
  sessionsPerWeek: WeeklyCount[]
  sessionsByCategory: CategoryShare[]
  recentSessions: AdminRecentSession[]
  lastUpdated: string
}

export interface LandingFeature {
  icon: 'shuffle' | 'audio-lines' | 'book-open' | 'trending-up'
  title: string
  description: string
}
