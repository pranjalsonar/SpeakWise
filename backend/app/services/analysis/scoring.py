"""Turn raw measurements into 0-100 scores, an overall grade, a summary and tips.

Ported from the POC's scoring.py; the summary is personalised with the speaker's first name.
"""
import numpy as np

WEIGHTS = {
    "fillers": 15, "pauses": 10, "repetition": 10, "clarity": 10, "pace": 10,
    "eye_contact": 15, "body_language": 10, "confidence": 5, "context": 15,
}
LABELS = {
    "fillers": "Filler words", "pauses": "Pauses", "repetition": "Word repetition",
    "clarity": "Clarity (mumbling)", "pace": "Speaking pace", "eye_contact": "Eye contact",
    "body_language": "Body language", "confidence": "Confidence", "context": "Context match",
}


def _clip(x):
    return float(np.clip(x, 0, 100))


def compute_scores(speech, video, context):
    minutes = max(speech["duration_sec"] / 60.0, 1e-6)
    s = {}

    # Fillers: <= 2/min is excellent, 15+/min scores 0.
    s["fillers"] = _clip(100 - (speech["filler_per_min"] - 2) * (100 / 13))

    # Pauses: long pauses hurt; a few short pauses are healthy, too many is choppy.
    long_pm = speech["long_pause_count"] / minutes
    short_pm = speech["short_pause_count"] / minutes
    pause = 100 - 22 * long_pm
    if short_pm > 18:
        pause -= (short_pm - 18) * 3
    if speech["opening_silence_sec"] > 4:
        pause -= 10
    s["pauses"] = _clip(pause)

    # Repetition: stutter-repeats per minute + overused words + repeated phrases.
    s["repetition"] = _clip(
        100 - 12 * speech["stutter_count"] / minutes
        - 6 * len(speech["overused_words"]) - 4 * len(speech["repeated_phrases"])
    )

    s["clarity"] = _clip(100 - (100 - speech["clarity_pct"]) * 4)

    # Pace: 120-160 wpm is ideal.
    wpm = speech["wpm"]
    if wpm == 0:
        s["pace"] = 0.0
    elif wpm < 120:
        s["pace"] = _clip(100 - (120 - wpm) * 1.6)
    elif wpm > 160:
        s["pace"] = _clip(100 - (wpm - 160) * 1.6)
    else:
        s["pace"] = 100.0

    # Eye contact: 75%+ of the time is excellent.
    s["eye_contact"] = _clip(video["eye_contact_pct"] / 75 * 100)

    body = 100.0
    body -= 0.6 * video["slouch_pct"]
    body -= 0.3 * video["shoulder_tilt_pct"]
    body -= 0.5 * video["arms_crossed_pct"]
    body -= 4 * video["face_touch_count"] / minutes
    body -= 0.8 * video["fidget_pct"]
    body -= 0.4 * video["excess_head_movement_pct"]
    body -= 0.5 * max(0.0, 90 - video["face_visible_pct"])
    if video["hands_visible_pct"] > 30 and video["gesture_pct"] < 5:
        body -= 5   # hands visible but completely static
    s["body_language"] = _clip(body)

    # Confidence: blend of visual and vocal signals.
    pitch = speech["pitch_variation_semitones"]
    voice_variety = 100 if 2 <= pitch <= 6 else _clip(40 + pitch * 30) if pitch < 2 else 80
    blink_pen = max(0.0, video["blinks_per_min"] - 30) * 2
    loud = speech["loudness_dbfs"]
    volume = 100 if loud > -30 else _clip(100 - (-30 - loud) * 5)
    s["confidence"] = _clip(
        0.25 * s["eye_contact"] + 0.20 * s["body_language"] + 0.15 * voice_variety
        + 0.15 * volume + 0.15 * s["fillers"] + 0.10 * (100 - video["tension_pct"])
        - blink_pen - 0.15 * video["looking_down_pct"]
    )
    s["voice_variety"] = voice_variety
    s["volume"] = volume

    s["context"] = _clip(context["score"])

    overall = sum(s[k] * w for k, w in WEIGHTS.items()) / sum(WEIGHTS.values())
    s["overall"] = round(overall, 1)
    return {k: round(v, 1) for k, v in s.items()}


def grade(score):
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 55:
        return "Fair"
    return "Needs work"


