// Single entry point for data access. Swap these mock modules for API-backed ones later.
export * as adminService from './adminService'
export * as authService from './authService'
export { AuthError } from './authService'
export * as contentService from './contentService'
export type { AuthErrorCode } from './authService'
export * as preferencesService from './preferencesService'
export * as sessionService from './sessionService'
export * as topicService from './topicService'
