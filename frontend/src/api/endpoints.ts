// Every backend route the frontend calls, relative to API_CONFIG.prefix.
// Group by backend module; add a section when you add an api.<module>.ts file.
export const ENDPOINTS = {
  auth: {
    login: '/auth/login',
    logout: '/auth/logout',
    me: '/auth/me',
  },
  users: {
    me: '/users/me',
  },
  topics: {
    suggest: '/topics/suggest',
    daily: '/topics/daily',
    custom: '/topics/custom',
    byId: (id: string) => `/topics/${encodeURIComponent(id)}`,
    readingMaterial: (id: string) => `/topics/${encodeURIComponent(id)}/reading-material`,
  },
  adminDashboard: {
    summary: '/admin/dashboard',
  },
  adminUsers: {
    list: '/users',
    byId: (id: number) => `/users/${id}`,
    resetPassword: (id: number) => `/users/${id}/reset-password`,
  },
} as const
