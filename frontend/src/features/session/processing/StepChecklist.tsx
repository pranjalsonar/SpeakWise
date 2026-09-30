import { Check } from 'lucide-react'
import './StepChecklist.css'

export type StepState = 'done' | 'active' | 'todo'

/** Processing steps: done = sage check · active = spinner ring · todo = outline. */
export function StepChecklist({ steps, states }: { steps: string[]; states: StepState[] }) {
  return (
    <ol className="step-checklist">
      {steps.map((label, i) => {
        const state = states[i] ?? 'todo'
        return (
          <li key={label} className={`step-checklist__item step-checklist__item--${state}`}>
            <span className="step-checklist__icon" aria-hidden="true">
              {state === 'done' && <Check size={16} />}
            </span>
            <span>{label}</span>
            <span className="sr-only">
              {state === 'done' ? ' (done)' : state === 'active' ? ' (in progress)' : ''}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