def build_tips(speech, video, context, scores):
    tips = []
    if scores["fillers"] < 80:
        top = sorted(speech["filler_breakdown"].items(), key=lambda kv: -kv[1])[:3]
        names = ", ".join(f'"{w}" ({c})' for w, c in top)
        tips.append((scores["fillers"],
                     f"You used {speech['filler_count']} filler words "
                     f"({speech['filler_per_min']}/min), mostly {names}. Replace them with a "
                     "silent one-second pause - silence sounds more confident than 'um'."))
    if scores["pauses"] < 80:
        tips.append((scores["pauses"],
                     f"{speech['long_pause_count']} long pauses (longest "
                     f"{speech['longest_pause_sec']}s). Plan 3-4 key points before you start "
                     "so you always know what comes next."))
    if scores["repetition"] < 80:
        bits = []
        if speech["overused_words"]:
            bits.append("overused: " + ", ".join(
                f"'{o['word']}' x{o['count']}" for o in speech["overused_words"][:3]))
        if speech["stutter_count"]:
            bits.append(f"{speech['stutter_count']} restarts like 'I I' or 'the the'")
        tips.append((scores["repetition"],
                     "Vary your vocabulary (" + "; ".join(bits) + "). Use synonyms and "
                     "finish each sentence before starting the next."))
    if scores["clarity"] < 80:
        tips.append((scores["clarity"],
                     f"{speech['mumbled_count']} words were unclear or too quiet. Open your "
                     "mouth more, slow down slightly and keep your volume up at sentence ends."))
    if scores["pace"] < 85:
        direction = "slow down" if speech["wpm"] > 160 else "speed up a little"
        tips.append((scores["pace"],
                     f"Your pace was {speech['wpm']:.0f} words/min; aim for 120-160, so "
                     f"{direction}."))
    if scores["eye_contact"] < 80:
        tips.append((scores["eye_contact"],
                     f"Eye contact only {video['eye_contact_pct']:.0f}% of the time"
                     + (f" (looking down {video['looking_down_pct']:.0f}%)"
                        if video["looking_down_pct"] > 15 else "")
                     + ". Look into the camera lens, not at your own image on screen."))
    if scores["body_language"] < 80:
        issues = []
        if video["slouch_pct"] > 20:
            issues.append(f"slouching {video['slouch_pct']:.0f}% of the time")
        if video["shoulder_tilt_pct"] > 20:
            issues.append("leaning to one side")
        if video["face_touch_count"]:
            issues.append(f"touching your face {video['face_touch_count']} times")
        if video["arms_crossed_pct"] > 10:
            issues.append("crossed arms")
        if video["fidget_pct"] > 10:
            issues.append("fidgety hand movements")
        if video["face_visible_pct"] < 90:
            issues.append("moving out of frame")
        tips.append((scores["body_language"],
                     "Body language: " + (", ".join(issues) or "posture could be more open")
                     + ". Sit or stand tall, shoulders level, hands relaxed and visible."))
    if scores["confidence"] < 75:
        extra = []
        if speech["pitch_variation_semitones"] < 2:
            extra.append("your voice was fairly monotone - vary pitch to stress key words")
        if speech["loudness_dbfs"] < -30:
            extra.append("speak louder")
        if video["blinks_per_min"] > 30:
            extra.append("frequent blinking suggests nervousness - slow your breathing")
        tips.append((scores["confidence"],
                     "Project more confidence: " + ("; ".join(extra) or
                     "steady eye contact, open posture and a firm voice") + "."))
    if scores["context"] < 70:
        missed = context.get("missed_points") or []
        tips.append((scores["context"],
                     f"Context match was {context['score']:.0f}% (target 70%). Stay on the "
                     "assigned topic and use facts from the reading"
                     + (": e.g. " + "; ".join(missed[:2]) if missed else "") + "."))
    tips.sort(key=lambda t: t[0])
    if not tips:
        tips.append((100, "Great job! Try a longer duration or a harder topic next time."))
    return [t for _, t in tips]


def build_summary(first_name, topic, speech, video, context, scores):
    parts = {k: scores[k] for k in WEIGHTS}
    best = max(parts, key=parts.get)
    worst = min(parts, key=parts.get)
    who = f"{first_name}, you" if first_name else "You"
    return (
        f"{who} spoke about {topic} for {speech['duration_sec'] / 60:.1f} min "
        f"({speech['word_count']} words, {speech['wpm']:.0f} wpm) and scored "
        f"{scores['overall']:.0f}/100 ({grade(scores['overall'])}). "
        f"Your strongest area was {LABELS[best].lower()} ({parts[best]:.0f}) and the "
        f"biggest opportunity is {LABELS[worst].lower()} ({parts[worst]:.0f}). "
        f"Your speech was {context['score']:.0f}% in context with the topic "
        f"({'passed' if context['passed'] else 'below'} the 70% target), with eye contact "
        f"{video['eye_contact_pct']:.0f}% of the time and {speech['filler_count']} filler words."
    )
