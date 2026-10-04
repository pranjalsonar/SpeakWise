import { BottomSheet } from '@/components/ui/BottomSheet'
import './NotesSheet.css'

interface NotesSheetProps {
  open: boolean
  notes: string
  onChange: (notes: string) => void
  onClose: () => void
}

/** Mobile notes: a tall bottom sheet with a Done button. */
export function NotesSheet({ open, notes, onChange, onClose }: NotesSheetProps) {
  return (
    <BottomSheet
      open={open}
      onClose={onClose}
      title="Notes"
      tall
      headerAction={
        <button type="button" className="notes-sheet__done" onClick={onClose}>
          Done
        </button>
      }
    >
      <textarea
        className="notes-sheet__input"
        aria-label="Notes"
        value={notes}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Jot down facts or phrases to use in your talk…"
        data-autofocus
      />
    </BottomSheet>
  )
}
