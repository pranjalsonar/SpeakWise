import { Shuffle } from 'lucide-react'
import { Button } from '@/components/ui/Button'

export function WelcomeScreen({ onRandomTopic }: { onRandomTopic: () => void }) {
  return (
    <section className="dk-hero">
      <h1>Practise speaking with real feedback.</h1>
      <p className="dk-muted">
        Read about a topic, speak about it on camera, and get an analysis of your delivery, body language and
        content.
      </p>
      <Button size="xl" iconLeft={<Shuffle size={20} />} onClick={onRandomTopic}>
        Random Topic
      </Button>
    </section>
  )
}
