import { defaultPreferences, deviceOptions, durations } from '../data/mockData'
import type { DeviceOptions, DurationMin, Preferences } from '../types'

export const getDefaultPreferences = (): Preferences => ({ ...defaultPreferences })

/** Fallback device list. On web the real list comes from enumerateDevices(). */
export const getMockDeviceOptions = (): DeviceOptions => deviceOptions

export const getDurations = (): readonly DurationMin[] => durations
