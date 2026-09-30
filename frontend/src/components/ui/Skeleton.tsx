import './Skeleton.css'

/** Placeholder block shown while mock/API data loads. */
export function Skeleton({ height = 72, radius = 24 }: { height?: number; radius?: number }) {
  return <div className="skeleton" style={{ height, borderRadius: radius }} aria-hidden="true" />
}
