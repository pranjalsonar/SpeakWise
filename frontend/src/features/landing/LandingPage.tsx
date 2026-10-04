import { contentService } from '@/core/services'
import { Features } from './Features'
import { Hero } from './Hero'
import { LandingFooter } from './LandingFooter'
import { LandingNav } from './LandingNav'
import './LandingPage.css'

export function LandingPage() {
  const content = contentService.getLandingContent()
  return (
    <div className="landing-page" id="top">
      <LandingNav links={content.navLinks} />
      <main>
        <Hero title={content.heroTitle} body={content.heroBody} />
        <Features features={content.features} />
      </main>
      <LandingFooter links={content.navLinks} />
    </div>
  )
}
