# Speak Wise — Database Design Document

## 1. Overview

Speak Wise records a user's talk session and analyzes it across audio and video dimensions, then generates an AI-based summary, transcript, and feedback. This document captures the design decisions, entity relationships, DB flow, and the SQL required to create and link every table.

---

## 2. Design Decisions

| # | Decision | Reasoning |
|---|----------|-----------|
| 1 | `talk_session` is the central/core table | Every other table (audio, video, summary) hangs off a single session, owned by a user. |
| 2 | `talk_session_audio`, `talk_session_video`, `talk_session_summary` are all **1:1** with `talk_session` | Each session produces exactly one audio-analysis record, one video-analysis record, and one summary/transcript record — enforced at the DB level using a `UNIQUE` constraint on the foreign key. |
| 3 | `mispronounced_words` and `repeated_words` are **1:many** off `talk_session_audio` | A single session's audio can flag multiple distinct mispronounced words and multiple distinct repeated words, each with its own occurrence count. |
| 4 | `summary` and `transcript` merged into **one table** (`talk_session_summary`) | Since summary and transcript are 1:1 with each other (and both 1:1 with the session), splitting them into two separate tables would only add a redundant join with no benefit. |
| 5 | `ai_feedback` is **1:1** with `talk_session_summary` (not directly with `talk_session`) | Feedback is generated from the summary/transcript, so it's linked via `summary_id`. Since `talk_session_summary` already has a 1:1 link to `talk_session`, linking `ai_feedback` directly to `talk_session_id` as well would duplicate the same relationship — the session can still be reached by joining through summary. |
| 6 | `ai_feedback_alternate_words` is **1:many** off `ai_feedback` | One session generates one feedback record, but that feedback can suggest alternates for multiple filler words — each filler word + its suggested alternate becomes its own row. |
| 7 | `ON DELETE CASCADE` on all foreign keys | Deleting a `talk_session` should clean up all its dependent data (audio, video, summary, feedback, and their child rows) automatically, avoiding orphaned records. |
| 8 | All 1:1 relationships enforced via `UNIQUE` constraint on the FK column | This is what makes it a true 1:1 instead of 1:many at the schema level — the DB will reject a second child row for the same parent. |
| 9 | Word-count fields (`filler_word_count`, `long_pauses_count`, `posture_count`, etc.) live directly on the parent table | These are single scalar values per session, not repeating data, so they don't need their own child tables. |
| 10 | Word-level detail (mispronounced words, repeated words, alternate words) lives in dedicated child tables | These are repeating/variable-length data (a session could have 0 or N of them), which is exactly what a 1:many child table is for. |
| 11 | `topic_name` added to `talk_session_summary` | Captures the topic/subject the user spoke on during the session, alongside its transcript and summary text. Kept nullable since it may be inferred by the AI after summarization and not always guaranteed. |

---

## 3. Entity Relationship (ERD) Flow

```
                                   ┌───────────┐
                                   │   users   │
                                   └─────┬─────┘
                                         │ 1
                                         │
                                         │ many
                                   ┌─────▼──────┐
                                   │ talk_session│
                                   └─────┬──────┘
                     ┌───────────────────┼───────────────────┐
                     │ 1:1               │ 1:1               │ 1:1
              ┌──────▼───────┐   ┌───────▼────────┐   ┌───────▼─────────────┐
              │talk_session_ │   │talk_session_    │   │talk_session_summary │
              │   audio      │   │   video         │   │ (summary+transcript)│
              └──────┬───────┘   └─────────────────┘   └───────┬─────────────┘
           ┌─────────┴─────────┐                                │ 1:1
           │ 1:many             │ 1:many                        │
    ┌──────▼───────┐    ┌───────▼────────┐                ┌─────▼──────┐
    │mispronounced_ │    │ repeated_words │                │ ai_feedback│
    │    words      │    │                │                └─────┬──────┘
    └───────────────┘    └────────────────┘                      │ 1:many
                                                          ┌────────▼─────────────────┐
                                                          │ai_feedback_alternate_words│
                                                          └───────────────────────────┘
```

**Flow narrative:**
1. A `user` starts a `talk_session` (context + score captured at session level).
2. That session generates two parallel analysis streams:
   - **Audio stream** → `talk_session_audio` → child rows in `mispronounced_words` and `repeated_words`.
   - **Video stream** → `talk_session_video` (posture, head movement, hand gestures — all scalar counts, no child tables needed).
3. Once the session ends, a `talk_session_summary` is generated (transcript + summary text, 1:1 with the session).
4. From that summary, an `ai_feedback` record (1:1 with summary) is generated.
5. The feedback expands into multiple `ai_feedback_alternate_words` rows — one per filler word detected, each paired with its suggested alternate.

