import { TextField } from './TextField'

interface SearchInputProps {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

/** Pill search field. The label is visually hidden (the placeholder carries the hint). */
export function SearchInput({ label, value, onChange, placeholder, className }: SearchInputProps) {
  return (
    <TextField
      label={label}
      hideLabel
      type="search"
      value={value}
      placeholder={placeholder}
      onChange={(e) => onChange(e.target.value)}
      className={className}
    />
  )
}
