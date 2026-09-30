import {
  adminUsers,
  feedbackReport,
  historySessions,
  mockAccounts,
  processingSteps,
  recentSessions,
  stats,
} from '../data/mockData'
import type { FeedbackReport, Session, Stats } from '../types'
import { sleep } from '../utils'

export interface Dashboard {
  stats: Stats
  recentSessions: Session[]
}

/** Accounts that come with practice history. Newly registered users start empty. */
const hasHistory = (email: string) => {
  const e = email.toLowerCase()
  return (
    mockAccounts.some((a) => a.email === e) ||
    adminUsers.some((u) => u.email === e && u.sessions > 0)
  )
}

export async function getDashboard(email: string): Promise<Dashboard> {
  await sleep(350)
  if (!hasHistory(email)) {
    return { stats: { sessionsCompleted: 0, minutesSpoken: 0, streakDays: 0 }, recentSessions: [] }
  }
  return { stats, recentSessions }
}

export async function getHistory(email: string): Promise<Session[]> {
  await sleep(350)
  return hasHistory(email) ? historySessions : []
}

export async function getFeedback(sessionId: string): Promise<FeedbackReport> {
  await sleep(400)
  const session = [...recentSessions, ...historySessions].find((s) => s.id === sessionId)
  if (!session) return { ...feedbackReport, sessionId }
  return {
    ...feedbackReport,
    sessionId,
    topicTitle: session.topicTitle,
    duration: `${session.durationMin}:00`,
    overallScore: session.score ?? feedbackReport.overallScore,
  }
}

export const getProcessingSteps = (): string[] => processingSteps

/** Report id for the talk that was just recorded (mock; the backend returns a real session id). */
export const LATEST_REPORT_ID = 'latest'

/** Mock processing timings (handoff § Processing). */
export const PROCESSING = {
  uploadTickMs: 200,
  uploadStepPct: 4,
  stepMs: 1000,
} as const
