import type { Session } from '@/core/types'

export const HISTORY_FILTERS = ['All', 'Completed', 'In progress'] as const
export const HISTORY_SORTS = ['Date', 'Score'] as const

export type HistoryFilter = (typeof HISTORY_FILTERS)[number]
export type HistorySort = (typeof HISTORY_SORTS)[number]

/**
 * Search by title or category, filter by status ("In progress" = processing),
 * sort by date (as returned, newest first) or score (highest first, processing last).
 */
export function applyHistoryFilters(
  sessions: Session[],
  query: string,
  filter: HistoryFilter,
  sort: HistorySort,
): Session[] {
  const q = query.trim().toLowerCase()
  const matches = sessions.filter((s) => {
    const inQuery =
      !q || s.topicTitle.toLowerCase().includes(q) || s.category.toLowerCase().includes(q)
    const inFilter =
      filter === 'All' ||
      (filter === 'Completed' && s.status === 'completed') ||
      (filter === 'In progress' && s.status === 'processing')
    return inQuery && inFilter
  })
  if (sort === 'Score') {
    return [...matches].sort((a, b) => (b.score ?? -1) - (a.score ?? -1))
  }
  return matches
}
