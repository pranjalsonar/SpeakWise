import { useCallback } from 'react'
import { useNavigate } from 'react-router'
import { ROUTES } from '@/app/routes'
import { usePreferences } from '@/context/PreferencesContext'
import { useSession } from '@/context/SessionContext'
import { topicService } from '@/core/services'
import type { ReadingTextSize } from '@/core/types'
import { pickRandomTopic } from '@/core/utils'

/** Profile's reading text size → the Prepare step's starting A−/A+ step. */
const TEXT_STEP_FOR: Record<ReadingTextSize, number> = { Small: -1, Medium: 0, Large: 1 }

export interface StartOptions {
  /** Open Topic with this suggested topic (e.g. "Use this topic"). */
  topicId?: string
  /** Open Topic with a random suggestion ("Suggest me a topic"). */
  random?: boolean
}

/** Starts a fresh session flow and opens the Topic step. */
export function useStartSession() {
  const navigate = useNavigate()
  const { dispatch } = useSession()
  const { preferences } = usePreferences()

  return useCallback(
    (options: StartOptions = {}) => {
      const suggestedTopicId = options.random
        ? pickRandomTopic(topicService.getTopics())?.id
        : options.topicId
      dispatch({
        type: 'start',
        durationMin: preferences.defaultDurationMin,
        textStep: TEXT_STEP_FOR[preferences.readingTextSize],
        suggestedTopicId,
      })
      navigate(ROUTES.sessionTopic)
    },
    [dispatch, navigate, preferences.defaultDurationMin, preferences.readingTextSize],
  )
}
