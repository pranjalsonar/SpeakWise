import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router'
import { ROUTES } from '@/app/routes'
import { FocusLayout } from '@/components/layout/FocusLayout'
import { Button } from '@/components/ui/Button'
import { ProgressBar } from '@/components/ui/ProgressBar'
import { useSession } from '@/context/SessionContext'
import { useInterval } from '@/core/hooks/useInterval'
import { sessionService } from '@/core/services'
import { BreathingLoader } from './BreathingLoader'
import { StepChecklist, type StepState } from './StepChecklist'
import './ProcessingPage.css'

const { PROCESSING, LATEST_REPORT_ID } = sessionService

/**
 * Mock upload (+4% every 200ms) then one checklist step per second, then Feedback.
 * With the real backend: upload the recording, then poll the session status.
 */
export function ProcessingPage() {
  const navigate = useNavigate()
  const { dispatch } = useSession()
  const steps = sessionService.getProcessingSteps()
  const [uploadPct, setUploadPct] = useState(0)
  const [doneSteps, setDoneSteps] = useState(0) // steps after "Uploaded"
  const uploaded = uploadPct >= 100
  const analysisSteps = steps.length - 1
  const finished = uploaded && doneSteps >= analysisSteps

  useInterval(
    () => setUploadPct((p) => Math.min(100, p + PROCESSING.uploadStepPct)),
    uploaded ? null : PROCESSING.uploadTickMs,
  )
  useInterval(() => setDoneSteps((n) => n + 1), uploaded && !finished ? PROCESSING.stepMs : null)

  useEffect(() => {
    if (!finished) return
    dispatch({ type: 'processed', sessionId: LATEST_REPORT_ID })
    navigate(ROUTES.feedback(LATEST_REPORT_ID), { replace: true })
  }, [finished, dispatch, navigate])

  const states: StepState[] = steps.map((_, i) => {
    if (i === 0) return uploaded ? 'done' : 'active'
    if (!uploaded) return 'todo'
    const index = i - 1
    return index < doneSteps ? 'done' : index === doneSteps ? 'active' : 'todo'
  })

  return (
    <FocusLayout step="Review">
      <main className="processing-page">
        <div className="processing-page__content">
          <BreathingLoader />
          <h1 className="processing-page__title" aria-live="polite">
            {uploaded ? 'Analysing your talk' : `Uploading… ${uploadPct}%`}
          </h1>
          <ProgressBar value={uploadPct} label="Upload progress" className="processing-page__bar" />
          <StepChecklist steps={steps} states={states} />
          <p className="processing-page__note">
            This usually takes under a minute. You can leave this page. We'll notify you.
          </p>
          <Button variant="secondary" onClick={() => navigate(ROUTES.home)}>
            Back to home
          </Button>
        </div>
      </main>
    </FocusLayout>
  )
}
