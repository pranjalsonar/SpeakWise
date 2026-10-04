import { useEffect, useState } from 'react'
import { preferencesService } from '@/core/services'
import type { DeviceOptions } from '@/core/types'

/**
 * Camera/microphone names from enumerateDevices(). Browsers hide labels until the
 * user grants camera access, so it falls back to the mock list until then.
 */
export function useMediaDevices(): DeviceOptions {
  const [devices, setDevices] = useState<DeviceOptions>(preferencesService.getMockDeviceOptions)

  useEffect(() => {
    let active = true
    const load = async () => {
      if (!navigator.mediaDevices?.enumerateDevices) return
      const list = await navigator.mediaDevices.enumerateDevices()
      const labelled = (kind: MediaDeviceKind) =>
        list.filter((d) => d.kind === kind && d.label).map((d) => d.label)
      const cameras = labelled('videoinput')
      const microphones = labelled('audioinput')
      if (active && (cameras.length || microphones.length)) {
        setDevices((prev) => ({
          cameras: cameras.length ? cameras : prev.cameras,
          microphones: microphones.length ? microphones : prev.microphones,
        }))
      }
    }
    load().catch(() => undefined)
    return () => {
      active = false
    }
  }, [])

  return devices
}
