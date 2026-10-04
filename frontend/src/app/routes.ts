import type { Role } from '@/core/types'

export const ROUTES = {
  landing: '/',
  login: '/login',
  register: '/register',
  home: '/home',
  history: '/history',
  profile: '/profile',
  sessionTopic: '/session/topic',
  sessionPrepare: '/session/prepare',
  sessionRecord: '/session/record',
  sessionReview: '/session/review',
  sessionProcessing: '/session/processing',
  feedback: (id: string) => `/feedback/${id}`,
  admin: '/admin',
  adminUsers: '/admin/users',
  devUi: '/dev/ui',
} as const

export const homePathFor = (role: Role) => (role === 'admin' ? ROUTES.admin : ROUTES.home)
