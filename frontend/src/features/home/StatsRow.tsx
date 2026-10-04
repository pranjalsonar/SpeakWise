import { Clock, Flame, Mic, type LucideIcon } from 'lucide-react'
import type { Stats } from '@/core/types'
import './StatsRow.css'

interface StatProps {
  icon: LucideIcon
  value: string
  label: string
  tone?: 'surface' | 'sage'
}

function StatCard({ icon: Icon, value, label, tone = 'surface' }: StatProps) {
  return (
    <div className={`stats-row__card stats-row__card--${tone}`}>
      <span className="stats-row__icon" aria-hidden="true">
        <Icon size={20} />
      </span>
      <div className="stats-row__text">
        <span className="stats-row__value">{value}</span>
        <span className="stats-row__label">{label}</span>
      </div>
    </div>
  )
}

export function StatsRow({ stats }: { stats: Stats }) {
  return (
    <section className="stats-row" aria-label="Your progress">
      <StatCard icon={Mic} value={String(stats.sessionsCompleted)} label="Sessions completed" />
      <StatCard icon={Clock} value={String(stats.minutesSpoken)} label="Minutes spoken" />
      <StatCard
        icon={Flame}
        value={`${stats.streakDays} ${stats.streakDays === 1 ? 'day' : 'days'}`}
        label="Current streak"
        tone="sage"
      />
    </section>
  )
}
