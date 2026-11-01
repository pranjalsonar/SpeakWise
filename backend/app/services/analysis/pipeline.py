"""End-to-end analysis of one recording, producing the report the app displays."""
import logging
from concurrent.futures import ThreadPoolExecutor

from app.core.config import settings
from app.services.analysis import asr, llm
from app.services.analysis.context import context_match
from app.services.analysis.media import SAMPLE_RATE, MediaError, load_audio, speech_audio_file
from app.services.analysis.scoring import (LABELS, WEIGHTS, build_summary, build_tips, compute_scores,
                                           grade)
from app.services.analysis.speech import analyze_speech
from app.services.analysis.vision import analyze_video, empty_video_metrics
from app.services.content import plain_text

log = logging.getLogger(__name__)

REPORT_VERSION = 1
MIN_WORDS = 5


class AnalysisError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _coach_input(first_name, article, speech, video, context, scores):
    top_fillers = sorted(speech["filler_breakdown"].items(), key=lambda kv: -kv[1])[:3]
    return {
        "first_name": first_name or "there",
        "topic": article["title"],
        "duration_min": round(speech["duration_sec"] / 60, 1),
        "overall_score": scores["overall"],
        "grade": grade(scores["overall"]),
        "scores_out_of_100": {LABELS[k]: scores[k] for k in WEIGHTS},
        "filler_words": {"count": speech["filler_count"], "per_minute": speech["filler_per_min"],
                         "most_used": dict(top_fillers)},
        "pauses": {"long": speech["long_pause_count"], "short": speech["short_pause_count"],
                   "longest_sec": speech["longest_pause_sec"]},
        "pace_wpm": speech["wpm"],
        "clarity_pct": speech["clarity_pct"],
        "repeated_words": [o["word"] for o in speech["overused_words"][:3]],
        "eye_contact_pct": video["eye_contact_pct"],
        "looking_down_pct": video["looking_down_pct"],
        "slouch_pct": video["slouch_pct"],
        "face_touches": video["face_touch_count"],
        "gesturing_pct": video["gesture_pct"],
        "pitch_variation_semitones": speech["pitch_variation_semitones"],
        "context_match_pct": context["score"],
        "content_covered": context.get("covered_points", []),
        "content_missed": context.get("missed_points", []),
    }


def run_analysis(video_path: str, article: dict, first_name: str | None, progress=lambda step, pct: None) -> dict:
    warnings = []

    progress("preparing", 0.05)
    try:
        audio = load_audio(video_path)
    except MediaError as exc:
        raise AnalysisError(exc.code, exc.message) from exc
    audio_file = speech_audio_file(audio)

    progress("analysing", 0.15)
    with ThreadPoolExecutor(max_workers=1) as pool:
        asr_future = pool.submit(asr.transcribe, audio_file)
        try:
            video = analyze_video(video_path)
        except Exception:
            log.exception("Video analysis failed")
            video = empty_video_metrics()
            warnings.append("Video analysis failed, so body-language scores are not reliable.")
        progress("transcribing", 0.55)
        try:
            heard = asr_future.result()
        except asr.ASRError as exc:
            msg = ("The speech service is busy right now. Please try again in a minute."
                   if exc.code == "rate_limited" else "The speech service is unavailable right now.")
            raise AnalysisError(exc.code, msg) from exc
    if video["frames_analyzed"] and video["face_visible_pct"] < 20:
        warnings.append("Your face was hard to see. Face the camera in good light for accurate results.")
    if heard["errors"]:
        warnings.append("One speech service was unavailable; results used " + " + ".join(heard["providers"]) + ".")

    words = heard["words"]
    if len(words) < MIN_WORDS:
        raise AnalysisError("no_speech", "We couldn't hear enough speech. Speak clearly and a bit louder, then try again.")

    progress("measuring", 0.65)
    speech = analyze_speech(heard["transcript"], words, audio, SAMPLE_RATE)

    progress("checking_content", 0.75)
    material = plain_text(article["body"])
    judgement = None
    try:
        judgement = llm.judge_relevance(article["title"], material, heard["transcript"])
    except llm.LLMError as exc:
        log.warning("LLM judge unavailable: %s", exc)
    context = context_match(article["title"], material, heard["transcript"], judgement)

    progress("scoring", 0.85)
    scores = compute_scores(speech, video, context)

    progress("writing_feedback", 0.9)
    coach = None
    try:
        coach = llm.coach_feedback(_coach_input(first_name, article, speech, video, context, scores))
    except llm.LLMError as exc:
        log.warning("Coach feedback unavailable: %s", exc)

    return {
        "version": REPORT_VERSION,
        "topic": {"id": article["id"], "title": article["title"], "category": article["category"]},
        "first_name": first_name,
        "scores": scores,
        "grade": grade(scores["overall"]),
        "labels": LABELS,
        "weights": WEIGHTS,
        "summary": build_summary(first_name, article["title"], speech, video, context, scores),
        "coach": coach,
        "tips": build_tips(speech, video, context, scores),
        "speech": speech,
        "video": video,
        "context": context,
        "providers": {"asr": heard["providers"],
                      "judge": judgement["model"] if judgement else None,
                      "coach": coach["model"] if coach else None},
        "warnings": warnings,
    }
