import { useState, type ReactNode } from 'react'
import { TextField, type TextFieldProps } from './TextField'

interface PasswordFieldProps extends Omit<TextFieldProps, 'type' | 'endAdornment'> {
  /** Extra adornment shown before the toggle (e.g. the "passwords match" check). */
  status?: ReactNode
  /** Controlled visibility, for when one toggle drives several fields (register). */
  visible?: boolean
  onToggleVisible?: () => void
}

export function PasswordField({ status, visible, onToggleVisible, ...props }: PasswordFieldProps) {
  const [ownVisible, setOwnVisible] = useState(false)
  const isVisible = visible ?? ownVisible
  const toggle = onToggleVisible ?? (() => setOwnVisible((v) => !v))

  return (
    <TextField
      {...props}
      type={isVisible ? 'text' : 'password'}
      endAdornment={
        <>
          {status}
          <button
            type="button"
            className="field__toggle"
            onClick={toggle}
            aria-label={isVisible ? 'Hide password' : 'Show password'}
            aria-pressed={isVisible}
          >
            {isVisible ? 'Hide' : 'Show'}
          </button>
        </>
      }
    />
  )
}
