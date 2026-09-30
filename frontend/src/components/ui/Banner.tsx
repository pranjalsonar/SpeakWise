import type { ReactNode } from 'react'
import './Banner.css'

export function Banner({ children }: { children: ReactNode }) {
  return (
    <div className="banner" role="alert">
      {children}
    </div>
  )
}
