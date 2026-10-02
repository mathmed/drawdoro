import { BookOpenText, MessageSquare, Workflow } from 'lucide-react'
import { useState } from 'react'
import { useLocation } from 'react-router-dom'

import { startLogin } from '../auth/session'
import Spinner from '../components/ui/loading/Spinner'
import Logo from '../components/ui/Logo'
import { branding } from '../config/branding'

const FEATURES = [
  { icon: Workflow, title: 'Draw architecture', description: 'An infinite canvas with shapes that snap together and smart connecting arrows.' },
  { icon: BookOpenText, title: 'Keep docs close', description: 'Markdown documentation and component properties live next to each diagram.' },
  { icon: MessageSquare, title: 'Work together', description: 'Edit in real time and discuss any shape with anchored comments.' },
]

function GoogleMark() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden>
      <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.7 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.2-.1-2.3-.4-3.5z" />
      <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z" />
      <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z" />
      <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.2-.1-2.3-.4-3.5z" />
    </svg>
  )
}

// First screen for signed-out visitors: what the product is, and the single way in.
export default function Landing() {
  const location = useLocation()
  const [isRedirecting, setIsRedirecting] = useState(false)

  function handleSignIn(): void {
    setIsRedirecting(true)
    const returnTo = `${location.pathname}${location.search}`
    void startLogin(returnTo === '/auth/callback' ? '/' : returnTo)
  }

  return (
    <div className="landing scroll">
      <header className="landing-header">
        <Logo size={28} withWordmark />
      </header>
      <main className="landing-main">
        <div className="landing-copy">
          <span className="landing-eyebrow">Internal architecture workspace</span>
          <h1 className="landing-title">Design systems visually. Keep everyone on the same page.</h1>
          <p className="landing-description">
            {branding.name} brings architecture diagrams, documentation and team discussion together in one
            collaborative canvas.
          </p>
          <button
            type="button"
            className="btn btn-lg google-button"
            onClick={handleSignIn}
            disabled={isRedirecting}
            aria-busy={isRedirecting}
          >
            {isRedirecting ? <Spinner size={18} /> : <GoogleMark />}
            Continue with Google
          </button>
          <p className="landing-note">Use your company Google account.</p>
        </div>
        <div className="landing-preview" aria-hidden>
          <div className="preview-card preview-a">API Gateway</div>
          <div className="preview-card preview-b">Orders service</div>
          <div className="preview-card preview-c">Orders DB</div>
          <svg className="preview-lines" viewBox="0 0 400 300" fill="none">
            <path d="M120 78 V150 H212" />
            <path d="M300 172 V224" />
          </svg>
        </div>
      </main>
      <section className="landing-features">
        {FEATURES.map(({ icon: Icon, title, description }) => (
          <div key={title} className="feature">
            <Icon size={18} />
            <div className="feature-title">{title}</div>
            <div className="feature-description">{description}</div>
          </div>
        ))}
      </section>
    </div>
  )
}
