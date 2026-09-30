import { contentService } from '@/core/services'
import { passwordStrength } from '@/core/utils'
import './PasswordStrength.css'

const levels = ['weak', 'fair', 'strong'] as const

/** 3-segment meter + label and hint, shown while typing a new password. */
export function PasswordStrength({ password }: { password: string }) {
  const score = passwordStrength(password)
  if (score === 0) return null
  const [label, hint] = contentService.getRegisterRules().strength[score]
  const level = levels[score - 1]

  return (
    <div className={`password-strength password-strength--${level}`} aria-live="polite">
      <div className="password-strength__bars" aria-hidden="true">
        {[1, 2, 3].map((segment) => (
          <span
            key={segment}
            className={['password-strength__bar', segment <= score && 'password-strength__bar--on']
              .filter(Boolean)
              .join(' ')}
          />
        ))}
      </div>
      <p className="password-strength__text">
        <b>{label}.</b> {hint}
      </p>
    </div>
  )
}
