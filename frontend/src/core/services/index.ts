// Mock data access for screens not yet on the backend. Real API calls live in src/api.
export * as authService from './authService'
export { AuthError } from './authService'
export * as contentService from './contentService'
export type { AuthErrorCode } from './authService'
export * as preferencesService from './preferencesService'
export * as sessionService from './sessionService'
export * as topicService from './topicService'
