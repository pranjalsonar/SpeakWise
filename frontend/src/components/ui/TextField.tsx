import { useId, type InputHTMLAttributes, type ReactNode } from 'react'
import './Field.css'

export interface TextFieldProps extends Omit<
  InputHTMLAttributes<HTMLInputElement>,
  'className' | 'size'
> {
  label: string
  error?: string
  helper?: ReactNode
  /** Content inside the pill, after the input (e.g. Show/Hide, check icon). */
  endAdornment?: ReactNode
  /** Leading icon inside the pill (search). */
  startAdornment?: ReactNode
  hideLabel?: boolean
  /** Rendered on the label row's right (e.g. "Forgot password?"). */
  labelAction?: ReactNode
  /** md = 48px · lg = 52px (auth forms). */
  size?: 'md' | 'lg'
  className?: string
}

export function TextField({
  label,
  error,
  helper,
  endAdornment,
  startAdornment,
  hideLabel = false,
  labelAction,
  size = 'md',
  className,
  id,
  ...inputProps
}: TextFieldProps) {
  const autoId = useId()
  const inputId = id ?? autoId
  const messageId = `${inputId}-msg`
  const hasMessage = Boolean(error || helper)

  return (
    <div className={['field', size === 'lg' && 'field--lg', className].filter(Boolean).join(' ')}>
      {labelAction ? (
        <div className="field__label-row">
          <label htmlFor={inputId} className="field__label">
            {label}
          </label>
          {labelAction}
        </div>
      ) : (
        <label htmlFor={inputId} className={hideLabel ? 'sr-only' : 'field__label'}>
          {label}
        </label>
      )}
      <div
        className={[
          'field__control',
          error && 'field__control--error',
          startAdornment && 'field__control--start',
          endAdornment && 'field__control--end',
        ]
          .filter(Boolean)
          .join(' ')}
      >
        {startAdornment && <span className="field__start">{startAdornment}</span>}
        <input
          {...inputProps}
          id={inputId}
          className="field__input"
          aria-invalid={error ? true : undefined}
          aria-describedby={hasMessage ? messageId : undefined}
        />
        {endAdornment && <span className="field__end">{endAdornment}</span>}
      </div>
      {hasMessage && (
        <div id={messageId} className="field__messages">
          {helper && <div className="field__helper">{helper}</div>}
          {error && <p className="field__error">{error}</p>}
        </div>
      )}
    </div>
  )
}
