import { ArrowLeft } from 'lucide-react'
import { Link } from 'react-router-dom'

import Logo from '../components/ui/Logo'

import { branding } from '../config/branding'

export default function NotFound() {
  return (
    <div className="not-found">
      <Logo size={40} />
      <div className="not-found-code">404</div>
      <h1 style={{ fontSize: 18, fontWeight: 600 }}>Page not found</h1>
      <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>The page you’re looking for doesn’t exist or was moved.</p>
      <Link to="/" className="btn btn-secondary" style={{ marginTop: 12, textDecoration: 'none' }}>
        <ArrowLeft size={15} /> Back to {branding.name}
      </Link>
    </div>
  )
}
