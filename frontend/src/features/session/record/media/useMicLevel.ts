import { useEffect, useState } from 'react'

const BAR_COUNT = 10
const MIN_PCT = 15
const IDLE_BARS = Array.from({ length: BAR_COUNT }, () => MIN_PCT)

/**
 * 10 bar heights (15–100%) from the live microphone level (Web Audio AnalyserNode).
 * Without a stream (no permission / demo mode) the bars animate gently so the UI still reads.
 */
export function useMicLevel(stream: MediaStream | null, active: boolean): number[] {
  const [bars, setBars] = useState<number[]>(IDLE_BARS)

  useEffect(() => {
    if (!active) return

    const audioTrack = stream?.getAudioTracks()[0]
    const AudioCtx = window.AudioContext
    if (!stream || !audioTrack || !AudioCtx) {
      const id = window.setInterval(
        () => setBars(IDLE_BARS.map(() => MIN_PCT + Math.round(Math.random() * 45))),
        200,
      )
      return () => window.clearInterval(id)
    }

    const ctx = new AudioCtx()
    const source = ctx.createMediaStreamSource(stream)
    const analyser = ctx.createAnalyser()
    analyser.fftSize = 64
    source.connect(analyser)
    const data = new Uint8Array(analyser.frequencyBinCount)

    const id = window.setInterval(() => {
      analyser.getByteFrequencyData(data)
      const step = Math.floor(data.length / BAR_COUNT) || 1
      setBars(
        IDLE_BARS.map((_, i) => {
          const value = data[i * step] ?? 0
          return Math.max(MIN_PCT, Math.min(100, Math.round((value / 255) * 100)))
        }),
      )
    }, 120)

    return () => {
      window.clearInterval(id)
      source.disconnect()
      void ctx.close()
    }
  }, [stream, active])

  return active ? bars : IDLE_BARS
}
