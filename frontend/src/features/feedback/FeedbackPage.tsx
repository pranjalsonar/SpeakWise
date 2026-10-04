import { ArrowLeft, ArrowRight, Check } from 'lucide-react'
import { useNavigate, useParams } from 'react-router'
import { ROUTES } from '@/app/routes'
import { AppShell } from '@/components/layout/AppShell'
import { Button } from '@/components/ui/Button'
import { IconButton } from '@/components/ui/IconButton'
import { Skeleton } from '@/components/ui/Skeleton'
import { usePreferences } from '@/context/PreferencesContext'
import { useSession } from '@/context/SessionContext'
import { useAsync } from '@/core/hooks/useAsync'
import type { SessionTopic } from '@/core/session/sessionReducer'
import { sessionService, topicService } from '@/core/services'
import type { DurationMin, FeedbackReport } from '@/core/types'
import { formatClock, formatLongDate } from '@/core/utils'
import { useStartSession } from '@/hooks/useStartSession'
import { InsightList } from './InsightList'
import { MetricCard } from './MetricCard'
import { ScoreRing } from './ScoreRing'
import { Transcript } from './Transcript'
import './FeedbackPage.css'

export function FeedbackPage() {
  const { id = '' } = useParams()
  const navigate = useNavigate()
  const { session, dispatch } = useSession()
  const { preferences } = usePreferences()
  const startSession = useStartSession()
  const { data } = useAsync(() => sessionService.getFeedback(id), [id])

  // The report for the talk just recorded carries the live session's topic and length.
  const isLatest = id === sessionService.LATEST_REPORT_ID
  const report: FeedbackReport | undefined =
    data && isLatest && session.topic
      ? {
          ...data,
          topicTitle: session.topic.title,
          date: formatLongDate(new Date()),
          duration: formatClock(session.recording?.durationSec ?? session.durationMin * 60),
        }
      : data

  const practiceAgain = () => {
    if (!report) return
    if (isLatest && session.topic) {
      dispatch({ type: 'practiceAgain' })
    } else {
      const known = topicService.getTopics().find((t) => t.title === report.topicTitle)
      const topic: SessionTopic = known
        ? {
            id: known.id,
            title: known.title,
            category: known.category,
            difficulty: known.difficulty,
          }
        : { id: 'own', title: report.topicTitle }
      const minutes = Number.parseInt(report.duration, 10)
      const durationMin = ([1, 3, 5] as const).includes(minutes as DurationMin)
        ? (minutes as DurationMin)
        : preferences.defaultDurationMin
      dispatch({ type: 'start', durationMin })
      dispatch({ type: 'confirmTopic', topic })
    }
    navigate(ROUTES.sessionPrepare)
  }

  const actions = (
    <>
      <Button size="lg" className="feedback-page__primary" onClick={practiceAgain}>
        Practice again
      </Button>
      <Button variant="secondary" onClick={() => startSession({ random: true })}>
        New topic
      </Button>
      <Button variant="ghost" size="sm" onClick={() => navigate(ROUTES.home)}>
        Back to home
      </Button>
    </>
  )

  const mobileHeader = (
    <header className="feedback-page__topbar">
      <IconButton
        aria-label="Back to home"
        icon={<ArrowLeft size={20} />}
        onClick={() => navigate(ROUTES.home)}
      />
      <span className="feedback-page__topbar-title">Feedback</span>
    </header>
  )

  return (
    <AppShell mobileHeader={mobileHeader} hideTabBar activePath={ROUTES.history}>
      {!report ? (
        <div className="feedback-page__loading">
          <Skeleton height={80} radius={24} />
          <Skeleton height={320} radius={40} />
        </div>
      ) : (
        <div className="feedback-page">
          <header className="feedback-page__header">
            <div className="feedback-page__heading">
              <p className="overline">Feedback report</p>
              <h1 className="feedback-page__title">{report.topicTitle}</h1>
              <p className="feedback-page__meta">
                {report.date} · {report.duration} spoken
              </p>
            </div>
            <div className="feedback-page__actions feedback-page__actions--top">{actions}</div>
          </header>

          <div className="feedback-page__grid">
            <div className="feedback-page__left">
              <section className="feedback-page__score" aria-label="Overall score">
                <ScoreRing score={report.overallScore} />
                <p className="feedback-page__verdict">{report.verdict}</p>
                <p className="feedback-page__score-meta">
                  {report.topicTitle} · {report.date.replace(/, \d{4}$/, '')} · {report.duration}
                </p>
              </section>
              <div className="feedback-page__well">
                <InsightList
                  title="What went well"
                  items={report.wentWell}
                  tone="well"
                  icon={<Check size={16} />}
                />
              </div>
              <div className="feedback-page__improve">
                <InsightList
                  title="What to improve"
                  items={report.toImprove}
                  tone="improve"
                  icon={<ArrowRight size={16} />}
                />
              </div>
            </div>

            <div className="feedback-page__right">
              <section className="feedback-page__metrics" aria-label="Scores by skill">
                {report.metrics.map((metric) => (
                  <MetricCard key={metric.key} metric={metric} />
                ))}
              </section>
              <div className="feedback-page__transcript">
                <Transcript segments={report.transcript} />
              </div>
            </div>
          </div>

          <div className="feedback-page__actions feedback-page__actions--bottom">{actions}</div>
        </div>
      )}
    </AppShell>
  )
}
