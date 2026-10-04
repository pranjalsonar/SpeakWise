import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Check } from 'lucide-react'
import { Link } from 'react-router'
import { ROUTES } from '@/app/routes'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { Button } from '@/components/ui/Button'
import { PasswordField } from '@/components/ui/PasswordField'
import { TextField } from '@/components/ui/TextField'
import { useAuth } from '@/context/AuthContext'
import { AuthError, contentService } from '@/core/services'
import { isValidEmail } from '@/core/utils'
import { PasswordStrength } from './PasswordStrength'
import './AuthForm.css'

type Field = 'name' | 'email' | 'password' | 'confirm'
type RegisterErrors = Partial<Record<Field, string>>

export function RegisterPage() {
  const rules = contentService.getRegisterRules()
  const { register } = useAuth()
  const [values, setValues] = useState<Record<Field, string>>({
    name: '',
    email: '',
    password: '',
    confirm: '',
  })
  const [errors, setErrors] = useState<RegisterErrors>({})
  const [showPasswords, setShowPasswords] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const passwordsMatch = values.confirm.length > 0 && values.confirm === values.password

  const update = (field: Field) => (event: ChangeEvent<HTMLInputElement>) => {
    setValues((prev) => ({ ...prev, [field]: event.target.value }))
    setErrors((prev) => ({ ...prev, [field]: undefined }))
  }

  const validate = (): RegisterErrors => ({
    name: values.name.trim() ? undefined : rules.nameRequired,
    email: isValidEmail(values.email) ? undefined : rules.email,
    password: values.password.length >= rules.passwordMin ? undefined : rules.passwordMinMsg,
    confirm: values.confirm === values.password && values.confirm ? undefined : rules.mismatch,
  })

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    const next = validate()
    setErrors(next)
    if (Object.values(next).some(Boolean)) return

    setSubmitting(true)
    try {
      await register(values.name, values.email, values.password)
    } catch (error) {
      if (error instanceof AuthError) setErrors({ email: error.message })
      setSubmitting(false)
    }
  }

  const toggle = () => setShowPasswords((v) => !v)

  return (
    <AuthLayout
      tone="sage"
      headline="Your first talk is 20 minutes away."
      body="Read for 15 minutes, speak for up to 5, and see how you did."
      mobileHeader={{ backTo: ROUTES.login }}
    >
      <div className="auth-form__intro">
        <h1 className="auth-form__title auth-form__title--register">Create your account</h1>
        <p className="auth-form__subtitle">You'll log in with your email and password.</p>
      </div>

      <form className="auth-form auth-form--register" onSubmit={onSubmit} noValidate>
        <TextField
          label="Full name"
          size="lg"
          autoComplete="name"
          placeholder="Priya Sharma"
          value={values.name}
          error={errors.name}
          onChange={update('name')}
        />
        <TextField
          label="Email"
          type="email"
          size="lg"
          autoComplete="email"
          placeholder="you@example.com"
          value={values.email}
          error={errors.email}
          onChange={update('email')}
        />
        <PasswordField
          label="Password"
          size="lg"
          autoComplete="new-password"
          placeholder="At least 8 characters"
          value={values.password}
          error={errors.password}
          visible={showPasswords}
          onToggleVisible={toggle}
          helper={<PasswordStrength password={values.password} />}
          onChange={update('password')}
        />
        <TextField
          label="Confirm password"
          size="lg"
          type={showPasswords ? 'text' : 'password'}
          autoComplete="new-password"
          placeholder="Type it again"
          value={values.confirm}
          error={errors.confirm}
          onChange={update('confirm')}
          endAdornment={
            passwordsMatch ? (
              <span className="field__status" aria-label="Passwords match">
                <Check size={20} />
              </span>
            ) : undefined
          }
        />

        <Button type="submit" size="lg" block loading={submitting} className="auth-form__submit">
          {submitting ? 'Creating account…' : 'Create account'}
        </Button>
      </form>

      <p className="auth-form__switch">
        Already have an account?{' '}
        <Link to={ROUTES.login} className="text-link">
          Log in
        </Link>
      </p>
    </AuthLayout>
  )
}
