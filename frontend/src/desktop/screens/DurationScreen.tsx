import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import { Banner } from '@/components/ui/Banner'

const OPTIONS = [
  { seconds: 60, label: '1 minute' },
  { seconds: 180, label: '3 minutes' },
  { seconds: 300, label: '5 minutes' },
]

interface Props {
  error: string | null
  onBack: () => void
  onStart: (durationS: number) => Promise<void>
}

export function DurationScreen({ error, onBack, onStart }: Props) {
  const [selected, setSelected] = useState(180)
  const [busy, setBusy] = useState(false)
  return (
    <section className="dk-panel">
      <h1>How long will you speak?</h1>
      <p className="dk-muted">Recording stops automatically when the time is up.</p>
      {error && <Banner>{error}</Banner>}
      <div className="dk-durations" role="radiogroup" aria-label="Speaking duration">
        {OPTIONS.map((o) => (
          <button
            key={o.seconds}
            role="radio"
            aria-checked={selected === o.seconds}
            className={`dk-duration ${selected === o.seconds ? 'dk-duration--on' : ''}`}
            onClick={() => setSelected(o.seconds)}
          >
            {o.label}
          </button>
        ))}
      </div>
      <div className="dk-actions">
        <Button variant="ghost" onClick={onBack}>
          Back to reading
        </Button>
        <Button
          size="lg"
          loading={busy}
          onClick={async () => {
            setBusy(true)
            await onStart(selected)
            setBusy(false)
          }}
        >
          Set up camera
        </Button>
      </div>
    </section>
  )
}
