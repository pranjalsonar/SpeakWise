import { useState, type FormEvent } from 'react'
import { BottomSheet } from '@/components/ui/BottomSheet'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { SegmentedControl } from '@/components/ui/SegmentedControl'
import { TextField } from '@/components/ui/TextField'
import { useToast } from '@/context/ToastContext'
import type { UserStatus } from '@/core/types'
import { isValidEmail } from '@/core/utils'
import { useIsDesktop } from '@/hooks/useMediaQuery'
import { useAdminData } from '../AdminDataContext'
import './AddUserDialog.css'

const STATUSES: readonly UserStatus[] = ['Active', 'Inactive']

interface Errors {
  name?: string
  email?: string
}

/** Add user: Modal on desktop, BottomSheet on mobile. Validates name, email and uniqueness. */
export function AddUserDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const isDesktop = useIsDesktop()
  const { users, addUser } = useAdminData()
  const { showToast } = useToast()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<UserStatus>('Active')
  const [errors, setErrors] = useState<Errors>({})
  const [saving, setSaving] = useState(false)

  const close = () => {
    setName('')
    setEmail('')
    setStatus('Active')
    setErrors({})
    onClose()
  }

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    const normalized = email.trim().toLowerCase()
    const next: Errors = {
      name: name.trim() ? undefined : 'Enter a full name.',
      email: !isValidEmail(normalized)
        ? 'Enter a valid email address.'
        : users?.some((u) => u.email.toLowerCase() === normalized)
          ? 'A user with this email already exists.'
          : undefined,
    }
    setErrors(next)
    if (next.name || next.email) return

    setSaving(true)
    try {
      await addUser({ name, email: normalized, status })
      showToast(`${name.trim()} was added. An invite was sent to ${normalized}.`)
      close()
    } catch (error) {
      setErrors({ email: error instanceof Error ? error.message : 'Could not add this user.' })
    } finally {
      setSaving(false)
    }
  }

  const form = (
    <form className="add-user" onSubmit={onSubmit} noValidate>
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
      <div className="add-user__status">
        <span className="add-user__label" id="add-user-status">
          Status
        </span>
        <SegmentedControl
          label="Status"
          options={STATUSES}
          value={status}
          onChange={setStatus}
          fullWidth={!isDesktop}
        />
      </div>
      <p className="add-user__helper">They'll get an email invite to set their password.</p>
      {isDesktop ? (
        <div className="add-user__actions">
          <Button variant="secondary" onClick={close}>
            Cancel
          </Button>
          <Button type="submit" loading={saving}>
            Add user
          </Button>
        </div>
      ) : (
        <div className="add-user__stack">
          <Button type="submit" size="lg" block loading={saving}>
            Add user
          </Button>
          <Button variant="secondary" block onClick={close}>
            Cancel
          </Button>
        </div>
      )}
    </form>
  )

  return isDesktop ? (
    <Modal open={open} onClose={close} title="Add user" width={480}>
      {form}
    </Modal>
  ) : (
    <BottomSheet open={open} onClose={close} title="Add user">
      {form}
    </BottomSheet>
  )
}
