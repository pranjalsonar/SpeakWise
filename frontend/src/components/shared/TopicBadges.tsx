import { Badge, DifficultyBadge } from '@/components/ui/Badge'
import type { SessionTopic } from '@/core/session/sessionReducer'
import './TopicBadges.css'

/** Category + difficulty, or "Custom · Your topic" for topics the user typed. */
export function TopicBadges({
  topic,
  tone = 'raised',
}: {
  topic: SessionTopic
  tone?: 'raised' | 'surface'
}) {
  return (
    <div className={`topic-badges topic-badges--${tone}`}>
      <Badge tone="category" className="topic-badges__category">
        {topic.category ?? 'Custom'}
      </Badge>
      {topic.difficulty ? (
        <DifficultyBadge difficulty={topic.difficulty} />
      ) : (
        <Badge tone="custom">Your topic</Badge>
      )}
    </div>
  )
}
