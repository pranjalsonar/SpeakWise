// Turns whatever MediaRecorder produced into a validated MP4 (H.264 + AAC) using the
// packaged ffmpeg-static binary, so the result does not depend on the machine's codecs.
const { execFile } = require('node:child_process')
const fs = require('node:fs')
const ffmpegPath = require('ffmpeg-static')

function run(args) {
  return new Promise((resolve) => {
    execFile(ffmpegPath, args, { windowsHide: true, maxBuffer: 16 * 1024 * 1024 }, (error, _out, stderr) =>
      resolve({ ok: !error, stderr: String(stderr) }),
    )
  })
}

/** Parses `ffmpeg -i` output: streams present and container duration. */
async function probe(file) {
  const { stderr } = await run(['-hide_banner', '-i', file])
  const m = stderr.match(/Duration: (\d+):(\d+):(\d+(?:\.\d+)?)/)
  return {
    hasVideo: /Stream #.*Video:/.test(stderr),
    hasAudio: /Stream #.*Audio:/.test(stderr),
    durationS: m ? Number(m[1]) * 3600 + Number(m[2]) * 60 + Number(m[3]) : null,
  }
}

class MediaError extends Error {}

async function toValidatedMp4(inputPath, outputPath, isMp4) {
  if (!ffmpegPath || !fs.existsSync(ffmpegPath)) throw new MediaError('The packaged ffmpeg binary is missing.')
  const transcode = ['-y', '-hide_banner', '-i', inputPath, '-c:v', 'libx264', '-preset', 'veryfast',
    '-crf', '23', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', outputPath]
  // Native MP4 from MediaRecorder is usually fragmented; a stream copy fixes the index cheaply.
  let result = isMp4
    ? await run(['-y', '-hide_banner', '-i', inputPath, '-c', 'copy', '-movflags', '+faststart', outputPath])
    : await run(transcode)
  if (!result.ok && isMp4) result = await run(transcode)
  if (!result.ok) throw new MediaError('The recording could not be converted to MP4.')

  const info = await probe(outputPath)
  if (!info.hasVideo) throw new MediaError('The recording has no video track.')
  if (!info.hasAudio) throw new MediaError('The recording has no audio track. Check the microphone.')
  if (!info.durationS || info.durationS < 3) throw new MediaError('The recording is too short to analyse (under 3 seconds).')
  return info
}

module.exports = { toValidatedMp4, MediaError }
