// Builds mobile/src/content/articles.json from content/articles/*.md and validates every article.
// The same JSON is read by the backend (LLM judge + context match).
//
// Usage: node content/build-articles.mjs
//
// Article file format:
//   ---
//   id: why-we-need-sleep
//   title: Why We Need Sleep
//   category: Science
//   level: Easy
//   as_of: 2026-11            (optional)
//   demo: true                (optional – skips the word-count rule, used for the demo article)
//   summary: One or two sentences.
//   points:
//   - Talking point one
//   - Talking point two
//   ---
//   Markdown body...
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const SRC_DIR = join(HERE, 'articles');
const OUT_FILE = join(HERE, '..', 'mobile', 'src', 'content', 'articles.json');
// Copy for the backend, so it can be deployed (e.g. in Docker) without the mobile folder.
const BACKEND_COPY = join(HERE, '..', 'backend', 'content', 'articles.json');

const CATEGORIES = ['Science', 'Space', 'History', 'Current Affairs', 'Literature', 'Fiction & Myth'];
const MIN_WORDS = 600;
const MAX_WORDS = 700;
const READING_WPM = 180; // relaxed reading speed for easy English

function parse(file, text) {
  const m = text.replace(/\r\n/g, '\n').match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
  if (!m) throw new Error(`${file}: missing --- front matter ---`);
  const meta = { points: [] };
  for (const line of m[1].split('\n')) {
    if (!line.trim()) continue;
    const point = line.match(/^-\s+(.*)$/);
    if (point) {
      meta.points.push(point[1].trim());
      continue;
    }
    const kv = line.match(/^(\w+):\s*(.*)$/);
    if (!kv) throw new Error(`${file}: cannot read front matter line "${line}"`);
    if (kv[1] !== 'points') meta[kv[1]] = kv[2].trim();
  }
  return { meta, body: m[2].trim() };
}

const countWords = (s) => s.replace(/[#*_>`-]/g, ' ').split(/\s+/).filter(Boolean).length;

const errors = [];
const articles = [];
const ids = new Set();

for (const file of readdirSync(SRC_DIR).filter((f) => f.endsWith('.md')).sort()) {
  try {
    const { meta, body } = parse(file, readFileSync(join(SRC_DIR, file), 'utf8'));
    for (const key of ['id', 'title', 'category', 'level', 'summary']) {
      if (!meta[key]) errors.push(`${file}: missing "${key}"`);
    }
    if (!CATEGORIES.includes(meta.category)) errors.push(`${file}: unknown category "${meta.category}"`);
    if (ids.has(meta.id)) errors.push(`${file}: duplicate id "${meta.id}"`);
    ids.add(meta.id);
    if (meta.points.length < 4) errors.push(`${file}: needs at least 4 talking points`);

    const words = countWords(body);
    const isDemo = meta.demo === 'true';
    if (!isDemo && (words < MIN_WORDS || words > MAX_WORDS)) {
      errors.push(`${file}: ${words} words (expected ${MIN_WORDS}-${MAX_WORDS})`);
    }
    articles.push({
      id: meta.id,
      title: meta.title,
      category: meta.category,
      level: meta.level,
      word_count: words,
      read_minutes: Math.max(1, Math.round(words / READING_WPM)),
      summary: meta.summary,
      talking_points: meta.points,
      body,
      as_of: meta.as_of || null,
    });
  } catch (e) {
    errors.push(e.message);
  }
}

if (errors.length) {
  console.error(`✗ ${errors.length} problem(s):\n  ` + errors.join('\n  '));
  process.exit(1);
}

// Bump the version whenever content changes so installed apps re-seed their SQLite topics.
let version = 1;
try {
  const prev = JSON.parse(readFileSync(OUT_FILE, 'utf8'));
  const same = JSON.stringify(prev.articles) === JSON.stringify(articles);
  version = same ? prev.version : (prev.version || 0) + 1;
} catch {
  // first build
}

const json = JSON.stringify({ version, articles }, null, 2) + '\n';
writeFileSync(OUT_FILE, json, 'utf8');
mkdirSync(dirname(BACKEND_COPY), { recursive: true });
writeFileSync(BACKEND_COPY, json, 'utf8');
const byCat = CATEGORIES.map((c) => `${c}: ${articles.filter((a) => a.category === c).length}`).join(', ');
console.log(`✓ ${articles.length} articles (version ${version}) → ${OUT_FILE}\n  ${byCat}`);
for (const a of articles) console.log(`  ${String(a.word_count).padStart(4)} words  ${a.id}`);
