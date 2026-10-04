import { useState, type FormEvent } from 'react'
import { Link } from 'react-router'
import { ROUTES } from '@/app/routes'
import { AuthLayout } from '@/components/layout/AuthLayout'
import { Banner } from '@/components/ui/Banner'
import { Button } from '@/components/ui/Button'
import { PasswordField } from '@/components/ui/PasswordField'
import { TextField } from '@/components/ui/TextField'
import { useAuth } from '@/context/AuthContext'
import { AuthError, contentService } from '@/core/services'
import { isValidEmail } from '@/core/utils'
import './AuthForm.css'

interface LoginErrors {
  email?: string
  password?: string
}

export function LoginPage() {
  const copy = contentService.getLoginCopy()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<LoginErrors>({})
  const [banner, setBanner] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const validate = (): LoginErrors => ({
    email: isValidEmail(email) ? undefined : copy.errors.email,
    password: password ? undefined : copy.errors.password,
  })

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    const next = validate()
    setErrors(next)
    setBanner(null)
    if (next.email || next.password) return

    setSubmitting(true)
    try {
      // On success RedirectIfAuthed sends the user to their home (or where they came from).
      await login(email, password)
    } catch (error) {
      setBanner(error instanceof AuthError ? error.message : copy.errors.credentials)
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout
      tone="accent"
      headline={copy.brandHeadline}
      body={copy.brandBody}
      mobileHeader="banner"
    >
      <div className="auth-form__intro">
        <h1 className="auth-form__title">{copy.title}</h1>
        <p className="auth-form__subtitle">{copy.subtitle}</p>
      </div>

      {banner && <Banner>{banner}</Banner>}

      <form className="auth-form" onSubmit={onSubmit} noValidate>
        <TextField
          label="Email"
          type="email"
          size="lg"
          autoComplete="email"
          value={email}
          error={errors.email}
          onChange={(e) => {
            setEmail(e.target.value)
            setErrors((prev) => ({ ...prev, email: undefined }))
            setBanner(null)
          }}
        />

        <div className="auth-form__password">
          <PasswordField
            label="Password"
            size="lg"
            autoComplete="current-password"
            placeholder="Your password"
            value={password}
            error={errors.password}
            labelAction={
              <a href="#forgot" className="text-link auth-form__forgot auth-form__forgot--top">
                Forgot password?
              </a>
            }
            onChange={(e) => {
              setPassword(e.target.value)
              setErrors((prev) => ({ ...prev, password: undefined }))
              setBanner(null)
            }}
          />
          <a href="#forgot" className="text-link auth-form__forgot auth-form__forgot--bottom">
            Forgot password?
          </a>
        </div>

        <Button type="submit" size="lg" block loading={submitting} className="auth-form__submit">
          {submitting ? 'Logging in…' : 'Log in'}
        </Button>
      </form>

      <p className="auth-form__switch">
        New here?{' '}
        <Link to={ROUTES.register} className="text-link">
          Create an account
        </Link>
      </p>
    </AuthLayout>
  )
}
