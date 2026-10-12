// Converts generated test media (ffmpeg test pattern + tone, not a real recording) to MP4.
const assert = require('node:assert/strict')
const { execFileSync } = require('node:child_process')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const { test } = require('node:test')
const ffmpeg = require('ffmpeg-static')
const { toValidatedMp4 } = require('../lib/media.cjs')

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'sw-media-test-'))
const gen = (out, seconds, withAudio = true) =>
  execFileSync(ffmpeg, ['-y', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i', `testsrc=size=320x240:rate=15:duration=${seconds}`,
    ...(withAudio ? ['-f', 'lavfi', '-i', `sine=frequency=440:duration=${seconds}`] : []),
    '-c:v', 'libvpx', ...(withAudio ? ['-c:a', 'libopus'] : []), out])

test.after(() => fs.rmSync(dir, { recursive: true, force: true }))

test('converts WebM with audio + video into a validated MP4', async () => {
  const input = path.join(dir, 'in.webm')
  gen(input, 4)
  const info = await toValidatedMp4(input, path.join(dir, 'out.mp4'), false)
  assert.ok(info.hasAudio && info.hasVideo)
  assert.ok(Math.abs(info.durationS - 4) < 0.5)
})

test('rejects a recording without audio', async () => {
  const input = path.join(dir, 'silent.webm')
  gen(input, 4, false)
  await assert.rejects(toValidatedMp4(input, path.join(dir, 'silent.mp4'), false), /no audio/)
})

test('rejects a recording shorter than 3 seconds', async () => {
  const input = path.join(dir, 'short.webm')
  gen(input, 1)
  await assert.rejects(toValidatedMp4(input, path.join(dir, 'short.mp4'), false), /too short/)
})

test('rejects garbage input', async () => {
  const input = path.join(dir, 'junk.webm')
  fs.writeFileSync(input, 'not a video')
  await assert.rejects(toValidatedMp4(input, path.join(dir, 'junk.mp4'), false), /could not be converted/)
})
