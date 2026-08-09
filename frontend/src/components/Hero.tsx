import "./Hero.css";
function Hero() {
  return (
    <section className="hero" id="home">
      <div className="hero-content">
        <div className="hero-text">
          <p className="hero-badge">AI Powered Learning</p>
      <h1>Master Public Speaking with AI</h1>

      <p className="hero-description">
        Improve your confidence, communication skills, vocabulary, and domain
        knowledge through AI-powered public speaking practice with personalized
        feedback.
      </p>

      <div className="hero-actions">
        <button className="primary-button" type="button">
          Get Started
        </button>
        <button className="secondary-button" type="button">
          Learn More
        </button>
      </div>

      <div className="hero-stats" aria-label="SpeakWise statistics">
        <div className="stat-item">
          <strong>500+</strong>
          <span>Students Practicing</span>
        </div>
        <div className="stat-item">
          <strong>95%</strong>
          <span>Confidence Improvement</span>
        </div>
        <div className="stat-item">
          <strong>10K+</strong>
          <span>Speeches Analysed</span>
        </div>
      </div>
    </div>

    <div className="hero-visual" aria-hidden="true">
      <div className="hero-illustration">
        <div className="illustration-circle"></div>

        <div className="ai-card">
          <span className="ai-card-label">AI Speech Coach</span>
          <span className="ai-card-status">Listening...</span>
        </div>

        <div className="microphone-placeholder">
          <div className="microphone-top"></div>
          <div className="microphone-stem"></div>
          <div className="microphone-base"></div>
        </div>

        <div className="speech-bubble">
          <span className="speech-line"></span>
          <span className="speech-line"></span>
          <span className="speech-line short-line"></span>
        </div>

        <div className="analytics-card">
          <span className="analytics-title">Speaking Progress</span>
          <div className="analytics-bars">
            <span className="bar bar-one"></span>
            <span className="bar bar-two"></span>
            <span className="bar bar-three"></span>
            <span className="bar bar-four"></span>
          </div>
          <span className="analytics-score">95%</span>
        </div>
      </div>
    </div>
  </div>
</section>
  );
}
export default Hero;