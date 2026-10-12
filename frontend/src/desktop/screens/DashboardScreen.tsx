import type { ReactNode } from 'react'
import { Button } from '@/components/ui/Button'
import type { Metric, SessionReport } from '../report'

const UNIT_SUFFIX: Record<string, string> = {
  percent: '%',
  seconds: ' s',
  per_minute: ' / min',
  per_100_words: ' / 100 words',
  words_per_minute: ' wpm',
  dbfs: ' dBFS',
  db: ' dB',
  degrees: '°',
  score_0_100: ' / 100',
}

function formatValue(m: Metric): string {
  const v = m.value as number
  if (m.unit === 'count') return String(Math.round(v))
  if (m.unit === 'ratio') return v.toFixed(3)
  const digits = m.unit === 'seconds' || m.unit === 'degrees' ? 1 : 0
  return `${v.toFixed(digits)}${UNIT_SUFFIX[m.unit] ?? ` ${m.unit}`}`
}

/** Status rules from INTEGRATION.md: never turn a missing measurement into 0. */
export function MetricRow({ label, metric, caveat }: { label: string; metric?: Metric | null; caveat?: string }) {
  if (!metric || metric.status === 'skipped') return null
  let value: ReactNode
  if (metric.status === 'ok' || metric.status === 'warning') value = formatValue(metric)
  else if (metric.status === 'unavailable') value = <span className="dk-na">Not measured</span>
  else value = <span className="dk-na">Could not measure</span>
  const note = metric.status === 'failed' ? null : metric.note
  return (
    <div className="dk-metric">
      <dt>{label}</dt>
      <dd>
        {value}
        {metric.status === 'warning' && <span className="dk-est">estimate</span>}
        {(note || caveat) && <small>{[note, caveat].filter(Boolean).join(' · ')}</small>}
      </dd>
    </div>
  )
}

