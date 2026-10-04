import './ScoreCircle.css'

interface ScoreCircleProps {
  score: number
  size?: 36 | 40 | 44
}

/** Small sage disc with the score in Caprasimo (session rows, admin lists). */
export function ScoreCircle({ score, size = 44 }: ScoreCircleProps) {
  return (
    <span className={`score-circle score-circle--${size}`} aria-label={`Score ${score}`}>
      {score}
    </span>
  )
}
