import { Pen } from 'lucide-react'
import { Avatar } from '@/components/ui/Avatar'
import { Badge } from '@/components/ui/Badge'
import { IconButton } from '@/components/ui/IconButton'
import { Toggle } from '@/components/ui/Toggle'
import type { AdminUser } from '@/core/types'
import { formatShortDate, formatTimeAgo } from '@/core/utils'
import './UserRow.css'

interface UserRowProps {
  user: AdminUser
  /** The signed-in admin's own row: status can't be switched off. */
  isSelf: boolean
  onToggleActive: (active: boolean) => void
  onEdit: () => void
}

/** Desktop: table row · mobile: card with the status toggle on the right. */
export function UserRow({ user, isSelf, onToggleActive, onEdit }: UserRowProps) {
  const lastActive = user.lastActiveAt ? formatTimeAgo(new Date(user.lastActiveAt)) : 'Never'
  const joined = formatShortDate(new Date(user.joinedAt))
  const sessions = `${user.sessions} ${user.sessions === 1 ? 'session' : 'sessions'}`

  return (
    <div className="user-row">
      <div className="user-row__identity">
        <Avatar initials={user.initials} />
        <div className="user-row__text">
          <span className="user-row__name">
            {user.name}
            {user.role === 'admin' && (
              <Badge tone="admin" size="sm">
                Admin
              </Badge>
            )}
            {isSelf && <span className="user-row__you">(you)</span>}
          </span>
          <span className="user-row__email">{user.email}</span>
          <span className="user-row__meta">
            {sessions} · {lastActive}
          </span>
        </div>
      </div>
      <span className="user-row__cell">{user.sessions}</span>
      <span className="user-row__cell user-row__cell--muted">{lastActive}</span>
      <span className="user-row__cell user-row__cell--muted">{joined}</span>
      <div className="user-row__status">
        <Toggle
          size="sm"
          tone="status"
          checked={user.isActive}
          disabled={isSelf}
          title={isSelf ? "You can't deactivate your own account" : undefined}
          label={`${user.name}: ${user.isActive ? 'active, click to deactivate' : 'inactive, click to activate'}`}
          onChange={onToggleActive}
        />
        <span
          className={`user-row__status-label user-row__status-label--${user.isActive ? 'on' : 'off'}`}
          aria-hidden="true"
        >
          {user.isActive ? 'Active' : 'Inactive'}
        </span>
      </div>
      <IconButton
        icon={<Pen size={16} />}
        aria-label={`Edit ${user.name}`}
        title="Edit user"
        size={40}
        tone="plain"
        className="user-row__edit"
        onClick={onEdit}
      />
    </div>
  )
}
