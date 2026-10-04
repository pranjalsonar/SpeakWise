import { useId, useRef, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { useDialogBehavior } from '@/hooks/useDialogBehavior'
import './Dialog.css'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  width?: 460 | 480
  /** Darker scrim over the camera screens. */
  scrim?: 'default' | 'dark'
  children: ReactNode
}

/** Centred desktop dialog (radius 40, cream ground). */
export function Modal({
  open,
  onClose,
  title,
  width = 460,
  scrim = 'default',
  children,
}: ModalProps) {
  const ref = useRef<HTMLDivElement>(null)
  const titleId = useId()
  useDialogBehavior(ref, open, onClose)
  if (!open) return null

  return createPortal(
    <div
      className={`dialog-scrim dialog-scrim--${scrim} dialog-scrim--center`}
      onMouseDown={onClose}
    >
      <div
        ref={ref}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className={`modal modal--w${width}`}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h2 id={titleId} className="dialog__title dialog__title--modal">
          {title}
        </h2>
        {children}
      </div>
    </div>,
    document.body,
  )
}
