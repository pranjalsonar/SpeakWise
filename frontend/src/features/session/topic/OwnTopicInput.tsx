import { useId } from 'react'
import { OWN_TOPIC_MAX } from '@/core/session/sessionReducer'
import { useIsDesktop } from '@/hooks/useMediaQuery'
import './OwnTopicInput.css'

interface OwnTopicInputProps {
  value: string
  examples: string[]
  onChange: (text: string) => void
}

/** Free-text topic (max 120 chars) with example chips that fill the field. */
export function OwnTopicInput({ value, examples, onChange }: OwnTopicInputProps) {
  const id = useId()
  const isDesktop = useIsDesktop()
  const fieldProps = {
    id,
    className: 'own-topic__input',
    value,
    maxLength: OWN_TOPIC_MAX,
    placeholder: 'e.g. Why public libraries still matter',
    'aria-describedby': `${id}-count`,
  }

  return (
    <div className="own-topic">
      <label htmlFor={id} className="own-topic__label">
        What do you want to talk about?
      </label>
      {/* Mobile: a 96px textarea. Desktop: a single-line 60px pill. */}
      {isDesktop ? (
        <input {...fieldProps} onChange={(e) => onChange(e.target.value)} />
      ) : (
        <textarea
          {...fieldProps}
          rows={3}
          onChange={(e) => onChange(e.target.value.replace(/\n/g, ' '))}
        />
      )}
      <span id={`${id}-count`} className="own-topic__count">
        {value.length}/{OWN_TOPIC_MAX}
      </span>
      <span className="own-topic__hint">Try one of these</span>
      <div className="own-topic__examples">
        {examples.map((example) => (
          <button
            key={example}
            type="button"
            className="own-topic__example"
            onClick={() => onChange(example)}
          >
            {example}
          </button>
        ))}
      </div>
    </div>
  )
}
