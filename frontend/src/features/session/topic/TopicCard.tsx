import { Shuffle } from 'lucide-react'
import { Badge, DifficultyBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import type { Topic } from '@/core/types'
import './TopicCard.css'

interface TopicCardProps {
  topic: Topic
  onReroll: () => void
  /** A new suggestion is loading. */
  loading?: boolean
  /** Every topic matching the filter was already recorded; this one is a repeat. */
  allRecorded?: boolean
}

export function TopicCard({
  topic,
  onReroll,
  loading = false,
  allRecorded = false,
}: TopicCardProps) {
  return (
    <article className="topic-card" aria-live="polite" aria-busy={loading}>
      <span className="topic-card__circle" aria-hidden="true" />
      <div className="topic-card__badges">
        <Badge tone="category">{topic.category}</Badge>
        <DifficultyBadge difficulty={topic.difficulty} />
      </div>
      <h2 className="topic-card__title">{topic.title}</h2>
      <p className="topic-card__teaser">{topic.teaser}</p>
      {allRecorded && (
        <p className="topic-card__note">
          You've practised every topic here, so this one comes round again.
        </p>
      )}
      <Button
        variant="secondary"
        size="sm"
        iconLeft={<Shuffle size={16} />}
        className="topic-card__reroll"
        loading={loading}
        onClick={onReroll}
      >
        Suggest another
      </Button>
    </article>
  )
}
