/** Report produced by the backend (backend/app/services/analysis/pipeline.py, version 1). */

export type ScoreKey =
  | 'fillers'
  | 'pauses'
  | 'repetition'
  | 'clarity'
  | 'pace'
  | 'eye_contact'
  | 'body_language'
  | 'confidence'
  | 'context';

export type Report = {
  version: number;
  topic: { id: string; title: string; category: string };
  first_name: string | null;
  scores: Record<ScoreKey | 'overall' | 'voice_variety' | 'volume', number>;
  grade: string;
  labels: Record<ScoreKey, string>;
  weights: Record<ScoreKey, number>;
  summary: string;
  coach: {
    headline: string;
    strengths: string[];
    improvements: { area: string; advice: string }[];
    encouragement: string;
  } | null;
  tips: string[];
  speech: {
    transcript: string;
    transcript_segments: { text: string; kind: 'filler' | 'mumble' | null }[];
    duration_sec: number;
    word_count: number;
    wpm: number;
    filler_count: number;
    filler_per_min: number;
    filler_breakdown: Record<string, number>;
    short_pause_count: number;
    long_pause_count: number;
    longest_pause_sec: number;
    stutter_count: number;
    overused_words: { word: string; count: number }[];
    repeated_phrases: { phrase: string; count: number }[];
    mumbled_count: number;
    clarity_pct: number;
    loudness_dbfs: number;
    pitch_variation_semitones: number;
  };
  video: {
    frames_analyzed: number;
    face_visible_pct: number;
    eye_contact_pct: number;
    looking_down_pct: number;
    blinks_per_min: number;
    smile_pct: number;
    tension_pct: number;
    slouch_pct: number;
    shoulder_tilt_pct: number;
    arms_crossed_pct: number;
    face_touch_count: number;
    gesture_pct: number;
    fidget_pct: number;
  };
  context: {
    score: number;
    passed: boolean;
    verdict: string;
    on_topic_pct: number;
    material_coverage_pct: number;
    llm_score: number | null;
    covered_points: string[];
    missed_points: string[];
    off_topic_points: string[];
    factual_issues: string[];
    note: string;
  };
  warnings: string[];
};
