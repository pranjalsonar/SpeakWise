// IPC input validation for session:start.
const DURATIONS = [60, 180, 300]

function checkStartInput(input) {
  if (!input || typeof input !== 'object') return 'Invalid session input.'
  const { topic, readingMaterial, durationS } = input
  if (typeof topic !== 'string' || !topic.trim() || topic.length > 300) return 'Invalid topic.'
  if (typeof readingMaterial !== 'string' || !readingMaterial.trim() || readingMaterial.length > 200000) {
    return 'Invalid reading material.'
  }
  if (!DURATIONS.includes(durationS)) return 'Duration must be 60, 180 or 300 seconds.'
  return null
}

module.exports = { checkStartInput, DURATIONS }
