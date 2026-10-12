import { Button } from '@/components/ui/Button'
import type { Topic } from '../topics'

interface Props {
  topic: Topic
  onAnotherTopic: () => void
  onContinue: () => void
}

/** Renders topic.material verbatim (split only into paragraphs): this is the text the pipeline compares against. */
export function ReadingScreen({ topic, onAnotherTopic, onContinue }: Props) {
  const [title, ...paragraphs] = topic.material.split(/\n\s*\n/)
  return (
    <section className="dk-reading">
      <div className="dk-reading__meta">
        <span className="dk-pill">About {Math.max(1, Math.round(topic.words / 200))} min read</span>
        <Button variant="ghost" size="sm" onClick={onAnotherTopic}>
          Different topic
        </Button>
      </div>
      <article className="dk-article">
        <h1>{title}</h1>
        {paragraphs.map((p, i) =>
          p.includes('\n') || p.length > 80 ? <p key={i}>{p}</p> : <h2 key={i}>{p}</h2>,
        )}
      </article>
      <div className="dk-sticky">
        <Button size="lg" onClick={onContinue}>
          Continue to Speaking
        </Button>
      </div>
    </section>
  )
}
