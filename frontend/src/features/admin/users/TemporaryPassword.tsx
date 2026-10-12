import { Check, Copy } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import './TemporaryPassword.css'

/** Shows a generated password once, with a copy button. It can't be viewed again later. */
export function TemporaryPassword({ password, email }: { password: string; email: string }) {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(password)
      setCopied(true)
    } catch {
      // Clipboard blocked (e.g. insecure context): the password is still selectable.
    }
  }

  return (
    <div className="temp-password">
      <p className="temp-password__intro">
        Share this temporary password with <strong>{email}</strong>. It's shown only once.
      </p>
      <div className="temp-password__box">
        <code className="temp-password__value" aria-label="Temporary password">
          {password}
        </code>
        <Button
          variant="secondary"
          size="sm"
          iconLeft={copied ? <Check size={16} /> : <Copy size={16} />}
          onClick={copy}
        >
          {copied ? 'Copied' : 'Copy'}
        </Button>
      </div>
    </div>
  )
}