---

## 4. SQL — Create & Link All Tables

```sql
-- ========================================
-- 1. TALK SESSION (core table, linked to users)
-- ========================================
CREATE TABLE talk_session (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    context     TEXT,
    score       NUMERIC(5,2),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_talk_session_user_id ON talk_session(user_id);


-- ========================================
-- 2. TALK SESSION AUDIO (1:1 with talk_session)
-- ========================================
CREATE TABLE talk_session_audio (
    id                  BIGSERIAL PRIMARY KEY,
    talk_session_id     BIGINT NOT NULL UNIQUE REFERENCES talk_session(id) ON DELETE CASCADE,
    filler_word_count   INTEGER NOT NULL DEFAULT 0,
    long_pauses_count   INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2a. MISPRONOUNCED WORDS (1:many with talk_session_audio)
CREATE TABLE mispronounced_words (
    id                      BIGSERIAL PRIMARY KEY,
    talk_session_audio_id   BIGINT NOT NULL REFERENCES talk_session_audio(id) ON DELETE CASCADE,
    word                    VARCHAR(255) NOT NULL,
    count                   INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_mispronounced_words_audio_id ON mispronounced_words(talk_session_audio_id);

-- 2b. REPEATED WORDS (1:many with talk_session_audio)
CREATE TABLE repeated_words (
    id                      BIGSERIAL PRIMARY KEY,
    talk_session_audio_id   BIGINT NOT NULL REFERENCES talk_session_audio(id) ON DELETE CASCADE,
    word                    VARCHAR(255) NOT NULL,
    count                   INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX idx_repeated_words_audio_id ON repeated_words(talk_session_audio_id);


-- ========================================
-- 3. TALK SESSION VIDEO (1:1 with talk_session)
-- ========================================
CREATE TABLE talk_session_video (
    id                      BIGSERIAL PRIMARY KEY,
    talk_session_id         BIGINT NOT NULL UNIQUE REFERENCES talk_session(id) ON DELETE CASCADE,
    posture_count           INTEGER NOT NULL DEFAULT 0,
    head_movement_count     INTEGER NOT NULL DEFAULT 0,
    hand_gesture_count      INTEGER NOT NULL DEFAULT 0,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- ========================================
-- 4. TALK SESSION SUMMARY (1:1 with talk_session)
--    (summary + transcript merged, since they're 1:1 with each other)
-- ========================================
CREATE TABLE talk_session_summary (
    id                  BIGSERIAL PRIMARY KEY,
    talk_session_id     BIGINT NOT NULL UNIQUE REFERENCES talk_session(id) ON DELETE CASCADE,
    topic_name          VARCHAR(255),
    transcript          TEXT NOT NULL,
    summary_text        TEXT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- ========================================
-- 5. AI FEEDBACK (1:1 with talk_session_summary)
-- ========================================
CREATE TABLE ai_feedback (
    id              BIGSERIAL PRIMARY KEY,
    summary_id      BIGINT NOT NULL UNIQUE REFERENCES talk_session_summary(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 5a. AI FEEDBACK ALTERNATE WORDS (1:many with ai_feedback)
CREATE TABLE ai_feedback_alternate_words (
    id                  BIGSERIAL PRIMARY KEY,
    ai_feedback_id      BIGINT NOT NULL REFERENCES ai_feedback(id) ON DELETE CASCADE,
    filler_word         VARCHAR(255) NOT NULL,
    alternate_word      VARCHAR(255) NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_ai_feedback_alt_words_feedback_id ON ai_feedback_alternate_words(ai_feedback_id);
```

---

## 5. Relationship Summary

```
users (1) ──────────< (many) talk_session
talk_session (1) ──1:1── talk_session_audio
talk_session_audio (1) ──< (many) mispronounced_words
talk_session_audio (1) ──< (many) repeated_words
talk_session (1) ──1:1── talk_session_video
talk_session (1) ──1:1── talk_session_summary   [summary + transcript]
talk_session_summary (1) ──1:1── ai_feedback
ai_feedback (1) ──< (many) ai_feedback_alternate_words
```

---

## 6. Open Question / To Confirm

- `ai_feedback` currently holds only `id`, `summary_id`, and `created_at` — essentially a container/grouping table for the alternate-words list.
  - **Option A (current design):** Keep it as a separate table — useful if you plan to add more session-level AI fields later (e.g. `overall_feedback_score`, `tone_analysis`, `confidence_score`).
  - **Option B (simpler):** Fold `ai_feedback_alternate_words` directly onto `talk_session_summary` and drop the `ai_feedback` table entirely, since right now it adds a join with no extra data of its own.
  - Decide based on whether AI feedback is expected to grow beyond just the alternate-words list.
