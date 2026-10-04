import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { Link } from 'react-router'
import { Spinner } from './Spinner'
import './Button.css'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'light' | 'dark-outline'
export type ButtonSize = 'sm' | 'md' | 'lg' | 'xl'

interface CommonProps {
  variant?: ButtonVariant
  size?: ButtonSize
  block?: boolean
  loading?: boolean
  iconLeft?: ReactNode
  iconRight?: ReactNode
  className?: string
  children: ReactNode
}

type ButtonAsButton = CommonProps &
  Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'className' | 'children'> & {
    to?: undefined
    href?: undefined
  }
/** Router link (`to`) or plain anchor (`href`, e.g. in-page #hash links). */
type ButtonAsLink = CommonProps & {
  onClick?: () => void
  'aria-label'?: string
} & ({ to: string; href?: undefined } | { href: string; to?: undefined })

export type ButtonProps = ButtonAsButton | ButtonAsLink

/**
 * Pill button, Caprasimo label. Sizes: sm 44px · md 48px · lg 52px · xl 56px.
 * `light` = raised background with accent text (on accent cards).
 */
export function Button(props: ButtonProps) {
  const {
    variant = 'primary',
    size = 'md',
    block = false,
    loading = false,
    iconLeft,
    iconRight,
    className,
    children,
  } = props

  const classes = [
    'btn',
    `btn--${variant}`,
    `btn--${size}`,
    block && 'btn--block',
    loading && 'btn--loading',
    className,
  ]
    .filter(Boolean)
    .join(' ')

  const content = (
    <>
      {loading ? <Spinner size={16} /> : iconLeft}
      {children}
      {!loading && iconRight}
    </>
  )

  if (props.to !== undefined) {
    return (
      <Link
        to={props.to}
        className={classes}
        onClick={props.onClick}
        aria-label={props['aria-label']}
      >
        {content}
      </Link>
    )
  }

  if (props.href !== undefined) {
    return (
      <a
        href={props.href}
        className={classes}
        onClick={props.onClick}
        aria-label={props['aria-label']}
      >
        {content}
      </a>
    )
  }

  const {
    variant: _v,
    size: _s,
    block: _b,
    loading: _l,
    iconLeft: _il,
    iconRight: _ir,
    className: _c,
    children: _ch,
    to: _to,
    href: _href,
    type = 'button',
    disabled,
    ...rest
  } = props

  return (
    <button
      {...rest}
      type={type}
      className={classes}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
    >
      {content}
    </button>
  )
}
