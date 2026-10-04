import { Avatar } from '@/components/ui/Avatar'
import { ScoreCircle } from '@/components/ui/ScoreCircle'
import type { AdminRecentSession } from '@/core/types'
import { initialsOf } from '@/core/utils'
import './AdminRecentSessions.css'

/** Latest talks across all users. Desktop: a table-like list · mobile: compact rows. */
export function AdminRecentSessions({ sessions }: { sessions: AdminRecentSession[] }) {
  return (
    <section className="admin-recent" aria-labelledby="admin-recent-title">
      <h2 id="admin-recent-title" className="admin-recent__title">
        Recent sessions
      </h2>
      <ul className="admin-recent__list">
        {sessions.map((s) => (
          <li key={`${s.user}-${s.topic}`} className="admin-recent__row">
            <Avatar initials={initialsOf(s.user)} size={36} tone="raised" />
            <span className="admin-recent__user">{s.user}</span>
            <span className="admin-recent__main">
              <span className="admin-recent__topic">{s.topic}</span>
              <span className="admin-recent__meta">
                {s.user} · {s.when}
              </span>
            </span>
            <span className="admin-recent__when">{s.when}</span>
            <span className="admin-recent__score" aria-hidden="true">
              {s.score}
            </span>
            <span className="admin-recent__score-circle">
              <ScoreCircle score={s.score} size={40} />
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}
