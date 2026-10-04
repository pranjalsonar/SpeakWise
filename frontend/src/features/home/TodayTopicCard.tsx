import { Badge, DifficultyBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import type { Topic } from '@/core/types'
import './TodayTopicCard.css'

export function TodayTopicCard({ topic, onUse }: { topic: Topic; onUse: () => void }) {
  return (
    <section className="today-card" aria-labelledby="today-card-title">
      <p className="overline today-card__label">Today's topic</p>
      <h2 id="today-card-title" className="today-card__title">
        {topic.title}
      </h2>
      <div className="today-card__badges">
        <Badge tone="category">{topic.category}</Badge>
        <DifficultyBadge difficulty={topic.difficulty} />
      </div>
      <Button variant="secondary" size="sm" className="today-card__use" onClick={onUse}>
        Use this topic
      </Button>
    </section>
  )
}
