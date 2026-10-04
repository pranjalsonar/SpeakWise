import type { ReactNode } from 'react'
import { createBrowserRouter, Navigate } from 'react-router'
import type { SessionStep } from '@/core/session/sessionReducer'
import { AdminDataProvider } from '@/features/admin/AdminDataProvider'
import { AdminDashboardPage } from '@/features/admin/dashboard/AdminDashboardPage'
import { AdminUsersPage } from '@/features/admin/users/AdminUsersPage'
import { LoginPage } from '@/features/auth/LoginPage'
import { RegisterPage } from '@/features/auth/RegisterPage'
import { DevUiPage } from '@/features/dev/DevUiPage'
import { FeedbackPage } from '@/features/feedback/FeedbackPage'
import { HistoryPage } from '@/features/history/HistoryPage'
import { HomePage } from '@/features/home/HomePage'
import { LandingPage } from '@/features/landing/LandingPage'
import { ProfilePage } from '@/features/profile/ProfilePage'
import { PreparePage } from '@/features/session/prepare/PreparePage'
import { ProcessingPage } from '@/features/session/processing/ProcessingPage'
import { RecordPage } from '@/features/session/record/RecordPage'
import { ReviewPage } from '@/features/session/review/ReviewPage'
import { TopicSetupPage } from '@/features/session/topic/TopicSetupPage'
import { RedirectIfAuthed, RequireAuth, RequireSessionStep } from './guards'
import { ROUTES } from './routes'

const publicOnly = (page: ReactNode) => <RedirectIfAuthed>{page}</RedirectIfAuthed>
const student = (page: ReactNode) => <RequireAuth role="student">{page}</RequireAuth>
/** Session steps also require the flow to have reached that step. */
const sessionStep = (step: SessionStep, page: ReactNode) =>
  student(<RequireSessionStep step={step}>{page}</RequireSessionStep>)

export const router = createBrowserRouter([
  { path: ROUTES.landing, element: <LandingPage /> },
  { path: ROUTES.login, element: publicOnly(<LoginPage />) },
  { path: ROUTES.register, element: publicOnly(<RegisterPage />) },

  // Student app
  { path: ROUTES.home, element: student(<HomePage />) },
  { path: ROUTES.history, element: student(<HistoryPage />) },
  { path: ROUTES.profile, element: student(<ProfilePage />) },
  { path: '/feedback/:id', element: student(<FeedbackPage />) },

  // Session flow
  { path: ROUTES.sessionTopic, element: student(<TopicSetupPage />) },
  { path: ROUTES.sessionPrepare, element: sessionStep('prepare', <PreparePage />) },
  { path: ROUTES.sessionRecord, element: sessionStep('record', <RecordPage />) },
  { path: ROUTES.sessionReview, element: sessionStep('review', <ReviewPage />) },
  { path: ROUTES.sessionProcessing, element: sessionStep('processing', <ProcessingPage />) },

  // Admin (shared data provider for both pages)
  {
    path: ROUTES.admin,
    element: (
      <RequireAuth role="admin">
        <AdminDataProvider />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <AdminDashboardPage /> },
      { path: 'users', element: <AdminUsersPage /> },
    ],
  },

  ...(import.meta.env.DEV ? [{ path: ROUTES.devUi, element: <DevUiPage /> }] : []),

  { path: '*', element: <Navigate to={ROUTES.landing} replace /> },
])
