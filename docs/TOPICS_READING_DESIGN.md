# Topics and reading material (Wikipedia-backed)

Status: implemented (backend + web Topic/Prepare/Home/Record) · 2026-10-05

Frontend: `frontend/src/api/api.topics.ts`. The Topic step suggests/rerolls via `/topics/suggest` and resolves "My own topic" via `/topics/custom` on Continue (422 shows "did you mean" + related topics). Prepare shows `/topics/{id}/reading-material` with sources and attribution, and stores the version `id` and key points in the session (`readingMaterialId`, `keyPoints`). Record's cue card uses those key points. Home's Today's topic uses `/topics/daily`.

How SpeakWise picks speaking topics and builds the ~15-minute reading material shown on the Prepare step. The source is Wikipedia only (no LLM). Code lives in `backend/app/modules/topics/`, `backend/app/modules/reading/` and `backend/app/integrations/wikipedia/`.

## Goals

| Requirement | How it's met |
|---|---|
| Wikipedia is the only source | Material is extracted from real article text with rule-based (deterministic) cleanup and selection |
| Works for curated **and** user-typed topics | Both are rows in `topics` and go through one pipeline |
| Never re-serve material a user already **recorded** a talk with | A topic has several immutable *versions*; "used" is read from `talk_session.reading_material_id` |
| Fast and polite to Wikipedia | Articles cached in PostgreSQL, curated topics pre-built, batched requests, parallel fetches, circuit breaker |
| Attribution (Wikipedia is CC BY-SA 4.0) | Every version stores the exact revisions it came from, and the API returns an attribution line |

## Architecture

```
Topic page ──► topics module ──────────┐      reading module ◄── Prepare page
  suggest / daily / custom text        │        pick version for user
                                       │        build version (rule-based)
                                       ▼              │
                         integrations/wikipedia ◄─────┘   (cache first)
                                       │
           PostgreSQL: topics · topic_wiki_sources · wiki_articles ·
                       reading_materials · reading_material_sources · talk_session
                                       │  only on cache miss / stale (30 days)
                                       ▼
                         en.wikipedia.org · simple.wikipedia.org
```

## Data model

| Table | Purpose |
|---|---|
| `topics` | `title`, `teaser`, `category_id`, `difficulty` (1–3), `source` (`curated`/`custom`), `normalized_key` (unique), `created_by_user_id`, `is_active` |
| `topic_wiki_sources` | Articles behind a topic, best first: `rank`, `lang` (`en`/`simple`), `page_title` (stored canonical) |
| `wiki_articles` | Cache of parsed articles: `lang`, `page_id`, `title`, `revision_id`, `url`, `description`, `sections` (JSONB, lz4), `word_count`, `fetched_at` |
| `reading_materials` | Immutable versions: `topic_id`, `version_no`, `lang`, `content` (JSONB, lz4: summary, keyPoints, sections), `unit_keys` (pieces used), `word_count`, `read_minutes` |
| `reading_material_sources` | Attribution snapshot per version: `title`, `url` (`?oldid=` permalink), `revision_id`, `lang` |
| `talk_session` (+cols) | `topic_id`, `reading_material_id`, with indexes on `(user_id, topic_id)` and `(user_id, reading_material_id)` |

Text is stored in PostgreSQL JSONB, not files. It's small (~20 KB per version, ~25 KB per article), always read with its row, and must stay consistent with versions and sessions. PostgreSQL compresses it automatically (lz4). Measured: 30 versions plus 82 cached articles take ~2.6 MB. Talk **recordings** are the exception: they belong in object storage with a key in `talk_session`.

## Topic flows

**Curated (random) topics**: a hand-picked bank (`scripts/seed_topics.py`, 30 topics, 2–3 articles each, titles validated against Wikipedia).

- `GET /topics/suggest`: random active curated topic the user **hasn't recorded**, optional `category`, `difficulty`, `exclude_id` (reroll). If all matching topics are recorded, it returns the one recorded longest ago with `all_recorded: true`.
- `GET /topics/daily`: same topic for everyone each day (rotation through curated topics by date in `REPORTING_TIMEZONE`), plus `recorded` for the current user.

**Custom topics**: `POST /topics/custom {text}`

1. **Normalize**: tidy title. The key is lowercase content words with filler removed ("should", "is", "good", "better", "exist"...). "Should cities ban cars?" and "cities BAN cars" share one topic, so re-typing an existing topic costs nothing.
2. **Rate limit**: `CUSTOM_TOPICS_PER_HOUR` new topics per user (counted from the DB, so it works with multiple workers).
3. **Find articles** (2 requests): full-text search plus exact-title lookups for the phrase and its word pairs (broad articles like "Chess" rank low in search for a question). Disambiguation pages, "List of…" pages and short articles (under 400 words) are dropped. The rest are scored on title coverage/precision, snippet coverage, exact match, size and whether the title contains the topic's subject, with penalties for year/ordinal/bracketed titles. Candidates below 65% of the best score are discarded and the top 3 are kept.
4. Nothing relevant: **422** with Wikipedia's "did you mean" and related curated topics. Wikipedia down: **503**. Same text created concurrently: the unique key resolves the race.

