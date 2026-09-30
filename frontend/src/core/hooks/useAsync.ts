import { useEffect, useState, type DependencyList } from 'react'

export interface AsyncState<T> {
  data: T | undefined
  loading: boolean
  error: Error | undefined
}

interface Result<T> {
  deps: DependencyList
  data?: T
  error?: Error
}

const sameDeps = (a: DependencyList, b: DependencyList) =>
  a.length === b.length && a.every((value, i) => Object.is(value, b[i]))

/**
 * Runs an async loader whenever `deps` change and ignores results from stale runs.
 * `loading` is true until a result for the current deps arrives (stale data stays visible meanwhile).
 */
export function useAsync<T>(loader: () => Promise<T>, deps: DependencyList): AsyncState<T> {
  const [result, setResult] = useState<Result<T> | null>(null)

  useEffect(() => {
    let active = true
    loader().then(
      (data) => {
        if (active) setResult({ deps, data })
      },
      (error: unknown) => {
        if (active)
          setResult({ deps, error: error instanceof Error ? error : new Error(String(error)) })
      },
    )
    return () => {
      active = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- deps are supplied by the caller
  }, deps)

  const loading = !result || !sameDeps(result.deps, deps)
  return { data: result?.data, loading, error: loading ? undefined : result?.error }
}
