// Report validation tests. FIXTURE ONLY: the objects below are structural test data built for
// these checks; they are not real analysis results and are never shown in the app.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { readEnvelope, sha256Hex } from '../src/desktop/report.ts'

const MATERIAL = 'Exact reading text.'
const metric = (status: string, value: number | null) => ({ value, unit: 'count', status, note: null })

async function fixture() {
  const sha = await sha256Hex(MATERIAL)
  const expected = { sessionId: 'sw-test-1', topic: 'Test topic', materialSha256: sha }
  const report = {
    session_metadata: { session_id: 'pipe-1', schema_version: '1.0.0', topic: 'Test topic', reading_material_sha256: sha },
    input_validation: {},
    transcription: { status: 'ok', text: '' },
    audio_analysis: {
      status: 'ok',
      words_per_minute: metric('ok', 0), // a measured zero is valid
      speaking_time_s: metric('unavailable', null),
    },
    video_analysis: { status: 'warning', face_visible_pct: metric('warning', 50) },
    context_evaluation: { status: 'failed', topic_relevance: metric('failed', null) },
    improvement_suggestions: [],
    warnings: [],
    errors: [],
  }
  return { expected, report, envelope: { status: 'done', session_id: 'sw-test-1', report } }
}

test('accepts a well-formed report for the active session', async () => {
  const { expected, envelope } = await fixture()
  assert.equal(readEnvelope(envelope, expected).kind, 'done')
})

test('sha256 matches Python hashlib for the same UTF-8 text', async () => {
  // python -c "import hashlib;print(hashlib.sha256('abc'.encode()).hexdigest())"
  assert.equal(await sha256Hex('abc'), 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad')
})

test('pending, processing and error states', async () => {
  const { expected } = await fixture()
  assert.equal(readEnvelope({ status: 'pending', session_id: 'sw-test-1' }, expected).kind, 'pending')
  assert.equal(readEnvelope({ status: 'processing', session_id: 'sw-test-1' }, expected).kind, 'processing')
  const failed = readEnvelope({ status: 'error', session_id: 'sw-test-1', error: 'boom' }, expected)
  assert.deepEqual(failed, { kind: 'failed', message: 'boom' })
})

test('rejects mismatched session, topic and reading material', async () => {
  const { expected, envelope, report } = await fixture()
  assert.equal(readEnvelope({ ...envelope, session_id: 'other' }, expected).kind, 'invalid')
  const wrongTopic = { ...report, session_metadata: { ...report.session_metadata, topic: 'Other' } }
  assert.equal(readEnvelope({ ...envelope, report: wrongTopic }, expected).kind, 'invalid')
  assert.equal(readEnvelope(envelope, { ...expected, materialSha256: 'x' }).kind, 'invalid')
})

test('rejects malformed reports and metrics', async () => {
  const { expected, envelope, report } = await fixture()
  assert.equal(readEnvelope('nope', expected).kind, 'invalid')
  assert.equal(readEnvelope({ ...envelope, report: { session_metadata: report.session_metadata } }, expected).kind, 'invalid')
  const zeroForMissing = { ...report, audio_analysis: { ...report.audio_analysis, speaking_time_s: metric('unavailable', 0) } }
  assert.equal(readEnvelope({ ...envelope, report: zeroForMissing }, expected).kind, 'invalid')
  const missingValue = { ...report, audio_analysis: { ...report.audio_analysis, words_per_minute: metric('ok', null) } }
  assert.equal(readEnvelope({ ...envelope, report: missingValue }, expected).kind, 'invalid')
  const badStatus = { ...report, audio_analysis: { ...report.audio_analysis, words_per_minute: metric('great', 1) } }
  assert.equal(readEnvelope({ ...envelope, report: badStatus }, expected).kind, 'invalid')
})