## Reading material

`GET /topics/{id}/reading-material` returns a version the user hasn't recorded:

```
recorded = versions this user recorded a talk with (from talk_session)
1. lowest version not in recorded                                  → serve
2. else build next version (advisory lock per topic):
      use only pieces no earlier version used (≥60% new words required)
      not enough material → add 2 related articles (morelike) and retry
                                                                   → save, serve
3. else (exhausted or READING_MAX_VERSIONS reached)
      → version recorded longest ago, is_repeat=true, + 3 related unrecorded topics
```

- It's stable until the user records: reloading Prepare returns the same version. The frontend sends the version `id` when the session is saved.
- `pg_advisory_xact_lock(7301, topic_id)` serialises builds per topic. Concurrent first requests build exactly one version (tested with 6 parallel requests).

**Building a version** (`reading_builder.py`, pure functions):

1. Each section of each source article is a *piece* (`lang:page_id:section_index`).
2. **Score**: topic-keyword relevance (heading ×3, body density) + lead bonus + discussion-heading bonus (*benefits, drawbacks, criticism, impact, ethics, regulation…*) − rank penalty. Reference/link sections, sections under 40 words and list-like sections are excluded.
3. **Assemble**: a lead first, then the best pieces up to `READING_TARGET_WORDS` (2,500 ≈ 13 min). No piece may take more than 35% of the total, and long pieces are cut at a paragraph. Pieces are shown in article order.
4. **Summary**: first sentences of the lead. **Key points**: the first sentence of each section (5–7, 6–35 words).
5. **Headings**: "Parent: Child" for the main article, "Article: Section" for others.

**Beginner** topics use the Simple English counterpart (found via langlinks and stored as a `simple` source row) when it has at least 300 words, else English. Many Simple English articles are short, so most Beginner topics currently fall back to English.

**Caching**: a warm build makes no network calls. Stale (>30 days) or missing articles cost one batched info request per language (revision check: unchanged articles are only re-stamped), then changed articles are fetched in parallel (4 at a time). If Wikipedia is down, cached articles are still used.

## Wikipedia client

`app/integrations/wikipedia/client.py`:
- One pooled `httpx` client and a descriptive `User-Agent` (`WIKIPEDIA_USER_AGENT`)
- `formatversion=2`, `maxlag=5`, gzip
- 8 s timeout, 2 retries with backoff on network errors, 5xx, 429 and `maxlag`
- A circuit breaker opens for 60 s after 5 consecutive failures

| Need | Endpoint |
|---|---|
| Search | `action=query&list=search&srinfo=suggestion&srprop=wordcount\|snippet` |
| Resolve titles, redirects, disambiguation, revision, size, description, Simple English link | `action=query&prop=info\|pageprops\|description\|langlinks&redirects=1` (50 titles per call) |
| Full article text | `action=query&prop=extracts&explaintext=1&exsectionformat=wiki` (one page per call) |
| Related articles | `list=search&srsearch=morelike:<title>` (unquoted; quoting returns nothing) |

## Measured performance (dev machine, India → Wikipedia)

| Case | Time |
|---|---|
| Serve an existing version | ~20–30 ms (gzip: 19.9 KB → 7.1 KB) |
| Build a version, articles cached | 0.0–0.3 s |
| Build a version, nothing cached | 1.2–3.4 s |
| Create a custom topic | 1.0–1.7 s |

## Configuration (`backend/.env`)

| Variable | Default | Meaning |
|---|---|---|
| `WIKIPEDIA_USER_AGENT` | `SpeakWise/1.0 (<repo url>) python-httpx` | Must identify the app with a contact (Wikimedia policy) |
| `WIKI_CACHE_DAYS` | 30 | Re-check cached articles after this many days |
| `READING_TARGET_WORDS` | 2500 | Length of a version |
| `READING_MAX_VERSIONS` | 5 | Distinct versions per topic |
| `CUSTOM_TOPICS_PER_HOUR` | 10 | New custom topics per user per hour |

## Known limitations / next steps

- **Encyclopedic tone.** There's no real for/against structure, only discussion sections when articles have them. An LLM rewriting step could later turn stored versions into balanced briefings without changing this design.
- **Weak secondary sources for custom topics.** Rule-based matching sometimes picks loosely related second or third articles; their sections only get in when relevant.
- **Session saving doesn't exist yet.** The talk-session recording endpoint must store `topic_id` and `reading_material_id` (and check the material belongs to the topic). Until then nothing counts as "recorded".
- **Admin tools.** Manage curated topics and their articles, preview and rebuild versions.
