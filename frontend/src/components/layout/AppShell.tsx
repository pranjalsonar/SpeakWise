import type { ReactNode } from 'react'
import { History, House, Plus, User as UserIcon, type LucideIcon } from 'lucide-react'
import { NavLink } from 'react-router'
import { ROUTES } from '@/app/routes'
import { Avatar } from '@/components/ui/Avatar'
import { Button } from '@/components/ui/Button'
import { useCurrentUser } from '@/context/AuthContext'
import { useStartSession } from '@/hooks/useStartSession'
import './AppShell.css'

const navItems: { to: string; label: string; icon: LucideIcon }[] = [
  { to: ROUTES.home, label: 'Home', icon: House },
  { to: ROUTES.history, label: 'History', icon: History },
  { to: ROUTES.profile, label: 'Profile', icon: UserIcon },
]

interface AppShellProps {
  /** Mobile top bar title. Omit to show the SpeakWise logo (Home). */
  mobileTitle?: string
  /** Show the avatar on the mobile top bar. */
  mobileAvatar?: boolean
  /** Replace the mobile top bar entirely (e.g. Feedback's back arrow). */
  mobileHeader?: ReactNode
  /** Hide the mobile tab bar (e.g. Feedback). */
  hideTabBar?: boolean
  /** Highlight this nav item when the current route isn't one of them (Feedback → History). */
  activePath?: string
  children: ReactNode
}

/** Student app layout: 240px sidebar on desktop, top bar + bottom tab bar on mobile. */
export function AppShell({
  mobileTitle,
  mobileAvatar = true,
  mobileHeader,
  hideTabBar = false,
  activePath,
  children,
}: AppShellProps) {
  const user = useCurrentUser()
  const startSession = useStartSession()

  return (
    <div className={['app-shell', hideTabBar && 'app-shell--no-tabs'].filter(Boolean).join(' ')}>
      <aside className="app-shell__sidebar">
        <span className="app-shell__logo">SpeakWise</span>
        <Button
          iconLeft={<Plus size={16} />}
          className="app-shell__start"
          onClick={() => startSession()}
        >
          Start session
        </Button>
        <nav className="app-shell__nav" aria-label="Main">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                [
                  'app-shell__nav-item',
                  (isActive || to === activePath) && 'app-shell__nav-item--active',
                ]
                  .filter(Boolean)
                  .join(' ')
              }
            >
              <Icon size={20} aria-hidden="true" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="app-shell__user">
          <Avatar initials={user.initials} />
          <div className="app-shell__user-text">
            <span className="app-shell__user-name">{user.name}</span>
            <span className="app-shell__user-email">{user.email}</span>
          </div>
        </div>
      </aside>

      {mobileHeader ? (
        <div className="app-shell__topbar app-shell__topbar--custom">{mobileHeader}</div>
      ) : (
        <header className="app-shell__topbar">
          {mobileTitle ? (
            <h1 className="app-shell__topbar-title">{mobileTitle}</h1>
          ) : (
            <span className="app-shell__topbar-logo">SpeakWise</span>
          )}
          {mobileAvatar && <Avatar initials={user.initials} />}
        </header>
      )}

      <main className="app-shell__main">{children}</main>

      {!hideTabBar && (
        <nav className="app-shell__tabbar" aria-label="Main">
          <NavLink
            to={ROUTES.home}
            className={({ isActive }) =>
              ['app-shell__tab', isActive && 'app-shell__tab--active'].filter(Boolean).join(' ')
            }
          >
            <House size={20} aria-hidden="true" />
            Home
          </NavLink>
          <button
            type="button"
            className="app-shell__tab app-shell__tab--start"
            onClick={() => startSession()}
          >
            <span className="app-shell__start-circle" aria-hidden="true">
              <Plus size={20} />
            </span>
            Start
          </button>
          <NavLink
            to={ROUTES.history}
            className={({ isActive }) =>
              ['app-shell__tab', isActive && 'app-shell__tab--active'].filter(Boolean).join(' ')
            }
          >
            <History size={20} aria-hidden="true" />
            History
          </NavLink>
          <NavLink
            to={ROUTES.profile}
            className={({ isActive }) =>
              ['app-shell__tab', isActive && 'app-shell__tab--active'].filter(Boolean).join(' ')
            }
          >
            <UserIcon size={20} aria-hidden="true" />
            Profile
          </NavLink>
        </nav>
      )}
    </div>
  )
}
