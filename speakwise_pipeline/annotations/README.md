# Annotation workflow

Accuracy cannot be claimed without human annotations. This folder holds **templates only**;
filled-in annotations of real people stay out of Git (see `.gitignore`), because they contain
private transcripts.

## 1. Recordings (fillers, repetitions, pauses, transcript)

1. Get written consent from the speaker for recording, analysis and storage (template field `consent`).
2. Copy `templates/recording_annotation.json` to `annotations/<recording_id>.json`.
3. Listen in Audacity or ELAN at normal speed, then at 0.75x. Mark:
   * `reference_transcript`: verbatim, including "um", "uh", repeated words and false starts.
   * `fillers`: start/end seconds and label ("um", "like", "you know"...). Count "like/so" only when
     they carry no meaning (discourse filler).
   * `repetitions`: immediate unintended repeats; mark deliberate emphasis as `"type": "emphasis"`.
   * `pauses`: silences >= 0.5 s inside the talk (not before the first or after the last word).
   * `unclear`: stretches you could not understand.
4. Ideally a second person annotates independently; disagreements are discussed and recorded.
5. Score the pipeline: `python scripts/evaluate_annotations.py outputs/report_<id>.json annotations/<id>.json`
   (precision/recall/F1 with a 0.5 s tolerance, and word error rate).

## 2. Context ratings (relevance, key points, consistency)

1. Add an example to `templates/context_rating.jsonl` format: topic/material id, the transcript,
   and one entry per annotator.
2. Each annotator reads the material and the transcript, then records:
   * `relevance_1to5`: 1 = unrelated, 3 = partly about the material, 5 = fully about it.
   * `covered_key_points`: ids from `data/context_eval/materials.json`.
   * `inconsistent_statements`: sentences that contradict the material (not merely absent from it).
3. Compare with `scripts/evaluate_context.py` after setting `annotation_status` to
   `"human_rated"`; report rank correlation and key-point precision/recall.

Until such data exists, every accuracy number in this project is **preliminary**.
