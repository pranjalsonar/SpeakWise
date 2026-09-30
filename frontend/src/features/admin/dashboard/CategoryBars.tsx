import type { CategoryShare } from '@/core/types'
import './CategoryBars.css'

export function CategoryBars({ shares }: { shares: CategoryShare[] }) {
  return (
    <section className="category-bars" aria-labelledby="category-bars-title">
      <h2 id="category-bars-title" className="category-bars__title">
        Sessions by category
      </h2>
      <ul className="category-bars__list">
        {shares.map((share) => (
          <li key={share.category} className="category-bars__item">
            <div className="category-bars__row">
              <span>{share.category}</span>
              <span>{share.pct}%</span>
            </div>
            <span className="category-bars__track" aria-hidden="true">
              <span className="category-bars__fill" style={{ width: `${share.pct}%` }} />
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}
