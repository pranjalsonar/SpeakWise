import type { ReactNode } from 'react'
import { useIsDesktop } from '@/hooks/useMediaQuery'
import { BottomSheet } from './BottomSheet'
import { Button } from './Button'
import { Modal } from './Modal'
import './Dialog.css'

interface ConfirmDialogProps {
  open: boolean
  title: string
  body: ReactNode
  confirmLabel: string
  cancelLabel: string
  onConfirm: () => void
  onCancel: () => void
  danger?: boolean
  scrim?: 'default' | 'dark'
}

/**
 * Confirmation as a Modal on desktop and a BottomSheet on mobile.
 * Desktop puts the actions on the right (cancel, confirm). Mobile stacks them (confirm first).
 */
export function ConfirmDialog({
  open,
  title,
  body,
  confirmLabel,
  cancelLabel,
  onConfirm,
  onCancel,
  danger = false,
  scrim,
}: ConfirmDialogProps) {
  const isDesktop = useIsDesktop()
  const variant = danger ? 'danger' : 'primary'

  if (isDesktop) {
    return (
      <Modal open={open} onClose={onCancel} title={title} scrim={scrim}>
        <p className="dialog__body">{body}</p>
        <div className="dialog__actions">
          <Button variant="secondary" onClick={onCancel}>
            {cancelLabel}
          </Button>
          <Button variant={variant} onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </Modal>
    )
  }

  return (
    <BottomSheet open={open} onClose={onCancel} title={title} scrim={scrim}>
      <p className="dialog__body">{body}</p>
      <Button variant={variant} size="lg" block onClick={onConfirm}>
        {confirmLabel}
      </Button>
      <Button variant="secondary" block onClick={onCancel}>
        {cancelLabel}
      </Button>
    </BottomSheet>
  )
}
