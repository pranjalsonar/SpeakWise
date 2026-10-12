import { useState } from 'react'
import { bridge } from './bridge'
import type { SessionReport } from './report'
import { sha256Hex } from './report'
import { AnalyzingScreen } from './screens/AnalyzingScreen'
import { ConnectScreen } from './screens/ConnectScreen'
import { DashboardScreen } from './screens/DashboardScreen'
import { DurationScreen } from './screens/DurationScreen'
import { ReadingScreen } from './screens/ReadingScreen'
import { RecordScreen } from './screens/RecordScreen'
import { WelcomeScreen } from './screens/WelcomeScreen'
import { randomTopic, type Topic } from './topics'

type Screen = 'connect' | 'welcome' | 'reading' | 'duration' | 'record' | 'analyzing' | 'dashboard'

/** The single active session, held in memory only. */
export interface ActiveSession {
  sessionId: string
  topic: Topic
  durationS: number
  materialSha256: string
}

const STEPS: { screen: Screen; label: string }[] = [
  { screen: 'reading', label: 'Read' },
  { screen: 'duration', label: 'Duration' },
  { screen: 'record', label: 'Record' },
  { screen: 'analyzing', label: 'Analyse' },
  { screen: 'dashboard', label: 'Results' },
]

export function DesktopApp() {
  // `?screen=welcome` is only set by the screenshot script (desktop/lib/shots.cjs).
  const [screen, setScreen] = useState<Screen>(() =>
    new URLSearchParams(window.location.search).get('screen') === 'welcome' ? 'welcome' : 'connect',
  )
  const [topic, setTopic] = useState<Topic | null>(null)
  const [session, setSession] = useState<ActiveSession | null>(null)
  const [report, setReport] = useState<SessionReport | null>(null)
  const [error, setError] = useState<string | null>(null)

  const reset = async () => {
    if (session) await bridge().finish(session.sessionId)
    setSession(null)
    setReport(null)
    setTopic(null)
    setError(null)
    setScreen('welcome')
  }

  const startSession = async (durationS: number) => {
    if (!topic) return
    setError(null)
    const res = await bridge().startSession({ topic: topic.title, readingMaterial: topic.material, durationS })
    if (!res.ok) {
      setError(res.error)
      return
    }
    setSession({ sessionId: res.sessionId, topic, durationS, materialSha256: await sha256Hex(topic.material) })
    setScreen('record')
  }

  const stepIndex = STEPS.findIndex((s) => s.screen === screen)

  return (
    <div className="dk">
      <header className="dk-topbar">
        <span className="dk-brand">SpeakWise</span>
        {stepIndex >= 0 && (
          <ol className="dk-steps" aria-label="Session progress">
            {STEPS.map((s, i) => (
              <li key={s.screen} className={i < stepIndex ? 'done' : i === stepIndex ? 'current' : ''}>
                {s.label}
              </li>
            ))}
          </ol>
        )}
        {screen !== 'connect' && screen !== 'record' && screen !== 'analyzing' && (
          <button className="dk-link" onClick={() => setScreen('connect')}>
            Connection
          </button>
        )}
      </header>

      <main className="dk-main">
        {screen === 'connect' && <ConnectScreen onContinue={() => setScreen(session ? 'analyzing' : 'welcome')} />}
        {screen === 'welcome' && (
          <WelcomeScreen
            onRandomTopic={() => {
              setTopic(randomTopic())
              setScreen('reading')
            }}
          />
        )}
        {screen === 'reading' && topic && (
          <ReadingScreen
            topic={topic}
            onAnotherTopic={() => setTopic(randomTopic(topic.title))}
            onContinue={() => setScreen('duration')}
          />
        )}
        {screen === 'duration' && topic && (
          <DurationScreen error={error} onBack={() => setScreen('reading')} onStart={startSession} />
        )}
        {screen === 'record' && session && (
          <RecordScreen
            session={session}
            onSubmitted={() => setScreen('analyzing')}
            onCancel={async () => {
              await bridge().finish(session.sessionId)
              setSession(null)
              setScreen('duration')
            }}
          />
        )}
        {screen === 'analyzing' && session && (
          <AnalyzingScreen
            session={session}
            onReport={(r) => {
              setReport(r)
              setScreen('dashboard')
            }}
            onDiscard={reset}
          />
        )}
        {screen === 'dashboard' && session && report && (
          <DashboardScreen report={report} onNewSession={reset} />
        )}
      </main>
    </div>
  )
}
