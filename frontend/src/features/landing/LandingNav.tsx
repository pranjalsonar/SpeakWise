import { useState } from 'react'
import { Menu, X } from 'lucide-react'
import { ROUTES } from '@/app/routes'
import { Button } from '@/components/ui/Button'
import { IconButton } from '@/components/ui/IconButton'
import { landingHref } from './landingLinks'
import './LandingNav.css'

export function LandingNav({ links }: { links: string[] }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const close = () => setMenuOpen(false)

  return (
    <header className="landing-nav">
      <div className="landing-nav__bar">
        <a href="#top" className="landing-nav__logo">
          SpeakWise
        </a>

        <nav className="landing-nav__links" aria-label="Main">
          {links.map((link, i) => (
            <a
              key={link}
              href={landingHref(link)}
              className={['landing-nav__link', i === 0 && 'landing-nav__link--active']
                .filter(Boolean)
                .join(' ')}
              aria-current={i === 0 ? 'page' : undefined}
            >
              {link}
            </a>
          ))}
          <Button to={ROUTES.login} size="sm" className="landing-nav__cta">
            Get Started
          </Button>
        </nav>

        <IconButton
          className="landing-nav__menu-btn"
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={menuOpen}
          aria-controls="landing-menu"
          icon={menuOpen ? <X size={22} /> : <Menu size={22} />}
          onClick={() => setMenuOpen((open) => !open)}
        />
      </div>

      {menuOpen && (
        <nav id="landing-menu" className="landing-nav__menu" aria-label="Main">
          {links.map((link) => (
            <a
              key={link}
              href={landingHref(link)}
              className="landing-nav__menu-link"
              onClick={close}
            >
              {link}
            </a>
          ))}
          <Button to={ROUTES.login} block>
            Get Started
          </Button>
        </nav>
      )}
    </header>
  )
}
