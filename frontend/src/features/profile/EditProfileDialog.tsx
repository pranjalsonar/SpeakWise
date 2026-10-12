import { useState, type FormEvent } from 'react'
import * as usersApi from '@/api/api.users'
import { ApiError } from '@/api/client'
import { Banner } from '@/components/ui/Banner'
import { BottomSheet } from '@/components/ui/BottomSheet'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { TextField } from '@/components/ui/TextField'
import type { User } from '@/core/types'
import { isValidEmail } from '@/core/utils'
import { useIsDesktop } from '@/hooks/useMediaQuery'
import './EditProfileDialog.css'

interface Errors {
  name?: string
  email?: string
}

interface EditProfileDialogProps {
  open: boolean
  user: User
  onClose: () => void
  onSaved: (user: User) => void
}

/**
 * Edit your own name and email: Modal on desktop, BottomSheet on mobile.
 * Mount with a fresh `key` each time it opens so the fields start from the current user.
 */
export function EditProfileDialog({ open, user, onClose, onSaved }: EditProfileDialogProps) {
  const isDesktop = useIsDesktop()
  const [name, setName] = useState(user.name)
  const [email, setEmail] = useState(user.email)
  const [errors, setErrors] = useState<Errors>({})
  const [banner, setBanner] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    const trimmedName = name.trim()
    const normalizedEmail = email.trim().toLowerCase()
    const next: Errors = {
      name: trimmedName ? undefined : 'Enter your full name.',
      email: isValidEmail(normalizedEmail) ? undefined : 'Enter a valid email address.',
    }
    setErrors(next)
    setBanner(null)
    if (next.name || next.email) return

    // Only send what changed.
    const changes: usersApi.ProfileChanges = {}
    if (trimmedName !== user.name) changes.fullName = trimmedName
    if (normalizedEmail !== user.email) changes.email = normalizedEmail
    if (Object.keys(changes).length === 0) return onClose()

    setSaving(true)
    try {
      onSaved(await usersApi.updateMyProfile(changes))
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setErrors({ email: 'An account with this email already exists.' })
      } else {
        setBanner(error instanceof ApiError ? error.message : 'Could not save your profile.')
      }
      setSaving(false)
    }
  }

  const form = (
    <form className="edit-profile" onSubmit={onSubmit} noValidate>
      {banner && <Banner>{banner}</Banner>}
      <TextField
        label="Full name"
        value={name}
        error={errors.name}
        autoComplete="name"
        data-autofocus
        onChange={(e) => {
          setName(e.target.value)
          setErrors((prev) => ({ ...prev, name: undefined }))
        }}
      />
      <TextField
        label="Email"
        type="email"
        value={email}
        error={errors.email}
        autoComplete="email"
        onChange={(e) => {
          setEmail(e.target.value)
          setErrors((prev) => ({ ...prev, email: undefined }))
        }}
      />
      <p className="edit-profile__helper">You'll use this email to log in.</p>
      {isDesktop ? (
        <div className="edit-profile__actions">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={saving}>
            Save changes
          </Button>
        </div>
      ) : (
        <div className="edit-profile__stack">
          <Button type="submit" size="lg" block loading={saving}>
            Save changes
          </Button>
          <Button variant="secondary" block onClick={onClose}>
            Cancel
          </Button>
        </div>
      )}
    </form>
  )

  return isDesktop ? (
    <Modal open={open} onClose={onClose} title="Edit profile" width={480}>
      {form}
    </Modal>
  ) : (
    <BottomSheet open={open} onClose={onClose} title="Edit profile">
      {form}
    </BottomSheet>
  )
}
