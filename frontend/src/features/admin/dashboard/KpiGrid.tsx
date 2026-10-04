import type { AdminKpi } from '@/core/types'
import { formatNumber } from '@/core/utils'
import './KpiGrid.css'

export function KpiGrid({ kpis }: { kpis: AdminKpi[] }) {
  return (
    <section className="kpi-grid" aria-label="Platform numbers">
      {kpis.map((kpi) => (
        <div key={kpi.key} className="kpi-grid__card">
          <span className="kpi-grid__label">{kpi.label}</span>
          <span className="kpi-grid__value">{formatNumber(kpi.value)}</span>
          <span className="kpi-grid__delta">{kpi.delta}</span>
        </div>
      ))}
    </section>
  )
}
