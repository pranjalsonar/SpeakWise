import { Button } from '@/components/ui/Button'
import './StartSessionCard.css'

interface StartSessionCardProps {
  onStart: () => void
  onSuggest: () => void
}

export function StartSessionCard({ onStart, onSuggest }: StartSessionCardProps) {
  return (
    <section className="start-card" aria-labelledby="start-card-title">
      <span className="start-card__circle" aria-hidden="true" />
      <h2 id="start-card-title" className="start-card__title">
        Start a talk session
      </h2>
      <p className="start-card__text">
        Pick a topic, read for 15 minutes, then speak on camera for 1 to 5 minutes.
        <span className="start-card__text-extra"> Feedback arrives in under a minute.</span>
      </p>
      <div className="start-card__actions">
        <Button variant="light" size="lg" className="start-card__start" onClick={onStart}>
          Start session
        </Button>
        <button type="button" className="start-card__suggest" onClick={onSuggest}>
          Suggest me a topic
        </button>
      </div>
    </section>
  )
}
