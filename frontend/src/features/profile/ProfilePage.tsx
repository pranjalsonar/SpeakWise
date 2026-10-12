import { Pen } from 'lucide-react'
import { useEffect, useState } from 'react'
import * as usersApi from '@/api/api.users'
import { getAccessToken } from '@/api/authToken'
import { AppShell } from '@/components/layout/AppShell'
import { Avatar } from '@/components/ui/Avatar'
import { Button } from '@/components/ui/Button'
import { Chip } from '@/components/ui/Chip'
import { SegmentedControl } from '@/components/ui/SegmentedControl'
import { Select } from '@/components/ui/Select'
import { Toggle } from '@/components/ui/Toggle'
import { useAuth, useCurrentUser } from '@/context/AuthContext'
import { usePreferences } from '@/context/PreferencesContext'
import { useToast } from '@/context/ToastContext'
import { preferencesService } from '@/core/services'
import type { ReadingTextSize } from '@/core/types'
import { useLogout } from '@/hooks/useLogout'
import { useIsDesktop } from '@/hooks/useMediaQuery'
import { useMediaDevices } from '@/hooks/useMediaDevices'
import { EditProfileDialog } from './EditProfileDialog'
import { PreferenceRow } from './PreferenceRow'
import './ProfilePage.css'

const TEXT_SIZES: readonly ReadingTextSize[] = ['Small', 'Medium', 'Large']

/** "2026-10-04T…" → "Oct 2026" */
const formatJoined = (iso: string) =>
  new Date(iso).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })

export function ProfilePage() {
  const user = useCurrentUser()
  const { updateUser } = useAuth()
  const onLogout = useLogout()
  // Only backend accounts have a token; mock-registered users can't load or edit a profile.
  const hasAccount = getAccessToken() !== null
  const [editOpen, setEditOpen] = useState(false)
  const [editKey, setEditKey] = useState(0)
  const isDesktop = useIsDesktop()
  const { showToast } = useToast()
  const { preferences, updatePreferences } = usePreferences()
  const devices = useMediaDevices()

  // Show the latest details from the server (an admin or another device may have changed them).
  // A 401 here signs the user out via AuthProvider, so other errors just keep the saved details.
  useEffect(() => {
    if (!hasAccount) return
    let cancelled = false
    usersApi
      .getMyProfile()
      .then((fresh) => {
        if (!cancelled) updateUser(fresh)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [hasAccount, updateUser])

  const openEdit = () => {
    if (!hasAccount) {
      showToast('Log in with your SpeakWise account to edit your profile.')
      return
    }
    setEditKey((k) => k + 1) // fresh form each time
    setEditOpen(true)
  }

  const editButton = (
    <Button variant="secondary" iconLeft={<Pen size={16} />} block={!isDesktop} onClick={openEdit}>
      Edit profile
    </Button>
  )

  return (
    <AppShell mobileTitle="Profile" mobileAvatar={false}>
      <div className="profile-page">
        <h1 className="profile-page__title">Profile</h1>

        <section className="profile-page__card" aria-label="Your profile">
          <Avatar
            initials={user.initials}
            size={isDesktop ? 88 : 64}
            className="profile-page__avatar"
          />
          <div className="profile-page__identity">
            <span className="profile-page__name">{user.name}</span>
            <span className="profile-page__email">{user.email}</span>
            {user.joinedAt && (
              <span className="profile-page__meta">Member since {formatJoined(user.joinedAt)}</span>
            )}
          </div>
          {isDesktop && editButton}
        </section>
        {!isDesktop && editButton}

        <p className="overline profile-page__overline">Preferences</p>

        <section className="profile-page__prefs" aria-labelledby="prefs-title">
          <h2 id="prefs-title" className="profile-page__prefs-title">
            Preferences
          </h2>

          <PreferenceRow label="Default speaking duration" helper="Preselected on the Topic step">
            <div
              className="profile-page__durations"
              role="group"
              aria-label="Default speaking duration"
            >
              {preferencesService.getDurations().map((d) => (
                <Chip
                  key={d}
                  selected={preferences.defaultDurationMin === d}
                  onClick={() => updatePreferences({ defaultDurationMin: d })}
                  className="profile-page__duration"
                >
                  {d} min
                </Chip>
              ))}
            </div>
          </PreferenceRow>

          <PreferenceRow label="Reading text size" helper="Article size on the Prepare step">
            <SegmentedControl
              label="Reading text size"
              options={TEXT_SIZES}
              value={preferences.readingTextSize}
              onChange={(readingTextSize) => updatePreferences({ readingTextSize })}
              track="raised"
              fullWidth={!isDesktop}
            />
          </PreferenceRow>

          <PreferenceRow label="Camera" compact>
            <Select
              label="Camera"
              hideLabel
              value={preferences.selectedCamera}
              options={withSelected(devices.cameras, preferences.selectedCamera)}
              onChange={(selectedCamera) => updatePreferences({ selectedCamera })}
              className="profile-page__select"
            />
          </PreferenceRow>

          <PreferenceRow label="Microphone" compact>
            <Select
              label="Microphone"
              hideLabel
              value={preferences.selectedMicrophone}
              options={withSelected(devices.microphones, preferences.selectedMicrophone)}
              onChange={(selectedMicrophone) => updatePreferences({ selectedMicrophone })}
              className="profile-page__select"
            />
          </PreferenceRow>

          <PreferenceRow label="Notifications" helper="Tell me when feedback is ready" inline>
            <Toggle
              label="Notifications"
              checked={preferences.notifications}
              onChange={(notifications) => updatePreferences({ notifications })}
            />
          </PreferenceRow>
        </section>

        <Button
          variant={isDesktop ? 'secondary' : 'ghost'}
          className="profile-page__logout"
          onClick={onLogout}
        >
          Log out
        </Button>
      </div>

      <EditProfileDialog
        key={editKey}
        open={editOpen}
        user={user}
        onClose={() => setEditOpen(false)}
        onSaved={(updated) => {
          updateUser(updated)
          setEditOpen(false)
          showToast('Profile updated.')
        }}
      />
    </AppShell>
  )
}

/** Keeps the saved device selectable even if it isn't in the detected list. */
function withSelected(options: string[], selected: string): string[] {
  return options.includes(selected) ? options : [selected, ...options]
}
