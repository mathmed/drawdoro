import { FileQuestion, LogIn, RotateCw } from 'lucide-react'
import { useEffect, useState, type FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'

import { getSharedDiagram, type SharedDiagram as SharedDiagramData } from '../api/diagrams'
import { authConfig } from '../auth/config'
import { startLogin } from '../auth/session'
import SharedCanvas from '../components/canvas/SharedCanvas'
import EmptyState from '../components/ui/EmptyState'
import BrandLoader from '../components/ui/loading/BrandLoader'
import LoadingOverlay from '../components/ui/loading/LoadingOverlay'
import Logo from '../components/ui/Logo'
import { useDelayedVisibility } from '../hooks/useDelayedVisibility'
import { useAuthStore } from '../store/useAuthStore'

type LoadState = 'loading' | 'ready' | 'not-found'

// The outcome of one request (token and attempt); null when the diagram could not be opened.
interface LoadedDiagram {
  key: string
  diagram: SharedDiagramData | null
}

function loadStateOf(token: string | undefined, loaded: LoadedDiagram | null, requestKey: string): LoadState {
  if (token === undefined) {
    return 'not-found'
  }
  if (loaded?.key !== requestKey) {
    return 'loading'
  }
  return loaded.diagram === null ? 'not-found' : 'ready'
}

export default function SharedDiagramPage() {
  const { token } = useParams<{ token: string }>()
  const status = useAuthStore((state) => state.status)
  const profile = useAuthStore((state) => state.profile)

  const [loaded, setLoaded] = useState<LoadedDiagram | null>(null)
  const [guestName, setGuestName] = useState<string | null>(null)
  const [nameDraft, setNameDraft] = useState('')
  const [attempt, setAttempt] = useState(0)
  const requestKey = `${token}:${attempt}`

  useEffect(() => {
    if (token === undefined) {
      return
    }
    let active = true
    const key = `${token}:${attempt}`
    void getSharedDiagram(token)
      .then((data) => {
        if (active) {
          setLoaded({ key, diagram: data })
        }
      })
      .catch(() => {
        if (active) {
          setLoaded({ key, diagram: null })
        }
      })
    return () => {
      active = false
    }
  }, [token, attempt])

  const state = loadStateOf(token, loaded, requestKey)
  const diagram = loaded?.key === requestKey ? loaded.diagram : null

  const isLoading = status === 'loading' || state === 'loading'
  const showLoader = useDelayedVisibility(isLoading)
  const retry = (): void => setAttempt((count) => count + 1)

  function renderPage() {
    if (isLoading) {
      return <div className="loading-screen" aria-busy="true" />
    }

    if (state === 'not-found' || diagram === null || token === undefined) {
      return (
        <div className="full-center">
          <EmptyState
            icon={<FileQuestion size={20} />}
            title="Shared diagram not found"
            description="The link may be wrong or the diagram is no longer shared."
            action={
              <div className="empty-state-actions">
                <button type="button" className="btn btn-secondary" onClick={retry}>
                  <RotateCw size={14} /> Try again
                </button>
                <Link to="/" className="btn btn-secondary" style={{ textDecoration: 'none' }}>
                  Go home
                </Link>
              </div>
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
          <div className="share-gate reveal">
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

  // The page underneath mounts as soon as the data is in, and the loader fades out over it.
  return (
    <>
      {renderPage()}
      <LoadingOverlay visible={showLoader} screen>
        <BrandLoader label="Opening shared diagram" showName size={52} onRetry={retry} />
      </LoadingOverlay>
    </>
  )
}
