import { useId } from 'react'
import { ChevronDown } from 'lucide-react'
import './Field.css'

interface SelectProps {
  label: string
  hideLabel?: boolean
  value: string
  options: string[]
  onChange: (value: string) => void
  className?: string
}

export function Select({
  label,
  hideLabel = false,
  value,
  options,
  onChange,
  className,
}: SelectProps) {
  const id = useId()
  return (
    <div className={['field', className].filter(Boolean).join(' ')}>
      <label htmlFor={id} className={hideLabel ? 'sr-only' : 'field__label'}>
        {label}
      </label>
      <div className="field__select-wrap">
        <select
          id={id}
          className="field__select"
          value={value}
          onChange={(e) => onChange(e.target.value)}
        >
          {options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
        <ChevronDown size={18} className="field__select-icon" aria-hidden="true" />
      </div>
    </div>
  )
}
