"""Map a FinalReport onto the existing talk_session* / ai_feedback tables.

Pure data mapping: returns plain dicts keyed by table, with no SQLAlchemy and no
database access, so it is safe to run and test anywhere. A repository function
can insert the rows inside one transaction (see docs/ANALYSIS_INTEGRATION.md).

Assumptions to confirm (the columns' exact meaning isn't documented):
  talk_session.context            <- topic
  talk_session.score              <- rule-based overall score (0-100)
  talk_session_audio.*_count      <- filler / long-pause event counts
  talk_session_video.posture_count       <- slouch + lean events
  talk_session_video.head_movement_count <- look-away events
  talk_session_video.hand_gesture_count  <- fidget + face-touch events
  repeated_words                  <- repeated-word events grouped by word
  mispronounced_words             <- empty (pronunciation isn't analysed yet)
  ai_feedback_alternate_words     <- filler -> first suggested alternative
Everything that doesn't fit these tables (events, scores, segments, full feedback)
goes in `analysis_json`, intended for one JSONB column on a new table.
"""
from collections import Counter
from typing import Any

from app.analysis.schemas import FinalReport


def to_db_payload(final: FinalReport) -> dict[str, Any]:
    report, fb = final.report, final.feedback
    count = lambda *types: sum(e.type in types for e in report.events)  # noqa: E731

    repeats = Counter(e.meta.get("text", "") for e in report.events if e.type == "repetition")
    return {
        "talk_session": {"context": final.topic, "score": report.scores.overall},
        "talk_session_audio": {
            "filler_word_count": count("filler"),
            "long_pauses_count": count("long_pause"),
        },
        "repeated_words": [{"word": w, "count": c} for w, c in repeats.most_common() if w],
        "mispronounced_words": [],
        "talk_session_video": {
            "posture_count": count("slouch", "lean"),
            "head_movement_count": count("look_away"),
            "hand_gesture_count": count("fidget", "face_touch"),
        },
        "talk_session_summary": {
            "topic_name": final.topic,
            "transcript": report.transcript or "",
            "summary_text": fb.summary,
        },
        "ai_feedback_alternate_words": [
            {"filler_word": s.word, "alternate_word": s.alternatives[0]}
            for s in fb.vocabulary.filler_alternatives if s.alternatives
        ],
        "analysis_json": final.model_dump(mode="json"),
    }
