import { Pen } from 'lucide-react'
import { useNavigate } from 'react-router'
import { ROUTES } from '@/app/routes'
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
import { useIsDesktop } from '@/hooks/useMediaQuery'
import { useMediaDevices } from '@/hooks/useMediaDevices'
import { PreferenceRow } from './PreferenceRow'
import './ProfilePage.css'

const TEXT_SIZES: readonly ReadingTextSize[] = ['Small', 'Medium', 'Large']

export function ProfilePage() {
  const user = useCurrentUser()
  const { logout } = useAuth()
  const navigate = useNavigate()
  const isDesktop = useIsDesktop()
  const { showToast } = useToast()
  const { preferences, updatePreferences } = usePreferences()
  const devices = useMediaDevices()

  const onLogout = () => {
    logout()
    navigate(ROUTES.login, { replace: true })
  }

  const editButton = (
    <Button
      variant="secondary"
      iconLeft={<Pen size={16} />}
      block={!isDesktop}
      onClick={() => showToast('Profile editing is coming soon.')}
    >
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
    </AppShell>
  )
}

/** Keeps the saved device selectable even if it isn't in the detected list. */
function withSelected(options: string[], selected: string): string[] {
  return options.includes(selected) ? options : [selected, ...options]
}
