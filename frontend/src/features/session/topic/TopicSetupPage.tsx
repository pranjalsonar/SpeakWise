import { useEffect, useMemo } from 'react'
import { ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router'
import { ROUTES } from '@/app/routes'
import { FocusLayout } from '@/components/layout/FocusLayout'
import { StickyActionBar } from '@/components/layout/StickyActionBar'
import { Button } from '@/components/ui/Button'
import { Chip } from '@/components/ui/Chip'
import { SegmentedControl } from '@/components/ui/SegmentedControl'
import { useSession } from '@/context/SessionContext'
import type { SessionTopic, TopicMode } from '@/core/session/sessionReducer'
import { topicService } from '@/core/services'
import type { CategoryFilter } from '@/core/types'
import { pickRandomTopic } from '@/core/utils'
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
  const { mode, category, suggestedTopicId, ownTopic, durationMin } = session

  const pool = useMemo(() => topicService.filterTopics(category), [category])
  const suggested = suggestedTopicId ? topicService.getTopicById(suggestedTopicId) : undefined

  // First visit (or a stale id): pick a random suggestion.
  useEffect(() => {
    if (!suggested) {
      const topic = pickRandomTopic(pool)
      if (topic) dispatch({ type: 'suggestTopic', topicId: topic.id })
    }
  }, [suggested, pool, dispatch])

  const reroll = (fromPool = pool) => {
    const next = pickRandomTopic(fromPool, suggested?.id)
    if (next) dispatch({ type: 'suggestTopic', topicId: next.id })
  }

  const changeCategory = (next: CategoryFilter) => {
    dispatch({ type: 'setCategory', category: next })
    const nextPool = topicService.filterTopics(next)
    // Choosing a category that excludes the current topic rerolls automatically.
    if (suggested && !nextPool.some((t) => t.id === suggested.id)) reroll(nextPool)
  }

  const ownTitle = ownTopic.trim()
  const isOwn = mode === 'own' && ownTitle.length > 0
  const canContinue = mode === 'suggest' ? Boolean(suggested) : ownTitle.length > 0

  const chosen: SessionTopic | null = isOwn
    ? { id: 'own', title: ownTitle }
    : suggested
      ? {
          id: suggested.id,
          title: suggested.title,
          category: suggested.category,
          difficulty: suggested.difficulty,
        }
      : null

  const summary = `~15 min reading · ${durationMin} min speaking`

  const onContinue = () => {
    if (!canContinue || !chosen) return
    dispatch({ type: 'confirmTopic', topic: chosen })
    navigate(ROUTES.sessionPrepare)
  }

  const continueButton = (
    <Button
      size="lg"
      block
      disabled={!canContinue}
      iconRight={isDesktop ? <ArrowRight size={20} /> : undefined}
      onClick={onContinue}
    >
      Continue to reading
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
              {suggested && <TopicCard topic={suggested} onReroll={() => reroll()} />}
            </>
          ) : (
            <OwnTopicInput
              value={ownTopic}
              examples={topicService.getOwnTopicExamples()}
              onChange={(text) => dispatch({ type: 'setOwnTopic', text })}
            />
          )}

          <DurationPicker
            value={durationMin}
            onChange={(d) => dispatch({ type: 'setDuration', durationMin: d })}
          />
        </div>

        <aside className="topic-page__rail">
          <SessionSummaryCard
            title={chosen?.title ?? 'Your topic'}
            durationMin={durationMin}
            summary={summary}
          >
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
