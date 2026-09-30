import { Shuffle } from 'lucide-react'
import { Badge, DifficultyBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import type { Topic } from '@/core/types'
import './TopicCard.css'

export function TopicCard({ topic, onReroll }: { topic: Topic; onReroll: () => void }) {
  return (
    <article className="topic-card" aria-live="polite">
      <span className="topic-card__circle" aria-hidden="true" />
      <div className="topic-card__badges">
        <Badge tone="category">{topic.category}</Badge>
        <DifficultyBadge difficulty={topic.difficulty} />
      </div>
      <h2 className="topic-card__title">{topic.title}</h2>
      <p className="topic-card__teaser">{topic.teaser}</p>
      <Button
        variant="secondary"
        size="sm"
        iconLeft={<Shuffle size={16} />}
        className="topic-card__reroll"
        onClick={onReroll}
      >
        Suggest another
      </Button>
    </article>
  )
}
