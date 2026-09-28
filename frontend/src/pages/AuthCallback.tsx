import { CircleAlert, Loader2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { completeLogin } from '../auth/session'
import EmptyState from '../components/ui/EmptyState'
import { useAuthStore } from '../store/useAuthStore'

export default function AuthCallback() {
  const navigate = useNavigate()
  const initialize = useAuthStore((state) => state.initialize)
  const [error, setError] = useState<string | null>(null)
  // The authorization code is single-use; StrictMode's double effect must not redeem it twice.
  const started = useRef(false)

  useEffect(() => {
    if (started.current) {
      return
    }
    started.current = true
    completeLogin(window.location.search)
      .then(async (returnTo) => {
        await initialize()
        navigate(returnTo, { replace: true })
      })
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : 'Sign-in failed.'))
  }, [initialize, navigate])

  if (error !== null) {
    return (
      <div className="full-center">
        <EmptyState
          icon={<CircleAlert size={20} />}
          title="Could not sign you in"
          description={error}
          action={
            <Link to="/" className="btn btn-secondary" style={{ textDecoration: 'none' }}>
              Back to sign in
            </Link>
          }
        />
      </div>
    )
  }

  return (
    <div className="full-center">
      <Loader2 size={16} className="spinner" /> Signing you in…
    </div>
  )
}
