import { useCallback, useEffect, useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Banner } from '@/components/ui/Banner'
import { Spinner } from '@/components/ui/Spinner'
import { bridge, type ConnectionStatus } from '../bridge'

type CheckState = 'pass' | 'fail' | 'unknown'

function Check({ state, title, detail }: { state: CheckState; title: string; detail: string }) {
  const icon = state === 'pass' ? '✓' : state === 'fail' ? '✕' : '–'
  return (
    <li className={`dk-check dk-check--${state}`}>
      <span className="dk-check__icon" aria-hidden="true">
        {icon}
      </span>
      <div>
        <strong>{title}</strong>
        <p>{detail}</p>
      </div>
    </li>
  )
}

export function ConnectScreen({ onContinue }: { onContinue: () => void }) {
  const [status, setStatus] = useState<ConnectionStatus | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const test = useCallback(async () => {
    setBusy(true)
    setError(null)
    try {
      const res = await bridge().connectionStatus()
      if (res.ok) setStatus(res)
      else setError(res.error)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setBusy(false)
    }
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial check on mount
    void test()
  }, [test])

  const signIn = async () => {
    setBusy(true)
    setError(null)
    const res = await bridge().signIn()
    if (!res.ok) setError(res.error)
    await test()
  }

  const signOut = async () => {
    await bridge().signOut()
    await test()
  }

  const s = status
  const authState: CheckState = !s ? 'unknown' : s.authorized ? 'pass' : 'fail'
  const driveState: CheckState = !s?.authorized ? 'unknown' : s.driveReady ? 'pass' : 'fail'
  const workerState: CheckState = !s?.driveReady ? 'unknown' : s.workerAlive ? 'pass' : 'fail'
  const ready = Boolean(s?.authorized && s.driveReady && s.workerAlive)

  return (
    <section className="dk-panel dk-connect">
      <h1>Connect to the analysis workflow</h1>
      <p className="dk-muted">
        SpeakWise analyses your recording with the SpeakWise Colab notebook. Recordings travel through a
        &ldquo;SpeakWise Desktop&rdquo; folder in your Google Drive. The app can only see files it created there.
      </p>

      {s && !s.configured && <Banner>{s.configHint}</Banner>}
      {error && <Banner>{error}</Banner>}
      {s?.detail && <Banner>{s.detail}</Banner>}

      <ul className="dk-checks">
        <Check
          state={authState}
          title="Google authorization"
          detail={s?.authorized ? 'Connected with access limited to files SpeakWise creates.' : 'Not connected.'}
        />
        <Check
          state={driveState}
          title="File transfer (Google Drive)"
          detail={s?.driveReady ? 'SpeakWise Desktop folder is reachable.' : 'Needs Google authorization first.'}
        />
        <Check
          state={workerState}
          title="Inference (Colab notebook worker)"
          detail={
            s?.workerAlive
              ? `Worker is running (last seen ${s.heartbeatAgeS}s ago).`
              : s?.heartbeatAgeS != null
                ? `Worker last seen ${Math.round(s.heartbeatAgeS / 60)} min ago. Run the "Desktop app worker" section in the notebook.`
                : 'Worker has not been seen. Open the notebook, run sections 1–4, then the "Desktop app worker" section.'
          }
        />
      </ul>

      <div className="dk-actions">
        {s?.configured && !s.authorized && (
          <Button onClick={signIn} loading={busy}>
            Connect Google
          </Button>
        )}
        <Button variant="secondary" onClick={test} disabled={busy}>
          {busy ? <Spinner size={16} /> : null} Test Connection
        </Button>
        {s?.authorized && (
          <Button variant="secondary" onClick={() => bridge().openNotebook()}>
            Open Colab Notebook
          </Button>
        )}
        {s?.authorized && (
          <Button variant="ghost" onClick={signOut}>
            Disconnect
          </Button>
        )}
      </div>

      <div className="dk-ready">
        {ready ? (
          <>
            <span className="dk-pill dk-pill--ok">Ready</span>
            <Button size="lg" onClick={onContinue}>
              Continue
            </Button>
          </>
        ) : s?.driveReady ? (
          <>
            <span className="dk-pill">Not ready: Colab worker offline</span>
            <Button variant="secondary" onClick={onContinue}>
              Continue anyway (analysis waits for the worker)
            </Button>
          </>
        ) : (
          <span className="dk-pill">Not ready</span>
        )}
      </div>
    </section>
  )
}
