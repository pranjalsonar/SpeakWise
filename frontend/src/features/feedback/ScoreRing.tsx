import './ScoreRing.css'

/** Conic-gradient ring (sage on neutral) with the overall score in the middle. */
export function ScoreRing({ score }: { score: number }) {
  return (
    <div
      className="score-ring"
      style={{ background: `conic-gradient(var(--sage-600) 0 ${score}%, var(--neutral-300) 0)` }}
      role="img"
      aria-label={`Overall score ${score} out of 100`}
    >
      <div className="score-ring__inner">
        <span className="score-ring__value">{score}</span>
        <span className="score-ring__max">/ 100</span>
      </div>
    </div>
  )
}
