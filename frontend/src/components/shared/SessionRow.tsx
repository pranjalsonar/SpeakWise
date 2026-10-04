import { Link } from 'react-router'
import { ROUTES } from '@/app/routes'
import { Badge } from '@/components/ui/Badge'
import { ScoreCircle } from '@/components/ui/ScoreCircle'
import type { Session } from '@/core/types'
import './SessionRow.css'

type RowVariant = 'home' | 'history'

/**
 * One session. Mobile: a raised card with a "Category · 3 min · Sep 25" meta line.
 * Desktop: a pill row in a table grid (title | category | length | date | score).
 */
export function SessionRow({
  session,
  variant = 'home',
}: {
  session: Session
  variant?: RowVariant
}) {
  const duration = `${session.durationMin} min`
  return (
    <Link to={ROUTES.feedback(session.id)} className={`session-row session-row--${variant}`}>
      <span className="session-row__main">
        <span className="session-row__title">{session.topicTitle}</span>
        <span className="session-row__meta">
          {session.category} · {duration} · {session.date}
        </span>
      </span>
      <span className="session-row__cell session-row__cell--category">
        <Badge tone="category">{session.category}</Badge>
      </span>
      <span className="session-row__cell session-row__cell--muted">{duration}</span>
      <span className="session-row__cell session-row__cell--muted">{session.date}</span>
      <span className="session-row__score">
        {session.status === 'processing' || session.score === null ? (
          <Badge tone="processing" className="session-row__processing">
            Processing
          </Badge>
        ) : (
          <ScoreCircle score={session.score} />
        )}
      </span>
    </Link>
  )
}

/** Column header for the desktop History table. */
export function SessionTableHeader({ count }: { count: number }) {
  return (
    <div className="session-row session-row--header session-row--history" aria-hidden="true">
      <span>
        Topic · {count} {count === 1 ? 'session' : 'sessions'}
      </span>
      <span>Category</span>
      <span>Length</span>
      <span>Date</span>
      <span className="session-row__score">Score</span>
    </div>
  )
}
