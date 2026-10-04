import type { ReactNode } from 'react'
import { BookOpen, Mic, Video } from 'lucide-react'
import type { DurationMin } from '@/core/types'
import './SessionSummaryCard.css'

interface SessionSummaryCardProps {
  title: string
  durationMin: DurationMin
  summary: string
  children: ReactNode
}

/** Desktop right-rail card: what the session involves, plus the primary action. */
export function SessionSummaryCard({
  title,
  durationMin,
  summary,
  children,
}: SessionSummaryCardProps) {
  return (
    <section className="summary-card" aria-labelledby="summary-card-title">
      <p className="overline">Your session</p>
      <h2 id="summary-card-title" className="summary-card__title">
        {title}
      </h2>
      <dl className="summary-card__facts">
        <div className="summary-card__fact">
          <BookOpen size={20} aria-hidden="true" />
          <dt>Reading</dt>
          <dd>~15 min</dd>
        </div>
        <div className="summary-card__fact">
          <Mic size={20} aria-hidden="true" />
          <dt>Speaking</dt>
          <dd>{durationMin} min</dd>
        </div>
        <div className="summary-card__fact">
          <Video size={20} aria-hidden="true" />
          <dt>Front camera</dt>
          <dd>Required</dd>
        </div>
      </dl>
      <p className="summary-card__summary">{summary}</p>
      {children}
    </section>
  )
}
