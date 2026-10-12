import { useCallback, useEffect, useState } from 'react'
import * as usersApi from '@/api/api.admin.users'
import type { AdminUser, AdminUserCounts } from '@/core/types'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'

const PAGE_SIZE = 50

interface ListState {
  /** Which query this data belongs to (search + status + reload version). */
  key: string
  users: AdminUser[]
  total: number
  counts: AdminUserCounts
}

/**
 * Users list for the admin Users screen: server-side search (debounced) and status filter,
 * "load more" paging, and local updates after create/edit so the list doesn't refetch.
 */
export function useAdminUsers(search: string, status: usersApi.UserStatusFilter | undefined) {
  const debouncedSearch = useDebouncedValue(search.trim())
  const [version, setVersion] = useState(0)
  const key = `${debouncedSearch}|${status ?? ''}|${version}`

  const [list, setList] = useState<ListState | null>(null)
  const [error, setError] = useState<{ key: string; error: Error } | null>(null)
  const [loadingMore, setLoadingMore] = useState(false)

  useEffect(() => {
    let active = true
    usersApi.listUsers({ search: debouncedSearch, status, limit: PAGE_SIZE }).then(
      (page) => {
        if (active) setList({ key, ...page })
      },
      (err: unknown) => {
        if (active) setError({ key, error: err instanceof Error ? err : new Error(String(err)) })
      },
    )
    return () => {
      active = false
    }
  }, [key, debouncedSearch, status])

  const failed = error?.key === key ? error.error : undefined
  // Stale results stay on screen while the next query loads.
  const loading = list?.key !== key && !failed

  const loadMore = useCallback(async () => {
    if (!list) return
    setLoadingMore(true)
    try {
      const page = await usersApi.listUsers({
        search: debouncedSearch,
        status,
        skip: list.users.length,
        limit: PAGE_SIZE,
      })
      setList((current) => {
        if (!current || current.key !== list.key) return current
        const seen = new Set(current.users.map((u) => u.id))
        return {
          ...current,
          users: [...current.users, ...page.users.filter((u) => !seen.has(u.id))],
          total: page.total,
          counts: page.counts,
        }
      })
    } finally {
      setLoadingMore(false)
    }
  }, [list, debouncedSearch, status])

  /** Put an updated user in place and keep the active/inactive counts right. */
  const replaceUser = useCallback((updated: AdminUser) => {
    setList((current) => {
      if (!current) return current
      const previous = current.users.find((u) => u.id === updated.id)
      const delta =
        previous && previous.isActive !== updated.isActive ? (updated.isActive ? 1 : -1) : 0
      return {
        ...current,
        users: current.users.map((u) => (u.id === updated.id ? updated : u)),
        counts: {
          ...current.counts,
          active: current.counts.active + delta,
          inactive: current.counts.inactive - delta,
        },
      }
    })
  }, [])

  /** Show a newly created user at the top (the list is newest first). */
  const addUser = useCallback((created: AdminUser) => {
    setList((current) => {
      if (!current) return current
      return {
        ...current,
        users: [created, ...current.users],
        total: current.total + 1,
        counts: {
          all: current.counts.all + 1,
          active: current.counts.active + (created.isActive ? 1 : 0),
          inactive: current.counts.inactive + (created.isActive ? 0 : 1),
        },
      }
    })
  }, [])

  const reload = useCallback(() => setVersion((v) => v + 1), [])

  return {
    users: list?.users,
    total: list?.total ?? 0,
    counts: list?.counts,
    hasMore: list ? list.users.length < list.total : false,
    loading,
    loadingMore,
    error: failed,
    loadMore,
    replaceUser,
    addUser,
    reload,
  }
}
