import { useCallback, useEffect, useRef, useState } from 'react'
import { ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router'
import * as topicsApi from '@/api/api.topics'
import { ApiError } from '@/api/client'
import { ROUTES } from '@/app/routes'
import { FocusLayout } from '@/components/layout/FocusLayout'
import { StickyActionBar } from '@/components/layout/StickyActionBar'
import { Banner } from '@/components/ui/Banner'
import { Button } from '@/components/ui/Button'
import { Chip } from '@/components/ui/Chip'
import { SegmentedControl } from '@/components/ui/SegmentedControl'
import { Skeleton } from '@/components/ui/Skeleton'
import { useSession } from '@/context/SessionContext'
import type { SessionTopic, TopicMode } from '@/core/session/sessionReducer'
import { topicService } from '@/core/services'
import type { CategoryFilter, Topic } from '@/core/types'
import { useIsDesktop } from '@/hooks/useMediaQuery'
import { DurationPicker } from './DurationPicker'
import { OwnTopicInput } from './OwnTopicInput'
import { SessionSummaryCard } from './SessionSummaryCard'
import { TopicCard } from './TopicCard'
import './TopicSetupPage.css'

const MODE_LABELS = { suggest: 'Suggest a topic', own: 'My own topic' } as const
const MODE_OPTIONS = [MODE_LABELS.suggest, MODE_LABELS.own] as const

export function TopicSetupPage() {
  const navigate = useNavigate()
  const isDesktop = useIsDesktop()
  const { session, dispatch } = useSession()
  const { mode, category, suggestedTopic, ownTopic, durationMin } = session

  // ---- Suggested (curated) topic, from the API ----
  const [suggesting, setSuggesting] = useState(false)
  const [suggestError, setSuggestError] = useState<string | null>(null)
  const [allRecorded, setAllRecorded] = useState(false)
  const latestRequest = useRef(0)

  // Only sets state once the response arrives (safe to call from an effect).
  const loadSuggestion = useCallback(
    async (forCategory: CategoryFilter, excludeId?: string) => {
      const request = ++latestRequest.current // only the newest request may update the page
      try {
        const result = await topicsApi.suggestTopic({ category: forCategory, excludeId })
        if (request !== latestRequest.current) return
        dispatch({ type: 'suggestTopic', topic: result.topic })
        setAllRecorded(result.allRecorded)
        setSuggestError(null)
      } catch (error) {
        if (request !== latestRequest.current) return
        setSuggestError(error instanceof ApiError ? error.message : "Couldn't load a topic.")
      } finally {
        if (request === latestRequest.current) setSuggesting(false)
      }
    },
    [dispatch],
  )

  // User-triggered: show the loading state right away.
  const fetchSuggestion = (forCategory: CategoryFilter, excludeId?: string) => {
    setSuggesting(true)
    setSuggestError(null)
    void loadSuggestion(forCategory, excludeId)
  }

  // First visit (or after "Suggest me a topic"): fetch a random suggestion.
  // No topic yet already renders the skeleton, so no loading flag is needed here.
  useEffect(() => {
    if (mode !== 'suggest' || suggestedTopic) return
    let active = true // ignored once a topic arrives from elsewhere (e.g. a reroll)
    topicsApi.suggestTopic({ category }).then(
      (result) => {
        if (!active) return
        dispatch({ type: 'suggestTopic', topic: result.topic })
        setAllRecorded(result.allRecorded)
        setSuggestError(null)
      },
      (error: unknown) => {
        if (active) {
          setSuggestError(error instanceof ApiError ? error.message : "Couldn't load a topic.")
        }
      },
    )
    return () => {
      active = false
    }
  }, [mode, suggestedTopic, category, dispatch])

  const changeCategory = (next: CategoryFilter) => {
    dispatch({ type: 'setCategory', category: next })
    // A category that excludes the current topic fetches a new one.
    if (next !== 'All' && suggestedTopic?.category !== next) fetchSuggestion(next)
  }

  // ---- Own topic: resolved against Wikipedia when the user continues ----
  const [resolving, setResolving] = useState(false)
  const [ownError, setOwnError] = useState<topicsApi.CustomTopicError | null>(null)

  const setOwnTopic = (text: string) => {
    dispatch({ type: 'setOwnTopic', text })
    setOwnError(null)
  }

  const pickRelatedTopic = (topic: Topic) => {
    dispatch({ type: 'suggestTopic', topic })
    dispatch({ type: 'setMode', mode: 'suggest' })
    setOwnError(null)
  }

  // ---- Continue ----
  const ownTitle = ownTopic.trim()
  const canContinue =
    mode === 'suggest' ? Boolean(suggestedTopic) && !suggesting : ownTitle.length >= 3

  const chosenTitle =
    mode === 'own' ? ownTitle || 'Your topic' : (suggestedTopic?.title ?? 'Your topic')

  const confirm = (topic: SessionTopic) => {
    dispatch({ type: 'confirmTopic', topic })
    navigate(ROUTES.sessionPrepare)
  }

  const onContinue = async () => {
    if (!canContinue || resolving) return
    if (mode === 'suggest' && suggestedTopic) {
      confirm(topicsApi.toSessionTopic(suggestedTopic))
      return
    }
    setResolving(true)
    setOwnError(null)
    try {
      const { topic } = await topicsApi.createCustomTopic(ownTitle)
      confirm(topic)
    } catch (error) {
      setOwnError(topicsApi.customTopicError(error))
      setResolving(false)
    }
  }

  const summary = `~15 min reading · ${durationMin} min speaking`

  const continueButton = (
    <Button
      size="lg"
      block
      disabled={!canContinue}
      loading={resolving}
      iconRight={isDesktop && !resolving ? <ArrowRight size={20} /> : undefined}
      onClick={() => void onContinue()}
    >
      {resolving ? 'Finding reading material…' : 'Continue to reading'}
    </Button>
  )

  return (
    <FocusLayout step="Topic">
      <div className="topic-page">
        <div className="topic-page__main">
          <header className="topic-page__header">
            <h1 className="topic-page__title">Choose your topic</h1>
            <p className="topic-page__subtitle">Let SpeakWise pick one, or bring your own.</p>
          </header>

          <SegmentedControl
            label="How to choose a topic"
            options={MODE_OPTIONS}
            value={MODE_LABELS[mode]}
            onChange={(label) =>
              dispatch({
                type: 'setMode',
                mode: (label === MODE_LABELS.own ? 'own' : 'suggest') as TopicMode,
              })
            }
            size="lg"
            fullWidth={!isDesktop}
          />

          {mode === 'suggest' ? (
            <>
              <div className="topic-page__categories" role="group" aria-label="Category">
                {topicService.getCategories().map((c) => (
                  <Chip key={c} selected={category === c} onClick={() => changeCategory(c)}>
                    {c}
                  </Chip>
                ))}
              </div>
              {suggestError && !suggesting ? (
                <div className="topic-page__error">
                  <Banner>{suggestError}</Banner>
                  <Button variant="secondary" size="sm" onClick={() => fetchSuggestion(category)}>
                    Try again
                  </Button>
                </div>
              ) : suggestedTopic ? (
                <TopicCard
                  topic={suggestedTopic}
                  loading={suggesting}
                  allRecorded={allRecorded}
                  onReroll={() => fetchSuggestion(category, suggestedTopic.id)}
                />
              ) : (
                <Skeleton height={isDesktop ? 300 : 240} radius={36} />
              )}
            </>
          ) : (
            <>
              <OwnTopicInput
                value={ownTopic}
                examples={topicService.getOwnTopicExamples()}
                onChange={setOwnTopic}
              />
              {ownError && (
                <div className="topic-page__error">
                  <Banner>{ownError.message}</Banner>
                  {ownError.suggestion && (
                    <p className="topic-page__hint">
                      Did you mean{' '}
                      <button
                        type="button"
                        className="text-link"
                        onClick={() => setOwnTopic(ownError.suggestion ?? '')}
                      >
                        {ownError.suggestion}
                      </button>
                      ?
                    </p>
                  )}
                  {ownError.relatedTopics.length > 0 && (
                    <div className="topic-page__related">
                      <span className="topic-page__hint">Or try one of these:</span>
                      {ownError.relatedTopics.map((topic) => (
                        <Chip key={topic.id} onClick={() => pickRelatedTopic(topic)}>
                          {topic.title}
                        </Chip>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          <DurationPicker
            value={durationMin}
            onChange={(d) => dispatch({ type: 'setDuration', durationMin: d })}
          />
        </div>

        <aside className="topic-page__rail">
          <SessionSummaryCard title={chosenTitle} durationMin={durationMin} summary={summary}>
            {continueButton}
          </SessionSummaryCard>
        </aside>
      </div>

      <StickyActionBar>
        <p className="topic-page__summary">{summary}</p>
        {continueButton}
      </StickyActionBar>
    </FocusLayout>
  )
}
