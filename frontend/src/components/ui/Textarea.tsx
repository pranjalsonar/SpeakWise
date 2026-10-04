import { useId, type TextareaHTMLAttributes } from 'react'
import './Field.css'

interface TextareaProps extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'className'> {
  label: string
  hideLabel?: boolean
  className?: string
}

export function Textarea({ label, hideLabel = false, className, id, ...props }: TextareaProps) {
  const autoId = useId()
  const inputId = id ?? autoId
  return (
    <div className={['field', className].filter(Boolean).join(' ')}>
      <label htmlFor={inputId} className={hideLabel ? 'sr-only' : 'field__label'}>
        {label}
      </label>
      <textarea {...props} id={inputId} className="field__textarea" />
    </div>
  )
}
