import { useId, useRef, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { useDialogBehavior } from '@/hooks/useDialogBehavior'
import './Dialog.css'

interface BottomSheetProps {
  open: boolean
  onClose: () => void
  title: string
  /** Rendered on the title row's right (e.g. a Done button). */
  headerAction?: ReactNode
  scrim?: 'default' | 'dark'
  /** Fixed-height sheet whose body flexes (notes). */
  tall?: boolean
  children: ReactNode
}

/** Mobile sheet: grab handle, 36px top radius, content stacked. */
export function BottomSheet({
  open,
  onClose,
  title,
  headerAction,
  scrim = 'default',
  tall = false,
  children,
}: BottomSheetProps) {
  const ref = useRef<HTMLDivElement>(null)
  const titleId = useId()
  useDialogBehavior(ref, open, onClose)
  if (!open) return null

  return createPortal(
    <div
      className={`dialog-scrim dialog-scrim--${scrim} dialog-scrim--bottom`}
      onMouseDown={onClose}
    >
      <div
        ref={ref}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className={['sheet', tall && 'sheet--tall'].filter(Boolean).join(' ')}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <span className="sheet__handle" aria-hidden="true" />
        <div className="sheet__header">
          <h2 id={titleId} className="dialog__title dialog__title--sheet">
            {title}
          </h2>
          {headerAction}
        </div>
        {children}
      </div>
    </div>,
    document.body,
  )
}
