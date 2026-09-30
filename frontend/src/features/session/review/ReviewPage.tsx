import { useState } from 'react'
import { Download, RotateCcw } from 'lucide-react'
import { Navigate, useNavigate } from 'react-router'
import { ROUTES } from '@/app/routes'
import { FocusLayout } from '@/components/layout/FocusLayout'
import { StickyActionBar } from '@/components/layout/StickyActionBar'
import { Button } from '@/components/ui/Button'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { useSession } from '@/context/SessionContext'
import { formatClock, formatLongDate } from '@/core/utils'
import { VideoPlayer } from './VideoPlayer'
import './ReviewPage.css'

export function ReviewPage() {
  const { session } = useSession()
  // The recording lives in memory only; after a reload there is nothing to review.
  if (!session.recording || !session.topic) return <Navigate to={ROUTES.sessionRecord} replace />
  return <ReviewContent />
}

function ReviewContent() {
  const navigate = useNavigate()
  const { session, dispatch } = useSession()
  const [confirmOpen, setConfirmOpen] = useState(false)
  const topic = session.topic!
  const recording = session.recording!
  const spoken = formatClock(recording.durationSec)
  const today = formatLongDate(new Date())
  const extension = recording.mimeType.includes('mp4') ? 'mp4' : 'webm'

  const submit = () => {
    dispatch({ type: 'submit' })
    navigate(ROUTES.sessionProcessing)
  }

  const rerecord = () => {
    setConfirmOpen(false)
    dispatch({ type: 'discardRecording' })
    navigate(ROUTES.sessionRecord)
  }

  const reRecordButton = (
    <Button
      variant="secondary"
      iconLeft={<RotateCcw size={16} />}
      block
      onClick={() => setConfirmOpen(true)}
    >
      Re-record
    </Button>
  )

  const downloadButton = recording.url ? (
    <a
      className="review-page__download"
      href={recording.url}
      download={`speakwise-talk.${extension}`}
    >
      <Download size={16} aria-hidden="true" />
      Download
    </a>
  ) : (
    <Button variant="ghost" iconLeft={<Download size={16} />} block disabled>
      Download
    </Button>
  )

  return (
    <FocusLayout step="Review">
      <div className="review-page">
        <div className="review-page__player">
          <VideoPlayer src={recording.url} durationSec={recording.durationSec} />
        </div>

        <aside className="review-page__panel">
          <h1 className="review-page__title">Review your talk</h1>
          <div className="review-page__summary">
            <h2 className="review-page__topic">{topic.title}</h2>
            <p className="review-page__meta">
              {spoken} spoken · {today}
            </p>
            <dl className="review-page__facts">
              <div>
                <dt>Duration</dt>
                <dd>{spoken}</dd>
              </div>
              <div>
                <dt>Date</dt>
                <dd>{today}</dd>
              </div>
            </dl>
          </div>
          <div className="review-page__actions">
            <Button size="lg" block onClick={submit}>
              Submit for feedback
            </Button>
            {reRecordButton}
            {downloadButton}
          </div>
        </aside>
      </div>

      <StickyActionBar>
        <Button size="lg" block onClick={submit}>
          Submit for feedback
        </Button>
        <div className="review-page__row">
          {reRecordButton}
          {downloadButton}
        </div>
      </StickyActionBar>

      <ConfirmDialog
        open={confirmOpen}
        title="Re-record?"
        body="This will discard your current recording."
        confirmLabel="Discard and re-record"
        cancelLabel="Cancel"
        danger
        onConfirm={rerecord}
        onCancel={() => setConfirmOpen(false)}
      />
    </FocusLayout>
  )
}
