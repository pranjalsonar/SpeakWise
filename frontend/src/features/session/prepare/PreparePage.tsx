import { useCallback, useState, type UIEvent } from 'react'
import { Pen } from 'lucide-react'
import { useNavigate } from 'react-router'
import { ROUTES } from '@/app/routes'
import { FocusLayout } from '@/components/layout/FocusLayout'
import { StickyActionBar } from '@/components/layout/StickyActionBar'
import { TopicBadges } from '@/components/shared/TopicBadges'
import { Button } from '@/components/ui/Button'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { ProgressBar } from '@/components/ui/ProgressBar'
import { Skeleton } from '@/components/ui/Skeleton'
import { useSession } from '@/context/SessionContext'
import { useAsync } from '@/core/hooks/useAsync'
import { useInterval } from '@/core/hooks/useInterval'
import { PREP_SECONDS, READY_THRESHOLD_PCT } from '@/core/session/sessionReducer'
import { topicService } from '@/core/services'
import { formatNumber } from '@/core/utils'
import { Article } from './Article'
import { NotesSheet } from './NotesSheet'
import { PrepRail } from './PrepRail'
import { TextSizeControl } from './TextSizeControl'
import './PreparePage.css'

export function PreparePage() {
  const navigate = useNavigate()
  const { session, dispatch } = useSession()
  const topic = session.topic!
  const { data: material } = useAsync(() => topicService.getReadingMaterial(topic.id), [topic.id])
  const [prepSecondsLeft, setPrepSecondsLeft] = useState(PREP_SECONDS)
  const [dialog, setDialog] = useState<'notes' | 'early' | null>(null)

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
            <p className="prepare-page__meta">
              ≈ {material?.readMinutes ?? 15} min read · {formatNumber(material?.wordCount ?? 2800)}{' '}
              words
            </p>
            {material ? (
              <Article
                sections={material.sections}
                keyPoints={material.keyPoints}
                textStep={session.textStep}
              />
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
