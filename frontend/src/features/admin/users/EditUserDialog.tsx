import { useState, type FormEvent } from 'react'
import * as usersApi from '@/api/api.admin.users'
import { ApiError } from '@/api/client'
import { Banner } from '@/components/ui/Banner'
import { BottomSheet } from '@/components/ui/BottomSheet'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { SegmentedControl } from '@/components/ui/SegmentedControl'
import { TextField } from '@/components/ui/TextField'
import type { AdminUser } from '@/core/types'
import { isValidEmail } from '@/core/utils'
import { useIsDesktop } from '@/hooks/useMediaQuery'
import { TemporaryPassword } from './TemporaryPassword'
import './AddUserDialog.css'
import './EditUserDialog.css'

const ROLES = ['Student', 'Admin'] as const
const STATUSES = ['Active', 'Inactive'] as const

interface Errors {
  name?: string
  email?: string
}

interface EditUserDialogProps {
  open: boolean
  user: AdminUser
  /** Editing your own account: role and status are locked. */
  isSelf: boolean
  onClose: () => void
  onSaved: (user: AdminUser) => void
}

type ResetState = 'idle' | 'confirm' | 'working' | { password: string }

/**
 * Edit any user's name, email, role and status, or reset their password.
 * Modal on desktop, BottomSheet on mobile. Mount with a fresh `key` per opening.
 */
export function EditUserDialog({ open, user, isSelf, onClose, onSaved }: EditUserDialogProps) {
  const isDesktop = useIsDesktop()
  const [name, setName] = useState(user.fullName ?? '')
  const [email, setEmail] = useState(user.email)
  const [role, setRole] = useState<(typeof ROLES)[number]>(
    user.role === 'admin' ? 'Admin' : 'Student',
  )
  const [status, setStatus] = useState<(typeof STATUSES)[number]>(
    user.isActive ? 'Active' : 'Inactive',
  )
  const [errors, setErrors] = useState<Errors>({})
  const [banner, setBanner] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [reset, setReset] = useState<ResetState>('idle')

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    const trimmedName = name.trim()
    const normalizedEmail = email.trim().toLowerCase()
    const next: Errors = {
      name: trimmedName ? undefined : 'Enter a full name.',
      email: isValidEmail(normalizedEmail) ? undefined : 'Enter a valid email address.',
    }
    setErrors(next)
    setBanner(null)
    if (next.name || next.email) return

    // Only send what changed.
    const changes: usersApi.AdminUserChanges = {}
    if (trimmedName !== (user.fullName ?? '')) changes.fullName = trimmedName
    if (normalizedEmail !== user.email) changes.email = normalizedEmail
    if (!isSelf) {
      const nextRole = role === 'Admin' ? 'admin' : 'student'
      if (nextRole !== user.role) changes.role = nextRole
      if ((status === 'Active') !== user.isActive) changes.isActive = status === 'Active'
    }
    if (Object.keys(changes).length === 0) return onClose()

    setSaving(true)
    try {
      onSaved(await usersApi.updateUser(user.id, changes))
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setErrors({ email: 'A user with this email already exists.' })
      } else {
        setBanner(error instanceof ApiError ? error.message : 'Could not save this user.')
      }
      setSaving(false)
    }
  }

  const onReset = async () => {
    setReset('working')
    setBanner(null)
    try {
      setReset({ password: await usersApi.resetPassword(user.id) })
    } catch (error) {
      setReset('idle')
      setBanner(error instanceof ApiError ? error.message : 'Could not reset the password.')
    }
  }

  const resetSection =
    typeof reset === 'object' ? (
      <TemporaryPassword password={reset.password} email={user.email} />
    ) : reset === 'idle' ? (
      <div className="edit-user__reset-row">
        <span className="edit-user__reset-text">Forgot their password?</span>
        <Button variant="secondary" size="sm" onClick={() => setReset('confirm')}>
          Reset password
        </Button>
      </div>
    ) : (
      <div className="edit-user__reset-confirm">
        <p className="edit-user__reset-text">
          Their current password will stop working and a new temporary one is generated.
        </p>
        <div className="edit-user__reset-actions">
          <Button variant="secondary" size="sm" onClick={() => setReset('idle')}>
            Cancel
          </Button>
          <Button variant="danger" size="sm" loading={reset === 'working'} onClick={onReset}>
            Reset password
          </Button>
        </div>
      </div>
    )

  const form = (
    <form className="add-user" onSubmit={onSubmit} noValidate>
      {banner && <Banner>{banner}</Banner>}
      <TextField
        label="Full name"
        value={name}
        error={errors.name}
        autoComplete="off"
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
        autoComplete="off"
        onChange={(e) => {
          setEmail(e.target.value)
          setErrors((prev) => ({ ...prev, email: undefined }))
        }}
      />
      {isSelf ? (
        <p className="add-user__helper">
          You can't change your own role or status, so the app always keeps an admin.
        </p>
      ) : (
        <>
          <div className="add-user__status">
            <span className="add-user__label">Role</span>
            <SegmentedControl
              label="Role"
              options={ROLES}
              value={role}
              onChange={setRole}
              fullWidth={!isDesktop}
            />
          </div>
          <div className="add-user__status">
            <span className="add-user__label">Status</span>
            <SegmentedControl
              label="Status"
              options={STATUSES}
              value={status}
              onChange={setStatus}
              fullWidth={!isDesktop}
            />
          </div>
        </>
      )}
      <p className="add-user__helper">Role and email changes apply the next time they log in.</p>

      <div className="edit-user__reset">{resetSection}</div>

      {isDesktop ? (
        <div className="add-user__actions">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button type="submit" loading={saving}>
            Save changes
          </Button>
        </div>
      ) : (
        <div className="add-user__stack">
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

  const title = `Edit ${user.name}`

  return isDesktop ? (
    <Modal open={open} onClose={onClose} title={title} width={480}>
      {form}
    </Modal>
  ) : (
    <BottomSheet open={open} onClose={onClose} title={title}>
      {form}
    </BottomSheet>
  )
}
