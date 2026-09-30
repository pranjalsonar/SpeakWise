import { useId, useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import type { TranscriptSegment } from '@/core/types'
import './Transcript.css'

/** Collapsible transcript with filler words highlighted. */
export function Transcript({ segments }: { segments: TranscriptSegment[] }) {
  const [open, setOpen] = useState(false)
  const bodyId = useId()
  const fillerCount = segments.filter((s) => s.isFiller).length

  return (
    <section className="transcript">
      <button
        type="button"
        className="transcript__toggle"
        aria-expanded={open}
        aria-controls={bodyId}
        onClick={() => setOpen((o) => !o)}
      >
        Transcript
        <span className="transcript__hint">
          <span className="transcript__count">{fillerCount} filler words highlighted</span>
          {open ? (
            <ChevronUp size={20} aria-hidden="true" />
          ) : (
            <ChevronDown size={20} aria-hidden="true" />
          )}
        </span>
      </button>
      {open && (
        <p id={bodyId} className="transcript__body">
          {segments.map((segment, i) =>
            segment.isFiller ? (
              <mark key={i} className="transcript__filler">
                {segment.text}
              </mark>
            ) : (
              <span key={i}>{segment.text}</span>
            ),
          )}
        </p>
      )}
    </section>
  )
}
