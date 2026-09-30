import type { ReactNode } from 'react'
import './InsightList.css'

interface InsightListProps {
  title: string
  items: string[]
  tone: 'well' | 'improve'
  icon: ReactNode
}

/** "What went well" (sage) / "What to improve" (accent) cards. */
export function InsightList({ title, items, tone, icon }: InsightListProps) {
  return (
    <section className={`insight-list insight-list--${tone}`}>
      <h2 className="insight-list__title">{title}</h2>
      <ul className="insight-list__items">
        {items.map((item) => (
          <li key={item} className="insight-list__item">
            <span className="insight-list__icon" aria-hidden="true">
              {icon}
            </span>
            {item}
          </li>
        ))}
      </ul>
    </section>
  )
}
