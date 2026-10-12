import type { Category, CategoryFilter, Difficulty, DurationMin, Topic } from '../types'

/** A topic chosen for a session. Own topics have no category or difficulty. */
export interface SessionTopic {
  /** Backend topic id (curated or custom). */
  id: string
  title: string
  category?: Category
  difficulty?: Difficulty
}

export type TopicMode = 'suggest' | 'own'

/** How far the user has got. Used by route guards. */
export type SessionStep = 'topic' | 'prepare' | 'record' | 'review' | 'processing' | 'feedback'

export interface Recording {
  /** Object URL (web) or file URI (native). */
  url: string
  mimeType: string
  durationSec: number
  /** True when no camera was available and the flow ran on the placeholder preview. */
  simulated: boolean
}

export interface SessionState {
  step: SessionStep
  mode: TopicMode
  category: CategoryFilter
  /** The suggestion shown on the Topic step (from the API). */
  suggestedTopic: Topic | null
  ownTopic: string
  durationMin: DurationMin
  topic: SessionTopic | null
  /** Reading-material version read on Prepare; saved with the talk so it isn't served again. */
  readingMaterialId: number | null
  /** Its key points, for the cue card on the Record step. */
  keyPoints: string[]
  readPct: number
  notes: string
  textStep: number
  recording: Recording | null
  feedbackSessionId: string | null
}

/** Article text size steps (each step = 2px): −1 … +2. */
export const TEXT_STEP_MIN = -1
export const TEXT_STEP_MAX = 2
export const TEXT_STEP_PX = 2
export const OWN_TOPIC_MAX = 120
export const READY_THRESHOLD_PCT = 90
export const PREP_SECONDS = 15 * 60
export const COUNTDOWN_FROM = 5
export const FINAL_SECONDS = 10

export const createInitialSession = (durationMin: DurationMin = 3): SessionState => ({
  step: 'topic',
  mode: 'suggest',
  category: 'All',
  suggestedTopic: null,
  ownTopic: '',
  durationMin,
  topic: null,
  readingMaterialId: null,
  keyPoints: [],
  readPct: 0,
  notes: '',
  textStep: 0,
  recording: null,
  feedbackSessionId: null,
})

export type SessionAction =
  | {
      type: 'start'
      durationMin: DurationMin
      textStep?: number
      suggestedTopic?: Topic
      mode?: TopicMode
      ownTopic?: string
    }
  | { type: 'setMode'; mode: TopicMode }
  | { type: 'setCategory'; category: CategoryFilter }
  | { type: 'suggestTopic'; topic: Topic }
  | { type: 'setOwnTopic'; text: string }
  | { type: 'setDuration'; durationMin: DurationMin }
  | { type: 'confirmTopic'; topic: SessionTopic }
  | { type: 'setReadingMaterial'; id: number; keyPoints: string[] }
  | { type: 'setReadPct'; pct: number }
  | { type: 'setNotes'; notes: string }
  | { type: 'setTextStep'; step: number }
  | { type: 'goToRecord' }
  | { type: 'recorded'; recording: Recording }
  | { type: 'discardRecording' }
  | { type: 'submit' }
  | { type: 'processed'; sessionId: string }
  | { type: 'practiceAgain' }
  | { type: 'reset'; durationMin: DurationMin }

export function sessionReducer(state: SessionState, action: SessionAction): SessionState {
  switch (action.type) {
    case 'start':
      return {
        ...createInitialSession(action.durationMin),
        textStep: action.textStep ?? 0,
        suggestedTopic: action.suggestedTopic ?? null,
        mode: action.mode ?? 'suggest',
        ownTopic: (action.ownTopic ?? '').slice(0, OWN_TOPIC_MAX),
      }
    case 'setMode':
      return { ...state, mode: action.mode }
    case 'setCategory':
      return { ...state, category: action.category }
    case 'suggestTopic':
      return { ...state, suggestedTopic: action.topic }
    case 'setOwnTopic':
      return { ...state, ownTopic: action.text.slice(0, OWN_TOPIC_MAX) }
    case 'setDuration':
      return { ...state, durationMin: action.durationMin }
    case 'confirmTopic':
      return {
        ...state,
        topic: action.topic,
        step: 'prepare',
        readPct: 0,
        recording: null,
        readingMaterialId: null,
        keyPoints: [],
      }
    case 'setReadingMaterial':
      return { ...state, readingMaterialId: action.id, keyPoints: action.keyPoints }
    case 'setReadPct':
      return { ...state, readPct: Math.max(state.readPct, Math.round(action.pct)) }
    case 'setNotes':
      return { ...state, notes: action.notes }
    case 'setTextStep':
      return {
        ...state,
        textStep: Math.min(TEXT_STEP_MAX, Math.max(TEXT_STEP_MIN, action.step)),
      }
    case 'goToRecord':
      return { ...state, step: 'record', recording: null }
    case 'recorded':
      return { ...state, step: 'review', recording: action.recording }
    case 'discardRecording':
      return { ...state, step: 'record', recording: null }
    case 'submit':
      return { ...state, step: 'processing' }
    case 'processed':
      return { ...state, step: 'feedback', feedbackSessionId: action.sessionId }
    case 'practiceAgain':
      // Prepare fetches the material again: after a recorded talk the API serves a new version.
      return state.topic
        ? {
            ...state,
            step: 'prepare',
            readPct: 0,
            recording: null,
            feedbackSessionId: null,
            readingMaterialId: null,
            keyPoints: [],
          }
        : state
    case 'reset':
      return createInitialSession(action.durationMin)
  }
}

const STEP_ORDER: SessionStep[] = ['topic', 'prepare', 'record', 'review', 'processing', 'feedback']

/** True if the session has reached (or passed) `step`. */
export const hasReached = (state: SessionState, step: SessionStep) =>
  STEP_ORDER.indexOf(state.step) >= STEP_ORDER.indexOf(step)
