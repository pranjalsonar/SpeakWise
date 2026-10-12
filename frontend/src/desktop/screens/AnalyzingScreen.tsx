import { useCallback, useEffect, useRef, useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Banner } from '@/components/ui/Banner'
import { Spinner } from '@/components/ui/Spinner'
import { bridge } from '../bridge'
import type { ActiveSession } from '../DesktopApp'
import { readEnvelope, type SessionReport } from '../report'

const POLL_MS = 10000

type Stage =
  | { kind: 'uploading' }
  | { kind: 'upload-failed'; message: string }
  | { kind: 'waiting'; workerAlive: boolean; heartbeatAgeS: number | null }
  | { kind: 'processing' }
  | { kind: 'failed'; message: string }

interface Props {
  session: ActiveSession
  onReport: (report: SessionReport) => void
  onDiscard: () => void
}

export function AnalyzingScreen({ session, onReport, onDiscard }: Props) {
  const [stage, setStage] = useState<Stage>({ kind: 'uploading' })
  const [notice, setNotice] = useState<string | null>(null)
  const [elapsed, setElapsed] = useState(0)
  const [uploadAttempt, setUploadAttempt] = useState(0)
  const done = useRef(false)

  const expected = { sessionId: session.sessionId, topic: session.topic.title, materialSha256: session.materialSha256 }

  const handleEnvelope = useCallback(
    (envelope: unknown, beat?: { workerAlive: boolean; heartbeatAgeS: number | null }) => {
      const state = readEnvelope(envelope, {
        sessionId: session.sessionId,
        topic: session.topic.title,
        materialSha256: session.materialSha256,
      })
      if (state.kind === 'done') {
        done.current = true
        onReport(state.report)
      } else if (state.kind === 'pending') {
        setStage({ kind: 'waiting', workerAlive: beat?.workerAlive ?? false, heartbeatAgeS: beat?.heartbeatAgeS ?? null })
      } else if (state.kind === 'processing') {
        setStage({ kind: 'processing' })
      } else {
        // Failed analysis or a report that fails validation is never shown as results.
        setStage({ kind: 'failed', message: state.message })
      }
      return state.kind
    },
    [session, onReport],
  )

  // Upload, then poll Drive until the worker writes the report.
  useEffect(() => {
    let stopped = false
    let timer: number | undefined
    const poll = async () => {
      if (stopped || done.current) return
      const res = await bridge().poll(session.sessionId)
      if (stopped) return
      if (!res.ok) setNotice(`Could not check for the report: ${res.error} Retrying…`)
      else {
        setNotice(null)
        const kind = handleEnvelope(res.envelope, res)
        if (kind === 'failed' || kind === 'invalid' || kind === 'done') return
      }
      timer = window.setTimeout(poll, POLL_MS)
    }
    ;(async () => {
      const res = await bridge().submit(session.sessionId)
      if (stopped) return
      if (!res.ok) {
        setStage({ kind: 'upload-failed', message: res.error })
        return
      }
      await poll()
    })()
    return () => {
      stopped = true
      window.clearTimeout(timer)
    }
  }, [session.sessionId, handleEnvelope, uploadAttempt])

  useEffect(() => {
    const t = window.setInterval(() => setElapsed((s) => s + 1), 1000)
    return () => window.clearInterval(t)
  }, [])

  const importReport = async () => {
    const res = await bridge().importReport(session.sessionId)
    if (!res.ok) setNotice(res.error)
    else if (!res.canceled) handleEnvelope(res.envelope)
  }

  const mins = `${Math.floor(elapsed / 60)}:${String(elapsed % 60).padStart(2, '0')}`

  return (
    <section className="dk-panel dk-analyzing">
      <h1>Analyzing Your Speech</h1>
      <p className="dk-muted">
        {session.topic.title} · {session.durationS / 60} min · elapsed {mins}
      </p>

      {stage.kind === 'uploading' && (
        <p className="dk-status">
          <Spinner size={20} /> Uploading your recording to Google Drive…
        </p>
      )}
      {stage.kind === 'upload-failed' && (
        <>
          <Banner>Upload failed: {stage.message}</Banner>
          <Button onClick={() => { setStage({ kind: 'uploading' }); setUploadAttempt((n) => n + 1) }}>Retry upload</Button>
        </>
      )}
      {stage.kind === 'waiting' && (
        <>
          <p className="dk-status">
            <Spinner size={20} /> Uploaded. Waiting for Colab report…
          </p>
          <div className="dk-howto">
            {stage.workerAlive ? (
              <p>The Colab worker is running and will pick this session up shortly.</p>
            ) : (
              <>
                <p>
                  <strong>Manual step required:</strong> the Colab worker is not running
                  {stage.heartbeatAgeS != null ? ` (last seen ${Math.round(stage.heartbeatAgeS / 60)} min ago)` : ''}.
                  Open the notebook with the same Google account, run sections 1–4, then run
                  &ldquo;13. Desktop app worker&rdquo;. Uploading to Drive does not start Colab by itself.
                </p>
                <Button variant="secondary" onClick={() => bridge().openNotebook()}>
                  Open Colab Notebook
                </Button>
              </>
            )}
          </div>
        </>
      )}
      {stage.kind === 'processing' && (
        <p className="dk-status">
          <Spinner size={20} /> Colab is analysing your recording. This usually takes a few minutes.
        </p>
      )}
      {stage.kind === 'failed' && <Banner>Analysis failed: {stage.message}</Banner>}
      {notice && <Banner>{notice}</Banner>}

      <div className="dk-actions">
        {stage.kind !== 'uploading' && stage.kind !== 'upload-failed' && (
          <Button variant="secondary" onClick={importReport}>
            Import report file
          </Button>
        )}
        <Button variant="ghost" onClick={onDiscard}>
          Discard session
        </Button>
      </div>
      <p className="dk-fine">Session ID {expected.sessionId}</p>
    </section>
  )
}
