import { useCallback } from 'react'
import { useNavigate } from 'react-router'
import { ROUTES } from '@/app/routes'
import { usePreferences } from '@/context/PreferencesContext'
import { useSession } from '@/context/SessionContext'
import type { DurationMin, ReadingTextSize, Topic } from '@/core/types'

/** Profile's reading text size → the Prepare step's starting A−/A+ step. */
const TEXT_STEP_FOR: Record<ReadingTextSize, number> = { Small: -1, Medium: 0, Large: 1 }

export interface StartOptions {
  /** Open Topic with this suggestion (e.g. Home's "Use this topic"). */
  topic?: Topic
  /** Open Topic on a fresh random suggestion ("Suggest me a topic"). This is the default. */
  random?: boolean
  /** Open Topic in "My own topic" mode with this text filled in. */
  ownTopic?: string
  durationMin?: DurationMin
}

/** Starts a fresh session flow and opens the Topic step. */
export function useStartSession() {
  const navigate = useNavigate()
  const { dispatch } = useSession()
  const { preferences } = usePreferences()

  return useCallback(
    (options: StartOptions = {}) => {
      // With no suggestion stored, the Topic step fetches a random one from the API.
      dispatch({
        type: 'start',
        durationMin: options.durationMin ?? preferences.defaultDurationMin,
        textStep: TEXT_STEP_FOR[preferences.readingTextSize],
        suggestedTopic: options.random ? undefined : options.topic,
        mode: options.ownTopic ? 'own' : 'suggest',
        ownTopic: options.ownTopic,
      })
      navigate(ROUTES.sessionTopic)
    },
    [dispatch, navigate, preferences.defaultDurationMin, preferences.readingTextSize],
  )
}
