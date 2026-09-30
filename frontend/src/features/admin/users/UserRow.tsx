import { Avatar } from '@/components/ui/Avatar'
import { Toggle } from '@/components/ui/Toggle'
import type { AdminUser, UserStatus } from '@/core/types'
import { initialsOf } from '@/core/utils'
import './UserRow.css'

interface UserRowProps {
  user: AdminUser
  onStatusChange: (status: UserStatus) => void
}

/** Desktop: table row · mobile: card with the status toggle on the right. */
export function UserRow({ user, onStatusChange }: UserRowProps) {
  const active = user.status === 'Active'
  return (
    <div className="user-row">
      <div className="user-row__identity">
        <Avatar initials={initialsOf(user.name)} />
        <div className="user-row__text">
          <span className="user-row__name">{user.name}</span>
          <span className="user-row__email">{user.email}</span>
          <span className="user-row__meta">
            {user.sessions} sessions · {user.lastActive}
          </span>
        </div>
      </div>
      <span className="user-row__cell">{user.sessions}</span>
      <span className="user-row__cell user-row__cell--muted">{user.lastActive}</span>
      <span className="user-row__cell user-row__cell--muted">{user.joined}</span>
      <div className="user-row__status">
        <Toggle
          size="sm"
          tone="status"
          checked={active}
          label={`${user.name}: ${active ? 'active, click to deactivate' : 'inactive, click to activate'}`}
          onChange={(checked) => onStatusChange(checked ? 'Active' : 'Inactive')}
        />
        <span
          className={`user-row__status-label user-row__status-label--${active ? 'on' : 'off'}`}
          aria-hidden="true"
        >
          {user.status}
        </span>
      </div>
    </div>
  )
}
