import { useState } from 'react'
import { Mic, Shuffle } from 'lucide-react'
import { Avatar } from '@/components/ui/Avatar'
import { Badge, DifficultyBadge } from '@/components/ui/Badge'
import { Banner } from '@/components/ui/Banner'
import { Button } from '@/components/ui/Button'
import { Chip } from '@/components/ui/Chip'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { EmptyState } from '@/components/ui/EmptyState'
import { IconButton } from '@/components/ui/IconButton'
import { PasswordField } from '@/components/ui/PasswordField'
import { ProgressBar } from '@/components/ui/ProgressBar'
import { ScoreCircle } from '@/components/ui/ScoreCircle'
import { SearchInput } from '@/components/ui/SearchInput'
import { SegmentedControl } from '@/components/ui/SegmentedControl'
import { Select } from '@/components/ui/Select'
import { TextField } from '@/components/ui/TextField'
import { Textarea } from '@/components/ui/Textarea'
import { Toggle } from '@/components/ui/Toggle'
import { useToast } from '@/context/ToastContext'
import './DevUiPage.css'

/** Dev-only gallery of every primitive, for checking against the prototype's Design System tab. */
export function DevUiPage() {
  const [mode, setMode] = useState<'Suggest a topic' | 'My own topic'>('Suggest a topic')
  const [duration, setDuration] = useState(3)
  const [on, setOn] = useState(true)
  const [search, setSearch] = useState('')
  const [camera, setCamera] = useState('FaceTime HD Camera')
  const [dialog, setDialog] = useState(false)
  const { showToast } = useToast()

  return (
    <main className="dev-ui">
      <h1>SpeakWise design system</h1>

      <section className="dev-ui__section">
        <h3>Buttons</h3>
        <div className="dev-ui__row">
          <Button>Default</Button>
          <Button loading>Loading</Button>
          <Button disabled>Disabled</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Danger</Button>
          <Button variant="light">Light</Button>
          <IconButton aria-label="Shuffle" icon={<Shuffle size={20} />} size={48} />
        </div>
        <div className="dev-ui__row">
          <Button size="sm">Small 44</Button>
          <Button size="lg">Large 52</Button>
          <Button size="xl">XL 56</Button>
        </div>
      </section>

      <section className="dev-ui__section">
        <h3>Inputs</h3>
        <TextField
          label="Email"
          defaultValue="priya.sharma@example.com"
          helper="We'll never share your email."
        />
        <PasswordField
          label="Password"
          defaultValue="secret"
          error="Password must be at least 8 characters."
        />
        <Textarea label="Notes" hideLabel placeholder="Notes…" />
        <SearchInput
          label="Search"
          value={search}
          onChange={setSearch}
          placeholder="Search sessions"
        />
        <Select
          label="Camera"
          value={camera}
          onChange={setCamera}
          options={['FaceTime HD Camera', 'Logitech C920']}
        />
        <Banner>Email or password is incorrect. Check them and try again.</Banner>
      </section>

      <section className="dev-ui__section">
        <h3>Chips, badges, controls</h3>
        <div className="dev-ui__row">
          {[1, 3, 5].map((d) => (
            <Chip key={d} selected={d === duration} onClick={() => setDuration(d)}>
              {d} min
            </Chip>
          ))}
        </div>
        <div className="dev-ui__row">
          <DifficultyBadge difficulty="Beginner" />
          <DifficultyBadge difficulty="Intermediate" />
          <DifficultyBadge difficulty="Advanced" />
          <Badge tone="processing">Processing</Badge>
          <Badge tone="category">Technology</Badge>
          <Badge tone="admin" size="sm">
            Admin
          </Badge>
        </div>
        <SegmentedControl
          label="Topic mode"
          options={['Suggest a topic', 'My own topic'] as const}
          value={mode}
          onChange={setMode}
        />
        <ProgressBar value={68} label="Progress" />
        <div className="dev-ui__row">
          <Toggle checked={on} onChange={setOn} label="Notifications" />
          <Toggle checked={on} onChange={setOn} label="Status" size="sm" tone="status" />
          <ScoreCircle score={84} />
          <Avatar initials="PS" />
          <Avatar initials="AD" tone="accent" size={48} />
        </div>
      </section>

      <section className="dev-ui__section">
        <h3>Feedback</h3>
        <div className="dev-ui__row">
          <Button variant="secondary" onClick={() => setDialog(true)}>
            Open confirm
          </Button>
          <Button
            variant="secondary"
            onClick={() => showToast("Recording submitted. We'll notify you.")}
          >
            Show toast
          </Button>
        </div>
        <EmptyState
          icon={<Mic size={28} />}
          title="No sessions yet"
          body="Your first talk takes about 20 minutes."
        />
      </section>

      <ConfirmDialog
        open={dialog}
        title="You've read 42%. Start anyway?"
        body="Reading is optional, but covering the key points helps your relevance score."
        confirmLabel="Start anyway"
        cancelLabel="Keep reading"
        onConfirm={() => setDialog(false)}
        onCancel={() => setDialog(false)}
      />
    </main>
  )
}
