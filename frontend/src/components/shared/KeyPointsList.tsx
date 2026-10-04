import './KeyPointsList.css'

/** Numbered key points with sage number discs (Prepare rail, Record cue card). */
export function KeyPointsList({
  points,
  tone = 'light',
}: {
  points: string[]
  tone?: 'light' | 'dark'
}) {
  return (
    <ol className={`key-points key-points--${tone}`}>
      {points.map((point, i) => (
        <li key={point} className="key-points__item">
          <span className="key-points__num" aria-hidden="true">
            {i + 1}
          </span>
          <span>{point}</span>
        </li>
      ))}
    </ol>
  )
}
