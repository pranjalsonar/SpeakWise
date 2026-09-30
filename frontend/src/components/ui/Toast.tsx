import { Check } from 'lucide-react'
import './Toast.css'

export function Toast({ message }: { message: string }) {
  return (
    <div className="toast" role="status" aria-live="polite">
      <Check size={18} className="toast__icon" aria-hidden="true" />
      <span>{message}</span>
    </div>
  )
}
