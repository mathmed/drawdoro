import { CircleAlert } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { completeLogin, startLogin } from '../auth/session'
import EmptyState from '../components/ui/EmptyState'
import BrandLoader from '../components/ui/loading/BrandLoader'
import { useDelayedVisibility } from '../hooks/useDelayedVisibility'
import { useAuthStore } from '../store/useAuthStore'

export default function AuthCallback() {
  const navigate = useNavigate()
  const initialize = useAuthStore((state) => state.initialize)
  const [error, setError] = useState<string | null>(null)
  // The authorization code is single-use; StrictMode's double effect must not redeem it twice.
  const started = useRef(false)
  const showLoader = useDelayedVisibility(error === null)

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
    <div className="loading-screen" aria-busy="true">
      {showLoader ? (
        <BrandLoader
          label="Signing you in"
          showName
          size={52}
          retryLabel="Sign in again"
          onRetry={() => void startLogin('/')}
        />
      ) : null}
    </div>
  )
}
