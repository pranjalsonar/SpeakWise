// Topics + reading material API. Used by TopicSetupPage, PreparePage and HomePage.
import type { SessionTopic } from '@/core/session/sessionReducer'
import type { Category, CategoryFilter, Difficulty, ReadingMaterial, Topic } from '@/core/types'
import { ApiError, apiGet, apiPost } from './client'
import { ENDPOINTS } from './endpoints'

// ---- Backend response shapes (snake_case, as the API returns them) ----
interface TopicDto {
  id: number
  title: string
  teaser: string | null
  category: string | null
  difficulty: Difficulty
  source: 'curated' | 'custom'
  recorded: boolean
}

interface ReadingMaterialDto {
  id: number
  topic: TopicDto
  version: number
  is_repeat: boolean
  lang: string
  summary: string
  key_points: string[]
  sections: { heading: string; paragraphs: string[] }[]
  word_count: number
  read_minutes: number
  sources: { title: string; url: string; lang: string; revision_id: number }[]
  license: string
  license_url: string
  attribution: string
  related_topics: TopicDto[]
}

// ---- Mapping ----

/** A curated topic for cards (Topic Setup, Home). Curated topics always have a category. */
export function toTopic(dto: TopicDto): Topic {
  return {
    id: String(dto.id),
    title: dto.title,
    category: (dto.category ?? 'Technology') as Category,
    difficulty: dto.difficulty,
    teaser: dto.teaser ?? '',
    recorded: dto.recorded,
  }
}

/** The topic a session runs on. Custom topics show as "Custom · Your topic" (no badges). */
export function toSessionTopic(topic: TopicDto | Topic): SessionTopic {
  const isCustom = 'source' in topic && topic.source === 'custom'
  return {
    id: String(topic.id),
    title: topic.title,
    category: isCustom ? undefined : ((topic.category ?? undefined) as Category | undefined),
    difficulty: isCustom ? undefined : topic.difficulty,
  }
}

function toReadingMaterial(dto: ReadingMaterialDto): ReadingMaterial {
  return {
    id: dto.id,
    topicId: String(dto.topic.id),
    version: dto.version,
    isRepeat: dto.is_repeat,
    readMinutes: dto.read_minutes,
    wordCount: dto.word_count,
    summary: dto.summary,
    keyPoints: dto.key_points,
    // The Key points box sits after the opening section.
    sections: dto.sections.map((section, i) => ({ ...section, showKeyPoints: i === 0 })),
    sources: dto.sources.map(({ title, url }) => ({ title, url })),
    attribution: dto.attribution,
    licenseUrl: dto.license_url,
    relatedTopics: dto.related_topics.map(toTopic),
  }
}

// ---- API calls ----

/** A random curated topic the user hasn't recorded. `allRecorded`: every match was recorded. */
export async function suggestTopic(
  options: { category?: CategoryFilter; excludeId?: string } = {},
): Promise<{ topic: Topic; allRecorded: boolean }> {
  const params = new URLSearchParams()
  if (options.category && options.category !== 'All') params.set('category', options.category)
  if (options.excludeId) params.set('exclude_id', options.excludeId)
  const query = params.size ? `?${params}` : ''
  const data = await apiGet<{ topic: TopicDto; all_recorded: boolean }>(
    `${ENDPOINTS.topics.suggest}${query}`,
  )
  return { topic: toTopic(data.topic), allRecorded: data.all_recorded }
}

/** Today's topic (same for everyone). */
export async function getDailyTopic(): Promise<{ date: string; topic: Topic }> {
  const data = await apiGet<{ date: string; topic: TopicDto }>(ENDPOINTS.topics.daily)
  return { date: data.date, topic: toTopic(data.topic) }
}

/**
 * Turn typed text into a topic backed by Wikipedia. Throws ApiError:
 * 422 (nothing found; see customTopicError), 429 (hourly limit), 503 (Wikipedia down).
 */
export async function createCustomTopic(
  text: string,
): Promise<{ topic: SessionTopic; created: boolean }> {
  const data = await apiPost<{ topic: TopicDto; created: boolean }>(ENDPOINTS.topics.custom, {
    text: text.trim(),
  })
  return { topic: toSessionTopic(data.topic), created: data.created }
}

export interface CustomTopicError {
  message: string
  /** Wikipedia's "did you mean" spelling, when it has one. */
  suggestion: string | null
  /** Curated topics with similar words. */
  relatedTopics: Topic[]
}

/** User-facing details for a failed createCustomTopic call. */
export function customTopicError(error: unknown): CustomTopicError {
  if (!(error instanceof ApiError)) {
    return {
      message: 'Something went wrong. Please try again.',
      suggestion: null,
      relatedTopics: [],
    }
  }
  const body = (error.body ?? {}) as { suggestion?: string | null; related_topics?: TopicDto[] }
  const message =
    error.status === 422 && Array.isArray(error.detail)
      ? 'Describe the topic in 3–120 characters.'
      : error.message
  return {
    message,
    suggestion: body.suggestion ?? null,
    relatedTopics: (body.related_topics ?? []).map(toTopic),
  }
}

/** Reading material for the Prepare step: a version this user hasn't recorded a talk with. */
export async function getReadingMaterial(topicId: string): Promise<ReadingMaterial> {
  return toReadingMaterial(
    await apiGet<ReadingMaterialDto>(ENDPOINTS.topics.readingMaterial(topicId)),
  )
}
