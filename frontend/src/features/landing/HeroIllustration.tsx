import './HeroIllustration.css'

/** Decorative styled-div illustration (no images). Hidden from assistive tech. */
export function HeroIllustration() {
  return (
    <div className="hero-art" aria-hidden="true">
      <span className="hero-art__circle hero-art__circle--accent" />
      <span className="hero-art__circle hero-art__circle--sage" />
      <span className="hero-art__rec">
        <span className="hero-art__rec-dot" />
        REC 2:41
      </span>
      <div className="hero-art__topic">
        <span className="hero-art__topic-label">Today's topic</span>
        <span className="hero-art__topic-title">Should AI tutors replace homework help?</span>
      </div>
      <div className="hero-art__score">
        <div className="hero-art__score-row">
          <span>Clarity</span>
          <span>82</span>
        </div>
        <div className="hero-art__bar">
          <span className="hero-art__bar-fill hero-art__bar-fill--sage" />
        </div>
        <div className="hero-art__score-row">
          <span>Pace</span>
          <span>142 wpm</span>
        </div>
        <div className="hero-art__bar">
          <span className="hero-art__bar-fill hero-art__bar-fill--accent" />
        </div>
      </div>
    </div>
  )
}
