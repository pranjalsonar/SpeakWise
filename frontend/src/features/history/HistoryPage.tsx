import { useMemo, useState } from 'react'
import { History } from 'lucide-react'
import { AppShell } from '@/components/layout/AppShell'
import { SessionRow, SessionTableHeader } from '@/components/shared/SessionRow'
import { Button } from '@/components/ui/Button'
import { Chip } from '@/components/ui/Chip'
import { EmptyState } from '@/components/ui/EmptyState'
import { SearchInput } from '@/components/ui/SearchInput'
import { SegmentedControl } from '@/components/ui/SegmentedControl'
import { Skeleton } from '@/components/ui/Skeleton'
import { useCurrentUser } from '@/context/AuthContext'
import { useAsync } from '@/core/hooks/useAsync'
import { sessionService } from '@/core/services'
import { useIsDesktop } from '@/hooks/useMediaQuery'
import {
  applyHistoryFilters,
  HISTORY_FILTERS,
  HISTORY_SORTS,
  type HistoryFilter,
  type HistorySort,
} from './historyFilters'
import './HistoryPage.css'

export function HistoryPage() {
  const user = useCurrentUser()
  const isDesktop = useIsDesktop()
  const { data: sessions, loading } = useAsync(
    () => sessionService.getHistory(user.email),
    [user.email],
  )
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<HistoryFilter>('All')
  const [sort, setSort] = useState<HistorySort>('Date')

  const items = useMemo(
    () => applyHistoryFilters(sessions ?? [], query, filter, sort),
    [sessions, query, filter, sort],
  )
  const countLabel = `${items.length} ${items.length === 1 ? 'session' : 'sessions'}`

  const clearFilters = () => {
    setQuery('')
    setFilter('All')
    setSort('Date')
  }

  const sortChips = HISTORY_SORTS.map((option) => (
    <Chip key={option} size="sm" selected={sort === option} onClick={() => setSort(option)}>
      {option}
    </Chip>
  ))

  const empty = (
    <EmptyState
      icon={<History />}
      size="md"
      variant={isDesktop ? 'plain' : 'dashed'}
      title="No sessions found"
      body="Try another search or filter."
      action={
        <Button variant="secondary" size={isDesktop ? 'md' : 'sm'} onClick={clearFilters}>
          Clear filters
        </Button>
      }
    />
  )

  return (
    <AppShell mobileTitle="History">
      <div className="history-page">
        <header className="history-page__header">
          <h1 className="history-page__title">History</h1>
          <p className="history-page__subtitle">Every talk you've recorded, with its score.</p>
        </header>

        <div className="history-page__toolbar">
          <SearchInput
            label="Search sessions"
            value={query}
            onChange={setQuery}
            placeholder={isDesktop ? 'Search topics or categories' : 'Search topics'}
            className="history-page__search"
          />
          <SegmentedControl
            label="Filter sessions"
            options={HISTORY_FILTERS}
            value={filter}
            onChange={setFilter}
            fullWidth={!isDesktop}
          />
          <div className="history-page__sort">
            <span className="history-page__count">{countLabel}</span>
            <span className="history-page__sort-label">{isDesktop ? 'Sort by' : 'Sort'}</span>
            {sortChips}
          </div>
        </div>

        {loading ? (
          <Skeleton height={420} radius={40} />
        ) : (
          <section className="history-page__list" aria-label="Sessions">
            <SessionTableHeader count={items.length} />
            {items.map((session) => (
              <SessionRow key={session.id} session={session} variant="history" />
            ))}
            {items.length === 0 && empty}
          </section>
        )}
      </div>
    </AppShell>
  )
}
