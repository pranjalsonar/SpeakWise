// Static Topic-step options. Topics and reading material come from the backend: src/api/api.topics.ts.
import { categories, ownTopicExamples } from '../data/mockData'
import type { CategoryFilter } from '../types'

/** Category chips (match the backend's topic_categories). */
export const getCategories = (): CategoryFilter[] => categories
/** Example chips under "My own topic". */
export const getOwnTopicExamples = (): string[] => ownTopicExamples
