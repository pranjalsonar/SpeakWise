import { useCallback, useEffect, useState, type UIEvent } from 'react'
import { Pen } from 'lucide-react'
import { useNavigate } from 'react-router'
import * as topicsApi from '@/api/api.topics'
import { ROUTES } from '@/app/routes'
import { FocusLayout } from '@/components/layout/FocusLayout'
import { StickyActionBar } from '@/components/layout/StickyActionBar'
import { TopicBadges } from '@/components/shared/TopicBadges'
import { Banner } from '@/components/ui/Banner'
import { Button } from '@/components/ui/Button'
import { Chip } from '@/components/ui/Chip'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { ProgressBar } from '@/components/ui/ProgressBar'
import { Skeleton } from '@/components/ui/Skeleton'
import { useSession } from '@/context/SessionContext'
import { useAsync } from '@/core/hooks/useAsync'
import { useInterval } from '@/core/hooks/useInterval'
import { PREP_SECONDS, READY_THRESHOLD_PCT } from '@/core/session/sessionReducer'
import { formatNumber } from '@/core/utils'
import { useStartSession } from '@/hooks/useStartSession'
import { Article } from './Article'
import { NotesSheet } from './NotesSheet'
import { PrepRail } from './PrepRail'
import { TextSizeControl } from './TextSizeControl'
import './PreparePage.css'

export function PreparePage() {
  const navigate = useNavigate()
  const startSession = useStartSession()
  const { session, dispatch } = useSession()
  const topic = session.topic!
  const [attempt, setAttempt] = useState(0)
  const { data: material, error } = useAsync(
    () => topicsApi.getReadingMaterial(topic.id),
    [topic.id, attempt],
  )
  const [prepSecondsLeft, setPrepSecondsLeft] = useState(PREP_SECONDS)
  const [dialog, setDialog] = useState<'notes' | 'early' | null>(null)

  // Remember which version was read (saved with the talk) and its key points (Record cue card).
  useEffect(() => {
    if (material && material.id !== session.readingMaterialId) {
      dispatch({ type: 'setReadingMaterial', id: material.id, keyPoints: material.keyPoints })
    }
  }, [material, session.readingMaterialId, dispatch])

  // Advisory 15:00 reading timer (it never blocks the user).
  useInterval(
    () => setPrepSecondsLeft((s) => Math.max(0, s - 1)),
    prepSecondsLeft > 0 ? 1000 : null,
  )

  const onScroll = useCallback(
    (event: UIEvent<HTMLDivElement>) => {
      const el = event.currentTarget
      const max = el.scrollHeight - el.clientHeight
      const pct = max <= 0 ? 100 : Math.min(100, (el.scrollTop / max) * 100)
      if (Math.round(pct) > session.readPct) dispatch({ type: 'setReadPct', pct })
    },
    [dispatch, session.readPct],
  )

  const setTextStep = (step: number) => dispatch({ type: 'setTextStep', step })
  const setNotes = (notes: string) => dispatch({ type: 'setNotes', notes })

  const goRecord = () => {
    dispatch({ type: 'goToRecord' })
    navigate(ROUTES.sessionRecord)
  }
  const onReady = () => (session.readPct < READY_THRESHOLD_PCT ? setDialog('early') : goRecord())

  return (
    <FocusLayout
      step="Prepare"
      bordered={false}
      mobileSegments={false}
      fitViewport
      mobileActions={
        <TextSizeControl step={session.textStep} onChange={setTextStep} tone="surface" />
      }
      belowTopBar={
        <ProgressBar value={session.readPct} label="Reading progress" height={4} square />
      }
    >
      <div className="prepare-page">
        <div className="prepare-page__scroll" onScroll={onScroll}>
          <article className="prepare-page__article">
            <TopicBadges topic={topic} tone="surface" />
            <h1 className="prepare-page__title">{topic.title}</h1>
            {material && (
              <p className="prepare-page__meta">
                ≈ {material.readMinutes} min read · {formatNumber(material.wordCount)} words
              </p>
            )}
            {material?.isRepeat && (
              <div className="prepare-page__notice">
                <Banner>
                  You've already practised every version of this topic, so here's the one you read
                  longest ago.
                </Banner>
                {material.relatedTopics.length > 0 && (
                  <div className="prepare-page__related">
                    <span>Want something new? Try:</span>
                    {material.relatedTopics.map((related) => (
                      <Chip key={related.id} onClick={() => startSession({ topic: related })}>
                        {related.title}
                      </Chip>
                    ))}
                  </div>
                )}
              </div>
            )}
            {material ? (
              <>
                <Article
                  sections={material.sections}
                  keyPoints={material.keyPoints}
                  textStep={session.textStep}
                />
                <footer className="prepare-page__sources">
                  <p className="prepare-page__sources-title">Sources</p>
                  <ul className="prepare-page__sources-list">
                    {material.sources.map((source) => (
                      <li key={source.url}>
                        <a href={source.url} target="_blank" rel="noreferrer" className="text-link">
                          {source.title}
                        </a>
                      </li>
                    ))}
                  </ul>
                  <p className="prepare-page__attribution">
                    {material.attribution}{' '}
                    <a
                      href={material.licenseUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="text-link"
                    >
                      License
                    </a>
                  </p>
                </footer>
              </>
            ) : error ? (
              <div className="prepare-page__notice">
                <Banner>Couldn't load the reading material. {error.message}</Banner>
                <div className="prepare-page__related">
                  <Button variant="secondary" size="sm" onClick={() => setAttempt((a) => a + 1)}>
                    Try again
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => navigate(ROUTES.sessionTopic)}>
                    Choose another topic
                  </Button>
                </div>
              </div>
            ) : (
              <div className="prepare-page__loading">
                <Skeleton height={28} radius={14} />
                <Skeleton height={180} radius={24} />
                <Skeleton height={140} radius={24} />
              </div>
            )}
          </article>
        </div>

        <PrepRail
          secondsLeft={prepSecondsLeft}
          readPct={session.readPct}
          keyPoints={material?.keyPoints ?? []}
          textStep={session.textStep}
          onTextStep={setTextStep}
          notes={session.notes}
          onNotes={setNotes}
          onReady={onReady}
        />

        <button
          type="button"
          className="prepare-page__notes-fab"
          onClick={() => setDialog('notes')}
        >
          <Pen size={16} aria-hidden="true" />
          Notes
        </button>
      </div>

      <StickyActionBar>
        <p className="prepare-page__read">{session.readPct}% read</p>
        <Button size="lg" block onClick={onReady}>
          I'm ready, start talk
        </Button>
      </StickyActionBar>

      <NotesSheet
        open={dialog === 'notes'}
        notes={session.notes}
        onChange={setNotes}
        onClose={() => setDialog(null)}
      />

      <ConfirmDialog
        open={dialog === 'early'}
        title={`You've read ${session.readPct}%. Start anyway?`}
        body="Reading is optional, but covering the key points helps your relevance score."
        confirmLabel="Start anyway"
        cancelLabel="Keep reading"
        onConfirm={goRecord}
        onCancel={() => setDialog(null)}
      />
    </FocusLayout>
  )
}