const humanize = (key: string) => key.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())
const clock = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`

const CLAIM_LABEL: Record<string, string> = {
  supported: 'Supported by the reading',
  potentially_inconsistent: 'Check against the reading',
  not_addressed: 'Not addressed in the reading',
  unable_to_evaluate: 'Could not evaluate',
}

function Card({ title, status, children }: { title: string; status?: string; children: ReactNode }) {
  return (
    <section className="dk-card">
      <header>
        <h2>{title}</h2>
        {status && status !== 'ok' && <span className="dk-pill">{status}</span>}
      </header>
      {children}
    </section>
  )
}

export function DashboardScreen({ report, onNewSession }: { report: SessionReport; onNewSession: () => void }) {
  const a = report.audio_analysis
  const v = report.video_analysis
  const c = report.context_evaluation

  return (
    <div className="dk-dashboard">
      <div className="dk-dashboard__head">
        <div>
          <h1>Your analysis</h1>
          <p className="dk-muted">{report.session_metadata.topic}</p>
        </div>
        <Button size="lg" onClick={onNewSession}>
          Start New Session
        </Button>
      </div>

      {(report.errors.length > 0 || report.warnings.length > 0) && (
        <section className="dk-card dk-card--warn">
          <h2>Notes from the analysis</h2>
          <ul>
            {report.errors.map((e, i) => (
              <li key={`e${i}`}>
                <strong>{e.module}:</strong> {e.message}
              </li>
            ))}
            {report.warnings.map((w, i) => (
              <li key={`w${i}`}>
                <strong>{w.module}:</strong> {w.message}
              </li>
            ))}
          </ul>
        </section>
      )}

      <div className="dk-grid">
        <Card title="Audio" status={a.status}>
          <dl>
            <MetricRow label="Speech rate" metric={a.words_per_minute} />
            <MetricRow label="Speaking time" metric={a.speaking_time_s} />
            <MetricRow label="Filler words" metric={a.fillers?.total} />
            <MetricRow label="Fillers per minute" metric={a.fillers?.per_minute} />
            <MetricRow label="Accidental repetitions" metric={a.repetitions?.accidental_word_repetitions} />
            <MetricRow label="Phrase repetitions" metric={a.repetitions?.phrase_repetitions} />
            <MetricRow label="Short pauses" metric={a.pauses?.short_pauses} />
            <MetricRow label="Long pauses" metric={a.pauses?.long_pauses} />
            <MetricRow label="Longest pause" metric={a.pauses?.longest_pause_s} />
            <MetricRow label="Unclear segments" metric={a.clarity?.unclear_segments} />
            <MetricRow label="Unclear speech" metric={a.clarity?.unclear_speech_s} />
            <MetricRow label="Signal-to-noise" metric={a.audio_quality?.snr_estimate_db} />
            <MetricRow label="Speech level" metric={a.audio_quality?.speech_rms_dbfs} />
            <MetricRow label="Clipping" metric={a.audio_quality?.clipping_ratio} />
          </dl>
          {a.fillers && Object.keys(a.fillers.by_type).length > 0 && (
            <p className="dk-fine">
              Fillers: {Object.entries(a.fillers.by_type).map(([k, n]) => `${k} ×${n}`).join(', ')}
            </p>
          )}
        </Card>

        <Card title="Video" status={v.status}>
          <dl>
            <MetricRow label="Face visible" metric={v.face_visible_pct} />
            <MetricRow label="Head toward camera" metric={v.head_toward_camera_pct} />
            <MetricRow
              label="Camera-directed gaze"
              metric={v.camera_directed_gaze_pct}
              caveat="Estimate only; not a measure of confidence"
            />
            {Object.entries(v.head_orientation).map(([k, m]) => (
              <MetricRow key={`h-${k}`} label={`Head ${humanize(k).toLowerCase()}`} metric={m} />
            ))}
            {Object.entries(v.posture).map(([k, m]) => (
              <MetricRow key={`p-${k}`} label={humanize(k)} metric={m} />
            ))}
            {Object.entries(v.movement).map(([k, m]) => (
              <MetricRow key={`m-${k}`} label={humanize(k)} metric={m} />
            ))}
          </dl>
        </Card>

        <Card title="Context" status={c.status}>
          <dl>
            <MetricRow label="Topic relevance" metric={c.topic_relevance} />
            <MetricRow label="Key-point coverage" metric={c.key_point_coverage_adjusted} />
            <MetricRow
              label="Context alignment"
              metric={c.context_alignment}
              caveat={`Provisional target ${c.provisional_threshold}/100, not yet validated`}
            />
          </dl>
          {c.verdict && (
            <p className="dk-fine">
              {c.verdict === 'meets_provisional_target' ? 'Meets' : 'Below'} the provisional target.
            </p>
          )}
          {c.key_points.length > 0 && (
            <>
              <h3>Key points</h3>
              <ul className="dk-list">
                {c.key_points.map((k) => (
                  <li key={k.id} className={k.covered ? 'dk-yes' : 'dk-no'}>
                    {k.covered ? 'Covered' : 'Not covered'}: {k.text}
                  </li>
                ))}
              </ul>
            </>
          )}
          {c.claims.length > 0 && (
            <>
              <h3>Claims you made</h3>
              <ul className="dk-list">
                {c.claims.map((cl, i) => (
                  <li key={i}>
                    &ldquo;{cl.text}&rdquo; <em>{CLAIM_LABEL[cl.label] ?? cl.label}</em>
                    {cl.start != null && <span className="dk-fine"> at {clock(cl.start)}</span>}
                  </li>
                ))}
              </ul>
            </>
          )}
          {c.off_topic_segments.length > 0 && (
            <>
              <h3>Off-topic moments</h3>
              <ul className="dk-list">
                {c.off_topic_segments.map((s, i) => (
                  <li key={i}>
                    {clock(s.start)}–{clock(s.end)} {s.text && <>&ldquo;{s.text}&rdquo;</>}
                  </li>
                ))}
              </ul>
            </>
          )}
        </Card>

        <Card title="How to improve">
          {report.improvement_suggestions.length === 0 ? (
            <p className="dk-muted">The analysis returned no suggestions.</p>
          ) : (
            <ul className="dk-suggestions">
              {report.improvement_suggestions.map((s) => (
                <li key={s.id}>
                  <h3>
                    {s.title} {s.certainty === 'estimate' && <span className="dk-est">estimate</span>}
                  </h3>
                  <p>{s.suggestion}</p>
                  {s.evidence.length > 0 && <p className="dk-fine">{s.evidence.join(' · ')}</p>}
                  {s.moments.length > 0 && <p className="dk-fine">At {s.moments.map(clock).join(', ')}</p>}
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      {report.transcription.text && (
        <details className="dk-card">
          <summary>Transcript</summary>
          <p>{report.transcription.text}</p>
        </details>
      )}
    </div>
  )
}
