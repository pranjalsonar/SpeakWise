import type { WeeklyCount } from '@/core/types'
import './WeeklyBarChart.css'

/** Bar height scale from the handoff: value / 800. */
const SCALE_MAX = 800

/** CSS bar chart of talk sessions over the last 8 weeks. */
export function WeeklyBarChart({ weeks }: { weeks: WeeklyCount[] }) {
  const first = weeks[0]
  const last = weeks[weeks.length - 1]
  const summary = weeks.map((w) => `${w.week}: ${w.count}`).join(', ')

  return (
    <section className="week-chart" aria-labelledby="week-chart-title">
      <div className="week-chart__head">
        <h2 id="week-chart-title" className="week-chart__title">
          <span className="week-chart__title-long">Talk sessions per week</span>
          <span className="week-chart__title-short">Sessions per week</span>
        </h2>
        <span className="week-chart__range">Last 8 weeks</span>
      </div>
      <div
        className="week-chart__plot"
        role="img"
        aria-label={`Talk sessions per week. ${summary}`}
      >
        {weeks.map((w) => (
          <div key={w.week} className="week-chart__col">
            <span className="week-chart__value">{w.count}</span>
            <span className="week-chart__area">
              <span
                className="week-chart__bar"
                style={{ height: `${Math.min(100, (w.count / SCALE_MAX) * 100)}%` }}
              />
            </span>
            <span className="week-chart__label">{w.week}</span>
          </div>
        ))}
      </div>
      {first && last && (
        <div className="week-chart__foot" aria-hidden="true">
          <span>{first.week}</span>
          <span>
            {last.week} · {last.count}
          </span>
        </div>
      )}
    </section>
  )
}
