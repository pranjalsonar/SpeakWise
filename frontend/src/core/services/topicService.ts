import {
  article,
  categories,
  keyPoints,
  ownTopicExamples,
  todaysTopicId,
  topics,
} from '../data/mockData'
import type { CategoryFilter, ReadingMaterial, Topic } from '../types'
import { sleep } from '../utils'

// Synchronous getters for static catalogue data (instant in the mock; cached lists from the API later).
export const getTopics = (): Topic[] => topics
export const getCategories = (): CategoryFilter[] => categories
export const getOwnTopicExamples = (): string[] => ownTopicExamples
export const getTodaysTopic = (): Topic => topics.find((t) => t.id === todaysTopicId) ?? topics[0]!
export const getTopicById = (id: string): Topic | undefined => topics.find((t) => t.id === id)

export const filterTopics = (category: CategoryFilter): Topic[] =>
  category === 'All' ? topics : topics.filter((t) => t.category === category)

/** The mock has one article. Every topic reuses it until the backend generates real material. */
export async function getReadingMaterial(topicId: string): Promise<ReadingMaterial> {
  await sleep(300)
  return {
    topicId,
    readMinutes: article.readMinutes,
    wordCount: article.wordCount,
    keyPoints,
    sections: article.sections,
  }
}

/** Key points are needed synchronously by the record screen's cue card. */
export const getKeyPoints = (): string[] => keyPoints
