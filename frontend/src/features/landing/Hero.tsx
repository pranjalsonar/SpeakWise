import { ROUTES } from '@/app/routes'
import { Button } from '@/components/ui/Button'
import { HeroIllustration } from './HeroIllustration'
import './Hero.css'

export function Hero({ title, body }: { title: string; body: string }) {
  return (
    <section className="hero" aria-labelledby="hero-title">
      <div className="hero__copy">
        <p className="hero__overline">AI public-speaking coach</p>
        <h1 id="hero-title" className="hero__title">
          {title}
        </h1>
        <p className="hero__body">{body}</p>
        <div className="hero__actions">
          <Button to={ROUTES.login} size="lg" className="hero__btn">
            Get Started
          </Button>
          <Button href="#features" variant="secondary" size="lg" className="hero__btn">
            Learn More
          </Button>
        </div>
      </div>
      <HeroIllustration />
    </section>
  )
}
