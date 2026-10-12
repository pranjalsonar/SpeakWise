const assert = require('node:assert/strict')
const { test } = require('node:test')
const { checkStartInput } = require('../lib/validate.cjs')

const good = { topic: 'Climate change', readingMaterial: 'Some text.', durationS: 180 }

test('accepts the three supported durations', () => {
  for (const durationS of [60, 180, 300]) assert.equal(checkStartInput({ ...good, durationS }), null)
})

test('rejects other durations and missing fields', () => {
  assert.match(checkStartInput({ ...good, durationS: 120 }), /Duration/)
  assert.match(checkStartInput({ ...good, topic: ' ' }), /topic/)
  assert.match(checkStartInput({ ...good, readingMaterial: '' }), /reading/)
  assert.match(checkStartInput(null), /Invalid/)
})
