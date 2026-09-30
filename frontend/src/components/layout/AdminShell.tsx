import type { ReactNode } from 'react'
import { House, TrendingUp, User as UserIcon, type LucideIcon } from 'lucide-react'
import { NavLink } from 'react-router'
import { ROUTES } from '@/app/routes'
import { Avatar } from '@/components/ui/Avatar'
import { useCurrentUser } from '@/context/AuthContext'
import './AdminShell.css'

const navItems: { to: string; label: string; tabLabel: string; icon: LucideIcon; end?: boolean }[] =
  [
    { to: ROUTES.admin, label: 'Dashboard', tabLabel: 'Dashboard', icon: TrendingUp, end: true },
    { to: ROUTES.adminUsers, label: 'Users', tabLabel: 'Users', icon: UserIcon },
    { to: ROUTES.home, label: 'Back to app', tabLabel: 'App', icon: House },
  ]

interface AdminShellProps {
  /** Mobile top bar title. */
  mobileTitle: string
  /** Mobile top bar action (e.g. "Add user"). When set, the Admin badge is hidden. */
  mobileAction?: ReactNode
  children: ReactNode
}

/** Admin layout: dark 240px sidebar on desktop, title bar + 3-tab bar on mobile. */
export function AdminShell({ mobileTitle, mobileAction, children }: AdminShellProps) {
  const user = useCurrentUser()

  return (
    <div className="admin-shell">
      <aside className="admin-shell__sidebar">
        <div className="admin-shell__brand">
          <span className="admin-shell__logo">SpeakWise</span>
          <span className="admin-shell__badge">Admin</span>
        </div>
        <nav className="admin-shell__nav" aria-label="Admin">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                ['admin-shell__nav-item', isActive && 'admin-shell__nav-item--active']
                  .filter(Boolean)
                  .join(' ')
              }
            >
              <Icon size={20} aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="admin-shell__user">
          <Avatar initials={user.initials} tone="accent" />
          <div className="admin-shell__user-text">
            <span className="admin-shell__user-name">{user.name}</span>
            <span className="admin-shell__user-email">{user.email}</span>
          </div>
        </div>
      </aside>

      <header className="admin-shell__topbar">
        <h1 className="admin-shell__title">{mobileTitle}</h1>
        {mobileAction ? (
          <span className="admin-shell__action">{mobileAction}</span>
        ) : (
          <span className="admin-shell__badge admin-shell__badge--light">Admin</span>
        )}
      </header>

      <main className="admin-shell__main">{children}</main>

      <nav className="admin-shell__tabbar" aria-label="Admin">
        {navItems.map(({ to, tabLabel, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              ['admin-shell__tab', isActive && 'admin-shell__tab--active'].filter(Boolean).join(' ')
            }
          >
            <Icon size={20} aria-hidden="true" />
            {tabLabel}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
