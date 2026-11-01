import type { Report, ScoreKey } from '@/types/report';

export type MetricCard = {
  key: ScoreKey;
  label: string;
  score: number;
  /** Short measured value, e.g. "142 wpm". */
  value?: string;
  /** One plain-English sentence. */
  insight: string;
};

const pct = (n: number) => `${Math.round(n)}%`;

/** Turns the backend report into the handoff's metric cards (name · score · bar · value · insight). */
export function buildMetricCards(report: Report): MetricCard[] {
  const { speech: s, video: v, context: c, scores } = report;
  const label = (k: ScoreKey) => report.labels[k];
  const topFillers = Object.entries(s.filler_breakdown)
    .filter(([w]) => !w.startsWith('('))
    .sort((a, b) => b[1] - a[1])
    .slice(0, 2)
    .map(([w, n]) => `'${w}' ×${n}`)
    .join(', ');

  const cards: MetricCard[] = [
    {
      key: 'fillers',
      label: label('fillers'),
      score: scores.fillers,
      value: `${s.filler_count} ${s.filler_count === 1 ? 'filler' : 'fillers'}`,
      insight: s.filler_count === 0 ? 'No filler words. Great control.' : `${topFillers || 'Some hesitation sounds'}. Try a silent pause instead.`,
    },
    {
      key: 'pace',
      label: label('pace'),
      score: scores.pace,
      value: `${Math.round(s.wpm)} wpm`,
      insight:
        s.wpm >= 120 && s.wpm <= 160
          ? 'Right in the ideal range (120–160 wpm).'
          : s.wpm > 160
            ? 'A little fast. Slow down so key points land.'
            : 'A little slow. Keep the energy up between ideas.',
    },
    {
      key: 'pauses',
      label: label('pauses'),
      score: scores.pauses,
      value: `${s.long_pause_count} long ${s.long_pause_count === 1 ? 'pause' : 'pauses'}`,
      insight: s.long_pause_count === 0 ? 'Smooth flow with natural breaths.' : `Longest pause ${s.longest_pause_sec}s. Plan your next point before you start.`,
    },
    {
      key: 'repetition',
      label: label('repetition'),
      score: scores.repetition,
      value: s.stutter_count ? `${s.stutter_count} restarts` : undefined,
      insight: s.overused_words.length
        ? `You leaned on ${s.overused_words.slice(0, 2).map((o) => `'${o.word}'`).join(' and ')}. Try synonyms.`
        : 'Good variety of words.',
    },
    {
      key: 'clarity',
      label: label('clarity'),
      score: scores.clarity,
      value: `${pct(s.clarity_pct)} clear`,
      insight: s.mumbled_count ? `${s.mumbled_count} words were unclear or too quiet.` : 'Every word came through clearly.',
    },
    {
      key: 'eye_contact',
      label: label('eye_contact'),
      score: scores.eye_contact,
      value: pct(v.eye_contact_pct),
      insight: v.eye_contact_pct >= 75 ? 'Strong, steady eye contact.' : 'Look at the lens, not your own picture.',
    },
    {
      key: 'body_language',
      label: label('body_language'),
      score: scores.body_language,
      insight:
        v.slouch_pct > 20
          ? 'Sit or stand taller; you slouched at times.'
          : v.face_touch_count > 0
            ? `You touched your face ${v.face_touch_count} ${v.face_touch_count === 1 ? 'time' : 'times'}.`
            : 'Open, relaxed posture.',
    },
    {
      key: 'confidence',
      label: label('confidence'),
      score: scores.confidence,
      insight:
        s.pitch_variation_semitones < 2
          ? 'Vary your pitch to stress key words.'
          : 'Steady voice with good expression.',
    },
    {
      key: 'context',
      label: label('context'),
      score: scores.context,
      value: `${pct(c.score)} on topic`,
      insight: c.verdict || (c.passed ? 'You stayed on topic.' : 'Use more ideas from the article.'),
    },
  ];
  return cards;
}

/** "1:05" */
export const fmtDuration = (sec: number) => `${Math.floor(sec / 60)}:${String(Math.round(sec % 60)).padStart(2, '0')}`;
