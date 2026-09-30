import type { ReactNode } from 'react'
import { ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router'
import { IconButton } from '@/components/ui/IconButton'
import './AuthLayout.css'

interface AuthLayoutProps {
  /** Brand panel colour: accent (login) or sage (register). */
  tone: 'accent' | 'sage'
  headline: string
  body: string
  /** Mobile header: an accent banner (login) or back arrow + logo (register). */
  mobileHeader: 'banner' | { backTo: string }
  children: ReactNode
}

/** Desktop: 50/50 split with a decorative brand panel. Mobile: header + form. */
export function AuthLayout({ tone, headline, body, mobileHeader, children }: AuthLayoutProps) {
  const navigate = useNavigate()

  return (
    <div className="auth-layout">
      <aside className={`auth-layout__brand auth-layout__brand--${tone}`}>
        <span className="auth-layout__circle auth-layout__circle--a" aria-hidden="true" />
        <span className="auth-layout__circle auth-layout__circle--b" aria-hidden="true" />
        <span className="auth-layout__circle auth-layout__circle--c" aria-hidden="true" />
        <span className="auth-layout__logo">SpeakWise</span>
        <div className="auth-layout__pitch">
          <p className="auth-layout__headline">{headline}</p>
          <p className="auth-layout__body">{body}</p>
        </div>
      </aside>

      <main className="auth-layout__main">
        {mobileHeader === 'banner' ? (
          <div className="auth-layout__banner" aria-hidden="true">
            <span className="auth-layout__banner-circle auth-layout__banner-circle--a" />
            <span className="auth-layout__banner-circle auth-layout__banner-circle--b" />
            <span className="auth-layout__banner-logo">SpeakWise</span>
          </div>
        ) : (
          <div className="auth-layout__back">
            <IconButton
              aria-label="Back"
              icon={<ArrowLeft size={20} />}
              onClick={() => navigate(mobileHeader.backTo)}
            />
            <span className="auth-layout__back-logo">SpeakWise</span>
          </div>
        )}
        <div className="auth-layout__form">{children}</div>
      </main>
    </div>
  )
}
