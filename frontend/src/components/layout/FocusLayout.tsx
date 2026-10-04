import type { ReactNode } from 'react'
import { Check, X } from 'lucide-react'
import { useNavigate } from 'react-router'
import { ROUTES } from '@/app/routes'
import { IconButton } from '@/components/ui/IconButton'
import './FocusLayout.css'

const SESSION_STEPS = ['Topic', 'Prepare', 'Record', 'Review'] as const
export type SessionStepName = (typeof SESSION_STEPS)[number]

interface FocusLayoutProps {
  step: SessionStepName
  /** Extra controls on the mobile top bar's right (e.g. A−/A+ on Prepare). */
  mobileActions?: ReactNode
  /** Rendered directly under the top bar (e.g. the reading progress bar). */
  belowTopBar?: ReactNode
  /** Dark camera surface (Record). */
  tone?: 'light' | 'dark'
  /** Hairline under the desktop top bar (off when a progress bar sits there). */
  bordered?: boolean
  /** Show the 4-segment progress bar on mobile (off on Prepare, which shows reading progress). */
  mobileSegments?: boolean
  /** Lock the layout to the viewport so the page manages its own scroll areas. */
  fitViewport?: boolean
  /** Hide the top bar on mobile (Record draws its own overlay header). */
  hideMobileTopBar?: boolean
  onExit?: () => void
  children: ReactNode
}

/** Distraction-free layout for session steps: no nav, just exit + progress. */
export function FocusLayout({
  step,
  mobileActions,
  belowTopBar,
  tone = 'light',
  bordered = true,
  mobileSegments = true,
  fitViewport = false,
  hideMobileTopBar = false,
  onExit,
  children,
}: FocusLayoutProps) {
  const navigate = useNavigate()
  const index = SESSION_STEPS.indexOf(step)
  const exit = onExit ?? (() => navigate(ROUTES.home))
  const classes = [
    'focus-layout',
    `focus-layout--${tone}`,
    !bordered && 'focus-layout--borderless',
    !mobileSegments && 'focus-layout--no-segments',
    fitViewport && 'focus-layout--fit',
    hideMobileTopBar && 'focus-layout--no-mobile-topbar',
  ]

  return (
    <div className={classes.filter(Boolean).join(' ')}>
      <header className="focus-layout__topbar">
        <div className="focus-layout__row">
          <IconButton
            aria-label="Exit session"
            icon={<X size={20} />}
            tone={tone === 'dark' ? 'dark' : 'outline'}
            onClick={exit}
          />
          <div className="focus-layout__mobile-title">
            <span className="focus-layout__step-name">{step}</span>
            <span className="focus-layout__step-count">Step {index + 1} of 4</span>
          </div>
          {mobileActions && <div className="focus-layout__mobile-actions">{mobileActions}</div>}

          <ol className="focus-layout__steps" aria-label="Session progress">
            {SESSION_STEPS.map((name, i) => {
              const state = i < index ? 'done' : i === index ? 'current' : 'todo'
              return (
                <li key={name} className={`focus-layout__step focus-layout__step--${state}`}>
                  {i > 0 && <span className="focus-layout__line" aria-hidden="true" />}
                  <span className="focus-layout__dot" aria-hidden="true">
                    {state === 'done' ? <Check size={16} /> : i + 1}
                  </span>
                  <span className="focus-layout__label">
                    {name}
                    <span className="sr-only">
                      {state === 'done' ? ' (done)' : state === 'current' ? ' (current step)' : ''}
                    </span>
                  </span>
                </li>
              )
            })}
          </ol>

          <span className="focus-layout__step-summary">
            Step {index + 1} · {step}
          </span>
        </div>

        <div className="focus-layout__segments" aria-hidden="true">
          {SESSION_STEPS.map((name, i) => (
            <span
              key={name}
              className={['focus-layout__segment', i <= index && 'focus-layout__segment--on']
                .filter(Boolean)
                .join(' ')}
            />
          ))}
        </div>
      </header>
      {belowTopBar}
      {children}
    </div>
  )
}
