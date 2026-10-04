import { AudioLines } from 'lucide-react'
import './BreathingLoader.css'

/** Calm "breathing" circle shown while the talk uploads and is analysed. */
export function BreathingLoader() {
  return (
    <span className="breathing-loader" aria-hidden="true">
      <span className="breathing-loader__core">
        <AudioLines size={28} />
      </span>
    </span>
  )
}
