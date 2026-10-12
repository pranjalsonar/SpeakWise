// Report contract (speakwise_pipeline/src/speakwise/schemas.py, schema 1.x) and the checks the
// desktop app runs before showing anything. Kept dependency-free so it runs under `node --test`.

export type Status = 'ok' | 'warning' | 'unavailable' | 'failed' | 'skipped'
const STATUSES: readonly string[] = ['ok', 'warning', 'unavailable', 'failed', 'skipped']

export interface Metric {
  value: number | null
  unit: string
  status: Status
  denominator?: string | null
  note?: string | null
}

export interface TimedEvent {
  type: string
  start: number
  end: number
  text?: string | null
  details?: Record<string, unknown>
}

interface Section {
  status: Status
  warnings: string[]
  limitations: string[]
}

export interface SessionReport {
  session_metadata: {
    session_id: string
    schema_version: string
    topic: string
    reading_material_sha256: string
    speaking_duration_selected_s?: number | null
  }
  transcription: Section & { text: string }
  audio_analysis: Section & {
    speaking_time_s: Metric
    words_per_minute: Metric
    fillers?: (Section & { total: Metric; per_minute: Metric; by_type: Record<string, number>; events: TimedEvent[] }) | null
    repetitions?: (Section & { accidental_word_repetitions: Metric; phrase_repetitions: Metric; possible_emphasis: Metric }) | null
    pauses?: (Section & { short_pauses: Metric; long_pauses: Metric; longest_pause_s: Metric; pauses_per_minute: Metric }) | null
    clarity?: (Section & { unclear_segments: Metric; unclear_speech_s: Metric }) | null
    audio_quality?: (Section & { snr_estimate_db: Metric; speech_rms_dbfs: Metric; clipping_ratio: Metric }) | null
  }
  video_analysis: Section & {
    face_visible_pct: Metric
    head_toward_camera_pct: Metric
    camera_directed_gaze_pct: Metric
    head_orientation: Record<string, Metric>
    posture: Record<string, Metric>
    movement: Record<string, Metric>
  }
  context_evaluation: Section & {
    topic_relevance: Metric
    key_point_coverage_adjusted: Metric
    context_alignment: Metric
    provisional_threshold: number
    verdict?: string | null
    key_points: { id: number; text: string; covered: boolean; evidence_start?: number | null }[]
    claims: { text: string; start?: number | null; label: string; evidence?: string | null; reason?: string | null }[]
    off_topic_segments: TimedEvent[]
  }
  improvement_suggestions: {
    id: string
    area: string
    title: string
    suggestion: string
    evidence: string[]
    moments: number[]
    certainty: string
  }[]
  warnings: { module: string; code: string; message: string }[]
  errors: { module: string; stage: string; type: string; message: string }[]
}

export interface Expected {
  sessionId: string
  topic: string
  materialSha256: string
}

export type EnvelopeState =
  | { kind: 'pending' }
  | { kind: 'processing' }
  | { kind: 'failed'; message: string }
  | { kind: 'invalid'; message: string }
  | { kind: 'done'; report: SessionReport }

const REQUIRED_SECTIONS = [
  'session_metadata',
  'input_validation',
  'transcription',
  'audio_analysis',
  'video_analysis',
  'context_evaluation',
  'improvement_suggestions',
  'warnings',
  'errors',
]

const isObject = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v)

/** Every object shaped like a Metric must obey the value/status rule from schemas.py. */
function metricProblems(node: unknown, path: string, out: string[]): void {
  if (Array.isArray(node)) {
    node.forEach((child, i) => metricProblems(child, `${path}[${i}]`, out))
    return
  }
  if (!isObject(node)) return
  if ('unit' in node && 'status' in node && 'value' in node) {
    const { status, value } = node
    if (typeof status !== 'string' || !STATUSES.includes(status)) out.push(`${path}: unknown status`)
    else if ((status === 'ok' || status === 'warning') !== (typeof value === 'number' && Number.isFinite(value))) {
      out.push(`${path}: value does not match status '${status}'`)
    }
    return
  }
  for (const [key, child] of Object.entries(node)) metricProblems(child, path ? `${path}.${key}` : key, out)
}

/** Interprets the envelope the Colab worker writes: {status, session_id, report?, error?}. */
export function readEnvelope(envelope: unknown, expected: Expected): EnvelopeState {
  if (!isObject(envelope)) return { kind: 'invalid', message: 'The report file is not a JSON object.' }
  if (envelope.session_id !== expected.sessionId) {
    return { kind: 'invalid', message: 'The report belongs to a different session.' }
  }
  if (envelope.status === 'pending') return { kind: 'pending' }
  if (envelope.status === 'processing') return { kind: 'processing' }
  if (envelope.status === 'error') {
    return { kind: 'failed', message: typeof envelope.error === 'string' ? envelope.error : 'The Colab worker reported an error.' }
  }
  if (envelope.status !== 'done') return { kind: 'invalid', message: 'The report has an unknown status.' }

  const report = envelope.report
  if (!isObject(report)) return { kind: 'invalid', message: 'The report is missing.' }
  const missing = REQUIRED_SECTIONS.filter((k) => !(k in report))
  if (missing.length) return { kind: 'invalid', message: `The report is missing: ${missing.join(', ')}.` }

  const meta = report.session_metadata
  if (!isObject(meta)) return { kind: 'invalid', message: 'The report has no session metadata.' }
  if (typeof meta.schema_version !== 'string' || !meta.schema_version.startsWith('1.')) {
    return { kind: 'invalid', message: `Unsupported report schema version ${String(meta.schema_version)}.` }
  }
  if (meta.topic !== expected.topic) return { kind: 'invalid', message: 'The report was produced for a different topic.' }
  if (meta.reading_material_sha256 !== expected.materialSha256) {
    return { kind: 'invalid', message: 'The report was produced from different reading material.' }
  }
  const problems: string[] = []
  metricProblems(report, '', problems)
  if (problems.length) return { kind: 'invalid', message: `The report has invalid metrics (${problems.slice(0, 3).join('; ')}).` }

  return { kind: 'done', report: report as unknown as SessionReport }
}

export async function sha256Hex(text: string): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text))
  return Array.from(new Uint8Array(digest), (b) => b.toString(16).padStart(2, '0')).join('')
}
