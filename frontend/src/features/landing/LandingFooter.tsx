import { landingHref } from './landingLinks'
import './LandingFooter.css'

const socials = [
  { label: 'LinkedIn', short: 'in' },
  { label: 'X', short: 'X' },
  { label: 'YouTube', short: 'YT' },
]

export function LandingFooter({ links }: { links: string[] }) {
  return (
    <footer className="landing-footer" id="contact">
      <div className="landing-footer__brand" id="about">
        <span className="landing-footer__logo">SpeakWise</span>
        <span className="landing-footer__copy">© 2026 SpeakWise. All rights reserved.</span>
      </div>

      <nav className="landing-footer__col" aria-labelledby="footer-links">
        <span id="footer-links" className="landing-footer__heading">
          Quick links
        </span>
        <div className="landing-footer__links">
          {links.map((link) => (
            <a key={link} href={landingHref(link)} className="landing-footer__link">
              {link}
            </a>
          ))}
        </div>
      </nav>

      <div className="landing-footer__col">
        <span className="landing-footer__heading">Follow</span>
        <div className="landing-footer__socials">
          {socials.map((s) => (
            <a
              key={s.label}
              href="#contact"
              className="landing-footer__social"
              aria-label={s.label}
            >
              {s.short}
            </a>
          ))}
        </div>
      </div>
    </footer>
  )
}
