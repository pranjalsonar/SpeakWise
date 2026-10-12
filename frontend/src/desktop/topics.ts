// Prepared practice passages (no content-generation service is configured for the desktop demo).
// The first line of each file is its title and doubles as the topic sent to the pipeline.
import climate from './topics/climate_change.txt?raw'
import renewable from './topics/renewable_energy.txt?raw'
import sleep from './topics/sleep_and_learning.txt?raw'
import social from './topics/social_media.txt?raw'

export interface Topic {
  title: string
  /** Exactly what the reading screen displays and what the pipeline receives. */
  material: string
  words: number
}

function toTopic(raw: string): Topic {
  const material = raw.replace(/\r\n/g, '\n').trim()
  const title = material.split('\n', 1)[0]!.trim()
  return { title, material, words: material.split(/\s+/).length }
}

export const TOPICS: Topic[] = [climate, renewable, sleep, social].map(toTopic)

export function randomTopic(exclude?: string): Topic {
  const pool = TOPICS.filter((t) => t.title !== exclude)
  return pool[Math.floor(Math.random() * pool.length)]!
}
