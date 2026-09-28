import { FileQuestion, Loader2, LogIn } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'

import { getSharedDiagram, type SharedDiagram as SharedDiagramData } from '../api/diagrams'
import { authConfig } from '../auth/config'
import { startLogin } from '../auth/session'
import SharedCanvas from '../components/canvas/SharedCanvas'
import EmptyState from '../components/ui/EmptyState'
import Logo from '../components/ui/Logo'
import { useAuthStore } from '../store/useAuthStore'

type LoadState = 'loading' | 'ready' | 'not-found'

export default function SharedDiagramPage() {
  const { token } = useParams<{ token: string }>()
  const status = useAuthStore((state) => state.status)
  const profile = useAuthStore((state) => state.profile)

  const [state, setState] = useState<LoadState>('loading')
  const [diagram, setDiagram] = useState<SharedDiagramData | null>(null)
  const [guestName, setGuestName] = useState<string | null>(null)
  const [nameDraft, setNameDraft] = useState('')

  useEffect(() => {
    if (token === undefined) {
      setState('not-found')
      return
    }
    let active = true
    setState('loading')
    void getSharedDiagram(token)
      .then((data) => {
        if (active) {
          setDiagram(data)
          setState('ready')
        }
      })
      .catch(() => {
        if (active) {
          setState('not-found')
        }
      })
    return () => {
      active = false
    }
  }, [token])

  if (status === 'loading' || state === 'loading') {
    return (
      <div className="full-center">
        <Loader2 size={16} className="spinner" /> Opening shared diagram…
      </div>
    )
  }

  if (state === 'not-found' || diagram === null || token === undefined) {
    return (
      <div className="full-center">
        <EmptyState
          icon={<FileQuestion size={20} />}
          title="Shared diagram not found"
          description="The link may be wrong or the diagram is no longer shared."
          action={
            <Link to="/" className="btn btn-secondary" style={{ textDecoration: 'none' }}>
              Go home
            </Link>
          }
        />
      </div>
    )
  }

  // Signed-in users open the diagram straight away; guests pick a name first.
  const isSignedIn = status === 'signed-in'
  const resolvedGuestName = isSignedIn ? undefined : (guestName ?? undefined)

  if (!isSignedIn && guestName === null) {
    return (
      <div className="landing">
        <div className="share-gate">
          <Logo size={40} />
          <h1 className="share-gate-title">{diagram.name}</h1>
          <p className="share-gate-description">
            You were invited to view this diagram. Sign in, or continue as a guest with just your name.
          </p>
          <form
            className="share-gate-form"
            onSubmit={(event: FormEvent) => {
              event.preventDefault()
              const trimmed = nameDraft.trim()
              if (trimmed !== '') {
                setGuestName(trimmed)
              }
            }}
          >
            <input
              className="input"
              autoFocus
              value={nameDraft}
              placeholder="Your name"
              aria-label="Your name"
              onChange={(event) => setNameDraft(event.target.value)}
            />
            <button type="submit" className="btn btn-primary" disabled={nameDraft.trim() === ''}>
              Continue as guest
            </button>
          </form>
          {authConfig.enabled ? (
            <button
              type="button"
              className="btn btn-secondary share-gate-signin"
              onClick={() => void startLogin(`/share/${token}`)}
            >
              <LogIn size={15} /> Sign in instead
            </button>
          ) : null}
        </div>
      </div>
    )
  }

  const displayName = isSignedIn ? profile?.name : resolvedGuestName

  return (
    <div className="share-view">
      <header className="share-view-bar">
        <Logo />
        <span className="share-view-name">{diagram.name}</span>
        <span className="share-view-badge">Read-only</span>
        {displayName !== undefined && displayName !== null ? (
          <span className="share-view-viewer">{displayName}</span>
        ) : null}
      </header>
      <div className="share-view-stage">
        <SharedCanvas diagram={diagram} shareToken={token} guestName={resolvedGuestName} />
      </div>
    </div>
  )
}
