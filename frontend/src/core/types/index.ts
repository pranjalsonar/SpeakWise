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

export interface ReadingMaterial {
  topicId: string
  readMinutes: number
  wordCount: number
  keyPoints: string[]
  sections: ArticleSection[]
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
export type UserStatus = 'Active' | 'Inactive'

export interface AdminUser {
  id: string
  name: string
  email: string
  sessions: number
  lastActive: string
  joined: string
  status: UserStatus
}

export interface AdminKpi {
  key: 'totalUsers' | 'activeUsers' | 'sessions' | 'minutes' | 'avgScore'
  label: string
  value: number
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
  user: string
  topic: string
  score: number
  when: string
}

export interface LandingFeature {
  icon: 'shuffle' | 'audio-lines' | 'book-open' | 'trending-up'
  title: string
  description: string
}
